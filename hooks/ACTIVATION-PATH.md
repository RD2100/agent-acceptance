# Draft Hooks — Activation Path

> Status: 4 audit-only draft hooks exist but are not registered.
> Registration requires human gate per Phase 0-5.

## Current Draft Hooks

| Hook | Purpose | Exit Code | Ready for Registration |
|------|---------|:---:|:---:|
| `pre-final.audit.draft.ps1` | Session-end SADP compliance check | 0 (audit-only) | Yes — complements sadp-audit.ps1 |
| `pre-task.audit.draft.ps1` | Pre-task scope validation | 0 (audit-only) | Yes — validates TaskSpec before execution |
| `pre-tool.audit.draft.ps1` | Pre-tool-call risk check | 0 (audit-only) | Partial — needs risk matrix update |
| `skill-intake-scan.audit.draft.ps1` | External skill intake validation | 0 (audit-only) | Partial — needs allowlist sync |

## Activation Steps

1. **Human reviewer** reviews each draft hook for correctness
2. **Human reviewer** runs: `powershell -ExecutionPolicy Bypass -File hooks/register-hooks.ps1`
3. Hook transitions from `audit.draft` → `governance` (exit 0 → exit 0 or 1)
4. Update `hooks/sealed-files-manifest.json` if hook touches sealed files

## Priority

1. `pre-final.audit.draft.ps1` — highest value, closes session-end audit gap
2. `pre-task.audit.draft.ps1` — validates TaskSpec before execution
3. `pre-tool.audit.draft.ps1` — tool-level safety net
4. `skill-intake-scan.audit.draft.ps1` — external skill safety

## Blockers
- Phase 0-5: hook registration requires human gate
- No automated hook testing framework
