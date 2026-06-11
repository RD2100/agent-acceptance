# 记忆索引

> 最后更新: 2026-06-06T08:46:31Z
> 条目总数: 15
> 生成方式: memory_compiler.py
> 隐私分类: 默认私有

## 概念条目

| 记忆ID | 标题 | 记忆类型 | 状态 |
|--------|------|---------|------|
| MEM-A2-001 | 系统性缺陷 SD-01（summary-only evidence pack）仍... | 失败模式 | 活跃 |
| MEM-A2-002 | 系统性缺陷 SD-02（ready_for_review 被当作 closed）... | 失败模式 | 活跃 |
| MEM-A2-003 | 识别到已闭合任务，可作为后续 memory 编译的数据来源... | 工作流规则 | 活跃 |
| MEM-A2-004 | 识别到已闭合任务，可作为后续 memory 编译的数据来源... | 工作流规则 | 活跃 |
| MEM-A2-005 | 识别到已闭合任务，可作为后续 memory 编译的数据来源... | 工作流规则 | 活跃 |
| MEM-A2-006 | 识别到已闭合任务，可作为后续 memory 编译的数据来源... | 工作流规则 | 活跃 |
| MEM-A2-007 | 识别到已闭合任务，可作为后续 memory 编译的数据来源... | 工作流规则 | 活跃 |
| MEM-A2-008 | summary-only evidence pack 被 GPT 驳回；必须包含... | 教训 | 活跃 |
| MEM-A2-009 | ready_for_review 不等于 closed；closed 必须有 G... | 教训 | 活跃 |
| MEM-A2-010 | 多轮迭代后仍被 GPT 判 blocked，说明 pre-submission ... | 失败模式 | 活跃 |
| MEM-A2-011 | summary-only evidence pack 被 GPT 驳回；必须包含... | 教训 | 活跃 |
| MEM-A2-012 | ready_for_review 不等于 closed；closed 必须有 G... | 教训 | 活跃 |
| MEM-A2-013 | 多轮迭代后仍被 GPT 判 blocked，说明 pre-submission ... | 失败模式 | 活跃 |
| MEM-A2-014 | summary-only evidence pack 被 GPT 驳回；必须包含... | 教训 | 活跃 |
| MEM-A2-015 | ready_for_review 不等于 closed；closed 必须有 G... | 教训 | 活跃 |


## 失败模式

| 记忆ID | 模式 | 出现次数 | 关联 gate | 状态 |
|--------|------|---------|----------|------|
| — | 系统性缺陷 SD-01（summary-only evidence pack）仍处于 open 状态... | 待统计 | 待评估 | 活跃 |
| — | 系统性缺陷 SD-02（ready_for_review 被当作 closed）仍处于 open 状... | 待统计 | 待评估 | 活跃 |
| — | 多轮迭代后仍被 GPT 判 blocked，说明 pre-submission self-verif... | 待统计 | 待评估 | 活跃 |
| — | 多轮迭代后仍被 GPT 判 blocked，说明 pre-submission self-verif... | 待统计 | 待评估 | 活跃 |


## 踩坑记录

| 记忆ID | 坑 | 关联任务 |
|--------|-----|---------|


## 下一步总体计划

Memory Compiler 原型已运行。当前编译了 15 条记录。
后续应增加：自动检测重复模式、关联 gate 更新建议、与 WORKFLOW_AUDIT_LEDGER 联动。
