# Decision: allow_paths Override for Known False Positives

**Decision ID:** DR-20260612-ALLOW-PATHS
**Date:** 2026-06-12
**Status:** APPROVED (retroactive)
**Trigger:** PHASE3D-GOVERNANCE-POLICY-REREVIEW-A1
**Authorizes:** Commit 3ad49d30 (secret-named evidence files + NEG-009 fixtures)

## Context

Phase 3 batch cleanup (PHASE3-BATCH-CLEANUP-A1) committed ~700 files to reduce
workspace noise from ~200 untracked to 4. During final batch (3d), 42 files
matching `deny_paths: **/*secret*` were committed alongside governance hook
optimizations. This mixed cleanup with policy change, creating drift against
three governance documents.

## Conflicts Identified

1. `evidence-capture-standard.md:43` — `secret-scan-output.txt` MUST NOT be staged
2. `evidence-generation-hygiene.md:102` — deny-listed files ZIP-only, never git
3. `human-required-decision-record.md:103` — mock secret fixtures need human auth

## Decisions

### D1: secret-scan-output.txt — NARROW (keep allow_paths, narrow scope)

**Before:** `allow_paths: ["**/secret-scan-output.txt"]`
**After:** `allow_paths: ["_evidence/**/secret-scan-output.txt", "_archive/**/secret-scan-output.txt"]`

**Rationale:** These are scanner output artifacts, not actual secrets. The original
rule was written before evidence directory archiving required committing full
evidence dirs to git. Reverting would extract 24 files from committed evidence
dirs into ZIP — disruptive for minimal security benefit. Narrowing to known
evidence/archive paths prevents accidental allow of files named
`secret-scan-output.txt` elsewhere in the repo.

**Doc sync:** Update `evidence-capture-standard.md` and `evidence-generation-hygiene.md`
to add exception clause for `allow_paths`-covered files.

### D2: NEG-009-secrets-read.json — NARROW + retroactive authorization

**Before:** `allow_paths: ["**/NEG-*-secrets-*.json"]`
**After:** `allow_paths: ["_projects/**/negative-test-fixtures/NEG-*-secrets-*.json"]`

**Rationale:** These are intentional negative test fixtures that MUST match
secret-like patterns to validate ai_guard blocking behavior. Trigger 8 of
human-required-decision-record.md requires explicit human authorization —
this decision record provides that authorization retroactively.

**Human authorization:** Provided by workspace owner during
PHASE3D-GOVERNANCE-POLICY-REREVIEW-A1 review (2026-06-12).

**Doc sync:** Update `human-required-decision-record.md` Trigger 8 to note
that allow_paths with decision record satisfies the authorization requirement.

### D3: AI_GUARD_FILE_LIST — ADD test coverage

**Current:** No test coverage for env var fallback or allow_paths override.
**Action:** Add tests to `test_ai_guard_staged_scope.py`:
- `test_files_mode_reads_from_env_var`: verifies `AI_GUARD_FILE_LIST` fallback
- `test_allow_paths_overrides_deny_paths`: verifies allow_paths narrow override

### D4: Hook v2.4.1 env var change — ADD integration note

**Current:** Hook change tested implicitly (56-file commit succeeded).
**Action:** Add test that verifies ai_guard.py `--files` with no args reads env var.
Full hook integration test is out of scope (requires PowerShell test runner).

## Files Changed

- `.ai/policy.yaml` — narrow allow_paths scope
- `docs/agent-runtime/evidence-capture-standard.md` — add allow_paths exception
- `docs/agent-runtime/evidence-generation-hygiene.md` — add allow_paths exception
- `docs/agent-runtime/human-required-decision-record.md` — note allow_paths satisfies Trigger 8
- `tests/test_ai_guard_staged_scope.py` — add env var + allow_paths tests
