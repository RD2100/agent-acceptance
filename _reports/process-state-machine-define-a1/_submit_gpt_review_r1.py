#!/usr/bin/env python3
"""PROCESS-STATE-MACHINE-DEFINE-A1 R1 GPT review submitter.

Based on the hardened R2 submit script from HANDOFF-WORKFLOW-HARDENING-PLAN-A1.
Uses before_assistant_count baseline + run_id as authoritative anchor.
Submits to the continuation conversation (Scenario A).
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
TASK_ID = 'PROCESS-STATE-MACHINE-DEFINE-A1'
RUN_ID = 'PROCESS_STATE_MACHINE_DEFINE_A1_REVIEW_20260609T022432_RD'
PACK = ROOT / 'evidence_packs/process-state-machine-define-a1/PROCESS_STATE_MACHINE_DEFINE_A1_20260609T022432.zip'

REPORT_DIR = ROOT / '_reports/process-state-machine-define-a1'
PACK_DIR = ROOT / 'evidence_packs/process-state-machine-define-a1'
TARGET_URL = 'https://chatgpt.com/c/6a26cc03-235c-83a2-a0fc-cd29be615959'

CHAT_URL_OUT = REPORT_DIR / 'GPT_REVIEW_CHAT_URL_R1.txt'
STATUS_OUT = REPORT_DIR / 'GPT_REVIEW_SUBMISSION_STATUS_R1.json'
SCREENSHOT_OUT = REPORT_DIR / 'GPT_REVIEW_UPLOAD_CONFIRMATION_R1.png'
RESULT_OUT = PACK_DIR / 'GPT_REVIEW_RESULT_R1.txt'
REPORT_RESULT_OUT = REPORT_DIR / 'GPT_REVIEW_RESULT_R1.txt'
RECON_OUT = REPORT_DIR / 'GPT_CAPTURE_RECONCILIATION_R1.json'
RECORD_OUT = REPORT_DIR / 'GPT_REVIEW_RECORD_R1.json'

PROMPT = (PACK_DIR / 'GPT_REVIEW_PROMPT.md').read_text(encoding='utf-8')


def parse_judgment(text):
    m = re.search(r'overall_judgment:\s*([^\s|]+)', text, re.I)
    return m.group(1).strip().lower() if m else None


def page_has_attachment_text(text):
    lowered = text.lower()
    return ('process_state_machine' in lowered
            or 'process-state-machine' in lowered
            or 'state_machine_define' in lowered
            or 'changed_files' in lowered)


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
        'button[data-testid="send-button"]', '#composer-submit-button',
        'button.composer-submit-button-color', 'button[aria-label*="Send"]',
        'button:has-text("Send")', 'button:has-text("发送")',
    ]
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
            return {ok: true, method: 'js_click', label: b.getAttribute('aria-label')};
        }''')
        if js_result.get('ok'):
            return js_result
    except Exception as exc:
        errors.append(f'js_fallback: {exc!r}')
    return {'ok': False, 'errors': errors}


async def try_upload(page):
    errors = []
    inputs = page.locator('input[type="file"]')
    count = await inputs.count()
    for i in range(count):
        try:
            await inputs.nth(i).set_input_files(str(PACK))
            await asyncio.sleep(8)
            body_text = await page.locator('body').inner_text(timeout=10000)
            if page_has_attachment_text(body_text):
                return {'ok': True, 'method': f'input[{i}]'}
        except Exception as exc:
            errors.append(f'input[{i}]: {exc!r}')
    # Try clicking attach buttons
    for label in ['Attach', 'Upload', 'Add photos and files', '附件', '上传', '+']:
        try:
            button = page.get_by_label(label)
            if await button.count() > 0:
                await button.first.click(timeout=5000)
                await asyncio.sleep(1)
                inputs = page.locator('input[type="file"]')
                for i in range(await inputs.count()):
                    try:
                        await inputs.nth(i).set_input_files(str(PACK))
                        await asyncio.sleep(8)
                        body_text = await page.locator('body').inner_text(timeout=10000)
                        if page_has_attachment_text(body_text):
                            return {'ok': True, 'method': f'label:{label}/input[{i}]'}
                    except Exception as exc:
                        errors.append(f'label {label} input[{i}]: {exc!r}')
        except Exception as exc:
            errors.append(f'label {label}: {exc!r}')
    return {'ok': False, 'errors': errors}


async def capture_with_baseline(page, before_user_count, before_assistant_count):
    """Capture: use baseline + run_id as authoritative anchor."""
    recon = {
        'target_run_id': RUN_ID,
        'target_task_id': TASK_ID,
        'before_user_count': before_user_count,
        'before_assistant_count': before_assistant_count,
        'after_user_count': None,
        'after_assistant_count': None,
        'candidate_indices': [],
        'selected_index': None,
        'last_index': None,
        'last_text_contains_run_id': False,
        'selected_text_contains_run_id': False,
        'selected_text_contains_end_marker': False,
        'capture_mismatch': False,
        'decision': None,
    }

    target_reply = None
    stable = 0
    last_text = ''

    for tick in range(120):
        await asyncio.sleep(5)
        msgs = page.locator('[data-message-author-role="assistant"]')
        count = await msgs.count()
        recon['after_assistant_count'] = count

        users = page.locator('[data-message-author-role="user"]')
        recon['after_user_count'] = await users.count()

        if count <= before_assistant_count:
            continue

        # Scan NEW assistant messages only
        for i in range(before_assistant_count, count):
            txt = await msgs.nth(i).inner_text(timeout=10000)
            if RUN_ID in txt and 'overall_judgment:' in txt and 'END_OF_GPT_RESPONSE' in txt:
                recon['candidate_indices'].append(i)
                target_reply = txt
                recon['selected_index'] = i
                recon['selected_text_contains_run_id'] = True
                recon['selected_text_contains_end_marker'] = True
                print(f'Capture: found target at assistant[{i}], tick={tick}')
                break

        if target_reply:
            break

        # Stability check
        last_msg = await msgs.nth(count - 1).inner_text(timeout=10000)
        if last_msg == last_text:
            stable += 1
        else:
            stable = 0
            last_text = last_msg
        if stable >= 15 and len(last_text) > 300:
            print(f'Capture: stable but no run_id match at tick {tick}')
            break

    # Check last assistant for mismatch
    msgs = page.locator('[data-message-author-role="assistant"]')
    last_idx = (await msgs.count()) - 1
    recon['last_index'] = last_idx
    if last_idx >= 0:
        last_txt = await msgs.nth(last_idx).inner_text(timeout=10000)
        recon['last_text_contains_run_id'] = RUN_ID in last_txt

    if recon['selected_index'] is not None and recon['selected_index'] != last_idx:
        recon['capture_mismatch'] = True
        recon['decision'] = 'selected_by_run_id_not_last'
    elif recon['selected_index'] is not None:
        recon['decision'] = 'selected_and_last_match'
    else:
        recon['decision'] = 'capture_failed_no_run_id_match'

    RECON_OUT.write_text(json.dumps(recon, ensure_ascii=False, indent=2), encoding='utf-8')
    return target_reply, recon


async def main():
    status = {
        'run_id': RUN_ID,
        'task_id': TASK_ID,
        'round': 'R1',
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
        ctx = browser.contexts[0]

        # Find or open continuation conversation
        page = None
        for pg in ctx.pages:
            if TARGET_URL in pg.url:
                page = pg
                print(f'Reusing page: {pg.url}')
                break
        if page is None:
            page = await ctx.new_page()
            await page.goto(TARGET_URL, wait_until='domcontentloaded', timeout=60000)
            print(f'Opened: {TARGET_URL}')
        await page.bring_to_front()
        await asyncio.sleep(5)

        status['chat_url_initial'] = page.url
        CHAT_URL_OUT.write_text(page.url + '\n', encoding='utf-8')

        # Clear composer
        status['clear_composer'] = await clear_composer(page)

        # Upload attachment
        upload = await try_upload(page)
        status['upload_attempt'] = upload
        status['upload_confirmed'] = bool(upload.get('ok'))
        await page.screenshot(path=str(SCREENSHOT_OUT), full_page=False)

        STATUS_OUT.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding='utf-8')

        if not status['upload_confirmed']:
            status['status'] = 'manual_required'
            status['reason'] = 'unable_to_confirm_attachment_visible'
            STATUS_OUT.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding='utf-8')
            print(json.dumps(status, ensure_ascii=False, indent=2))
            return

        # Paste prompt
        pyperclip.copy(PROMPT)
        editor = await find_editor(page)
        await editor.click(timeout=30000)
        await page.keyboard.press('Control+v')
        await asyncio.sleep(2)

        # Record baseline BEFORE send
        before_user_count = await page.locator('[data-message-author-role="user"]').count()
        before_assistant_count = await page.locator('[data-message-author-role="assistant"]').count()
        print(f'Baseline: users={before_user_count}, assistants={before_assistant_count}')

        # Click send button
        send_click = await click_visible_send_button(page)
        status['send_click'] = send_click
        if not send_click.get('ok'):
            status['status'] = 'manual_required'
            status['reason'] = 'submit_button_not_found'
            STATUS_OUT.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding='utf-8')
            print(json.dumps(status, ensure_ascii=False, indent=2))
            return

        # Confirm message sent
        sent_ok = False
        for _ in range(24):
            await asyncio.sleep(1)
            uc = await page.locator('[data-message-author-role="user"]').count()
            if uc > before_user_count:
                sent_ok = True
                print(f'Send confirmed: user_count {before_user_count} -> {uc}')
                break

        if not sent_ok:
            status['status'] = 'manual_required'
            status['reason'] = 'send_not_confirmed'
            STATUS_OUT.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding='utf-8')
            print(json.dumps(status, ensure_ascii=False, indent=2))
            return

        status['sent'] = True
        status['sent_at'] = time.strftime('%Y-%m-%dT%H:%M:%S')
        STATUS_OUT.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding='utf-8')
        print('Message sent. Waiting for GPT reply...')

        # Capture with baseline + run_id matching
        reply, recon = await capture_with_baseline(page, before_user_count, before_assistant_count)

        if reply is None:
            reply = ''

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
            'capture_reconciliation': recon,
            'chat_url_final': page.url,
            'result_path': str(RESULT_OUT),
            'report_result_path': str(REPORT_RESULT_OUT),
        })
        CHAT_URL_OUT.write_text(page.url + '\n', encoding='utf-8')
        STATUS_OUT.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps(status, ensure_ascii=False, indent=2))


asyncio.run(main())
