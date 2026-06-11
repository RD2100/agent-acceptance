#!/usr/bin/env python3
"""HANDOFF-WORKFLOW-HARDENING-PLAN-A1 GPT review submitter.

Based on: _reports/gpt-browser-submit-guide.md (project-standard workflow)
Template: _reports/global-project-evidence-binding-a1/_submit_gpt_review.py

Steps (per runbook):
1. Connect CDP at 127.0.0.1:9222
2. New ChatGPT page (Scenario B: independent evidence pack review)
3. Clear composer
4. Upload evidence pack ZIP
5. Paste prompt (Chinese, with run_id + END_OF_GPT_RESPONSE)
6. Click visible send button (NOT Control+Enter)
7. Confirm user bubble or assistant response
8. Capture reply matching this run_id
9. Save to GPT_REVIEW_RESULT.txt
"""

import asyncio
import hashlib
import json
import re
import time
from pathlib import Path

import pyperclip
from playwright.async_api import async_playwright

ROOT = Path('D:/agent-acceptance')
TASK_ID = 'HANDOFF-WORKFLOW-HARDENING-PLAN-A1'
RUN_ID = 'HANDOFF_WORKFLOW_HARDENING_PLAN_A1_REVIEW_20260609_012328_RD'
PACK = ROOT / 'evidence_packs/handoff-workflow-hardening-plan-a1/HANDOFF_WORKFLOW_HARDENING_PLAN_A1_20260609T013519.zip'

REPORT_DIR = ROOT / '_reports/handoff-workflow-hardening-plan-a1'
PACK_DIR = ROOT / 'evidence_packs/handoff-workflow-hardening-plan-a1'

# 延续性项目上下文对话（from handoff doc section 三）
TARGET_URL = 'https://chatgpt.com/c/6a26cc03-235c-83a2-a0fc-cd29be615959'

CHAT_URL_OUT = REPORT_DIR / 'GPT_REVIEW_CHAT_URL.txt'
STATUS_OUT = REPORT_DIR / 'GPT_REVIEW_SUBMISSION_STATUS.json'
SCREENSHOT_OUT = REPORT_DIR / 'GPT_REVIEW_UPLOAD_CONFIRMATION.png'
RESULT_OUT = PACK_DIR / 'GPT_REVIEW_RESULT.txt'
REPORT_RESULT_OUT = REPORT_DIR / 'GPT_REVIEW_RESULT.txt'

PROMPT = f"""GPT REVIEW REQUEST: HANDOFF-WORKFLOW-HARDENING-PLAN-A1

run_id: {RUN_ID}

请审查附件 evidence pack。该任务目标是基于现有仓库 workflow 和最近 GPT verdict，形成 GPT-agent 自动化交接流程的硬化计划，而不是重新设计或直接实现所有机制。

请重点判断：

1. 是否复用了仓库已有 workflow / source-of-truth / verifier / runbook / evidence pack 结构；
2. 是否没有重新发明一套 GPT-agent 流程；
3. 是否准确识别流程完整度缺口；
4. 是否保留 accepted_with_limitation / blocked / partial / needs_more_evidence / human_required 语义；
5. 是否没有修改 legacy PROJECT_HISTORY / HANDOFF / PASTE_BLOCK；
6. 是否没有执行 git reset / clean / checkout / restore / commit / push；
7. 是否给出后续可执行的最小任务路线。

如果附件不可检查，请返回 review_unverified。

请只返回：

run_id: {RUN_ID}
task_id: HANDOFF-WORKFLOW-HARDENING-PLAN-A1
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
"""


def parse_judgment(text):
    m = re.search(r'overall_judgment:\s*([^\s]+)', text, re.I)
    return m.group(1).strip().lower() if m else None


def page_has_attachment_text(text):
    lowered = text.lower()
    return ('handoff-workflow-hardening-plan' in lowered
            or 'hardening-plan-a1' in lowered
            or 'hardening_plan' in lowered)


async def find_editor(page):
    for sel in ['div[contenteditable="true"].ProseMirror', 'div[contenteditable="true"]', 'textarea']:
        loc = page.locator(sel)
        if await loc.count() > 0:
            return loc.last
    raise RuntimeError('editor not found')


async def clear_composer(page):
    try:
        editor = await find_editor(page)
        await editor.click(timeout=10000)
        await page.keyboard.press('Control+A')
        await page.keyboard.press('Backspace')
        await asyncio.sleep(0.5)
        return {'ok': True}
    except Exception as exc:
        return {'ok': False, 'error': repr(exc)}


