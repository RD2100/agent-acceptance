# Quality Review: Multi-Agent Readiness Scripts

| Field | Value |
|---|---|
| **Reviewer** | Quality-Reviewer (ma-quality-review-a1) |
| **Date** | 2026-06-13 |
| **Verdict** | **PARTIAL** |
| **Scope** | 6 primary files + 4 supporting files |
| **P0 Findings** | 0 |
| **P1 Findings** | 2 |
| **P2 Findings** | 5 |
| **Residual Risks** | 3 |

---

## 1. Files Reviewed

| File | Lines | Role |
|---|---|---|
| `D:\agent-acceptance\scripts\multi_agent_gate0_preflight.py` | 308 | Gate 0 read-only preflight checker |
| `D:\agent-acceptance\scripts\multi_agent_dispatch_plan.py` | 519 | Dispatch plan builder with conflict detection |
| `D:\agent-acceptance\scripts\validate_multi_agent_dispatch_plan.py` | 100 | Consumer-side dispatch plan validator |
| `D:\agent-acceptance\tests\test_multi_agent_gate0_preflight.py` | 244 | Tests for Gate 0 preflight |
| `D:\agent-acceptance\tests\test_cross_repo_execution_guards.py` | 447 | Tests for cross-repo execution guards |
| `D:\agent-acceptance\scripts\cross_repo_authorization.py` | 129 | Shared authorization validation logic |
| `D:\agent-acceptance\scripts\cross_repo_verify.py` | 170 | Cross-repo verification script (supporting) |
| `D:\agent-acceptance\scripts\multi_repo_smoke.py` | 175 | Cross-repo smoke test script (supporting) |
| `D:\agent-acceptance\schemas\agent-runtime\multi-agent-gate0-preflight.schema.json` | 78 | Preflight report schema (supporting) |
| `D:\agent-acceptance\schemas\agent-runtime\multi-agent-dispatch-plan.schema.json` | 464 | Dispatch plan schema (supporting) |

---

## 2. Fake-Green Risk Assessment

### 2.1 No Critical Fake-Green Vectors

The following anti-fake-green mechanisms are **correctly implemented** and verified by tests:

| Mechanism | Location | Test Coverage |
|---|---|---|
| `executed_external_runtime` locked to `false` | Preflight schema line 20: `"const": false` | `test_schema_rejects_external_runtime_execution_flag` (test file line 201-221) |
| Schema conditional constraints (PASS requires `human_gate_required=false`) | Preflight schema lines 57-76 | `test_schema_rejects_human_required_without_gate_flag` (test file line 224-244) |
| Cross-repo scripts default to HUMAN_REQUIRED | `cross_repo_verify.py` lines 109-117, `multi_repo_smoke.py` lines 113-121 | `test_cross_repo_verify_default_is_human_required` (guard test line 38-51), `test_multi_repo_smoke_default_is_human_required` (guard test line 259-272) |
| Subprocess calls fail-closed without authorization | Both cross-repo scripts | Monkeypatched `pytest.fail` on `subprocess.run` (guard test lines 42-43, 57-59, 183-184, 262-264) |
| KNOWN_ISSUES does not fake-green to overall PASS | `multi_repo_smoke.py` lines 91-95 + 138, status is KNOWN_ISSUES which is not PASS so `all_ok` evaluates False | `test_multi_repo_smoke_known_issues_do_not_fake_green` (guard test lines 316-344): asserts overall FAIL and exit code 1 |
| Legacy lightweight auth rejected | `cross_repo_authorization.py` lines 71-73 | `test_cross_repo_verify_rejects_legacy_lightweight_auth` (guard test line 179-204) |
| Expired auth rejected | `cross_repo_authorization.py` lines 121-126 | `test_cross_repo_verify_rejects_expired_auth` (guard test line 236-256) |
| Duplicate agent IDs block preflight | `multi_agent_gate0_preflight.py` lines 132-140 | `test_duplicate_agent_ids_block` (test file line 159-182) |

**Assessment: The core fake-green resistance is solid.** The system correctly defaults to HUMAN_REQUIRED, requires explicit authorization for execution, and schema-enforces that preflight reports cannot claim external runtime execution.

### 2.2 KNOWN_ISSUES Analysis (Previously Flagged as P1 -- Re-evaluated)

