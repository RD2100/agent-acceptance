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
CHAT_URL = (ROOT / "_reports/global-project-handoff-repair-a1/GPT_REVIEW_CHAT_URL.txt").read_text(encoding="utf-8").strip()
RESULT_OUT = ROOT / "evidence_packs/global-project-handoff-repair-a1/GPT_REVIEW_RESULT.txt"
REPORT_RESULT_OUT = ROOT / "_reports/global-project-handoff-repair-a1/GPT_REVIEW_RESULT.txt"
STATUS_OUT = ROOT / "_reports/global-project-handoff-repair-a1/GPT_REVIEW_FOLLOWUP_STATUS.json"

PROMPT = f"""请对我刚才上传的 GLOBAL_PROJECT_HANDOFF_REPAIR_A1_20260608_223800.zip 做结构化审查。刚才你回复了流程原则，但没有给出本次 run_id 的 verdict。

本次 run_id: {RUN_ID}
任务: GLOBAL-PROJECT-HANDOFF-REPAIR-A1

请只返回下面 YAML 块，不要解释。必须包含同一个 run_id 和 END_OF_GPT_RESPONSE。
如果你没有看到或无法读取刚才上传的 ZIP，请返回 overall_judgment: review_unverified。

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

async def find_editor(page):
    for sel in ['div[contenteditable="true"].ProseMirror', 'div[contenteditable="true"]', 'textarea']:
        loc = page.locator(sel)
        if await loc.count() > 0:
            return loc.last
    raise RuntimeError("editor not found")

async def click_visible_send_button(page):
    for sel in ['button[data-testid="send-button"]', '#composer-submit-button', 'button.composer-submit-button-color']:
        loc = page.locator(sel)
        for i in range(await loc.count()):
            btn = loc.nth(i)
            try:
                if await btn.is_visible(timeout=1000) and await btn.is_enabled(timeout=1000):
                    await btn.click(timeout=10000)
                    return {"ok": True, "selector": sel, "index": i}
            except Exception:
                pass
    js_result = await page.evaluate('''() => { const b=document.querySelector('button[data-testid="send-button"], #composer-submit-button, button.composer-submit-button-color'); if(!b) return {ok:false}; b.click(); return {ok:true, method:'js_click'}; }''')
    return js_result

async def main():
    status = {"run_id": RUN_ID, "chat_url": CHAT_URL, "sent": False, "captured": False}
    async with async_playwright() as pw:
        browser = await pw.chromium.connect_over_cdp("http://localhost:9222")
        ctx = browser.contexts[0]
        page = None
        for pg in ctx.pages:
            if CHAT_URL in pg.url:
                page = pg
                break
        if page is None:
            page = await ctx.new_page()
            await page.goto(CHAT_URL, wait_until="domcontentloaded", timeout=60000)
        await page.bring_to_front(); await asyncio.sleep(1)
        pyperclip.copy(PROMPT)
        editor = await find_editor(page)
        await editor.click(timeout=15000)
        await page.keyboard.press("Control+A")
        await page.keyboard.press("Backspace")
        await page.keyboard.press("Control+v")
        await asyncio.sleep(1)
        before_user = await page.locator('[data-message-author-role="user"]').count()
        before_asst = await page.locator('[data-message-author-role="assistant"]').count()
        click = await click_visible_send_button(page)
        status["send_click"] = click
        if not click.get("ok"):
            status["status"] = "manual_required"; status["reason"] = "submit_button_not_clickable"
            STATUS_OUT.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8"); print(json.dumps(status, ensure_ascii=False, indent=2)); return
        sent_ok = False
        for _ in range(24):
            await asyncio.sleep(1)
            if await page.locator('[data-message-author-role="user"]').count() > before_user or await page.locator('[data-message-author-role="assistant"]').count() > before_asst:
                sent_ok = True; break
        status["sent"] = sent_ok
        if not sent_ok:
            status["status"] = "manual_required"; status["reason"] = "send_not_confirmed"
            STATUS_OUT.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8"); print(json.dumps(status, ensure_ascii=False, indent=2)); return
        last = ""; stable = 0
        for _ in range(96):
            await asyncio.sleep(5)
            msgs = page.locator('[data-message-author-role="assistant"]')
            if await msgs.count() == 0: continue
            reply = await msgs.last.inner_text(timeout=10000)
            if reply == last: stable += 1
            else: stable = 0; last = reply
            if RUN_ID in reply and "END_OF_GPT_RESPONSE" in reply and "overall_judgment:" in reply: break
            if stable >= 10 and len(reply) > 300: break
        reply = last
        RESULT_OUT.write_text(reply, encoding="utf-8")
        REPORT_RESULT_OUT.write_text(reply, encoding="utf-8")
        status.update({"captured": bool(reply), "reply_chars": len(reply), "reply_sha256": hashlib.sha256(reply.encode('utf-8')).hexdigest() if reply else None, "run_id_match": RUN_ID in reply, "has_end_marker": "END_OF_GPT_RESPONSE" in reply, "has_overall_judgment": "overall_judgment:" in reply, "parsed_overall_judgment": parse_judgment(reply), "result_path": str(RESULT_OUT)})
        STATUS_OUT.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(status, ensure_ascii=False, indent=2))

asyncio.run(main())
