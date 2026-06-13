#!/usr/bin/env python3
"""Send review reports to ChatGPT via Playwright (one at a time, wait for response).

Security: Evidence attribution uses the resolved target from binding, not hardcoded values.
Each evidence record includes actual page URL, actual conversation_id, prompt hash, and
response hash, with an assertion that they match the binding target.
"""
import asyncio
import hashlib
import json
import sys
import time
import urllib.request
from pathlib import Path

from playwright.async_api import async_playwright

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

from cdp_dispatch_runner import (
    discover_reports, load_binding, discover_targets,
    map_reports_to_reviewers, format_review_prompt_safe, _detect_prompt_injection,
    EVIDENCE_DIR,
)
from cdp_write_adapter import _conversation_id_from_url


def _sha256(text: str) -> str:
    """Return the full SHA-256 digest used by evidence records."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _resolve_browser_cdp_endpoint(endpoint: str = "http://localhost:9222") -> str:
    """Resolve an HTTP CDP endpoint to its browser WebSocket URL."""
    if endpoint.startswith(("ws://", "wss://")):
        return endpoint

    version_url = f"{endpoint.rstrip('/')}/json/version"
    with urllib.request.urlopen(version_url, timeout=5) as response:
        payload = json.loads(response.read().decode("utf-8"))

    ws_url = payload.get("webSocketDebuggerUrl")
    if not isinstance(ws_url, str) or not ws_url.startswith(("ws://", "wss://")):
        raise RuntimeError("CDP /json/version did not provide a browser WebSocket URL")
    return ws_url


async def _actual_target_info(page) -> dict:
    """Read actual target identity from the browser CDP session."""
    session = await page.context.new_cdp_session(page)
    try:
        payload = await session.send("Target.getTargetInfo")
    finally:
        await session.detach()
    return payload["targetInfo"]


def _attribution_matches(expected_target, actual_target: dict) -> bool:
    """Compare expected binding identity with browser-derived target identity."""
    actual_conversation_id = _conversation_id_from_url(actual_target.get("url", ""))
    return (
        actual_target.get("targetId") == expected_target.target_id
        and actual_conversation_id == expected_target.conversation_id
    )


async def _paste_via_clipboard(page, prompt: str) -> None:
    """Paste a prompt and clear the OS clipboard before returning."""
    await page.evaluate("(text) => navigator.clipboard.writeText(text)", prompt)
    try:
        await page.keyboard.press("Control+v")
    finally:
        await page.evaluate("() => navigator.clipboard.writeText('')")


async def send_one(page, prompt: str, *, timeout: int = 300, need_reload: bool = False) -> dict:
    """Send one prompt and wait for response.
    
    Uses clipboard paste (Ctrl+V) for reliable text entry into
    ChatGPT's ProseMirror editor, then Enter to submit.
    """
    # Reload page if state is corrupted (first message or after failures)
    if need_reload:
        print("    Reloading page to clear stale state...", flush=True)
        await page.reload(wait_until='networkidle')
        await asyncio.sleep(3)
    
    ta = page.locator('#prompt-textarea')
    await ta.wait_for(state='visible', timeout=15000)
    await ta.click()
    await page.keyboard.press("Control+a")
    await page.keyboard.press("Backspace")
    await asyncio.sleep(0.3)

    # Use clipboard paste for reliable React state sync, then remove sensitive content.
    await asyncio.sleep(0.3)
    await _paste_via_clipboard(page, prompt)
    await asyncio.sleep(1.0)

    text = await ta.inner_text()
    if not text.strip():
        return {"success": False, "error": "Text not entered via clipboard"}

    # Wait for send button to appear (data-testid="send-button")
    send_btn = page.locator('[data-testid="send-button"]')
    try:
        await send_btn.wait_for(state='visible', timeout=5000)
    except Exception:
        pass  # May not appear, Enter should still work

    # Press Enter to submit
    await page.keyboard.press("Enter")
    await asyncio.sleep(2)

    remaining = await ta.inner_text()
    if remaining and remaining.strip():
        return {"success": False, "error": "Message not sent", "remaining": remaining[:100]}

    # Wait for response
    start = time.monotonic()
    print("    Waiting for response...", flush=True)

    # Wait for generation to start
    await asyncio.sleep(5)

    # Poll until generation completes
    for i in range(timeout // 3):
        stop_visible = await page.locator('[data-testid="stop-button"]').is_visible()
        elapsed = time.monotonic() - start
        if not stop_visible and elapsed > 8:
            break
        if i % 10 == 0 and i > 0:
            print(f"    [{elapsed:.0f}s] still generating...", flush=True)
        await asyncio.sleep(3)

    # Capture last assistant message
    await asyncio.sleep(2)
    msgs = page.locator('[data-message-author-role="assistant"]')
    count = await msgs.count()
    response_text = ""
    if count > 0:
        response_text = await msgs.nth(count - 1).inner_text()

    elapsed = time.monotonic() - start
    return {
        "success": True,
        "sent": True,
        "response_text": response_text,
        "response_time_seconds": round(elapsed, 1),
        "message_count": count,
    }


async def main() -> int:
    print("=== CDP Review Dispatch via Playwright ===\n")

    reports = discover_reports()
    print(f"Reports: {len(reports)}")
    for r in reports:
        print(f"  {r['role']:25s} {r['file']:30s} {r['verdict']:12s} {r['content_length']} chars")

    binding = load_binding()
    targets = discover_targets()
    mappings = map_reports_to_reviewers(reports, binding, targets)

    if not mappings:
        print("ERROR: No valid reviewer mappings — fail-closed (no active reviewer binding)")
        return 1

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

    # Derive reviewer conversation_id from resolved mapping (not hardcoded)
    # All reports map to the same reviewer, so take the first mapping's target
    resolved_target = mappings[0][1]
    reviewer_conv = resolved_target.conversation_id
    print(f"Resolved reviewer: conv={reviewer_conv}, target={resolved_target.target_id}")

    async with async_playwright() as pw:
        browser = await pw.chromium.connect_over_cdp(_resolve_browser_cdp_endpoint())

        # Find reviewer page by resolved conversation_id
        reviewer_pages = [
            page
            for context in browser.contexts
            for page in context.pages
            if _conversation_id_from_url(page.url) == reviewer_conv
        ]
        if len(reviewer_pages) != 1:
            print(
                f"ERROR: Expected exactly one reviewer page (conv={reviewer_conv}), "
                f"found {len(reviewer_pages)}"
            )
            print(f"  Binding requires: {resolved_target.url}")
            print(f"  Available tabs: {[p.url for ctx in browser.contexts for p in ctx.pages]}")
            return 1

        reviewer_page = reviewer_pages[0]
        actual_url = reviewer_page.url
        actual_target = await _actual_target_info(reviewer_page)
        actual_url = actual_target.get("url", actual_url)
        actual_conv = _conversation_id_from_url(actual_url)
        actual_target_id = actual_target.get("targetId")
        attribution_verified = _attribution_matches(resolved_target, actual_target)
        if not attribution_verified:
            print(
                "ERROR: Evidence attribution mismatch: "
                f"expected target={resolved_target.target_id}, conv={reviewer_conv}; "
                f"actual target={actual_target_id}, conv={actual_conv}, url={actual_url}"
            )
            return 1
        print(f"Reviewer page: {actual_url}")
        print(f"Attribution verified: binding target == actual page\n")

        results = []
        first_message = True
        for i, (report, target) in enumerate(mappings):
            injection_flags = _detect_prompt_injection(report.get("content", ""))
            print(f"[{i+1}/{len(mappings)}] {report['role']} — {report['file']}")
            prompt = format_review_prompt_safe(report)
            print(f"  Prompt: {len(prompt)} chars")

            # Reload on first message or if previous failed (clears stale state)
            need_reload = first_message
            first_message = False
            
            if injection_flags:
                result = {
                    "success": False,
                    "sent": False,
                    "error": "prompt injection indicators: " + ", ".join(injection_flags),
                    "status": "BLOCKED_PROMPT_INJECTION",
                    "injection_flags": injection_flags,
                }
                print(f"  BLOCKED: {result['error']}")
            else:
                result = await send_one(
                    reviewer_page, prompt, timeout=300, need_reload=need_reload
                )
            
            # Retry once with reload if failed
            if not result.get("success") and result.get("status") != "BLOCKED_PROMPT_INJECTION":
                print(f"  First attempt failed: {result.get('error')}. Retrying with reload...")
                await asyncio.sleep(2)
                result = await send_one(reviewer_page, prompt, timeout=300, need_reload=True)
            
            # Evidence with full attribution chain
            result["report_role"] = report["role"]
            result["report_file"] = report["file"]
            result["report_verdict"] = report["verdict"]
            result["target_id"] = target.target_id
            result["conversation_id"] = target.conversation_id
            result["expected_target_id"] = target.target_id
            result["expected_conversation_id"] = target.conversation_id
            result["actual_target_id"] = actual_target_id
            result["actual_page_url"] = actual_url
            result["actual_conversation_id"] = actual_conv
            result["prompt_hash"] = _sha256(prompt)
            result["response_hash"] = _sha256(result.get("response_text", ""))
            result["attribution_verified"] = attribution_verified
            results.append(result)

            # Save evidence
            safe_name = report["file"].replace(".md", "").lower()
            ev_file = EVIDENCE_DIR / f"review-{safe_name}.json"
            ev_file.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"  Evidence: {ev_file}")

            if result["success"]:
                preview = result["response_text"][:150].replace("\n", " ")
                print(f"  Response ({result['response_time_seconds']}s): {preview}...")
            else:
                print(f"  FAILED: {result.get('error')}")

            print()

        # Summary
        sent = sum(1 for r in results if r.get("sent"))
        failed = sum(1 for r in results if not r.get("sent"))
        print(f"{'='*60}")
        print(f"Done: {sent}/{len(results)} sent, {failed} failed")

        # Save summary with resolved attribution
        summary = {
            "schema_version": "2.1.0",
            "dispatch_method": "playwright_cdp",
            "resolved_reviewer_conversation": reviewer_conv,
            "resolved_target_id": resolved_target.target_id,
            "actual_target_id": actual_target_id,
            "actual_conversation_id": actual_conv,
            "actual_page_url": actual_url,
            "attribution_verified": attribution_verified,
            "total_reports": len(reports),
            "sent": sent,
            "failed": failed,
            "results": results,
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        }
        summary_file = EVIDENCE_DIR / "REVIEW_DISPATCH_SUMMARY.json"
        summary_file.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Summary: {summary_file}")

        # This Browser is attached to the user-owned shared Chrome instance.
        # Exiting async_playwright() disconnects this client; browser.close()
        # would close the shared runtime and every project tab.
        return 0 if sent == len(results) and failed == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
