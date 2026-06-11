# GPT Review Prompt — STATE-MACHINE-RUNTIME-INTEGRATE-A1

## 审查请求

**task_id**: STATE-MACHINE-RUNTIME-INTEGRATE-A1
**run_id**: STATE_MACHINE_RUNTIME_INTEGRATE_A1_20260609T124000_RD
**parent_task**: STARTUP-READ-GATE-DEFAULT-PATH-RUNID-HARDEN-A1 (GPT-authorized)

## 背景

本任务创建状态机运行时执行脚本，将 startup_read_gate 和 evidence_pack_linter 集成为 draft → gate_passing 转换的 guard 条件。完全对齐 PROCESS_STATE_MACHINE.json 中定义的 8 状态、10 转换、8 不变量。

## 请审查以下附件 Evidence Pack

Evidence Pack (ZIP) 包含：
- `scripts/state_machine_runtime.py` — 状态机运行时脚本（~280行）
- `tests/test_state_machine_runtime.py` — 22 个测试
- `_reports/process-state-machine-define-a1/PROCESS_STATE_MACHINE.json` — 状态机定义（参考）
- `EXECUTION_REPORT.md` — 执行报告
- `PACK_MANIFEST.md` — 包清单

## 审查重点

1. **状态定义完整性**：8 个状态是否与 PROCESS_STATE_MACHINE.json 完全对齐？
2. **转换正确性**：10 个转换是否完整覆盖？
3. **Guard 实现**：draft → gate_passing 的三个 guard 条件是否正确集成？
4. **startup_read_gate 集成**：是否正确使用了 auto-detect required reads path？
5. **测试覆盖**：22 个测试是否覆盖了主要路径？

## 回复格式要求

```
overall_judgment: [accepted | accepted_with_limitation | blocked | human_required]
evidence_pack_reviewed: [true | false]
attachment_reviewed: [true | false]
blocking_issues:
required_fixes:
limitations:
next_task_authorization:
task_id: [下一个任务ID]
authorized: [已授权 | 未授权]
execute_immediately: [是 | 否]
ask_before_starting: [是 | 否]

run_id: STATE_MACHINE_RUNTIME_INTEGRATE_A1_20260609T124000_RD
task_id: STATE-MACHINE-RUNTIME-INTEGRATE-A1

END_OF_GPT_RESPONSE_
```
