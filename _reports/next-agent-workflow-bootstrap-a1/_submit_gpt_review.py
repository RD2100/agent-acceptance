import asyncio, hashlib, json, re, time
from pathlib import Path
import pyperclip
from playwright.async_api import async_playwright
ROOT=Path('D:/agent-acceptance')
TASK_ID='NEXT-AGENT-WORKFLOW-BOOTSTRAP-IMPLEMENT-A1'
RUN_ID=(ROOT/'_reports/next-agent-workflow-bootstrap-a1/GPT_REVIEW_RUN_ID.txt').read_text(encoding='utf-8').strip()
URL=(ROOT/'_reports/next-agent-workflow-bootstrap-a1/GPT_REVIEW_CHAT_URL.txt').read_text(encoding='utf-8').strip()
PACK=ROOT/'evidence_packs/next-agent-workflow-bootstrap-a1/NEXT_AGENT_WORKFLOW_BOOTSTRAP_IMPLEMENT_A1_20260608_235642.zip'
STATUS=ROOT/'_reports/next-agent-workflow-bootstrap-a1/GPT_REVIEW_SUBMISSION_STATUS.json'
RESULT=ROOT/'_reports/next-agent-workflow-bootstrap-a1/GPT_REVIEW_RESULT.txt'
PACK_RESULT=ROOT/'evidence_packs/next-agent-workflow-bootstrap-a1/GPT_REVIEW_RESULT.txt'
SHOT=ROOT/'_reports/next-agent-workflow-bootstrap-a1/GPT_REVIEW_UPLOAD_CONFIRMATION.png'
PROMPT=f'''GPT REVIEW REQUEST: {TASK_ID}

run_id: {RUN_ID}

Please review the attached implementation pack. Verify that it creates a minimal repo-backed startup read gate for the next agent without redesigning the GPT-agent workflow.

Return ONLY:
run_id: {RUN_ID}
task_id: {TASK_ID}
overall_judgment: accepted | accepted_with_limitation | blocked | review_unverified
evidence_pack_reviewed: true | false
attachment_reviewed: true | false
blocking_issues:
  - <issue or none>
required_fixes:
  - <fix or none>
limitations:
  - <limitation or none>
next_task_authorization:
  task_id: GLOBAL-PROJECT-EVIDENCE-BINDING-A1-R2 | none
  authorized: 已授权 | 未授权
  execute_immediately: 是 | 否
  ask_before_starting: 是 | 否
END_OF_GPT_RESPONSE
'''
def parse(text):
    m=re.search(r'overall_judgment:\s*([^\s]+)',text,re.I); return m.group(1).strip().lower() if m else None
def has_attach(text):
    t=text.lower(); return 'next_agent_workflow_bootstrap' in t or 'next-agent-workflow-bootstrap' in t or 'bootstrap_implement' in t
async def editor(page):
    for sel in ['div[contenteditable="true"].ProseMirror','div[contenteditable="true"]','textarea']:
        loc=page.locator(sel)
        if await loc.count()>0: return loc.last
    raise RuntimeError('editor not found')
async def send_button(page):
    for sel in ['button[data-testid="send-button"]','#composer-submit-button','button.composer-submit-button-color','button[aria-label*="Send"]','button:has-text("Send")','button:has-text("发送")']:
        try:
            loc=page.locator(sel)
            for i in range(await loc.count()):
                b=loc.nth(i)
                if await b.is_visible(timeout=1000) and await b.is_enabled(timeout=1000):
                    await b.click(timeout=10000); return {'ok':True,'selector':sel,'index':i}
        except Exception: pass
    return {'ok':False}
async def main():
    status={'run_id':RUN_ID,'task_id':TASK_ID,'pack':str(PACK),'pack_exists':PACK.exists(),'pack_sha256':hashlib.sha256(PACK.read_bytes()).hexdigest() if PACK.exists() else None,'sent':False,'captured':False}
    async with async_playwright() as pw:
        browser=await pw.chromium.connect_over_cdp('http://localhost:9222')
        ctx=browser.contexts[0] if browser.contexts else await browser.new_context()
        page=None
        for pg in ctx.pages:
            if URL in pg.url: page=pg; break
        if page is None:
            page=await ctx.new_page(); await page.goto(URL, wait_until='domcontentloaded', timeout=60000)
        await page.bring_to_front(); await asyncio.sleep(3)
        ed=await editor(page); await ed.click(timeout=10000); await page.keyboard.press('Control+A'); await page.keyboard.press('Backspace')
        inputs=page.locator('input[type="file"]'); uploaded=False
        for i in range(await inputs.count()):
            try:
                await inputs.nth(i).set_input_files(str(PACK)); await asyncio.sleep(8)
                body=await page.locator('body').inner_text(timeout=10000)
                if has_attach(body): uploaded=True; status['upload_attempt']={'ok':True,'method':f'input[{i}]'}; break
            except Exception as e: status.setdefault('upload_errors',[]).append(repr(e))
        status['upload_confirmed']=uploaded
        await page.screenshot(path=str(SHOT), full_page=False)
        if not uploaded:
            status['status']='manual_required'; status['reason']='upload_not_confirmed'; STATUS.write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(status,ensure_ascii=False,indent=2)); return
        pyperclip.copy(PROMPT); ed=await editor(page); await ed.click(timeout=30000); await page.keyboard.press('Control+v'); await asyncio.sleep(1)
        before_u=await page.locator('[data-message-author-role="user"]').count(); before_a=await page.locator('[data-message-author-role="assistant"]').count()
        click=await send_button(page); status['send_click']=click
        if not click.get('ok'):
            status['status']='manual_required'; status['reason']='send_not_clicked'; STATUS.write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(status,ensure_ascii=False,indent=2)); return
        ok=False
        for _ in range(30):
            await asyncio.sleep(1); u=await page.locator('[data-message-author-role="user"]').count(); a=await page.locator('[data-message-author-role="assistant"]').count()
            if u>before_u or a>before_a: ok=True; break
        status['send_confirm']={'ok':ok,'user_count':u,'assistant_count':a}
        if not ok:
            status['status']='manual_required'; status['reason']='send_not_confirmed'; STATUS.write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(status,ensure_ascii=False,indent=2)); return
        status['sent']=True; status['sent_at']=time.strftime('%Y-%m-%dT%H:%M:%S'); STATUS.write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
        target=''; last=''; stable=0
        for _ in range(120):
            await asyncio.sleep(5); msgs=page.locator('[data-message-author-role="assistant"]')
            for i in range(await msgs.count()):
                txt=await msgs.nth(i).inner_text(timeout=10000)
                if RUN_ID in txt and 'overall_judgment:' in txt and 'END_OF_GPT_RESPONSE' in txt: target=txt
            if target: break
            if await msgs.count()>0:
                txt=await msgs.last.inner_text(timeout=10000)
                stable=stable+1 if txt==last else 0; last=txt
                if stable>=12 and len(txt)>300: break
        reply=target or last
        RESULT.write_text(reply,encoding='utf-8'); PACK_RESULT.write_text(reply,encoding='utf-8')
        status.update({'captured':bool(reply),'reply_chars':len(reply),'reply_sha256':hashlib.sha256(reply.encode('utf-8')).hexdigest() if reply else None,'run_id_match':RUN_ID in reply,'has_end_marker':'END_OF_GPT_RESPONSE' in reply,'has_overall_judgment':'overall_judgment:' in reply,'parsed_overall_judgment':parse(reply),'chat_url_final':page.url})
        STATUS.write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(status,ensure_ascii=False,indent=2))
asyncio.run(main())
