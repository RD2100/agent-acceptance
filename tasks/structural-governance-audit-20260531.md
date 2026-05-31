# Structural Governance Audit — 2026-05-31

> Auditor: Claude Code (structural audit mode)
> Object: RD2100 Agent Runtime v2 (D:\agent-acceptance)
> Baseline commit: f6e29bc (`feat: require independent reviewer node in SADP workflow`)
> Method: Read-only. No code modified. Cross-referenced all schemas, scripts, hooks, CI, rules, docs, and templates.

---

## Step 1: Governance Concept Inventory

| Concept | Files Found | Declared Role | Enforced By | Risk |
|---------|-------------|---------------|-------------|------|
| `@go` | SKILL.md, AGENTS.md, SADP, CLAUDE.md | Explicit formal-workflow trigger. User types `@go` to start SADP | No runtime — dispatches described as `opencode run` but no automation script | MEDIUM: manual-only trigger |
| SADP | sub-agent-dispatch-protocol.md, AGENTS.md, SKILL.md, sadp-audit.ps1, core.md | Full state machine: Gate 0 → TaskSpec → Executor → Tester → Reviewer → Finalizer | sadp-audit.ps1 (partial), pre-commit (partial) | HIGH: key steps unenforced |
| TaskSpec | task-spec.schema.json, SADP §1, integration-contracts.md Contract 1, rules/core.md, sadp-audit.ps1 | Work unit contract with gate_0 and conflict_registry | Schema exists; no runtime validation; sadp-audit only checks file-name match in write_set | HIGH: self-attestation gating |
| ExecutionReport | execution-report.schema.json, SADP §2, docs/EXECUTION_REPORT_TEMPLATE.md, integration-contracts.md Contract 5 | Final structured report → human reviewer | Schema exists; no runtime validation; template diverges from schema | CRITICAL |
| GateResult | gate-result.schema.json, integration-contracts.md Contract 4, authority-matrix.md, verification-gates.md | Single verification gate check; signer_role≠executor | JSON schema `not: {const: "executor"}`; no runtime validator | MEDIUM |
| EvidenceIndex | evidence-index.schema.json, integration-contracts.md Contract 3 | Index of evidence artifacts | Schema exists; freshness field missing from schema (only in docs) | MEDIUM |
| executor/fixer | SADP §0.R.1, SKILL.md, authority-matrix.md | Produces code changes, diff.patch, execution log. Must NOT produce review artifacts | Enforced by ai_guard.py evidence mode (reviewer_forbidden_roles). But evidence mode never called. | CRITICAL |
| reviewer | SADP §0.R.1, SKILL.md, rules/review.md, authority-matrix.md, docs/agent-runtime/reviewer-playbook.md | Independent from executor; produces review.md, review.yaml, P0/P1 findings | ai_guard.py evidence mode validates reviewer_role. But never invoked. | CRITICAL |
| finalizer | SADP §0.R.3, SKILL.md | Runs ai_guard.py evidence, summarizes; must NOT substitute for reviewer | Declared only. No script/hook enforces. | CRITICAL |
| Plan Auditor | SADP §3.3a, audit-record.schema.md, AGENTS.md | Independent compliance check; must not self-audit | Declared. No script/hook enforces independence. Session-ledger/sadp-audit are partial. | HIGH |
| review.md / review.yaml | SKILL.md, SADP §0.R.2, ai_guard.py evidence mode, .ai/policy.yaml | Machine-readable reviewer verdict; required for pass | review.yaml validated by ai_guard.py evidence mode (never called). review.md has no schema. | CRITICAL |
| diff.patch | SKILL.md, SADP §0.R.2, .ai/policy.yaml | Real code delta | Declared in evidence contract. No producer/generator script. | MEDIUM |
| test-output.md | SKILL.md, SADP §0.R.2, .ai/policy.yaml | Command output and exit codes | Declared. No producer script. No verification. | MEDIUM |
| safety-report.json | SKILL.md, SADP §0.R.2, .ai/policy.yaml | Security/path/scope check output | No schema. No producer. No validator. | HIGH |
| chain-evidence.json | SKILL.md, SADP §0.R.2, .ai/policy.yaml | Role/session/model chain | No schema. No producer. No validator. | HIGH |
| final-report.md | SKILL.md, SADP §0.R.2, .ai/policy.yaml | Finalizer deterministic summary | No schema. No producer beyond declaration. | MEDIUM |
| ai_guard | tools/ai_guard.py, .ai/policy.yaml, pre-commit, pre-push, CI, sadp-audit | Unified rule engine for secret/scope/evidence checks | Yes — wired into pre-commit, pre-push, CI. But evidence mode unreachable. | MEDIUM |
| sadp-audit | scripts/sadp-audit.ps1, pre-commit | TaskSpec coverage + secret scan on staged diff | Yes — wired into pre-commit gate. | LOW |
| pre-commit | hooks/pre-commit.governance.ps1, .git/hooks/pre-commit (via core.hooksPath) | Manifest regen → sadp-audit. Blocks commit on failure. | Active via core.hooksPath. Calls sadp-audit. | LOW |
| pre-push | hooks/pre-push.governance.ps1, .github/workflows/ai-guard.yml | ai_guard full + drift + governance. Blocks push on failure. | Active. Mirrors CI. | LOW |
| CI | .github/workflows/ai-guard.yml | ai_guard full + drift + governance on PR/push to main | Active. Does NOT run evidence mode. Does NOT validate schemas. Does NOT check reviewer artifacts. | MEDIUM |
| branch protection | .github/workflows/ai-guard.yml (implicit) | CI must pass for PR merge | Passive — CI gate only. No required-reviewers rule visible in workflow. | LOW |
| accepted | execution-report.schema.json: status enum, SADP §0.R.3 | Final state requiring reviewer_artifacts | Schema enforces via `allOf/if/accepted/then/required: reviewer_artifacts`. No runtime validation. | HIGH |
| reviewed | execution-report.schema.json: status enum | Post-submission, pre-accepted | Separate from `reviewed_inputs` in review.yaml. Ambiguous. | MEDIUM |
| passed | review.yaml verdict enum, GateResult result enum, RunSpec exit_code 0, varios docs | Different meanings across artifacts | GateResult.result has `pass`; review.yaml verdict has `pass`; ExecutionReport status uses `accepted` not `passed` | HIGH |
| blocked | review.yaml verdict, GateResult result, RunSpec status, sadp-audit exit 1, various | Blocked means different things in different contexts | GateResult.result: `blocked`; review.yaml verdict: `blocked`; RunSpec.status: `blocked`; sadp-audit: BLOCKED. Generally consistent. | LOW |
| escalate | review.yaml verdict, GateResult (implicit via escalation rules) | Human intervention required | Consistent in review.yaml and SADP. Not in GateResult schema. | LOW |
| P0/P1 findings | SADP §0.R, SKILL.md, ai_guard.py, .ai/policy.yaml, verification-gates.md, rules/core.md, rules/security.md, rules/review.md | Blocking finding severities | ai_guard.py evidence: unresolved P0/P1 + verdict=pass → BLOCKED. But evidence mode unreachable. rules define P0s but no gate validates them all. | CRITICAL |

