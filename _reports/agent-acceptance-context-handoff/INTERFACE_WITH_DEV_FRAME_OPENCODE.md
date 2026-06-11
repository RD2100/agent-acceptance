# INTERFACE_WITH_DEV_FRAME_OPENCODE

> Generated: 2026-06-02
> Purpose: 定义 agent-acceptance 与 dev-frame-opencode 之间的职责边界、接口格式、消费方式

## 1. 职责边界

### agent-acceptance（规范层）
- 定义 acceptance criteria（验收标准）
- 定义 gate rules（门控规则）
- 定义 decision schema（决策格式）
- 定义 human_required 分类
- 定义 stage gate 判定条件
- 定义 Issue Contract / Ledger merge / Finalizer blocking 语义
- 定义什么条件下 accepted / blocked / human_required
- **不负责**：本地执行、打包、测试、Chrome CDP、GPT reply monitor

### dev-frame-opencode（执行层）
- 本地执行任务
- 收集测试证据
- 生成 evidence pack
- Chrome CDP handoff
- GPT reply monitor
- 多轮 review loop
- 读取 agent-acceptance 的规范并遵守
- **不负责**：定义验收标准、伪造 baseline、绕过 acceptance gate

## 2. dev-frame-opencode 应读取的 agent-acceptance 文件

| 优先级 | 文件 | 用途 |
|--------|------|------|
| P0 | `rules/core.md` | 硬停止规则，禁止的操作 |
| P0 | `rules/git.md` | Git安全规则 |
| P0 | `docs/agent-runtime/runtime-invariants.md` | 40条不变量，P0违规=BLOCKED |
| P1 | `docs/agent-runtime/verification-gates.md` | P0-P3 gate定义 |
| P1 | `docs/agent-runtime/reviewer-playbook.md` | 评审流程，human_required判定 |
| P1 | `docs/agent-runtime/authority-matrix.md` | 谁可以产生什么合约 |
| P2 | `docs/agent-runtime/integration-contracts.md` | 8个核心数据合约格式 |
| P2 | `schemas/agent-runtime/gate-result.schema.json` | GateResult JSON格式 |
| P2 | `schemas/agent-runtime/execution-report.schema.json` | ExecutionReport JSON格式 |

## 3. agent-acceptance 应输出的判定

### 3.1 当前已有的输出格式

| 输出 | 格式 | 消费者 |
|------|------|--------|
| GateResult | JSON (gate-result.schema.json) | Reviewer, dev-frame |
| ExecutionReport | JSON (execution-report.schema.json) | Human reviewer, plan agent |
| AuditRecord | YAML (audit-record.schema.md) | Plan Auditor |
| Reviewer Decision | Markdown (reviewer-playbook.md template) | Human |
| SessionLedger | YAML (session-ledger.schema.md) | Plan Auditor |

### 3.2 需要新增的输出格式

| 输出 | 用途 | 消费者 |
|------|------|--------|
| StageGateResult | 阶段推进判定 | dev-frame-opencode loop harness |
| AUTO_DECISION_LOG | 自动决策日志 | GPT (复审), dev-frame |
| human_required_taxonomy | 结构化人工分类 | dev-frame (判断是否需要暂停) |
| Issue Contract | 问题契约 | GPT, dev-frame |

## 4. Stage Gate 接口设计建议

### 4.1 输入
```yaml
stage_gate_input:
  current_stage: S2 | S3 | M4-A
  gate_results:
    - gate_id: string
      level: P0 | P1 | P2 | P3
      result: pass | fail | warning | blocked | skipped
  execution_reports:
    - report_id: string
      status: pass | fail | blocked
  evidence_chain:
    - artifact_path: string
      freshness: current | historical | stale
  changed_files: [path, ...]
  reviewer_decision: pass_to_review | needs_revision | blocked | human_required | null
```

### 4.2 输出
```yaml
stage_gate_result:
  stage_id: S2 | S3 | M4-A
  decision: advance | hold | block | escalate
  reason: string
  allow_next_stage: true | false
  s3_allowed: true | false  # 针对S2→S3推进
  auto_decision: true | false  # 是否为自动判定
  human_required_categories: [direction | sensitive_op | irreversible | evidence_uncertainty] | []
  auto_decision_log_ref: string  # 指向 AUTO_DECISION_LOG
```

### 4.3 稳定字段（loop parser需要）
- `decision` — enum，稳定不变
- `allow_next_stage` — boolean
- `auto_decision` — boolean，区分自动/人工
- `reason` — string，机器可读

## 5. Decision Parser 稳定性要求

当前存在的多个决策格式**需要统一**：

| 现有格式 | 决策值 | 问题 |
|---------|--------|------|
| GateResult.result | pass/fail/warning/blocked/skipped | 没有 advance/hold 语义 |
| AuditRecord.decision | pass/block/escalate | 没有 "advance" 语义 |
| Reviewer decision | pass_to_review/needs_revision/blocked/human_required | 面向评审，不是面向阶段推进 |
| ExecutionReport.status | draft/submitted/reviewed/accepted/rejected | 报告状态，不是阶段推进决策 |

**建议**: 新增 `stage_gate_decision` schema，统一阶段推进判定，不与现有决策格式冲突。

## 6. Loop Harness 消费方式

dev-frame-opencode 的 loop harness 应该：

1. **读取** agent-acceptance 的 `stage_gate_result`（JSON/YAML）
2. **解析** `decision` 字段
3. **如果** `decision = advance` 且 `auto_decision = true` → 自动进入下一阶段
4. **如果** `decision = hold` 且 `human_required_categories` 非空 → 暂停，等待人工输入
5. **如果** `decision = block` → 终止，报告阻塞原因
6. **记录** AUTO_DECISION_LOG（每轮必需）
7. **注意**: loop harness 自己不做 acceptance criteria 判定，它只消费 agent-acceptance 的判定结果

## 7. 当前接口缺口

| 缺口 | 影响 |
|------|------|
| 没有 stage gate 概念 | dev-frame 无法判断是否可以进入下一阶段 |
| 没有 auto_decision 标识 | loop harness 不知道是否可以自动推进 |
| 没有 human_required 分类 | loop harness 不知道暂停原因属于哪类 |
| 没有 AUTO_DECISION_LOG | GPT 复审时缺乏自动决策依据 |
| 多套决策格式不统一 | parser 需要处理多种格式，维护成本高 |
