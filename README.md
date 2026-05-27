# Agent Acceptance — 通用验收链路

通用的任务执行/验证/恢复框架。不绑定特定执行引擎，通过 CLI 接口与被测对象交互。

## 仓库定位

本仓库是 [ai-workflow-hub](D:\dev-frame\ai-workflow-hub) 的**独立验收层**，存放验收脚本、工作队列、文档和质量门。

- **验收脚本**：位于 `scripts/`，通过 CLI 与被测对象交互
- **工作队列**：位于 `agent-workqueue/`，定义 Tier 0/1/2 任务编排
- **验收命令**：通过 ai-workflow-hub CLI 在下游仓库目录执行，约定上游路径环境变量 `$env:AI_WORKFLOW_HUB = "D:\dev-frame\ai-workflow-hub"`
- **本地自检**：本仓库可独立运行 `Test-WorkQueue.ps1`、batch/queue/smoke 的 dry-run 模式，无需上游仓库

## 分层

| 层 | 目录 | 职责 |
|----|------|------|
| PowerShell Runner | `scripts/` | 单命令验收入口，exit code 语义 |
| Batch Runner | `scripts/` | 批量任务执行，每任务独立报告 |
| WorkQueue | `agent-workqueue/` | 队列化批量推进，Tier 分级，升级规则 |
| Parallel Group | `scripts/Run-QueueGroup.ps1` | 受控并行，冲突防护 |

## 快速开始

```powershell
# Smoke — 7 项基础检查
powershell -ExecutionPolicy Bypass -File scripts/Run-Smoke.ps1

# Batch — 10 项本地质量检查
powershell -ExecutionPolicy Bypass -File scripts/Run-Batch.ps1 `
  -TaskFile scripts/examples/batch-local-quality.json

# WorkQueue — 5 队列批量执行
powershell -ExecutionPolicy Bypass -File scripts/Run-AllQueues.ps1

# Parallel — 3 并行安全队列
powershell -ExecutionPolicy Bypass -File scripts/Run-QueueGroup.ps1 `
  -Parallel -MaxParallel 2 `
  -QueueFiles agent-workqueue/docs-quality.queue.json,...
```

## 核心约定

- Exit 0 = PASS, 1 = BLOCKED, 2 = FAILED
- Tier 0 自动执行，Tier 2 必须升级
- 禁止假绿：FAILED/BLOCKED 不伪装成 PASS
- 默认 dry-run，真实操作需要显式 flag

## 文档

- `docs/RECOVERY_PIPELINE_RUNBOOK.md` — OS kill 后如何恢复
- `docs/AGENT_WORKQUEUE_RULES.md` — 分级与升级规则
- `docs/ARTIFACT_RETENTION_POLICY.md` — 产物清理策略
- `docs/OPERATOR_RUNBOOK_INDEX.md` — 操作手册索引
- `docs/NEXT_AGENT_HANDOFF.md` — 下一智能体交接
