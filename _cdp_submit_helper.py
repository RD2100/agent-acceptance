"""CDP submission helper — uses clipboard paste instead of keyboard.type for long messages.

Usage:
    from _cdp_submit_helper import paste_and_send

    await paste_and_send(page, message_text)
"""
import asyncio
import json


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
