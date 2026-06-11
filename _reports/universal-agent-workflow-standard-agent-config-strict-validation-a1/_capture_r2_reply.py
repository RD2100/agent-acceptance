#!/usr/bin/env python3
"""Manually capture last GPT assistant reply from ChatGPT via CDP."""
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

REPORT_DIR = Path(__file__).resolve().parent
OUTPUT = REPORT_DIR / "GPT_REVIEW_RESULT_R2.txt"

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    ctx = browser.contexts[0]
    page = ctx.pages[0]
    
    selector = '[data-message-author-role="assistant"]'
    msgs = page.query_selector_all(selector)
    
    if msgs:
        last = msgs[-1]
        text = last.inner_text()
        has_end = "END_OF_GPT_RESPONSE" in text
        print(f"Assistant messages: {len(msgs)}")
        print(f"Last message length: {len(text)}")
        print(f"Has END_OF_GPT_RESPONSE: {has_end}")
        print("---FIRST 500 CHARS---")
        print(text[:500])
        print("---LAST 500 CHARS---")
        print(text[-500:])
        OUTPUT.write_text(text, encoding="utf-8")
        print(f"\nSaved to {OUTPUT}")
    else:
        print("No assistant messages found")
    browser.close()
