## 注意：本文与 capability-routing-final-audit.md 存在内容重叠
## 两者同属 Batch CR-B，描述同一批 CR0-CR5 能力路由工作；handoff 是 final-audit 的过渡/操作版本
# Capability Routing Handoff -- CR5

> Batch CR-B, 2026-05-27

## Current State

- **CR0**: 17 capabilities registered, all auto_use/execution/mutation=false
- **CR1**: 13 task types mapped to preferred/fallback/forbidden
- **CR2**: Agent prompt enforces pre-task selection + post-task audit; reviewer prompt covers 9-step review
- **CR3**: 30 negative tests, 18 hard stops, 0 expected_gate_decision=pass
- **CR4**: Reviewer playbook with 15-min quick review + 60-min deep review paths

## What Exists

| Directory | Key Files |
|-----------|----------|
| `docs/agent-runtime/` | capability-inventory.md, capability-risk-matrix.md, task-capability-routing-matrix.md, capability-selection-policy.md, capability-fallback-policy.md, coding-agent-capability-prompt.md, reviewer-capability-prompt.md, capability-routing-report-template.md, capability-routing-negative-tests.md, capability-routing-reviewer-playbook.md, capability-routing-reviewer-checklist.md, capability-routing-final-audit.md, capability-routing-handoff.md, capability-routing-status-index.md |
| `schemas/resource-integration/` | capability-record.schema.json, capability-routing-audit-record.schema.json |

## What Is Safe To Do Next

1. Reviewer sign-off on CR0-CR4
2. Integrate `coding-agent-capability-prompt.md` into agent execution workflow
3. Require `Capability Routing Audit` section in all future ExecutionReports
4. Use `capability-routing-reviewer-checklist.md` for all future batch reviews

## What Must Not Be Done

- Execute any capability that is forbidden in current phase
- Auto-trigger any capability (all auto_use_allowed=false)
- Skip preferred capability without recording reason
- Use forbidden capability as fallback
- Treat Phase 6C as unblocked

## Reviewer Focus (10 items)

1. Is Capability Routing Audit present in every future ExecutionReport?
2. Are forbidden capabilities ever marked Used?=yes?
3. Are preferred capabilities skipped without reason?
4. Is fallback chain valid when used?
5. Are status checks evidenced?
6. Is Phase 6C still blocked?
8. Are scripts still not_run without human gate?
9. Is memory still read_only?
10. Are all capabilities still auto_use/execution/mutation=false?
