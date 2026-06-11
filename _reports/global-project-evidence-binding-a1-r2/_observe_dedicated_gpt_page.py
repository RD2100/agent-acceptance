import asyncio, json
from pathlib import Path
from playwright.async_api import async_playwright
OUT=Path('D:/agent-acceptance/_reports/global-project-evidence-binding-a1-r2/DEDICATED_GPT_PAGE_OBSERVE.json')
SHOT=Path('D:/agent-acceptance/_reports/global-project-evidence-binding-a1-r2/DEDICATED_GPT_PAGE_OBSERVE.png')
async def main():
    async with async_playwright() as pw:
        browser=await pw.chromium.connect_over_cdp('http://127.0.0.1:9223')
        ctx=browser.contexts[0]
        page=ctx.pages[-1]
        await page.bring_to_front()
        await asyncio.sleep(3)
        body=''
        try: body=await page.locator('body').inner_text(timeout=5000)
        except Exception as e: body=repr(e)
        counts={}
        for sel in ['div[contenteditable="true"]','textarea','button[data-testid="send-button"]','a[href*="login"]','button:has-text("Log in")','button:has-text("登录")']:
            try: counts[sel]=await page.locator(sel).count()
            except Exception as e: counts[sel]=repr(e)
        await page.screenshot(path=str(SHOT), full_page=False)
        data={'url':page.url,'title':await page.title(),'counts':counts,'body_excerpt':body[:2000],'screenshot':str(SHOT)}
        OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(data,ensure_ascii=False,indent=2))
asyncio.run(main())
