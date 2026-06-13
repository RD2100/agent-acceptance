# Quality Review: Multi-Agent Readiness Scripts

| Field | Value |
|-------|-------|
| **Task ID** | ma-quality-review-a1 |
| **Reviewer Role** | Quality-Reviewer |
| **Parallel Group** | local-readiness |
| **Date** | 2026-06-13 |
| **Verdict** | **PASS** |
| **P0 Count** | 0 |
| **P1 Count** | 0 |
| **P2 Count** | 5 |

---

## Verdict

**PASS.** All three readiness scripts (`multi_agent_gate0_preflight.py`, `multi_agent_dispatch_plan.py`, `production_readiness_gate.py`) correctly implement fail-closed semantics. No P0 or P1 safety issues were found. Five P2 observations are documented below with file:line evidence. The fake-green resistance posture is strong: every layer (schema constraints, semantic validation, and test suite) independently prevents `HUMAN_REQUIRED` from being silently downgraded to `PASS`/`READY`.

---

## Scope

This review audits the following scripts, schemas, and test files for safety, error handling, and fake-green resistance:

### Scripts Reviewed

| File | Lines | Role |
|------|-------|------|
| `D:\agent-acceptance\scripts\multi_agent_gate0_preflight.py` | 560 | Gate 0 read-only preflight checker |
| `D:\agent-acceptance\scripts\multi_agent_dispatch_plan.py` | 582 | Dispatch plan builder with conflict detection |
| `D:\agent-acceptance\scripts\production_readiness_gate.py` | 637 | Three-mode production readiness gate |
| `D:\agent-acceptance\scripts\validate_multi_agent_dispatch_plan.py` | 100 | Consumer-side dispatch plan validator |

### Schemas Reviewed

| File | Lines |
|------|-------|
| `D:\agent-acceptance\schemas\agent-runtime\multi-agent-gate0-preflight.schema.json` | 83 |
| `D:\agent-acceptance\schemas\agent-runtime\multi-agent-dispatch-plan.schema.json` | 478 |

### Tests Reviewed

| File | Tests | Key Coverage Areas |
|------|-------|-------------------|
| `D:\agent-acceptance\tests\test_multi_agent_gate0_preflight.py` | 11 | Authorization, stale sessions, future approval, path escape, schema enforcement, duplicate agents, proposed capability |
| `D:\agent-acceptance\tests\test_multi_agent_dispatch_plan.py` | 12 | Schema validation, preflight binding, write conflict detection, CLI output, READY gate, malformed input |
| `D:\agent-acceptance\tests\test_production_readiness_gate.py` | 22 | All three modes, missing/stale/tampered evidence, hash verification, stress probes, session freshness, pilot binding, authorization |
| `D:\agent-acceptance\tests\test_validate_multi_agent_dispatch_plan.py` | 9 | Current plan validation, schema drift, write conflict replay, external runtime claim, malformed JSON |
| `D:\agent-acceptance\tests\test_cross_repo_execution_guards.py` | 14 | Default human-required, auth required, legacy auth rejection, expired auth, known-issue fake-green, timeouts, missing cwd |

**Total: 68 tests executed via pytest across 5 test files.**

---

## Audit Area 1: Gate 0 Preflight (`multi_agent_gate0_preflight.py`)

### 1.1 Missing Authorization Handling -- PASS

The script properly fails when authorization is missing or incomplete.