**File:** `D:\agent-acceptance\scripts\multi_repo_smoke.py`, lines 90-102 and 138

The previous review flagged the KNOWN_ISSUES path as a P1 fake-green risk. After careful re-inspection:

```python
# Line 91-95
status = (
    "PASS"
    if exit_code == 0
    else ("KNOWN_ISSUES" if name in KNOWN_FAILURES else "FAIL")
)

# Line 138
all_ok = all(v["status"] == "PASS" for v in results.values())
```

KNOWN_ISSUES is **not** equal to "PASS", so `all_ok` is `False`, and the overall result is FAIL with exit code 1. The test at guard test line 339-340 confirms: `assert exit_code == 1` and `assert report["overall"] == "FAIL"`.

**Revised assessment:** KNOWN_ISSUES is correctly treated as a failure at the overall level. It does not fake-green to PASS. However, the `known_failure_allowance` field in the output is not validated against actual failure signatures (see P2-005 below).

### 2.3 Fake-Green Concern: Hardcoded Security Report (P1)

**File:** `D:\agent-acceptance\scripts\multi_agent_dispatch_plan.py`, lines 129-136

```python
"security_report": {
    "new_external_api": False,
    "env_example_placeholders_only": True,
    "real_key_patterns_found": False,
    "staged_diff_secret_scan_run": False,
    "key_rotation_needed": False,
},
```

Every TaskSpec emitted by `_task_spec()` includes a `security_report` with `staged_diff_secret_scan_run: False` and `real_key_patterns_found: False`. These values are **hardcoded**, not computed from actual scan results. A downstream consumer reading the TaskSpec could interpret these as evidence that a real scan was performed and found no issues, when in reality no scan was executed.

**Why this is not P0:** The `security_report` fields in the TaskSpec schema (`task-spec.schema.json` lines 202-246) do not have `"const"` constraints, and the field `staged_diff_secret_scan_run: False` correctly communicates "no scan was run" to an informed reader. The schema requires these fields for task completion, so they serve as a checklist, not as scan evidence.

**Why this is P1:** An uninformed consumer or automated tool could trust these values as scan evidence. The dispatch plan does not annotate the security report as "pre-populated defaults, not actual scan results."

### 2.4 Fake-Green Concern: Static Gate 0 Evidence (P2)

**File:** `D:\agent-acceptance\scripts\multi_agent_dispatch_plan.py`, lines 62-89

The `_gate0()` function returns a fully static dictionary claiming:
- `queried_sources` lists 4 documents
- `matched_capabilities` lists 3 capabilities
- `sufficiency_decision: "existing_partial"`
- `decision: "build_delta"`

None of these are computed at runtime. They are hardcoded assertions. While this is appropriate for a plan builder (not an executor), the output looks identical to a genuinely computed Gate 0 result.

---

## 3. Findings

### P1 Findings

#### P1-001: Hardcoded security_report values indistinguishable from real scan evidence

**File:** `D:\agent-acceptance\scripts\multi_agent_dispatch_plan.py`, lines 129-136

Every TaskSpec emitted includes a `security_report` with hardcoded values. The `staged_diff_secret_scan_run: False` and `real_key_patterns_found: False` fields look like scan results but are static defaults. No annotation distinguishes "not yet scanned" from "scanned and clean."

**Impact:** Downstream consumers or automated tools may trust these values as evidence of actual security scans.

**Recommendation:** Add a `"scan_status": "not_yet_scanned"` field or document in the TaskSpec description that security_report values are defaults to be overwritten during execution.

#### P1-002: Unhandled FileNotFoundError in dispatch plan `_load_json`

**File:** `D:\agent-acceptance\scripts\multi_agent_dispatch_plan.py`, lines 52-53

```python
def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))
```

This function has no error handling. If the preflight JSON file does not exist, `Path.read_text()` raises an unhandled `FileNotFoundError`. Compare with the preflight module's `_load_json` (line 36-42 of `multi_agent_gate0_preflight.py`) which properly handles both `FileNotFoundError` and `JSONDecodeError`, returning a structured tuple.

The `build_plan()` function handles the `None` path case via `_load_preflight()` (line 367-374), but when a path IS supplied and the file is missing or malformed, the script crashes with a raw traceback instead of a structured error.

