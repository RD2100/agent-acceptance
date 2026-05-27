# Resource Integration Reviewer Playbook -- RD2100 Agent Runtime v2

> Batch Z, 2026-05-27
> Purpose: Fast-path and deep-review guidance for the human reviewer evaluating the Resource Integration Final Audit.

---

## 15-Minute Quick Review Path

If you have limited time, follow this accelerated path to verify the most critical items.

### Quick Review Checklist (15 min)

1. **Git baseline** (2 min): Run `git status --short`. Confirm only 5 new files under `docs/agent-runtime/resource-integration-*.md` and no other untracked/modified files beyond the pre-existing 13M + 6U dirty baseline. Reject if any dirty baseline file was touched.

2. **Schema parse check** (3 min): Verify `resource-integration-final-audit.md` reports PARSE_OK for all 18 schemas. Spot-check 2-3 critical schemas:
   - `resource-registry-record.schema.json` -- confirm `lifecycle_state` allOf constraint limits R0
   - `script-safety-record.schema.json` -- confirm `allowed_to_run` const = false

3. **Negative test existence** (2 min): Confirm all 9 negative test files are listed in the audit and have zero tests with expected_gate_decision=pass.

4. **Forbidden action sweep** (3 min): Review the Forbidden Action Check table (18 checks). All should read PASS.

5. **Dangerous language spot check** (3 min): Search for "approved" in `resource-registry-record.schema.json`. It should appear only in the description comment: "'approved', 'enabled', 'capability_approved', 'active', and 'installed' are NOT valid promotion_status values."

6. **Gate decision** (2 min): Confirm the Final Gate Matrix shows R0-R7 as PROCEED and Phase 6C as BLOCKED. Sign off or request deeper review.

---

## 60-Minute Deep Review Path

