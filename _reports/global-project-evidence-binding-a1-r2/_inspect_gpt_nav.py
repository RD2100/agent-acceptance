import asyncio, json
from pathlib import Path
from playwright.async_api import async_playwright
OUT=Path('D:/agent-acceptance/_reports/global-project-evidence-binding-a1-r2/GPT_NAV_INSPECT.json')
async def main():
    async with async_playwright() as pw:
        browser=await pw.chromium.connect_over_cdp('http://127.0.0.1:9223')
        ctx=browser.contexts[0]
        page=ctx.pages[-1]
        await page.bring_to_front(); await asyncio.sleep(1)
        data=await page.evaluate('''() => ({
            url: location.href,
            links: Array.from(document.querySelectorAll('a')).slice(0,80).map(a=>({text:(a.innerText||a.textContent||'').trim(), href:a.href, aria:a.getAttribute('aria-label')})),
            buttons: Array.from(document.querySelectorAll('button')).slice(0,120).map(b=>({text:(b.innerText||b.textContent||'').trim(), aria:b.getAttribute('aria-label'), testid:b.getAttribute('data-testid'), cls:b.className}))
        })''')
        OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(data,ensure_ascii=False,indent=2)[:6000])
asyncio.run(main())
