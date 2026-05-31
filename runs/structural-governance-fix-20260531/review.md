# Independent Review R3 — structural-governance-fix-20260531

> Reviewer: deepseek-v4-pro (opencode), separate session | 2026-05-31

## Verdict: PASS

The protected-path gate upgrade correctly requires BOTH TaskSpec coverage AND independent reviewer evidence. No self-approval or fake-green path is reintroduced. All six P0 blockers remain resolved.

---

## R3 Focus: Test-ProtectedPaths.ps1 — Governance Change Gate

### Old Behavior (BLOCKED unconditionally)
```
Protected paths touched → BLOCKED
Suggestion: "Ensure TaskSpec + ExecutionReport exist per SADP"
```
This was a soft suggestion — it said what to do but didn't enforce it.

### New Behavior (Two-gate admission)
```
Protected paths touched
  → Test-TaskSpecCoversViolations: Are ALL violations covered by allow_write/write_set?
  → Test-ReviewerEvidenceExists: Does any run/ dir have valid ai_guard.py evidence PASS?
  → If BOTH true → PASS (admitted through SADP evidence)
  → Otherwise → BLOCKED
```

### Self-Approval Analysis

The two-gate admission does NOT reintroduce agent self-approval:

| Attempted Bypass | Why It Fails |
|------------------|--------------|
| Executor writes a TaskSpec with wide allow_write | TaskSpec covers files but `Test-ReviewerEvidenceExists` still fails — no independent reviewer |
| Executor writes review.yaml with reviewer_role=executor | `ai_guard.py evidence` line 130: `ERROR: reviewer_role must not be executor` → exit 1 → `Test-ReviewerEvidenceExists` returns false |
| Executor writes review.yaml with reviewer_id == executor_id | `ai_guard.py evidence` line 146: `ERROR: reviewer_id must differ from executor_id` → exit 1 |
| Executor writes review.yaml with verdict=pass but has unresolved P0 | `ai_guard.py evidence` lines 158-162: `ERROR: pass verdict is invalid with unresolved P0/P1` → exit 1 |
| Executor writes review.yaml without reviewed_inputs | `ai_guard.py evidence` line 184: `ERROR: review.yaml must list reviewed_inputs` → exit 1 |
| Executor avoids review.yaml entirely | `Test-ReviewerEvidenceExists` searches for `review.yaml` → none found → returns false |
| Executor forges a review.yaml that passes ai_guard evidence | Requires a separate `reviewer_id`, valid `verdict`, complete `reviewed_inputs`, resolved P0/P1 findings — this is exactly what a real independent reviewer produces |

The executor's TaskSpec declares intent (what files it will touch). The independent reviewer validates execution (that changes are correct, safe, and complete). Neither alone is sufficient; `Test-ProtectedPaths.ps1` gates on the conjunction.

### Test-PathCoveredByPattern verification
- Exact path match ✓ (normalized forward slashes)
- `/**` prefix match ✓ (e.g., `schemas/agent-runtime/**`)
- PowerShell WildcardPattern with IgnoreCase ✓
- Invalid pattern → catch block returns $false (safe default) ✓

### Test-ReviewerEvidenceExists verification
- Calls `ai_guard.py evidence <dir>` for every `runs/*/review.yaml`
- Checks `$LASTEXITCODE -eq 0` (exit code, not string match) ✓
- Returns true if ANY run dir has valid evidence ✓
- Returns false if no run dirs, no ai_guard.py, or no valid evidence ✓

---

## Diff Self-Reference (Check 3)

`grep "^diff --git a/runs/"` on `diff.patch` → **zero matches**. The `go_evidence.py init` correctly excludes `runs/**`.

---

## Six P0 Blockers (Check 4)

| # | Blocker | Resolution | Still Addressed |
|---|---------|------------|-----------------|
| P0-1 | Evidence mode unreachable | CI (`ai-guard.yml:31`) + pre-push (`pre-push.governance.ps1:24`) + pre-commit advisory | **YES** |
| P0-2 | No evidence producers | `go_evidence.py` init/guard/finalize + chain/safety/review schemas | **YES** |
| P0-3 | review.yaml has no schema | `review.schema.json` — 6 required, enum-constrained, not(executor|fixer|coder) | **YES** |
| P0-4 | Status vocabulary misaligned | `status=[pass,fail,blocked,escalate]` + `review_status=[draft,...,rejected]` | **YES** |
| P0-5 | Gate 0 unvalidated | sadp-audit RULE 0 validates `gate_0.inventory_evidence` | **YES** |
| P0-6 | Task scope unenforced | sadp-audit calls `ai_guard.py task <file>` with real TaskSpec | **YES** |

R3 change (`Test-ProtectedPaths.ps1` upgrade) is additive — it does not remove or weaken any of these resolutions.

---

## Fake-Green Gate Audit (Check 2, re-verified)

| Path | Mechanism | Status |
|------|-----------|--------|
| executor self-review | ai_guard evidence: reviewer_role ∉ [executor,fixer,coder] | BLOCKED |
| same session_id | ai_guard evidence: reviewer_id ≠ executor_id | BLOCKED |
| pass+unresolved P0 | ai_guard evidence: verdict=pass + P0/P1 unresolved → error | BLOCKED |
| skipped evidence | ai_guard evidence: reviewed_inputs must contain all 4 files | BLOCKED |
| finalizer overrides | go_evidence.py finalize: exit-code-based, no judgment | DETERMINISTIC |
| CI bypass | ai-guard.yml → Test-ReviewerEvidence.ps1 (exit 1 blocks CI) | ENFORCED |
| pre-push bypass | pre-push.governance.ps1 step 2/4 → Test-ReviewerEvidence.ps1 | ENFORCED |
| pre-commit bypass (protected) | Test-ProtectedPaths.ps1 → TaskSpec + reviewer evidence gate | ENFORCED |