**Impact:** An operator running `--preflight path/to/missing.json` gets a Python traceback instead of a structured BLOCKED report. This is a silent failure path in the CLI.

**Evidence:** Trace the call chain: `main()` line 494 -> `build_plan()` line 457 -> `_load_preflight()` line 375 -> `_load_json()` line 53 -- unhandled crash.

### P2 Findings

#### P2-001: Encoding inconsistency between preflight and dispatch plan JSON loaders

**Files:**
- `D:\agent-acceptance\scripts\multi_agent_gate0_preflight.py`, line 38: `encoding="utf-8"`
- `D:\agent-acceptance\scripts\multi_agent_dispatch_plan.py`, line 53: `encoding="utf-8-sig"`
- `D:\agent-acceptance\scripts\cross_repo_authorization.py`, line 66: `encoding="utf-8-sig"`
- `D:\agent-acceptance\scripts\validate_conversation_registry.py`, line 122: `encoding="utf-8"`

The preflight and conversation registry validators read files with `encoding="utf-8"`, while the dispatch plan and authorization modules use `encoding="utf-8-sig"`. On Windows, a binding file saved with UTF-8 BOM (common with Notepad, PowerShell) will cause the preflight loader to include the BOM character in the parsed string. While `json.loads` in modern Python handles BOM in most cases, the inconsistency creates a fragile boundary.

**Impact:** A binding file saved with BOM could behave differently between modules. The test `test_cross_repo_verify_rejects_legacy_utf8_bom_auth` (guard test line 207-233) confirms BOM handling in the authorization path but no equivalent test exists for the preflight path.

#### P2-002: `_section()` parser silently returns empty for malformed headings

**File:** `D:\agent-acceptance\scripts\multi_agent_gate0_preflight.py`, lines 45-53

```python
def _section(text: str, heading: str) -> str:
    marker = f"## {heading}"
    start = text.find(marker)
    if start < 0:
        return ""
```

The `_section()` function performs string matching on `## {heading}` markers. If the capability inventory markdown uses a different heading style (e.g., `### 29.` or `## 29. Dev-frame-opencode dispatch` with different casing or spacing), the function silently returns `""`, causing `_validate_capability_inventory` to report "CAP-029 section missing" without distinguishing "section truly absent" from "heading format changed."

**Impact:** A documentation refactor could silently break preflight capability checks. The error message would say "CAP-029 section missing" when the section exists with a slightly different heading format.

#### P2-003: No negative test for partial tool-policy terms

**File:** `D:\agent-acceptance\tests\test_multi_agent_gate0_preflight.py`

The `_write_runtime_docs` helper (lines 34-59) always writes a complete tool policy with all 4 required terms present. No test exercises the case where 1-3 terms are present and verifies the correct "missing policy term(s)" error.

The `_validate_tool_policy` function (`multi_agent_gate0_preflight.py` lines 200-228) explicitly handles this case (line 211: `missing = [term for term in required_terms if term not in text]`), but the behavior is untested.

**Impact:** The partial-missing-terms code path in `_validate_tool_policy` is untested. While the logic appears correct, an untested branch is a maintenance risk.

#### P2-004: No scope-mismatch test for `cross_repo_verify`

**File:** `D:\agent-acceptance\tests\test_cross_repo_execution_guards.py`

There is no test verifying that `cross_repo_verify` rejects an authorization record with `scope="multi_repo_smoke"` (wrong scope). The `multi_repo_smoke` module has `test_multi_repo_smoke_rejects_unknown_repo_in_auth` (line 425-447) for repo-set mismatch, but neither module has a dedicated wrong-scope test.

The authorization module (`cross_repo_authorization.py` line 77-78) does check `data.get("scope") != required_scope`, so the code path exists but is only tested implicitly.

**Impact:** Low, because the code is correct and the authorization module itself handles this. But the gap means integration-level scope enforcement is not independently verified for `cross_repo_verify`.

#### P2-005: KNOWN_FAILURES allowance is not validated against actual failure evidence

**File:** `D:\agent-acceptance\scripts\multi_repo_smoke.py`, line 23

```python
KNOWN_FAILURES = {"devframe-control-plane": 3}
```

