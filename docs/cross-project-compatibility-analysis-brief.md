# 跨项目兼容性深度分析：agent-acceptance ↔ dev-frame / test-frame

> 提交给网页版深度分析 | 2026-05-30
> 源项目：D:\agent-acceptance (RD2100 Agent Runtime v2)
> 版本：Phase 0-5 完成，Phase 6C 阻塞，open code 1.15.12

---

## 一、背景

RD2100 Agent Runtime (agent-acceptance) 是一个 AI agent 治理运行时，通过 SADP 协议（Gate 0 → TaskSpec → Execute → ExecutionReport → Plan Auditor）管理 agent 行为。它与两个外部项目有集成关系：

| 项目 | 路径 | 角色 | 当前阶段 | 状态 |
|------|------|------|----------|------|
| **dev-frame** | D:\dev-frame | 编排适配器候选 | R3 adapter_dry_run | 禁止执行，只读 |
| **test-frame** | D:\test-frame | 证据提供者候选 | R2 evidence provider | 禁止执行，历史数据 only |

两个 frame 都不是 active executor，所有执行被禁止。集成方式是 agent-acceptance 单方面定义 8 个核心数据契约（TaskSpec, RunSpec, EvidenceIndex, GateResult, ExecutionReport, SkillIntakeRecord, ToolRiskRecord, MemoryUpdateRecord），frame 作为候选生产者和消费者被引用。

## 二、核心问题

**agent-acceptance 是否兼容 dev-frame 和 test-frame 的后续迭代升级？**

当前回答：**不兼容。** 原因有三层。

### 层 1：硬路径耦合

agent-acceptance 文档中大量硬编码绝对路径：

- D:\dev-frame\ai-workflow-hub
- D:\dev-frame\smoke_test.py
- D:\test-frame\evidence
- D:\test-frame\aggregator
- D:\test-frame\attribution

integration-contracts.md 已经记录了历史路径漂移：D:\devFrame vs D:\dev-frame。当前无自动检测机制。

### 层 2：单方面契约，无版本协商

8 个核心数据契约完全由 agent-acceptance 单方面定义。dev-frame 和 test-frame：
- 不感知这些契约的存在
- 不承诺遵守任何 schema
- 没有版本号字段
- 没有兼容性声明

如果 dev-frame 未来产出自己的 TaskSpec 格式，两边直接断裂。

### 层 3：阶段状态耦合

agent-acceptance 的组件矩阵按具体文件路径 + 当前阶段状态硬编码：

`yaml
# dev-frame-adapter-spec.md
ai-workflow-hub:
  R3 Access: read_only
  R3 Status: design_only
  Key Constraint: no execution

# test-frame-evidence-provider.md
aggregator/:
  R2 Access: forbidden
  R2 Status: human_gated
`

如果 dev-frame 独立升级（比如 R3 → R4，允许执行），agent-acceptance 里的禁止列表不会自动更新——要么过松（安全风险），要么过紧（阻塞合法操作）。

## 三、缺失的兼容机制（7 项）

| # | 缺失项 | 具体表现 | 风险等级 |
|---|--------|----------|----------|
| 1 | **Schema version 字段** | 8 个契约无 version，消费者无法识别格式变更 | 高 |
| 2 | **Frame manifest** | dev-frame/test-frame 无 manifest 声明自己的版本和接口 | 高 |
| 3 | **兼容矩阵** | 不知道哪些版本组合经过验证 | 中 |
| 4 | **路径注册表** | 硬编码路径无中心注册、无变更检测 | 中 |
| 5 | **契约协商协议** | 单方面定义，对方无义务遵守 | 高 |
| 6 | **阶段同步机制** | 各 frame 独立升级，agent-acceptance 无感知 | 中 |
| 7 | **弃用策略** | 旧契约/旧路径无生命周期管理 | 低 |

## 四、需要分析的 5 个关键问题

### Q1：最小兼容契约应该长什么样？

如果只能加最少的东西来解决这个问题，应该加什么？