async def click_visible_send_button(page):
    selectors = [
        'button[data-testid="send-button"]',
        '#composer-submit-button',
        'button.composer-submit-button-color',
        'button[aria-label="Send prompt"]',
        'button[aria-label="Send message"]',
        'button[aria-label*="Send"]',
        'button:has-text("Send")',
        'button:has-text("发送")',
    ]
    errors = []
    for sel in selectors:
        try:
            loc = page.locator(sel)
            for i in range(await loc.count()):
                btn = loc.nth(i)
                if await btn.is_visible(timeout=1000) and await btn.is_enabled(timeout=1000):
                    await btn.click(timeout=10000)
                    return {'ok': True, 'selector': sel, 'index': i, 'method': 'locator_click'}
        except Exception as exc:
            errors.append(f'{sel}: {exc!r}')
    # JS fallback
    try:
        js_result = await page.evaluate('''() => {
            const candidates = Array.from(document.querySelectorAll('button')).filter(b => {
                const r = b.getBoundingClientRect();
                const label = (b.getAttribute('aria-label') || '') + ' ' +
                              (b.getAttribute('data-testid') || '') + ' ' + b.className;
                return r.width > 0 && r.height > 0 && !b.disabled &&
                       /send-button|composer-submit|发送|Send/i.test(label);
            });
            const b = candidates[candidates.length - 1];
            if (!b) return {ok: false, reason: 'no_candidate'};
            b.click();
            const r = b.getBoundingClientRect();
            return {ok: true, method: 'js_click', x: r.x, y: r.y,
                    label: b.getAttribute('aria-label'),
                    testid: b.getAttribute('data-testid'), cls: b.className};
        }''')
        if js_result.get('ok'):
            return js_result
        errors.append(f'js_fallback: {js_result}')
    except Exception as exc:
        errors.append(f'js_fallback: {exc!r}')
    return {'ok': False, 'errors': errors}


async def confirm_message_sent(page, before_user_count, before_assistant_count):
    checks = []
    for _ in range(24):
        await asyncio.sleep(1)
        user_count = await page.locator('[data-message-author-role="user"]').count()
        assistant_count = await page.locator('[data-message-author-role="assistant"]').count()
        editor_text = ''
        try:
            editor = await find_editor(page)
            editor_text = (await editor.inner_text(timeout=2000)).strip()
        except Exception:
            pass
        checks.append({
            'user_count': user_count,
            'assistant_count': assistant_count,
            'editor_chars': len(editor_text),
            'url': page.url,
        })
        if user_count > before_user_count:
            return {'ok': True, 'reason': 'user_message_bubble_appeared', 'checks': checks[-5:]}
        if assistant_count > before_assistant_count and user_count >= before_user_count:
            return {'ok': True, 'reason': 'assistant_response_started', 'checks': checks[-5:]}
    return {'ok': False, 'reason': 'no_user_bubble_or_assistant_response_after_click',
            'checks': checks[-5:]}


async def try_upload(page):
    errors = []
    # Try existing file inputs
    inputs = page.locator('input[type="file"]')
    count = await inputs.count()
    for i in range(count):
        try:
            await inputs.nth(i).set_input_files(str(PACK))
            await asyncio.sleep(8)
            body_text = await page.locator('body').inner_text(timeout=10000)
            if page_has_attachment_text(body_text):
                return {'ok': True, 'method': f'input[{i}]',
                        'body_excerpt': body_text[:2000]}
        except Exception as exc:
            errors.append(f'input[{i}]: {exc!r}')

    # Try clicking attach buttons then setting newly available input
    for label in ['Attach', 'Upload', 'Add photos and files', '附件', '上传', '+']:
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
                        body_text = await page.locator('body').inner_text(timeout=10000)
                        if page_has_attachment_text(body_text):
                            return {'ok': True,
                                    'method': f'label:{label}/input[{i}]',
                                    'body_excerpt': body_text[:2000]}
                    except Exception as exc:
                        errors.append(f'label {label} input[{i}]: {exc!r}')
        except Exception as exc:
            errors.append(f'label {label}: {exc!r}')

    body_text = await page.locator('body').inner_text(timeout=10000)
    return {'ok': False, 'errors': errors, 'body_excerpt': body_text[:3000]}