| Scenario | Behavior | Evidence |
|----------|----------|----------|
| Activation record file missing | `human_required` | `multi_agent_gate0_preflight.py:97-105` -- `if not path.exists()` returns check with status `human_required` |
| Activation record JSON invalid | `blocked` | `multi_agent_gate0_preflight.py:107-109` -- `_load_json` error path returns `blocked` |
| `authorized` not `true` | `human_required` | `multi_agent_gate0_preflight.py:131-132` |
| `risk_acknowledged` not `true` | `human_required` | `multi_agent_gate0_preflight.py:133-134` |
| Missing required auth strings | `human_required` | `multi_agent_gate0_preflight.py:120-131` -- loop over `required_strings` (authorizing_task, exact_command, evidence_file, decision_maker, decision_reason) |
| Empty `expected_write_set` | `human_required` | `multi_agent_gate0_preflight.py:135-141` |
| Auth evidence file invalid | `human_required` | `multi_agent_gate0_preflight.py:166-176` -- validates run_id and authorized in evidence |
| Expired authorization | `human_required` | `multi_agent_gate0_preflight.py:154-155` |
| Future `approved_at` | `human_required` | `multi_agent_gate0_preflight.py:150-151` -- clock skew tolerance applied |
| `exact_command` missing `run_id` | `human_required` | `multi_agent_gate0_preflight.py:157-159` |

**Test coverage:**
- `test_active_bindings_without_run_bound_authorization_require_human_gate` (line 206): verifies exit_code=2, overall=HUMAN_REQUIRED when activation record is missing.
- `test_future_authorization_approval_requires_human_gate` (line 296): verifies future approved_at is caught.
- `test_activation_evidence_cannot_escape_repository_root` (line 335): verifies path traversal is blocked.

### 1.2 Stale Session Evidence (>15 min) -- PASS

| Parameter | Value | Evidence |
|-----------|-------|----------|
| `SESSION_EVIDENCE_MAX_AGE_SECONDS` | `15 * 60` (900 seconds) | `multi_agent_gate0_preflight.py:29` |
| `CLOCK_SKEW_TOLERANCE_SECONDS` | `5 * 60` (300 seconds) | `multi_agent_gate0_preflight.py:30` |
| Stale check logic | `age_seconds > SESSION_EVIDENCE_MAX_AGE_SECONDS` | `multi_agent_gate0_preflight.py:228-232` |
| Future check logic | `age_seconds < -CLOCK_SKEW_TOLERANCE_SECONDS` | `multi_agent_gate0_preflight.py:229-230` |

When session evidence is stale, the `live_agent_sessions` check returns `human_required`, which propagates to `overall=HUMAN_REQUIRED` via the priority logic at lines 494-499.

**Test coverage:**
- `test_stale_session_evidence_requires_human_gate` (line 265): uses `stale_sessions=True` which sets `verified_at` to `now - 2 hours` (line 81), well beyond the 15-minute threshold. Asserts exit_code=2, overall=HUMAN_REQUIRED, and "stale" in check detail.

### 1.3 External Runtime Execution Rejection -- PASS

| Layer | Mechanism | Evidence |
|-------|-----------|----------|
| Code | `evaluate_preflight` hardcodes `executed_external_runtime: False` | `multi_agent_gate0_preflight.py:508` |
| Schema | `executed_external_runtime` has `"const": false` | `multi-agent-gate0-preflight.schema.json:25-27` |
| Schema (conditional) | `overall=PASS` requires `human_gate_required=false`; `overall=HUMAN_REQUIRED` requires `human_gate_required=true` | `multi-agent-gate0-preflight.schema.json:62-81` |

**Test coverage:**
- `test_schema_rejects_external_runtime_execution_flag` (line 445): verifies schema rejects `executed_external_runtime: true`.
- `test_schema_rejects_human_required_without_gate_flag` (line 468): verifies schema rejects contradictory `HUMAN_REQUIRED` + `human_gate_required: false`.

### 1.4 Additional Safety Properties

- **Path traversal protection**: `_resolve_evidence_path` at lines 74-91 resolves paths and enforces `candidate.relative_to(root)`, rejecting any evidence file outside the repository root.
- **Session ID uniqueness**: Lines 265-275 require at least 2 distinct session IDs, preventing a single session from claiming to be multiple agents.
- **CDP session verification**: Line 251 requires `cdp_session.active=true`.
- **CAP-029 inventory check**: Lines 396-436 validate that the capability is registered and approved for execution.
- **Tool policy terms**: Lines 439-467 require specific runtime gate terms in the policy document.

