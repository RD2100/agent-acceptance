# Production Readiness

This document defines the authoritative readiness states for agent-acceptance.
Narrative reports, historical scores, and static conversation bindings do not
promote a runtime by themselves.

## Modes

| Mode | Meaning | Required evidence |
|------|---------|-------------------|
| `local_governance` | The repository can safely run local governance and validation workflows. | Current canonical test result plus real task-runner allow/block/finish probes. |
| `controlled_pilot` | A bounded multi-agent pilot may be dispatched. | Local readiness, current Gate 0 `PASS`, and dispatch plan `READY`. |
| `formal_use` | The multi-agent/multi-GPT workflow may be promoted for normal use. | Controlled-pilot readiness, a current real two-session pilot with independent review, and explicit production-promotion authorization. |

The machine authority is `scripts/production_readiness_gate.py`:

```powershell
python scripts\production_readiness_gate.py `
  --mode formal_use `
  --local-evidence _reports\production-readiness-automation-a1\LOCAL_VERIFICATION.json `
  --preflight _reports\multi-agent-gate0-preflight-a1\PREFLIGHT_CURRENT.json `
  --dispatch-plan _reports\multi-agent-dispatch-plan-a1\DISPATCH_PLAN_CURRENT.json `
  --pilot-evidence _reports\real-multi-gpt-pilot-a1\PILOT_EXECUTION.json `
  --production-authorization _reports\production-promotion-a1\AUTHORIZATION.json
```

Exit codes:

- `0`: `READY`
- `1`: `BLOCKED`
- `2`: `HUMAN_REQUIRED`

## Evidence Rules

- Evidence paths must remain inside the repository.
- Local verification and pilot evidence must be no older than 24 hours.
- Canonical tests use exactly `python -m pytest tests/ -q` and require zero failures.
- Runner probes must bind to this task ID and preserve the exact runner command,
  target file, exit code, and decisive output markers. Synthetic status-only JSON
  is insufficient.
- Gate 0 and dispatch artifacts require current `generated_at` timestamps;
  missing, stale, future, or malformed timestamps block readiness.
- A READY dispatch plan must bind its nested `source_preflight` to the same
  current Gate 0 artifact by resolved path, SHA256, generated_at, and status
  fields. A copied or repo-escaping nested source is invalid.
- Gate 0 and dispatch artifacts must remain read-only and must not claim external execution.
- A real pilot needs at least two distinct session IDs and an independent reviewer identity different from executor identities.
- Pilot evidence must bind to the exact Gate 0 and dispatch artifacts by SHA256.
- Each pilot session must reference matching live-session JSON with current
  `verified_at` proof; missing, stale, future, malformed, or mismatched session
  timestamps block formal use.
- Review evidence must include existing Markdown and YAML artifacts.
- Formal promotion authorization must be current, scoped to `formal_use`, tied to the pilot run ID, and include explicit risk acknowledgement.
- Formal promotion must be approved after the referenced pilot completes.

## Current Boundary

The repository can reach `local_governance: READY` using only local checks.
`controlled_pilot` and `formal_use` remain human-gated until current run-bound
authorization and real independent session evidence exist. Static bindings are
discovery metadata, not authorization.

The paper workflow remains paused and is not part of this promotion path.
`devframe-control-plane` and `dev-frame-opencode` remain governed external
runtimes; their execution requires a separate exact-command authorization.

## Tracked Protected-Document Debt

The capability inventory skips CAP-009, and the cumulative-trigger section has
advisory/mandatory wording tension. Both files are protected by the SADP
exclusive-lock rule. This batch records the debt but does not bypass that lock.
Neither item is used as positive evidence by the readiness gate.
