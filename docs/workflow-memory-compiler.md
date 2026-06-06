# Workflow Memory Compiler — DevFrame 工作流记忆编译层设计

> 版本: 1.0.0-draft
> 权威来源: agent-acceptance（规范层，设计先行）
> REVIEW_RUN_ID: memory-a1-workflow-memory-design-v1

## 1. 为什么 DevFrame 需要 Workflow Memory Layer

近期工作流暴露出重复性缺陷：

| 缺陷 ID | 现象 | 出现次数 | 首次发现 |
|---------|------|---------|---------|
| SD-01 | agent 提交 summary-only evidence pack | 3+ | PAPER-A1 |
| SD-02 | ready_for_review 被误当成 closed | 2+ | ARCH-GAP-A1 |
| SD-03 | self-referential failure（治理任务自身绕过治理） | 1 | ARCH-GAP-A1 |
| SD-04 | manifest/ZIP/SHA256/provenance 不一致 | 3+ | PAPER-A1 |

每次缺陷都在 GPT 审查阶段才发现，教训停留在 GPT 对话中。HANDOFF.md 解决了项目冷启动问题，但如果 agent 或 GPT 切换后，"PAPER-A1 曾经因为 summary-only pack 被驳回 3 次" 这个教训无法被新 agent 自动获取。

## 2. 它解决什么问题

- GPT 审查中发现的 failure pattern 被沉淀为可检索知识
- 新 agent / 新 GPT 对话可通过 memory index 快速获取历史教训
- 重复缺陷被 lint 规则检测，在提交 GPT 前阻断
- 已修正但可能再次出现的问题被标记为 gotcha

## 3. 它不解决什么问题

- 不替代 evidence pack 或 GPT review result
- 不替代 WORKFLOW_AUDIT_LEDGER 的权威性
- 不替代 HANDOFF.md 的项目冷启动功能
- 不自动修改治理规则、guard 或 contract
- 不自动 accept 任何 conclusion
- 不处理真实论文全文

## 4. 与 claude-memory-compiler 的关系

借鉴 [claude-memory-compiler](https://github.com/coleam00/claude-memory-compiler) 的**思想**：

| 概念 | claude-memory-compiler | DevFrame Memory Layer |
|------|----------------------|----------------------|
| daily log | 自动捕获 session log | 手动/半自动从 GPT_REVIEW_RESULT 编译 |
| compiled knowledge | 自动从 session 提取 | 从 workflow ledger + GPT review 提取，需 source 引用 |
| index | 自动维护 | 手动/半自动维护，按 memory_type 分类 |
| lint | 自动检查矛盾/孤立 | 按 MEMORY_LINT_CONTRACT 规则检查 |
| hooks | 自动 SessionEnd/PreCompact | **本任务不启用 hooks** |

**关键区别**：claude-memory-compiler 设计为自动捕获和编译 Claude Code session。DevFrame 涉及隐私论文、安全边界和 GPT accepted 审查，不能自动 ingest raw transcript。DevFrame memory layer 必须 source-citable、privacy-redacted、evidence-adjacent 但不可混淆。

## 5. 与三层架构的关系

```
agent-acceptance（本任务）:
  - 定义 memory 编译规则、隐私边界、lint 规则
  - 定义 allowed/prohibited sources
  - 提供 memory entry / index / daily log 模板

devframe-control-plane（后续）:
  - 在 pipeline closure 后可调用 memory 编译
  - 在 handoff 生成时可引用 memory index
  - 不直接修改权威 memory

dev-frame-opencode（后续）:
  - 可读取 memory index 作为上下文
  - 不可直接修改权威 memory
```

## 6. 与 HANDOFF.md 的关系

- HANDOFF.md = 项目冷启动文档，手动维护
- Memory Layer = 结构化教训知识库，从 GPT review 和工作流 ledger 编译
- HANDOFF.md 可引用 memory index 中的关键教训
- memory 不能替代 HANDOFF.md 中的项目定位、架构、安全边界

## 7. 与 WORKFLOW_AUDIT_LEDGER 的关系

- AUDIT_LEDGER = 权威的任务追踪记录（plan → execute → GPT review → status）
- Memory Layer = 从 ledger 中提取 patterns，但不修改 ledger
- Memory entry 必须引用 ledger 中的 task_id / review_run_id
- 两者互相参照但不能替代

## 8. 与 GPT_REVIEW_RESULT 的关系

- GPT_REVIEW_RESULT = 权威审查结论（accepted / blocked / review_unverified）
- Memory Layer = 从 review result 中提取 lesson 和 failure pattern
- Memory entry 的 source_review_run_id 必须指向实际存在的 GPT review
- memory 不能声称 accepted 如果 GPT review 没有 accepted

## 9. 为什么 memory 不能替代 evidence

| 维度 | Evidence | Memory |
|------|----------|--------|
| 权威性 | 权威（accepted/blocked 判决依据） | 辅助（经验参考） |
| 生成方式 | 框架生成（runner/builder/adapter） | 手动/半自动编译 |
| 验证 | manifest + SHA256 + bidirectional | 无 SHA256（lesson 不适用 hash） |
| 诉讼价值 | 高（不可篡改） | 低（可更新/废弃） |
| 必须性 | 必须（accepted 需要） | 可选（辅助参考） |

## 10. 为什么 memory 不能替代 GPT accepted

- GPT accepted 是每个任务闭包的必须条件
- Memory entry 是对任务经验的总结，不是审查替代
- `claims_accepted_without_gpt_review` = blocked（见 MEMORY_ENTRY_CONTRACT）

## 11. 设计原则

1. **Evidence-First**: memory 永远不能替代 evidence pack
2. **Privacy-First**: 默认所有论文内容为 private
3. **Append-Only Source**: memory entry 来源必须是非 transient、已存档的文档
4. **Compiled Knowledge Must Cite Source**: 每条 lesson 必须引用 source_review_run_id
5. **Memory is Advisory, Not Authoritative**: 不能用于 accepted/blocked 判决
6. **No Automatic External Upload**: 不自动上传到外部服务
7. **No Auto-Accept Edits**: 不允许 LLM 自动 acceptEdits 修改权威治理文件

## 12. 安全边界

| 边界 | 值 |
|------|-----|
| 真实论文全文 | 禁止进入 memory |
| 用户私有文本 | 禁止进入 memory |
| 完整聊天 transcript | 禁止进入 memory |
| cookie/session/browser profile | 禁止进入 memory |
| API keys/secrets | 禁止进入 memory |
| 脱敏工作流教训 | 允许进入 memory |
| GPT review 中的通用失败模式 | 允许进入 memory |
| contract/schema 设计经验 | 允许进入 memory |