---

## Audit Area 2: Dispatch Plan (`multi_agent_dispatch_plan.py`)

### 2.1 Preflight PASS Gate Before READY -- PASS

The `build_plan()` function at lines 511-540 uses a tiered status determination:

1. Default: `status = "READY"`
2. If conflict errors exist: `status = "BLOCKED"` (line 525-526)
3. If preflight is HUMAN_REQUIRED or human_gate_required: `status = "HUMAN_REQUIRED"` (line 527-528)
4. If preflight is BLOCKED: `status = "BLOCKED"` (line 529-530)

The `validate_plan()` function at lines 469-508 adds an independent semantic layer:

| Check | Evidence |
|-------|----------|
| `executed_external_runtime` must be `false` | `multi_agent_dispatch_plan.py:473-474` |
| Source preflight `executed_external_runtime` must not be `true` | `multi_agent_dispatch_plan.py:476-477` |
| READY status requires PASS preflight with `human_gate_required=false` | `multi_agent_dispatch_plan.py:479-482` |
| READY status requires all human-gated activation tasks resolved (status in completed/closed/accepted_with_limitation, no blocking conditions) | `multi_agent_dispatch_plan.py:483-495` |
| Every embedded TaskSpec validated against JSON schema | `multi_agent_dispatch_plan.py:497-504` |

The dispatch plan schema adds conditional constraints via `allOf`:
- `status=READY` implies `source_preflight.overall=PASS` and `source_preflight.human_gate_required=false` (lines 420-454)
- `status=HUMAN_REQUIRED` implies `source_preflight.human_gate_required=true` (lines 456-476)
- `executed_external_runtime` has `"const": false` (line 30)

**Test coverage:**
- `test_default_plan_matches_preflight_and_is_read_only` (line 79): verifies current preflight produces HUMAN_REQUIRED plan.
- `test_ready_plan_rejects_deferred_human_activation_tasks` (line 253): verifies a forged PASS preflight cannot hide unresolved human activation tasks.
- `test_missing_preflight_returns_blocked_plan_without_traceback` (line 279): verifies missing preflight produces BLOCKED without crashing.

### 2.2 Write Conflict Detection Between Parallel Workers -- PASS

The `_summarize_conflicts()` function at lines 426-466 implements:

| Check | Evidence |
|-------|----------|
| Duplicate `task_id` detection | `multi_agent_dispatch_plan.py:432-435` |
| `parallel_safe=true` tasks touching protected files flagged | `multi_agent_dispatch_plan.py:438-440` |
| Write-set overlap detection within same parallel group | `multi_agent_dispatch_plan.py:447-458` |
| Path normalization for cross-platform comparison | `multi_agent_dispatch_plan.py:39-41` (`_norm` replaces backslashes, strips, removes trailing slash) |
| Directory/file prefix overlap detection | `multi_agent_dispatch_plan.py:46-50` (`_paths_conflict` handles exact match, parent-child, and child-parent) |

The `_paths_conflict` function correctly handles three overlap cases:
1. Exact path match: `left_norm == right_norm`
2. Left is parent of right: `right_norm.startswith(left_norm + "/")`
3. Right is parent of left: `left_norm.startswith(right_norm + "/")`

**Test coverage:**
- `test_parallel_ready_assignments_have_disjoint_write_sets` (line 171): verifies default plan has no write overlaps.
- `test_validate_plan_detects_parallel_write_conflict` (line 185): verifies exact-path overlap is caught.
- `test_validate_plan_detects_directory_file_write_conflict` (line 204): verifies directory/file prefix overlap is caught.

---

## Audit Area 3: Production Readiness Gate (`production_readiness_gate.py`)

### 3.1 Three-Input Requirement -- PASS

