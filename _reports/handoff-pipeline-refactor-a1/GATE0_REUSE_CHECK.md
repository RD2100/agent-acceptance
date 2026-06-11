# GATE0 Reuse-Before-Build Check — HANDOFF-PIPELINE-REFACTOR-A1

> Phase: 0 (inventory only, no implementation)
> Agent: minimax-m3 (Claude Code harness)
> Generated: 2026-06-08 20:34 (local)
> Repo: D:/agent-acceptance
> Companion artifact: `GATE0_REUSE_CHECK.json` (machine-readable)
> Companion artifact: `SHELL_HEALTH_BEFORE.txt`

This report answers SADP core-008 (Reuse-before-Build): **what already exists that makes the proposed new construction unnecessary?**

---

## 0. Shell + repo verification

- `pwd && date && echo FRESH_SHELL_OK && git rev-parse --is-inside-work-tree && git status --short`
- Returned synchronously in < 1s. `FRESH_SHELL_OK` printed. `git rev-parse` returned `true`. ✅
- Working tree is **dirty (pre-existing)** — 17 modified, 1 deleted, ≥30 untracked at root. Not caused by this run.
- **Environment quirk**: each Bash tool call starts in `D:\dev-frame-opencode` and cwd is reset back after the call. All Phase 0 commands used `cd "D:/agent-acceptance" && ...` to compensate.

---

## 1. Source-of-truth inventory (P0/P1/P2 candidates located)

| Concern | Status | Path(s) | Notes |
|---|---|---|---|
| Project Index | PARTIAL — paper-scoped only | `_reports/PAPER_PROJECT_INDEX.json`, `_reports/PAPER_PROJECT_INDEX_GPT_VIEW.md` (builder: `scripts/paper_project_index.py`) | **There is no general project-wide index file.** Only paper modules M1-M12. Phase 1 must decide: build a general index, or document the absence. |
| Issue ledger | MULTIPLE CANDIDATES, no canonical pick | `.ai/module_ledger/{M1,M2,M3}.json`, `.ai/tasks/*.yaml` (24 files), `.ai/current-task.yaml`, `tasks/` (not yet inspected), `docs/WORKFLOW_AUDIT_LEDGER.yaml` (mentioned in BOOT_CONTEXT, not verified) | User decision needed in Phase 1. |
| Captured GPT verdicts | YES, multiple stores | `evidence_packs/<task>/GPT_REVIEW_RESULT*.txt`, `evidence_packs/GPT_REPLY_56.txt`, `evidence_packs/GPT_REPLY_57.txt`, `GPT_*.txt` at repo root (≥24 files, UNTRACKED), `_reports/_c7_gpt_response_*.txt`, `_reports/m{N}_round{N}_gpt_response.txt` | Verifier: `scripts/verify_gpt_reply.py` (enforces `END_OF_GPT_RESPONSE` marker). |
| Evidence-pack schema/convention | YES, enforced | Required files: `CLOSURE_REPORT.md`, `GPT_REVIEW_PROMPT.md`, `PACK_MANIFEST.md`, `SAFETY_ATTESTATION.md`. Required dirs: `actual_deliverables/`, `reports/`. Expected reports include `TARGETED_TEST_OUTPUT.txt`, `TEST_OUTPUT.txt`. | Linter: `scripts/evidence_pack_linter.py`. Pre-submit gate: `scripts/pre_gpt_review_gate.py`. |
| GPT review transaction runner | YES, exists | `scripts/gpt_review_transaction.py` (pre-gate → linter → CDP submit (manual) → verify → closure) | Capture: `scripts/capture_gpt_reply.py`. Verify: `scripts/verify_gpt_reply.py`. Queue: `scripts/review_queue.py` (queue dir `.ai/review_queue/` currently empty). |
| `verify_gpt_reply.py` | YES, exists | `scripts/verify_gpt_reply.py` | Enforces END_OF_GPT_RESPONSE + `overall_judgment` regex. Treats absence as `verdict_allowed=False`. Exactly matches the P0 rule "未读取 GPT 回复，不得报告 verdict". |
| Review queue | YES, exists | `scripts/review_queue.py` (lifecycle: queued → submitted → gpt_replied → accepted/blocked → closed, MAX_ACTIVE=1) | Queue dir currently empty — no in-flight ticket. |
| Existing handoff/boot/history files | YES, multiple — and none marked SUPERSEDED | `HANDOFF.md`, `HANDOFF_V5.md`, `HANDOFF_V6.md`, `BOOT_CONTEXT.md`, `PROJECT_HISTORY.md`, `PROJECT_HISTORY_FINAL.md`, `HISTORY_ANALYSIS.md` (all at repo root) | High risk: a new agent reading the repo cold could pick any of these as "current". `LEGACY_HANDOFF_INVENTORY.md` is needed. |
| Memory compiler outputs | YES, exists | `.claude/skills/claude-memory-compiler/knowledge/{gpt-review-loop,paper-pipeline,shell-health}.md`. Sync: `scripts/sync_compiled_memory.py`. Local memory mirror: `memory/{index.md,knowledge/,tasks/,daily/}`. | Compiler: `scripts/memory_compiler.py`. Memory linter: `scripts/memory_lint.py`. Privacy validator: `scripts/validate_context_memory.py`. |
| Pre-existing handoff_*.py scripts | NONE | — | All proposed `handoff_*.py` names are free. |
| Pre-existing stale-check capability | NONE | — | Real gap. |
| Pre-existing safety-scan capability | YES (reusable) | `scripts/validate_context_memory.py` (FAIL_CLOSED_PATTERNS list covers `real_paper_full_text`, `raw_paper_text`, `博士论文正文`, `用户论文全文`, api_key, etc.); `scripts/memory_lint.py` L-002; `scripts/compress_project_context.py` `privacy_ok()` | Recommended: thin wrapper, do **not** duplicate pattern list. |
| Pre-existing source-of-truth map | NONE | — | Real gap. |
| Test suite | 36 test files in `tests/` | incl. `test_boot_context_builder.py`, `test_memory_compiler.py`, `test_context_memory_privacy.py`, `test_handoff_trigger.py`, `test_gpt_reply_completeness.py`, `test_review_queue.py` | None exercise the proposed orchestrators. Per `gsd-tdd` rule: TDD RED → GREEN → REGRESSION required. |

