# R2 test-frame Reviewer Checklist

> Batch R2-C, 2026-05-27
> RD2100 Agent Runtime v2
> Phase: R2 (Evidence Provider Registration)
> Purpose: 10-step structured review process for R2 gate decisions.

---

## R2 Boundary Banner

```
REVIEWER CHECKLIST -- R2 test-frame Evidence Provider Registration
Scope: Verify R2 compliance. Do NOT execute tests. Do NOT run aggregator/attribution/CLI/orchestrator.
All evidence is historical. No GateResult is produced by test tools. Reviewer is the sole gate authority.
```

---

## 10-Step Review Process

---

### Step 1: Changed Files Check

**Objective**: Verify only R2 approved outputs were modified. No D:\test-frame changes.

| Check | Expected | Finding |
|-------|----------|:-------:|
| R2 output files modified only (docs/agent-runtime/r2-*) | YES | |
| D:\test-frame modified | NO | |
| scripts/ modified | NO | |
| agent-workqueue/ modified | NO | |
| rules/ modified | NO | |
| hooks/ modified | NO | |
| .claude/ modified | NO | |
| .codegraph/ modified | NO | |
| README.md or AGENTS.md modified | NO | |
| Untracked files outside approved paths | NONE | |

**Decision Rule**: Any modification to D:\test-frame or forbidden paths = **BLOCKED**. R2 is read-only against test-frame.

---

### Step 2: Execution Audit

**Objective**: Verify zero test execution across the entire forbidden surface.

| Check | Expected | Finding |
|-------|----------|:-------:|
| pytest executed | NO | |
| npm test executed | NO | |
| playwright executed | NO | |
| aggregator (any invocation) | NO | |
| attribution (any invocation) | NO | |
| CLI (any command) | NO | |
| orchestrator (any dispatch) | NO | |
| Any test runner invoked | NO | |
| Any subprocess calling test-frame tools | NO | |

**Decision Rule**: Any YES = **BLOCKED**. R2 execution_policy is `forbidden`.

**Verification Method**: Check session logs, tool call history, file modification timestamps, and git diff for any sign of execution artifacts (e.g., new test-results files, .pytest_cache, node_modules, allure-report directories).

---

### Step 3: Historical Evidence Check

**Objective**: Verify no historical report was treated as current pass.

| Check | Expected | Finding |
|-------|----------|:-------:|
| Historical report treated as current pass | NO | |
| EvidenceIndex entry has status=verified without reviewer action | NO | |
| EvidenceIndex entry has freshness=current | NO | |
| Any claim "test passed today" or equivalent | NO | |
| Any claim of "current" test-frame state beyond directory existence | NO | |
| All evidence references marked historical or stale_or_unknown | YES | |

**Decision Rule**: Any historical evidence treated as current = **needs_revision**. All R2 evidence defaults to `stale_or_unknown`.

**Policy Reference**: `historical-evidence-policy.md` Section 3 (7 prohibited uses), Section 5 (Freshness Classification).

---

### Step 4: Attribution Boundary Check

**Objective**: Verify attribution did NOT produce any GateResult. Verify no auto-pass/fail.

| Check | Expected | Finding |
|-------|----------|:-------:|
| Attribution executed | NO | |
| Attribution imported or called | NO | |
| Attribution output treated as GateResult | NO | |
| Attribution auto-signed pass/fail | NO | |
| GateResult produced by attribution | NO | |
| GateResult evidence_ids reference attribution output without reviewer annotation | NO | |
| Anti-pattern AP-1 through AP-5 detected | NONE | |

**Decision Rule**: Attribution producing GateResult or auto-signing = **needs_revision**. Attribution is forbidden in R2 and can never produce a GateResult.

**Policy Reference**: `test-frame-attribution-alignment.md` Section 1 (Core Principle), Section 4 (5 Anti-Patterns).

---

### Step 5: EvidenceIndex Mapping Check

**Objective**: Verify all evidence references have complete metadata.

| Check | Expected | Finding |
|-------|----------|:-------:|
| Every evidence entry has run_id | YES | |
| Every evidence entry has timestamp (ISO8601) | YES | |
| Every evidence entry has source | YES | |
| Every evidence entry has freshness | YES | |
| Default freshness is stale_or_unknown (not current, not recent) | YES | |
| Default status is collected (not verified) | YES | |
| Verified status only present if reviewer explicitly validated | YES | |
| EvidenceIndex records with status=verified in R2 | NONE | |
| EvidenceIndex records produced from forbidden components | NONE | |