The `evaluate_readiness()` function at lines 545-601 enforces mode-based input requirements:

| Mode | Required Inputs | Evidence |
|------|----------------|----------|
| `local_governance` | `local_evidence` | `production_readiness_gate.py:564` |
| `controlled_pilot` | `local_evidence` + `preflight` + `dispatch_plan` | `production_readiness_gate.py:564-569` |
| `formal_use` | All of the above + `pilot_evidence` + `production_authorization` | `production_readiness_gate.py:564-585` |

Missing inputs are handled with the `missing_status` parameter in `_load_json`:
- Missing `local_evidence` produces `blocked` (line 121: `missing_status="blocked"`)
- Missing `preflight` produces `human_required` (line 245: `missing_status="human_required"`)
- Missing `dispatch_plan` produces `human_required` (line 284: `missing_status="human_required"`)
- Missing `pilot_evidence` produces `human_required` (line 359: `missing_status="human_required"`)
- Missing `production_authorization` produces `human_required` (line 491: `missing_status="human_required"`)

CLI enforces `--local-evidence` as required via argparse (line 608).

**Test coverage:**
- `test_missing_local_evidence_is_blocked` (line 245): exit_code=1, status=BLOCKED.
- `test_formal_use_requires_real_pilot_evidence` (line 525): missing pilot evidence produces HUMAN_REQUIRED.
- `test_formal_use_requires_production_authorization` (line 653): missing authorization produces HUMAN_REQUIRED.

### 3.2 Invalid Input Rejection -- PASS

Each input undergoes multi-layer validation:

**Local evidence** (`_validate_local`, lines 119-239):
- Freshness check (24h max age via `MAX_EVIDENCE_AGE_SECONDS`, 5min clock skew tolerance)
- `task_id` must match `PRODUCTION-READINESS-AUTOMATION-A1` (line 128-129)
- Canonical tests: command must be `python -m pytest tests/ -q`, exit_code=0, failed=0, passed>0 (lines 134-141)
- SHA256 verification of raw test output (lines 146-153)
- Raw output text confirmation of passed count (lines 154-156)
- Three stress probes validated with exact expected behavior: `allowed_edit` (PASS), `forbidden_edit` (BLOCKED), `missing_finish_artifacts` (BLOCKED) (lines 158-229)
- Each probe evidence file verified for: name, task_id, file, status, exit_code, runner command, output markers (lines 202-229)
- `executed_external_runtime` must be `false` (lines 231-232)

**Preflight** (`_validate_preflight`, lines 242-276):
- Freshness check (line 248-252)
- `executed_external_runtime` must be `false` (lines 253-256)
- Contradictory state detection: `overall` and `human_gate_required` must be consistent (lines 271-276)

**Dispatch plan** (`_validate_dispatch`, lines 279-349):
- Freshness check (lines 287-291)
- `executed_external_runtime` must be `false` (lines 292-293)
- READY dispatch requires PASS source preflight (lines 296-306)
- Source preflight path must match the current preflight input (lines 308-318)
- Source preflight SHA256 must match the actual file on disk (lines 319-327)
- Source preflight fields (`generated_at`, `overall`, `human_gate_required`) must match actual data (lines 328-338)
- Source preflight `executed_external_runtime` must be false (lines 337-338)
- Source preflight freshness independently checked (line 339)

**Pilot evidence** (`_validate_pilot`, lines 352-481):
- Freshness check on `completed_at` (line 364)
- `executed_external_runtime` must be `true` (line 371) -- real pilot must have executed
- SHA256 bindings to exact preflight and dispatch plan artifacts (lines 373-392)
- At least 2 agent sessions with distinct session IDs (lines 397-440)
- Each session evidence file validated for freshness, agent_id, session_id, `live=true`, verified_at consistency (lines 400-438)
- Independent review: verdict=pass, reviewer_id distinct from executor_ids, evidence_files include .md and .yaml (lines 442-470)

