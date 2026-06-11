import asyncio, hashlib, json, re, time
from pathlib import Path
import pyperclip
from playwright.async_api import async_playwright
ROOT=Path('D:/agent-acceptance')
TASK_ID='GLOBAL-PROJECT-EVIDENCE-BINDING-A1-R2'
RUN_ID=(ROOT/'_reports/global-project-evidence-binding-a1-r2/GPT_REVIEW_RUN_ID.txt').read_text(encoding='utf-8').strip()
PACK=ROOT/'evidence_packs/global-project-evidence-binding-a1-r2/GLOBAL_PROJECT_EVIDENCE_BINDING_A1_R2_20260609_085323.zip'
URL='https://chatgpt.com/c/6a26cc03-235c-83a2-a0fc-cd29be615959'
CDP='http://127.0.0.1:9223'
STATUS=ROOT/'_reports/global-project-evidence-binding-a1-r2/GPT_REVIEW_SUBMISSION_STATUS.json'
RESULT=ROOT/'_reports/global-project-evidence-binding-a1-r2/GPT_REVIEW_RESULT.txt'
PACK_RESULT=ROOT/'evidence_packs/global-project-evidence-binding-a1-r2/GPT_REVIEW_RESULT.txt'
SHOT=ROOT/'_reports/global-project-evidence-binding-a1-r2/GPT_REVIEW_UPLOAD_CONFIRMATION.png'
PROMPT=f'''GPT 审查请求：GLOBAL-PROJECT-EVIDENCE-BINDING-A1-R2

run_id: {RUN_ID}

请审查附件 R2 evidence pack。请重点判断：
1. 是否正确承认 `HANDOFF_REPLY_V4.txt` 仍是 `tracked_deleted_human_required`，而不是伪装成 resolved/pass。
2. safety attestation 是否已与 git evidence 一致，不再声称所有 legacy 文件都未删除。
3. source binding / manifest 是否一致；若声明嵌入旧 closure ZIP，pack 和 manifest 中是否确实存在。
4. 是否保留 whole-project/global status partial / needs_more_evidence、production promotion 未批准、296 PASS 未验证。
5. 是否未执行 git restore / checkout / reset / clean，未删除/移动/重命名/覆盖 legacy 文件。

如果附件不可检查，请返回 review_unverified。
请只返回以下结构，字段名保持英文以便 verifier 解析，内容用中文：

run_id: {RUN_ID}
task_id: {TASK_ID}
overall_judgment: accepted | accepted_with_limitation | blocked | review_unverified
evidence_pack_reviewed: true | false
attachment_reviewed: true | false
blocking_issues:
  - <问题或 none>
required_fixes:
  - <修复或 none>
limitations:
  - <限制或 none>
next_task_authorization:
  task_id: <下个任务或 none>
  authorized: 已授权 | 未授权
  execute_immediately: 是 | 否
  ask_before_starting: 是 | 否
END_OF_GPT_RESPONSE
'''
def parse(t):
 m=re.search(r'overall_judgment:\s*([^\s]+)',t,re.I); return m.group(1).strip().lower() if m else None
def has_attach(t):
 x=t.lower(); return 'global_project_evidence_binding_a1_r2' in x or 'global-project-evidence-binding-a1-r2' in x or 'a1_r2' in x
async def editor(page):
 for sel in ['div[contenteditable="true"].ProseMirror','div[contenteditable="true"]','textarea']:
  loc=page.locator(sel)
  if await loc.count()>0: return loc.last
 raise RuntimeError('editor not found')
async def send_btn(page):
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
 status={'run_id':RUN_ID,'task_id':TASK_ID,'target_url':URL,'pack':str(PACK),'pack_exists':PACK.exists(),'pack_sha256':hashlib.sha256(PACK.read_bytes()).hexdigest() if PACK.exists() else None,'sent':False,'captured':False}
 async with async_playwright() as pw:
  browser=await pw.chromium.connect_over_cdp(CDP)
  ctx=browser.contexts[0] if browser.contexts else await browser.new_context()
  page=None
  for pg in ctx.pages:
   if URL in pg.url: page=pg; break
  if page is None:
   page=await ctx.new_page(); await page.goto(URL, wait_until='domcontentloaded', timeout=60000)
  await page.bring_to_front(); await asyncio.sleep(5)
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
  bu=await page.locator('[data-message-author-role="user"]').count(); ba=await page.locator('[data-message-author-role="assistant"]').count()
  click=await send_btn(page); status['send_click']=click
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
  RESULT.write_text(reply,encoding='utf-8'); PACK_RESULT.write_text(reply,encoding='utf-8')
  status.update({'captured':bool(reply),'reply_chars':len(reply),'reply_sha256':hashlib.sha256(reply.encode('utf-8')).hexdigest() if reply else None,'run_id_match':RUN_ID in reply,'has_end_marker':'END_OF_GPT_RESPONSE' in reply,'has_overall_judgment':'overall_judgment:' in reply,'parsed_overall_judgment':parse(reply),'chat_url_final':page.url,'result_path':str(RESULT)})
  STATUS.write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(status,ensure_ascii=False,indent=2))
asyncio.run(main())
