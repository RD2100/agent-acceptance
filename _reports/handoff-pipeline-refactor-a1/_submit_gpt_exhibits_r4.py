import asyncio
import hashlib
import json
import time
from pathlib import Path

import pyperclip
from playwright.async_api import async_playwright

ROOT = Path("D:/agent-acceptance")
URL_ID = "6a23dd8c-4550-83a8-bdee-76ca5a982edb"
OUT = ROOT / "evidence_packs/handoff-pipeline-refactor-a1/GPT_REVIEW_RESULT_R4.txt"
REPORT_OUT = ROOT / "_reports/handoff-pipeline-refactor-a1/GPT_REVIEW_RESULT_R4.txt"
STATUS_OUT = ROOT / "_reports/handoff-pipeline-refactor-a1/GPT_SUBMISSION_STATUS_R4.json"

PROMPT = """GPT REVIEW REQUEST R4: HANDOFF-PIPELINE-REFACTOR-A1

The prior replies kept saying Phase 1 evidence was unavailable. To avoid attachment/UI ambiguity, here is a compact evidence exhibit. Please review ONLY these exhibits and return the YAML verdict.

EXHIBIT A — Source of truth file exists and content summary
Path: HANDOFF_SOURCE_OF_TRUTH.md
Content: defines P0 as verified GPT verdicts/evidence packs/TEST_OUTPUT/Project Index/ledgers/manifests; P1 as GPT-approved BOOT_CONTEXT/HANDOFF/PASTE_BLOCK; P2 as claude-memory-compiler and memory/index recall layer; P3 as legacy PROJECT_HISTORY/old HANDOFF/old PASTE_BLOCK. States coding agents may draft but cannot self-approve final handoff.

EXHIBIT B — Legacy inventory exists and content summary
Path: LEGACY_HANDOFF_INVENTORY.md
Content: inventories HANDOFF.md, HANDOFF_V5.md, HANDOFF_V6.md, PROJECT_HISTORY.md, PROJECT_HISTORY_FINAL.md, HISTORY_ANALYSIS.md, BOOT_CONTEXT.md, root GPT_*.txt, _reports/*gpt_response*.txt, memory/index.md, and claude-memory-compiler outputs. It says no legacy file was deleted, moved, renamed, rewritten, or marked.

EXHIBIT C — Handoff draft exists and is not approved
Path: _reports/handoff-pipeline-refactor-a1/HANDOFF_DRAFT_FOR_GPT.md
Key lines: task_id HANDOFF-PIPELINE-REFACTOR-A1; approval_status: draft_only; "This file is a coding-agent draft. It is not approved handoff material until GPT review is captured and verified." Includes P0/P1/P2/P3 hierarchy and safety boundaries. Does not contain paper full text.

EXHIBIT D — Stale check exists
Path: _reports/handoff-pipeline-refactor-a1/HANDOFF_STALE_CHECK.md/json
Findings: BOOT_CONTEXT_TEST_COUNT_CONFLICT HIGH (65/232/247); TEST_COUNT_WITHOUT_FRESH_P0 MEDIUM; MEMORY_FROZEN_REPO_ACTIVE MEDIUM; UNVERIFIED_CONVERSATIONAL_CLAIM INFO for 296 PASS. Uses phrase "unverified conversational claim", not hallucination/fabrication as final conclusion.

EXHIBIT E — Safety scan exists and passes
Path: _reports/handoff-pipeline-refactor-a1/HANDOFF_SAFETY_SCAN.md
Content: scanner validate_context_memory.validate_file; files_checked: 4; pass: True; issues: none.

EXHIBIT F — Targeted tests pass
Path: _reports/handoff-pipeline-refactor-a1/TARGETED_TEST_OUTPUT.txt
Raw output: 13 passed in 0.31s for tests/test_handoff_safety_scan.py, tests/test_handoff_stale_check.py, tests/test_handoff_source_map.py, tests/test_handoff_compiler.py.

EXHIBIT G — Evidence pack gates pass
Path: _reports/handoff-pipeline-refactor-a1/PRE_GPT_GATE_OUTPUT.txt
Content: evidence_pack_linter valid true, errors [], warnings []; pre_gpt_review_gate gate_passed true, errors [], warnings [], deliverable_count 22, has_sha256_entries true.

EXHIBIT H — Evidence pack exists
Path: evidence_packs/handoff-pipeline-refactor-a1/closure-pack.zip
SHA256: 2e701b1e22e105fbf6adad73dd47a44d2478516e8cd4c39e3ad15c0b4055f793
Size: 47021 bytes.

EXHIBIT I — Minimax M3 observation exists
Path: _reports/minimax-m3-observation/MINIMAX_M3_OBSERVATION_LOG.md and MINIMAX_M3_EVIDENCE_TABLE.json
Content: records objective evidence only; no final capability conclusion; records positives and weaknesses, including initial bash cd syntax issue and 296 PASS as unverified conversational claim.

EXHIBIT J — Approved handoff NOT generated
No HANDOFF_APPROVED_FOR_NEW_GPT.md, PASTE_BLOCK_APPROVED_FOR_NEW_GPT.txt, HANDOFF_APPROVAL_RECORD.json, or HANDOFF_MANIFEST.sha256 generated.

Please judge based on the above exhibits. If you still cannot review, say exactly what single missing exhibit prevents review.

Return ONLY this YAML-like block:

task_id: HANDOFF-PIPELINE-REFACTOR-A1
overall_judgment: accepted | accepted_with_limitation | blocked | review_unverified
safety_verdict: pass | fail | review_unverified
source_of_truth_verdict: pass | fail | review_unverified
stale_check_verdict: pass | fail | review_unverified
legacy_handoff_verdict: pass | fail | review_unverified
minimax_m3_observation_verdict: pass | fail | review_unverified
evidence_pack_reviewed: true | false
blocking_issues:
  - <issue or none>
required_fixes:
  - <fix or none>
limitations:
  - <limitation or none>
next_allowed_action: <specific next action>
END_OF_GPT_RESPONSE
"""