**Production authorization** (`_validate_authorization`, lines 484-542):
- `authorized=true` required (lines 496-502)
- `scope=formal_use` required (line 505-506)
- `run_id` must match pilot run_id (lines 507-508)
- `risk_acknowledged=true` required (lines 509-510)
- Non-empty `authorization_id`, `decision_maker`, `decision_reason` (lines 511-514)
- Temporal ordering: `approved_at` must be after pilot `completed_at` (lines 523-524)
- Expiry check (lines 529-535)

**Test coverage (selected):**
- `test_stale_local_evidence_is_blocked` (line 257)
- `test_local_raw_output_hash_mismatch_is_blocked` (line 272)
- `test_synthetic_probe_without_runner_command_and_output_is_blocked` (line 286)
- `test_ready_dispatch_requires_pass_source_preflight` (line 343)
- `test_ready_dispatch_source_preflight_path_must_match_current_preflight` (line 362)
- `test_ready_dispatch_source_preflight_hash_mismatch_is_blocked` (line 392)
- `test_formal_use_rejects_duplicate_session_ids` (line 539)
- `test_formal_use_binds_pilot_to_exact_preflight_artifact` (line 633)
- `test_production_authorization_must_follow_pilot` (line 683)
- `test_expired_production_authorization_is_human_required` (line 702)
- `test_report_never_claims_external_runtime_execution` (line 760, parametrized across all 3 modes)

### 3.3 Repository Path Escape Protection -- PASS

`_load_json` at lines 60-71 and `_resolve_file` at lines 87-104 both enforce `candidate.relative_to(root)`, rejecting any evidence path outside the repository root.

**Test coverage:**
- `test_repo_escape_is_blocked` (line 745)
- `test_preflight_repo_escape_is_blocked` (line 507)
- `test_ready_dispatch_source_preflight_repo_escape_is_blocked` (line 411)

---

## Audit Area 4: Fake-Green Resistance

### 4.1 Schema-Level Defenses

| Schema | Constraint | Evidence |
|--------|-----------|----------|
| Preflight | `executed_external_runtime` const `false` | `multi-agent-gate0-preflight.schema.json:25` |
| Preflight | `overall=PASS` implies `human_gate_required=false` | `multi-agent-gate0-preflight.schema.json:63-71` |
| Preflight | `overall=HUMAN_REQUIRED` implies `human_gate_required=true` | `multi-agent-gate0-preflight.schema.json:73-80` |
| Dispatch | `executed_external_runtime` const `false` | `multi-agent-dispatch-plan.schema.json:30` |
| Dispatch | `status=READY` implies `source_preflight.overall=PASS` and `human_gate_required=false` | `multi-agent-dispatch-plan.schema.json:420-454` |
| Dispatch | `status=HUMAN_REQUIRED` implies `source_preflight.human_gate_required=true` | `multi-agent-dispatch-plan.schema.json:456-476` |
| Dispatch | `source_preflight.executed_external_runtime` const `false` | `multi-agent-dispatch-plan.schema.json:63-65` |

### 4.2 Semantic-Level Defenses

| Script | Defense | Evidence |
|--------|---------|----------|
| `gate0_preflight` | Three-state output (PASS/HUMAN_REQUIRED/BLOCKED) with explicit priority ordering: blocked > human_required > pass | `multi_agent_gate0_preflight.py:494-502` |
| `gate0_preflight` | Activation record validation checks 10+ independent conditions including evidence file cross-references | `multi_agent_gate0_preflight.py:94-276` |
| `dispatch_plan` | `validate_plan` independently verifies READY preconditions beyond schema constraints | `multi_agent_dispatch_plan.py:469-508` |
| `dispatch_plan` | `_summarize_conflicts` recomputes write conflicts from scratch, does not trust stale summary | `multi_agent_dispatch_plan.py:426-466` |
| `dispatch_plan` | `main()` re-validates the built plan and forces BLOCKED if validation fails | `multi_agent_dispatch_plan.py:559-565` |
| `production_readiness` | `_validate_dispatch` recomputes source preflight SHA256 from disk, does not trust embedded claims | `production_readiness_gate.py:319-327` |
| `production_readiness` | `_validate_pilot` binds to exact preflight and dispatch artifacts via SHA256 comparison | `production_readiness_gate.py:373-392` |
| `validate_dispatch_plan` | Independent validator re-runs `validate_plan` semantic checks on serialized plans | `validate_multi_agent_dispatch_plan.py:55-84` |

