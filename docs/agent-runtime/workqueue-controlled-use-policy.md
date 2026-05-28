# WorkQueue Controlled Use Policy -- R7

> Batch Y (R7), 2026-05-27
> R7 = read-only queue inspection only. No task dispatch. No consumption.

## 1. WorkQueue Role

WorkQueues define tier-graded task orchestration. In R7, queues are registered and classified. They are NOT consumed. Task dispatch is a future capability requiring separate human gate.

## 2. Queue Inventory

| Queue File | Tier | Tasks | Status |
|------------|:---:|:---:|:---:|
| cleanup-dryrun.queue.json | 1 | TBD | registered |
| docs-quality.queue.json | 1 | TBD | registered |
| local-quality.queue.json | 1 | TBD | registered |
| recovery-regression.queue.json | 1 | TBD | registered |
| release-readiness.queue.json | 2 | TBD | registered |

## 3. Tier Semantics (from operating-model.md)

| Tier | Auto-Execute | Escalation | R7 Status |
|:---:|:---:|-----------|:---:|
| 0 | YES | None | N/A (no Tier 0 queues defined) |
| 1 | YES | Log warning | active, auto-execute (read-only checks only) |
| 2 | NO | Must escalate to human | active, auto-execute (read-only checks only) |

Tier 1 queues (read-only checks only) are auto-enabled. No ScriptSafetyRecord required for read-only queues. Tier 2 still requires human gate.

## 4. Queue Consumption Gate

Before any WorkQueue is consumed:
1. Queue JSON validated against schema
2. Each task has approved TaskSpec
3. Execution plan reviewed and approved
4. ScriptSafetyRecord exists for the runner script
5. Pre/post git status required
6. EvidenceIndex pre-registered for each task
7. Reviewer explicitly approves queue consumption

## 5. Queue Modification

WorkQueue JSON files are part of the dirty baseline (13 modified files). They must not be further modified without explicit batch approval.

## 6. Forbidden Actions

- Consuming any queue (dispatching tasks)
- Modifying queue JSON definitions
- Auto-executing Tier 1 queues
- Skipping Tier 2 escalation
- Creating new queues without TaskSpec
- Using queue output as GateResult without reviewer
- Bypassing human gate for queue consumption

## 7. Dry-Run Default

Per operating-model.md: all runners default to dry-run mode. Even when queues are eventually consumed in future phases, the default behavior is dry-run. Real operations require explicit flags (-Real, -Apply).
