# Context Compression

> 主题: context_compression
> 关联任务: CONTEXT-COMPRESSION-A1
> 最后更新: 2026-06-07
> 阅读时机: 了解上下文压缩架构时

## 问题

长时间对话后上下文持续膨胀。新 agent 每次都读取完整 PROJECT_HISTORY（~25K 字符）和 HANDOFF，导致冷启动成本高、信息噪音大。

## 解决方案

建立三层压缩架构：
1. BOOT_CONTEXT.md（3K-6K）：新 agent 冷启动入口
2. memory/index.md：可检索记忆索引
3. memory/tasks/*.md（300-800 字/任务）：压缩的 task lifecycle
4. memory/knowledge/*.md（500-1200 字/主题）：主题知识

## 压缩 pipeline

segment → classify → deduplicate → supersede → privacy_filter → emit

Privacy guard fail-closed：阻断论文正文、raw transcript、private text、secrets。

## 与 PROJECT_HISTORY.md 的关系

PROJECT_HISTORY.md 保持为 long-lived truth source，但不再是每次 session 的必读文件。新 agent 先读 BOOT_CONTEXT.md，按需深入。
