# Acceptance Script Registry -- R7

> Batch Y (R7), 2026-05-27
> R7 = register and classify scripts only. No execution. No WorkQueue consumption.

## 1. R7 Boundary

R7 registers all agent-acceptance native scripts, workqueues, templates, and historical runs. All scripts are classified with safety records. No script is executed. No WorkQueue is consumed. No template is overwritten. No run history is modified.

## 2. Script Inventory

### PowerShell Scripts (scripts/)

| Script | Type | Execution Status | Mutation Risk | Network Risk | Secret Risk |
|--------|:---:|:---:|:---:|:---:|:---:|
| Run-Smoke.ps1 | smoke | not_run | medium | none | none |
| Run-Batch.ps1 | batch | not_run | medium | none | none |
| Run-WorkQueue.ps1 | queue | not_run | high | none | none |
| Run-AllQueues.ps1 | queue | not_run | high | none | none |
| Run-QueueGroup.ps1 | queue | not_run | high | none | none |
| Test-WorkQueue.ps1 | test | not_run | medium | none | none |
| Write-Report.ps1 | report | not_run | medium | none | none |

**All scripts**: `execution_status = not_run`, `allowed_to_run = false`, `human_gate_required = true`.

### Script Safety Profiles

| Script | Mutation Risk Detail |
|--------|---------------------|
| Run-Smoke.ps1 | Reads filesystem. Dry-run by default. No writes without -Real flag. |
| Run-Batch.ps1 | Reads and potentially writes (reports). Dry-run by default. |
| Run-WorkQueue.ps1 | Processes queue tasks. May trigger real operations with -Real flag. |
| Run-AllQueues.ps1 | Batch processes all 5 queues. Cumulative risk. |
| Run-QueueGroup.ps1 | Parallel execution with conflict protection. |
| Test-WorkQueue.ps1 | Tests queue logic. May produce test artifacts. |
| Write-Report.ps1 | Writes report files. Medium mutation risk. |

## 3. WorkQueue Inventory (agent-workqueue/)

| Queue | Tier | Status | Notes |
|-------|:---:|:---:|-------|
| cleanup-dryrun.queue.json | Tier 1 | registered | Dry-run cleanup |
| docs-quality.queue.json | Tier 1 | registered | Documentation quality |
| local-quality.queue.json | Tier 1 | registered | Local code quality |
| recovery-regression.queue.json | Tier 1 | registered | Recovery regression |
| release-readiness.queue.json | Tier 2 | registered | Release readiness (Tier 2: must escalate) |

**All queues**: `consumed = false`. R7 only reads queue definitions. No task dispatch.

## 4. Template Inventory (templates/)

| Template | Status | Notes |
|----------|:---:|-------|
| AGENTS.single-project.md | reference_only | Single-project AGENTS template |
| project-batch-quality.json | reference_only | Batch quality template |
| project-quality.queue.json | reference_only | Quality queue template |

**All templates**: read-only. Modification requires separate TaskSpec with approved scope.

## 5. Run History (runs/)

| Directory | Status | Notes |
|-----------|:---:|-------|
| runs/powershell-acceptance/ | historical_only | Historical run artifacts |

**All runs**: historical evidence only. Cannot be used as current result. Cannot be modified.

## 6. Forbidden Actions (R7)

1. Execute any PowerShell script in scripts/
2. Consume any WorkQueue (dispatch tasks)
3. Modify any template
4. Modify any run history
5. Treat historical run as current pass
6. Auto-trigger any script from queue or batch
7. Modify script source code
8. Register scripts as scheduled tasks
9. Use script output as GateResult without reviewer
10. Bypass human gate for any script execution

## 7. Future Script Execution Gate

When a future phase authorizes script execution:
1. ScriptSafetyRecord must be approved by reviewer
2. Pre/post git status required
3. EvidenceIndex pre-registered
4. Human gate explicitly approves each execution
5. Output logged and checksum recorded
6. Exit code contract enforced (0=PASS, 1=BLOCKED, 2=FAILED)
