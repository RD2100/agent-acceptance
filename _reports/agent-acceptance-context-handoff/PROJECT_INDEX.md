# PROJECT_INDEX — agent-acceptance Context Handoff

> Generated: 2026-06-02
> Purpose: 项目结构摘要，关键文件路径与用途

## 1. 项目结构摘要

```
D:\agent-acceptance\                    <- 规范根目录
  AGENTS.md                              <- 导航入口，Hard Stops，文档地图
  README.md                              <- 项目概述，分层说明，快速开始
  rules/                                 <- 7个规则文件，44条规则
    README.md                            <- 规则索引+优先级系统
    core.md                              <- 运行时核心 (6条P0规则)
    coding.md                            <- 代码生成 (7条)
    security.md                          <- 安全硬停止 (8条)
    review.md                            <- 评审与证据 (6条)
    git.md                               <- Git安全 (6条)
    research.md                          <- 只读探索 (5条)
    frontend.md                          <- 前端规范 (6条)
  docs/agent-runtime/                    <- 运行时文档 (~85个文件)
    operating-model.md                   <- 执行层、Tier、生命周期
    integration-contracts.md             <- 8个核心数据合约
    verification-gates.md                <- P0-P3门控层级
    sub-agent-dispatch-protocol.md       <- SADP v1.0 多Agent调度
    session-ledger.schema.md             <- 会话账本schema
    audit-record.schema.md               <- Plan Auditor输出schema
    reviewer-playbook.md                 <- 评审者手册
    runtime-invariants.md                <- 40条运行时不变量
    capability-inventory.md              <- 28个能力清单
    authority-matrix.md                  <- 权限矩阵
    fmea-risk-analysis.md                <- FMEA风险分析
    resource-risk-matrix.md              <- 资源风险矩阵
    governance-manifest.md               <- 治理清单（历史参考）
    handoff-to-next-agent.md             <- Agent交接文档
    next-agent-handoff.md                <- 冷启动交接
    ... (另有65+文件)
  schemas/agent-runtime/                 <- JSON Schema
    task-spec.schema.json
    execution-report.schema.json
    gate-result.schema.json
    evidence-index.schema.json
    review.schema.json
    safety-report.schema.json
    chain-evidence.schema.json
    ... (共12个schema)
  schemas/resource-integration/          <- 资源集成schema (10个)
  hooks/                                 <- 治理钩子
    pre-edit.governance.ps1              <- 活跃钩子
    register-hooks.ps1                   <- 注册脚本
    pre-commit.governance.ps1
    pre-push.governance.ps1
    sealed-files-manifest.json           <- 密封文件清单
  scripts/                               <- PowerShell运行器
    Run-Smoke.ps1, Run-Batch.ps1, Run-AllQueues.ps1 等
  agent-workqueue/                       <- 工作队列定义
  templates/runtime-bootstrap/           <- 引导模板
  runs/                                  <- 历史运行记录
  audit/                                 <- 审计记录
  quarantine/                            <- 隔离区
  skills-inbox/                          <- 技能摄入区
```

## 2. 关键文件分类

### 2.1 规范层文件

| 文件 | 用途 |
|------|------|
| `rules/core.md` | 核心运行时规则 (core-001 ~ core-008) |
| `rules/review.md` | 评审与证据规则 (review-001 ~ review-006) |
| `rules/security.md` | 安全规则 (sec-001 ~ sec-008) |
| `rules/git.md` | Git安全规则 (git-001 ~ git-006) |
| `rules/coding.md` | 代码规范 (code-001 ~ code-007) |
| `docs/agent-runtime/verification-gates.md` | P0-P3门控定义 |
| `docs/agent-runtime/runtime-invariants.md` | 40条运行时不变量 |
| `docs/agent-runtime/reviewer-playbook.md` | 评审者判定手册 |
| `docs/agent-runtime/authority-matrix.md` | 权限矩阵 |
| `docs/agent-runtime/operating-model.md` | 执行模型 |

### 2.2 Schema层文件

| 文件 | 用途 |
|------|------|
| `schemas/agent-runtime/gate-result.schema.json` | 门控结果 |
| `schemas/agent-runtime/execution-report.schema.json` | 执行报告 |
| `schemas/agent-runtime/task-spec.schema.json` | 任务规格 |
| `schemas/agent-runtime/review.schema.json` | 评审裁决 |
| `schemas/agent-runtime/chain-evidence.schema.json` | 证据链 |

### 2.3 Stage Gate相关文件

| 文件 | 与Stage Gate的关系 |
|------|-------------------|
| `docs/agent-runtime/verification-gates.md` | 定义P0-P3门控层级，但**不包含S2/S3/M4-A阶段概念** |
| `docs/agent-runtime/reviewer-playbook.md` | 定义评审判定（含`human_required`），但**不包含自动阶段推进** |
| `docs/agent-runtime/sub-agent-dispatch-protocol.md` | 定义SADP Finalizer gate，但**不包含阶段gate自动推进** |

### 2.4 测试文件

| 文件 | 用途 |
|------|------|
| `scripts/tests/Test-DocsExist.ps1` | 文档存在性测试 |
| `scripts/tests/Test-GovernanceManifest.ps1` | 治理清单测试 |
| `scripts/tests/Invoke-GovernanceCanarySuite.ps1` | 治理金丝雀套件 |
| `scripts/checks/Test-BatchReferences.ps1` | 批处理引用检查 |
| `scripts/checks/Test-KeyScan.ps1` | 密钥扫描 |
| `scripts/checks/Test-ProtectedPaths.ps1` | 保护路径检查 |
| `docs/agent-runtime/negative-acceptance-tests.md` | 30个负面验收测试 |
| `docs/agent-runtime/negative-test-fixtures/` | 负面测试固件 |

## 3. 关键发现：项目缺少的概念

当前 agent-acceptance 项目**明确不包含**以下概念：

| 概念 | 存在性 |
|------|--------|
| S2/S3/M4-A 阶段划分 | 不存在 |
| Stage gate 自动推进 | 不存在 |
| `s3_allowed` 字段 | 不存在 |
| `allow_next_stage` 字段 | 不存在 |
| AUTO_DECISION_LOG | 不存在 |
| Issue Contract | 不存在 |
| Ledger merge | 不存在 |
| Finalizer blocking (独立于SADP) | 仅在 SADP 0.R.3 中存在 |
| review-issues.json | 不存在 |
| human_required 结构化分类 | 仅作为评审决策四选一存在，无子分类 |

## 4. 现有项目阶段

当前项目使用**Phase 0-5**阶段命名：
- Phase 0: Bootstrap
- Phase 1: 运行模型+合约+门控
- Phase 2: 资源清单+路径漂移
- Phase 3: 内存架构+工具策略
- Phase 4: FMEA+STRIDE+不变量
- Phase 5: 负面测试+评审手册
- Phase 6A-F: 外部资源审查 (部分完成)

这些Phase与用户所说的S2/S3/M4-A是**不同维度的概念**。
