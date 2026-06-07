# WorkQueue Governance

> 主题: workqueue
> 关联任务: WorkQueue integrity, specialized batches
> 最后更新: 2026-06-07
> 阅读时机: 需要运行或理解 agent-workqueue 时

## 概述

agent-workqueue 提供批量任务执行与 governance queue 管理。

## 已接受的 WorkQueue 任务

- WorkQueue integrity run: 队列完整性验证
- WorkQueue specialized batches: cleanup-dryrun, recovery-regression, release-readiness
- Run-WorkQueue.ps1 传播：runner exit propagation

## Queue 文件结构

- agent-workqueue/QUEUE_INDEX.md — 队列索引
- agent-workqueue/*.queue.json — 具体队列定义
- scripts/Run-WorkQueue.ps1 — 队列执行器
- scripts/examples/batch-*.json — 示例 batch 配置

## 安全约束

- 队列执行前需验证 safety-report.json
- 禁止在队列中包含论文处理任务
- 所有队列执行需有 GPT review gate