### Phase 1: Baseline Verification (10 min)

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1.1 | Run `git status --short` | 13 modified tracked files + 6 untracked dirs visible. 5 new audit files under docs/agent-runtime/ |
| 1.2 | Run `git diff --stat` | Changes only in the pre-existing modified files (README.md, agent-workqueue/*, docs/*.md, scripts/*.ps1) |
| 1.3 | Check `C:\Users\RD` path writes | No new files under C:\Users\RD\.claude\ from this session |
| 1.4 | Verify commit baseline | HEAD is 100a116 feat: agent-acceptance v1.0 |

### Phase 2: Schema Audit (15 min)

Go through the 18 schemas in the Schema Audit table. For each critical schema, verify one enforcement manually:

| Schema | Verification |
|--------|-------------|
| resource-registry-record.schema.json | Read the `allOf` block. Confirm: "R0 records may only use lifecycle_state: discovered, registered, or classified." |
| capability-promotion-record.schema.json | Read the `allOf` block. Confirm: human_gate_passed must be false when promotion_status is not "approved". |
| evidence-provider-record.schema.json | Confirm execution_policy enum=["forbidden"]. Read the 4 allOf blocks that reject "current_after_approved_run", "current_pass", "human_gated", "dry_run_allowed". |
| dev-frame-adapter-record.schema.json | Confirm execution_policy=["forbidden"], adapter_status range does not include "active" or "capability_approved". |
| codegraph-index-record.schema.json | Read both allOf blocks: (1) stale/unknown => trusted=false, (2) empty => trusted=false. |
| local-skill-intake-record.schema.json | Confirm auto_trigger_allowed=false, execution_allowed=false, install_allowed=false (all const). Read the evolution type allOf block. |
| memory-context-record.schema.json | Confirm access_mode="read_only", write_allowed=false, used_as_fact=false (all const). |
| script-safety-record.schema.json | Confirm execution_status=["not_run","human_required","forbidden"], allowed_to_run=false. |

### Phase 3: Negative Test Audit (15 min)

For each of the 9 negative test files, verify:

1. **File exists** and is referenced in the audit.
2. **No test has expected_gate_decision=pass** -- scan for any "PASS" in the expected gate decision column.
3. **Hard stops are correctly marked** -- spot-check 3 hard stops per file.
4. **Coverage is complete** -- each phase's primary boundary violations are covered.

Quick verification commands for each file:
- R0: Must cover script execution, MCP enablement, hook registration, memory write, skill auto-load, reindex, workqueue consumption, package manager, external clone, template overwrite, run history edit.
- R2: Must cover pytest/npm/playwright execution, aggregator, attribution, CLI, orchestrator, file modification, dependency install, external service trigger.
- R3: Must cover smoke_test.py, ai-workflow-hub, ai-workflow-hub-e2e, dev-frame modification, package install, workqueue trigger.
- R4: Must cover auto-reindex, trusted with stale/unknown/empty, index deletion, index copy, DB modification.
- R7: Must cover script execution, workqueue consumption, template overwrite, run history modification, parallel execution, -Real flag, fake dry-run, tier escalation bypass.
- Acceptance-native: Must cover missing git status, fake green, source-of-truth, MCP config, external clone, package manager, memory write, dangerous git, executor self-approval, skill intake.

### Phase 4: Cross-Consistency Audit (10 min)

Verify these 9 relationships:

1. Read `resource-registry.md` -- confirm all 8 resources have lifecycle_state in R0 range, promotion_status = registered or candidate. No "capability_approved" or "active".
3. Read `test-frame-evidence-map.md` -- confirm aggregator can_produce_gate_result=no, access_mode=forbidden.
4. Read `dev-frame-adapter-record.schema.json` example -- confirm execution_policy="forbidden", smoke_validation_policy="historical_only".
5. Read `codegraph-stale-policy.md` -- confirm stale/unknown/empty indexes must NOT be trusted, auto-reindex permanently forbidden.
6. Read `local-skill-intake-record.schema.json` -- confirm evolution skills are deferred/rejected, next_phase_blocked=true.
8. Read `acceptance-script-registry.md` -- confirm all scripts not executed, allowed_to_run=false.
9. Read `phase-6-source-lock-quarantine.md` -- confirm Phase 6C clone requires explicit approval, static review checklist exists.

### Phase 5: Gate Decision (10 min)

| Gate | Decision Options | Recommended |
|------|-----------------|-------------|
| R0 | PROCEED / BLOCKED / needs_revision | **PROCEED** -- schema passes, 25 negative tests, cross-consistency verified |
| R1 | PROCEED / BLOCKED / needs_revision | **PROCEED** -- schema passes, 28 negative tests, mcp_status=disabled enforced |
| R2 | PROCEED / BLOCKED / needs_revision | **PROCEED** -- schema passes, 30 negative tests, all components forbidden |
| R3 | PROCEED / BLOCKED / needs_revision | **PROCEED** -- schema passes, 20 negative tests, design_only enforced |
| R4 | PROCEED / BLOCKED / needs_revision | **PROCEED** -- schema passes, 20 negative tests, stale-aware enforced |
| R5 | PROCEED / BLOCKED / needs_revision | **PROCEED** -- schema passes, 25 negative tests, no execution/install enforced |
| R6 | PROCEED / BLOCKED / needs_revision | **PROCEED** -- schema passes, 23 negative tests, read_only enforced |
| R7 | PROCEED / BLOCKED / needs_revision | **PROCEED** -- schema passes, 25 negative tests, scripts not_run enforced |
| 6C | PROCEED / **BLOCKED** / needs_revision | **BLOCKED** -- source URL + clone approval required |

---

## Schema Audit Checklist

- [ ] All 18 schema files exist at expected paths
- [ ] All 18 schemas parse as valid JSON (verified by PowerShell ConvertFrom-Json)
- [ ] Each schema has correct `$schema` reference (draft/2020-12)
- [ ] Each schema has `additionalProperties: false`
- [ ] Resource-integration schemas enforce phase-appropriate enum/const restrictions
- [ ] Agent-runtime schemas enforce Phase 0-5 policy boundaries
- [ ] SourceLockRecord schema (Phase 6) correctly models quarantine workflow
- [ ] Examples in schemas match the enforcement constraints

## Negative Test Audit Checklist

- [ ] All 9 negative test files exist
- [ ] Total tests >= 200 (actual: 226)
- [ ] Zero tests have expected_gate_decision=pass
- [ ] Hard stops correctly flagged (actual: 140 of 226)
- [ ] Each test has: scenario, input report features, expected gate decision, expected findings, related rule, hard stop flag
- [ ] Each phase's critical boundary violations are covered by at least one negative test
- [ ] Test files reference the correct phase schemas and policy docs
- [ ] R2 file correctly uses `### NEG-R2-XXX` (3 hashes) instead of `##`

## Dangerous Language Audit Checklist

- [ ] Search for "approved" -- no permissive usage (enum descriptions, negative tests, and future planning only)
- [ ] Search for "installed" -- no permissive usage
- [ ] Search for "enabled" -- only in negative test scenarios
- [ ] Search for "active" -- only in forbidden lifecycle_state descriptions
- [ ] Search for "capability_approved" -- only in negative test scenarios or excluded-from-enum descriptions
- [ ] Search for "write_memory" -- always forbidden
- [ ] Search for "used_as_fact.*true" -- always forbidden/negative test
- [ ] Search for "trusted_for_current_run.*true" -- only in documented precondition context
- [ ] Search for "reindex" -- always forbidden or described as future human-gated
- [ ] Search for "npm install", "pip install" -- always forbidden
- [ ] Search for "git push", "git checkout" -- always forbidden (except Phase 6C quarantine context)
- [ ] Search for "Remove-Item", "Set-Content" -- not found (confirm absence)

## Changed Files Audit Checklist

- [ ] `git status --short` shows expected modified files (13M as of baseline)
- [ ] No new untracked files outside approved directories
- [ ] No files under C:\Users\RD modified during this session
- [ ] No files under D:\dev-frame, D:\test-frame, or D:\agent-acceptance outside docs/agent-runtime/ modified
- [ ] `git diff` shows only pre-existing changes (README.md, agent-workqueue, docs/*.md, scripts/*.ps1)
- [ ] New audit files (5) are all under docs/agent-runtime/resource-integration-*.md

---

## Final Gate Decision Tree

```
START
  |
  v
Dirty baseline preserved? ----NO----> REJECT IMMEDIATELY
  | YES
  v
All 18 schemas parse? ----NO----> REJECT (malformed schema)
  | YES
  v
Phase enums/consts correct? ----NO----> needs_revision
  | YES
  v
All 9 negative test files exist? ----NO----> needs_revision (missing coverage)
  | YES
  v
Any test has gate_decision=pass? ----YES----> REJECT (false positive)
  | NO
  v
Cross-consistency verified? ----NO----> needs_revision (inconsistency)
  | YES
  v
Zero permissive dangerous language? ----NO----> needs_revision (boundary leak)
  | YES
  v
All 18 forbidden checks pass? ----NO----> REJECT (boundary violation)
  | YES
  v
PROCEED -- All R0-R7 gates pass.
  |
  v
Phase 6C: Source URL approved? ----NO----> BLOCKED (expected, defer to 6C agent)
```

---

## What to Reject Immediately

1. **Dirty baseline touched**: Any modification to the 13M + 6U pre-existing files.
2. **Schema parse failure**: Any of the 18 schemas that does not parse as valid JSON.
3. **Permissive language**: Any dangerous term used in a permissive (granting permission) rather than forbidden/negative-test/future/description context.
4. **Expected gate_decision=pass** in any negative test file.
5. **Missing hard stop on a script execution**: R7 negative tests specifically require hard stops for any script execution scenario. If a test has "Ran script" but Hard Stop: false, reject.
7. **execution_policy not "forbidden"** in EvidenceProvider or DevFrameAdapter schemas.
8. **allowed_to_run=true** in ScriptSafetyRecord schema.

---

## What Can Be Deferred

1. **Phase 6C source lock execution**: Design is complete, execution is deferred to a separate batch. This is expected and documented.
2. **CodeGraph reindex for empty index**: The schema correctly enforces trusted=false. Reindex can be deferred to Phase 7+.
3. **WorkQueue consumption process definition**: Schemas and negative tests are in place. Actual consumption process can be defined in Phase 7.
4. **Skill execution gate process**: R5 classifies skills, Phase 6C quarantines them, Phase 7 would execute them. Gate process definition is a Phase 7 task.
5. **Rule conflict resolution process**: R5 negative test documents the requirement; implementation is a Phase 7 task.
6. **Phase 6A deferred skills re-evaluation**: ECC, AnySearch, addyosmani-agent-skills-zh were deferred for insufficient data. Re-evaluation is a Phase 6F task.

---

## What Requires Human Approval

| Item | Phase | Approval Needed |
|------|:-----:|----------------|
| R0 gate: Resource registry accepted | R0 | Human reviewer sign-off |
| R2 gate: Evidence provider accepted | R2 | Human reviewer sign-off |
| R3 gate: Dev-frame adapter accepted | R3 | Human reviewer sign-off |
| R4 gate: CodeGraph policy accepted | R4 | Human reviewer sign-off |
| R5 gate: Skill intake accepted | R5 | Human reviewer sign-off |
| R6 gate: Memory context accepted | R6 | Human reviewer sign-off |
| R7 gate: Acceptance native accepted | R7 | Human reviewer sign-off |
| Phase 6C: Source URL approval | 6C | Human authorization |
| Phase 6C: Clone into quarantine | 6C | Human authorization (separate from URL approval) |
| Any script execution (even -DryRun) | R7+ | Human gate (per-run, per-script) |
| Any CodeGraph reindex | R4+ | Human gate (5 preconditions) |
| Any skill installation | 6F+ | Human gate (post-quarantine review) |
| Any memory write | 7+ | Human gate |
| Any package installation | 7+ | Human gate (environment mutation) |

---

## Reviewer Signature Block

```
Reviewer: ____________________
Date: ________________________
Decision: [ ] PROCEED all R0-R7 gates
          [ ] PROCEED with conditions (list below)
          [ ] needs_revision (list required changes below)
          [ ] BLOCKED (list blocking issues below)

Conditions / Required Changes / Blocking Issues:
________________________________________________
________________________________________________
________________________________________________
```
