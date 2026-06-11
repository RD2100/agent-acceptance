import asyncio
import hashlib
import json
import re
import time
from pathlib import Path

import pyperclip
from playwright.async_api import async_playwright

ROOT = Path("D:/agent-acceptance")
TASK_ID = "GLOBAL-PROJECT-HANDOFF-REPAIR-A1"
RUN_ID = (ROOT / "_reports/global-project-handoff-repair-a1/GPT_REVIEW_RUN_ID.txt").read_text(encoding="utf-8").strip()
PACK = ROOT / "evidence_packs/global-project-handoff-repair-a1/GLOBAL_PROJECT_HANDOFF_REPAIR_A1_20260608_223800.zip"
CHAT_URL_OUT = ROOT / "_reports/global-project-handoff-repair-a1/GPT_REVIEW_CHAT_URL.txt"
STATUS_OUT = ROOT / "_reports/global-project-handoff-repair-a1/GPT_REVIEW_SUBMISSION_STATUS.json"
SCREENSHOT_OUT = ROOT / "_reports/global-project-handoff-repair-a1/GPT_REVIEW_UPLOAD_CONFIRMATION.png"
RESULT_OUT = ROOT / "evidence_packs/global-project-handoff-repair-a1/GPT_REVIEW_RESULT.txt"
REPORT_RESULT_OUT = ROOT / "_reports/global-project-handoff-repair-a1/GPT_REVIEW_RESULT.txt"
TARGET_URL = "https://chatgpt.com/c/6a26cc03-235c-83a2-a0fc-cd29be615959"

PROMPT = f"""GPT REVIEW REQUEST: GLOBAL-PROJECT-HANDOFF-REPAIR-A1

run_id: {RUN_ID}

Please review the attached ZIP evidence pack for GLOBAL-PROJECT-HANDOFF-REPAIR-A1.

Task goal:
Repair the gap where HANDOFF-PIPELINE-REFACTOR-A1 proved the handoff pipeline but did not provide a complete whole-project/global project status handoff.

Please verify:
1. The existing DevFrame evidence-first workflow was reused, not redesigned.
2. WHOLE_PROJECT_STATUS_HANDOFF.md provides a whole-project/global status layer, not just an A1 subtask summary.
3. WHOLE_PROJECT_SOURCE_OF_TRUTH_MAP.json separates P0/P1/P2/P3/unverified claims.
4. 296 PASS remains unverified and is not promoted to source-of-truth.
5. 12 passed vs 13 passed is recorded as a limitation.
6. Empty closed_modules / human_required_modules are not used to hide unknown status.
7. WHOLE_PROJECT_MODULE_STATUS explicitly marks unknown / needs_more_evidence / human_required_review where evidence is incomplete.
8. S3/B2/B3 are treated as historical lineage, not current production promotion.
9. Production promotion is not claimed without P0/P1 evidence.
10. TARGETED_TEST_OUTPUT.txt, SAFETY_SCAN.md, PACK_MANIFEST.md, PRE_GPT_GATE_OUTPUT.txt, and EXECUTION_REPORT.md are present.
11. No legacy PROJECT_HISTORY / HANDOFF / PASTE_BLOCK files were deleted, moved, renamed, or rewritten.
12. No paper full text, raw paragraphs, private notes, tokens, or secrets are included.

If the attachment cannot be inspected, return review_unverified.
Your reply must include the same run_id and END_OF_GPT_RESPONSE.
Return ONLY this YAML-like block:

run_id: {RUN_ID}
task_id: GLOBAL-PROJECT-HANDOFF-REPAIR-A1
overall_judgment: accepted | accepted_with_limitation | blocked | review_unverified
safety_verdict: pass | fail | review_unverified
source_of_truth_verdict: pass | fail | review_unverified
whole_project_handoff_verdict: pass | fail | review_unverified
stale_claims_verdict: pass | fail | review_unverified
test_ledger_verdict: pass | fail | review_unverified
evidence_pack_reviewed: true | false
attachment_reviewed: true | false
blocking_issues:
  - <issue or none>
required_fixes:
  - <fix or none>
limitations:
  - <limitation or none>
next_allowed_action: <specific next action>
next_task_authorization:
  task_id: <next task id or none>
  authorized: 已授权 | 未授权
  execute_immediately: 是 | 否
  ask_before_starting: 是 | 否
END_OF_GPT_RESPONSE
"""


def parse_judgment(text):
    m = re.search(r"overall_judgment:\s*([^\s]+)", text, re.I)
    return m.group(1).strip().lower() if m else None


def page_has_attachment_text(text):
    lowered = text.lower()
    return "global_project_handoff_repair_a1" in lowered or "global-project-handoff-repair-a1" in lowered or "handoff_repair" in lowered


