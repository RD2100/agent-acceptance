# R0 Reviewer Checklist -- RD2100 Agent Runtime v2

> Batch R0-C, 2026-05-27
> Phase: R0 (Registry & Classification Only)
> Purpose: 10-step review process for R0 batch outputs

## Hard Boundaries Reminder

R0 produces registration records and classification decisions only. No resource may be executed, enabled, installed, or configured at R0. All capability enablement is deferred to R1-R7.

---

## Step 1: Changed Files Check

Verify that only R0-approved outputs were modified. Compare pre-batch and post-batch git status.

### Procedure

1. Capture `git status --short` before any batch work begins (INV-006)
2. After batch completes, capture `git status --short` again (INV-007)
3. Diff the two snapshots line-by-line (INV-008)

### R0-C Approved Output Paths

Only these files may appear as new or modified:

| Approved File | Expected Status |
|---------------|----------------|
| `docs/agent-runtime/r0-reviewer-checklist.md` | ?? (new) |
| `docs/agent-runtime/r0-negative-tests.md` | ?? (new) |

### Dirty Baseline Files (Must Be Unchanged)

| File | Pre-Batch Status |
|------|-----------------|
| README.md | M |
| agent-workqueue/QUEUE_INDEX.md | M |
| agent-workqueue/cleanup-dryrun.queue.json | M |
| agent-workqueue/docs-quality.queue.json | M |
| agent-workqueue/local-quality.queue.json | M |
| agent-workqueue/recovery-regression.queue.json | M |
| agent-workqueue/release-readiness.queue.json | M |
| docs/FLOW_CATALOG.md | M |
| docs/NEXT_STAGE_BACKLOG.md | M |
| docs/RUNBOOK.md | M |
| scripts/Run-WorkQueue.ps1 | M |
| scripts/Test-WorkQueue.ps1 | M |
| scripts/examples/batch-docs-quality.json | M |

### Check Result

| Check | Expected | Actual |
|-------|----------|--------|
| Dirty baseline files unchanged | 13 M files show same hash | |
| Untracked directories unchanged | .claude/, .codegraph/, hooks/, rules/, schemas/, skills-inbox/, templates/ unchanged | |
| New files only in approved paths | Only docs/agent-runtime/r0-*.md | |
| No unexpected modifications | Zero | |

**Decision**: [ ] PASS / [ ] FAIL -- proceed to Step 2

---

## Step 2: Approved Outputs Check

Verify all writes were within the approved output scope defined in the batch plan and in resource-integration-plan.md.

### Approved Write Paths for R0

| Path Pattern | Purpose |
|-------------|---------|
| `docs/agent-runtime/resource-*.md` | Resource classification documents |
| `docs/agent-runtime/r0-*.md` | R0 batch-specific outputs |
| `schemas/resource-integration/*.json` | Resource integration schemas |

### Forbidden Write Paths

| Path | Reason |
|------|--------|
| `C:\Users\RD\*` | Outside project root; personal files |
| `README.md` | Dirty baseline -- must not be modified |
| `AGENTS.md` | Untracked baseline -- must not be modified |
| `scripts/*` | Dirty baseline and P1-controlled |
| `agent-workqueue/*` | Dirty baseline and P1-controlled |
| `hooks/*` | Untracked baseline |
| `rules/*` | Untracked baseline |
| `.claude/*` | Untracked baseline |
| `.codegraph/*` | Untracked baseline |
| `skills-inbox/*` | Untracked baseline |
| `templates/*` | Untracked baseline |
| `docs/FLOW_CATALOG.md` | Dirty baseline |
| `docs/NEXT_STAGE_BACKLOG.md` | Dirty baseline |
| `docs/RUNBOOK.md` | Dirty baseline |
| `docs/COMMAND_CHEATSHEET.md` | Untracked baseline |
| `docs/SINGLE_PROJECT_ADOPTION.md` | Untracked baseline |
| `docs/SINGLE_PROJECT_QUEUE_SPEC.md` | Untracked baseline |

