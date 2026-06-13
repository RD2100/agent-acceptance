#!/usr/bin/env python3
"""CDP Write Adapter — inject prompts into ChatGPT via Chrome DevTools Protocol.

Low-level adapter that connects to an existing Chrome instance with
``--remote-debugging-port=9222`` and sends text to ChatGPT conversation
tabs.  This is the **write** counterpart to the read-only CDP helpers
in ``multi_cdp_launcher.py``.

Requirements
------------
* Python ≥ 3.10
* ``websockets`` ≥ 13 (async library — Chrome 149+ rejects the
  synchronous ``websocket-client`` handshake)
* Chrome running with ``--remote-debugging-port=9222``
* At least one open ``chatgpt.com/c/<conversation-id>`` tab

Usage
-----
::

  # dry-run: validate connectivity without sending
  python cdp_write_adapter.py dry-run --page-id <target-id>

  # inject a prompt and wait for the response
  python cdp_write_adapter.py inject --page-id <target-id> --prompt "Hello"

  # inject from file (for long TaskSpecs)
  python cdp_write_adapter.py inject --page-id <target-id> --prompt-file task.md

  # capture the latest assistant response from a page
  python cdp_write_adapter.py capture --page-id <target-id>

Architecture
------------
::

  ┌─────────────────┐      WebSocket       ┌──────────────────┐
  │ cdp_write_adapter│ ◄──────────────────► │ Chrome (port 9222)│
  │  (this script)   │   CDP protocol 1.3   │  ChatGPT tab      │
  └─────────────────┘                       └──────────────────┘
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent
DEFAULT_CDP_PORT = 9222
DEFAULT_RESPONSE_TIMEOUT = 300  # seconds — 5 min for complex tasks
DEFAULT_POLL_INTERVAL = 3       # seconds between response polls

# ── Data classes ──────────────────────────────────────────────────────


@dataclass
class CDPPage:
    """Metadata for one open Chrome tab."""
    target_id: str
    url: str
    conversation_id: str | None
    title: str
    ws_url: str

    @classmethod
    def from_cdp_json(cls, data: dict) -> "CDPPage":
        url = data.get("url", "")
        conv_id = None
        if "/c/" in url:
            conv_id = url.split("/c/")[-1].split("?")[0].split("#")[0]
        return cls(
            target_id=data["id"],
            url=url,
            conversation_id=conv_id,
            title=data.get("title", ""),
            ws_url=data.get("webSocketDebuggerUrl", ""),
        )


@dataclass
class InjectionResult:
    """Result of injecting a prompt into a ChatGPT tab."""
    success: bool
    method: str          # "execCommand" | "dom" | "clipboard"
    text_length: int
    error: str | None = None


@dataclass
class DispatchResult:
    """End-to-end result of sending a prompt and capturing the response."""
    injection: InjectionResult
    sent: bool
    response_text: str
    response_time_seconds: float
    error: str | None = None
    captured_at: str = ""

    def __post_init__(self):
        if not self.captured_at:
            self.captured_at = _utc_now()


# ── Utilities ─────────────────────────────────────────────────────────


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _list_cdp_pages(port: int = DEFAULT_CDP_PORT) -> list[CDPPage]:
    """List all open pages via CDP HTTP endpoint."""
    try:
        with urllib.request.urlopen(f"http://localhost:{port}/json", timeout=5) as resp:
            pages = json.loads(resp.read().decode("utf-8"))
        return [CDPPage.from_cdp_json(p) for p in pages if isinstance(p, dict)]
    except Exception:
        return []


def _find_chatgpt_pages(port: int = DEFAULT_CDP_PORT) -> list[CDPPage]:
    """Filter to ChatGPT conversation pages only."""
    return [p for p in _list_cdp_pages(port) if "chatgpt.com/c/" in p.url]


# ── CDP WebSocket client ─────────────────────────────────────────────


class CDPClient:
    """Async CDP client using ``websockets`` library.

    Connects to a single page-level WebSocket and provides helpers
    for ``Runtime.evaluate`` and ``Input.dispatchKeyEvent``.
    """

    def __init__(self, ws_url: str, timeout: int = 30):
        self._ws_url = ws_url
        self._timeout = timeout
        self._ws: Any = None
        self._msg_id = 0

    async def connect(self) -> None:
        from websockets.asyncio.client import connect as ws_connect
        self._ws = await ws_connect(self._ws_url, open_timeout=self._timeout)

    async def close(self) -> None:
        if self._ws:
            await self._ws.close()
            self._ws = None

    async def send_command(self, method: str, params: dict | None = None) -> dict:
        """Send a CDP command and wait for the matching response."""
        if not self._ws:
            raise RuntimeError("Not connected")
        self._msg_id += 1
        mid = self._msg_id
        msg: dict[str, Any] = {"id": mid, "method": method}
        if params:
            msg["params"] = params
        await self._ws.send(json.dumps(msg))
        deadline = time.monotonic() + self._timeout
        while time.monotonic() < deadline:
            raw = await self._ws.recv()
            data = json.loads(raw)
            if data.get("id") == mid:
                if "error" in data:
                    raise RuntimeError(f"CDP error: {data['error']}")
                return data.get("result", {})
        raise TimeoutError(f"No response for {method} within {self._timeout}s")

    async def evaluate(self, expression: str, *, await_promise: bool = False) -> Any:
        """Evaluate JavaScript in the page context."""
        result = await self.send_command("Runtime.evaluate", {
            "expression": expression,
            "returnByValue": True,
            "awaitPromise": await_promise,
        })
        return result.get("result", {}).get("value")

    async def dispatch_key(self, key: str, code: str, vk: int) -> None:
        """Dispatch a key event (down + up)."""
        params = {
            "key": key,
            "code": code,
            "windowsVirtualKeyCode": vk,
            "nativeVirtualKeyCode": vk,
        }
        await self.send_command("Input.dispatchKeyEvent", {**params, "type": "keyDown"})
        await self.send_command("Input.dispatchKeyEvent", {**params, "type": "keyUp"})


# ── ChatGPT page operations ──────────────────────────────────────────


class ChatGPTController:
    """High-level controller for a single ChatGPT conversation tab."""

    # Selector for the ProseMirror input element
    INPUT_SELECTOR = "#prompt-textarea"
    SEND_BUTTON_SELECTOR = 'button[data-testid="send-button"]'

    def __init__(self, cdp: CDPClient):
        self._cdp = cdp

    async def check_page_ready(self) -> dict:
        """Check that the page is loaded and has an editable input."""
        js = """
        (function() {
            const el = document.querySelector('#prompt-textarea');
            return JSON.stringify({
                ready: document.readyState === 'complete',
                hasInput: !!el,
                editable: el ? el.contentEditable === 'true' : false,
                url: window.location.href,
                title: document.title
            });
        })()
        """
        raw = await self._cdp.evaluate(js)
        return json.loads(raw) if raw else {}

    async def inject_prompt(self, text: str) -> InjectionResult:
        """Inject text into the ChatGPT input box.

        Uses ``document.execCommand('insertText')`` which works correctly
        with the ProseMirror editor.  Falls back to direct DOM
        manipulation + events if execCommand fails.
        """
        escaped = text.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")
        js = f"""
        (function() {{
            const el = document.querySelector('#prompt-textarea');
            if (!el) return JSON.stringify({{ok: false, error: 'input not found'}});

            el.focus();
            el.innerHTML = '';

            // Primary: execCommand (ProseMirror-compatible)
            const ok = document.execCommand('insertText', false, `{escaped}`);
            if (ok) return JSON.stringify({{ok: true, method: 'execCommand', len: el.innerText.length}});

            // Fallback: direct DOM + synthetic events
            el.innerHTML = '<p>' + `{escaped}`.replace(/\\n/g, '</p><p>') + '</p>';
            el.dispatchEvent(new Event('input', {{bubbles: true}}));
            el.dispatchEvent(new Event('change', {{bubbles: true}}));
            return JSON.stringify({{ok: true, method: 'dom', len: el.innerText.length}});
        }})()
        """
        raw = await self._cdp.evaluate(js)
        data = json.loads(raw) if raw else {"ok": False, "error": "no response"}
        if data.get("ok"):
            return InjectionResult(
                success=True,
                method=data.get("method", "unknown"),
                text_length=data.get("len", 0),
            )
        return InjectionResult(
            success=False,
            method="none",
            text_length=0,
            error=data.get("error", "unknown"),
        )

    async def send_prompt(self) -> bool:
        """Submit the current input by pressing Enter.

        Returns True if the input was cleared (indicating send success).
        """
        # First try Enter key
        await self._cdp.dispatch_key("Enter", "Enter", 13)
        await asyncio.sleep(1.0)

        # Check if input was cleared
        remaining = await self._cdp.evaluate(
            "(document.querySelector('#prompt-textarea') || {}).innerText || ''"
        )
        if not remaining or remaining.strip() == "":
            return True

        # Fallback: click the send button
        click_js = """
        (function() {
            const btn = document.querySelector('button[data-testid="send-button"]');
            if (btn && !btn.disabled) { btn.click(); return 'clicked'; }
            return 'no_button';
        })()
        """
        result = await self._cdp.evaluate(click_js)
        await asyncio.sleep(1.0)
        return result == "clicked"

    async def is_generating(self) -> bool:
        """Check if ChatGPT is currently generating a response."""
        js = """
        (function() {
            // Stop button appears during generation
            const stop = document.querySelector('[data-testid="stop-button"]');
            if (stop && stop.offsetParent !== null) return 'true';
            // Check for streaming indicator
            const streaming = document.querySelector('[data-testid="streaming-indicator"]');
            if (streaming) return 'true';
            // Check for the "stop generating" button by aria-label
            const btns = document.querySelectorAll('button');
            for (const b of btns) {
                const label = (b.getAttribute('aria-label') || '').toLowerCase();
                if (label.includes('stop') || label.includes('停止')) return 'true';
            }
            return 'false';
        })()
        """
        result = await self._cdp.evaluate(js)
        return result == "true"

    async def wait_for_response(self, timeout: int = DEFAULT_RESPONSE_TIMEOUT,
                                 poll_interval: int = DEFAULT_POLL_INTERVAL) -> str:
        """Wait for ChatGPT to finish generating and return the last response."""
        start = time.monotonic()
        # Wait for generation to start (may take a moment)
        await asyncio.sleep(2)

        # Poll until generation completes
        while time.monotonic() - start < timeout:
            generating = await self.is_generating()
            if not generating:
                # Give a moment for final rendering
                await asyncio.sleep(1)
                return await self.capture_last_response()
            await asyncio.sleep(poll_interval)

        return await self.capture_last_response()

    async def capture_last_response(self) -> str:
        """Extract the text of the last assistant message."""
        js = """
        (function() {
            // ChatGPT uses [data-message-author-role="assistant"] for responses
            const msgs = document.querySelectorAll('[data-message-author-role="assistant"]');
            if (msgs.length === 0) return '';
            const last = msgs[msgs.length - 1];
            // Get the text content, trimming whitespace
            return (last.innerText || '').trim();
        })()
        """
        result = await self._cdp.evaluate(js)
        return result or ""

    async def get_page_title(self) -> str:
        """Get the current page title (conversation name)."""
        return await self._cdp.evaluate("document.title") or ""


# ── High-level dispatch function ──────────────────────────────────────


async def dispatch_to_page(
    ws_url: str,
    prompt: str,
    *,
    wait_for_response: bool = True,
    response_timeout: int = DEFAULT_RESPONSE_TIMEOUT,
    dry_run: bool = False,
) -> DispatchResult:
    """Full dispatch cycle: connect → inject → send → capture."""
    cdp = CDPClient(ws_url, timeout=30)
    controller = ChatGPTController(cdp)

    try:
        await cdp.connect()

        # Pre-flight: check page is ready
        page_info = await controller.check_page_ready()
        if not page_info.get("hasInput") or not page_info.get("editable"):
            return DispatchResult(
                injection=InjectionResult(False, "none", 0, "Page not ready"),
                sent=False,
                response_text="",
                response_time_seconds=0,
                error=f"Page not ready: {json.dumps(page_info, ensure_ascii=False)}",
            )

        if dry_run:
            return DispatchResult(
                injection=InjectionResult(True, "dry_run", len(prompt)),
                sent=False,
                response_text="",
                response_time_seconds=0,
            )

        # Inject prompt
        injection = await controller.inject_prompt(prompt)
        if not injection.success:
            return DispatchResult(
                injection=injection,
                sent=False,
                response_text="",
                response_time_seconds=0,
                error=f"Injection failed: {injection.error}",
            )

        # Send prompt
        start_time = time.monotonic()
        sent = await controller.send_prompt()
        if not sent:
            return DispatchResult(
                injection=injection,
                sent=False,
                response_text="",
                response_time_seconds=time.monotonic() - start_time,
                error="Send failed: input not cleared and no send button found",
            )

        # Wait for response (optional)
        response_text = ""
        if wait_for_response:
            response_text = await controller.wait_for_response(timeout=response_timeout)

        elapsed = time.monotonic() - start_time
        return DispatchResult(
            injection=injection,
            sent=True,
            response_text=response_text,
            response_time_seconds=round(elapsed, 2),
        )

    except Exception as e:
        return DispatchResult(
            injection=InjectionResult(False, "none", 0, str(e)),
            sent=False,
            response_text="",
            response_time_seconds=0,
            error=str(e),
        )
    finally:
        await cdp.close()


# ── CLI ───────────────────────────────────────────────────────────────


def cmd_list_pages(args) -> int:
    """List all open ChatGPT conversation tabs."""
    pages = _find_chatgpt_pages(args.port)
    if not pages:
        print("No ChatGPT pages found on CDP port", args.port)
        return 1

    print(f"ChatGPT pages on localhost:{args.port}:")
    for p in pages:
        conv = p.conversation_id or "N/A"
        print(f"  [{p.target_id[:16]}...] conv={conv[:16]}...")
        print(f"    title: {p.title[:60]}")
        print(f"    url:   {p.url}")
    return 0


def cmd_dry_run(args) -> int:
    """Validate CDP connectivity without sending anything."""
    pages = _find_chatgpt_pages(args.port)
    target = None
    for p in pages:
        if p.target_id == args.page_id or p.target_id.startswith(args.page_id):
            target = p
            break

    if not target:
        print(f"Target {args.page_id} not found")
        return 1

    print(f"Target: {target.target_id}")
    print(f"URL:    {target.url}")
    print(f"Conv:   {target.conversation_id}")

    async def _check():
        cdp = CDPClient(target.ws_url)
        ctrl = ChatGPTController(cdp)
        await cdp.connect()
        info = await ctrl.check_page_ready()
        title = await ctrl.get_page_title()
        await cdp.close()
        return info, title

    info, title = asyncio.run(_check())
    print(f"Title:  {title}")
    print(f"Ready:  {info.get('ready')}")
    print(f"Input:  {info.get('hasInput')} (editable: {info.get('editable')})")
    print("DRY-RUN: PASS" if info.get("hasInput") else "DRY-RUN: FAIL")
    return 0 if info.get("hasInput") else 1


def cmd_inject(args) -> int:
    """Inject a prompt into a ChatGPT tab."""
    pages = _find_chatgpt_pages(args.port)
    target = None
    for p in pages:
        if p.target_id == args.page_id or p.target_id.startswith(args.page_id):
            target = p
            break

    if not target:
        print(f"Target {args.page_id} not found")
        return 1

    # Read prompt from file or argument
    if args.prompt_file:
        prompt = Path(args.prompt_file).read_text(encoding="utf-8")
    elif args.prompt:
        prompt = args.prompt
    else:
        print("Provide --prompt or --prompt-file")
        return 1

    print(f"Target: {target.target_id} ({target.conversation_id})")
    print(f"Prompt: {len(prompt)} chars")
    print(f"Wait:   {not args.no_wait}")
    print()

    result = asyncio.run(dispatch_to_page(
        target.ws_url,
        prompt,
        wait_for_response=not args.no_wait,
        response_timeout=args.timeout,
        dry_run=False,
    ))

    # Output result as JSON
    output = {
        "success": result.sent and result.injection.success,
        "injection": {
            "method": result.injection.method,
            "text_length": result.injection.text_length,
            "success": result.injection.success,
        },
        "sent": result.sent,
        "response_time_seconds": result.response_time_seconds,
        "response_text_preview": result.response_text[:500] if result.response_text else "",
        "error": result.error,
        "captured_at": result.captured_at,
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))

    # Save evidence if requested
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nEvidence saved: {output_path}")

    return 0 if output["success"] else 1


def cmd_capture(args) -> int:
    """Capture the last assistant response from a ChatGPT tab."""
    pages = _find_chatgpt_pages(args.port)
    target = None
    for p in pages:
        if p.target_id == args.page_id or p.target_id.startswith(args.page_id):
            target = p
            break

    if not target:
        print(f"Target {args.page_id} not found")
        return 1

    async def _capture():
        cdp = CDPClient(target.ws_url)
        ctrl = ChatGPTController(cdp)
        await cdp.connect()
        text = await ctrl.capture_last_response()
        title = await ctrl.get_page_title()
        await cdp.close()
        return text, title

    text, title = asyncio.run(_capture())
    output = {
        "target_id": target.target_id,
        "conversation_id": target.conversation_id,
        "title": title,
        "response_text": text,
        "captured_at": _utc_now(),
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nEvidence saved: {output_path}")

    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CDP Write Adapter — inject prompts into ChatGPT via CDP"
    )
    sub = parser.add_subparsers(dest="command")

    # list-pages
    p_list = sub.add_parser("list-pages", help="List open ChatGPT tabs")
    p_list.add_argument("--port", type=int, default=DEFAULT_CDP_PORT)

    # dry-run
    p_dry = sub.add_parser("dry-run", help="Validate connectivity")
    p_dry.add_argument("--page-id", required=True, help="CDP target ID (prefix OK)")
    p_dry.add_argument("--port", type=int, default=DEFAULT_CDP_PORT)

    # inject
    p_inj = sub.add_parser("inject", help="Inject prompt into ChatGPT")
    p_inj.add_argument("--page-id", required=True, help="CDP target ID (prefix OK)")
    p_inj.add_argument("--port", type=int, default=DEFAULT_CDP_PORT)
    p_inj.add_argument("--prompt", help="Prompt text")
    p_inj.add_argument("--prompt-file", help="Read prompt from file")
    p_inj.add_argument("--no-wait", action="store_true", help="Don't wait for response")
    p_inj.add_argument("--timeout", type=int, default=DEFAULT_RESPONSE_TIMEOUT)
    p_inj.add_argument("--output", help="Save evidence JSON to file")

    # capture
    p_cap = sub.add_parser("capture", help="Capture last assistant response")
    p_cap.add_argument("--page-id", required=True, help="CDP target ID (prefix OK)")
    p_cap.add_argument("--port", type=int, default=DEFAULT_CDP_PORT)
    p_cap.add_argument("--output", help="Save evidence JSON to file")

    args = parser.parse_args()

    if args.command == "list-pages":
        sys.exit(cmd_list_pages(args))
    elif args.command == "dry-run":
        sys.exit(cmd_dry_run(args))
    elif args.command == "inject":
        sys.exit(cmd_inject(args))
    elif args.command == "capture":
        sys.exit(cmd_capture(args))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
