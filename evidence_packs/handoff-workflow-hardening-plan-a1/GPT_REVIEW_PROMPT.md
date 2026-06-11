# GPT Review Prompt — HANDOFF-WORKFLOW-HARDENING-PLAN-A1

GPT REVIEW REQUEST: HANDOFF-WORKFLOW-HARDENING-PLAN-A1

run_id: HANDOFF_WORKFLOW_HARDENING_PLAN_A1_REVIEW_20260609_012328_RD

请审查附件 evidence pack。该任务目标是基于现有仓库 workflow 和最近 GPT verdict，形成 GPT-agent 自动化交接流程的硬化计划，而不是重新设计或直接实现所有机制。

请重点判断：

1. 是否复用了仓库已有 workflow / source-of-truth / verifier / runbook / evidence pack 结构；
2. 是否没有重新发明一套 GPT-agent 流程；
3. 是否准确识别流程完整度缺口；
4. 是否保留 accepted_with_limitation / blocked / partial / needs_more_evidence / human_required 语义；
5. 是否没有修改 legacy PROJECT_HISTORY / HANDOFF / PASTE_BLOCK；
6. 是否没有执行 git reset / clean / checkout / restore / commit / push；
7. 是否给出后续可执行的最小任务路线。

如果附件不可检查，请返回 review_unverified。

请只返回：

run_id: HANDOFF_WORKFLOW_HARDENING_PLAN_A1_REVIEW_20260609_012328_RD
task_id: HANDOFF-WORKFLOW-HARDENING-PLAN-A1
overall_judgment: accepted | accepted_with_limitation | blocked | review_unverified
evidence_pack_reviewed: true | false
attachment_reviewed: true | false
blocking_issues:
- <问题或 none>
required_fixes:
- <修复或 none>
limitations:
- <限制或 none>
next_task_authorization:
task_id: <下个任务或 none>
authorized: 已授权 | 未授权
execute_immediately: 是 | 否
ask_before_starting: 是 | 否
END_OF_GPT_RESPONSE
