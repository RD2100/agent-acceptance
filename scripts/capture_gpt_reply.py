"""Reliable GPT reply capture — waits for END_OF_GPT_RESPONSE, validates after capture."""
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from scripts.validate_gpt_reply_completeness import check_completeness


def capture_gpt_reply(page, save_path: str, expected_type: str = "review",
                       timeout: int = 300, poll_interval: int = 5) -> dict:
    """
    Capture GPT reply with end-marker detection.
    Returns {"captured": bool, "path": str, "size": int, "valid": bool, "issues": []}
    """
    save_fp = Path(save_path)
    end_marker = "END_OF_GPT_RESPONSE" if expected_type != "handoff" else "END_OF_HANDOFF"
    min_size = {"review": 2000, "task_plan": 3000, "handoff": 8000}.get(expected_type, 2000)

    waited = 0
    last_len = 0
    stable_count = 0

    while waited < timeout:
        time.sleep(poll_interval)
        waited += poll_interval

        msgs = page.locator('[data-message-author-role="assistant"]')
        if msgs.count() == 0:
            continue

        reply = msgs.last.text_content(timeout=5000) or ""
        current_len = len(reply)

        # End marker detected: capture immediately
        if end_marker in reply and current_len >= min_size:
            save_fp.write_text(reply, encoding="utf-8")
            result = check_completeness(save_path, expected_type)
            return {
                "captured": True, "path": save_path, "size": current_len,
                "valid": result["complete"], "issues": result["issues"],
                "waited_seconds": waited,
            }

        # Stable but no end marker: might be still generating or broken
        if current_len == last_len:
            stable_count += 1
        else:
            stable_count = 0
            last_len = current_len

        # If stable too long without end marker, re-read once more
        if stable_count >= 6 and current_len >= min_size:
            time.sleep(10)
            msgs = page.locator('[data-message-author-role="assistant"]')
            reply = msgs.last.text_content(timeout=5000) or ""
            save_fp.write_text(reply, encoding="utf-8")
            result = check_completeness(save_path, expected_type)
            return {
                "captured": True, "path": save_path, "size": len(reply),
                "valid": result["complete"], "issues": result["issues"],
                "waited_seconds": waited,
            }

    # Timeout
    msgs = page.locator('[data-message-author-role="assistant"]')
    if msgs.count() > 0:
        reply = msgs.last.text_content(timeout=5000) or ""
        save_fp.write_text(reply, encoding="utf-8")
        result = check_completeness(save_path, expected_type)
        return {
            "captured": len(reply) > 0, "path": save_path, "size": len(reply),
            "valid": result["complete"], "issues": result["issues"],
            "waited_seconds": waited, "timeout": True,
        }

    return {"captured": False, "path": save_path, "size": 0, "valid": False,
            "issues": ["no reply captured"], "timeout": True}


# CLI for standalone use:
if __name__ == "__main__":
    from playwright.sync_api import sync_playwright

    target_url = sys.argv[1] if len(sys.argv) > 1 else None
    save_path = sys.argv[2] if len(sys.argv) > 2 else "GPT_REPLY.txt"

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://localhost:9222")
        page = None
        for ctx in browser.contexts:
            for pg in ctx.pages:
                if target_url and target_url in pg.url:
                    page = pg; break
            if page: break
        if not page:
            page = browser.contexts[0].pages[0]

        result = capture_gpt_reply(page, save_path)
        print(f"Captured: {result['captured']}, size: {result['size']}, valid: {result['valid']}")
        if result["issues"]:
            for i in result["issues"]:
                print(f"  - {i}")