---

## 2. Reuse decisions (per requested write_set item)

| Proposed new artifact | Decision | Existing capability | Delta justification |
|---|---|---|---|
| `scripts/handoff_compiler.py` | **REUSE + thin wrapper** (~150-250 LoC) | `build_boot_context.py`, `compress_project_context.py`, `validate_handoff.py` | New orchestrator only: call `build_boot_context` as trunk, inject source-of-truth priority section, emit `PASTE_BLOCK_DRAFT_FOR_NEW_GPT.txt` + `HANDOFF_EVIDENCE_MAP.json`, refuse to mark "approved". Do not rewrite compression logic. |
| `scripts/handoff_stale_check.py` | **NEW required** (~200 LoC) | none truly comparable | Compares test counts / module statuses / verdicts / commit dates across BOOT_CONTEXT, memory/index.md, PROJECT_HISTORY.md, and live repo state. **Concrete need**: BOOT_CONTEXT.md line 29 says "232 PASS" and line 35 says "247 PASS" — an in-file contradiction current tooling does not detect. |
| `scripts/handoff_safety_scan.py` | **REUSE** (~40-80 LoC wrapper) | `validate_context_memory.py`, `memory_lint.py L-002`, `compress_project_context.privacy_ok()` | Wrap `validate_context_memory.check()` against handoff draft + paste block. Emit `HANDOFF_SAFETY_SCAN.md`. **Do not** create a parallel pattern list (drift risk between two safety guards). |
| `scripts/handoff_source_map.py` | **NEW required** (~250 LoC) | partial — `verify_gpt_reply.py`, `gpt_review_transaction.py` are per-reply, not multi-claim mappers | Enumerates P0/P1/P2/P3 hierarchy and maps each handoff claim → `{source_layer, source_path, sha256, timestamp}`. Output: `HANDOFF_EVIDENCE_MAP.json`. |
| `schemas/handoff_compiler_result.schema.json` | **NEW required** | reference: `boot_context.schema.json`, `gpt_review_result.schema.json` | Describes orchestrator output envelope. Reuse field names from `boot_context.schema.json` where overlapping to reduce semantic drift. |
| `schemas/handoff_evidence_map.schema.json` | **NEW required** | none comparable | Distinct shape from review_result. |
| `schemas/minimax_m3_observation.schema.json` | **NEW required** | none | First-of-its-kind. Must enforce the 8 dimensions and required fields specified in the task prompt. |
| `tests/test_handoff_{compiler,stale_check,safety_scan,source_map}.py` | **NEW required** (TDD RED first) | related: `test_boot_context_builder.py`, `test_memory_compiler.py`, `test_context_memory_privacy.py`, `test_gpt_reply_completeness.py` | Existing tests do not cover the new orchestrators. Use synthetic fixtures only; never real paper text. |

