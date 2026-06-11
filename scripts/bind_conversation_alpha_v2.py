#!/usr/bin/env python3
"""Create a second ChatGPT conversation on port 9222 for project-alpha binding."""

import json
import time
import urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

REPO = Path("D:/agent-acceptance")
CDP = "http://localhost:9222"


def create_and_bind():
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP)
        ctx = browser.contexts[0]

        # Open new tab on port 9222
        page = ctx.new_page()
        page.goto("https://chatgpt.com", wait_until="domcontentloaded", timeout=30000)
        time.sleep(8)

        url = page.url
        print(f"New tab URL: {url}")

        textarea = page.query_selector("#prompt-textarea")
        if not textarea:
            print("Waiting for textarea...")
            for i in range(6):
                time.sleep(5)
                textarea = page.query_selector("#prompt-textarea")
                if textarea:
                    break
            if not textarea:
                print("FAILED: textarea not found")
                browser.close()
                return {"status": "failed", "reason": "no_textarea"}

        print("Textarea found. Sending message...")
        msg = "AWSP BINDING-2-A1 Test. This conversation is for Project Alpha isolation verification. Reply: ALPHA_BINDING_OK"

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
            msg,
        )
        time.sleep(1)
        page.keyboard.press("Enter")
        print("Message sent. Waiting...")
        time.sleep(20)

        conv_url = page.url
        print(f"Conversation URL: {conv_url}")

        conv_id = None
        if "/c/" in conv_url:
            conv_id = conv_url.split("/c/")[-1].split("?")[0].split("#")[0]

        if conv_id:
            print(f"Conversation ID: {conv_id}")

            # Verify in CDP page list
            pages = json.loads(
                urllib.request.urlopen(f"{CDP}/json", timeout=5).read()
            )
            chatgpt_pages = [p for p in pages if "chatgpt.com/c/" in p.get("url", "")]
            print(f"ChatGPT conversation pages: {len(chatgpt_pages)}")
            for cp in chatgpt_pages:
                print(f"  - {cp.get('url', '')[:100]}")

            # Update project-alpha binding
            binding_path = REPO / "_projects" / "project-alpha" / ".agent" / "CONVERSATION_BINDING.json"
            binding = json.loads(binding_path.read_text(encoding="utf-8"))
            for agent in binding["bindings"]:
                if agent["agent_id"] == "agent-alpha-001":
                    agent["binding_status"] = "active"
                    agent["conversation_id"] = conv_id
                    agent["chat_url"] = f"https://chatgpt.com/c/{conv_id}"
                    agent["cdp_endpoint"] = "http://localhost:9222"
                    agent["browser_profile_id"] = "cdp-profile-pilot-a1"
                    agent["allowed_task_scope"] = ["*"]
            binding_path.write_text(
                json.dumps(binding, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            print(f"Binding updated: {conv_id}")

            result = {
                "status": "bound",
                "project": "project-alpha",
                "conv_id": conv_id,
                "chatgpt_pages": len(chatgpt_pages),
                "cdp_port": 9222,
                "note": "Shared Chrome instance, distinct conversation for isolation verification",
            }
            result_path = REPO / "_reports" / "multi-project-batch-init-a1" / "BINDING_ALPHA_RESULT.json"
            result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
            print(f"SUCCESS: {json.dumps(result)}")
            return result
        else:
            print("ERROR: No conversation_id in URL")
            return {"status": "failed", "reason": "no_conversation_id"}

        browser.close()


if __name__ == "__main__":
    import sys
    result = create_and_bind()
    sys.exit(0 if result.get("status") == "bound" else 1)