### Check Result

| Check | Expected | Actual |
|-------|----------|--------|
| Writes within approved scope | All writes match approved path patterns | |
| No writes to forbidden paths | Zero writes outside approved scope | |
| No writes to C:\Users\RD | Zero | |
| No baseline file mutation | 13M + 6U unchanged | |

**Decision**: [ ] PASS / [ ] FAIL -- proceed to Step 3

---

## Step 3: Forbidden Action Check

Verify compliance with R0 Hard Boundary defined in resource-integration-plan.md.

### R0 Forbidden Actions (All Must Be False)

| # | Forbidden Action | Detected? | Evidence |
|---|-----------------|-----------|----------|
| 1 | Script executed (PowerShell, Python, shell) | [ ] NO / [ ] YES | |
| 2 | MCP enabled or registered | [ ] NO / [ ] YES | |
| 3 | Hooks registered or configured | [ ] NO / [ ] YES | |
| 4 | Memory written (memory/*.md, MEMORY.md, ACTIVE.md, agent-state.db) | [ ] NO / [ ] YES | |
| 5 | C:\Users\RD written | [ ] NO / [ ] YES | |
| 6 | Git mutations (commit, push, reset, clean, stash) | [ ] NO / [ ] YES | |
| 7 | Skill auto-loaded | [ ] NO / [ ] YES | |
| 8 | CodeGraph reindexed | [ ] NO / [ ] YES | |
| 9 | WorkQueue consumed (task dispatched) | [ ] NO / [ ] YES | |
| 10 | Package manager used (npm install, pip install, yarn) | [ ] NO / [ ] YES | |
| 11 | External source cloned | [ ] NO / [ ] YES | |
| 12 | UI automation used (computer-use tools) | [ ] NO / [ ] YES | |

### Check Result

| Check | Expected | Actual |
|-------|----------|--------|
| Forbidden actions count | 0 | |

**Decision**: [ ] PASS / [ ] FAIL -- proceed to Step 4

---

## Step 4: Resource Registry Coverage Check

Verify all 8 resource categories are registered with required fields, per resource-registry.md and resource-registry-record.schema.json.

### Required Fields Per Resource

Each resource must have these 19 required fields per the JSON schema:

| # | Required Field | Type |
|---|---------------|------|
| 1 | resource_id | string (unique) |
| 2 | resource_name | string |
| 3 | resource_type | enum (8 values) |
| 4 | path_or_reference | string |
| 5 | path_status | enum (5 values) |
| 6 | runtime_layer | enum (8 values) |
| 7 | access_mode | enum (6 values) |
| 8 | risk_level | enum (4 values) |
| 9 | lifecycle_state | enum (12 values) |
| 10 | promotion_status | enum (4 values, max=candidate) |
| 11 | allowed_actions | array (non-empty) |
| 12 | forbidden_actions | array (non-empty) |
| 13 | human_gate_required | boolean |
| 14 | contract_mapping | array |
| 15 | evidence_requirements | array |
| 16 | local_verification_status | enum (5 values) |
| 17 | verification_gaps | array |
| 18 | next_phase | string |
| 19 | (schema: additionalProperties=false) | No extra fields |

### Registered Resources (from resource-registry.md)

| # | Resource ID | Name | Type | Risk | All Fields Present? |
|---|-------------|------|------|------|---------------------|
| 2 | res-devframe-002 | dev-frame | repository | high | [ ] YES / [ ] NO |
| 3 | res-testframe-003 | test-frame | test_framework | high | [ ] YES / [ ] NO |
| 4 | res-codegraph-004 | CodeGraph | code_intelligence | high | [ ] YES / [ ] NO |
| 5 | res-localskills-005 | Local Skills | skills_collection | high | [ ] YES / [ ] NO |
| 6 | res-rd2100memory-006 | RD2100 Memory | memory_system | high | [ ] YES / [ ] NO |
| 7 | res-clauderules-007 | Claude Plans/Rules | rules_config | medium | [ ] YES / [ ] NO |
| 8 | res-agentacceptance-008 | agent-acceptance Native | native_runtime | high | [ ] YES / [ ] NO |

### Check Result

| Check | Expected | Actual |
|-------|----------|--------|
| Total resources registered | 8 | |
| Resources with all required fields | 8 | |
| Resources with non-empty forbidden_actions | 8 | |
| Resources with non-empty allowed_actions | 8 | |

**Decision**: [ ] PASS / [ ] FAIL -- proceed to Step 5

---

## Step 5: High/Critical Resource Controls

Verify that all high and critical risk resources have the mandatory safety controls.

### Required Controls for High/Critical

Per resource-risk-matrix.md and resource-registry.md:

1. **human_gate_required**: MUST be `true`
2. **forbidden_actions**: MUST be non-empty array with specific, enforceable entries
3. **risk_level**: MUST be `high` or `critical`
4. **promotion_status**: MUST NOT be beyond `candidate` at R0

### Per-Resource Check

| Resource ID | Risk | human_gate_required | forbidden_actions non-empty | promotion_status <= candidate |
|-------------|------|:---:|:---:|:---:|
| res-devframe-002 | high | [ ] Y / [ ] N | [ ] Y / [ ] N | [ ] Y / [ ] N |
| res-testframe-003 | high | [ ] Y / [ ] N | [ ] Y / [ ] N | [ ] Y / [ ] N |
| res-codegraph-004 | high | [ ] Y / [ ] N | [ ] Y / [ ] N | [ ] Y / [ ] N |
| res-localskills-005 | high | [ ] Y / [ ] N | [ ] Y / [ ] N | [ ] Y / [ ] N |
| res-rd2100memory-006 | high | [ ] Y / [ ] N | [ ] Y / [ ] N | [ ] Y / [ ] N |
| res-agentacceptance-008 | high | [ ] Y / [ ] N | [ ] Y / [ ] N | [ ] Y / [ ] N |

Note: res-clauderules-007 is medium risk -- human gate not mandatory (but set to true as a precaution).

### R0 Promotion Constraint Check

| Resource ID | lifecycle_state | promotion_status | lifecycle_state valid at R0? | promotion_status valid at R0? |
|-------------|----------------|-----------------|:---:|:---:|
| res-devframe-002 | registered | registered | [ ] Y | [ ] Y |
| res-testframe-003 | registered | registered | [ ] Y | [ ] Y |
| res-codegraph-004 | registered | registered | [ ] Y | [ ] Y |
| res-localskills-005 | registered | registered | [ ] Y | [ ] Y |
| res-rd2100memory-006 | registered | registered | [ ] Y | [ ] Y |
| res-clauderules-007 | registered | registered | [ ] Y | [ ] Y |
| res-agentacceptance-008 | registered | registered | [ ] Y | [ ] Y |

### Check Result

| Check | Expected | Actual |
|-------|----------|--------|
| High/critical resources with human_gate_required=true | 7/7 | |
| High/critical with non-empty forbidden_actions | 7/7 | |
| No resource promoted beyond candidate at R0 | 8/8 | |
| No lifecycle state beyond R0 scope | 8/8 | |

**Decision**: [ ] PASS / [ ] FAIL -- proceed to Step 6

---

## Step 6: Schema Validation

Verify both JSON schemas parse correctly and enforce R0 constraints.

### Checklist for resource-registry-record.schema.json

| # | Check | Expected | Actual |
|---|-------|----------|--------|
| 1 | Valid JSON syntax | Parse without error | [ ] Y / [ ] N |
| 2 | `$schema` is draft-2020-12 | Correct | [ ] Y / [ ] N |
| 3 | `$id` matches canonical path | `https://agent-acceptance.rd2100/schemas/resource-integration/resource-registry-record.schema.json` | [ ] Y / [ ] N |
| 4 | `resource_type` enum has 8 values | mcp_server, repository, test_framework, code_intelligence, skills_collection, memory_system, rules_config, native_runtime | [ ] Y / [ ] N |
| 5 | `promotion_status` enum excludes capability_approved | Only: registered, candidate, deferred, rejected | [ ] Y / [ ] N |
| 6 | `lifecycle_state` enum includes capability_approved (valid as a state, but R0 cannot set it) | 12 values including capability_approved | [ ] Y / [ ] N |
| 7 | `risk_level` enum has 4 values | low, medium, high, critical | [ ] Y / [ ] N |
| 8 | `access_mode` enum has 6 values | snapshot_only, read_only, dry_run_candidate, reference_only, human_gated, forbidden | [ ] Y / [ ] N |
| 9 | `additionalProperties` is `false` | No extra fields allowed | [ ] Y / [ ] N |

### Checklist for capability-promotion-record.schema.json

| # | Check | Expected | Actual |
|---|-------|----------|--------|
| 1 | Valid JSON syntax | Parse without error | [ ] Y / [ ] N |
| 2 | `$schema` is draft-2020-12 | Correct | [ ] Y / [ ] N |
| 3 | `promotion_gate` enum has 6 gates | registered_to_candidate through capability_proposed_to_capability_approved | [ ] Y / [ ] N |
| 4 | `promotion_status` enum has 5 values | not_started, pending_human_review, approved, rejected, blocked | [ ] Y / [ ] N |
| 5 | `promotion_status` does not include capability_approved | Only the 5 values above | [ ] Y / [ ] N |
| 6 | `human_gate_passed` constraint enforces `allOf` | If promotion_status is not "approved", human_gate_passed MUST be false | [ ] Y / [ ] N |
| 7 | `additionalProperties` is `false` | No extra fields allowed | [ ] Y / [ ] N |

### Cross-Schema Consistency Check

| # | Check | Expected | Actual |
|---|-------|----------|--------|
| 1 | `resource_id` field names match between schemas | Both use `resource_id` | [ ] Y / [ ] N |
| 2 | promotion_status values in registry schema vs promotion schema are consistent | Registry: registered/candidate; Promotion: not_started/pending_human_review/approved | [ ] Y / [ ] N |
| 3 | Lifecycle/promotion constraints do not contradict | Registry R0 cannot promote; Promotion tracks gate progression | [ ] Y / [ ] N |

### Check Result

| Check | Expected | Actual |
|-------|----------|--------|
| resource-registry-record.schema.json validates | PASS | |
| capability-promotion-record.schema.json validates | PASS | |
| Cross-schema consistency | PASS | |

**Decision**: [ ] PASS / [ ] FAIL -- proceed to Step 7

---

## Step 7: Fake Green Detection

Per INV-009 (P0 Hard Stop), verify no FAILED/BLOCKED status was reported as PASS.

### Fake Green Patterns to Detect

| # | Pattern | Check |
|---|---------|-------|
| 1 | FAILED reported as PASS | Any task with exit code 2 (INV-010) but status "completed" or "pass" |
| 2 | BLOCKED reported as PASS | Any task with exit code 1 but status "completed" or "pass" |
| 3 | Skipped validation marked pass | Any gate check skipped without explicit SKIPPED status and documented reason |
| 4 | Unknown marked as verified | Any resource with local_verification_status="verified" but no supporting evidence |
| 5 | Unavailable tool marked pass | Any check using a forbidden/unavailable tool reported as PASS |
| 6 | Historical run treated as current | Any RunSpec with old timestamp reported as current evidence |
| 7 | Flaky test reported as PASS (INV-011) | Known flaky test failure reported as PASS instead of BLOCKED |
| 8 | Executor self-signed GateResult (INV-028) | signer_role="executor" on a gate that requires reviewer |
| 9 | Implicit gate result assumed (INV-029) | Gate check documented as PASS without explicit GateResult record |
| 10 | human_gate_passed=true without reviewer approval | promotion_status is not "approved" but human_gate_passed is true |

### Detection Procedure

1. Cross-reference all reported task statuses with exit codes (INV-010)
2. For each GateResult, verify an explicit result field exists (INV-029)
3. Check all ExecutionReport status fields against gate evidence
4. Verify no "verified" status claims without supporting evidence (INV-032)
5. Confirm signer_role on all GateResult records is not "executor" for approval gates

### Check Result

| Check | Expected | Actual |
|-------|----------|--------|
| Fake green instances detected | 0 | |
| Exit code / status consistency | All consistent | |
| Gate results explicit | All explicit | |
| Evidence backing claims | All backed | |
| No executor self-approval | Zero instances | |

**Decision**: [ ] PASS / [ ] FAIL -- proceed to Step 8

---

## Step 8: Risk Matrix Completeness

Verify all 13 risk categories from resource-risk-matrix.md are covered with gate decisions.

### Required Fields Per Risk Category

Each of the 13 risk categories must have these 9 fields:

- risk_category
- affected_resources
- risk_level
- primary_threat
- current_control
- control_gap
- forbidden_actions
- gate_decision
- next_phase_policy

### Risk Category Coverage Check

| # | Risk Category | Affected Resources | Risk Level | Gate Decision Present? | Forbidden Actions? |
|---|---------------|-------------------|------------|:---:|:---:|
| 2 | Scripts (PowerShell) | res-agentacceptance-008 | high | [ ] Y / [ ] N | [ ] Y / [ ] N |
| 3 | Hooks (audit ps1) | res-agentacceptance-008 | high | [ ] Y / [ ] N | [ ] Y / [ ] N |
| 4 | Skills (local) | res-localskills-005 | high | [ ] Y / [ ] N | [ ] Y / [ ] N |
| 5 | Memory (RD2100) | res-rd2100memory-006 | high | [ ] Y / [ ] N | [ ] Y / [ ] N |
| 6 | CodeGraph | res-codegraph-004 | high | [ ] Y / [ ] N | [ ] Y / [ ] N |
| 7 | WorkQueue | res-agentacceptance-008 | high | [ ] Y / [ ] N | [ ] Y / [ ] N |
| 8 | Templates | res-agentacceptance-008 | medium | [ ] Y / [ ] N | [ ] Y / [ ] N |
| 9 | Historical Runs | res-agentacceptance-008 | medium | [ ] Y / [ ] N | [ ] Y / [ ] N |
| 10 | Evidence Providers | res-testframe-003 | high | [ ] Y / [ ] N | [ ] Y / [ ] N |
| 11 | UI Automation | res-agentacceptance-008 (indirect) | critical | [ ] Y / [ ] N | [ ] Y / [ ] N |
| 12 | Package Managers | res-devframe-002, res-testframe-003, res-agentacceptance-008 | high | [ ] Y / [ ] N | [ ] Y / [ ] N |
| 13 | External Sources | res-devframe-002, res-agentacceptance-008 | medium | [ ] Y / [ ] N | [ ] Y / [ ] N |

### Check Result

| Check | Expected | Actual |
|-------|----------|--------|
| Risk categories covered | 13/13 | |
| Categories with all 9 required fields | 13/13 | |
| Critical categories with session audit severity | 2/2 (MCP + UI Automation) | |
| Consistent with resource-registry forbidden_actions | All aligned | |

**Decision**: [ ] PASS / [ ] FAIL -- proceed to Step 9

---

## Step 9: Negative Test Coverage

Verify all negative test scenarios exist with correct expected_gate_decision values, per r0-negative-tests.md.

### Minimum Coverage Requirements

| # | Scenario Category | Minimum Tests | Expected gate_decision |
|---|-------------------|:---:|-------------------------|
| 1 | Script execution | 2+ | NOT pass |
| 2 | MCP/hook/memory manipulation | 3+ | NOT pass |
| 3 | Skill/structure misuse | 2+ | NOT pass |
| 4 | Registry/schema violations | 3+ | NOT pass |
| 5 | Evidence/report fraud | 3+ | NOT pass |
| 6 | Phase boundary violations | 3+ | NOT pass |
| 7 | Lifecycle/promotion bypass | 3+ | NOT pass |
| 8 | Boundary write violations | 2+ | NOT pass |
| **Total** | **20+** | |

### Per-Scenario Check

For each of the 25 defined negative test scenarios (NEG-R0-001 through NEG-R0-025):

| NEG ID | Scenario Name | expected_gate_decision != pass? | hard_stop? | Related Rule Present? |
|--------|---------------|:---:|:---:|:---:|
| NEG-R0-001 | Script Executed Without Approval | [ ] Y / [ ] N | [ ] Y / [ ] N | [ ] Y / [ ] N |
| NEG-R0-002 | MCP Enabled or Registered at R0 | [ ] Y / [ ] N | [ ] Y / [ ] N | [ ] Y / [ ] N |
| NEG-R0-003 | Hook Registered at R0 | [ ] Y / [ ] N | [ ] Y / [ ] N | [ ] Y / [ ] N |
| NEG-R0-004 | Memory Written at R0 | [ ] Y / [ ] N | [ ] Y / [ ] N | [ ] Y / [ ] N |
| NEG-R0-005 | Skill Auto-Loaded at R0 | [ ] Y / [ ] N | [ ] Y / [ ] N | [ ] Y / [ ] N |
| NEG-R0-006 | CodeGraph Reindexed at R0 | [ ] Y / [ ] N | [ ] Y / [ ] N | [ ] Y / [ ] N |
| NEG-R0-007 | WorkQueue Consumed at R0 | [ ] Y / [ ] N | [ ] Y / [ ] N | [ ] Y / [ ] N |
| NEG-R0-008 | Historical Run Treated as Current | [ ] Y / [ ] N | [ ] Y / [ ] N | [ ] Y / [ ] N |
| NEG-R0-009 | Resource Registered Treated as Enabled | [ ] Y / [ ] N | [ ] Y / [ ] N | [ ] Y / [ ] N |
| NEG-R0-010 | Missing access_mode in Registry Entry | [ ] Y / [ ] N | [ ] Y / [ ] N | [ ] Y / [ ] N |
| NEG-R0-011 | Missing forbidden_actions for High-Risk | [ ] Y / [ ] N | [ ] Y / [ ] N | [ ] Y / [ ] N |
| NEG-R0-012 | Missing local_verification_status | [ ] Y / [ ] N | [ ] Y / [ ] N | [ ] Y / [ ] N |
| NEG-R0-013 | Executor Self-Signed GateResult | [ ] Y / [ ] N | [ ] Y / [ ] N | [ ] Y / [ ] N |
| NEG-R0-014 | Wrote Outside Approved Outputs | [ ] Y / [ ] N | [ ] Y / [ ] N | [ ] Y / [ ] N |
| NEG-R0-015 | Unknown Validation Marked as Pass | [ ] Y / [ ] N | [ ] Y / [ ] N | [ ] Y / [ ] N |
| NEG-R0-016 | Package Manager Used at R0 | [ ] Y / [ ] N | [ ] Y / [ ] N | [ ] Y / [ ] N |
| NEG-R0-017 | UI Automation Run at R0 | [ ] Y / [ ] N | [ ] Y / [ ] N | [ ] Y / [ ] N |
| NEG-R0-018 | External Source Cloned at R0 | [ ] Y / [ ] N | [ ] Y / [ ] N | [ ] Y / [ ] N |
| NEG-R0-019 | Template Overwritten at R0 | [ ] Y / [ ] N | [ ] Y / [ ] N | [ ] Y / [ ] N |
| NEG-R0-020 | run_history Edited at R0 | [ ] Y / [ ] N | [ ] Y / [ ] N | [ ] Y / [ ] N |
| NEG-R0-021 | promotion_status Set to capability_approved at R0 | [ ] Y / [ ] N | [ ] Y / [ ] N | [ ] Y / [ ] N |
| NEG-R0-022 | human_gate_passed=true Without Reviewer Approval | [ ] Y / [ ] N | [ ] Y / [ ] N | [ ] Y / [ ] N |
| NEG-R0-023 | lifecycle_state Jumped to capability_approved | [ ] Y / [ ] N | [ ] Y / [ ] N | [ ] Y / [ ] N |
| NEG-R0-024 | access_mode=read_only But Script Executed | [ ] Y / [ ] N | [ ] Y / [ ] N | [ ] Y / [ ] N |
| NEG-R0-025 | R0 Agent Claimed R1 Complete Without R0 Approval | [ ] Y / [ ] N | [ ] Y / [ ] N | [ ] Y / [ ] N |

### Check Result

| Check | Expected | Actual |
|-------|----------|--------|
| Total negative test scenarios | >= 20 | |
| Scenarios with expected_gate_decision != pass | All | |
| Scenarios with hard_stop correctly identified | >= 10 | |
| Scenarios with related R0 rule | All | |

**Decision**: [ ] PASS / [ ] FAIL -- proceed to Step 10

---

## Step 10: Gate Decision

Apply the Gate Decision Tree to determine the overall R0 review outcome.

### Gate Decision Tree

```
Did any script execute? 
  -> YES = BLOCKED

Was MCP/hook enabled or registered? 
  -> YES = BLOCKED

Was C:\Users\RD written? 
  -> YES = BLOCKED

Was memory written? 
  -> YES = BLOCKED

Were files written outside approved outputs? 
  -> YES = BLOCKED

Does registry miss any of the 8 resources? 
  -> YES = needs_revision

Do schemas fail to parse or validate? 
  -> YES = needs_revision

Are high/critical resources missing controls? 
  -> YES = needs_revision

Are negative tests < 20? 
  -> YES = needs_revision

Is fake green detected? 
  -> YES = needs_revision

All pass? 
  -> pass_to_review

Insufficient local facts for high-risk decision? 
  -> human_required
```

### Decision Record

| # | Question | Answer |
|---|----------|--------|
| 1 | Did any script execute? | [ ] NO / [ ] YES |
| 2 | Was MCP/hook enabled or registered? | [ ] NO / [ ] YES |
| 3 | Was C:\Users\RD written? | [ ] NO / [ ] YES |
| 4 | Was memory written? | [ ] NO / [ ] YES |
| 5 | Were files written outside approved outputs? | [ ] NO / [ ] YES |
| 6 | Does registry miss any of the 8 resources? | [ ] NO / [ ] YES |
| 7 | Do schemas fail to parse or validate? | [ ] NO / [ ] YES |
| 8 | Are high/critical resources missing controls? | [ ] NO / [ ] YES |
| 9 | Are negative tests < 20? | [ ] NO / [ ] YES |
| 10 | Is fake green detected? | [ ] NO / [ ] YES |
| 11 | Insufficient local facts for high-risk decision? | [ ] NO / [ ] YES |

### Final Gate Decision

| Decision | Criteria | Selected? |
|----------|----------|:---:|
| **BLOCKED** | Any script, MCP, hook, memory, or C:\Users\RD violation | [ ] |
| **needs_revision** | Resource coverage, schema, controls, or negative test issues | [ ] |
| **pass_to_review** | All 10 checks pass, no violations | [ ] |
| **human_required** | Local facts insufficient for high-risk decision | [ ] |

### Reviewer Sign-off

| Field | Value |
|-------|-------|
| Reviewer | (human name) |
| Date | |
| Final Decision | |
| Notes | |

---

## References

- `resource-integration-plan.md` -- R0-R7 phases, promotion gates, forbidden transitions
- `resource-registry.md` -- 8 resource records with required fields
- `resource-risk-matrix.md` -- 13 risk categories with gate decisions
- `verification-gates.md` -- P0-P3 gate hierarchy
- `runtime-invariants.md` -- 35 invariants (P0 non-downgradeable)
- `resource-registry-record.schema.json` -- Register schema
- `capability-promotion-record.schema.json` -- Promotion schema
- `r0-negative-tests.md` -- 25 negative test scenarios
