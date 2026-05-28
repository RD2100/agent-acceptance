# TaskSpec: Regression Test — Batch C3C+C3D

> ID: task-regression-c3c-c3d-001
> Date: 2026-05-28
> Risk: low | Reversibility: reversible (read-only checks)

## Goal

Execute regression checks on all changes from Batch C3C (Capability Passport + Skills-inbox) and Batch C3D (CodeGraph, WorkQueue, Hooks, SessionLedger).

## Allowed Files (read-only)
- D:\agent-acceptance\docs\agent-runtime\capability-inventory.md
- D:\agent-acceptance\docs\agent-runtime\sub-agent-dispatch-protocol.md
- D:\agent-acceptance\hooks\pre-final.audit.ps1
- D:\agent-acceptance\hooks\pre-task.audit.ps1
- D:\agent-acceptance\hooks\pre-tool.audit.ps1
- D:\agent-acceptance\hooks\skill-intake-scan.audit.ps1
- D:\agent-acceptance\scripts\New-SessionLedger.ps1
- D:\agent-acceptance\hooks\registration-config.json
- D:\agent-acceptance\hooks\sealed-files-manifest.json
- D:\agent-acceptance\agent-workqueue\SADP-INTEGRATION.md

## Acceptance Gates

### G1: PowerShell Syntax (all 5 scripts)
Run: Get-Command -Syntax on each .ps1 file. All 5 must pass.

### G2: Passport Distribution Consistency
Count verified_status in capability-inventory.md capability entries vs Summary table. Must match: verified=25, degraded=1, broken=1, stale=1, unknown=0, total=28.

### G3: SADP Cross-References
- Check §4.5 references agent-workqueue/SADP-INTEGRATION.md (file must exist)
- Check §3.3b WorkQueue auto-trigger table queue filenames match actual files in agent-workqueue/

### G4: Hook Registration Config
- registration-config.json must be valid JSON
- sealed-files-manifest.json must include all 5 hook filenames

### G5: SessionLedger Syntax
- PSParser Tokenize must pass on New-SessionLedger.ps1

## Evidence Required
- Each gate: command output proving PASS/FAIL
- Final: pass/fail/blocked verdict

## Report Format
Standard ExecutionReport with per-gate evidence.

## Forbidden
- No file writes
- No git mutations
- No package install