The hardcoded allowance count (3) is not validated against any external evidence source. While KNOWN_ISSUES correctly maps to overall FAIL (confirmed in section 2.2 above), the `known_failure_allowance` field in the output could mislead a consumer into thinking "3 failures are expected and acceptable" when the actual failure count or signatures may differ from expectations.

**Impact:** Low for fake-green risk (overall FAIL is correctly returned). Medium for evidence quality: the allowance number is a static assertion, not a verified bound.

---

## 4. Error Handling Audit

### 4.1 Robust Error Handling (Good)

| Module | Pattern | Assessment |
|---|---|---|
| `multi_agent_gate0_preflight.py` `_load_json` (line 36-42) | Catches FileNotFoundError, JSONDecodeError; returns tuple | Robust |
| `cross_repo_authorization.py` `validate_cross_repo_authorization` (lines 46-128) | Catches JSONDecodeError, validates all fields, returns structured errors | Robust |
| `cross_repo_verify.py` `_run_repo_command` (lines 60-98) | Catches TimeoutExpired, FileNotFoundError, OSError; returns structured FAIL | Robust |
| `multi_repo_smoke.py` `_run_repo_smoke` (lines 53-102) | Same pattern as cross_repo_verify | Robust |
| `validate_multi_agent_dispatch_plan.py` `_load_json` (lines 25-31) | Uses JSON_LOAD_FAILED sentinel; catches FileNotFoundError, JSONDecodeError | Robust |

### 4.2 Silent Failure or Crash Risk

| Module | Pattern | Assessment |
|---|---|---|
| `multi_agent_gate0_preflight.py` `_section()` (lines 45-53) | Returns `""` on missing heading | Silent failure (P2-002) |
| `multi_agent_dispatch_plan.py` `_load_json` (lines 52-53) | No error handling at all | Crash on missing file (P1-002) |

### 4.3 Fail-Closed Behavior Verification

All cross-repo execution paths correctly fail closed. Summary:

- **Default mode (no --execute):** Returns HUMAN_REQUIRED, exit code 2. Verified by `test_cross_repo_verify_default_is_human_required` and `test_multi_repo_smoke_default_is_human_required`.
- **--execute without authorization:** Returns HUMAN_REQUIRED, exit code 2. Verified by `test_cross_repo_verify_execute_requires_authorization` and `test_multi_repo_smoke_execute_requires_authorization`.
- **--execute with expired authorization:** Returns HUMAN_REQUIRED, exit code 2. Verified by `test_cross_repo_verify_rejects_expired_auth`.
- **--execute with legacy authorization:** Returns HUMAN_REQUIRED, exit code 2. Verified by `test_cross_repo_verify_rejects_legacy_lightweight_auth`.
- **--execute with legacy BOM authorization:** Returns HUMAN_REQUIRED, exit code 2. Verified by `test_cross_repo_verify_rejects_legacy_utf8_bom_auth`.
- **--execute with unknown repos in authorization:** Returns HUMAN_REQUIRED, exit code 2. Verified by `test_multi_repo_smoke_rejects_unknown_repo_in_auth`.
- **Authorized execution with timeout:** Returns FAIL with structured evidence including `error_type: "timeout"`. Verified by `test_cross_repo_verify_timeout_is_structured_fail` and `test_multi_repo_smoke_timeout_is_structured_fail`.
- **Authorized execution with missing cwd:** Returns FAIL with structured evidence including `error_type: "missing_cwd"`. Verified by `test_cross_repo_verify_missing_cwd_is_structured_fail` and `test_multi_repo_smoke_missing_cwd_is_structured_fail`.
- **Authorized execution with OSError:** Returns FAIL with structured evidence including `error_type: "execution_exception"`. Verified by `test_cross_repo_verify_execution_exception_is_structured_fail` and `test_multi_repo_smoke_execution_exception_is_structured_fail`.

**Assessment: Fail-closed behavior is comprehensive and well-tested. All 9 distinct failure modes have dedicated test coverage.**

---

## 5. Security Review

### 5.1 Secret Leak Risk

- **No secrets in code.** All scripts use configuration files and JSON records. No API keys, tokens, or credentials are hardcoded.
- **Authorization records** (`cross_repo_authorization.py`) are JSON files with audit fields but no secrets. The `decision_maker` field is a human-readable string, not a credential.
- **TaskSpec security_report** is hardcoded to safe defaults (P1-001 above). No real scan data is embedded.

