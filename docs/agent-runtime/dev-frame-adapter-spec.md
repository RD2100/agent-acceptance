# dev-frame Orchestration Adapter Spec -- R3

> Batch X (R3), 2026-05-27
> R3 exit granted (2026-05-28). adapter_dry_run authorized. Read-only command inspection permitted. No test execution yet.


> **Phase Exit Authorization**: 2026-05-28. Reviewer: RD. R3 exit gate satisfied.
> adapter_dry_run now authorized. Read-only command inspection (`dir`, `git log`, `cat`) permitted on dev-frame components.
> Test execution (smoke_test.py, e2e) still requires separate human gate per ScriptSafetyRecord.

## 1. dev-frame Role

dev-frame is an **orchestration adapter candidate**, NOT an active executor. It is registered as a potential source of task orchestration capability. It is NOT authorized to execute tasks in R3.

## 2. RunSpec Relationship

dev-frame adapter maps to RunSpec (Contract 2) as a **candidate producer**.

- In future phases, dev-frame could generate RunSpec records from task definitions
- Currently (R3): design only, no RunSpec production
- `runspec_mapping`: "candidate only; not an active executor"

## 3. EvidenceIndex Relationship

Historical `smoke_report.txt` (2026-05-27, 3/3 PASS) and existing test results can be referenced in EvidenceIndex as **historical evidence only**.

- No current evidence is produced by dev-frame in R3
- All evidence from dev-frame must be marked `historical` in EvidenceIndex status field
- Default freshness: `stale_or_unknown`

## 4. GateResult NON-Relationship

dev-frame MUST NOT produce GateResult. Smoke reports and test results are evidence inputs to reviewer decisions, not decisions themselves.

- No dev-frame component may sign a gate
- No dev-frame component may determine pass/fail
- No dev-frame output may auto-advance a gate

## 5. Component Boundaries

| Component | Path | R3 Access | R3 Status | Key Constraint |
|-----------|------|:---:|:---:|---|
| ai-workflow-hub | `D:\dev-frame\ai-workflow-hub` | read_only (dir listing) | design_only | no execution |
| ai-workflow-hub-e2e | `D:\dev-frame\ai-workflow-hub-e2e` | read_only (dir listing) | design_only | no execution |
| smoke_test.py | D:\dev-frame\smoke_test.py | read_only (source) | adapter_dry_run | read source, do not execute | |
| smoke_report.txt | D:\dev-frame\smoke_report.txt | read_only | current (2026-05-27 baseline) | 3/3 PASS (historical baseline) |
| agent-acceptance (clone) | `D:\dev-frame\agent-acceptance` | read_only (dir listing) | duplicate | secondary clone; canonical is `D:\agent-acceptance` |
| .aiworkflow | `D:\dev-frame\.aiworkflow` | read_only (dir listing) | reference | no modification |
| aihub-worktrees | `D:\dev-frame\aihub-worktrees` | read_only (dir listing) | reference | no modification |

## 6. Historical smoke_report Policy

- `smoke_report.txt` (2026-05-27) is historical evidence
- It shows 3/3 PASS at that point in time
- It does NOT prove current state
- It can be referenced in EvidenceIndex as `historical, collected 2026-05-27`
- It MUST NOT be used to claim "dev-frame is currently passing"

## 7. adapter_draft vs adapter_dry_run

| | adapter_draft (R3 current) | adapter_dry_run (future) |
|---|---|---|
| **Definition** | Design documents, schemas, policies only | Read-only command inspection |
| **Execution** | None | None (still no test execution) |
| **State change** | None | None |
| **Human gate** | Not required (design phase) | Required (separate approval) |
| **Evidence** | Document existence | Command output inspection |

## 8. Dry-Run Human Gate (Authorized 2026-05-28)

Before any dry-run:
1. ScriptSafetyRecord must exist (script path, expected side effects, timeout, rollback)
2. Reviewer must explicitly approve the dry-run
3. Expected side effects must be documented before execution
4. EvidenceIndex must be pre-registered for the dry-run
5. Pre/post `git status --short` required

## 9. Forbidden Actions

1. execute smoke_test.py
2. execute ai-workflow-hub code (any .py file)
3. execute ai-workflow-hub-e2e tests
4. modify any file in D:\dev-frame
5. install packages (npm/pip) in dev-frame
6. run any script in dev-frame
7. treat smoke_report.txt as current pass
8. produce GateResult from any dev-frame component
9. expand RunSpec scope based on dev-frame
10. modify .aiworkflow
11. modify aihub-worktrees
12. use dev-frame/agent-acceptance as canonical root
13. run e2e tests
14. trigger WorkQueue from dev-frame
15. modify agent-acceptance files from dev-frame context

## 10. R3 Exit Gate

Before moving to a future dry-run phase:
1. ScriptSafetyRecord template defined
2. dry-run human gate procedure documented
3. Smoke validation policy approved by reviewer
4. All R3 negative tests passing (0 expected_gate_decision=pass)
5. Reviewer explicitly approves R3 exit