### 4.3 Test-Level Defenses (Fake-Green Specific)

| Test | What It Prevents | Evidence |
|------|-----------------|----------|
| `test_schema_rejects_external_runtime_execution_flag` | Cannot claim PASS while asserting external runtime was executed | `test_multi_agent_gate0_preflight.py:445-465` |
| `test_schema_rejects_human_required_without_gate_flag` | Cannot set HUMAN_REQUIRED without human_gate_required=true | `test_multi_agent_gate0_preflight.py:468-488` |
| `test_ready_plan_rejects_deferred_human_activation_tasks` | Forged PASS preflight cannot hide unresolved human tasks | `test_multi_agent_dispatch_plan.py:253-276` |
| `test_validator_rejects_external_runtime_execution_claim` | Dispatch plan cannot claim external runtime execution | `test_validate_multi_agent_dispatch_plan.py:85-95` |
| `test_validator_rejects_parallel_write_conflict` | Stale conflict summary cannot hide real write conflicts | `test_validate_multi_agent_dispatch_plan.py:61-82` |
| `test_multi_repo_smoke_known_issues_do_not_fake_green` | KNOWN_ISSUES label cannot convert non-zero exit to PASS | `test_cross_repo_execution_guards.py:316-344` |
| `test_cross_repo_verify_default_is_human_required` | Default mode never silently executes | `test_cross_repo_execution_guards.py:38-51` |
| `test_cross_repo_verify_rejects_legacy_lightweight_auth` | Legacy auth cannot authorize execution | `test_cross_repo_execution_guards.py:179-204` |
| `test_report_never_claims_external_runtime_execution` | All modes hardcode executed_external_runtime=false | `test_production_readiness_gate.py:760-769` |
| `test_formal_use_requires_real_pilot_evidence` | Cannot skip pilot evidence for formal_use | `test_production_readiness_gate.py:525-536` |

### 4.4 KNOWN_ISSUES Analysis

The `KNOWN_ISSUES` status in `multi_repo_smoke.py` was previously flagged as a potential fake-green vector. Analysis confirms it is safe:

- `KNOWN_ISSUES` is not equal to `"PASS"`, so the overall aggregation `all(v["status"] == "PASS" for v in results.values())` evaluates to `False`.
- The overall result is `FAIL` with exit code 1 when any repo has `KNOWN_ISSUES` status.
- The test `test_multi_repo_smoke_known_issues_do_not_fake_green` (line 316) confirms: `assert exit_code == 1` and `assert report["overall"] == "FAIL"`.

---

## Findings

### P0 Findings: None

### P1 Findings: None

### P2 Findings

#### P2-01: Early Return in `_validate_activation_record` Limits Diagnostic Visibility

**File**: `D:\agent-acceptance\scripts\multi_agent_gate0_preflight.py:97-105`

When the activation record file does not exist, the function returns early with only a `run_authorization` check (status `human_required`). It does not produce `live_agent_sessions` or `independent_session_ids` checks because `agent_ids` is empty at that point (it comes from binding validation, not the activation record). This is correct fail-closed behavior, but it means the report contains fewer diagnostic checks than when the activation record exists but is invalid.

**Severity rationale**: No safety impact. The `human_required` status propagates correctly. Diagnostic completeness issue only.