### 5.2 Path Traversal

- **`multi_agent_gate0_preflight.py` line 301:** `output_path.parent.mkdir(parents=True, exist_ok=True)` will create any directory hierarchy specified by `--output`. This is an operator-controlled CLI argument, so the risk is limited to operator error or malicious invocation with an untrusted path.
- **`multi_agent_dispatch_plan.py` line 507:** Same pattern for `--output` argument.
- **`cross_repo_authorization.py` line 61:** `Path(record_path)` trusts the caller-supplied path. However, the function only reads the file and validates its JSON contents, so the risk is limited to information disclosure (reading arbitrary JSON files and reporting their structure via error messages).

### 5.3 Authorization Integrity

- The authorization record (`cross_repo_authorization.py`) uses no cryptographic signatures. It relies on JSON file integrity and human review. This is an acknowledged design choice (the record is "auditable" not "tamper-proof").
- The `risk_acknowledged: true` field (line 79) is a second boolean gate beyond `authorized: true`, providing defense against accidental authorization.
- The exact-match repo set validation (lines 94-106) prevents scope creep: both missing and extra repos are rejected.
- Timestamp validation (lines 24-43, 108-126) requires timezone-aware ISO timestamps and checks that `expires_at > approved_at` and that the record is not expired at evaluation time.

---

## 6. Test Coverage Quality

### 6.1 `test_multi_agent_gate0_preflight.py` (7 tests)

| Test | What It Verifies | Fake-Green Risk |
|---|---|---|
| `test_current_repo_preflight_passes_pilot_ready` (line 71) | Live repo state produces PASS | Low: depends on real state, but assertions are specific (exit_code==0, overall==PASS, executed_external_runtime==False) |
| `test_cli_output_writes_same_schema_valid_report` (line 81) | CLI --output matches stdout, schema-valid | Low: verifies file/stdout consistency |
| `test_two_active_bindings_with_approved_capability_pass` (line 106) | Synthetic happy path | None: fully synthetic, meaningful assertions |
| `test_proposed_opencode_capability_requires_human_gate` (line 133) | CAP-029 proposed = HUMAN_REQUIRED | None: verifies blocking behavior |
| `test_duplicate_agent_ids_block` (line 159) | Duplicate agent_id = BLOCKED | None: verifies blocking behavior |
| `test_missing_binding_blocks` (line 185) | Missing file = BLOCKED | None: verifies blocking behavior |
| `test_schema_rejects_external_runtime_execution_flag` (line 201) | Schema enforces const false | None: schema-level constraint |
| `test_schema_rejects_human_required_without_gate_flag` (line 224) | Schema enforces conditional consistency | None: schema-level constraint |

**Gaps:** No test for partial tool-policy terms. No test for malformed capability inventory headings. No test for binding JSON with BOM encoding on the preflight path.

### 6.2 `test_cross_repo_execution_guards.py` (18 tests)

| Category | Tests | Fake-Green Risk |
|---|---|---|
| Default/dry-run HUMAN_REQUIRED | 2 (verify + smoke) | None: monkeypatched subprocess with `pytest.fail` ensures no execution |
| Missing authorization | 2 (verify + smoke) | None: verifies fail-closed |
| Authorized execution happy path | 2 (verify + smoke) | None: verifies call count matches repo count |
| Known issues do not fake-green | 1 (smoke only) | None: critical test, asserts overall FAIL and exit 1 |
| Timeout handling | 2 (verify + smoke) | None: structured FAIL evidence verified |
| Missing cwd handling | 2 (verify + smoke) | None: structured FAIL evidence verified |
| OSError handling | 2 (verify + smoke) | None: structured FAIL evidence verified |
| Legacy auth rejection | 2 (plain + BOM) | None: verifies audit field requirement |
| Expired auth rejection | 1 (verify only) | None: verifies expiry check |
| Unknown repo rejection | 1 (smoke only) | None: verifies exact scope match |

**Gaps:** No wrong-scope test for either module. No test for `authorized=false` with otherwise valid record. Authorization expiry boundary not tested at the exact edge (only clearly-expired dates).

---

## 7. Residual Risks

### RR-001: Live-State Test Fragility

