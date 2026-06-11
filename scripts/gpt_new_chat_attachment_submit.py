#!/usr/bin/env python3
"""gpt_new_chat_attachment_submit.py — 参数化 GPT 审查提交器。

支持 Scenario A（延续性对话）和 Scenario B（新对话），使用 hardened capture 逻辑：
- before_assistant_count baseline + run_id authoritative matching
- capture reconciliation report per submission

Usage:
    python scripts/gpt_new_chat_attachment_submit.py \\
        --task-id "TASK-ID" \\
        --pack-path "./path/to/pack.zip" \\
        --run-id-path "./path/to/run_id.txt" \\
        --output-path "./path/to/output.txt" \\
        --prompt-template "./path/to/prompt.md" \\
        [--chat-url "https://chatgpt.com/c/xxx"] \\
        [--report-dir "./path/to/report_dir"] \\
        [--cdp-url "http://127.0.0.1:9222"] \\
        [--timeout 300] \\
        [--dry-run]
"""

import argparse
import asyncio
import hashlib
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    import pyperclip
    from playwright.async_api import async_playwright
except ImportError as e:
    print(f"ERROR: Missing dependency: {e}")
    print("Install: pip install playwright pyperclip && python -m playwright install chromium")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Default prompt template (used when --prompt-template is not provided)
# ---------------------------------------------------------------------------
DEFAULT_PROMPT_TEMPLATE = """GPT REVIEW REQUEST: {{TASK_ID}}

run_id: {{RUN_ID}}

You are reviewing {{TASK_ID}}. The attached file is the evidence pack.
Please inspect the attachment and return a fresh verdict for this run_id.

Important:
- Your response must include the same run_id.
- End with END_OF_GPT_RESPONSE.
- If the attachment is unavailable or unreadable, use overall_judgment: review_unverified and evidence_pack_reviewed: false.

Return this YAML-like block:

run_id: {{RUN_ID}}
task_id: {{TASK_ID}}
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
  task_id: <next task id>
  authorized: 已授权 | 未授权
  execute_immediately: 是 | 否
  ask_before_starting: 是 | 否
END_OF_GPT_RESPONSE
"""


# ---------------------------------------------------------------------------
# Template rendering
# ---------------------------------------------------------------------------
def render_prompt(template: str, task_id: str, run_id: str,
                  pack_manifest_path: Path | None = None) -> str:
    """Replace template variables in the prompt."""
    result = template.replace("{{TASK_ID}}", task_id)
    result = result.replace("{{RUN_ID}}", run_id)
    result = result.replace("{{TIMESTAMP}}", datetime.now(timezone.utc).isoformat())

    if "{{PACK_MANIFEST}}" in result:
        if pack_manifest_path and pack_manifest_path.exists():
            manifest_text = pack_manifest_path.read_text(encoding="utf-8")
        else:
            manifest_text = "(PACK_MANIFEST not available)"
        result = result.replace("{{PACK_MANIFEST}}", manifest_text)

    return result


# ---------------------------------------------------------------------------
# Page interaction helpers
# ---------------------------------------------------------------------------
def parse_judgment(text: str) -> str | None:
    m = re.search(r"overall_judgment:\s*([^\s|]+)", text, re.I)
    return m.group(1).strip().lower() if m else None


def make_attachment_checker(pack_path: Path):
    """Return a function that checks if page text shows the attachment."""
    pack_name = pack_path.name.lower()
    pack_stem = pack_path.stem.lower()
    keywords = [pack_name, pack_stem]
    # Add partial matches for common patterns
    if "-" in pack_stem:
        keywords.append(pack_stem.replace("-", "_"))

    def check(text: str) -> bool:
        lowered = text.lower()
        return any(kw in lowered for kw in keywords)

    return check


async def find_editor(page):
    for sel in ['div[contenteditable="true"].ProseMirror',
                'div[contenteditable="true"]', 'textarea']:
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
        '#composer-submit-button',
        'button.composer-submit-button-color',
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
                    return {"ok": True, "selector": sel, "index": i}
        except Exception as exc:
            errors.append(f"{sel}: {exc!r}")
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
        if js_result.get("ok"):
            return js_result
    except Exception as exc:
        errors.append(f"js_fallback: {exc!r}")
    return {"ok": False, "errors": errors}