---

## Step 2: Declared vs Enforced vs CI vs Recovery vs Skill Workflows

### Declared Workflow (from SADP + SKILL.md + AGENTS.md)

```
human_gate
  → executor/fixer (code changes, diff.patch, execution log)
  → tester (test-output.md)
  → guards (sadp-audit + ai_guard, safety-report.json + chain-evidence.json)
  → reviewer (separate session, review.md + review.yaml)
  → finalizer (ai_guard.py evidence, final-report.md)
  → verdict: pass | blocked | fail | escalate
```

### Enforced Workflow (pre-commit → sadp-audit → ai_guard)

```
git commit
  → pre-commit.governance.ps1
    → Update-GovernanceManifest.ps1 (manifest auto-regen)
    → sadp-audit.ps1
      → TaskSpec coverage check (if 3+ files or governance touched)
      → Secret pattern scan on staged diff
      → ai_guard.py staged (deny_paths + secret patterns)
      → .env.example template warning
```

### CI Workflow (.github/workflows/ai-guard.yml)

```
PR / push to main
  → ai_guard.py full (deny_paths + scopes + secret scan on git diff vs origin/main)
  → Test-GovernanceDrift.ps1 (rule IDs, phase boundaries, manifest coverage, capability counts)
  → Test-Governance.ps1 -Mode blocking (protected paths, key scan, batch references)
```

### Pre-Push Workflow (hooks/pre-push.governance.ps1)

```
git push
  → ai_guard.py full
  → Test-GovernanceDrift.ps1
  → Test-Governance.ps1 -Mode blocking
```
(Identical to CI, which is good.)

### Skill Workflow (@go / SKILL.md)

```
User says @go
  → Gate 0: check AGENTS.md, rules, mode, allow_write
  → Executor/fixer: opencode run; collect diff.patch
  → Tester: run commands; write test-output.md
  → Guards: sadp-audit.ps1 + ai_guard.py task; write safety-report.json
  → Reviewer: separate session; write review.md + review.yaml
  → Finalizer: ai_guard.py evidence <run-evidence-dir>
  → Verdict: passed only if guard + reviewer + evidence all pass
```
**Status**: Entirely declarative. Zero automation scripts implement this flow. `opencode run` commands are in the SKILL.md as examples but no orchestrator script exists.

### Recovery Workflow (RECOVERY_PIPELINE_RUNBOOK.md)

```
OS/system kill
  → sync_goal_runs() (ai-workflow-hub)
  → goal review-recovered --dry-run
  → goal review-recovered --apply (requires explicit ACK)
```
**Status**: References dev-frame/ai-workflow-hub; not tested in agent-acceptance context. `diff.patch`, `trace.json`, `state.json` paths mirror evidence contract loosely but differently.

### Workflow Differences

| Difference | Source A | Source B | Severity | Recommendation |
|------------|----------|----------|----------|----------------|
| human_gate step declared but unimplemented | SADP §0.R state machine, SKILL.md | No script/hook/CI implements human_gate entry point | P0 | Either implement human gate or remove from declared flow |
| reviewer evidence production declared but unreachable | SADP §0.R.2, SKILL.md | ai_guard.py `evidence` mode exists but zero callers | P0 | Wire evidence check into pre-commit or add CI job |
| finalizer step declared but unreachable | SADP §0.R.3, SKILL.md | No script/hook/CI runs `ai_guard.py evidence <dir>` | P0 | Same fix as above |
| diff.patch/test-output/safety-report/chain-evidence required | .ai/policy.yaml required_evidence_files | No producer scripts exist; no run directories contain them | P0 | Create producer scripts or declare these as aspirational |
| CI runs ai_guard.py full but full mode doesn't check evidence | .github/workflows/ai-guard.yml | ai_guard.py evidence mode (separate, never called) | P0 | CI should run evidence mode for runs/ directories |
| sadp-audit calls ai_guard.py staged but SKILL says it should write safety-report.json | sadp-audit.ps1 line 258 | SKILL.md evidence table | P1 | sadp-audit output could be captured as safety-report.json |
| Recovery runbook references dev-frame paths not agent-acceptance paths | RECOVERY_PIPELINE_RUNBOOK.md | SADP evidence contract paths | P2 | Align or note as external system |
| @go skill describes full orchestration but no orchestrator script | SKILL.md "Automated Dispatch" section | No .ps1/.py orchestrator exists | P1 | Accept as human-driven manual workflow or build orchestrator |
| Cumulated trigger window in SADP §0.0a is advisory-only | SADP §0.0a | sadp-audit.ps1 checks 3+ files threshold (actual enforcement) | P1 | Mismatch: SADP says advisory, sadp-audit enforces |

---

## Step 3: Role Boundary Consistency

### Analysis

Sources checked:
- SADP §0.R.1 Role Boundaries table
- SKILL.md evidence contract
- authority-matrix.md
- gate-result.schema.json (signer_role constraint)
- execution-report.schema.json (reviewer_artifacts.reviewer_role constraint)
- ai_guard.py (reviewer_forbidden_roles check)
- .ai/policy.yaml (reviewer_forbidden_roles: [executor, fixer, coder])

