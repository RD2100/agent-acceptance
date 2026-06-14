# Evidence Reviewer Index: devframe-control-plane-registry-migration-a1

## Review Focus

- Confirm `.agent/PROJECT_REGISTRY.json` diff only adds
  `devframe-control-plane` as `pending_binding`.
- Confirm the decision packet records human authorization.
- Confirm no external runtime, source repository mutation, submodule, or
  physical bootstrap is included.
- Confirm `_projects/project-gamma` deletion set is not staged.

## Critical Files

- `.agent/PROJECT_REGISTRY.json`
- `_reports/devframe-control-plane-registry-decision-a1/DECISION_PACKET.md`
- `_reports/devframe-control-plane-registry-migration-a1/REGISTRY_MIGRATION_REPORT.md`
- `.ai/current-task.yaml`
- `tasks/devframe-control-plane-registry-migration-a1.md`