#### P2-02: Cross-Group Write Conflicts Not Checked

**File**: `D:\agent-acceptance\scripts\multi_agent_dispatch_plan.py:442-458`

`_summarize_conflicts()` only checks write conflicts within the same `parallel_group_id`. If tasks from different parallel groups (e.g., `local-readiness` and `serial-integration`) both write to the same path, no conflict is flagged. This is mitigated by the current plan architecture:
- Serial tasks (`parallel_safe=false`) are excluded from the conflict check loop at line 444
- The Integrator task (`serial-integration` group) runs only after first-wave tasks complete (declared via `depends_on`)
- Each parallel group has exclusive write targets (`_reports/multi-agent-*/` directories)

**Severity rationale**: No current risk. The plan architecture prevents cross-group write overlap by design. Would become relevant if the plan structure changes.

#### P2-03: No Explicit Test for Malformed Activation Record JSON

**File**: `D:\agent-acceptance\tests\test_multi_agent_gate0_preflight.py`

While `_load_json` at `multi_agent_gate0_preflight.py:42-53` handles `JSONDecodeError` and returns `blocked`, there is no dedicated test for a corrupt/malformed activation record JSON file. The `test_missing_binding_blocks` test (line 429) covers the missing-file path for bindings but not specifically for the activation record.

**Severity rationale**: The code path is covered generically by `_load_json` error handling. Adding a test would improve defense-in-depth documentation but is not required for safety.

#### P2-04: CLI/Library Interface Inconsistency for `--local-evidence`

**File**: `D:\agent-acceptance\scripts\production_readiness_gate.py:549` vs line 608

The argparse definition uses `required=True` for `--local-evidence`, but the `evaluate_readiness()` function signature accepts `local_evidence: Path | None = None`. When called programmatically with `local_evidence=None`, `_validate_local` correctly returns a `blocked` check via `_load_json(None, ...)` at lines 57-58 and 120-123. The behavior is correct but the interface contract is inconsistent between CLI and library usage.

**Severity rationale**: No safety impact. The fail-closed behavior is correct. Documentation clarity issue only.

#### P2-05: Static Gate 0 Evidence in Dispatch Plan Builder

**File**: `D:\agent-acceptance\scripts\multi_agent_dispatch_plan.py:75-102`

The `_gate0()` function returns a fully static dictionary for every TaskSpec's `gate_0` field, claiming specific `queried_sources`, `matched_capabilities`, and `sufficiency_decision` values. None of these are computed at runtime; they are hardcoded assertions. While this is appropriate for a plan builder (which declares intent, not execution results), the output looks identical to a genuinely computed Gate 0 result.

**Mitigation**: The `security_report.scan_status` is correctly set to `"not_run"` (line 143), which signals to consumers that the task has not yet executed. The test `test_generated_security_report_starts_not_run` (line 160) verifies this.

**Severity rationale**: No safety impact. The `scan_status: "not_run"` field provides a signal. However, the `gate_0` field lacks an equivalent "not yet evaluated" marker.

---

## Changed Files

None. This is a read-only quality audit. No scripts, tests, schemas, docs, or .agent files were modified.

---

## Known Gaps