| Role | Allowed Outputs | Forbidden Outputs | Conflicting Sources | Verdict |
|------|-----------------|-------------------|---------------------|---------|
| executor/fixer | code changes, execution log, diff.patch | review.md, review.yaml, final pass verdict | SADP+R: consistent. But `fixer` not in GateResult signer_role constraint (only "executor" forbidden). ai_guard checks "fixer" too. | MINOR GAP: GateResult schema allows "fixer" signer |
| reviewer | review.md, review.yaml, P0/P1 findings | implementation changes | SADP+R: consistent. But no automation prevents reviewer from editing code (only documented). | DOC_ONLY: no code enforcement |
| finalizer | final-report.md, deterministic artifact summary | reviewer judgment, code-quality approval | SADP+R: consistent. No automation gating. | DOC_ONLY: no enforcement script |
| tester | test-output.md, command exit-code evidence | code-quality approval | SADP+R: consistent. `tester` role not referenced in any schema/enum. Only in docs. | DOC_ONLY: not modeled in schemas |
| Plan Auditor | audit record, compliance findings, decision (pass/block/escalate) | must not self-audit; must not re-judge implementation quality | SADP §3.3a vs authority-matrix.md: authority-matrix doesn't list "Plan Auditor" as a separate role. SADP says Plan Auditor ≠ Plan Agent. | AMBIGUOUS: Plan Auditor role boundary not in authority-matrix |
| human reviewer | final override, P0/P1 sign-off | N/A (highest authority) | SADP §0, authority-matrix.md: `1. Human reviewer (overrides all)`. SKILL.md doesn't mention human reviewer. AGENTS.md mentions "Human Reviewer (oversight tier)". | MINOR GAP: human reviewer absent from SKILL.md |
| AI reviewer vs human reviewer | AI: review.md + review.yaml; Human: override | AI must not be executor; Human must not be bypassed | SADP mentions both. review.yaml has reviewer_id but no `is_human` field. ai_guard.py evidence doesn't distinguish. | P1: no way to tell if reviewer_id is human or AI |

### Specific conflicts found:

1. **GateResult schema forbids `executor` but not `fixer`** (gate-result.schema.json:44): `"not": { "const": "executor" }`. But ai_guard.py and .ai/policy.yaml also forbid `fixer` and `coder`. The JSON schema is looser than the Python validator.

2. **Plan Auditor =/= reviewer**: SADP §3.3a Plan Auditor checks compliance (TaskSpec existence, gate_0 validity, file coverage). SKILL.md "reviewer" checks code quality (reads diff, runs tests, finds issues). These are different roles but AGENTS.md groups both under "review." The authority-matrix.md does not list Plan Auditor as a separate producer.

3. **fixer role undefined in schemas**: SADP §0.R.1 treats executor/fixer as one role. But .ai/policy.yaml lists "fixer" separately in reviewer_forbidden_roles. The schemas (execution-report, gate-result) don't mention "fixer" at all. Is fixer a distinct role or a synonym?

---

## Step 4: Declared vs Enforced Gap Analysis

| Rule | Declared In | Enforced By | Test Exists | Gap |
|------|-------------|-------------|-------------|-----|
| No secrets | core-002, sec-001, sec-005, AGENTS.md P0#2 | ai_guard.py (secret scan), sadp-audit (R5), pre-commit, CI, pre-push | Canary 3 (secret injection) | COVERED |
| No fake green | core-004, review-001, AGENTS.md P0#4 | None automated. Exit code contract in RunSpec schema, but no runtime check verifies exit_code matches reported status | None | DOC_ONLY |
| No destructive git | core-001, git-001, git-002, AGENTS.md P0#1 | .ai/policy.yaml dangerous_commands list (declared, not validated). ai_guard.py does not check git commands. | None | DOC_ONLY |
| No write outside TaskSpec | core-005, SADP §0.2, AGENTS.md P0#5 | ai_guard.py task mode checks allow_write vs git diff. But task mode never invoked in hooks/CI. Only `staged` (allow_write=["**"]) and `full` (allow_write=["**"]) used in practice. | None | IMPLICIT_ENFORCEMENT (code exists, never called correctly) |
| No pass without independent reviewer | SADP §0.R, SKILL.md P0#6, AGENTS.md P0#7 | ai_guard.py evidence mode validates reviewer_role not in forbidden roles. But evidence mode NEVER called. pre-commit/CI/pre-push don't check. | None | CODE_EXISTS_UNREACHABLE |
| No pass with unresolved P0/P1 | SADP §0.R.3, SKILL.md P0#7, ai_guard.py | ai_guard.py evidence mode checks. Never called. | None | CODE_EXISTS_UNREACHABLE |
| P0/P1 finding unresolved must block | SADP §0.R.3, SKILL.md P0#7 | ai_guard.py evidence mode: unresolved blocking severities + pass verdict → BLOCKED. Never called. | None | CODE_EXISTS_UNREACHABLE |
| Reviewer must read diff/test/safety/chain | SADP §0.R.2 reviewed_inputs, SKILL.md Reviewer Rules | ai_guard.py evidence mode checks reviewed_inputs completeness. Never called. | None | CODE_EXISTS_UNREACHABLE |
| Finalizer cannot override reviewer | SADP §0.R.3, SKILL.md Finalizer Rule | Declarative only. No machine check. | None | DOC_ONLY |
| No capability without inventory | core-007 | Test-GovernanceDrift checks capability count. Not per-capability verification. | None | PARTIAL (count check only) |
| Gate 0 required for construction tasks | core-008, SADP §0.1 | task-spec.schema.json requires gate_0 for construction tasks. But no runtime validation. sadp-audit only checks TaskSpec existence, not content. | None | SCHEMA_ONLY |
| ExecutionReport must cover all changed files | sadp-audit V2, SADP §3.3a | sadp-audit V2 checks file coverage in TaskSpec write_set. | Canary (protected path modification blocked by Test-Governance) | PARTIAL (sadp-audit checks write_set; Test-Governance checks protected paths) |
| No skip hooks | git-003 | Declared. Hook bypass is possible via `--no-verify`. pre-commit.governance.ps1 references core-001 for override authority. | None | LOCAL_ONLY (git --no-verify bypasses) |
| Phase 0-5 commit freeze | git-006 | pre-edit.governance.ps1 exits 0 (advisory). Test-Governance doesn't specifically check for new commits. | None | DOC_ONLY (exited advisory mode) |
| Memory writes blocked | AGENTS.md Phase 0-5 constraints | pre-edit.governance.ps1 exits 0 (was exit 1, downgraded to advisory). | None | DOC_ONLY (exited advisory mode) |
| Protected files require exclusive lock | SADP §0.2 | Declared only. No runtime lock mechanism exists. | None | DOC_ONLY |
| Plan Agent cannot self-audit | SADP §3.3a | session-ledger.schema.md anti-bypass rule #2: Plan Agent cannot set audit_status to passed. But no automation checks who set the status. | None | DOC_ONLY |

