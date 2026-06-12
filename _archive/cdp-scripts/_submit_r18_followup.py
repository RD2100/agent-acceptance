"""Build R18-FOLLOWUP evidence ZIP and submit via CDP."""
import os, json, subprocess, zipfile, hashlib, asyncio, pyperclip

os.chdir("D:/agent-acceptance")

EVID_DIR = "_evidence/R18-followup-cleanup"
ZIP_PATH = "_evidence/EVIDENCE_PACK_R18_FOLLOWUP.zip"
RUN_DIR = "_reports/r18-followup-cleanup-a1"
REPLY_PATH = f"{EVID_DIR}/gpt_reply.txt"
os.makedirs(EVID_DIR, exist_ok=True)

# Copy run evidence to evidence directory
import shutil
for f in os.listdir(RUN_DIR):
    if f.endswith((".py",)):  # skip generator scripts
        continue
    src = os.path.join(RUN_DIR, f)
    dst = os.path.join(EVID_DIR, f)
    shutil.copy2(src, dst)

# Add git show for this commit
r = subprocess.run(["git", "show", "--name-status", "bc974d2f"],
                   capture_output=True, encoding="utf-8")
with open(f"{EVID_DIR}/git-show-name-status-bc974d2f.txt", "w", encoding="utf-8") as f:
    f.write(r.stdout)

# Add git log
r2 = subprocess.run(["git", "log", "--oneline", "-8"], capture_output=True, encoding="utf-8")
with open(f"{EVID_DIR}/git-log.txt", "w", encoding="utf-8") as f:
    f.write(r2.stdout)

# Build ZIP
if os.path.exists(ZIP_PATH):
    os.remove(ZIP_PATH)
with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
    for fname in sorted(os.listdir(EVID_DIR)):
        fpath = os.path.join(EVID_DIR, fname)
        if os.path.isfile(fpath):
            zf.write(fpath, f"_evidence/R18-FOLLOWUP-CLEANUP/{fname}")

sha = hashlib.sha256(open(ZIP_PATH, "rb").read()).hexdigest()
fcount = len(zipfile.ZipFile(ZIP_PATH).infolist())
print(f"ZIP: {ZIP_PATH} ({fcount} files, {os.path.getsize(ZIP_PATH):,} bytes, sha256={sha[:16]})")

# Submission message
MSG = f"""## R18 Follow-Up Submission — Full SADP Closed Loop

Commit: bc974d2f (238 files, SADP hook PASSED)

### GPT R18 v3 Follow-Up Resolution:

| Required Follow-Up | Status | Evidence |
|---|---|---|
| Cleanup 26 untracked entries | DONE | 7 session artifacts + evidence committed, 15 NEG-009 remain deferred |
| Repair handoff-pipeline-refactor gate_0 | DONE | Valid inventory_evidence added |
| NEG-009 remain denied | CONFIRMED | 15 files still on deny_paths |
| Create dedicated TaskSpec | DONE | R18-FOLLOWUP-CLEANUP-A1 |

### Additional Changes:
- project-beta: 186 files deleted (removed from PROJECT_REGISTRY)
- dev-frame-writing: new project scaffold (11th project)
- test_router_10_project_stress.py: updated for new registry state

### SADP Evidence Chain:
- Gate 0: TaskSpec created with write_set
- Executor: 238 files staged
- Tester: 1038 passed, 0 failed, 21 warnings
- Guard: 0 scope violations, 0 deny violations
- Reviewer: PASS (0 P0, 0 P1, all findings resolved)
- Finalizer: final-report.md generated
- Git: SADP pre-commit hook PASSED (0 errors, 1 advisory warning)

### ZIP Contents ({fcount} files):
Attached EVIDENCE_PACK_R18_FOLLOWUP.zip

Please review and provide verdict. END_OF_GPT_RESPONSE"""

# CDP Submit
from playwright.async_api import async_playwright

async def submit():
    pyperclip.copy(MSG)
    print("Message copied to clipboard")

    async with async_playwright() as pw:
        browser = await pw.chromium.connect_over_cdp("http://localhost:9222")
        page = None
        for ctx in browser.contexts:
            for pg in ctx.pages:
                if "6a297f76" in pg.url:
                    page = pg; break
            if page: break

        if not page:
            print("ERROR: Target page not found"); return

        print(f"Target: {page.url}")
        await page.bring_to_front()
        await asyncio.sleep(1)
        await page.keyboard.press("Escape"); await asyncio.sleep(0.3)
        await page.keyboard.press("Escape"); await asyncio.sleep(0.3)

        # Upload ZIP
        fi = page.locator('input[type="file"]')
        if await fi.count() > 0:
            await fi.first.set_input_files(os.path.abspath(ZIP_PATH))
            print("ZIP uploaded")
            await asyncio.sleep(3)

        # Paste message
        editor = page.locator('div[contenteditable="true"].ProseMirror')
        if await editor.count() == 0:
            editor = page.locator('#prompt-textarea')
        await editor.first.click()
        await asyncio.sleep(0.5)
        await page.keyboard.press("Control+v")
        await asyncio.sleep(2)

        # Submit
        await page.keyboard.press("Control+Enter")
        print("Submitted. Waiting 150s...")
        await asyncio.sleep(150)

        # Capture reply
        replies = page.locator('div[data-message-author-role="assistant"]')
        count = await replies.count()
        if count > 0:
            reply = await replies.nth(count - 1).inner_text()
            print(f"Reply: {len(reply)} chars")
            print(f"Preview: {reply[:400]}")
            with open(REPLY_PATH, "w", encoding="utf-8") as f:
                f.write(reply)
            print(f"Saved to {REPLY_PATH}")
        else:
            print("No reply found")

    print("Done.")

asyncio.run(submit())
