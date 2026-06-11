## Hook Failure Semantics

This document formally defines the failure propagation rules for `pre-commit.governance.ps1` (v2.2.0).
Every commit that passes through the SADP pre-commit hook produces `_evidence/hook-output/latest.json`.
The semantics below govern how each stage's exit code maps to the `overall_result` field and the hook's
process exit code.

### Stage Classification

| Stage | Blocking? | Failure Effect | Rationale |
|---|---|---|---|
| manifest-regen | No | Advisory only | Manifest drift is logged but does not indicate a governance violation |
| sadp-audit | **Yes** | `BLOCKED` + exit 1 | Sole enforcement gate; validates sealed-file integrity and rule compliance |
| ai-guard | No | `PASS_WITH_WARNINGS` | Content policy scan; failures logged for review but do not block commits |
| test-governance | No | Advisory only | Advisory scan (e.g., stale task check); never affects commit decision |

### Result Mapping

```
overall_result  = BLOCKED              if sadp-audit.exit_code ≠ 0
                = PASS_WITH_WARNINGS   if ai-guard.exit_code ≠ 0 AND sadp-audit.exit_code = 0
                = PASS                 otherwise
```

The hook process exit code follows a simple rule: `exit 1` only when `sadp-audit` fails.
All other stage failures produce `exit 0` with appropriate warnings in console output and `latest.json`.

### Early-Exit Path

When `sadp-audit` fails, the hook takes an early-exit path (line ~129 in the script):

1. Writes `latest.json` with 3 stages (manifest-regen, sadp-audit, ai-guard) — test-governance is omitted because it never ran.
2. Sets `overall_result = "BLOCKED"`.
3. Prints `[BLOCKED]` to console.
4. Calls `exit 1`, which rejects the commit.

### Timeout Behavior

`ai_guard.py` runs inside a PowerShell background job with a 30-second timeout. If the timeout expires:

1. The job is stopped and removed.
2. `ai-guard.exit_code` is set to `1` in `latest.json`.
3. `overall_result` becomes `PASS_WITH_WARNINGS` (not `BLOCKED`).
4. The commit is allowed to proceed.

This design prevents a hung AI guard process from blocking all commits indefinitely.

### Schema Conformance

`latest.json` MUST validate against `schemas/agent-runtime/evidence-capture.schema.json`.
The schema defines:

- `stages`: array of 1–4 items (enum: manifest-regen, sadp-audit, ai-guard, test-governance)
- `overall_result`: enum of PASS, PASS_WITH_WARNINGS, BLOCKED
- `hook_version`: semver pattern

### Anti-Patterns (DO NOT)

1. **Do not** make ai-guard blocking without explicit policy decision and version bump.
2. **Do not** set `overall_result = "BLOCKED"` when the hook exits 0 — this creates a contradiction.
3. **Do not** remove timeout protection from ai-guard; indefinite hangs are worse than skipped checks.
4. **Do not** add new blocking stages without updating the early-exit path and this document.

### Version History

| Hook Version | Change |
|---|---|
| 2.0.0 | Initial 3-stage hook (manifest, sadp-audit, test-governance) |
| 2.1.0 | Added ai-guard as separate capture + output persistence |
| 2.2.0 | Fixed failure semantics: PASS_WITH_WARNINGS for ai-guard, 30s timeout, schema alignment |