async def find_editor(page):
    for sel in ['div[contenteditable="true"].ProseMirror', 'div[contenteditable="true"]', 'textarea']:
        loc = page.locator(sel)
        if await loc.count() > 0:
            return loc.last
    raise RuntimeError("editor not found")


async def clear_composer(page):
    try:
        editor = await find_editor(page)
        await editor.click(timeout=10000)
        await page.keyboard.press("Control+A")
        await page.keyboard.press("Backspace")
        await asyncio.sleep(0.5)
        return {"ok": True}
    except Exception as exc:
        return {"ok": False, "error": repr(exc)}


async def click_visible_send_button(page):
    selectors = ['button[data-testid="send-button"]', '#composer-submit-button', 'button.composer-submit-button-color', 'button[aria-label="Send prompt"]', 'button[aria-label="Send message"]', 'button[aria-label*="Send"]', 'button:has-text("Send")', 'button:has-text("发送")']
    errors = []
    for sel in selectors:
        try:
            loc = page.locator(sel)
            for i in range(await loc.count()):
                btn = loc.nth(i)
                if await btn.is_visible(timeout=1000) and await btn.is_enabled(timeout=1000):
                    await btn.click(timeout=10000)
                    return {"ok": True, "selector": sel, "index": i, "method": "locator_click"}
        except Exception as exc:
            errors.append(f"{sel}: {exc!r}")
    # JS fallback: click the visible composer submit button directly in DOM.
    try:
        js_result = await page.evaluate('''() => {
            const candidates = Array.from(document.querySelectorAll('button')).filter(b => {
                const r = b.getBoundingClientRect();
                const label = (b.getAttribute('aria-label') || '') + ' ' + (b.getAttribute('data-testid') || '') + ' ' + b.className;
                return r.width > 0 && r.height > 0 && !b.disabled && /send-button|composer-submit|发送|Send/i.test(label);
            });
            const b = candidates[candidates.length - 1];
            if (!b) return {ok:false, reason:'no_candidate'};
            b.click();
            const r = b.getBoundingClientRect();
            return {ok:true, method:'js_click', x:r.x, y:r.y, label:b.getAttribute('aria-label'), testid:b.getAttribute('data-testid'), cls:b.className};
        }''')
        if js_result.get('ok'):
            return js_result
        errors.append(f"js_fallback: {js_result}")
    except Exception as exc:
        errors.append(f"js_fallback: {exc!r}")
    # Coordinate fallback near the visible composer submit button, based on DOM probe.
    try:
        box = await page.evaluate('''() => {
            const b = document.querySelector('button[data-testid="send-button"], #composer-submit-button, button.composer-submit-button-color');
            if (!b) return null;
            const r = b.getBoundingClientRect();
            return {x:r.x + r.width/2, y:r.y + r.height/2};
        }''')
        if box:
            await page.mouse.click(box['x'], box['y'])
            return {"ok": True, "method": "coordinate_click", "x": box['x'], "y": box['y']}
    except Exception as exc:
        errors.append(f"coordinate_fallback: {exc!r}")
    return {"ok": False, "errors": errors}


async def confirm_message_sent(page, before_user_count, before_assistant_count):
    checks = []
    for _ in range(24):
        await asyncio.sleep(1)
        user_count = await page.locator('[data-message-author-role="user"]').count()
        assistant_count = await page.locator('[data-message-author-role="assistant"]').count()
        editor_text = ""
        try:
            editor = await find_editor(page)
            editor_text = (await editor.inner_text(timeout=2000)).strip()
        except Exception:
            pass
        checks.append({"user_count": user_count, "assistant_count": assistant_count, "editor_chars": len(editor_text), "url": page.url})
        if user_count > before_user_count:
            return {"ok": True, "reason": "user_message_bubble_appeared", "checks": checks[-5:]}
        if assistant_count > before_assistant_count and user_count >= before_user_count:
            return {"ok": True, "reason": "assistant_response_started", "checks": checks[-5:]}
    return {"ok": False, "reason": "no_user_bubble_or_assistant_response_after_click", "checks": checks[-5:]}


async def try_upload(page):
    errors = []
    inputs = page.locator('input[type="file"]')
    for i in range(await inputs.count()):
        try:
            await inputs.nth(i).set_input_files(str(PACK))
            await asyncio.sleep(8)
            body_text = await page.locator("body").inner_text(timeout=10000)
            if page_has_attachment_text(body_text):
                return {"ok": True, "method": f"input[{i}]", "body_excerpt": body_text[:2000]}
        except Exception as exc:
            errors.append(f"input[{i}]: {exc!r}")
    return {"ok": False, "errors": errors, "body_excerpt": (await page.locator('body').inner_text(timeout=10000))[:3000]}


