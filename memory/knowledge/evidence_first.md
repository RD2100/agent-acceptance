# Evidence-First Review

> 主题: evidence_first
> 关联任务: GROUP-01, GROUP-02, GROUP-05, GROUP-06, WORKFLOW-HARDENING-A1, PAPER-A2
> 最后更新: 2026-06-07
> 阅读时机: 构建 evidence pack 或提交 GPT 审查前

## 核心原则

Evidence-First 工作流要求每个非平凡任务必须：
1. Authorization（构建授权证据包 ZIP → CDP 提交 GPT → 等待审查）
2. Execution（GPT accepted 后执行代码变更）
3. Evidence（收集 TEST_OUTPUT、SAFETY_ATTESTATION、CLOSURE_REPORT 等）
4. Closure（构建闭合证据包 ZIP → CDP 提交 GPT → GPT accepted → closed）
5. Chain（持久化到 DECISION_LEDGER，更新 PROJECT_HISTORY.md）

## 关键规则

- commit + push ≠ done。正确终点是 GPT accepted + ledger entry
- 跳过 GPT 审查的任务不得声称 closed
- pre-push gate step 2.6 强制检查 GPT 审查状态
- 对话超过 60 条需强制 handoff

## 已知陷阱

- SD-01: summary-only evidence pack 被 GPT 驳回。必须包含 actual deliverables
- SD-02: ready_for_review 被当作 closed。必须有 GPT accepted 才算 closed
- 多轮迭代后仍 blocked：说明 pre-submission self-verify 未生效