async def main():
    status = {
        'run_id': RUN_ID,
        'task_id': TASK_ID,
        'pack': str(PACK),
        'pack_exists': PACK.exists(),
        'pack_size': PACK.stat().st_size if PACK.exists() else None,
        'pack_sha256': hashlib.sha256(PACK.read_bytes()).hexdigest() if PACK.exists() else None,
        'sent': False,
        'captured': False,
        'upload_confirmed': False,
    }

    async with async_playwright() as pw:
        browser = await pw.chromium.connect_over_cdp('http://127.0.0.1:9222')
        ctx = browser.contexts[0] if browser.contexts else await browser.new_context()

        # Scenario A: reuse existing page with project context, or open target URL
        page = None
        for pg in ctx.pages:
            if TARGET_URL in pg.url:
                page = pg
                print(f'Reusing existing page: {pg.url}')
                break
        if page is None:
            page = await ctx.new_page()
            await page.goto(TARGET_URL, wait_until='domcontentloaded', timeout=60000)
            print(f'Opened new page: {TARGET_URL}')
        await page.bring_to_front()
        await asyncio.sleep(5)

        status['chat_url_initial'] = page.url
        CHAT_URL_OUT.write_text(page.url + '\n', encoding='utf-8')

        # Clear composer
        clear_result = await clear_composer(page)
        status['clear_composer_before_upload'] = clear_result

        # Upload attachment
        upload = await try_upload(page)
        status['upload_attempt'] = upload
        status['upload_confirmed'] = bool(upload.get('ok'))
        await page.screenshot(path=str(SCREENSHOT_OUT), full_page=False)
        status['upload_confirmation_screenshot'] = str(SCREENSHOT_OUT)
        STATUS_OUT.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding='utf-8')

        if not status['upload_confirmed']:
            status['status'] = 'manual_required'
            status['reason'] = 'unable_to_confirm_attachment_visible_in_new_gpt_chat'
            STATUS_OUT.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding='utf-8')
            print(json.dumps(status, ensure_ascii=False, indent=2))
            return

        # Paste prompt
        pyperclip.copy(PROMPT)
        editor = await find_editor(page)
        await editor.click(timeout=30000)
        await page.keyboard.press('Control+v')
        await asyncio.sleep(2)

        body_after_paste = await page.locator('body').inner_text(timeout=10000)
        if not page_has_attachment_text(body_after_paste):
            status['status'] = 'manual_required'
            status['reason'] = 'attachment_not_visible_after_prompt_paste'
            STATUS_OUT.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding='utf-8')
            print(json.dumps(status, ensure_ascii=False, indent=2))
            return

        # Click send button (NOT Control+Enter)
        before_user_count = await page.locator('[data-message-author-role="user"]').count()
        before_assistant_count = await page.locator('[data-message-author-role="assistant"]').count()

        send_click = await click_visible_send_button(page)
        status['send_click'] = send_click
        if not send_click.get('ok'):
            status['status'] = 'manual_required'
            status['reason'] = 'submit_button_not_found_or_not_clickable'
            STATUS_OUT.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding='utf-8')
            print(json.dumps(status, ensure_ascii=False, indent=2))
            return

        # Confirm message sent
        send_confirm = await confirm_message_sent(page, before_user_count, before_assistant_count)
        status['send_confirm'] = send_confirm
        if not send_confirm.get('ok'):
            status['status'] = 'manual_required'
            status['reason'] = 'submit_button_clicked_but_send_not_confirmed'
            STATUS_OUT.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding='utf-8')
            print(json.dumps(status, ensure_ascii=False, indent=2))
            return

        status['sent'] = True
        status['sent_at'] = time.strftime('%Y-%m-%dT%H:%M:%S')
        STATUS_OUT.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding='utf-8')
        print('Message sent. Waiting for GPT reply...')

        # Capture reply (match run_id + END_OF_GPT_RESPONSE + overall_judgment)
        last = ''
        stable = 0
        for tick in range(120):
            await asyncio.sleep(5)
            if page.url != status.get('chat_url_final'):
                status['chat_url_final'] = page.url
                CHAT_URL_OUT.write_text(page.url + '\n', encoding='utf-8')
            msgs = page.locator('[data-message-author-role="assistant"]')
            if await msgs.count() == 0:
                continue
            reply = await msgs.last.inner_text(timeout=10000)
            if reply == last:
                stable += 1
            else:
                stable = 0
                last = reply
            if RUN_ID in reply and 'END_OF_GPT_RESPONSE' in reply and 'overall_judgment:' in reply:
                print(f'Reply captured at tick {tick}')
                break
            if stable >= 12 and len(reply) > 300:
                print(f'Reply stable at tick {tick}, chars={len(reply)}')
                break

        reply = last
        RESULT_OUT.write_text(reply, encoding='utf-8')
        REPORT_RESULT_OUT.write_text(reply, encoding='utf-8')
        status.update({
            'captured': bool(reply),
            'reply_chars': len(reply),
            'reply_sha256': hashlib.sha256(reply.encode('utf-8')).hexdigest() if reply else None,
            'run_id_match': RUN_ID in reply,
            'has_end_marker': 'END_OF_GPT_RESPONSE' in reply,
            'has_overall_judgment': 'overall_judgment:' in reply,
            'parsed_overall_judgment': parse_judgment(reply),
            'chat_url_final': page.url,
            'result_path': str(RESULT_OUT),
            'report_result_path': str(REPORT_RESULT_OUT),
        })
        CHAT_URL_OUT.write_text(page.url + '\n', encoding='utf-8')
        STATUS_OUT.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps(status, ensure_ascii=False, indent=2))


asyncio.run(main())
