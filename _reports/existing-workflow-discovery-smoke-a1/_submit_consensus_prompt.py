import asyncio
import hashlib
import json
import re
import time
from pathlib import Path

import pyperclip
from playwright.async_api import async_playwright

ROOT = Path('D:/agent-acceptance')
RUN_ID = (ROOT / '_reports/existing-workflow-discovery-smoke-a1/GPT_CONSENSUS_RUN_ID.txt').read_text(encoding='utf-8').strip()
TASK_ID = 'NEXT-AGENT-WORKFLOW-BOOTSTRAP-CONSENSUS-A1'
PROMPT = (ROOT / '_reports/existing-workflow-discovery-smoke-a1/GPT_CONSENSUS_PROMPT.md').read_text(encoding='utf-8')
URL = (ROOT / '_reports/existing-workflow-discovery-smoke-a1/GPT_REVIEW_CHAT_URL.txt').read_text(encoding='utf-8').strip()
STATUS = ROOT / '_reports/existing-workflow-discovery-smoke-a1/GPT_CONSENSUS_SUBMISSION_STATUS.json'
RESULT = ROOT / '_reports/existing-workflow-discovery-smoke-a1/GPT_CONSENSUS_RESULT.txt'


def parse_judgment(text):
    m = re.search(r'overall_judgment:\s*([^\s]+)', text, re.I)
    return m.group(1).strip().lower() if m else None


async def find_editor(page):
    for sel in ['div[contenteditable="true"].ProseMirror', 'div[contenteditable="true"]', 'textarea']:
        loc = page.locator(sel)
        if await loc.count() > 0:
            return loc.last
    raise RuntimeError('editor not found')


async def clear_composer(page):
    editor = await find_editor(page)
    await editor.click(timeout=10000)
    await page.keyboard.press('Control+A')
    await page.keyboard.press('Backspace')
    await asyncio.sleep(0.5)


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
                    return {'ok': True, 'selector': sel, 'index': i}
        except Exception as exc:
            errors.append(f'{sel}: {exc!r}')
    return {'ok': False, 'errors': errors}


async def confirm_sent(page, before_user, before_assistant):
    checks = []
    for _ in range(30):
        await asyncio.sleep(1)
        user = await page.locator('[data-message-author-role="user"]').count()
        assistant = await page.locator('[data-message-author-role="assistant"]').count()
        checks.append({'user_count': user, 'assistant_count': assistant, 'url': page.url})
        if user > before_user:
            return {'ok': True, 'reason': 'user_message_bubble_appeared', 'checks': checks[-5:]}
        if assistant > before_assistant:
            return {'ok': True, 'reason': 'assistant_response_started', 'checks': checks[-5:]}
    return {'ok': False, 'reason': 'not_confirmed', 'checks': checks[-5:]}


async def main():
    status = {'run_id': RUN_ID, 'task_id': TASK_ID, 'target_url': URL, 'sent': False, 'captured': False}
    async with async_playwright() as pw:
        browser = await pw.chromium.connect_over_cdp('http://localhost:9222')
        ctx = browser.contexts[0] if browser.contexts else await browser.new_context()
        page = None
        for pg in ctx.pages:
            if URL in pg.url:
                page = pg
                break
        if page is None:
            page = await ctx.new_page()
            await page.goto(URL, wait_until='domcontentloaded', timeout=60000)
        await page.bring_to_front()
        await asyncio.sleep(3)
        await clear_composer(page)
        pyperclip.copy(PROMPT)
        editor = await find_editor(page)
        await editor.click(timeout=30000)
        await page.keyboard.press('Control+v')
        await asyncio.sleep(1)
        before_user = await page.locator('[data-message-author-role="user"]').count()
        before_assistant = await page.locator('[data-message-author-role="assistant"]').count()
        click = await click_visible_send_button(page)
        status['send_click'] = click
        if not click.get('ok'):
            status['status'] = 'manual_required'
            status['reason'] = 'send_button_not_clicked'
            STATUS.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding='utf-8')
            print(json.dumps(status, ensure_ascii=False, indent=2)); return
        confirm = await confirm_sent(page, before_user, before_assistant)
        status['send_confirm'] = confirm
        if not confirm.get('ok'):
            status['status'] = 'manual_required'
            status['reason'] = 'send_not_confirmed'
            STATUS.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding='utf-8')
            print(json.dumps(status, ensure_ascii=False, indent=2)); return
        status['sent'] = True
        status['sent_at'] = time.strftime('%Y-%m-%dT%H:%M:%S')
        STATUS.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding='utf-8')
        target = ''
        last = ''
        stable = 0
        for _ in range(120):
            await asyncio.sleep(5)
            msgs = page.locator('[data-message-author-role="assistant"]')
            for i in range(await msgs.count()):
                txt = await msgs.nth(i).inner_text(timeout=10000)
                if RUN_ID in txt and 'overall_judgment:' in txt and 'END_OF_GPT_RESPONSE' in txt:
                    target = txt
            if target:
                break
            if await msgs.count() > 0:
                txt = await msgs.last.inner_text(timeout=10000)
                if txt == last:
                    stable += 1
                else:
                    last = txt
                    stable = 0
                if stable >= 12 and len(txt) > 300:
                    break
        reply = target or last
        RESULT.write_text(reply, encoding='utf-8')
        status.update({
            'captured': bool(reply),
            'reply_chars': len(reply),
            'reply_sha256': hashlib.sha256(reply.encode('utf-8')).hexdigest() if reply else None,
            'run_id_match': RUN_ID in reply,
            'has_end_marker': 'END_OF_GPT_RESPONSE' in reply,
            'has_overall_judgment': 'overall_judgment:' in reply,
            'parsed_overall_judgment': parse_judgment(reply),
            'chat_url_final': page.url,
            'result_path': str(RESULT),
        })
        STATUS.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps(status, ensure_ascii=False, indent=2))

asyncio.run(main())