async def main():
    status = {"run_id": RUN_ID, "task_id": TASK_ID, "pack": str(PACK), "pack_exists": PACK.exists(), "pack_size": PACK.stat().st_size if PACK.exists() else None, "pack_sha256": hashlib.sha256(PACK.read_bytes()).hexdigest() if PACK.exists() else None, "sent": False, "captured": False, "upload_confirmed": False}
    async with async_playwright() as pw:
        browser = await pw.chromium.connect_over_cdp("http://localhost:9222")
        ctx = browser.contexts[0] if browser.contexts else await browser.new_context()
        page = None
        for pg in ctx.pages:
            if TARGET_URL in pg.url:
                page = pg
                break
        if page is None:
            page = await ctx.new_page()
            await page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=60000)
        await page.bring_to_front()
        await asyncio.sleep(5)
        CHAT_URL_OUT.write_text(page.url + "\n", encoding="utf-8")
        status["chat_url_initial"] = page.url
        status["clear_composer_before_upload"] = await clear_composer(page)
        upload = await try_upload(page)
        status["upload_attempt"] = upload
        status["upload_confirmed"] = bool(upload.get("ok"))
        await page.screenshot(path=str(SCREENSHOT_OUT), full_page=False)
        status["upload_confirmation_screenshot"] = str(SCREENSHOT_OUT)
        STATUS_OUT.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
        if not status["upload_confirmed"]:
            status["status"] = "manual_required"
            status["reason"] = "unable_to_confirm_attachment_visible_in_new_gpt_chat"
            STATUS_OUT.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
            print(json.dumps(status, ensure_ascii=False, indent=2)); return
        pyperclip.copy(PROMPT)
        editor = await find_editor(page)
        await editor.click(timeout=30000)
        await page.keyboard.press("Control+v")
        await asyncio.sleep(2)
        body_after_paste = await page.locator("body").inner_text(timeout=10000)
        if not page_has_attachment_text(body_after_paste):
            status["status"] = "manual_required"
            status["reason"] = "attachment_not_visible_after_prompt_paste"
            STATUS_OUT.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
            print(json.dumps(status, ensure_ascii=False, indent=2)); return
        before_user_count = await page.locator('[data-message-author-role="user"]').count()
        before_assistant_count = await page.locator('[data-message-author-role="assistant"]').count()
        send_click = await click_visible_send_button(page)
        status["send_click"] = send_click
        if not send_click.get("ok"):
            status["status"] = "manual_required"; status["reason"] = "submit_button_not_found_or_not_clickable"
            STATUS_OUT.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
            print(json.dumps(status, ensure_ascii=False, indent=2)); return
        send_confirm = await confirm_message_sent(page, before_user_count, before_assistant_count)
        status["send_confirm"] = send_confirm
        if not send_confirm.get("ok"):
            status["status"] = "manual_required"; status["reason"] = "submit_button_clicked_but_send_not_confirmed"
            STATUS_OUT.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
            print(json.dumps(status, ensure_ascii=False, indent=2)); return
        status["sent"] = True; status["sent_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        STATUS_OUT.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
        last = ""; stable = 0
        for _ in range(120):
            await asyncio.sleep(5)
            if page.url != status.get("chat_url_final"):
                status["chat_url_final"] = page.url; CHAT_URL_OUT.write_text(page.url + "\n", encoding="utf-8")
            msgs = page.locator('[data-message-author-role="assistant"]')
            if await msgs.count() == 0:
                continue
            reply = await msgs.last.inner_text(timeout=10000)
            if reply == last:
                stable += 1
            else:
                stable = 0; last = reply
            if RUN_ID in reply and "END_OF_GPT_RESPONSE" in reply and "overall_judgment:" in reply:
                break
            if stable >= 12 and len(reply) > 300:
                break
        reply = last
        RESULT_OUT.write_text(reply, encoding="utf-8")
        REPORT_RESULT_OUT.write_text(reply, encoding="utf-8")
        status.update({"captured": bool(reply), "reply_chars": len(reply), "reply_sha256": hashlib.sha256(reply.encode("utf-8")).hexdigest() if reply else None, "run_id_match": RUN_ID in reply, "has_end_marker": "END_OF_GPT_RESPONSE" in reply, "has_overall_judgment": "overall_judgment:" in reply, "parsed_overall_judgment": parse_judgment(reply), "chat_url_final": page.url, "result_path": str(RESULT_OUT), "report_result_path": str(REPORT_RESULT_OUT)})
        CHAT_URL_OUT.write_text(page.url + "\n", encoding="utf-8")
        STATUS_OUT.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(status, ensure_ascii=False, indent=2))

asyncio.run(main())