**Summary**: Of 17 strong rules checked:
- 1 fully covered (secrets)
- 1 partially covered (3+ files threshold)
- 4 have code that exists but is never invoked (CODE_EXISTS_UNREACHABLE)
- 2 are SCHEMA_ONLY (schema constraint, no runtime validator)
- 1 is IMPLICIT_ENFORCEMENT (task mode exists, never used correctly)
- 1 is LOCAL_ONLY (hook bypass possible with --no-verify)
- 8 are DOC_ONLY (declared, zero enforcement)

---

## Step 5: Schema and Report Template Consistency

| Schema | Contract | Runtime Producer | Runtime Validator | Gap |
|--------|----------|------------------|-------------------|-----|
| task-spec.schema.json | SADP §1, integration-contracts.md §1 | Manual authoring (human/agent writes Markdown with YAML blocks) | None | Schema defines JSON structure but TaskSpecs are written as Markdown. No conversion/validation pipeline exists. security_report section in schema is not referenced in SADP TaskSpec template. |
| execution-report.schema.json | SADP §2, integration-contracts.md §5, EXECUTION_REPORT_TEMPLATE.md | Manual (human/agent writes Markdown) | None | MAJOR: Schema status enum is `draft|submitted|reviewed|accepted|rejected`. SADP Markdown template uses `PASS|FAIL|BLOCKED`. EXECUTION_REPORT_TEMPLATE.md uses `pass|blocked|needs review`. Three incompatible status systems. |
| gate-result.schema.json | integration-contracts.md §4, verification-gates.md | Manual (agent writes during gate check) | None | signer_role forbids `executor` only. ai_guard evidence forbids `executor|fixer|coder`. Schema is looser than runtime check. |
| evidence-index.schema.json | integration-contracts.md §3 | Manual | None | Contract 3 defines `freshness`, `currency_basis`, `approved_run_id` fields. These are NOT in the JSON schema. Schema only has `collected|verified|disputed` status. Docs say `status=verified` requires `freshness=current` but schema has no freshness field. |
| run-spec.schema.json | integration-contracts.md §2 | Manual (Script runner produces JSON) | None | Exit code enum is 0,1,2; matches declared contract. status enum `pending|running|completed|blocked|failed`. Run-Batch.ps1 may produce this; unclear if format matches. |
| review.yaml (no schema) | SADP §0.R.2, SKILL.md, ai_guard.py evidence, .ai/policy.yaml | Manual (reviewer session) | ai_guard.py evidence mode (never called) | CRITICAL: review.yaml is the most critical machine-readable artifact (determines pass/block). It has NO JSON schema. The structure is defined in 3 places (SKILL.md, SADP, ai_guard.py) but inconsistently: SKILL.md uses `reviewer_role`/`reviewer_id` top-level; ai_guard.py checks both `reviewer_role` top-level AND `reviewer.role` nested. |
| review.md (no schema) | SADP §0.R.2, SKILL.md, .ai/policy.yaml | Manual (reviewer session) | None | Free-form Markdown. Low risk but desirable to have a checklist schema. |
| safety-report.json (no schema) | SKILL.md, .ai/policy.yaml | Declared but no producer | None | HIGH: Required in evidence contract but no schema defines its structure. ai_guard.py could produce it but doesn't. |
| chain-evidence.json (no schema) | SKILL.md, .ai/policy.yaml | Declared but no producer | None | HIGH: Required in evidence contract but no schema. No producer. |
| final-report.md (no schema) | SKILL.md, .ai/policy.yaml | Declared but no producer | None | MEDIUM: Free-form summary. Low structural risk. |

### Specific execution-report status inconsistency:

| Source | Status Values | Context |
|--------|--------------|---------|
| execution-report.schema.json | draft, submitted, reviewed, accepted, rejected | JSON schema enum |
| SADP §2 template | PASS, FAIL, BLOCKED | Markdown template example |
| EXECUTION_REPORT_TEMPLATE.md | pass, blocked, needs review | "Executive Decision" field |
| integration-contracts.md §5 | draft, submitted, reviewed, accepted, rejected | Matches schema |
| AGENTS.md SADP flow | Pass/Block/Escalate | Flow description |
| SKILL.md | pass | blocked | fail | escalate | Reviewer verdict, not report status |

The schema's `draft|submitted|reviewed|accepted|rejected` describes a **document lifecycle** (writing → submitted for review → reviewed → accepted/rejected). The templates use `PASS|FAIL|BLOCKED` which describes a **task outcome**. These are incompatible semantic models. An ExecutionReport can be "accepted" (document lifecycle) while the task result is "BLOCKED" (task outcome), or vice versa.

---

## Step 6: CI / Hook / Guard Coverage Matrix

| Gate | Trigger | Checks | Missing Checks | Severity |
|------|---------|--------|----------------|----------|
| pre-edit governance hook | Every Write/Edit tool call | Memory dirs, governance files, sealed files, secret patterns, dirty baseline, scope | Exits 0 even on BLOCKED (advisory mode). No actual blocking. | P2 (intentionally advisory per comments) |
| pre-commit governance | git commit | Manifest auto-regen → sadp-audit (TaskSpec coverage, secret scan, ai_guard staged) | Does NOT: check for reviewer artifacts, validate ExecutionReport status, check task mode scope, run evidence validation, check P0/P1 resolution | P0 |
| pre-push governance | git push | ai_guard full, Test-GovernanceDrift, Test-Governance blocking | Same gaps as pre-commit. Does NOT run evidence mode. Does NOT validate reviewer independence. | P0 |
| CI ai-guard | PR/push to main | ai_guard full, Test-GovernanceDrift, Test-Governance blocking | Same gaps. Does NOT run evidence mode. Does NOT check reviewer artifacts for merged PRs. | P0 |
| ai_guard.py evidence mode | NEVER TRIGGERED | reviewer_role validation, reviewer_id ≠ executor_id check, reviewed_inputs completeness, verdict validation, unresolved P0/P1 check | This is the most critical missing enforcement. All reviewer-independence rules live here and none are called. | P0 |
| ai_guard.py task mode | NEVER TRIGGERED (called as `staged` which uses allow_write=["**"]) | TaskSpec scope enforcement (allow_write vs changed files) | Scope enforcement code exists but is never used with actual TaskSpec allow_write. | P1 |
| sadp-audit V2 coverage check | pre-commit (when TaskSpecs exist) | Cross-references changed files against TaskSpec write_set | Only checks file name mention, not structured write_set field. Loose regex match. | P2 |
| Canary suite | Manual (scripts/tests/Invoke-GovernanceCanarySuite.ps1) | Smoke batch, protected path violation, secret injection | Does NOT test: reviewer independence, P0/P1 unresolved pass, evidence package completeness, task mode scope, self-review, missing review.yaml | P1 |

