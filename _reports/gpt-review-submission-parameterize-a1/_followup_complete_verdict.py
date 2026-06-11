#!/usr/bin/env python3
"""Follow-up to request complete verdict with next_task_authorization.

R1 reply was truncated (missing next_task_authorization and END_OF_GPT_RESPONSE).
This script sends a follow-up message asking GPT to provide the complete output format.
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
TASK_ID = 'GPT-REVIEW-SUBMISSION-PARAMETERIZE-A1'
RUN_ID = 'GPT_REVIEW_SUBMISSION_PARAMETERIZE_A1_REVIEW_20260609T023631_RD'

REPORT_DIR = ROOT / '_reports/gpt-review-submission-parameterize-a1'
PACK_DIR = ROOT / 'evidence_packs/gpt-review-submission-parameterize-a1'
TARGET_URL = 'https://chatgpt.com/c/6a26cc03-235c-83a2-a0fc-cd29be615959'

RESULT_OUT = PACK_DIR / 'GPT_REVIEW_RESULT_R2.txt'
REPORT_RESULT_OUT = REPORT_DIR / 'GPT_REVIEW_RESULT_R2.txt'
RECON_OUT = REPORT_DIR / 'GPT_CAPTURE_RECONCILIATION_R2.json'
STATUS_OUT = REPORT_DIR / 'GPT_REVIEW_SUBMISSION_STATUS_R2.json'

FOLLOWUP_MSG = f"""你上一次的回复被截断了，缺少 next_task_authorization 和 END_OF_GPT_RESPONSE 标记。

请补全你的审查结果。请重新输出完整的 YAML-like block，确保包含以下所有字段：

run_id: {RUN_ID}
task_id: GPT-REVIEW-SUBMISSION-PARAMETERIZE-A1
evidence_pack_reviewed: true
attachment_reviewed: true
overall_judgment: (保持你之前的判断)
blocking_issues: (保持你之前的判断)
required_fixes: (保持你之前的判断)
limitations: (保持你之前的判断)
next_task_authorization:
  task_id: (下一个任务 ID)
  authorized: 已授权 | 未授权
  execute_immediately: 是 | 否
  ask_before_starting: 是 | 否

END_OF_GPT_RESPONSE"""


def parse_judgment(text):
    m = re.search(r'overall_judgment:\s*([^\s|]+)', text, re.I)
    return m.group(1).strip().lower() if m else None


async def find_editor(page):
    for sel in ['div[contenteditable="true"].ProseMirror', 'div[contenteditable="true"]', 'textarea']:
        loc = page.locator(sel)
        if await loc.count() > 0:
            return loc.last
    raise RuntimeError('editor not found')


async def click_visible_send_button(page):
    selectors = [
        'button[data-testid="send-button"]', '#composer-submit-button',
        'button.composer-submit-button-color', 'button[aria-label*="Send"]',
        'button:has-text("Send")', 'button:has-text("发送")',
    ]
    for sel in selectors:
        try:
            loc = page.locator(sel)
            for i in range(await loc.count()):
                btn = loc.nth(i)
                if await btn.is_visible(timeout=1000) and await btn.is_enabled(timeout=1000):
                    await btn.click(timeout=10000)
                    return {'ok': True, 'selector': sel, 'index': i}
        except Exception:
            pass
    return {'ok': False}


async def capture_with_baseline(page, before_user_count, before_assistant_count):
    recon = {
        'target_run_id': RUN_ID, 'target_task_id': TASK_ID,
        'before_user_count': before_user_count, 'before_assistant_count': before_assistant_count,
        'after_user_count': None, 'after_assistant_count': None,
        'candidate_indices': [], 'selected_index': None, 'last_index': None,
        'capture_mismatch': False, 'decision': None,
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
        # Look for complete reply with BOTH run_id AND END_OF_GPT_RESPONSE AND next_task_authorization
        for i in range(before_assistant_count, count):
            txt = await msgs.nth(i).inner_text(timeout=10000)
            if (RUN_ID in txt and 'overall_judgment:' in txt
                    and 'END_OF_GPT_RESPONSE' in txt
                    and 'next_task_authorization' in txt):
                recon['candidate_indices'].append(i)
                target_reply = txt
                recon['selected_index'] = i
                print(f'Capture: found complete reply at assistant[{i}], tick={tick}')
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
        if stable >= 15 and len(last_text) > 200:
            print(f'Capture: stable but incomplete at tick {tick}')
            break
    msgs = page.locator('[data-message-author-role="assistant"]')
    last_idx = (await msgs.count()) - 1
    recon['last_index'] = last_idx
    if recon['selected_index'] is not None and recon['selected_index'] != last_idx:
        recon['capture_mismatch'] = True
        recon['decision'] = 'selected_by_content_not_last'
    elif recon['selected_index'] is not None:
        recon['decision'] = 'selected_and_last_match'
    else:
        recon['decision'] = 'capture_failed'
    RECON_OUT.write_text(json.dumps(recon, ensure_ascii=False, indent=2), encoding='utf-8')
    return target_reply, recon


async def main():
    status = {
        'run_id': RUN_ID, 'task_id': TASK_ID, 'round': 'R2_followup',
        'sent': False, 'captured': False,
    }
    async with async_playwright() as pw:
        browser = await pw.chromium.connect_over_cdp('http://127.0.0.1:9222')
        ctx = browser.contexts[0]
        page = None
        for pg in ctx.pages:
            if TARGET_URL in pg.url:
                page = pg
                break
        if page is None:
            page = await ctx.new_page()
            await page.goto(TARGET_URL, wait_until='domcontentloaded', timeout=60000)
        await page.bring_to_front()
        await asyncio.sleep(5)

        # Record baselines
        before_user_count = await page.locator('[data-message-author-role="user"]').count()
        before_assistant_count = await page.locator('[data-message-author-role="assistant"]').count()
        print(f'Baseline: users={before_user_count}, assistants={before_assistant_count}')

        # Paste follow-up message
        pyperclip.copy(FOLLOWUP_MSG)
        editor = await find_editor(page)
        await editor.click(timeout=30000)
        await page.keyboard.press('Control+v')
        await asyncio.sleep(2)

        # Click send
        send_click = await click_visible_send_button(page)
        if not send_click.get('ok'):
            status['status'] = 'manual_required'
            status['reason'] = 'send_button_not_found'
            STATUS_OUT.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding='utf-8')
            print(json.dumps(status, ensure_ascii=False, indent=2))
            return

        # Confirm sent
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
        print('Follow-up sent. Waiting for complete reply...')

        # Capture with enhanced criteria
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
            'has_next_task_auth': 'next_task_authorization' in reply,
            'parsed_overall_judgment': parse_judgment(reply),
            'capture_reconciliation': recon,
            'result_path': str(RESULT_OUT),
        })
        STATUS_OUT.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps(status, ensure_ascii=False, indent=2))

asyncio.run(main())