async def try_upload(page, pack_path: Path, attachment_check):
    errors = []
    inputs = page.locator('input[type="file"]')
    count = await inputs.count()
    for i in range(count):
        try:
            await inputs.nth(i).set_input_files(str(pack_path))
            await asyncio.sleep(8)
            body_text = await page.locator("body").inner_text(timeout=10000)
            if attachment_check(body_text):
                return {"ok": True, "method": f"input[{i}]"}
        except Exception as exc:
            errors.append(f"input[{i}]: {exc!r}")

    for label in ["Attach", "Upload", "Add photos and files", "附件", "上传", "+"]:
        try:
            button = page.get_by_label(label)
            if await button.count() > 0:
                await button.first.click(timeout=5000)
                await asyncio.sleep(1)
                inputs = page.locator('input[type="file"]')
                for i in range(await inputs.count()):
                    try:
                        await inputs.nth(i).set_input_files(str(pack_path))
                        await asyncio.sleep(8)
                        body_text = await page.locator("body").inner_text(timeout=10000)
                        if attachment_check(body_text):
                            return {"ok": True, "method": f"label:{label}/input[{i}]"}
                    except Exception as exc:
                        errors.append(f"label {label} input[{i}]: {exc!r}")
        except Exception as exc:
            errors.append(f"label {label}: {exc!r}")

    return {"ok": False, "errors": errors}


async def capture_with_baseline(page, run_id, task_id,
                                before_user_count, before_assistant_count,
                                timeout_ticks=120):
    """Hardened capture: baseline + run_id as authoritative anchor."""
    recon = {
        "target_run_id": run_id,
        "target_task_id": task_id,
        "before_user_count": before_user_count,
        "before_assistant_count": before_assistant_count,
        "after_user_count": None,
        "after_assistant_count": None,
        "candidate_indices": [],
        "selected_index": None,
        "last_index": None,
        "last_text_contains_run_id": False,
        "selected_text_contains_run_id": False,
        "selected_text_contains_end_marker": False,
        "capture_mismatch": False,
        "decision": None,
    }

    target_reply = None
    stable = 0
    last_text = ""

    for tick in range(timeout_ticks):
        await asyncio.sleep(5)
        msgs = page.locator('[data-message-author-role="assistant"]')
        count = await msgs.count()
        recon["after_assistant_count"] = count

        users = page.locator('[data-message-author-role="user"]')
        recon["after_user_count"] = await users.count()

        if count <= before_assistant_count:
            continue

        # Scan NEW assistant messages only (index >= before_assistant_count)
        for i in range(before_assistant_count, count):
            txt = await msgs.nth(i).inner_text(timeout=10000)
            if run_id in txt and "overall_judgment:" in txt and "END_OF_GPT_RESPONSE" in txt:
                recon["candidate_indices"].append(i)
                target_reply = txt
                recon["selected_index"] = i
                recon["selected_text_contains_run_id"] = True
                recon["selected_text_contains_end_marker"] = True
                print(f"Capture: found target at assistant[{i}], tick={tick}")
                break

        if target_reply:
            break

        # Stability check (diagnostic only)
        last_msg = await msgs.nth(count - 1).inner_text(timeout=10000)
        if last_msg == last_text:
            stable += 1
        else:
            stable = 0
            last_text = last_msg
        if stable >= 15 and len(last_text) > 300:
            print(f"Capture: stable but no run_id match at tick {tick}")
            break

    # Check last assistant for mismatch
    msgs = page.locator('[data-message-author-role="assistant"]')
    last_idx = (await msgs.count()) - 1
    recon["last_index"] = last_idx
    if last_idx >= 0:
        last_txt = await msgs.nth(last_idx).inner_text(timeout=10000)
        recon["last_text_contains_run_id"] = run_id in last_txt

    if recon["selected_index"] is not None and recon["selected_index"] != last_idx:
        recon["capture_mismatch"] = True
        recon["decision"] = "selected_by_run_id_not_last"
    elif recon["selected_index"] is not None:
        recon["decision"] = "selected_and_last_match"
    else:
        recon["decision"] = "capture_failed_no_run_id_match"

    return target_reply, recon


