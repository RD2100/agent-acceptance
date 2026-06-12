## Hook Failure Semantics

This document formally defines the failure propagation rules for `pre-commit.governance.ps1` (v2.4.0).
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
| conversation-health | No | Advisory only | A3 Layer 4: reads conversation-health evidence, never blocks commit |

### Governance Decision: Test-Governance Advisory Mode

**Decision**: Test-Governance is advisory (non-blocking) in v2.3.0.

**Rationale**: `Test-Governance.ps1` is invoked with `-Mode advisory`, which means it runs
advisory checks (e.g., stale task detection, protected path coverage) that are informational
rather than enforcement. Its exit code reflects advisory findings, not governance violations.
Making it blocking would require modifying `Test-Governance.ps1` to distinguish advisory from
enforcement failures — this is outside the scope of the current hook failure semantics task.

**Trade-off**: This means a Test-Governance failure (e.g., stale tasks detected) will NOT
reject the commit. The failure is still logged in `_evidence/hook-output/test-governance-*.txt`
and `latest.json` for post-commit review.

**Future path**: If Test-Governance should become a blocking gate, a separate
`HUMAN_REQUIRED` task must be opened to modify `Test-Governance.ps1` to support
enforcement mode, and the hook must be updated accordingly.

**Approved by**: Task EVIDENCE-CAPTURE-HOOK-FAILURE-RUNTIME-VALIDATION-A1 scope constraint
(no modification to Test-Governance.ps1 without separate human_required task).

### Governance Decision: Conversation-Health Advisory Mode (A3)

**Decision**: Conversation-health is advisory (non-blocking) in v2.4.0.

**Rationale**: This is Layer 4 of the four-layer conversation health defense
(conversation-health-gate.md §1.4). The primary enforcement points are Layer 1
(pre-task hard gate), Layer 2 (pre-GPT gate), and Layer 3 (evidence pack requirement).
The pre-commit advisory layer provides an additional signal at commit time but is not
the primary enforcement mechanism. Making it blocking would duplicate enforcement
already covered by Layers 1–3 and would introduce friction for routine commits.

**Behavior**: `scripts/pre_commit_health_advisory.py` reads existing conversation-health
evidence (`latest.json` or `current.json`) and runs the decision engine in advisory mode.
It outputs a diagnostic summary (decision, severity, recommendation) but never blocks.
Fail-graceful: any internal error results in exit 0 with a diagnostic message.

**Approved by**: Task CONVERSATION-HEALTH-GATE-A3 scope definition.

### Result Mapping

```
overall_result  = BLOCKED    if sadp-audit or ai-guard has exit_code ≠ 0
                = PASS       otherwise
```

The hook process exit code follows a simple rule: `exit 1` when any required stage fails.
All required stages must fail closed — no silent pass on failure.

### Decision Tree

```
Start
  |
  v
[manifest-regen] -- always runs, advisory. Log exit_code, continue.
  |
  v
[sadp-audit] -- BLOCKING. If exit_code != 0:
  |                -> Write latest.json with 3 stages (manifest, sadp, ai-guard)
  |                -> overall_result = BLOCKED
  |                -> exit 1 (EARLY EXIT: stages 4-5 never run)
  |              If exit_code == 0: continue.
  v
[ai-guard] -- BLOCKING. Invoked as: python tools/ai_guard.py --files <staged_files>
  |            If exit_code != 0 (including timeout):
  |                -> overall_result = BLOCKED
  |                -> continue to stages 4-5 (advisory stages still run for logging)
  |              If exit_code == 0: continue.
  v
[test-governance] -- ADVISORY. Runs with -Mode advisory. Log exit_code, continue.
  |
  v
[conversation-health] -- ADVISORY (A3 Layer 4). Fail-graceful. Log exit_code, continue.
  |
  v
Compute overall_result:
  If sadp-audit.exit_code != 0 OR ai-guard.exit_code != 0:
    overall_result = BLOCKED, exit 1
  Else:
    overall_result = PASS, exit 0
```

Note: sadp-audit early-exit is the only path where latest.json has fewer than 5 stages.
In all other cases (including ai-guard failure), all 5 stages run and appear in latest.json.

### ai-guard Invocation: --files Flag

Since v2.4.0, the hook invokes ai_guard.py with explicit file scoping:

