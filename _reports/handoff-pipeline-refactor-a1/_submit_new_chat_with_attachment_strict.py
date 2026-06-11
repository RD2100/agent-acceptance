import asyncio
import hashlib
import json
import re
import time
from pathlib import Path

import pyperclip
from playwright.async_api import async_playwright

ROOT = Path("D:/agent-acceptance")
RUN_ID = (ROOT / "_reports/handoff-pipeline-refactor-a1/ATTACH_CHAT_RUN_ID.txt").read_text(encoding="utf-8").strip()
PACK = ROOT / "evidence_packs/handoff-pipeline-refactor-a1/closure-pack.zip"
CHAT_URL_OUT = ROOT / "_reports/handoff-pipeline-refactor-a1/ATTACH_GPT_CHAT_URL.txt"
STATUS_OUT = ROOT / "_reports/handoff-pipeline-refactor-a1/ATTACH_SUBMISSION_STATUS.json"
SCREENSHOT_OUT = ROOT / "_reports/handoff-pipeline-refactor-a1/ATTACH_UPLOAD_CONFIRMATION.png"
RESULT_OUT = ROOT / "evidence_packs/handoff-pipeline-refactor-a1/GPT_REVIEW_RESULT_ATTACHCHAT.txt"
REPORT_RESULT_OUT = ROOT / "_reports/handoff-pipeline-refactor-a1/GPT_REVIEW_RESULT_ATTACHCHAT.txt"

