# Governance Manifest ¡ª RD2100 Agent Runtime v2

> Generated: 2026-05-28 | Source: RD2100 Agent Runtime v2 | This manifest locks protected governance sections.

## Protected Sections (Hash-Verified)

| Section ID | File | Hash (SHA256) |
|------------|------|---------------|
| P0_RULES | `rules/core.md` | 69EA63CB45524624AB38C06253A1120756ED823D4E652254362AB425F00DBCCC |
| AGENTS_HARD_STOPS | `AGENTS.md` | 5FAB1CA89A425F7A793795265E3810E67EE60A3563104DD96B28B151472A4C8F |

## Protected Content Summary

### P0_RULES (rules/core.md)
- core-001: No Destructive Git Without Approval
- core-002: No Secret Exposure
- core-003: Phase Boundary Enforcement
- core-007: No Capability Without Inventory Registration
- core-008: Resource Sufficiency + Execute Agent Veto Contract
- Knowledge Metabolism Rule (P0 cap = 7)

### AGENTS_HARD_STOPS (AGENTS.md)
- 6 Hard Stops, Phase 0-5 Boundary, Protected files list
- SADP auto-trigger rules, Reuse-before-Build Rule

## Drift Detection

On every session start: compare protected section hashes against this manifest.
Any mismatch -> escalate to human reviewer.

```yaml
check_on_session_start:
  - compare: rules/core.md hash vs manifest
    on_mismatch: escalate_to_human
  - compare: AGENTS.md protected sections hash vs manifest
    on_mismatch: escalate_to_human
```

## Integrity Check Command

```powershell
Get-FileHash rules/core.md, AGENTS.md -Algorithm SHA256 | ForEach-Object { "$($_.Hash)  $([System.IO.Path]::GetFileName($_.Path))" }
```

> This project IS the canonical source. is_canonical: true. No local overrides needed.
