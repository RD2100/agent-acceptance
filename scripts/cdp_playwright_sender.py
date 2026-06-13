#!/usr/bin/env python3
"""Send review reports to ChatGPT via Playwright (one at a time, wait for response)."""
import asyncio
import json
import sys
import time
from pathlib import Path

from playwright.async_api import async_playwright

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

from cdp_dispatch_runner import (
    discover_reports, load_binding, discover_targets,
    map_reports_to_reviewers, format_review_prompt_safe, EVIDENCE_DIR,
)

REVIEWER_CONV = "6a297f76-3e7c-83a5-a0e5-b4413d923c7e"


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

    # Use clipboard paste for reliable React state sync
    import json as _json
    await page.evaluate(f"""(text) => navigator.clipboard.writeText(text)""", prompt)
    await asyncio.sleep(0.3)
    await page.keyboard.press("Control+v")
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


async def main():
    print("=== CDP Review Dispatch via Playwright ===\n")

    reports = discover_reports()
    print(f"Reports: {len(reports)}")
    for r in reports:
        print(f"  {r['role']:25s} {r['file']:30s} {r['verdict']:12s} {r['content_length']} chars")

    binding = load_binding()
    targets = discover_targets()
    mappings = map_reports_to_reviewers(reports, binding, targets)

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as pw:
        browser = await pw.chromium.connect_over_cdp("http://localhost:9222")

        # Find reviewer page
        reviewer_page = None
        for ctx in browser.contexts:
            for p in ctx.pages:
                if REVIEWER_CONV in p.url:
                    reviewer_page = p
                    break

        if not reviewer_page:
            print(f"Reviewer page ({REVIEWER_CONV}) not found!")
            return

        print(f"Reviewer page: {reviewer_page.url}\n")

        results = []
        first_message = True
        for i, (report, target) in enumerate(mappings):
            print(f"[{i+1}/{len(mappings)}] {report['role']} — {report['file']}")
            prompt = format_review_prompt_safe(report)
            print(f"  Prompt: {len(prompt)} chars")

            # Reload on first message or if previous failed (clears stale state)
            need_reload = first_message
            first_message = False
            
            result = await send_one(reviewer_page, prompt, timeout=300, need_reload=need_reload)
            
            # Retry once with reload if failed
            if not result.get("success"):
                print(f"  First attempt failed: {result.get('error')}. Retrying with reload...")
                await asyncio.sleep(2)
                result = await send_one(reviewer_page, prompt, timeout=300, need_reload=True)
            
            result["report_role"] = report["role"]
            result["report_file"] = report["file"]
            result["report_verdict"] = report["verdict"]
            result["target_id"] = target.target_id
            result["conversation_id"] = target.conversation_id
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

        # Save summary
        summary = {
            "schema_version": "2.0.0",
            "dispatch_method": "playwright_cdp",
            "reviewer_conversation": REVIEWER_CONV,
            "total_reports": len(reports),
            "sent": sent,
            "failed": failed,
            "results": results,
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        }
        summary_file = EVIDENCE_DIR / "REVIEW_DISPATCH_SUMMARY.json"
        summary_file.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Summary: {summary_file}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
