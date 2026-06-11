# GPT Review Prompt — STARTUP-READ-GATE-STRICT-HASH-TASKID-A1

## 审查请求

**task_id**: STARTUP-READ-GATE-STRICT-HASH-TASKID-A1
**run_id**: STARTUP_READ_GATE_STRICT_HASH_TASKID_A1_20260609T121957_RD
**parent_task**: STARTUP-READ-GATE-ENFORCE-A1 (GPT-authorized)

## 背景

本任务是对 STARTUP-READ-GATE-ENFORCE-A1 审查中发现的 limitations 的 follow-up 硬化。主要改动是在 `startup_read_gate.py` 中添加 `--strict` 模式，将关键 warning 提升为 error。

## 请审查以下附件 Evidence Pack

Evidence Pack (ZIP) 包含：
- `scripts/startup_read_gate.py` — 增强后的启动读门禁脚本（~350行，含严格模式）
- `tests/test_startup_read_gate.py` — 19 个回归测试（12 原有 + 7 新增）
- `EXECUTION_REPORT.md` — 执行报告
- `PACK_MANIFEST.md` — 包清单

## 审查重点

1. **strict 模式覆盖度**：是否覆盖了 R1 review 中提出的 4 个核心 limitation？
2. **向后兼容**：非 strict 模式行为是否完全保持不变？
3. **coverage_ratio 修复**：matched_required / must_read_count 计算是否正确？
4. **路径匹配**：`_normalize_path` + `_find_proof_entry` 是否足够健壮？
5. **测试质量**：新增测试是否覆盖了主要路径和边界条件？

## 已知未覆盖项

- state machine runtime 集成（后续任务）
- startup_timestamp 新鲜度检查
- pre_gpt_review_gate.py 集成
- strict 模式尚未默认启用

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

run_id: STARTUP_READ_GATE_STRICT_HASH_TASKID_A1_20260609T121957_RD
task_id: STARTUP-READ-GATE-STRICT-HASH-TASKID-A1

END_OF_GPT_RESPONSE_
```
