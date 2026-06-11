## Hook Failure Semantics

This document formally defines the failure propagation rules for `pre-commit.governance.ps1` (v2.3.0).
Every commit that passes through the SADP pre-commit hook produces `_evidence/hook-output/latest.json`.
The semantics below govern how each stage's exit code maps to the `overall_result` field and the hook's
process exit code.

### Stage Classification

| Stage | Blocking? | Failure Effect | Rationale |
|---|---|---|---|
| manifest-regen | No | Advisory only | Manifest drift is logged but does not indicate a governance violation |
| sadp-audit | **Yes** | `BLOCKED` + exit 1 | Validates sealed-file integrity and rule compliance |
| ai-guard | **Yes** | `BLOCKED` + exit 1 | Content policy scan; uses reliable Job.ChildJobs exit code |
| test-governance | No | Advisory only | Runs in `-Mode advisory`; exit code logged but does not block |

### Result Mapping

```
overall_result  = BLOCKED    if sadp-audit or ai-guard has exit_code ≠ 0
                = PASS       otherwise
```

The hook process exit code follows a simple rule: `exit 1` when any required stage fails.
All required stages must fail closed — no silent pass on failure.

### Early-Exit Path

When `sadp-audit` fails, the hook takes an early-exit path (line ~161 in the script):

1. Writes `latest.json` with 3 stages (manifest-regen, sadp-audit, ai-guard) — test-governance is omitted because it never ran.
2. Sets `overall_result = "BLOCKED"`.
3. Prints `[BLOCKED]` to console.
4. Calls `exit 1`, which rejects the commit.

For `ai-guard` and `test-governance` failures, the hook completes all stages before computing `overall_result` and exiting.

### Timeout Behavior

`ai_guard.py` runs inside a PowerShell background job with a 30-second timeout. If the timeout expires:

1. The job is stopped and removed.
2. `ai-guard.exit_code` is set to `1` in `latest.json`.
3. `overall_result` becomes `BLOCKED`.
4. The commit is rejected (exit 1).

This ensures a hung AI guard process does not silently pass commits.

### Schema Conformance

`latest.json` MUST validate against `schemas/agent-runtime/evidence-capture.schema.json`.
The schema defines:

- `stages`: array of 1–4 items (enum: manifest-regen, sadp-audit, ai-guard, test-governance)
- `overall_result`: enum of PASS, BLOCKED
- `hook_version`: semver pattern

### Output Validation

`scripts/validate_hook_output.py` validates `latest.json` against the schema:

```bash
python scripts/validate_hook_output.py \
    --file _evidence/hook-output/latest.json \
    --schema schemas/agent-runtime/evidence-capture.schema.json
```

It checks required fields, stage enum values, exit code types, and overall_result enum membership.
It also performs semantic checks (e.g., verifying that nonzero blocking-stage exit codes correspond to BLOCKED).

### Anti-Patterns (DO NOT)

1. **Do not** make any required stage non-blocking without explicit policy decision and version bump.
2. **Do not** set `overall_result = "BLOCKED"` when the hook exits 0 — this creates a contradiction.
3. **Do not** remove timeout protection from ai-guard; indefinite hangs are worse than blocked commits.
4. **Do not** add new stages without updating this document and the schema.
5. **Do not** represent replay-style evidence as raw console output.

### Version History

| Hook Version | Change |
|---|---|
| 2.0.0 | Initial 3-stage hook (manifest, sadp-audit, test-governance) |
| 2.1.0 | Added ai-guard as separate capture + output persistence |
| 2.2.0 | PASS_WITH_WARNINGS for ai-guard (non-blocking), 30s timeout, schema alignment |
| 2.3.0 | sadp-audit + ai-guard blocking (reliable exit code). test-governance advisory. Removed PASS_WITH_WARNINGS. |
