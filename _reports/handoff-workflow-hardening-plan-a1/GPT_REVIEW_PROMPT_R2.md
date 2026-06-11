GPT REVIEW REQUEST: HANDOFF-WORKFLOW-HARDENING-PLAN-A1-R2

run_id: HANDOFF_WORKFLOW_HARDENING_PLAN_A1_R2_REVIEW_20260609T021002_RD

请审查附件 R2 evidence pack。这是对 R1 blocked verdict 的修复提交。

R1 blocked 原因及本次修复：

1. source-of-truth 层级表述错误（P0/P1/P2/P3 定义不符合 HANDOFF_SOURCE_OF_TRUTH.md）
   → 已修正为与 HANDOFF_SOURCE_OF_TRUTH.md 一致的定义

2. gpt_new_chat_attachment_submit.py 能力描述与 HARDENING_GAP_ANALYSIS.json 不一致
   → 已统一描述：明确脚本当前为 pointer_only + 实际实现功能 + 参数化限制

3. startup proof 未纳入 evidence pack
   → 已将 STARTUP_READ_PROOF 和 STARTUP_READ_SUMMARY 纳入 pack 和 manifest

4. HANDOFF_REPLY_V4.txt 表述不够明确
   → 已明确其仍为 tracked_deleted_human_required，不得自动 git restore

新增内容（基于 R1 审查中发现的 capture 误取问题）：
- 新增 GAP-010（capture_mechanism_hardening）
- 新增附录 C：R1 审查经验教训
- 新增 GPT_CAPTURE_ADVICE.txt：GPT 关于 capture 固化的详细建议
- 核心原则：在延续性对话中，last assistant is not authoritative；target run_id match is authoritative

请重点判断：
1. R1 的 4 个 blocking issues 是否已全部修复
2. 新增的 capture 经验教训是否合理
3. 整体计划是否可接受（可附 limitation）

如果附件不可检查，请返回 review_unverified。

请只返回：

run_id: HANDOFF_WORKFLOW_HARDENING_PLAN_A1_R2_REVIEW_20260609T021002_RD
task_id: HANDOFF-WORKFLOW-HARDENING-PLAN-A1-R2
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