当前候选：
- 给 8 个契约各加一个 ersion: "1.0" 字段
- 给 dev-frame 和 test-frame 各创建一个 rame-manifest.yaml：
  `yaml
  frame: dev-frame
  version: 1.0.0
  compatible_contract_versions:
    TaskSpec: "1.0"
    EvidenceIndex: "1.0"
    GateResult: "1.0"
  paths:
    ai-workflow-hub: D:\dev-frame\ai-workflow-hub
    smoke_test: D:\dev-frame\smoke_test.py
  `
- agent-acceptance 在 Gate 0 时校验 manifest 兼容性

这是否足够？有什么遗漏？

### Q2：版本协商应该推还是拉？

- **推模式**：frame 升级时主动通知 agent-acceptance（需要 frame 感知 agent-acceptance 的存在）
- **拉模式**：agent-acceptance 在 Gate 0 时主动检查 frame 的 manifest（frame 不需要知道 agent-acceptance 的存在）

当前 frame 根本不知道 agent-acceptance 存在。拉模式是唯一可行的，但代价是：如果 frame 做了不兼容变更，agent-acceptance 要等到下次 Gate 0 才发现。这个代价是否可以接受？

### Q3：契约演进时如何不破坏旧消费端？

如果 TaskSpec v2 新增了必填字段，所有还在用 v1 的消费端都会断裂。常见策略：

- **只增不减**：新字段只加 optional，永远不删旧字段
- **并行版本**：同时维护 v1 和 v2，给消费端迁移窗口
- **消费端适配器**：agent-acceptance 内部做版本转换

哪个策略最适合这个三项目的场景？

### Q4：路径漂移能否自动化检测？

path-drift-register.md 记录了历史漂移但只是文档。能否做成自动化？

候选方案：
- Git hook 检测跨项目路径引用
- 定期 diff frame 目录结构 vs agent-acceptance 中的路径引用
- frame manifest 中的 paths 作为 source of truth，agent-acceptance 引用的路径必须匹配

### Q5：这个问题的优先级应该怎么排？

当前 agent-acceptance Phase 0-5 已完成，Phase 6C 阻塞（等人工给 source URL）。dev-frame 和 test-frame 都没有在活跃开发。

在什么条件下，这个兼容性问题会从"技术债务"升级为"阻塞风险"？

候选触发条件：
- dev-frame 或 test-frame 开始有新的 commit
- agent-acceptance 推进到需要 frame 参与的阶段
- 任一 frame 的文件结构发生变化
- 新的集成项目加入

## 五、当前证据清单

| 文件 | 关键内容 |
|------|----------|
| integration-contracts.md | 8 个契约定义 + 系统集成附注（含历史路径漂移记录） |
| dev-frame-adapter-spec.md | R3 适配器：15 个禁止操作，按路径列组件矩阵 |
| 	est-frame-evidence-provider.md | R2 证据提供者：23 个禁止操作，9 组件矩阵 |
| 	est-frame-attribution-alignment.md | 归因对齐契约：5 个反模式，NOT ALIGNED 状态 |
| sourcelock-contract.md | 外部 skill 的 SourceLock 记录含 SHA256 hash（可参考） |
| path-drift-register.md | 记录了历史路径漂移 D:\devFrame → D:\dev-frame |
| esource-integration-open-items.md | 10 个开放项，无兼容性相关 |

## 六、请求的分析产出

请网页版针对以上 5 个问题（Q1-Q5）给出深度分析，并：

1. 判断当前架构在兼容性方面的短板优先级
2. 给出最小可行的兼容契约设计（具体字段和校验逻辑）
3. 评估拉模式版本协商在这个三项目场景下的可行性
4. 给出契约演进策略建议（只增不减 vs 并行版本 vs 适配器）
5. 设计自动化路径漂移检测的最小实现
6. 给出触发条件：什么时候这个问题必须解决

---

> 完整上下文文件位于 D:\agent-acceptance\docs\agent-runtime\
> 核心文件：integration-contracts.md, dev-frame-adapter-spec.md, test-frame-evidence-provider.md, test-frame-attribution-alignment.md, sourcelock-contract.md
