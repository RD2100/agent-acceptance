GPT 咨询请求：HANDOFF_REPLY_V4.txt deletion/scope 处理建议

run_id: HANDOFF_REPLY_V4_RESTORE_SCOPE_CONSULT_20260609_083700_RD

task_id: HANDOFF-REPLY-V4-RESTORE-SCOPE-CONSULT-A1

背景：
当前任务是 GLOBAL-PROJECT-EVIDENCE-BINDING-A1-R2。上一轮 GLOBAL-PROJECT-EVIDENCE-BINDING-A1 被 GPT blocked，核心阻塞之一是 changed-files evidence 显示：

D HANDOFF_REPLY_V4.txt

上一轮 GPT blocking issue 原文要点：
- changed-files evidence shows tracked deletion of HANDOFF_REPLY_V4.txt, so the pack cannot independently verify that all legacy HANDOFF-related files were not deleted.
- SAFETY_ATTESTATION claims legacy files were not deleted/moved/renamed/rewritten, but git changed-files evidence contains D HANDOFF_REPLY_V4.txt.
- required fix: Resolve HANDOFF_REPLY_V4.txt by either restoring it if it is a protected legacy handoff artifact or providing P0 evidence that it is out of protected scope; update protected legacy status accordingly.

我刚做的只读检查：
1. `git status --short -- HANDOFF_REPLY_V4.txt` 显示：`D HANDOFF_REPLY_V4.txt`
2. `git ls-files --stage -- HANDOFF_REPLY_V4.txt` 显示它是 tracked 文件。
3. `git log --oneline -- HANDOFF_REPLY_V4.txt` 最近提交：`de457217 docs: HANDOFF-A1 — v4 Chinese bootstrap reply from new conversation 6a23dd8c`
4. Grep 发现多处现有证据把它列为 dirty baseline / excluded file / 不得修改或不得提交删除，例如：
   - `GPT_HANDOFF_FINAL.txt`: “不要删除 HANDOFF_REPLY_V4.txt。”
   - `_reports/dirty-worktree-split-a1/STAGING_PLAN.md`: “Do not commit HANDOFF_REPLY_V4.txt deletion without a separate ...”
   - 多个 `GROUP_*_EXCLUDED_FILES.txt`: `HANDOFF_REPLY_V4.txt deletion`
   - 多个 baseline status 文件显示它是既有 dirty deletion。

当前约束：
- 不得删除、移动、重命名、清理、覆盖 legacy PROJECT_HISTORY / HANDOFF / PASTE_BLOCK 文件。
- 不得执行 git reset / git clean / git checkout。
- git restore / 从 HEAD 恢复 HANDOFF_REPLY_V4.txt 属于触碰 legacy 文件状态，当前应视为 human_required，不可自动执行。
- 用户要求：这种不确定事项先问网页版 GPT 寻求建议。
- 后续 GPT 交流必须中文；机器字段可保留英文。

请给出建议：
A. R2 是否应该恢复 `HANDOFF_REPLY_V4.txt`？
B. 如果恢复是最佳闭合路径，是否必须先获得用户明确确认？
C. 如果不恢复，能否通过 P0 evidence 证明它 out-of-scope？当前这些证据是否足够？
D. R2 在不执行高风险操作的前提下，是否应先产出 `human_required` 决策记录而不是继续打包声称 resolved？
E. 最小、最安全、最符合现有流程的下一步是什么？

请只返回以下结构，字段名保持英文以便脚本验证，内容用中文：

run_id: HANDOFF_REPLY_V4_RESTORE_SCOPE_CONSULT_20260609_083700_RD
task_id: HANDOFF-REPLY-V4-RESTORE-SCOPE-CONSULT-A1
overall_judgment: accepted | accepted_with_limitation | blocked | review_unverified
consultation_verdict: restore_requires_human_confirmation | scope_out_supported | human_required | blocked
recommendation:
  - <建议>
restore_should_be_done: 是 | 否 | 不确定
restore_requires_user_confirmation: 是 | 否
scope_out_supported_by_current_evidence: 是 | 否 | 不确定
safe_automatic_next_steps:
  - <可自动执行步骤>
human_required_steps:
  - <需用户确认步骤>
risk_controls:
  - <风险控制>
next_task_authorization:
  task_id: GLOBAL-PROJECT-EVIDENCE-BINDING-A1-R2 | none
  authorized: 已授权 | 未授权
  execute_immediately: 是 | 否
  ask_before_starting: 是 | 否
END_OF_GPT_RESPONSE
