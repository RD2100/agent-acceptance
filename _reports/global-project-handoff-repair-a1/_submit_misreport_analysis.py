import asyncio
import hashlib
import json
import re
import time
from pathlib import Path

import pyperclip
from playwright.async_api import async_playwright

ROOT = Path("D:/agent-acceptance")
RUN_ID = (ROOT / "_reports/global-project-handoff-repair-a1/MISREPORT_ANALYSIS_RUN_ID.txt").read_text(encoding="utf-8").strip()
CHAT_URL = "https://chatgpt.com/c/6a26cc03-235c-83a2-a0fc-cd29be615959"
RESULT_OUT = ROOT / "_reports/global-project-handoff-repair-a1/MISREPORT_ANALYSIS_GPT_REPLY.txt"
STATUS_OUT = ROOT / "_reports/global-project-handoff-repair-a1/MISREPORT_ANALYSIS_SUBMISSION_STATUS.json"

PROMPT = f"""GPT ANALYSIS REQUEST: LOCAL CAPTURE / REPORTING MISJUDGMENT

run_id: {RUN_ID}

task_id: MISREPORT-ANALYSIS-A1

Context:
A coding agent submitted GLOBAL-PROJECT-HANDOFF-REPAIR-A1 for GPT review. The visible GPT reply included a valid structured verdict:

run_id: GLOBAL_HANDOFF_REPAIR_REVIEW_20260608_225353_EEUAEQ
task_id: GLOBAL-PROJECT-HANDOFF-REPAIR-A1
overall_judgment: accepted_with_limitation
safety_verdict: pass
source_of_truth_verdict: pass
whole_project_handoff_verdict: pass
stale_claims_verdict: pass
test_ledger_verdict: pass
evidence_pack_reviewed: true
attachment_reviewed: true
blocking_issues:
- none
required_fixes:
- Include explicit git status / changed-files evidence in the next closure pack to independently verify that no legacy PROJECT_HISTORY / HANDOFF / PASTE_BLOCK files were deleted, moved, renamed, or rewritten.
limitations:
- Whole-project/global status is correctly marked partial / needs_more_evidence, not fully closed.
- Production promotion is not proven by current P0/P1 evidence and must not be claimed.
- 296 PASS remains an unverified conversational claim and is not promoted to source-of-truth.
- 12 passed vs 13 passed is preserved as a nonblocking limitation.
- Source-of-truth map references several external repo evidence files by path and hash, but not all underlying historical evidence files are embedded in this ZIP.
- Safety scan passed and no sensitive paper text/tokens/secrets were evident in the reviewed pack, but the included scanner report checked 6 selected files rather than every file in the ZIP.
next_allowed_action: Use this accepted_with_limitation whole-project handoff repair layer as the current global status layer, then run a targeted evidence-binding pass to attach missing underlying P0/P1 evidence and git status/change-proof before any production-promotion review.
next_task_authorization:
task_id: GLOBAL-PROJECT-EVIDENCE-BINDING-A1
authorized: 已授权
execute_immediately: 是
ask_before_starting: 否
END_OF_GPT_RESPONSE

But the local coding agent mistakenly reported that the first GPT answer did not provide a valid run_id verdict, likely because its local CDP capture read an older/non-target assistant message or the agent interpreted the capture file incorrectly.

Please analyze:
1. Why this kind of false belief / misreport can happen in browser-CDP GPT review flows.
2. Which controls were missing or insufficient.
3. How to fix the local capture/reporting workflow so the agent does not misreport visible GPT verdicts again.
4. What should be added to evidence pack / execution report / observation log.
5. A concrete checklist for future GPT review capture.

Return ONLY this YAML-like block:

run_id: {RUN_ID}
task_id: MISREPORT-ANALYSIS-A1
overall_judgment: analyzed
root_causes:
  - <cause>
missing_controls:
  - <control>
required_fixes:
  - <fix>
future_capture_checklist:
  - <check>
observation_log_update:
  - <entry>
END_OF_GPT_RESPONSE
"""

