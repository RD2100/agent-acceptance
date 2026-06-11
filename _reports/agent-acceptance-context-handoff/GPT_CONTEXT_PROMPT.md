# GPT_CONTEXT_PROMPT — 提交给 GPT 的主上下文说明

> 生成: 2026-06-02
> 目标: 让 GPT 基于真实 agent-acceptance 上下文判断规范层如何做最小修正

---

## 背景

我们正在搭建一个"计划—执行—审核—再计划—再执行"的自动化框架。

三层职责：

1. **GPT** — 计划生成、复审、仲裁、再计划
2. **agent-acceptance** — 规范层、验收层、gate层（本项目）
3. **dev-frame-opencode** — 执行层

当前任务是让 GPT 诊断 agent-acceptance 规范层，判断最小修正方案。

## 当前 agent-acceptance 项目状态

### 项目性质
- 项目是 RD2100 Agent Runtime v2，处于 Phase 0-5 引导阶段
- 已有完善的规则体系（7个规则文件，44条规则）
- 已有完善的合约体系（8个核心数据合约，12个JSON Schema）
- 已有 P0-P3 门控层级
- 已有 SADP 多Agent调度协议
- 已有 40 条运行时不变量
- 已有评审者手册（含 Gate Decision Tree）
- 已有权限矩阵

### 关键缺失（与用户期望的差距）

1. **没有 Stage Gate 概念** — 当前项目使用 Phase 0-5（项目构建阶段），没有 S2/S3/M4-A 执行阶段概念
2. **没有阶段自动推进机制** — reviewer-playbook 的 Gate Decision Tree 以 "Is a human decision needed? → human_required" 结尾作为兜底，没有 auto_advance 路径
3. **human_required 无结构化分类** — 仅作为评审决策四选一（pass_to_review / needs_revision / blocked / human_required），无子分类
4. **没有 AUTO_DECISION_LOG** — 没有任何文件定义自动决策日志
5. **没有 Issue Contract / Ledger merge / review-issues.json** — 这些概念均不存在
6. **多套决策格式不统一** — GateResult、AuditRecord、Reviewer Decision、ExecutionReport 各自使用不同的决策枚举
7. **权限矩阵要求 "Auto-Advance Gate: Yes (with reviewer)"** — 不允许纯自动推进

### 用户新边界

1. 阶段推进不需要逐次询问用户
2. accepted + stage gate clean → 自动进入下一阶段
3. 真正需要人工确认的仅限：
   - 方向性决策
   - 文件删除/覆盖/移动/重命名
   - git reset/clean/rebase/force push
   - 修改核心治理规则
   - 修改 forbidden/high-risk 文件
   - 无法由现有证据证明的历史事实

## 请求 GPT 判断的问题

基于以上上下文，请回答：

1. **agent-acceptance 当前哪些规则与用户新边界冲突？**
   特别检查 reviewer-playbook Gate Decision Tree 末尾兜底是否会导致一切未匹配情况进入 human_required。

2. **是否应将"进入下一阶段"从 human confirmation 改为 stage gate 自动判定？**
   如果是，stage gate 的判定逻辑应该是什么样的？

3. **human_required 应如何重新分类？**
   附带的 HUMAN_REQUIRED_TAXONOMY_CURRENT.md 中有建议的分类体系，请评审。

4. **AUTO_DECISION_LOG 应如何成为每轮 loop 的必需产物？**
   附带的 AUTO_DECISION_LOG_CURRENT_STATUS.md 中有建议的字段，请评审。

5. **dev-frame-opencode 后续应如何读取 agent-acceptance 的判定？**
   需要什么接口格式？Stage gate result 应如何设计？

6. **最小 patch scope 是什么？**
   附件 RECOMMENDED_MINIMAL_PATCH_SCOPE.md 给出了建议，请评审是否确实最小。

7. **哪些文件可以改，哪些不应改？**
   请审核建议的文件清单。

8. **哪些修改应留到 dev-frame-opencode 阶段？**

9. **哪些事项仍然需要用户确认？**

10. **额外发现：GPT Handoff 基础设施缺失**
    用户描述的 oracle_gpt_*.py 脚本、.opencode/skills/ 目录、Chrome CDP handoff 基础设施在 agent-acceptance 和 dev-frame 中都不存在。这是否应该作为 dev-frame-opencode 的构建任务？在基础设施就绪之前，规范层修正是否可以先行？

## 明确约束

请 GPT 在回答时遵守以下约束：

- **不要建议大重构**。agent-acceptance 的现有规则体系（P0-P3 gate、SADP、不变量、权限矩阵）已经很复杂，不要在现有基础上做大规模重组。
- **不要要求直接进入 S3**。当前任务是诊断规范层，不是推进执行阶段。
- **不要让 dev-frame-opencode 先改**。规范层的修正应先于执行层的实现。
- **新增优先于修改**。如果可以通过新增文件实现，优先新增而非修改现有文件。
- **保持向后兼容**。现有的 P0-P3 gate、SADP、不变量、权限矩阵应保持有效。

## 额外上下文：GPT Handoff 基础设施缺失

用户指示了 oracle_gpt_*.py 脚本和 .opencode/skills/ 路径，但经查这些文件在 agent-acceptance 和 D:\dev-frame 中**都不存在**。playwright 已安装但无可用的 handoff 脚本。这意味着：
- 当前无法自动提交上下文给 GPT
- 上下文包已生成为本地 zip，需手动提交
- GPT handoff 基础设施属于 dev-frame-opencode 的建设范围

## 附件清单

1. PROJECT_INDEX.md — 项目结构摘要
2. CURRENT_RULES_SUMMARY.md — 当前规范内容摘要
3. CONFLICTS_WITH_USER_POLICY.md — 规则冲突分析
4. INTERFACE_WITH_DEV_FRAME_OPENCODE.md — 接口设计建议
5. HUMAN_REQUIRED_TAXONOMY_CURRENT.md — human_required 分类分析
6. AUTO_DECISION_LOG_CURRENT_STATUS.md — AUTO_DECISION_LOG 缺口分析
7. RECOMMENDED_MINIMAL_PATCH_SCOPE.md — 最小修改建议
8. 关键规则文件副本（rules/core.md, rules/review.md, reviewer-playbook.md 等）
9. 关键 schema 文件副本
