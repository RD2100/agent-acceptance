# CONFLICTS_WITH_USER_POLICY — 当前规则与用户新边界的冲突

> Generated: 2026-06-02
> Purpose: 系统检查当前 agent-acceptance 规则是否与用户新边界矛盾

## 用户新边界（引用自任务描述）

1. 阶段推进本身不需要逐次询问用户
2. 只要 accepted 条件满足，且 stage gate clean，dev-frame-opencode 可以自动进入下一阶段
3. 真正需要询问用户的事项仅限：
   - 方向性决策
   - 删除/清理/覆盖/移动/重命名文件
   - git reset/clean/rebase/force push 等不可逆操作
   - 修改核心治理规则或改变项目路线
   - 修改 forbidden/high-risk 文件
   - 无法由现有证据证明的历史事实

## 冲突检查结果

### 冲突1: "进入S3必须人工确认" — 溯源

**结论**: 当前 agent-acceptance **不存在** "进入S3必须人工确认" 的显式规则。
原因：当前项目根本没有S2/S3/M4-A阶段概念。

但存在**等效冲突**：
- `reviewer-playbook.md` Gate Decision Tree 最终检查 "Is a human decision needed? → human_required" 使得**所有待决策事项都可能被归入 human_required**
- `authority-matrix.md` 声明 agent-acceptance 的 Auto-Advance Gate 权限是 "Yes (with reviewer)"，即不能纯自动推进
- `operating-model.md` Tier 2 要求 "Must escalate to human"

**冲突等级**: 结构性冲突。当前架构没有纯自动推进路径。

### 冲突2: "accepted后只写allow_next_stage=true，不自动推进" — 溯源

**结论**: 当前 agent-acceptance **不存在** `allow_next_stage` 字段。该字段是用户期望的新增项。

当前接近的模式：
- SADP §3.3b 的 `decision: accept → dispatch next task`
- 但这是**任务级派发**，不是**阶段级推进**

**冲突等级**: 需要新增，不是修改。

### 冲突3: human_required 过于宽泛

当前 `human_required` 在 `reviewer-playbook.md` Gate Decision Tree 中作为**兜底项**出现：
> "Is a human decision needed? → human_required"

这意味着：
- 任何模糊情况都可能被归入 human_required
- 没有区分类别（方向决策 vs 敏感操作 vs 证据不确定）
- 没有定义哪些情况可以 auto decision

**冲突等级**: 需要重构 human_required 分类。

### 冲突4: 缺少 sensitive operation 分类

用户期望区分:
- 需要人工确认的: 方向决策、敏感操作、不可逆操作、治理规则修改、forbidden文件修改
- 可自动决定的: accepted + clean gate 后的阶段推进

当前项目对这些操作的约束分布在多处：
- `core.md` core-001 (destructive git) → 需要人工
- `core.md` core-003 (phase boundary) → P0 硬停止
- `git.md` git-002 (destructive commands) → 需要人工
- `rules/security.md` → P0/P1 规则
- 但没有**集中式的 sensitive operation 分类**

**冲突等级**: 需要新增分类。

### 冲突5: 缺少 AUTO_DECISION_LOG

用户期望每轮 loop 自动产生 AUTO_DECISION_LOG。当前项目中不存在此概念。

**冲突等级**: 需要全新创建。

### 冲突6: 没有区分"证据真实性问题"和"普通报告冲突"

当前 `reviewer-playbook.md` 将两者混在同一决策树中：
- "fake green → blocked"
- "incomplete but honest evidence → needs_revision / human_required"

但没有区分：
- 证据链断裂但无恶意（证据真实性问题）
- 报告声明与证据不一致（报告冲突）
- 证据存在但过期（时效性问题）

**冲突等级**: 需要细化 classification。

## 需要修改的规则

| 规则位置 | 需要修改的内容 | 优先级 |
|---------|--------------|--------|
| `reviewer-playbook.md` §10 | Gate Decision Tree 末尾兜底 human_required 需要细化分类 | P0 |
| `reviewer-playbook.md` §10 | 新增 auto decision 分支（accepted + clean gate → auto advance） | P0 |
| `authority-matrix.md` | "Auto-Advance Gate: Yes (with reviewer)" 需要放宽为 "Yes (auto when clean)" | P1 |
| `verification-gates.md` | 需要新增 stage gate 概念（不同于 P0-P3 quality gate） | P1 |
| `operating-model.md` | Tier 2 escalation 需要补充自动推进例外 | P2 |

## 不需要修改的规则

| 规则 | 原因 |
|------|------|
| `rules/core.md` core-001 ~ core-008 | 这些是运行时硬停止，与stage gate不冲突 |
| `rules/security.md` sec-001 ~ sec-008 | 安全规则独立于阶段推进 |
| `rules/git.md` git-001 ~ git-006 | 不可逆操作仍然需要人工确认 |
| `rules/review.md` review-001 ~ review-006 | 证据规则仍然有效 |
| `runtime-invariants.md` INV-001 ~ INV-040 | 不变量仍然有效 |

## 需要新增的内容

| 新增项 | 说明 |
|--------|------|
| Stage gate 定义 (S2/S3/M4-A) | 全新概念，定义阶段间推进条件 |
| Stage gate schema | JSON Schema，定义 `stage_gate_result` 数据结构 |
| AUTO_DECISION_LOG schema | 每次 loop 的自动决策日志 |
| human_required 分类 | 结构化分类：方向决策/敏感操作/不可逆操作/证据不确定性 |
| sensitive operation 分类 | 哪些操作需要人工，哪些可自动 |
| Issue Contract | 问题追踪契约 |
| review-issues.json schema | 评审问题追踪文件 |

## 解释口径问题（不需要改代码）

以下情况是解释口径问题，不是规则冲突：

1. **Phase 0-5 boundary** — 这是项目构建阶段，与用户说的 S2/S3 执行阶段是不同维度，不需要改名
2. **Tier 2 escalation** — 这是工作队列的风险分级，与 stage gate 是不同概念
3. **SADP Finalizer blocking** — 这是 @go 运行的证据验证，与阶段推进是不同层面
