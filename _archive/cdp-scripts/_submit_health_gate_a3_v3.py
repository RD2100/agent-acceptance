"""Submit A3 R1 to GPT — v3 using proven _ask_next_task_v2 pattern."""
import asyncio, json, sys, time as _time
from pathlib import Path
from playwright.async_api import async_playwright

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))
from _cdp_submit_helper import run_pre_gpt_gate

# Same conversation as A1/A2 reviews
TARGET_URL = "https://chatgpt.com/c/6a2a8cb1-b228-83aa-addb-79bda9aba043"
CDP_URL = "http://localhost:9222"
VERDICT_FILE = REPO / "_evidence" / "conversation_health_gate_a3_verdict.txt"

MSG = (REPO / "_evidence" / "CONVERSATION-HEALTH-GATE-A3" / "gpt-review-prompt.md"
       ).read_text(encoding="utf-8")


async def main():
    _start = _time.monotonic()

    # Pre-gate
    ec, dec, msg = run_pre_gpt_gate(allow_init=True)
    if ec != 0:
        print(f"BLOCKED ({ec}): {msg}")
        return
    print(f"GATE: {msg}")

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(CDP_URL)
        ctx = browser.contexts[0]

        # Find target page
        target = None
        for pg in ctx.pages:
            if "6a2a8cb1" in pg.url:
                target = pg
                break
        if not target:
            target = ctx.pages[0]
            print(f"Navigating from {target.url}")
            await target.goto(TARGET_URL, wait_until="networkidle", timeout=30000)
            await target.wait_for_timeout(5000)

        print(f"Page: {target.url}")

        # Count user messages before
        ub = await target.locator('div[data-message-author-role="user"]').count()
        print(f"User msgs before: {ub}")

        # Focus editor
        editor = target.locator('#prompt-textarea')
        if await editor.count() == 0:
            editor = target.locator('div[contenteditable="true"]').last
        await editor.click()
        await target.wait_for_timeout(500)

        # Paste via clipboard
        await target.evaluate(f"""
            async () => {{
                await navigator.clipboard.writeText({json.dumps(MSG)});
            }}
        """)
        await target.wait_for_timeout(500)
        await editor.press("Control+v")
        await target.wait_for_timeout(2000)

        # Send
        send_btn = target.locator('button[data-testid="send-button"]')
        disabled = await send_btn.first.get_attribute("disabled")
        print(f"Send disabled: {disabled}")
        if disabled is None:
            await send_btn.first.click()
        else:
            await editor.press("Enter")
            await target.wait_for_timeout(2000)
            d2 = await send_btn.first.get_attribute("disabled")
            if d2 is not None:
                await send_btn.first.click(force=True)

        await target.wait_for_timeout(5000)
        ua = await target.locator('div[data-message-author-role="user"]').count()
        print(f"User msgs after: {ua}")
        if ua <= ub:
            print("WARNING: Message may not have been sent")
            await target.screenshot(path=str(REPO / "_evidence" / "a3_r1_send_debug.png"))
            return
        print(f"SUCCESS: {ub} -> {ua}")

        # Wait for GPT response
        print("Waiting for GPT response (120s)...")
        await target.wait_for_timeout(120000)

        # Check if still generating
        stop_btn = target.locator('button[data-testid="stop-button"]')
        if await stop_btn.count() > 0 and await stop_btn.first.is_visible():
            print("GPT still generating, waiting more (60s)...")
            await target.wait_for_timeout(60000)

        # Capture reply
        ams = target.locator('div[data-message-author-role="assistant"]')
        cnt = await ams.count()
        if cnt > 0:
            reply = await ams.last.inner_text()
            print(f"\n=== GPT REPLY ({len(reply)} chars) ===")
            print(reply[:5000])
            VERDICT_FILE.write_text(reply, encoding="utf-8")
            print(f"\nVerdict saved: {VERDICT_FILE}")

            if "ACCEPTED" in reply:
                print("\n>>> VERDICT: ACCEPTED <<<")
            elif "NEEDS_REVISION" in reply:
                print("\n>>> VERDICT: NEEDS_REVISION <<<")
            else:
                print("\n>>> VERDICT: UNCLEAR <<<")

            # Post-response metrics refresh
            _reply_bytes = len(reply.encode("utf-8"))
            _resp_time = _time.monotonic() - _start
            try:
                _scripts_dir = str(REPO / "scripts")
                _path_added = False
                if _scripts_dir not in sys.path:
                    sys.path.insert(0, _scripts_dir)
                    _path_added = True
                from pre_gpt_gate import update_metrics as _um
                _updated, _err = _um(
                    new_metrics={
                        "assistant_message_count": cnt,
                        "last_gpt_reply_bytes": _reply_bytes,
                        "last_response_time_seconds": round(_resp_time, 1),
                    },
                    nav_result="ok",
                    source="cdp_dom_count",
                )
                if _err:
                    print(f"WARNING: Metrics refresh failed: {_err}")
                else:
                    print(f"Metrics refreshed — msgs={cnt}, bytes={_reply_bytes}")
            except ImportError as exc:
                print(f"Post-response refresh skipped: {exc}")
        else:
            print("No assistant messages found")
            await target.screenshot(path=str(REPO / "_evidence" / "a3_r1_capture_debug.png"))


asyncio.run(main())
