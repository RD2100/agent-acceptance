# CURRENT_RULES_SUMMARY — 当前规范内容摘要

> Generated: 2026-06-02
> Purpose: 整理 agent-acceptance 当前所有与 accepted/blocked/human_required/stage gate 相关的规则

## 1. Accepted 判定条件

当前项目对 "accepted" 的定义分散在多处：

### 1.1 ExecutionReport 状态
来自 `integration-contracts.md` Contract 5:
- `status` enum: `draft`, `submitted`, `reviewed`, `accepted`, `rejected`
- 从 `submitted` 变为 `accepted` 需要 **human reviewer** 操作
- INV-028 明确禁止 executor 自批准

### 1.2 SADP Plan Agent Review 判定
来自 `sub-agent-dispatch-protocol.md` §3.3b:
- `decision: accept | reject | request_revision`
- Accept条件: 所有gate PASS + regression PASS

### 1.3 Gate Result
来自 `verification-gates.md`:
- P0 PASS → continue. FAIL → BLOCKED
- P1 PASS → continue. FAIL → FAILED
- P2 PASS → continue. FAIL → WARNING
- P3 PASS → continue. FAIL → INFO

## 2. Blocked 判定条件

### 2.1 系统级 Blocked
- 任何 P0 硬停止违反 → BLOCKED
- 任何 P0 门控失败 → BLOCKED
- executor 自批准 → BLOCKED (INV-028)
- 假绿报告 → BLOCKED (INV-009)
- 脏基线修改 → BLOCKED (INV-004)
- Phase边界违反 → BLOCKED (INV-034)

### 2.2 SADP Audit Blocked
来自 `audit-record.schema.md`:
- 缺少 TaskSpec (SADP required) → block
- Gate 0 缺乏 inventory_evidence → block
- 缺少 ExecutionReport → block
- 变更文件未被 ExecutionReport 覆盖 → block
- 受保护文件被触碰但未报告 → block
- 累计触发绕过检测 → block

### 2.3 Finalizer Blocked
来自 SADP 0.R.3:
- reviewer artifacts 缺失 → blocked
- reviewer role 为 executor/fixer/coder → blocked
- reviewed inputs 不完整 → blocked
- P0/P1 finding 未解决 → blocked

## 3. Human Required 判定条件

当前 `human_required` **仅作为评审者决策四选一出现**。

来自 `reviewer-playbook.md` §10 Step 10:
- 允许的评审决策: `pass_to_review`, `needs_revision`, `blocked`, `human_required`

来自 Gate Decision Tree:
- 多个source-of-truth根且无决策 → `human_required`
- 预状态仅在写入后存在 → `human_required`
- 模糊的脏归属 → `human_required`
- 未预期的变更文件 → `blocked` 或 `human_required`
- 未归属的变更 → `human_required`
- 不完整但诚实的证据 → `needs_revision` 或 `human_required`
- 脏归属不明确 → `human_required`
- 最终检查: "Is a human decision needed? → human_required"

**关键发现**: `human_required` 是一个**无子分类的平坦标签**。没有区分"方向决策"与"敏感操作"与"证据不确定"，也没有结构化分类。

## 4. Stage Gate 规则

当前**不存在 stage gate 概念**。现有的是：

### 4.1 Gate Hierarchy (P0-P3)
来自 `verification-gates.md`:
```
P0: Security Gate → FAIL = BLOCKED
P1: Correctness Gate → FAIL = FAILED
P2: Quality Gate → FAIL = WARNING
P3: Completeness Gate → FAIL = INFO
```

### 4.2 Tier System
来自 `operating-model.md`:
- Tier 0: 自动执行
- Tier 1: 自动执行，记录警告
- Tier 2: 不自动执行，必须升级到人工

### 4.3 Phase 0-5 Boundary
来自 `AGENTS.md`:
- Phase 0-5 是一组**能力约束**（禁止安装、禁止写内存、禁止git提交等），不是阶段推进系统

## 5. S2/S3/M4-A 阶段关系

**不存在**。当前项目的 "Phase" 是项目构建阶段，与用户期望的 S2/S3/M4-A 执行阶段是不同维度。

## 6. allow_next_stage / s3_allowed / Finalizer Blocking

**均不存在**。当前唯一接近的是：

### 6.1 SADP 3.3b Plan Agent Review
- `decision: accept` → 派发下一个TaskSpec
- 但没有 "allow_next_stage" 或 "s3_allowed" 字段

### 6.2 SADP 0.R.3 Finalizer Gate
- `python tools/go_evidence.py finalize <run-evidence-dir>`
- 仅验证证据包结构，不决定阶段推进

### 6.3 Authority Matrix
来自 `authority-matrix.md`:
- agent-acceptance 的 "Auto-Advance Gate" 权限是 "Yes (with reviewer)"
- 意味着**不能无审查员自动推进**

## 7. 现有决策格式

### 7.1 GateResult (JSON Schema)
```json
{
  "gate_id": "g-001",
  "gate_level": "P0",
  "gate_name": "Security: No secrets",
  "result": "pass",
  "checked_at": "...",
  "details": "...",
  "evidence_ids": [...],
  "recommendation": "..."
}
```

### 7.2 Audit Record Decision
来自 `audit-record.schema.md`:
```yaml
decision: pass | block | escalate
```

### 7.3 Reviewer Decision
来自 `reviewer-playbook.md`:
```yaml
Decision: pass_to_review | needs_revision | blocked | human_required
```

### 7.4 ExecutionReport Status
来自 Contract 5:
```yaml
Status: draft | submitted | reviewed | accepted | rejected
```

**关键发现**: 没有统一的 "stage gate decision" schema。现有的多个决策格式各自独立，没有统一的阶段推进判定逻辑。

## 8. Issue Contract / Ledger Merge / Finalizer Blocking / review-issues.json

**均不存在**。这些概念是用户期望新增的，而非当前已有。

## 9. AUTO_DECISION_LOG

**不存在**。没有任何文件定义自动决策日志。

## 10. 总结：当前状态 vs 用户期望

| 用户期望的能力 | 当前存在性 | 差距 |
|--------------|-----------|------|
| accepted 判定 | 部分存在 (ExecutionReport status) | 没有与stage gate关联 |
| blocked 判定 | 完善 (P0/P1 gate + 不变量) | 没有与stage推进关联 |
| human_required 分类 | 存在但平坦 | 缺乏结构化子分类 |
| stage gate 自动推进 | 不存在 | 需要全新设计 |
| S2/S3/M4-A 阶段 | 不存在 | 需要全新定义 |
| AUTO_DECISION_LOG | 不存在 | 需要全新创建 |
| Issue Contract | 不存在 | 需要全新创建 |
| Ledger merge | 不存在 | 需要全新创建 |
| Finalizer blocking | 部分存在 (SADP) | 需要泛化到非@go场景 |
| review-issues.json | 不存在 | 需要全新创建 |