---

## 3. Stale findings (P0 = HIGH priority)

| ID | Severity | Where | Evidence | Implication |
|---|---|---|---|---|
| **STALE-01** | HIGH | `BOOT_CONTEXT.md` | Line 29 says `测试 232 PASS (170 baseline + 62 new)`. Line 35 says `247 tests PASS`. **Same file, two numbers.** | Any handoff built from BOOT_CONTEXT inherits the contradiction. Stale check must surface this. |
| **STALE-02** | MEDIUM | `memory/index.md`, `BOOT_CONTEXT.md`, `PROJECT_HISTORY.md` | All three quote `247 PASS`. No fresh pytest run executed during Phase 0 to re-verify. | P1+P2 agree but neither is re-verified against P0 (live test output). Standard practice: re-run pytest, compare. |
| **STALE-03** | INFO (but high learning value) | previous coding-agent reply (this session) | The previous reply (mine, before Phase 0) cited `296 PASS` as fact. Phase 0 found **no written source** for 296 anywhere in BOOT_CONTEXT, memory, PROJECT_HISTORY, or git log. The agent likely fabricated it from conversational context. | Strongest possible evidence for why memory compiler / coding-agent summaries **cannot** be promoted to P0. This will be the seed entry in `MINIMAX_M3_OBSERVATION_LOG` once Phase 1 is authorized. (Flagged for user assessment, not yet written to disk.) |
| **STALE-04** | MEDIUM | `BOOT_CONTEXT.md` vs recent git log | BOOT_CONTEXT recommends "wait for next GPT-authorized task" and says PROJECT-HISTORY-BOOT-MEMORY-SYNC-A1 is done. But last 10 commits are **all** paper M1-M12 R2/R3 review work, committed under date 2026-06-08. | BOOT_CONTEXT is at least a few commits behind real activity. Stale check must compare BOOT_CONTEXT "last updated" vs `git log -1 --format=%cI`. |
| **STALE-05** | MEDIUM | `memory/knowledge/paper_privacy.md` vs repo state | Memory says "论文处理被 freeze. 不进行 PAPER-C3 / 真实论文处理". But `evidence_packs/paper-c3-dry-run/` exists, `_reports/PAPER_PROJECT_INDEX.json` shows 12 active modules with `in_progress` status, recent commits are paper reviews. | Direct memory-vs-reality contradiction. **User must clarify before HANDOFF_DRAFT can honestly describe current module status.** |

---

## 4. Conflict & high-risk operation register

- **Naming conflicts**: none. All proposed `handoff_*.py`, `handoff_*.schema.json`, `minimax_m3_observation.schema.json`, and `test_handoff_*.py` filenames are free.
- **Schema conflicts**: none, but **recommend** aligning new schema field names with existing `boot_context.schema.json` and `gpt_review_result.schema.json` to reduce semantic drift across the codebase.
- **Old-handoff misuse risk**: **HIGH**. `HANDOFF.md`, `HANDOFF_V5.md`, `HANDOFF_V6.md`, `PROJECT_HISTORY.md`, `PROJECT_HISTORY_FINAL.md`, and ≥24 `GPT_*.txt` files sit at repo root with no SUPERSEDED notice. A cold-starting agent could grab any of them as "current".
- **Human-required decisions before Phase 1 begins implementation**:
  1. **Project Index scope**: build a general project-wide index, or document the absence? (Currently only paper-scoped exists.)
  2. **Canonical issue ledger pick**: `.ai/module_ledger/` (paper) + `.ai/tasks/` (governance)? Or one of `tasks/`, `docs/WORKFLOW_AUDIT_LEDGER.yaml`?
  3. **"Paper frozen vs paper active" contradiction (STALE-05)**: which side is truth? This is a project-state question, not a code question.

---

## 5. Phase 1 recommendation

**Proceed to Phase 1: YES, conditional on user resolving the two human-required questions above.**

### Minimum write set proposal (ordered, smallest-first, no execution yet)