1. **No end-to-end pipeline test**: There is no single test that runs `gate0_preflight -> dispatch_plan -> production_readiness_gate` as an integrated chain with consistent artifacts. Each script is tested in isolation with synthetic fixtures. This is acceptable for the current scope (the scripts consume each other's JSON artifacts), but a full-chain integration test would strengthen confidence.

2. **No fuzz testing on JSON inputs**: Malformed JSON handling is tested for top-level non-object and null cases (`test_validate_multi_agent_dispatch_plan.py:98-126`), but there is no systematic fuzz testing of deeply nested malformed structures.

3. **Timestamp-dependent tests**: Several tests use `datetime.now()` in fixture construction, which means they could theoretically become flaky near midnight or during NTP adjustments. The 5-minute clock skew tolerance mitigates this for production code, but test fixtures do not mock the clock.

4. **Schema `format` keyword not enforced**: The schemas use `"format": "date-time"` but `jsonschema` does not enforce format validation by default without a registered format checker. The scripts implement their own timestamp parsing (`_parse_timestamp` / `_parse_time`), which provides the real validation. The schema `format` keyword serves as documentation only.

5. **No partial tool-policy term test**: The `_validate_tool_policy` function handles the case where some but not all required terms are present (line 450: `missing = [term for term in required_terms if term not in text]`), but no test exercises this specific scenario.

---

## Residual Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Fake-green via forged preflight artifact | Very Low | High | SHA256 binding, freshness checks, schema constraints, and semantic validation all independently prevent this |
| Fake-green via stale authorization | Low | High | 15-min session freshness, 24h evidence freshness, expiry checks on all authorization records |
| Fake-green via path traversal | Very Low | Medium | `relative_to(root)` enforcement on all evidence paths, tested with multiple `test_*_repo_escape_is_blocked` tests |
| Undetected write conflict in plan | Very Low | Low | Current plan structure prevents this by design; conflict detection is comprehensive within parallel groups |
| Schema drift between plan and task-spec | Low | Medium | `test_plan_schema_task_spec_definition_tracks_core_task_schema_contract` and nested contract tests detect drift |

**Overall residual risk: LOW.** The defense-in-depth approach (schema constraints + semantic validation + comprehensive test suite) provides strong protection against false readiness claims. The three-layer architecture ensures that no single compromised layer can produce a fake-green result.

---

## Reviewer Index

| File | Lines Reviewed | Findings |
|------|---------------|----------|
| `D:\agent-acceptance\scripts\multi_agent_gate0_preflight.py` | 1-560 (full) | P2-01, P2-03 |
| `D:\agent-acceptance\scripts\multi_agent_dispatch_plan.py` | 1-582 (full) | P2-02, P2-05 |
| `D:\agent-acceptance\scripts\production_readiness_gate.py` | 1-637 (full) | P2-04 |
| `D:\agent-acceptance\scripts\validate_multi_agent_dispatch_plan.py` | 1-100 (full) | None |
| `D:\agent-acceptance\schemas\agent-runtime\multi-agent-gate0-preflight.schema.json` | 1-83 (full) | None |
| `D:\agent-acceptance\schemas\agent-runtime\multi-agent-dispatch-plan.schema.json` | 1-478 (full) | None |
| `D:\agent-acceptance\tests\test_multi_agent_gate0_preflight.py` | 1-489 (full) | None |
| `D:\agent-acceptance\tests\test_multi_agent_dispatch_plan.py` | 1-285 (full) | None |
| `D:\agent-acceptance\tests\test_production_readiness_gate.py` | 1-770 (full) | None |
| `D:\agent-acceptance\tests\test_validate_multi_agent_dispatch_plan.py` | 1-182 (full) | None |
| `D:\agent-acceptance\tests\test_cross_repo_execution_guards.py` | 1-448 (full) | None |

---

## Suggested Review Focus for Next Wave

1. **End-to-end pipeline test**: A single test that builds a complete chain from synthetic preflight through dispatch plan to production readiness gate, verifying SHA256 bindings and status propagation end-to-end.
2. **Clock-mocked tests**: Replace `datetime.now()` calls in test fixtures with a mock clock to eliminate theoretical flakiness near time boundaries.
3. **Activation record JSON malformation test**: Add an explicit test for corrupt activation record JSON to document the blocked-path behavior.
4. **Partial tool-policy term test**: Add a test where 1-3 of the 4 required tool-policy terms are present, verifying the correct error message.

---

## Governance Notes

- No git operations performed.
- No forbidden paths modified.
- No external runtime executed.
- `executed_external_runtime: false` throughout.