async def main():
    status = {"message_chars": len(PROMPT), "sent": False, "captured": False}
    async with async_playwright() as pw:
        browser = await pw.chromium.connect_over_cdp("http://localhost:9222")
        page = None
        for ctx in browser.contexts:
            for pg in ctx.pages:
                if URL_ID in pg.url:
                    page = pg
                    break
            if page:
                break
        if page is None:
            raise RuntimeError("target page not found")
        await page.bring_to_front()
        await page.keyboard.press("Escape")
        await asyncio.sleep(1)
        pyperclip.copy(PROMPT)
        editor = page.locator('div[contenteditable="true"].ProseMirror')
        if await editor.count() == 0:
            editor = page.locator('textarea, div[contenteditable="true"]').last
        await editor.click(timeout=15000)
        await page.keyboard.press("Control+v")
        await asyncio.sleep(1)
        await page.keyboard.press("Control+Enter")
        status["sent"] = True
        status["sent_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        STATUS_OUT.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
        last = ""
        stable = 0
        for _ in range(72):
            await asyncio.sleep(5)
            msgs = page.locator('[data-message-author-role="assistant"]')
            if await msgs.count() == 0:
                continue
            reply = await msgs.last.inner_text(timeout=10000)
            if reply == last:
                stable += 1
            else:
                stable = 0
                last = reply
            if "END_OF_GPT_RESPONSE" in reply:
                break
            if stable >= 8 and len(reply) > 300:
                break
        reply = last
        OUT.write_text(reply, encoding="utf-8")
        REPORT_OUT.write_text(reply, encoding="utf-8")
        status.update({"captured": bool(reply), "reply_chars": len(reply), "reply_sha256": hashlib.sha256(reply.encode("utf-8")).hexdigest() if reply else None, "valid_end_marker": "END_OF_GPT_RESPONSE" in reply, "result_path": str(OUT), "report_result_path": str(REPORT_OUT)})
        STATUS_OUT.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(status, ensure_ascii=False, indent=2))

asyncio.run(main())
