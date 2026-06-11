# AUTO_DECISION_LOG_CURRENT_STATUS — 自动决策日志当前状态

> Generated: 2026-06-02
> Purpose: 分析 AUTO_DECISION_LOG 当前是否存在，如不存在则描述缺口和建议

## 1. 当前状态：不存在

**AUTO_DECISION_LOG 在 agent-acceptance 项目中没有任何定义、引用或实现。**

- `grep -ri "auto_decision" docs/ rules/ schemas/` → 0 results
- `grep -ri "AUTO_DECISION" docs/ rules/ schemas/` → 0 results
- `grep -ri "auto.decision" docs/ rules/ schemas/` → 0 results

## 2. 可部分替代的现有机制

虽然没有 AUTO_DECISION_LOG，但以下现有机制可以记录部分决策：

| 现有机制 | 记录内容 | 与 AUTO_DECISION_LOG 的关系 |
|---------|---------|---------------------------|
| SessionLedger | session_id, changed_files, taskspecs, sadp_required, audit_status | 覆盖 session 级元数据，但不记录阶段推进决策 |
| AuditRecord | findings, issues, decision (pass/block/escalate), rationale | 覆盖 SADP 合规检查，但不记录阶段推进 |
| ExecutionReport | status, summary, changed_files, evidence, risks | 覆盖执行结果，但不记录自动决策逻辑 |
| GateResult | gate_id, result (pass/fail/...), details, recommendation | 覆盖单个门控结果，但不汇总为阶段决策 |

**这些机制的组合不等于 AUTO_DECISION_LOG**。关键缺口是：没有机制记录 "为什么这个阶段推进是自动决定的"。

## 3. AUTO_DECISION_LOG 应记录的字段（建议）

```yaml
auto_decision_log:
  log_id: "adl-{timestamp}-{stage}"
  timestamp: "ISO-8601"
  stage: S2 | S3 | M4-A
  stage_transition: "S2→S3" | "S3→M4-A" | null

  input_summary:
    gate_results:
      p0_pass: X, p0_fail: Y
      p1_pass: X, p1_fail: Y
    evidence_freshness: all_current | partial_historical | mixed
    changed_files_count: N
    reviewer_decision: pass_to_review | needs_revision | blocked | human_required | null

  decision:
    type: auto_advance | auto_hold | auto_block | human_required
    allow_next_stage: true | false
    reason: "All P0/P1 gates pass, evidence current, no conflicts"

  human_required_check:
    any_direction_decision_triggered: false
    any_sensitive_operation_detected: false
    any_irreversible_operation_requested: false
    any_governance_modification: false
    any_forbidden_file_touched: false
    any_evidence_uncertainty: false
    # 如果任一项为 true → human_required

  auto_decision_basis:
    rule_references: ["gate-rule-001", "stage-gate-003"]
    conditions_met: ["all P0 gates pass", "all P1 gates pass", "evidence chain complete"]
    conditions_unmet: []

  linked_artifacts:
    gate_results: ["g-001", "g-002", ...]
    execution_reports: ["rep-001"]
    audit_record: "audit-{session_id}"
```

## 4. AUTO_DECISION_LOG 与 Stage Gate / Loop State 的关联

```
Loop Iteration N
  → 执行任务
  → 收集证据 (ExecutionReport, EvidenceIndex)
  → 运行 gates (GateResult[])
  → 检查 human_required conditions
      ├─ 无触发 → 生成 AUTO_DECISION_LOG (type: auto_advance)
      │             → 写入 allow_next_stage = true
      │             → loop harness 读取，自动进入下一阶段
      └─ 有触发 → 生成 AUTO_DECISION_LOG (type: human_required)
                   → 写入 allow_next_stage = false
                   → 列出 human_required_categories
                   → loop harness 暂停，等待人工输入
```

## 5. AUTO_DECISION_LOG 的存储位置建议

| 方案 | 优点 | 缺点 |
|------|------|------|
| `runs/{run_id}/auto-decision-log.yaml` | 与运行记录一起 | 需要统一路径规范 |
| `_reports/loop/{loop_id}/auto-decision-log.yaml` | 按loop组织 | 与现有runs/目录分离 |
| 嵌入 ExecutionReport | 一体化 | report变得过大 |

**建议**: `runs/{run_id}/auto-decision-log.yaml`，与现有 runs/ 目录结构一致。

## 6. 关键设计决策（需要GPT判断）

1. AUTO_DECISION_LOG 应由 agent-acceptance 的 gate runner 生成，还是由 dev-frame-opencode 的 loop harness 生成？
   - **建议**: 由 agent-acceptance 生成判定逻辑（acceptance criteria），由 dev-frame-opencode 在每次 loop 结束时调用并填充具体值

2. 是否需要在每次 loop 开始时检查上一轮的 AUTO_DECISION_LOG？
   - **建议**: 是。loop harness 应首先读取上一轮的 AUTO_DECISION_LOG 以确定当前阶段。

3. AUTO_DECISION_LOG 是否可以由 GPT 复审修改？
   - **建议**: 可以标记为 `reviewed`，但原始决策不可删除。GPT 可以追加 `review_note`。
