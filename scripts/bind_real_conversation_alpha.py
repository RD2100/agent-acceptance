#!/usr/bin/env python3
"""Bind a real ChatGPT conversation to project-alpha on port 9223."""

import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CDP_9223 = "http://localhost:9223"


def bind_real_conversation():
    from playwright.sync_api import sync_playwright

    print("Connecting to CDP port 9223...")
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP_9223)
        context = browser.contexts[0]

        # Find or create page
        page = context.pages[0] if context.pages else context.new_page()

        print("Navigating to chatgpt.com...")
        page.goto("https://chatgpt.com", wait_until="domcontentloaded", timeout=60000)
        time.sleep(10)

        current_url = page.url
        print(f"Current URL: {current_url}")

        # Check if we're on a conversation page or login page
        if "login" in current_url or "auth" in current_url:
            print("NOT LOGGED IN on port 9223. This Chrome profile needs manual login first.")
            print("Please log in to ChatGPT on the port 9223 Chrome window, then re-run this script.")
            browser.close()
            return {"status": "needs_login", "url": current_url}

        # Try to find the input textarea
        try:
            page.wait_for_selector("#prompt-textarea", timeout=15000)
            print("ChatGPT input found — logged in!")
        except Exception:
            print("Input textarea not found. May need to wait longer or log in.")
            browser.close()
            return {"status": "input_not_found", "url": current_url}

        # Type a test message to create a conversation
        test_msg = "AWSP Multi-Project Binding Test — Project Alpha. Please confirm you can see this message. Reply with: BINDING_CONFIRMED_ALPHA"

        print(f"Sending test message ({len(test_msg)} chars)...")
        page.click("#prompt-textarea")
        time.sleep(0.5)

        page.evaluate(
            """(text) => {
                const el = document.querySelector('#prompt-textarea');
                el.focus();
                const sel = window.getSelection();
                sel.removeAllRanges();
                const range = document.createRange();
                range.selectNodeContents(el);
                sel.addRange(range);
                document.execCommand('insertText', false, text);
            }""",
            test_msg,
        )
        time.sleep(1)

        page.keyboard.press("Enter")
        print("Message sent. Waiting for conversation to create...")
        time.sleep(15)

        # Capture the conversation URL
        new_url = page.url
        print(f"New URL: {new_url}")

        # Extract conversation_id
        conv_id = None
        if "/c/" in new_url:
            conv_id = new_url.split("/c/")[-1].split("?")[0].split("#")[0]

        if conv_id:
            print(f"Conversation ID: {conv_id}")

            # Verify in page list
            pages_info = json.loads(
                __import__("urllib.request", fromlist=["urlopen"]).urlopen(
                    f"{CDP_9223}/json", timeout=5
                ).read()
            )
            chatgpt_pages = [p for p in pages_info if "chatgpt.com" in p.get("url", "")]
            print(f"ChatGPT pages on 9223: {len(chatgpt_pages)}")
            for cp in chatgpt_pages:
                print(f"  - {cp.get('url', '')[:100]}")

            # Update binding
            binding_dir = REPO / "_projects" / "project-alpha" / ".agent"
            binding_dir.mkdir(parents=True, exist_ok=True)
            binding_path = binding_dir / "CONVERSATION_BINDING.json"

            binding = json.loads(binding_path.read_text(encoding="utf-8"))
            for agent in binding["bindings"]:
                if agent["agent_id"] == "agent-alpha-001":
                    agent["binding_status"] = "active"
                    agent["conversation_id"] = conv_id
                    agent["chat_url"] = f"https://chatgpt.com/c/{conv_id}"
                    agent["allowed_task_scope"] = ["*"]

            binding_path.write_text(
                json.dumps(binding, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            print(f"Binding updated: {binding_path}")

            result = {
                "status": "bound",
                "project_id": "project-alpha",
                "port": 9223,
                "conversation_id": conv_id,
                "chat_url": f"https://chatgpt.com/c/{conv_id}",
                "binding_path": str(binding_path),
                "cdp_verified": True,
                "chatgpt_pages": len(chatgpt_pages),
            }

            # Save result
            result_path = REPO / "_reports" / "multi-project-batch-init-a1" / "BINDING_ALPHA_RESULT.json"
            result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
            print(f"Result saved: {result_path}")

        else:
            print("WARNING: Could not extract conversation_id from URL")
            result = {"status": "no_conversation_id", "url": new_url}

        browser.close()
        return result


if __name__ == "__main__":
    result = bind_real_conversation()
    print(f"\nFinal status: {result.get('status')}")
    sys.exit(0 if result.get("status") == "bound" else 1)