# ---------------------------------------------------------------------------
# Main submission logic
# ---------------------------------------------------------------------------
async def submit(args):
    task_id = args.task_id
    pack_path = Path(args.pack_path)
    run_id_path = Path(args.run_id_path)
    output_path = Path(args.output_path)
    report_dir = Path(args.report_dir) if args.report_dir else output_path.parent
    cdp_url = args.cdp_url
    timeout_ticks = args.timeout // 5  # 5s per tick
    chat_url = args.chat_url

    # Determine scenario
    scenario = "B"  # default: new chat
    if chat_url and chat_url != "https://chatgpt.com/":
        scenario = "A"  # continuation conversation

    # Validate inputs
    if not pack_path.exists():
        print(f"ERROR: pack not found: {pack_path}")
        sys.exit(1)
    if not run_id_path.exists():
        print(f"ERROR: run_id file not found: {run_id_path}")
        sys.exit(1)

    run_id = run_id_path.read_text(encoding="utf-8").strip()

    # Load prompt template
    if args.prompt_template:
        prompt_template_path = Path(args.prompt_template)
        if not prompt_template_path.exists():
            print(f"ERROR: prompt template not found: {prompt_template_path}")
            sys.exit(1)
        template = prompt_template_path.read_text(encoding="utf-8")
    else:
        template = DEFAULT_PROMPT_TEMPLATE

    # Look for PACK_MANIFEST in the pack's parent directory
    manifest_path = pack_path.parent / "PACK_MANIFEST.md"

    # Render prompt
    prompt = render_prompt(template, task_id, run_id, manifest_path)

    # Ensure report dir exists
    report_dir.mkdir(parents=True, exist_ok=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Output file paths
    chat_url_out = report_dir / "GPT_REVIEW_CHAT_URL.txt"
    status_out = report_dir / "GPT_REVIEW_SUBMISSION_STATUS.json"
    screenshot_out = report_dir / "GPT_REVIEW_UPLOAD_CONFIRMATION.png"
    result_out = output_path
    report_result_out = report_dir / "GPT_REVIEW_RESULT.txt"
    recon_out = report_dir / "GPT_CAPTURE_RECONCILIATION.json"

    attachment_check = make_attachment_checker(pack_path)

    pack_sha = hashlib.sha256(pack_path.read_bytes()).hexdigest()

    status = {
        "run_id": run_id,
        "task_id": task_id,
        "scenario": scenario,
        "pack": str(pack_path),
        "pack_exists": True,
        "pack_size": pack_path.stat().st_size,
        "pack_sha256": pack_sha,
        "prompt_chars": len(prompt),
        "dry_run": False,
        "sent": False,
        "captured": False,
        "upload_confirmed": False,
    }

    # DRY RUN MODE
    if args.dry_run:
        print("=== DRY RUN MODE ===")
        print(f"Task ID: {task_id}")
        print(f"Run ID: {run_id}")
        print(f"Pack: {pack_path} ({pack_path.stat().st_size} bytes)")
        print(f"Scenario: {scenario}")
        if chat_url:
            print(f"Chat URL: {chat_url}")
        print(f"Prompt length: {len(prompt)} chars")
        print(f"Output path: {output_path}")
        print(f"Report dir: {report_dir}")
        print()
        print("--- Prompt Preview (first 500 chars) ---")
        print(prompt[:500])
        print("--- End Preview ---")
        print()

        status["dry_run"] = True
        status["status"] = "dry_run_complete"
        status_out.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Dry run status saved: {status_out}")
        print("No actual submission performed.")
        return

    # LIVE SUBMISSION
    print(f"Submitting: task_id={task_id}, run_id={run_id}, scenario={scenario}")
    print(f"Pack: {pack_path} ({pack_path.stat().st_size} bytes, sha256={pack_sha[:16]}...)")

    async with async_playwright() as pw:
        browser = await pw.chromium.connect_over_cdp(cdp_url)
        ctx = browser.contexts[0]

        # Scenario A: reuse or open continuation URL
        # Scenario B: open new chat
        page = None
        if scenario == "A":
            for pg in ctx.pages:
                if chat_url in pg.url:
                    page = pg
                    print(f"Reusing page: {pg.url}")
                    break
            if page is None:
                page = await ctx.new_page()
                await page.goto(chat_url, wait_until="domcontentloaded", timeout=60000)
                print(f"Opened: {chat_url}")
        else:
            page = await ctx.new_page()
            await page.goto("https://chatgpt.com/", wait_until="domcontentloaded", timeout=60000)
            print("Opened new ChatGPT chat")

        await page.bring_to_front()
        await asyncio.sleep(5)

        status["chat_url_initial"] = page.url
        chat_url_out.write_text(page.url + "\n", encoding="utf-8")

        # Clear composer
        status["clear_composer"] = await clear_composer(page)

        # Upload attachment
        upload = await try_upload(page, pack_path, attachment_check)
        status["upload_attempt"] = upload
        status["upload_confirmed"] = bool(upload.get("ok"))
        await page.screenshot(path=str(screenshot_out), full_page=False)

        status_out.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")

        if not status["upload_confirmed"]:
            status["status"] = "manual_required"
            status["reason"] = "unable_to_confirm_attachment_visible"
            status_out.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
            print(json.dumps(status, ensure_ascii=False, indent=2))
            return

        # Paste prompt
        pyperclip.copy(prompt)
        editor = await find_editor(page)
        await editor.click(timeout=30000)
        await page.keyboard.press("Control+v")
        await asyncio.sleep(2)

        # Record baseline BEFORE send
        before_user_count = await page.locator('[data-message-author-role="user"]').count()
        before_assistant_count = await page.locator('[data-message-author-role="assistant"]').count()
        print(f"Baseline: users={before_user_count}, assistants={before_assistant_count}")

        # Click send button (NOT Control+Enter)
        send_click = await click_visible_send_button(page)
        status["send_click"] = send_click
        if not send_click.get("ok"):
            status["status"] = "manual_required"
            status["reason"] = "submit_button_not_found"
            status_out.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
            print(json.dumps(status, ensure_ascii=False, indent=2))
            return

        # Confirm message sent
        sent_ok = False
        for _ in range(24):
            await asyncio.sleep(1)
            uc = await page.locator('[data-message-author-role="user"]').count()
            if uc > before_user_count:
                sent_ok = True
                print(f"Send confirmed: user_count {before_user_count} -> {uc}")
                break

        if not sent_ok:
            status["status"] = "manual_required"
            status["reason"] = "send_not_confirmed"
            status_out.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
            print(json.dumps(status, ensure_ascii=False, indent=2))
            return

        status["sent"] = True
        status["sent_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        status_out.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
        print("Message sent. Waiting for GPT reply...")

        # Hardened capture with baseline + run_id matching
        reply, recon = await capture_with_baseline(
            page, run_id, task_id,
            before_user_count, before_assistant_count,
            timeout_ticks=timeout_ticks,
        )

        if reply is None:
            reply = ""

        # Save results
        result_out.write_text(reply, encoding="utf-8")
        report_result_out.write_text(reply, encoding="utf-8")
        recon_out.write_text(json.dumps(recon, ensure_ascii=False, indent=2), encoding="utf-8")

        status.update({
            "captured": bool(reply),
            "reply_chars": len(reply),
            "reply_sha256": hashlib.sha256(reply.encode("utf-8")).hexdigest() if reply else None,
            "run_id_match": run_id in reply,
            "has_end_marker": "END_OF_GPT_RESPONSE" in reply,
            "has_overall_judgment": "overall_judgment:" in reply,
            "parsed_overall_judgment": parse_judgment(reply),
            "capture_reconciliation": recon,
            "chat_url_final": page.url,
            "result_path": str(result_out),
            "report_result_path": str(report_result_out),
            "reconciliation_path": str(recon_out),
        })
        chat_url_out.write_text(page.url + "\n", encoding="utf-8")
        status_out.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(status, ensure_ascii=False, indent=2))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Parameterized GPT review submitter with attachment and hardened capture.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run — check prompt and config without submitting
  python scripts/gpt_new_chat_attachment_submit.py \\
      --task-id MY-TASK-A1 \\
      --pack-path evidence_packs/my-task-a1/pack.zip \\
      --run-id-path evidence_packs/my-task-a1/RUN_ID.txt \\
      --output-path _reports/my-task-a1/GPT_REVIEW_RESULT.txt \\
      --prompt-template evidence_packs/my-task-a1/GPT_REVIEW_PROMPT.md \\
      --dry-run

  # Submit to continuation conversation (Scenario A)
  python scripts/gpt_new_chat_attachment_submit.py \\
      --task-id MY-TASK-A1 \\
      --pack-path evidence_packs/my-task-a1/pack.zip \\
      --run-id-path evidence_packs/my-task-a1/RUN_ID.txt \\
      --output-path _reports/my-task-a1/GPT_REVIEW_RESULT.txt \\
      --prompt-template evidence_packs/my-task-a1/GPT_REVIEW_PROMPT.md \\
      --chat-url https://chatgpt.com/c/xxxxxxxx

  # Submit to new chat (Scenario B)
  python scripts/gpt_new_chat_attachment_submit.py \\
      --task-id MY-TASK-A1 \\
      --pack-path evidence_packs/my-task-a1/pack.zip \\
      --run-id-path evidence_packs/my-task-a1/RUN_ID.txt \\
      --output-path _reports/my-task-a1/GPT_REVIEW_RESULT.txt
        """,
    )

    parser.add_argument("--task-id", required=True,
                        help="Task ID (used in prompt injection and output naming)")
    parser.add_argument("--pack-path", required=True,
                        help="Path to evidence pack ZIP file")
    parser.add_argument("--run-id-path", required=True,
                        help="Path to file containing run_id")
    parser.add_argument("--output-path", required=True,
                        help="Path to save captured GPT reply")
    parser.add_argument("--prompt-template", default=None,
                        help="Path to prompt template file (default: built-in generic template)")
    parser.add_argument("--chat-url", default=None,
                        help="ChatGPT conversation URL. If provided and not chatgpt.com/, uses Scenario A (continuation). Default: Scenario B (new chat)")
    parser.add_argument("--report-dir", default=None,
                        help="Directory for status/screenshot/reconciliation files (default: output-path parent)")
    parser.add_argument("--cdp-url", default="http://127.0.0.1:9222",
                        help="Chrome DevTools Protocol URL (default: http://127.0.0.1:9222)")
    parser.add_argument("--timeout", type=int, default=300,
                        help="Capture timeout in seconds (default: 300)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Only generate prompt and show config, do not submit")

    args = parser.parse_args()
    asyncio.run(submit(args))


if __name__ == "__main__":
    main()