**Decision Rule**: Missing run_id, timestamp, source, or freshness = **needs_revision**. Verified status without reviewer action = **needs_revision**.

**Policy Reference**: `historical-evidence-policy.md` Section 4 (Required Metadata), Section 6 (Historical Evidence in EvidenceIndex).

---

### Step 6: Provider Status Check

**Objective**: Verify test-frame is registered as Evidence Provider Candidate, NOT active provider.

| Check | Expected | Finding |
|-------|----------|:-------:|
| test-frame registered as active provider | NO |
| test-frame registered as Evidence Provider Candidate | YES |
| execution_policy = forbidden | YES |
| current_result_policy = historical_only | YES |
| human_gate_required = true | YES |
| next_phase_blocked = true | YES |
| Provider transition attempted without exit gate satisfaction | NO |

**Decision Rule**: test-frame registered as active provider = **needs_revision**. R2 status is Evidence Provider Candidate only.

**Policy Reference**: `test-frame-evidence-provider.md` Provider Status section, R2 Exit Gate (15 conditions).

---

### Step 7: Forbidden Actions Audit

**Objective**: Verify complete forbidden actions list is clean.

Audit all 23 forbidden actions from `test-frame-evidence-provider.md`:

**15 Primary Forbidden Actions:**

| # | Action | Violated? |
|---|--------|:---------:|
| 1 | Execute pytest / npm test / playwright | |
| 2 | Execute aggregator | |
| 3 | Execute attribution | |
| 4 | Execute CLI commands | |
| 5 | Execute orchestrator | |
| 6 | Modify D:\test-frame | |
| 7 | Write test results | |
| 8 | Write reports | |
| 9 | Install dependencies | |
| 10 | Treat historical report as current pass | |
| 11 | Allow attribution to produce GateResult | |
| 12 | Trigger external services | |
| 13 | Read .env or credentials in test-frame | |
| 14 | Consume test-frame evidence in GateResult without reviewer approval | |
| 15 | Register test-frame as active provider | |

**8 Additional Constraints:**

| # | Action | Violated? |
|---|--------|:---------:|
| 16 | Import or call any aggregator function | |
| 17 | Import or call any attribution function | |
| 18 | Import or call any orchestrator function | |
| 19 | Import or call any CLI function | |
| 20 | Schedule or dispatch any task through orchestrator | |
| 21 | Treat any historical artifact as gate-check pass | |
| 22 | Produce evidence_index records with status=verified | |
| 23 | Produce gate_result records referencing test-frame evidence as current | |

**Decision Rule**: Any violation of the 23 forbidden actions = severity depends on action type. Execution violations (1-5, 12) = **BLOCKED**. Misclassification violations (10, 11, 14, 15, 21-23) = **needs_revision**. File modification violations (6-9) = **BLOCKED**. Import violations (16-20) = **needs_revision**.

Only 4 actions are permitted: read_directory, read_docs, validate_json, git_status.

---

### Step 8: Negative Test Pass

**Objective**: Verify all R2 negative tests exercised, none had expected_gate_decision=pass.

| Check | Expected | Finding |
|-------|----------|:-------:|
| Total negative test scenarios | >= 25 | |
| Scenarios with expected_gate_decision=pass | 0 (NONE) | |
| Hard stop scenarios marked correctly | YES | |
| BLOCKED scenarios map to correct decision tree node | YES | |
| needs_revision scenarios have specific finding documented | YES | |
| All 27 scenario categories covered | YES | |

**Decision Rule**: Any negative test with expected_gate_decision=pass = **needs_revision**. Negative tests MUST expect non-pass outcomes (BLOCKED, needs_revision, or human_required). Fewer than 25 scenarios = **needs_revision**.

---

### Step 9: D:\test-frame Integrity Check

**Objective**: Verify test-frame directory was NOT modified during R2.

| Check | Expected | Finding |
|-------|----------|:-------:|
| New files in D:\test-frame | NONE | |
| Modified files in D:\test-frame | NONE | |
| Deleted files in D:\test-frame | NONE | |
| File timestamps changed during R2 window | NONE | |
| .pytest_cache directory created/modified | NO | |
| node_modules created/modified | NO | |
| __pycache__ directories created/modified | NO | |
| allure-report directories created/modified | NO | |