```powershell
$stagedFiles = git diff --cached --name-only 2>$null
python tools/ai_guard.py --files $stagedFiles
```

The `--files` mode (added in AI-GUARD-FILES-MODE-AND-LARGE-FILE-SCAN-A1) ensures ai_guard
scans only the staged files, not the entire working tree. This mode runs `deny_paths`,
`restricted_paths`, and `secret_patterns` checks on the listed files. It does NOT check
TaskSpec `allow_write` scope (scope enforcement is handled by sadp-audit).

### Missing Script Fallback Behavior

When a required script is not found, the hook degrades gracefully:

| Missing Script | Behavior | Exit Code | Impact on overall_result |
|---|---|---|---|
| `Update-GovernanceManifest.ps1` | Logs warning, continues | 0 | Advisory — no impact |
| `sadp-audit.ps1` | Logs warning, skips audit, ai-guard also skipped | 0 | No blocking gate runs — PASS if ai-guard also skipped |
| `tools/ai_guard.py` | Logs info, skips AI guard | 0 | No blocking gate runs — PASS if sadp-audit also passes |
| `Test-Governance.ps1` | Logs warning, skips governance scan | 0 | Advisory — no impact |
| `pre_commit_health_advisory.py` | Logs advisory skip message | 0 | Advisory — no impact |

**Important**: If both `sadp-audit.ps1` and `ai_guard.py` are missing, no blocking gate runs
and the hook passes all commits unconditionally. This is by design — the hook is a governance
tool, not a security boundary. The absence of governance scripts indicates the project has not
been bootstrapped with SADP governance.

### Early-Exit Path

When `sadp-audit` fails, the hook takes an early-exit path (line ~161 in the script):

1. Writes `latest.json` with 3 stages (manifest-regen, sadp-audit, ai-guard) — test-governance and conversation-health are omitted because they never ran.
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

### Null Exit Code Semantics (Fail-Closed)

The schema allows `exit_code` to be `integer` or `null`. A `null` exit code means the
process exit code was unavailable (e.g., `Start-Job` did not complete normally).

Fail-closed rules:
- **Blocking stage** with `exit_code = null` → treated as failure (BLOCKED expected)
- **Advisory stage** with `exit_code = null` → logged but not blocking
- The hook defaults `null` to `1` internally, ensuring unavailable = blocked for blocking stages
- The validator rejects `null` exit codes on blocking stages unless `overall_result = BLOCKED`

### Schema Conformance

`latest.json` MUST validate against `schemas/agent-runtime/evidence-capture.schema.json`.
The schema defines:

- `stages`: array of 1–5 items (enum: manifest-regen, sadp-audit, ai-guard, test-governance, conversation-health)
- `overall_result`: enum of PASS, BLOCKED
- `hook_version`: semver pattern

**output_file path note**: The schema describes `output_file` as a relative path, but the
current hook implementation (v2.4.0) writes absolute paths (e.g., `D:\agent-acceptance\_evidence\hook-output\sadp-audit-*.txt`). This is a known deviation from the schema description
but does not affect validation — the schema type is `string` or `null`, not a format-constrained
path. Consumers should handle both absolute and relative paths. A future schema revision
should clarify this.

**BOM note**: `latest.json` is written by PowerShell's `ConvertTo-Json | Out-File -Encoding utf8`,
which produces UTF-8 with BOM. Consumers should read with `utf-8-sig` encoding to handle the BOM.

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
6. **Do not** invoke ai_guard.py without the `--files` flag — bare mode falls through to full git-diff scan, which may scan unintended files or miss staged-only changes.
7. **Do not** assume `output_file` paths are relative — current implementation writes absolute paths.

### Version History

| Hook Version | Change |
|---|---|
| 2.0.0 | Initial 3-stage hook (manifest, sadp-audit, test-governance) |
| 2.1.0 | Added ai-guard as separate capture + output persistence |
| 2.2.0 | PASS_WITH_WARNINGS for ai-guard (non-blocking), 30s timeout, schema alignment |
| 2.3.0 | sadp-audit + ai-guard blocking (reliable exit code). test-governance advisory. Removed PASS_WITH_WARNINGS. |
| 2.4.0 | Added conversation-health advisory stage (A3 Layer 4). Never blocks commit. Reads existing evidence. |
