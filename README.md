# Agent Acceptance — 规范验收层

> **Agent 冷启动：请按顺序读取以下文件，不要跳过。**
>
> 1. `PROJECT_HISTORY.md` — 项目生存文档（全部阶段历史、架构、经验、当前状态）
> 2. `HANDOFF_V5.md` — 当前交接快照（上一个 GPT 生成的最新上下文）
> 3. `D:\devframe-control-plane\PROJECT_HISTORY.md` — 子项目完整历史
>
> 读完三份文档后，你应能回答：项目是什么、做过什么、当前状态、安全边界、下一步。然后按 CLAUDE.md 中的协议工作。

---

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
