# Hook Governance Upgrade -- Reviewer Decision

> Date: 2026-05-28
> Gate Authority: RD2100
> Decision: **pass_to_review**

## TaskSpec

Activate `pre-edit.audit.draft.ps1` as the first governance hook in the RD2100 Agent Runtime. This hook blocks Write/Edit tool calls that target memory directories, sealed governance files, or secret patterns (`.env`, `.key`, `.pem`, `token`, `credential`, `id_rsa`, `id_ed25519`). All other 4 hooks remain audit-only drafts. No MCP enabled. No memory written. No skill executed.

## Scope

| Asset | Action | Status |
|-------|--------|:---:|
| `hooks/pre-edit.governance.ps1` | Activated from draft (renamed `*.audit.draft.ps1` ¡ú `*.governance.ps1` to resolve naming contradiction) | Active |
| `hooks/sealed-files-manifest.json` | Created: 22 sealed files + 3 sealed dirs + memory paths | Done |
| `hooks/register-hooks.ps1` | Created: registration script with auto-create + backup | Done |
| `hooks/registration-config.json` | Created: manual merge config snippet | Done |
| `~/.claude/settings.json` | Registered PreToolUse(Write|Edit) hook | Done |
| Other 4 hooks | Unchanged: audit-only draft, not registered, exit 0 always | Unchanged |

## Promotion Path (Human-Gated)

```
draft ¡ú reviewed ¡ú candidate ¡ú reviewer_gate ¡ú active (2026-05-28)
         ¡ü                                        ¡ü
    pre-edit reviewed for:                   RD2100 signed
    - no network calls
    - no file mutation
    - no secret access
    - exit 1 only on P0 hard violations
```

No capability_promotion_record was filed (human reviewer authority overrides gate chain).

## Boundary Declaration

- Active: 1 hook (pre-edit.governance.ps1)
- Draft: 4 hooks (pre-task, pre-tool, pre-final, skill-intake-scan)
- No further hook registration without new human gate
- `sealed-files-manifest.json` modifications require human approval
- `register-hooks.ps1` execution requires human approval (not auto-triggered)

## Commits

```
3cb6ea7 fix: register-hooks.ps1 auto-creates settings.json when missing
4c82458 fix: hook registration, manifest dedup, header sync
32fe7a9 feat: add hook registration script
b22edc3 feat: upgrade pre-edit hook to active blocking mode
```

## Post-Upgrade Doc Sync (Codex Agent, 2026-05-28)

9 governance documents updated to reflect pre-edit active status (was "all hooks audit-only draft"). File renamed from `pre-edit.audit.draft.ps1` ¡ú `pre-edit.governance.ps1`. All stale `NOT registered, NOT blocking` claims removed.

## Known Gaps

| Gap | Severity | Mitigation |
|-----|----------|------------|
| `settings.json` may be reset on Claude Code restart | low | `register-hooks.ps1` auto-creates if missing |
| Diagnostic logging writes to `$env:TEMP` | low | Temporary; remove when hook behavior confirmed stable |
| `sealed-files-manifest.json` not version-controlled separately from hook logic | low | Manifest is source of truth for sealed list; hook has hardcoded fallback of 7 core files |

## Next Agent Notes

- `pre-edit.governance.ps1` is ACTIVE. Do not disable without human gate.
- `register-hooks.ps1` is a governance script. Do not run without human gate.
- Other 4 hooks (`pre-task`, `pre-tool`, `pre-final`, `skill-intake-scan`) are AUDIT-ONLY DRAFT.
- Do not register additional hooks without a new TaskSpec + human gate.
- Do not modify `sealed-files-manifest.json` without human approval.

## Reviewer Signature

```
Gate Authority: RD2100
Decision: pass_to_review
Date: 2026-05-28
```