PROMPT = f"""GPT REVIEW REQUEST: HANDOFF-PIPELINE-REFACTOR-A1 ATTACHMENT-BACKED VERDICT

run_id: {RUN_ID}

You are reviewing HANDOFF-PIPELINE-REFACTOR-A1. The attached file is closure-pack.zip. Please inspect the attachment and return a fresh verdict for this run_id.

Important:
- This is a new GPT conversation.
- Ignore prior conversations.
- Your response must include the same run_id.
- Return ONLY the YAML-like block below.
- End with END_OF_GPT_RESPONSE.
- If the attachment is unavailable or unreadable, use overall_judgment: review_unverified and evidence_pack_reviewed: false.

Review scope inside closure-pack.zip:
- HANDOFF_SOURCE_OF_TRUTH.md
- LEGACY_HANDOFF_INVENTORY.md
- HANDOFF_DRAFT_FOR_GPT.md
- PASTE_BLOCK_DRAFT_FOR_NEW_GPT.txt
- HANDOFF_EVIDENCE_MAP.json
- HANDOFF_STALE_CHECK.md/json
- HANDOFF_SAFETY_SCAN.md
- TARGETED_TEST_OUTPUT.txt
- SAFETY_ATTESTATION.md
- MINIMAX_M3_OBSERVATION_LOG.md / EVIDENCE_TABLE.json
- PACK_MANIFEST.md
- CLOSURE_REPORT.md

Known limitations to check/preserve:
- CLOSURE_REPORT says 12 passed while TARGETED_TEST_OUTPUT says 13 passed.
- PRE_GPT_GATE_OUTPUT may not be listed in the pack manifest.
- Handoff draft proves the pipeline but may not yet be final full project-state handoff because closed_modules / human_required_modules may be empty.
- 296 PASS remains an unverified conversational claim.

Return ONLY this YAML-like block:

run_id: {RUN_ID}
task_id: HANDOFF-PIPELINE-REFACTOR-A1
overall_judgment: accepted | accepted_with_limitation | blocked | review_unverified
safety_verdict: pass | fail | review_unverified
source_of_truth_verdict: pass | fail | review_unverified
stale_check_verdict: pass | fail | review_unverified
legacy_handoff_verdict: pass | fail | review_unverified
minimax_m3_observation_verdict: pass | fail | review_unverified
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
  task_id: GENERATE-APPROVED-HANDOFF-A1
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
    return "closure-pack.zip" in lowered or "closure-pack" in lowered


async def find_editor(page):
    selectors = [
        'div[contenteditable="true"].ProseMirror',
        'div[contenteditable="true"]',
        'textarea',
    ]
    for sel in selectors:
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
    selectors = [
        'button[data-testid="send-button"]',
        'button[aria-label="Send prompt"]',
        'button[aria-label="Send message"]',
        'button[aria-label*="Send"]',
        'button:has-text("Send")',
        'button.composer-submit-button-color',
        'button:has-text("发送")',
    ]
    errors = []
    for sel in selectors:
        try:
            loc = page.locator(sel)
            count = await loc.count()
            for i in range(count):
                btn = loc.nth(i)
                if await btn.is_visible(timeout=1000) and await btn.is_enabled(timeout=1000):
                    await btn.click(timeout=10000)
                    return {"ok": True, "selector": sel, "index": i}
        except Exception as exc:
            errors.append(f"{sel}: {exc!r}")
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
    # First try visible/hidden file inputs.
    inputs = page.locator('input[type="file"]')
    count = await inputs.count()
    for i in range(count):
        try:
            await inputs.nth(i).set_input_files(str(PACK))
            await asyncio.sleep(8)
            body_text = await page.locator("body").inner_text(timeout=10000)
            if page_has_attachment_text(body_text):
                return {"ok": True, "method": f"input[{i}]", "body_excerpt": body_text[:2000]}
        except Exception as exc:
            errors.append(f"input[{i}]: {exc!r}")

    # Try clicking attach buttons then setting any newly available input.
    for label in ["Attach", "Upload", "Add photos and files", "附件", "上传", "+"]:
        try:
            button = page.get_by_label(label)
            if await button.count() > 0:
                await button.first.click(timeout=5000)
                await asyncio.sleep(1)
                inputs = page.locator('input[type="file"]')
                count = await inputs.count()
                for i in range(count):
                    try:
                        await inputs.nth(i).set_input_files(str(PACK))
                        await asyncio.sleep(8)
                        body_text = await page.locator("body").inner_text(timeout=10000)
                        if page_has_attachment_text(body_text):
                            return {"ok": True, "method": f"label:{label}/input[{i}]", "body_excerpt": body_text[:2000]}
                    except Exception as exc:
                        errors.append(f"label {label} input[{i}]: {exc!r}")
        except Exception as exc:
            errors.append(f"label {label}: {exc!r}")

    body_text = await page.locator("body").inner_text(timeout=10000)
    return {"ok": False, "errors": errors, "body_excerpt": body_text[:3000]}


async def main():
    status = {
        "run_id": RUN_ID,
        "pack": str(PACK),
        "pack_exists": PACK.exists(),
        "pack_size": PACK.stat().st_size if PACK.exists() else None,
        "pack_sha256": hashlib.sha256(PACK.read_bytes()).hexdigest() if PACK.exists() else None,
        "sent": False,
        "captured": False,
        "upload_confirmed": False,
    }
    async with async_playwright() as pw:
        browser = await pw.chromium.connect_over_cdp("http://localhost:9222")
        ctx = browser.contexts[0] if browser.contexts else await browser.new_context()
        page = await ctx.new_page()
        await page.goto("https://chatgpt.com/", wait_until="domcontentloaded", timeout=60000)
        await page.bring_to_front()
        await asyncio.sleep(5)
        CHAT_URL_OUT.write_text(page.url + "\n", encoding="utf-8")
        status["chat_url_initial"] = page.url
        clear_result = await clear_composer(page)
        status["clear_composer_before_upload"] = clear_result

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
            print(json.dumps(status, ensure_ascii=False, indent=2))
            return

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
            print(json.dumps(status, ensure_ascii=False, indent=2))
            return

        before_user_count = await page.locator('[data-message-author-role="user"]').count()
        before_assistant_count = await page.locator('[data-message-author-role="assistant"]').count()
        send_click = await click_visible_send_button(page)
        status["send_click"] = send_click
        if not send_click.get("ok"):
            status["status"] = "manual_required"
            status["reason"] = "submit_button_not_found_or_not_clickable"
            STATUS_OUT.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
            print(json.dumps(status, ensure_ascii=False, indent=2))
            return

        send_confirm = await confirm_message_sent(page, before_user_count, before_assistant_count)
        status["send_confirm"] = send_confirm
        if not send_confirm.get("ok"):
            status["status"] = "manual_required"
            status["reason"] = "submit_button_clicked_but_send_not_confirmed"
            STATUS_OUT.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
            print(json.dumps(status, ensure_ascii=False, indent=2))
            return

        status["sent"] = True
        status["sent_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        STATUS_OUT.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")

        last = ""
        stable = 0
        for _ in range(120):
            await asyncio.sleep(5)
            if page.url != status.get("chat_url_final"):
                status["chat_url_final"] = page.url
                CHAT_URL_OUT.write_text(page.url + "\n", encoding="utf-8")
            msgs = page.locator('[data-message-author-role="assistant"]')
            if await msgs.count() == 0:
                continue
            reply = await msgs.last.inner_text(timeout=10000)
            if reply == last:
                stable += 1
            else:
                stable = 0
                last = reply
            if RUN_ID in reply and "END_OF_GPT_RESPONSE" in reply and "overall_judgment:" in reply:
                break
            if stable >= 12 and len(reply) > 300:
                break

        reply = last
        RESULT_OUT.write_text(reply, encoding="utf-8")
        REPORT_RESULT_OUT.write_text(reply, encoding="utf-8")
        status.update({
            "captured": bool(reply),
            "reply_chars": len(reply),
            "reply_sha256": hashlib.sha256(reply.encode("utf-8")).hexdigest() if reply else None,
            "run_id_match": RUN_ID in reply,
            "has_end_marker": "END_OF_GPT_RESPONSE" in reply,
            "has_overall_judgment": "overall_judgment:" in reply,
            "parsed_overall_judgment": parse_judgment(reply),
            "chat_url_final": page.url,
            "result_path": str(RESULT_OUT),
            "report_result_path": str(REPORT_RESULT_OUT),
        })
        CHAT_URL_OUT.write_text(page.url + "\n", encoding="utf-8")
        STATUS_OUT.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(status, ensure_ascii=False, indent=2))

asyncio.run(main())