**Block A — documents only (no code):**
1. `HANDOFF_SOURCE_OF_TRUTH.md` (root) — defines P0/P1/P2/P3 hierarchy authoritatively.
2. `LEGACY_HANDOFF_INVENTORY.md` (root) — inventories existing handoff/history files with `current_replacement` pointer. **Does not delete or modify originals.**
3. `.ai/tasks/handoff-pipeline-refactor-a1.yaml` — TaskSpec entry.
4. `memory/tasks/handoff-pipeline-refactor-a1.md` — memory task pointer.

**Block B — TDD pairs (test RED → script GREEN):**
5. `tests/test_handoff_safety_scan.py` + `scripts/handoff_safety_scan.py` (thinnest wrapper; safest to start)
6. `tests/test_handoff_stale_check.py` + `scripts/handoff_stale_check.py`
7. `tests/test_handoff_source_map.py` + `scripts/handoff_source_map.py`
8. `tests/test_handoff_compiler.py` + `scripts/handoff_compiler.py`

**Block C — schemas (alongside their consumers):**
9. `schemas/handoff_compiler_result.schema.json`
10. `schemas/handoff_evidence_map.schema.json`
11. `schemas/minimax_m3_observation.schema.json`

**Block D — draft outputs (generated by scripts above):**
12. `_reports/handoff-pipeline-refactor-a1/HANDOFF_STALE_CHECK.{md,json}`
13. `_reports/handoff-pipeline-refactor-a1/HANDOFF_SAFETY_SCAN.md`
14. `_reports/handoff-pipeline-refactor-a1/HANDOFF_EVIDENCE_MAP.json`
15. `_reports/handoff-pipeline-refactor-a1/HANDOFF_DRAFT_FOR_GPT.md`
16. `_reports/handoff-pipeline-refactor-a1/PASTE_BLOCK_DRAFT_FOR_NEW_GPT.txt`
17. `_reports/handoff-pipeline-refactor-a1/TARGETED_TEST_OUTPUT.txt`
18. `_reports/handoff-pipeline-refactor-a1/SAFETY_ATTESTATION.md`
19. `_reports/minimax-m3-observation/MINIMAX_M3_OBSERVATION_LOG.md`
20. `_reports/minimax-m3-observation/MINIMAX_M3_EVIDENCE_TABLE.json`

**Block E — evidence pack (last):**
21. `evidence_packs/handoff-pipeline-refactor-a1/{actual_deliverables/, reports/, CLOSURE_REPORT.md, GPT_REVIEW_PROMPT.md, PACK_MANIFEST.md, SAFETY_ATTESTATION.md, closure-pack.zip}`

### Explicit Phase 1 forbiddens (carried from task prompt)

- ❌ delete / move / rename `HANDOFF.md`, `HANDOFF_V5.md`, `HANDOFF_V6.md`, `PROJECT_HISTORY.md`, `PROJECT_HISTORY_FINAL.md`, any `GPT_*.txt` at root.
- ❌ rewrite content inside any legacy file. Only **append** a SUPERSEDED notice — and only if user explicitly authorizes that sub-step (not auto-applied).
- ❌ promote any draft to `*_APPROVED_*` before a captured GPT verdict exists.
- ❌ include real paper full text, original paragraphs, advisor comments in any new artifact.
- ❌ auto-commit / auto-push.

---

## 6. Phase 0 summary for user

- ✅ Shell healthy, repo confirmed, no out-of-scope writes.
- ✅ Located all P0/P1/P2 source candidates.
- ⚠️ 3 of 4 proposed new scripts have substantial existing reuse paths (`handoff_compiler.py` partial, `handoff_safety_scan.py` heavy reuse). The savings: avoid duplicating the safety-pattern list (drift risk) and avoid re-implementing compression/boot-context logic.
- 🔴 5 stale findings, 2 of them HIGH/MEDIUM and 1 (STALE-05) is a true project-state question only the user can resolve.
- 🔴 0 old handoff files have SUPERSEDED markers → cold-start ambiguity risk is real.
- 🟡 `296 PASS` from the previous turn appears to be agent fabrication (no source). Honest disclosure, recorded here, **will become** the seed observation for Minimax-M3 capability log once Phase 1 starts.

### Stop point reached

Phase 0 ends here. Awaiting your decision on:

1. **Resolve STALE-05** (paper frozen vs active)?
2. **Pick canonical issue ledger** (or accept agent's inference: `.ai/module_ledger/` + `.ai/tasks/`)?
3. **Authorize Phase 1 Block A** (4 docs first, no code yet), or **authorize full Phase 1**?

END_OF_GATE0_REUSE_CHECK
