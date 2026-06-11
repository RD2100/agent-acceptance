#!/usr/bin/env python3
"""Create a second ChatGPT conversation for agent-pilot-beta via CDP."""
import asyncio, json, sys
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]

        # Get existing pages
        existing_pages = context.pages
        print(f"Existing pages: {len(existing_pages)}")
        for pg in existing_pages:
            print(f"  {pg.url}")

        # Open new ChatGPT conversation in a new tab
        new_page = await context.new_page()
        await new_page.goto("https://chatgpt.com/", wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(5)

        url = new_page.url
        title = await new_page.title()
        print(f"\nNew page: {title}")
        print(f"URL: {url}")

        # Check if logged in
        login_modal = new_page.locator('[data-testid="login-modal"], .modal-no-auth-login')
        if await login_modal.count() > 0:
            print("ERROR: Not logged in!")
            await new_page.close()
            await browser.close()
            sys.exit(1)

        # Type a greeting message to create the conversation
        input_sel = '#prompt-textarea'
        try:
            await new_page.wait_for_selector(input_sel, timeout=10000)
        except Exception:
            input_sel = '[contenteditable="true"]'
            await new_page.wait_for_selector(input_sel, timeout=10000)

        msg = "你好，这是一个测试对话。请回复'收到'即可。"
        await new_page.click(input_sel)
        await asyncio.sleep(0.3)
        await new_page.keyboard.insert_text(msg)
        await asyncio.sleep(0.5)
        await new_page.keyboard.press("Enter")
        print("Message sent, waiting for conversation to be created...")

        # Wait for the URL to change (ChatGPT redirects to /c/{conversation_id})
        await asyncio.sleep(10)
        new_url = new_page.url
        print(f"URL after send: {new_url}")

        # Extract conversation ID
        if "/c/" in new_url:
            conv_id = new_url.split("/c/")[-1].split("?")[0].split("#")[0]
            print(f"\nConversation ID: {conv_id}")
            print(f"Chat URL: {new_url}")

            # Wait for GPT response
            for i in range(12):
                await asyncio.sleep(5)
                stop_btn = new_page.locator('button[aria-label="Stop generating"]')
                if await stop_btn.count() == 0 and i > 1:
                    msgs = new_page.locator('[data-message-author-role="assistant"]')
                    if await msgs.count() > 0:
                        text = await msgs.last.inner_text()
                        print(f"GPT replied: {text[:200]}")
                        break

            # Save result
            result = {
                "agent_id": "agent-pilot-beta",
                "conversation_id": conv_id,
                "chat_url": new_url,
                "cdp_endpoint": "http://localhost:9222",
                "browser_profile_id": "cdp-profile-pilot-a1",
                "tab_created": True,
            }
            result_path = r"D:\agent-acceptance\_reports\multi-agent-multi-gpt-pilot-a1\BETA_CONVERSATION.json"
            with open(result_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"\nSaved to {result_path}")
        else:
            print("ERROR: Could not extract conversation ID from URL")

        # Don't close the new page - we need it to stay open
        await browser.close()

asyncio.run(main())
