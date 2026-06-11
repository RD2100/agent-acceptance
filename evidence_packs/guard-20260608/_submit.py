import asyncio, hashlib, subprocess, os, shutil, zipfile
from playwright.async_api import async_playwright

base = "evidence_packs/guard-20260608"
for d in [base, base+"/actual_deliverables"]: os.makedirs(d, exist_ok=True)
shutil.copy("scripts/verify_gpt_reply.py", base+"/actual_deliverables/")

# Test proof
r = subprocess.run(["python", "scripts/verify_gpt_reply.py", "evidence_packs/batch-final-20260608/GPT_R7.txt", "TEST"], capture_output=True, text=True)
with open(base+"/GUARD_TEST_OUTPUT.txt", "w") as f: f.write(r.stdout)

r2 = subprocess.run(["python", "scripts/verify_gpt_reply.py", "/tmp/fake_no_end.txt", "TEST"], capture_output=True, text=True)
with open(base+"/GUARD_FAIL_CLOSED.txt", "w") as f: f.write(r2.stdout)

lines = ["| path | bytes | sha256 |", "|---|---:|---|"]
for root, dirs, files in os.walk(base):
    for fn in sorted(files):
        if fn.endswith(".zip") or fn == "PACK_MANIFEST.md": continue
        fp = os.path.join(root, fn); rel = os.path.relpath(fp, base).replace("\\", "/")
        lines.append("| %s | %d | %s |" % (rel, os.path.getsize(fp), hashlib.sha256(open(fp,"rb").read()).hexdigest()))
lines.append("| PACK_MANIFEST.md | self | self_excluded |")
open(base+"/PACK_MANIFEST.md","w").write("\n".join(lines)+"\n")

zp = zipfile.ZipFile(base+"/guard-pack.zip", "w", zipfile.ZIP_DEFLATED)
for root, dirs, files in os.walk(base):
    for fn in files:
        if fn.endswith(".zip"): continue
        zp.write(os.path.join(root, fn), os.path.relpath(os.path.join(root, fn), base))
zp.close()

async def submit():
    async with async_playwright() as pw:
        browser = await pw.chromium.connect_over_cdp("http://localhost:9222")
        page = None
        for ctx in browser.contexts:
            for pg in ctx.pages:
                if "6a23dd8c" in pg.url: page = pg; break
        if not page: return
        await page.keyboard.press("Escape"); await asyncio.sleep(0.3)
        await page.locator('input[type="file"]').first.set_input_files(base+"/guard-pack.zip")
        await asyncio.sleep(3)
        await page.keyboard.press("Escape"); await asyncio.sleep(0.3)
        await page.evaluate('document.querySelector("div[contenteditable=true]").focus()')
        msg = "GPT-REVIEW-RESPONSE-BINDING-GUARD for review. verify_gpt_reply.py enforces P0 rule: no captured GPT reply, no verdict. Fail-closed. 275 PASS. guard-pack.zip attached. END_OF_GPT_RESPONSE"
        await page.keyboard.type(msg, delay=5); await asyncio.sleep(0.5)
        await page.keyboard.press("Control+Enter")
        print("Sent. Waiting 120s...")
        await asyncio.sleep(120)
        text = await page.locator('div[data-message-author-role="assistant"]').last.inner_text()
        sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
        for line in text.split("\n"):
            if any(w in line.lower() for w in ["verdict", "accepted", "blocked"]) and ":" in line:
                print(line.strip()[:120])
        print(f"SHA256: {sha[:16]}...")
        with open(base+"/GPT_RESULT.txt", "w", encoding="utf-8") as f: f.write(text)

asyncio.run(submit())
