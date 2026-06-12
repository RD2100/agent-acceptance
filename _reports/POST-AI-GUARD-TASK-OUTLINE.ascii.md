# Post-AI-GUARD Task Outline (ASCII-safe summary)
# See POST-AI-GUARD-TASK-OUTLINE.md for full Chinese version

Baseline: 1d820d3c (P1 --files mode + streaming scan) + b797f19 (test portability)
Status: v2 approved as roadmap

## Execution Order

Phase 1: WORKSPACE-CLOSURE-INVENTORY-A1 (read-only, no modifications)
Phase 2: HOOK-FAILURE-SEMANTICS-FINALIZE-A1 (docs + review)
Phase 3: Batch cleanup per inventory (each batch = independent TaskSpec)
Phase 4: Quality hardening (Codex P2/P3 + structural deficiencies)
Phase 5: Authorization gates (human-led, live dispatch / project binding)

## Phase 1 Detail: Inventory (read-only)

Scope: ~200 untracked files in workspace root
Output: inventory with columns: path | category | action | risk | has_zip | notes
Actions: KEEP / COMMIT / ARCHIVE / DISCARD

Categories:
  1. CDP temp scripts (~35): _ask_*, _capture_*, _submit_*, _build_*
  2. Session evidence dirs (~20): _evidence/* subdirs not archived to ZIP
  3. Evidence pack ZIPs (~15): iteration duplicates, mark final versions
  4. NEG-009 mock fixtures (17): _projects/*/NEG-009-secrets-read.json
  5. Windows artifacts: nul file
  6. Reports/docs: _reports/PROMPT_*.md etc.
  7. scripts/_evidence/ subdir: script run artifacts

## Stuck in_progress Tasks (need decision)

HANDOFF-PIPELINE-REFACTOR-A1 (P0) - may be superseded by CDP approach
EVIDENCE-CAPTURE-HOOK-FAILURE-SEMANTICS-A1 (P0) - merge into Phase 2
CONTEXT-COMPRESSION-A1 (P1) - ai_guard --files fixed, can retry commit
EVIDENCE-CAPTURE-HOOK-FAILURE-RUNTIME-VALIDATION-A1 (P1) - check coverage
R18-FOLLOWUP-CLEANUP-A1 (P1) - check remaining items
R18-WORKSPACE-CLEANUP-A1 (P1) - may be covered by Phase 3
EVIDENCE-CAPTURE-HOOK-FAILURE-RUNTIME-VALIDATION-CLEANUP-A1 (P2) - depends on above
R18-EVIDENCE-MAINTENANCE-A1 (P2) - may be covered by Phase 3

## Authorization Gates (human-led)

Live Dispatch: unauthorized, needs human auth + fresh dry-run
tripmark: tab_unresolved
7 pending projects: not bound
PAPER-C1: accepted, binding not committed
CODEGRAPH-FORK-POOL: review_unverified

## Out of Scope

- New feature development
- Cross-repo sync
- Live dispatch execution
- New project binding
