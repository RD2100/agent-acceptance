import asyncio, hashlib, json, re, time
from pathlib import Path
import pyperclip
from playwright.async_api import async_playwright
ROOT=Path('D:/agent-acceptance')
TASK_ID='HANDOFF-REPLY-V4-RESTORE-SCOPE-CONSULT-A1'
RUN_ID=(ROOT/'_reports/global-project-evidence-binding-a1-r2/GPT_HANDOFF_REPLY_V4_CONSULT_RUN_ID.txt').read_text(encoding='utf-8').strip()
PROMPT=(ROOT/'_reports/global-project-evidence-binding-a1-r2/GPT_HANDOFF_REPLY_V4_CONSULT_PROMPT.md').read_text(encoding='utf-8')
URL='https://chatgpt.com/c/6a26cc03-235c-83a2-a0fc-cd29be615959'
CDP_URL='http://127.0.0.1:9223'
STATUS=ROOT/'_reports/global-project-evidence-binding-a1-r2/GPT_HANDOFF_REPLY_V4_CONSULT_SUBMISSION_STATUS.json'
RESULT=ROOT/'_reports/global-project-evidence-binding-a1-r2/GPT_HANDOFF_REPLY_V4_CONSULT_RESULT.txt'
def parse(t):
    m=re.search(r'overall_judgment:\s*([^\s]+)',t,re.I); return m.group(1).strip().lower() if m else None
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
    status={'run_id':RUN_ID,'task_id':TASK_ID,'target_url':URL,'sent':False,'captured':False}
    async with async_playwright() as pw:
        browser=await pw.chromium.connect_over_cdp(CDP_URL)
        ctx=browser.contexts[0] if browser.contexts else await browser.new_context()
        page=None
        for pg in ctx.pages:
            if URL in pg.url:
                page=pg
                break
        if page is None:
            page=await ctx.new_page()
            await page.goto(URL, wait_until='domcontentloaded', timeout=60000)
        await page.bring_to_front(); await asyncio.sleep(5)
        ed=await editor(page); await ed.click(timeout=10000); await page.keyboard.press('Control+A'); await page.keyboard.press('Backspace')
        pyperclip.copy(PROMPT); await ed.click(timeout=10000); await page.keyboard.press('Control+v'); await asyncio.sleep(1)
        bu=await page.locator('[data-message-author-role="user"]').count(); ba=await page.locator('[data-message-author-role="assistant"]').count()
        click=await send_button(page); status['send_click']=click
        if not click.get('ok'):
            status['status']='manual_required'; status['reason']='send_not_clicked'; STATUS.write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(status,ensure_ascii=False,indent=2)); return
        ok=False
        for _ in range(30):
            await asyncio.sleep(1); u=await page.locator('[data-message-author-role="user"]').count(); a=await page.locator('[data-message-author-role="assistant"]').count()
            if u>bu or a>ba: ok=True; break
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
                txt=await msgs.last.inner_text(timeout=10000); stable=stable+1 if txt==last else 0; last=txt
                if stable>=12 and len(txt)>300: break
        reply=target or last
        RESULT.write_text(reply,encoding='utf-8')
        status.update({'captured':bool(reply),'reply_chars':len(reply),'reply_sha256':hashlib.sha256(reply.encode('utf-8')).hexdigest() if reply else None,'run_id_match':RUN_ID in reply,'has_end_marker':'END_OF_GPT_RESPONSE' in reply,'has_overall_judgment':'overall_judgment:' in reply,'parsed_overall_judgment':parse(reply),'chat_url_final':page.url,'result_path':str(RESULT)})
        STATUS.write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(status,ensure_ascii=False,indent=2))
asyncio.run(main())