`test_current_repo_preflight_passes_pilot_ready` (line 71) and `test_cli_output_writes_same_schema_valid_report` (line 81) run against the actual repository state. If the pilot configuration changes (e.g., a binding is retired, a capability is re-proposed), these tests will fail for reasons unrelated to code correctness. This is acceptable for current-state verification but should not be the sole test of PASS-path behavior. The synthetic test `test_two_active_bindings_with_approved_capability_pass` provides independent coverage.

### RR-002: Authorization Record is Not Tamper-Proof

The authorization record in `cross_repo_authorization.py` is a plain JSON file with no integrity protection (no signature, no hash chain). Any process with write access to the file can create or modify an authorization record. The design mitigates this through auditability (decision_maker, decision_reason, approved_at, expires_at) and human review, but it is not cryptographically tamper-resistant. This is an acknowledged design choice for the pilot phase.

### RR-003: Hardcoded Paths in Cross-Repo Scripts

`cross_repo_verify.py` (lines 19-31) and `multi_repo_smoke.py` (lines 20-22) hardcode absolute Windows paths like `"D:/agent-acceptance"`. The scripts are non-portable and cannot be tested in CI or on machines without the exact directory layout. Tests work around this by monkeypatching `subprocess.run`, but actual authorized execution requires the exact paths. This is an operational fragility, not a security risk.

---

## 8. Summary

### Strengths

1. **Fail-closed by default.** Every execution path defaults to HUMAN_REQUIRED. No silent execution can occur without explicit authorization.
2. **Schema-enforced invariants.** The preflight schema uses `const` and conditional constraints to prevent contradictory reports (e.g., PASS with human_gate_required=true, or any report claiming executed_external_runtime=true).
3. **Comprehensive error handling in execution paths.** Timeout, missing directory, and OS errors are all caught and converted to structured FAIL evidence with typed `error_type` fields.
4. **Strong test discipline.** Tests use `pytest.fail` on `subprocess.run` to verify that unauthorized paths never execute. The known-issues fake-green test correctly confirms KNOWN_ISSUES maps to overall FAIL.
5. **Authorization audit trail.** Required audit fields (decision_maker, decision_reason, approved_at, expires_at, risk_acknowledged) make authorization records reviewable. Exact scope and repo-set matching prevents scope creep.
6. **Write-conflict detection.** The dispatch plan builder checks for overlapping write sets between parallel-safe tasks in the same group, and the validator verifies these checks.
7. **KNOWN_ISSUES correctly handled.** Despite a previous review flagging this as P1, re-inspection confirms that KNOWN_ISSUES status is not "PASS" and therefore correctly produces overall FAIL.

### Weaknesses

1. **Hardcoded security reports** look like scan evidence but are static defaults (P1-001).
2. **Dispatch plan JSON loader** crashes on missing files instead of returning structured errors (P1-002).
3. **Encoding inconsistency** between modules could cause BOM-related parse issues on Windows (P2-001).
4. **Static Gate 0 evidence** in the plan builder is indistinguishable from runtime-computed evidence (P2 in section 2.4).
5. **Test gaps** exist for partial tool-policy terms, wrong-scope authorization, and BOM-encoded binding files on the preflight path.

### Verdict: PARTIAL

The codebase demonstrates strong safety fundamentals: fail-closed defaults, schema-enforced invariants, and well-designed guard tests. The two P1 findings (hardcoded security reports and unhandled file errors) do not create fake-green risk but do reduce evidence quality and operational robustness. The P2 findings are maintenance and portability concerns that do not block current use but should be addressed before the pilot moves beyond local readiness.

**No P0 blocking findings. The system is safe for human-gated operation.** The PARTIAL verdict reflects evidence quality gaps, not safety failures.

---

## 9. Changed Files

- `D:\agent-acceptance\_reports\multi-agent-quality-review-a1\QUALITY_REVIEW.md` (this report)

No scripts, tests, schemas, docs, or .agent files were modified.

## 10. Tests Run

- Read-only code inspection only. No pytest, cross-repo execution, opencode, live CDP, or paper workflow was executed, per task instructions.

## 11. Governance Notes

- No git operations performed.
- No forbidden paths modified.
- No external runtime executed.
- `executed_external_runtime: false` throughout.
