# BOOT_CONTEXT.md — DevFrame 冷启动入口

> 生成时间: 2026-06-08 (auto-updated)
> 版本: v1.0
> 用途: 新 agent 首次读取此文件即可了解项目全貌，无需加载完整 PROJECT_HISTORY。

---

## 1. 项目身份

DevFrame 是一个三层工作流治理体系，用 evidence-first + GPT 审查 + 自动化流水线管理 AI 辅助的软件工程任务。

核心价值：把多阶段 Agent/GPT 工作流变成可冷启动、可迁移、可审核、可交接的 evidence-first 框架。

关键仓库：
- agent-acceptance（本仓库）：规范验收层
- devframe-control-plane：编排控制层
- dev-frame-opencode：执行层

---

## 2. 三层架构

三层架构：
1. agent-acceptance（规范验收层）— 合约、schema、validator、GPT review 模板、pre-commit/pre-push gate
2. devframe-control-plane（编排控制层）— pipeline runner、state machine、submission adapter、CDP bridge、CLI
3. dev-frame-opencode（执行层）— 具体代码修改和测试运行

当前 agent-acceptance 测试 232 PASS（170 baseline + 62 new），devframe-control-plane 测试 65 PASS，全线绿色。

---

## 3. 当前阶段

当前阶段：治理基础设施完善，上下文压缩层已部署。CONTEXT-COMPRESSION-A1 + AI-GUARD-STAGED-SCOPE-A1 + GPT-REVIEW-QUEUE-A1 已 committed。247 tests PASS。ai_guard staged-only 模式生效。7 个 dirty baseline 文件受保护（未提交）。

---

## 4. 最近 Accepted 任务

最近 GPT-accepted 任务（2026-06-07）：
- GROUP-01: AA-FLOW-RUNNER-CONTRACT-BACKFILL — contracts + policies + tests (140 files)
- GROUP-02: PAPER-A3-VALIDATOR-RESIDUAL — validate_paper_task.py + test (2 core files)
- GROUP-03: MEMORY-A2-COMPILER-OUTPUT — frozen memory compiler output
- GROUP-04: AGENT-RUNTIME-CAPABILITY-CLEANUP — blackboard cleanup + capability inventory
- GROUP-05: CHAIN-EVIDENCE-HARDENING R3 — ai_guard + go_evidence + chain-evidence schema
- GROUP-06: VALIDATE-WORKFLOW-CLOSURE-CONTROL-PLANE-PATTERN — workflow closure validator
- WorkQueue: specialized batches + Run-WorkQueue propagation
- REPO-CODE-VERIFICATION-R3: remote origin/master clean for accepted scope
- CONTEXT-COMPRESSION-A1: privacy-safe context compression layer (accepted R6, committed)
- AI-GUARD-STAGED-SCOPE-A1: ai_guard staged-only fix (accepted R4, committed)
- GPT-REVIEW-QUEUE-A1: review queue with lifecycle (accepted_with_limitation, committed)

---

## 5. 当前开放风险

当前开放风险：
1. 7 个 dirty baseline 文件受保护（未提交，known_dirty_worktree_excluded）
2. 本地 dirty worktree 未被清理（不得 whole-dirty-tree commit）
3. REVIEW-TEMPLATE-V2 已 push 但未 GPT 审查（需补审）
4. CDP 通信依赖 Chrome --remote-debugging-port=9222 运行

---

## 6. 下一步推荐任务

推荐下一步：等待 GPT 授权下一个任务（如 PROJECT-HISTORY-BOOT-MEMORY-SYNC-A1 已完成）
- ai_guard 已修复，staged-only 模式生效
- review_queue.py 可用于后续 GPT review 提交管理
- 不得 whole-dirty-tree commit，不得触碰 dirty baseline

---

## 7. 绝对安全边界

绝对安全边界（永久禁止）：
- guard removal
- evidence cleanup/deletion/movement/renaming
- cookies/session/browser profile 读取
- 真实用户数据提交
- CURRENT_STATE/CURRENT_ROUTE 非授权修改
- DECISION_LEDGER 非授权写入
- whole-dirty-tree commit
- 论文正文、raw transcript、private text 写入 memory
- 跳过 GPT 审查声称 closed

---

## 8. 冷启动读取顺序

新 agent 冷启动读取顺序：
1. BOOT_CONTEXT.md（本文档）— 了解项目身份、架构、当前状态、安全边界
2. memory/index.md — 按需检索具体话题记忆
3. PROJECT_HISTORY.md — 仅当需要完整历史时（不推荐每次加载）
4. CLAUDE.md — Agent 行为协议
5. docs/WORKFLOW_AUDIT_LEDGER.yaml — 任务状态机记录

---

> Boot context 到此结束。需要更多上下文？读取 memory/index.md（记忆索引）或 PROJECT_HISTORY.md（完整项目历史）。
> 新 agent 冷启动读取顺序：BOOT_CONTEXT.md → memory/index.md → 按需深入 memory/tasks/ 或 PROJECT_HISTORY.md。不再使用 HANDOFF.md 交接。