---

## Step 7: Negative Test Matrix

Tests were performed by reading source code and logic-tracing; no destructive actions were executed against the real repo.

| # | Case | Command (hypothetical) | Expected Result | Actual (by code analysis) | Verdict |
|---|------|------------------------|-----------------|---------------------------|---------|
| 1 | Missing review.yaml | `python tools/ai_guard.py evidence runs/test-run/` | BLOCKED (EVIDENCE: missing required file: review.yaml) | ai_guard evidence mode checks existence → would block. But evidence mode is never called. | GAP: guard exists, unreachable |
| 2 | review.yaml reviewer_role=executor | `python tools/ai_guard.py evidence runs/test-run/` | BLOCKED (REVIEW: reviewer_role must not be executor) | ai_guard checks reviewer_forbidden_roles → would block. Unreachable. | GAP: guard exists, unreachable |
| 3 | reviewer_id == executor_id | `python tools/ai_guard.py evidence runs/test-run/` | BLOCKED (REVIEW: reviewer_id must differ) | ai_guard line 137-138 checks this → would block. Unreachable. | GAP: guard exists, unreachable |
| 4 | verdict=pass + unresolved P0 finding | `python tools/ai_guard.py evidence runs/test-run/` | BLOCKED (pass verdict invalid with unresolved P0/P1) | ai_guard lines 158-162 check this → would block. Unreachable. | GAP: guard exists, unreachable |
| 5 | reviewed_inputs missing diff.patch | `python tools/ai_guard.py evidence runs/test-run/` | BLOCKED (must list reviewed_inputs: diff.patch) | ai_guard lines 164-180 check completeness → would block. Unreachable. | GAP: guard exists, unreachable |
| 6 | accepted ExecutionReport missing reviewer_artifacts | Schema validation | INVALID (allOf/if/accepted/then/required: reviewer_artifacts) | Schema has the constraint. No runtime validator executes it. | SCHEMA_ONLY |
| 7 | Changed file outside TaskSpec allow_write | `python tools/ai_guard.py task .ai/tasks/task-xxx.yaml` | BLOCKED (SCOPE: path outside allow_write) | ai_guard task mode lines 218-233. But task mode is never called with the actual task file. | CODE_EXISTS_UNUSED |
| 8 | Staged diff contains secret-like string | `python tools/ai_guard.py staged` | BLOCKED (SECRET: file:line: pattern match) | Wired into sadp-audit → pre-commit. ACTIVE. | PASS |
| 9 | Restricted path changed without human confirmation | `python tools/ai_guard.py full` | WARNING (RESTRICTED: requires human review) | ai_guard full mode logs warning but exits 0 if only restricted (no secrets/deny). CI runs full mode. | WEAK: warning doesn't block |
| 10 | final-report.md exists but review.md missing | `python tools/ai_guard.py evidence runs/test-run/` | BLOCKED (EVIDENCE: missing required file: review.md) | ai_guard checks all required_evidence_files → would block. Unreachable. | GAP: guard exists, unreachable |

---

## Step 8: Structural Deficiency Findings

# Structural Governance Audit

## Verdict
**BLOCK** — Multiple P0 gaps. The reviewer independence chain has code (ai_guard.py evidence mode) but zero callers. `accepted` ExecutionReport status carries schema constraint for reviewer_artifacts but no runtime validator. Diff/test/safety/chain evidence files are required by policy but never produced. The governance pyramid is inverted: documentation dominates, enforcement is sparse.

## Executive Summary
The project has a sophisticated, well-documented governance framework. Schemas, rules, hooks, CI, and policy all exist and are internally consistent within their domains. However, **the critical enforcement path — independent reviewer evidence validation — is entirely unreachable**. `ai_guard.py evidence` mode implements all the hard gates (reviewer≠executor, P0/P1 must be resolved, reviewed_inputs completeness), but it is called by nothing. The pre-commit/pre-push/CI pipeline checks secrets, structured drift, and TaskSpec existence, but never validates that an independent reviewer has approved the work. An executor could produce a `pass` verdict today with zero reviewer evidence and no automation would block it.

## P0 Findings

### P0-1: Evidence mode unreachable — all reviewer independence gates are dead code
- **Evidence**: `ai_guard.py:184-200` (`run_evidence_mode`) validates reviewer_role, reviewer_id≠executor_id, verdict consistency, P0/P1 resolution, and reviewed_inputs completeness. Yet grep for `ai_guard.py evidence` across all hooks, CI workflows, and scripts returns zero callers. pre-commit calls `ai_guard.py staged`. CI/pre-push call `ai_guard.py full`. sadp-audit calls `ai_guard.py staged`. No path reaches evidence mode.
- **Impact**: An executor can self-review, mark pass with unresolved P0 findings, skip required evidence, and no automation blocks.
- **Fix**: Wire `ai_guard.py evidence <run-dir>` into pre-commit (as a final check after sadp-audit), into CI (as a PR check for any runs/ directory), or both.

### P0-2: No producer for required evidence files
- **Evidence**: `.ai/policy.yaml:36-42` requires `diff.patch, test-output.md, safety-report.json, chain-evidence.json, review.md, review.yaml, final-report.md`. Zero scripts produce these files. No run directory in `runs/` contains them. The evidence contract is declared but not operational.
- **Impact**: Evidence cannot be produced, so evidence validation is moot even if wired.
- **Fix**: At minimum, produce `diff.patch` via `git diff` in sadp-audit and capture ai_guard output as `safety-report.json`. Wire evidence production into the @go flow or the pre-commit hook.

