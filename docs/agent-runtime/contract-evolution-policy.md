# Contract Evolution Policy — RD2100 Agent Runtime v2

> Phase 3 | 2026-05-30
> Governs how the 8 core contracts evolve without breaking consumers.

## Version Format

All contracts use MAJOR.MINOR.PATCH:
- **MAJOR**: Breaking changes (field removal, semantic change, new required field)
- **MINOR**: Backward-compatible additions (new optional field, new enum value*)
- **PATCH**: Clarifications, doc fixes, no schema change

*New enum values are treated as MINOR but require compatibility check.

## Rules

### Within Same MAJOR Version: Add-Only

| Action | Allowed | Version Bump |
|--------|:-------:|:------------:|
| Add optional field | Yes | MINOR |
| Add new enum value | Yes* | MINOR |
| Clarify description | Yes | PATCH |
| Remove field | **No** | — |
| Change optional to required | **No** | — |
| Change field semantics | **No** | — |
| Change enum value meaning | **No** | — |
| Remove enum value | **No** | — |

*New enum values require compatibility check: all consumers must handle unknown enum values gracefully.

### Breaking Changes: Parallel Versions

When a breaking change is needed:

`	ext
1. Create vN+1 schema (e.g., TaskSpec v2.0.0)
2. Keep vN schema stable and supported
3. Both versions coexist during migration
4. Consumers declare accepted versions in their manifest
5. Migration window: minimum 2 phases
6. After migration: vN enters deprecation (still accepted, warning emitted)
7. After deprecation window: vN archived (rejected at Gate 0)
`

### Migration Lifecycle

`	ext
stable (v1) ────────────────┐
                             ├── migration window (2+ phases)
next (v2) ──────────────────┘
         │
         v
stable (v2) + deprecated (v1) ── deprecation window
         │
         v
stable (v2) only ── v1 archived
`

## Cross-Project Boundary: Consumer Adapter

External frame output MUST pass through an adapter before entering runtime:

`	ext
dev-frame native format
    → dev-frame adapter (in agent-acceptance)
    → Boundary Envelope
    → Canonical Contract (e.g., RunSpec v1)
`

Adapters live in gent-acceptance/adapters/ and are the ONLY place
where external format conversion happens. Contract conversion logic
must NOT be scattered across gates, reports, or planners.

## Deprecation Policy

| Phase | Behavior | Gate 0 Signal |
|-------|----------|:-------------:|
| stable | Accepted, no warning | — |
| deprecated | Accepted, WARNING logged | WARNING |
| rchived | Rejected at Gate 0 | BLOCKED |

Minimum deprecation window: 2 phases (e.g., Phase 6-7).

## Compatibility Lock Updates

When contracts evolve, the runtime compatibility lock MUST be updated:

`yaml
accepted_contract_versions:
  TaskSpec: ["1.0.0", "2.0.0"]  # Added v2
`

Frames update their manifests:

`yaml
contracts:
  produces:
    RunSpec:
      versions: ["1.0.0", "2.0.0"]  # Now supports v2
`

## Verification

The check-frame-compat.py script verifies:
- All produced contract versions have intersection with lock accepted versions
- No archived contract version is in use
- No unknown contract type is produced
