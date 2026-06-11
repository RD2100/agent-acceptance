# GPT Review Prompt — STARTUP-READ-GATE-DEFAULT-PATH-RUNID-HARDEN-A1

## 审查请求

**task_id**: STARTUP-READ-GATE-DEFAULT-PATH-RUNID-HARDEN-A1
**run_id**: STARTUP_READ_GATE_DEFAULT_PATH_RUNID_HARDEN_A1_20260609T123300_RD
**parent_task**: STARTUP-READ-GATE-INTEGRATE-PRE-GPT-A1 (GPT-authorized)

## 背景

本任务解决前几轮审查中反复出现的 3 个 limitation：
1. NEXT_AGENT_REQUIRED_READS.json 默认路径从硬编码改为自动探测
2. task_id 从 PACK_MANIFEST.md 中提取更加稳健
3. 缺失 required reads 文件时给出明确错误信息

## 请审查以下附件 Evidence Pack

Evidence Pack (ZIP) 包含：
- `scripts/pre_gpt_review_gate.py` — 增强后的 pre-GPT 门禁脚本（~170行）
- `tests/test_pre_gpt_review_gate.py` — 29 个回归测试（20 原有 + 9 新增）
- `EXECUTION_REPORT.md` — 执行报告
- `PACK_MANIFEST.md` — 包清单

## 审查重点

1. **路径自动探测**：resolve_required_reads_path 的搜索顺序是否合理？
2. **task_id 提取**：_extract_task_id_from_manifest 是否覆盖了常见格式？
3. **错误信息**：缺失 reads 时的错误信息是否足够明确？
4. **向后兼容**：所有原有测试是否仍然通过？

## 回复格式要求

```
overall_judgment: [accepted | accepted_with_limitation | blocked | human_required]
evidence_pack_reviewed: [true | false]
attachment_reviewed: [true | false]
blocking_issues:
[如有阻塞问题请列出]
required_fixes:
[如有必须修复项请列出]
limitations:
[限制条件和后续建议]
next_task_authorization:
task_id: [下一个任务ID]
authorized: [已授权 | 未授权]
execute_immediately: [是 | 否]
ask_before_starting: [是 | 否]

run_id: STARTUP_READ_GATE_DEFAULT_PATH_RUNID_HARDEN_A1_20260609T123300_RD
task_id: STARTUP-READ-GATE-DEFAULT-PATH-RUNID-HARDEN-A1

END_OF_GPT_RESPONSE_
```