def parse_judgment(text):
    m = re.search(r"overall_judgment:\s*([^\s]+)", text, re.I)
    return m.group(1).strip().lower() if m else None

async def find_editor(page):
    for sel in ['div[contenteditable="true"].ProseMirror','div[contenteditable="true"]','textarea']:
        loc=page.locator(sel)
        if await loc.count()>0:
            return loc.last
    raise RuntimeError('editor not found')

async def click_send(page):
    for sel in ['button[data-testid="send-button"]','#composer-submit-button','button.composer-submit-button-color']:
        loc=page.locator(sel)
        for i in range(await loc.count()):
            btn=loc.nth(i)
            try:
                if await btn.is_visible(timeout=1000) and await btn.is_enabled(timeout=1000):
                    await btn.click(timeout=10000)
                    return {'ok':True,'selector':sel,'index':i}
            except Exception:
                pass
    js=await page.evaluate('''() => { const b=document.querySelector('button[data-testid="send-button"], #composer-submit-button, button.composer-submit-button-color'); if(!b) return {ok:false}; b.click(); return {ok:true, method:'js_click'}; }''')
    return js

async def main():
    status={'run_id':RUN_ID,'chat_url':CHAT_URL,'sent':False,'captured':False}
    async with async_playwright() as pw:
        browser=await pw.chromium.connect_over_cdp('http://localhost:9222')
        ctx=browser.contexts[0]
        page=None
        for pg in ctx.pages:
            if CHAT_URL in pg.url:
                page=pg; break
        if page is None:
            page=await ctx.new_page(); await page.goto(CHAT_URL, wait_until='domcontentloaded', timeout=60000)
        await page.bring_to_front(); await asyncio.sleep(1)
        pyperclip.copy(PROMPT)
        editor=await find_editor(page)
        await editor.click(timeout=15000)
        await page.keyboard.press('Control+A'); await page.keyboard.press('Backspace'); await page.keyboard.press('Control+v')
        await asyncio.sleep(1)
        before_user=await page.locator('[data-message-author-role="user"]').count()
        before_asst=await page.locator('[data-message-author-role="assistant"]').count()
        click=await click_send(page); status['send_click']=click
        if not click.get('ok'):
            status['status']='manual_required'; status['reason']='send_button_not_clickable'; STATUS_OUT.write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(status,ensure_ascii=False,indent=2)); return
        sent=False
        for _ in range(24):
            await asyncio.sleep(1)
            if await page.locator('[data-message-author-role="user"]').count() > before_user or await page.locator('[data-message-author-role="assistant"]').count() > before_asst:
                sent=True; break
        status['sent']=sent
        if not sent:
            status['status']='manual_required'; status['reason']='send_not_confirmed'; STATUS_OUT.write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(status,ensure_ascii=False,indent=2)); return
        last=''; stable=0
        for _ in range(96):
            await asyncio.sleep(5)
            msgs=page.locator('[data-message-author-role="assistant"]')
            if await msgs.count()==0: continue
            reply=await msgs.last.inner_text(timeout=10000)
            if reply==last: stable+=1
            else: stable=0; last=reply
            if RUN_ID in reply and 'END_OF_GPT_RESPONSE' in reply and 'overall_judgment:' in reply: break
            if stable>=10 and len(reply)>300: break
        RESULT_OUT.write_text(last, encoding='utf-8')
        status.update({'captured':bool(last),'reply_chars':len(last),'reply_sha256':hashlib.sha256(last.encode('utf-8')).hexdigest() if last else None,'run_id_match':RUN_ID in last,'has_end_marker':'END_OF_GPT_RESPONSE' in last,'has_overall_judgment':'overall_judgment:' in last,'parsed_overall_judgment':parse_judgment(last),'result_path':str(RESULT_OUT)})
        STATUS_OUT.write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(status,ensure_ascii=False,indent=2))

asyncio.run(main())
