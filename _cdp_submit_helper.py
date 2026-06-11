"""CDP submission helper — uses clipboard paste instead of keyboard.type for long messages.

CONVERSATION-HEALTH-GATE-A2: Now integrates with pre_gpt_gate for
conversation health enforcement before every GPT/CDP submission.

Usage:
    from _cdp_submit_helper import paste_and_send, run_pre_gpt_gate

    # Check gate before submission
    exit_code, decision, message = run_pre_gpt_gate()
    if exit_code != 0:
        print(f"BLOCKED: {message}")
        return

    await paste_and_send(page, message_text)
"""
import asyncio
import json
import sys
from pathlib import Path


def run_pre_gpt_gate(allow_init=False):
    """Run the Pre-GPT gate check before CDP submission.

    Returns (exit_code, decision, message).
    exit_code 0 = proceed, non-zero = blocked.

    A2 integration: legacy scripts call this before any CDP interaction.
    """
    try:
        repo = Path(__file__).resolve().parent
        scripts_dir = str(repo / "scripts")
        added = False
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
            added = True
        from pre_gpt_gate import check_pre_gpt_gate  # type: ignore
        result = check_pre_gpt_gate(allow_init=allow_init)
        if added and scripts_dir in sys.path:
            sys.path.remove(scripts_dir)
        return result
    except ImportError as exc:
        # Fail-closed: if pre_gpt_gate is not available, BLOCK submission
        # This prevents legacy scripts from bypassing the gate when the
        # decision engine module is missing or broken.
        return 3, {
            "decision": "UNKNOWN",
            "severity": "BLOCKING",
            "reasons": [{
                "code": "pre_gpt_gate_unavailable",
                "actual": str(exc),
                "threshold": "pre_gpt_gate import required",
                "policy": "force",
            }]
        }, f"BLOCKED: pre_gpt_gate unavailable: {exc}"


async def paste_and_send(page, msg: str):
    """Paste message via clipboard into ChatGPT textarea and send.

    Works around the keyboard.type() fragmentation issue for long messages.
    """
    # Click textarea to focus
    textarea = page.locator("#prompt-textarea")
    await textarea.click()
    await asyncio.sleep(0.5)

    # Use JS to write text to clipboard, then simulate Ctrl+V paste
    await page.evaluate(f"navigator.clipboard.writeText({json.dumps(msg)})")
    await asyncio.sleep(0.3)
    await page.keyboard.press("Control+v")
    await asyncio.sleep(1)

    # Send via button or Enter
    send_btn = page.locator('button[data-testid="send-button"]')
    if await send_btn.is_visible():
        await send_btn.click()
        print("Message sent!")
    else:
        await page.keyboard.press("Enter")
        print("Sent via Enter")

    await asyncio.sleep(3)