### P0-3: review.yaml has no JSON schema
- **Evidence**: `review.yaml` is the most critical machine-readable gateway (determines pass/block). Its structure is defined in SKILL.md, SADP §0.R.2, and implicitly in `ai_guard.py:115-179`. But `schemas/agent-runtime/` contains no `review.schema.json`. `execution-report.schema.json:107-131` models `reviewer_artifacts` as an object within the report, but this is the *container*, not the *artifact schema*.
- **Impact**: review.yaml cannot be structurally validated. Inconsistencies between the different structural definitions (top-level fields vs nested `reviewer.*` object in ai_guard) will cause silent validation failures.
- **Fix**: Create `schemas/agent-runtime/review.schema.json` defining the canonical review.yaml structure. Align ai_guard.py to validate against it.

### P0-4: ExecutionReport status enum incompatible with all templates
- **Evidence**: Schema has `draft|submitted|reviewed|accepted|rejected`. SADP §2 template uses `PASS|FAIL|BLOCKED`. EXECUTION_REPORT_TEMPLATE.md uses `pass|blocked|needs review`. Three different status systems for the same artifact.
- **Impact**: Any agent following the SADP template produces reports that fail schema validation. Any system consuming reports can't reliably determine task outcome vs document lifecycle state.
- **Fix**: Align schema and templates. Recommended: schema uses `pass|fail|blocked|escalate` for task outcome, separate `review_status: draft|submitted|reviewed|accepted|rejected` for document lifecycle.

### P0-5: gate_0 inventory_evidence required by schema but never runtime-validated
- **Evidence**: `task-spec.schema.json:72-158` requires `gate_0.inventory_evidence` with `queried_sources` (minItems:1) and `matched_capabilities`. `sadp-audit.ps1` checks TaskSpec existence and V2 checks write_set coverage, but never parses gate_0 content. The schema constraint exists but no runtime validates it.
- **Impact**: A TaskSpec with `gate_0: { triggered: true }` without inventory_evidence passes audit. The core-008 Reuse-before-Build rule is unenforceable.
- **Fix**: sadp-audit should parse TaskSpec gate_0 and reject missing inventory_evidence.

### P0-6: ai_guard.py task mode (write-scope enforcement) never called with actual TaskSpec
- **Evidence**: `ai_guard.py:208-218` task mode reads TaskSpec `allow_write` and checks git diff against it. But pre-commit calls `staged` (allow_write=["**"]), and CI calls `full` (allow_write=["**"]). Neither passes a TaskSpec file. sadp-audit does its own V2 coverage check but doesn't invoke `ai_guard.py task`.
- **Impact**: The "no write outside TaskSpec scope" rule (core-005, SADP §0.2) is unenforced.
- **Fix**: sadp-audit should call `ai_guard.py task <task-file>` when a TaskSpec exists.

## P1 Findings

### P1-1: EvidenceIndex schema missing freshness fields
- **Evidence**: `integration-contracts.md` Contract 3 defines `freshness`, `currency_basis`, `approved_run_id`. The JSON schema `evidence-index.schema.json` has none of these. The docs say `status=verified` requires `freshness=current`, but the schema can't enforce this.
- **Fix**: Add freshness fields to evidence-index.schema.json.

### P1-2: GateResult schema allows "fixer" as signer but policy forbids it
- **Evidence**: `gate-result.schema.json:44` forbids only `executor`. `.ai/policy.yaml:44-47` and `ai_guard.py:125-128` also forbid `fixer` and `coder`. Schema is looser than policy.
- **Fix**: Update gate-result.schema.json signer_role to forbid executor|fixer|coder.

### P1-3: Pre-commit does not run Test-Governance.ps1
- **Evidence**: `pre-commit.governance.ps1` runs manifest regen → sadp-audit → exit. `Test-Governance.ps1` (proxy for Test-ProtectedPaths, Test-KeyScan, Test-BatchReferences) is NOT called by the pre-commit hook. pre-push and CI run it, but pre-commit doesn't.
- **Impact**: Protected path modifications, key leaks in non-secret patterns, and batch reference drift pass through pre-commit. They're caught at push/CI but not at commit time.
- **Fix**: Add Test-Governance (advisory mode) to pre-commit. Keep blocking mode for pre-push/CI.

### P1-4: "human_gate" entry point in state machine has no implementation
- **Evidence**: SADP §0.R and SKILL.md both show `human_gate → executor/fixer → tester → reviewer → finalizer`. But `human_gate` is never defined, scripted, or triggered. It's a diagram node with no backing.
- **Fix**: Either define human_gate as manual confirmation step with instructions, or remove it from the state machine.

### P1-5: Plan Auditor role boundary ambiguous
- **Evidence**: `authority-matrix.md` lists agent-acceptance as producer of all contracts but doesn't separate "Plan Auditor" as a distinct role. SADP §3.3a says Plan Auditor must be independent of Plan Agent. But who is Plan Auditor in practice? The matrix doesn't say. The `audit-record.schema.md` describes an output schema but no producer role.
- **Fix**: Add Plan Auditor to authority-matrix.md as a distinct row. Clarify: is it a human, a separate AI session, or a script?

### P1-6: Cumulated trigger window says advisory but sadp-audit enforces
- **Evidence**: SADP §0.0a says cumulative trigger is "advisory" in @go-only mode. But sadp-audit.ps1 blocks when 3+ files changed and no TaskSpec exists (RULE 1, line 144). This is contradictory: either SADP should update to say 3+ files always triggers, or sadp-audit should not block on file count.
- **Fix**: Align SADP §0.0a with sadp-audit enforcement. Remove "advisory" qualifier or remove the 3+ trigger from sadp-audit.

### P1-7: No distinction between AI reviewer and human reviewer in review.yaml
- **Evidence**: `review.yaml` has `reviewer_id` but no field indicating whether the reviewer is human or AI. SADP mentions both. `ai_guard.py` doesn't distinguish. A self-review by the same AI model with a different session_id would pass the reviewer_id ≠ executor_id check.
- **Fix**: Add `reviewer_type: human | ai` to review.yaml. ai_guard evidence mode should check it.

## P2/P3 Findings

### P2-1: fixer role undefined in schemas
- `fixer` appears in SADP §0.R.1 (as executor/fixer), `.ai/policy.yaml` (forbidden reviewer role), and SKILL.md. But no schema enum includes it. The authority matrix doesn't mention it. Is fixer a distinct role? If not, remove the distinction. If yes, define it.

