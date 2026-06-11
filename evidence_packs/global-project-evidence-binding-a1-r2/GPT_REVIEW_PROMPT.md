GPT 审查请求：GLOBAL-PROJECT-EVIDENCE-BINDING-A1-R2

run_id: GLOBAL_EVIDENCE_BINDING_A1_R2_20260609_085323

请审查附件 R2 evidence pack。重点：
1. 是否正确处理上一轮 blocked 的三个问题。
2. `HANDOFF_REPLY_V4.txt` 是否被如实标记为 `tracked_deleted_human_required`，没有被包装成 resolved/pass。
3. safety attestation 是否已和 git evidence 一致。
4. source binding / manifest 是否一致，旧 closure ZIP 若声称嵌入则确实在 pack 与 manifest 中。
5. 是否保留 partial / needs_more_evidence、production 未批准、296 PASS 未验证等限制。

请只返回：
run_id: GLOBAL_EVIDENCE_BINDING_A1_R2_20260609_085323
task_id: GLOBAL-PROJECT-EVIDENCE-BINDING-A1-R2
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