**Decision Rule**: Any D:\test-frame modification = **BLOCKED**. R2 is read-only against test-frame.

**Verification Method**: Compare git status, file timestamps, and directory listings before/after R2 session. Check git diff D:\test-frame.

---

### Step 10: Gate Decision

**Objective**: Apply the Gate Decision Tree to determine the final outcome.

---

## Gate Decision Tree

```
Q1:  Was any test executed (pytest/npm/playwright)?       YES = BLOCKED    NO = continue
Q2:  Was aggregator/attribution/CLI/orchestrator executed? YES = BLOCKED    NO = continue
Q3:  Was D:\test-frame modified?                           YES = BLOCKED    NO = continue
Q4:  Were dependencies installed (pip/npm)?                YES = BLOCKED    NO = continue
Q5:  Were external services triggered?                     YES = BLOCKED    NO = continue
Q6:  Was historical evidence treated as current pass?      YES = needs_revision  NO = continue
Q7:  Did attribution produce GateResult?                   YES = needs_revision  NO = continue
Q8:  Is EvidenceIndex metadata incomplete?                 YES = needs_revision  NO = continue
Q9:  Is freshness defaulted to stale_or_unknown?           YES = correct (R2)    NO = needs_revision
Q10: Are negative tests < 25?                              YES = needs_revision  NO = continue
Q11: Is test-frame registered as active provider?          YES = needs_revision  NO = continue
Q12: Was any forbidden action (primary 1-15) violated?     YES = blocking (see matrix)  NO = continue
Q13: Was any additional constraint (16-23) violated?       YES = needs_revision  NO = continue
Q14: Insufficient local facts for decision?                YES = human_required  NO = continue
ALL PASS? -> pass_to_review
```

### Gate Outcome Summary

| Outcome | Condition | Next Action |
|---------|-----------|-------------|
| **blocked** | Test execution, D:\test-frame modification, dependency installation, external service trigger, or orchestration occurred | Halt immediately. Investigate scope of violation. Determine if rollback needed. |
| **needs_revision** | Historical evidence misclassified, attribution boundary crossed, incomplete EvidenceIndex metadata, insufficient negative tests, or provider status incorrect | Fix the identified issues. Re-run the checklist. |
| **human_required** | Insufficient local facts to reach conclusion; edge case not covered by decision tree | Escalate to human reviewer with specific questions and evidence gaps documented. |
| **pass_to_review** | All 13 decision nodes pass. No forbidden actions. All evidence properly classified as historical. Negative tests >= 25 with no expected_pass. Attribution boundary clean. | Hand off to human reviewer for final approval. test-frame remains as Evidence Provider Candidate. |

---

## Reviewer Decision Record

| Field | Value |
|-------|-------|
| Reviewer | |
| Date | 2026-05-27 |
| Batch | R2-C |
| Phase | R2 (Evidence Provider Registration) |
| Gate Outcome | |
| Blocked Reason (if applicable) | |
| Revision Items (if applicable) | |
| Human Questions (if applicable) | |
| Signature | |

---

## Verification

- [x] 10-step review process defined
- [x] Gate Decision Tree with 14 decision nodes
- [x] 4 possible outcomes: blocked, needs_revision, human_required, pass_to_review
- [x] 23 forbidden actions enumerated in Step 7 audit matrix
- [x] Each step references the relevant R2 policy document
- [x] Decision tree maps to negative test expected outcomes
- [x] No test-frame execution
- [x] No D:\test-frame modification
- [x] No write to C:\Users\RD
- [x] No commit, push, or destructive git operation

---

## References

- `test-frame-evidence-provider.md` -- R2 evidence provider policy, 23 forbidden actions, 4 allowed actions
- `test-frame-evidence-map.md` -- Component-to-contract mapping, GateResult prohibition for all 9 components
- `test-frame-attribution-alignment.md` -- Attribution boundary, 5 anti-patterns, reviewer as sole GateResult producer
- `historical-evidence-policy.md` -- Freshness classification, required metadata, EvidenceIndex rules
- `r2-test-frame-negative-tests.md` -- Negative test scenarios covering all R2 violation types