### P2-2: governance-manifest.md marked as LEGACY but still referenced
- `docs/agent-runtime/governance-manifest.md` says "LEGACY DOCUMENT... Do not rely on hashes here." But `sealed-files-manifest.json` includes it (SHA: 75E7B816...). AGENTS.md references it in the document map. Either delete or update.

### P2-3: sadp-audit V2 write_set check uses regex not YAML parsing
- `sadp-audit.ps1:97-99` checks if file name appears anywhere in TaskSpec content via regex. This is fragile (false positives on mentions, false negatives on structured write_set lists). Should parse YAML properly.

### P2-4: Canary suite tests only 3 scenarios
- `Invoke-GovernanceCanarySuite.ps1` tests smoke batch, protected path, and secret injection. Missing: reviewer independence, evidence completeness, self-review, task scope, P0/P1 resolution. Needs expansion.

### P2-5: pre-edit.governance.ps1 exits 0 on all violations
- All BLOCKED conditions (memory write, governance file, sealed file, secret pattern) exit 0 with advisory message. The comment says "blocking delegated to Test-Governance.ps1" but Test-Governance is not called by pre-edit. The hook fires but never blocks.

### P3-1: AGENTS.md hard stops count mismatch
- AGENTS.md lists 7 hard stops (#1-#7). core.md Knowledge Metabolism Rule says "P0 rules are capped at 7" and counts 6 internal P0s. The AGENTS.md list and core.md count are off by one.

### P3-2: Duplicate evidence file lists
- Evidence package is listed in SKILL.md §Evidence Contract, SADP §0.R.2, `.ai/policy.yaml:36-42`, and `ai_guard.py:164-169`. Four copies of the same list with minor variations.

---

## Drift Map

### Doc Says But No Execution
| Doc Claim | Source | Execution Gap |
|-----------|--------|---------------|
| "finalizer runs `python tools/ai_guard.py evidence <run-evidence-dir>`" | SADP §0.R.3, SKILL.md §Finalizer Rule | No caller exists |
| "reviewer must run in separate session" | SADP §0.R.1 | No enforcement; same model with different session_id passes |
| "Gate 0: Resource Sufficiency Check" | SADP §0 | sadp-audit checks TaskSpec existence, not gate_0 content |
| "No capability without inventory registration" | core-007 | Test-GovernanceDrift checks capability count, not per-capability registration status |
| "Plan Agent cannot audit its own compliance" | SADP §3.3a | No mechanism verifies auditor ≠ plan agent |
| "Memory writes blocked in Phase 0-5" | AGENTS.md | pre-edit exits 0 on memory path violations |

### Execution Says But No Doc
| Execution Reality | Source | Doc Gap |
|-------------------|--------|---------|
| sadp-audit RULE 1: 3+ files → block | sadp-audit.ps1:144-150 | SADP §0.0a says cumulative trigger is "advisory" in @go-only mode |
| pre-edit.governance exits 0 on all blocks | pre-edit.governance.ps1 | AGENTS.md Phase 0-5 says memory writes blocked — the hook says advisory |
| CI runs Test-GovernanceDrift which checks rule ID bidirectional consistency | Test-GovernanceDrift.ps1:25-53 | No doc describes this check in the governance flow |
| Manifest auto-regen before sadp-audit in pre-commit | pre-commit.governance.ps1:12-40 | Not documented in SADP or SKILL.md workflow |

### Schema Has But Not Validated
| Schema Constraint | Schema File | Runtime Validator Gap |
|-------------------|-------------|----------------------|
| ExecutionReport status enum: draft\|submitted\|reviewed\|accepted\|rejected | execution-report.schema.json:30 | No validator; templates use different values |
| ExecutionReport accepted → requires reviewer_artifacts | execution-report.schema.json:133-143 | No validator |
| reviewer_artifacts.reviewer_role not in [executor, fixer, coder] | execution-report.schema.json:121 | No validator |
| TaskSpec gate_0.inventory_evidence.queried_sources minItems:1 | task-spec.schema.json:97-103 | No validator |
| GateResult signer_role not: "executor" | gate-result.schema.json:43-44 | No validator |
| EvidenceIndex status enum (collected\|verified\|disputed) | evidence-index.schema.json:39 | No validator |
| TaskSpec security_report required fields | task-spec.schema.json:197-241 | No validator; not in SADP template |

---

## Recommended Fix Plan

Priority order. Each step includes specific files, tests, and verification.

### Fix 1: Wire evidence mode into CI (addresses P0-1, P0-2 partial)
- **Files to modify**: `.github/workflows/ai-guard.yml` — add a step:
  ```yaml
  - name: Reviewer Evidence Validation
    run: |
      for d in runs/*/; do
        python tools/ai_guard.py evidence "$d" || exit 1
      done
    continue-on-error: false
  ```
- **Test**: Create a fixture run directory with valid evidence, invalid evidence (missing review.yaml, self-review), and verify CI blocks on invalid, passes on valid.
- **Verification**: Push a test PR with a run dir containing a review.yaml where reviewer_role=executor. CI must fail.
- **Risk**: Low. evidence mode reads only, no writes. If runs/ has no evidence dirs, loop is empty (no-op).

### Fix 2: Create review.yaml JSON schema (addresses P0-3)
- **Files to create**: `schemas/agent-runtime/review.schema.json`
- **Schema structure**: Based on SADP §0.R.2, align with ai_guard.py expectations. Required: reviewer_role, reviewer_id, executor_id, verdict, reviewed_inputs. verdict enum: pass|blocked|fail|escalate. reviewer_role not in [executor, fixer, coder].
- **Test**: Validate a sample review.yaml against the schema with a JSON schema validator.
- **Verification**: ai_guard.py evidence mode should load and validate review.yaml against the schema.
- **Risk**: Low. additive.

### Fix 3: Align ExecutionReport status values (addresses P0-4)
- **Files to modify**: 
  - `schemas/agent-runtime/execution-report.schema.json` — change status enum to include `pass|fail|blocked|escalate`; add separate `review_status` field for the document lifecycle
  - `docs/EXECUTION_REPORT_TEMPLATE.md` — align Executive Decision values
  - SADP §2 — align PASS|FAIL|BLOCKED with schema
- **Test**: Sample ExecutionReport JSON validates against updated schema.
- **Verification**: None of the existing reports would break (they use Markdown, not JSON).
- **Risk**: LOW. Schemas are not runtime-validated today, so consumers aren't broken.

### Fix 4: Call task mode from sadp-audit when TaskSpec exists (addresses P0-6)
- **Files to modify**: `scripts/sadp-audit.ps1` — after detecting TaskSpecs exist, call `python tools/ai_guard.py task <task-file>` for the most relevant TaskSpec.
- **Test**: Create a TaskSpec with allow_write=[], make a change, run pre-commit — should block.
- **Verification**: Git commit of a file outside TaskSpec scope should fail.
- **Risk**: LOW. Only activates when TaskSpec exists, which is rare (gated on 3+ files or governance files).

### Fix 5: Validate gate_0 content in sadp-audit (addresses P0-5)
- **Files to modify**: `scripts/sadp-audit.ps1` — add a YAML parse of TaskSpec content to check gate_0.inventory_evidence existence and completeness.
- **Test**: TaskSpec with gate_0 but no inventory_evidence → sadp-audit blocks.
- **Verification**: Pre-commit blocks on construction tasks without proper gate_0.
- **Risk**: LOW. Only activates when TaskSpec exists.

### Fix 6: Add freshness to EvidenceIndex schema (addresses P1-1)
- **Files to modify**: `schemas/agent-runtime/evidence-index.schema.json` — add freshness enum, currency_basis, approved_run_id fields.
- **Risk**: LOW. Additive.

### Fix 7: Tighten GateResult signer_role (addresses P1-2)
- **Files to modify**: `schemas/agent-runtime/gate-result.schema.json` — change `"not": { "const": "executor" }` to `"not": { "enum": ["executor", "fixer", "coder"] }`.
- **Risk**: LOW.

### Fix 8: Add Test-Governance advisory to pre-commit (addresses P1-3)
- **Files to modify**: `hooks/pre-commit.governance.ps1` — add `Test-Governance.ps1 -Mode advisory` after sadp-audit.
- **Risk**: LOW. Advisory mode always exits 0; violations logged but not blocking.

### Fix 9: Expand canary suite (addresses P2-4)
- **Files to modify**: `scripts/tests/Invoke-GovernanceCanarySuite.ps1` — add canaries for: self-review, evidence missing, P0 unresolved pass.
- **Risk**: LOW. Tests run in temp dir.

---

## Reviewer Index

### Files Read (complete)
1. `AGENTS.md` — agent instructions, hard stops, document map, phase boundaries
2. `templates/runtime-bootstrap/SKILL.md` — @go skill orchestrator definition
3. `docs/agent-runtime/sub-agent-dispatch-protocol.md` — SADP v1.0 full spec
4. `tools/ai_guard.py` — unified rule engine (286 lines)
5. `scripts/sadp-audit.ps1` — external SADP compliance auditor (285 lines)
6. `.github/workflows/ai-guard.yml` — CI workflow definition
7. `.ai/policy.yaml` — canonical policy rules
8. `hooks/pre-edit.governance.ps1` — governance pre-edit hook
9. `hooks/pre-commit.governance.ps1` — pre-commit governance gate
10. `hooks/pre-push.governance.ps1` — pre-push governance gate
11. `hooks/sealed-files-manifest.json` — file manifest with SHA256 hashes
12. `scripts/Test-Governance.ps1` — authoritative diff gate
13. `scripts/Test-GovernanceDrift.ps1` — full-repo governance drift check
14. `scripts/Test-GovernanceManifest.ps1` — manifest sync verification
15. `scripts/checks/Test-ProtectedPaths.ps1` — protected path check
16. `scripts/checks/Test-KeyScan.ps1` — secret scan via ai_guard
17. `scripts/tests/Invoke-GovernanceCanarySuite.ps1` — canary test suite
18. `rules/core.md` — 8 core runtime rules
19. `rules/review.md` — 6 review rules
20. `rules/security.md` — 8 security rules
21. `rules/git.md` — 6 git safety rules
22. `rules/README.md` — rule index
23. `schemas/agent-runtime/task-spec.schema.json` — TaskSpec schema
24. `schemas/agent-runtime/execution-report.schema.json` — ExecutionReport schema
25. `schemas/agent-runtime/gate-result.schema.json` — GateResult schema
26. `schemas/agent-runtime/evidence-index.schema.json` — EvidenceIndex schema
27. `schemas/agent-runtime/run-spec.schema.json` — RunSpec schema
28. `schemas/agent-runtime/README.md` — schema index
29. `docs/agent-runtime/authority-matrix.md` — authority matrix
30. `docs/agent-runtime/governance-manifest.md` — legacy governance manifest
31. `docs/agent-runtime/verification-gates.md` — P0-P3 gate hierarchy
32. `docs/agent-runtime/integration-contracts.md` — 8 core data contracts
33. `docs/agent-runtime/audit-record.schema.md` — Plan Auditor output schema
34. `docs/agent-runtime/session-ledger.schema.md` — session compliance evidence
35. `docs/RECOVERY_PIPELINE_RUNBOOK.md` — recovery pipeline
36. `docs/EXECUTION_REPORT_TEMPLATE.md` — execution report template

### Commands Run
- `ls` of all major directories (docs, schemas, tools, scripts, hooks, runs, reports, tasks, .ai, governance)
- `git log --oneline -10` to verify recent commit compliance

### Not Covered
- `docs/agent-runtime/capability-inventory.md` — read the sealed manifest's hash reference but not the full 33KB content
- `schemas/resource-integration/` — 10 resource integration schemas not audited (out of scope)
- `agent-workqueue/` — work queue JSON not audited (separate system)
- dev-frame and test-frame external systems — referenced but not part of this repo
- Actual runtime execution of `ai_guard.py evidence` — not tested because evidence directory doesn't exist
- Real pre-commit hook behavior — confirmed active via git log but not executed in this session

### Audit Limitations
- This is a structural/static audit. Dynamic behavior (hook execution, race conditions, multi-agent timing) was not tested.
- The audit assumes documentation is accurate for declared intent. Where docs and code conflict, I flagged the conflict.
- Canary suite execution was not performed (destructive git operations require explicit permission per audit scope).
- Schema validation against actual data files was not performed (no runtime JSON validator was run).
