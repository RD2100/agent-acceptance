# GPT Review Prompt — STARTUP-READ-GATE-INTEGRATE-PRE-GPT-A1

## 审查请求

**task_id**: STARTUP-READ-GATE-INTEGRATE-PRE-GPT-A1
**run_id**: STARTUP_READ_GATE_INTEGRATE_PRE_GPT_A1_20260609T122600_RD
**parent_task**: STARTUP-READ-GATE-STRICT-HASH-TASKID-A1 (GPT-authorized)

## 背景

本任务将 `startup_read_gate.py` 集成到 `pre_gpt_review_gate.py` 中，实现硬ening 计划 §5.7.3 的要求：在 GPT 提交前自动验证启动证明的完整性。

## 请审查以下附件 Evidence Pack

Evidence Pack (ZIP) 包含：
- `scripts/pre_gpt_review_gate.py` — 集成后的 pre-GPT 门禁脚本（~130行）
- `scripts/startup_read_gate.py` — startup read gate 脚本（~350行，含 strict 模式）
- `tests/test_pre_gpt_review_gate.py` — 20 个回归测试（15 原有 + 5 新增集成测试）
- `tests/test_startup_read_gate.py` — 19 个测试（不变）
- `EXECUTION_REPORT.md` — 执行报告
- `PACK_MANIFEST.md` — 包清单

## 审查重点

1. **集成正确性**：startup_read_gate 是否正确嵌入 pre_gpt_review_gate 工作流？
2. **向后兼容**：不提供 `--startup-proof-path` 时行为是否完全不变？
3. **错误传播**：startup gate errors 是否正确阻止 CDP 提交？
4. **strict 模式传递**：strict 标志是否正确传递到 startup gate？
5. **测试覆盖**：5 个集成测试是否覆盖了主要路径？

## 已知未覆盖项

- 强制所有提交必须通过 startup gate（当前是 opt-in）
- 状态机运行时集成
- startup_timestamp 新鲜度检查

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

run_id: STARTUP_READ_GATE_INTEGRATE_PRE_GPT_A1_20260609T122600_RD
task_id: STARTUP-READ-GATE-INTEGRATE-PRE-GPT-A1

END_OF_GPT_RESPONSE_
```
