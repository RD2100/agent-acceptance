# HUMAN_REQUIRED_TAXONOMY_CURRENT — 当前 human_required 分类

> Generated: 2026-06-02
> Purpose: 分析当前 human_required 使用方式，并与用户期望的分类体系对比

## 1. 当前 human_required 使用位置

### 1.1 reviewer-playbook.md Gate Decision Tree (§8)

以下情况触发 `human_required`:

| 触发条件 | 语义 | 属于用户分类的哪类？ |
|---------|------|-------------------|
| 多个 source-of-truth 根且无决策 | 配置模糊 | 方向性决策 |
| 预状态仅在写入后存在（pre-status missing, post only） | 证据缺失 | 证据真实性问题 |
| 模糊的脏归属（unclear dirty attribution） | 归属不清 | 证据真实性问题 |
| 未预期的变更文件 | 范围外变更 | 敏感操作 |
| 未归属的变更（unattributed change） | 归属不清 | 证据真实性问题 |
| 不完整但诚实的证据 | 证据不完整 | 证据真实性问题 |
| 最终兜底: "Is a human decision needed?" | 通用兜底 | **未分类** — 过于宽泛 |

### 1.2 reviewer-playbook.md Step 2 (Source of Truth)

- Wrong canonical root → `blocked`
- Missing source_of_truth_ref → `needs_revision`
- Multiple roots with no decision → `human_required` (方向性决策)

### 1.3 reviewer-playbook.md Step 3 (Pre-Batch Git Status)

- Pre-status after writes only → `human_required` (证据真实性问题)

### 1.4 reviewer-playbook.md Step 5 (Approved Outputs)

- Unexpected changed file → `blocked` or `human_required` (敏感操作)

### 1.5 reviewer-playbook.md Step 5 (Changed Files Attribution)

- Unattributed change → `human_required` (证据真实性问题)

## 2. 当前 human_required 的问题

### 2.1 无结构化分类
当前 human_required 是一个**单一标签**，不携带类别信息。消费者（dev-frame loop harness）无法判断：
- 这需要方向性决策？（需要GPT输入）
- 这是敏感操作确认？（需要用户确认）
- 这是证据不确定？（可以重试收集证据）

### 2.2 兜底过于宽泛
Gate Decision Tree 最终检查 "Is a human decision needed? → human_required"
这意味着任何未明确匹配的情况都可能导致 human_required，包括本应自动推进的情况。

### 2.3 与 blocked 的边界模糊
多处使用 "blocked or human_required" 的二选一，没有清晰的判定标准。

## 3. 用户期望的 human_required 分类

根据用户新边界，真正需要 human confirmation 的仅限：

| 类别 | 描述 | 当前是否覆盖 |
|------|------|------------|
| 方向性决策 | 架构选择、技术路线、目标变更 | 部分覆盖（多根无决策） |
| 删除/清理/覆盖/移动/重命名文件 | 任何文件毁灭性操作 | **未覆盖**（在 git.md 中作为 git 规则，但未作为 human_required 类别） |
| git reset/clean/rebase/force push | 不可逆 git 操作 | **未覆盖**（在 git.md 中作为 git 规则，但未作为 human_required 类别） |
| 修改核心治理规则 | 改变项目路线 | **未覆盖** |
| 修改 forbidden/high-risk 文件 | 受保护文件修改 | 部分覆盖（unexpected changed file → blocked/human_required） |
| 无法由现有证据证明的历史事实 | pre-S2 baseline, dirty worktree 来源等 | 部分覆盖（unattributed change → human_required） |

## 4. 用户期望的可自动决策事项

| 事项 | 当前如何处理 | 应该如何处理 |
|------|------------|------------|
| accepted + clean gate → 下一阶段 | 无此概念 | 自动推进 + 记录 AUTO_DECISION_LOG |
| 普通gate失败（非P0） | FAILED → 需要修复 | 自动重试或报告 |
| 证据完整且无冲突 | pass_to_review → 等待评审 | 自动通过（如已满足auto条件） |

## 5. 建议的 human_required 分类体系

```yaml
human_required_taxonomy:
  direction_decision:        # 方向性决策
    - architecture_choice
    - technology_roadmap
    - goal_change
  sensitive_operation:       # 敏感操作
    - file_deletion
    - file_rename_or_move
    - file_overwrite
    - directory_cleanup
  irreversible_operation:    # 不可逆操作
    - git_reset
    - git_clean
    - git_rebase
    - git_force_push
    - git_branch_delete
  governance_modification:   # 治理修改
    - core_rule_change
    - acceptance_criteria_change
    - project_roadmap_change
  forbidden_file_access:     # 禁止文件访问
    - high_risk_file_modify
    - sealed_file_modify
  evidence_uncertainty:      # 证据不确定性
    - pre_baseline_unknown
    - dirty_worktree_source_unknown
    - historical_fact_unverifiable
  other:                     # 兜底（应尽量少用）
    - uncategorized
```

## 6. 可能被误归为 human_required 的事项

| 事项 | 当前可能被归入 | 正确归类 |
|------|-------------|---------|
| Gate clean but reviewer hasn't signed off | 兜底 human_required | 应自动推进 (auto_decision) |
| P2 WARNING 但无 P0/P1 失败 | 可能被归入 blocked | 应允许推进 (WARNING = non-blocking) |
| 证据完整但格式不规范 | needs_revision | 应自动推进 + 记录格式问题 |
| Tier 2 工作队列 | 必须升级人工 | 需要区分 Tier 2 风险和阶段推进 |
