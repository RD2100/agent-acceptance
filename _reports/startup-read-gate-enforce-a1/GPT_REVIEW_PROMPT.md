# GPT Review Prompt — STARTUP-READ-GATE-ENFORCE-A1

**task_id**: `STARTUP-READ-GATE-ENFORCE-A1`
**run_id**: `{{RUN_ID}}`
**generated_at**: `{{TIMESTAMP}}`

---

You are reviewing the deliverables for task `STARTUP-READ-GATE-ENFORCE-A1` (authorized by VERIFY-GPT-REPLY-STRUCTURED-PARSE-HARDEN-A1 R1 review, hardening plan §5.7).

## Task Objective

Implement a startup read gate enforcement script (`scripts/startup_read_gate.py`) that verifies an agent has completed all required reads before starting work. The script should check proof file existence, required reads coverage, SHA-256 hash verification, gate status, and P0 critical reads.

## Expected Deliverables

1. `scripts/startup_read_gate.py` — Startup read gate enforcement script
2. `tests/test_startup_read_gate.py` — 12 regression test cases
3. `EXECUTION_REPORT.md` — Execution report with test output

## Review Criteria

Please evaluate:

1. **Completeness**: Does the gate check all 5 items specified in §5.7.2?
2. **Fail-closed behavior**: Does the gate default to BLOCKED on any error?
3. **Hash verification**: Does SHA-256 checking work correctly with `sha256:` prefix handling?
4. **P0 enforcement**: Are P0-level reads treated as critical (separate error)?
5. **Coverage computation**: Is the coverage ratio calculated correctly?
6. **Test quality**: Are tests comprehensive (pass, fail, edge cases)?
7. **CLI interface**: Is the CLI clean and following project conventions?

## Evidence Pack Manifest

{{PACK_MANIFEST}}

## Response Format

Please respond with:
1. `overall_judgment`: accepted | accepted_with_limitation | blocked | human_required
2. `evidence_pack_reviewed: true`
3. `attachment_reviewed: true`
4. `blocking_issues`: list or "none"
5. `required_fixes`: list or "none"
6. `limitations`: list (if any)
7. `next_task_authorization`: { task_id, authorized, execute_immediately, ask_before_starting }

run_id: {{RUN_ID}}
task_id: STARTUP-READ-GATE-ENFORCE-A1

END_OF_GPT_RESPONSE
