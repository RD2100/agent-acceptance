请阅读附件 HANDOFF_V5.md（约 13KB，含 END_OF_HANDOFF 标记）。

## 用以下格式回复确认理解

审查运行ID: handoff-verify-v5
交接理解判决: 已理解
项目身份已理解: 是
三层架构已理解: 是
已完成阶段已理解: 是
当前未闭合任务已理解: 是
安全边界已理解: 是
下一步任务已理解: 是
可以继续执行: 是
说明: 用中文说明理解，至少 5 句话

## 必须遵守的规则

1. closed 必须是 GPT accepted + ledger 记录。不许把 ready_for_review 当 closed
2. 每次提交 GPT 必须构建 evidence pack。不许提交 summary-only pack
3. GPT 回复必须等到 END_OF_GPT_RESPONSE 后才读取。不足 2000 bytes 不得执行
4. GPT accepted 后必须给出 next_task_authorization
5. 不得删除/移动/重命名 evidence。不得伪造 GPT accepted。不得默认开 live CDP
6. 对话超过 60 条 assistant message 必须 handoff

## 当前待闭合任务（按顺序执行）

1. REVIEW-TEMPLATE-V2 closure — commit bc841e9d 已 push 但从未提交 GPT。构建 evidence pack，提交审查
2. MEMORY-A3 + WORKFLOW_AUDIT_LEDGER SD-01/02/03 状态变更 — 合并为一个 closure pack 提交 GPT 确认
3. GPT-REVIEW-GATE-A1 — GPT 已给方案（docs/GPT_STRUCTURAL_FIX.txt），执行

## 确认后直接开始执行，不再询问
