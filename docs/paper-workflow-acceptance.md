# Paper Workflow Acceptance — 论文工作流验收规范层

> Authority: agent-acceptance
> Layer: normative (contract + evidence + decision rules)
> Scope: design_only / contract_first / no_runtime_execution
> REVIEW_RUN_ID: paper-a1-contract-design-v1

---

## 1. 为什么论文工作流属于 agent-acceptance 的规范层

agent-acceptance 的核心职责是定义"什么叫合格"——不执行，不编排，不操作。它提供：

- acceptance contracts（验收合约）
- evidence pack requirements（证据包要求）
- fail-closed rules（安全阻断规则）
- decision schema（accepted / blocked / needs_more_evidence）

论文工作流与代码工作流在这些维度上是同构的：

| 维度 | 代码工作流 | 论文工作流 |
|------|-----------|-----------|
| 任务定义 | TaskSpec + pipeline stage | paper_task_id + task_type |
| 执行证据 | TEST_OUTPUT, DIFF_STAT | CITATION_CHECK_RESULT, REVISION_DIFF_SUMMARY |
| 安全证言 | SAFETY_ATTESTATION.md | CONFIDENTIALITY_ATTESTATION |
| 结果判决 | FLOW_OUTCOME (accepted/blocked/human_required) | PAPER_FLOW_OUTCOME (accepted/blocked/needs_more_evidence) |
| 可追溯性 | REVIEW_RUN_ID + SHA256 | PAPER_REVIEW_RUN_ID + input/output version hash |
| 阻断条件 | guard_removal, evidence_cleanup | fabricated_citation, author_intent_violation, confidentiality_leak |
| 伪造防护 | stale logs blocked, missing evidence blocked | stale paper version blocked, missing citation check blocked |

因此，论文验收规范是 agent-acceptance 的自然扩展，而不是新建一个独立系统。

---

## 2. 三层架构边界

```
agent-acceptance (本仓库)
  role: 定义论文任务验收规范
  owns:
    - paper acceptance contracts
    - paper evidence pack schema
    - paper fail-closed rules
    - paper decision schema
  NOT:
    - 不编排 pipeline
    - 不执行审查
    - 不调用 LLM

devframe-control-plane
  role: 读取 contract_id / contract_version 并编排流程
  NOT:
    - 不在本任务中新增 pipeline runner 逻辑
    - 不在本任务中改 state machine
    - 不在本任务中新增 live CDP 行为

dev-frame-opencode
  role: 具体执行论文审查、润色、引用核验
  NOT:
    - 不在本任务中实现 paper skill
    - 不在本任务中调用真实 LLM
    - 不在本任务中读取真实用户论文
```

---

## 3. Evidence-First 在论文场景中的含义

Evidence-First 的核心原则不变：

> agent summary is not evidence。
> 不能只凭 agent 说"已完成"就 accepted。

论文场景下的 evidence 包括：

| evidence 类型 | 说明 | 要求 |
|--------------|------|------|
| input_version_hash | 输入论文版本的 SHA256 | 必填 |
| output_version_hash | 输出论文版本的 SHA256 | 必填（如有修改） |
| input_summary | 脱敏后的输入摘要 | 可选（脱敏），不得含全文 |
| output_summary | 脱敏后的输出摘要 | 可选（脱敏），不得含全文 |
| revision_diff_summary | 改动差异摘要 | 改写/润色任务必填 |
| review_report | 审查报告 | 审查类任务必填 |
| citation_check_result | 引用核验结果 | 引用核验任务必填 |
| author_intent_preservation | 作者原意保持声明 | 改写/润色任务必填 |
| confidentiality_attestation | 保密证言 | 所有论文任务必填 |

---

## 4. Paper Decision Schema

统一判决语义（与代码工作流 FLOW_OUTCOME 同构）：

### 4.1 accepted

条件：
- 所有 required_evidence 齐全
- 未触发任何 fail_closed 条件
- 符合对应 contract 的 acceptance_criteria
- confidentiality_attestation 通过

含义：论文任务符合验收规范，可进入下一阶段。

### 4.2 blocked

条件（任一即触发）：
- 触发 fail_closed 条件（如 fabricated_citation、author_intent_violation）
- evidence 与结论之间存在不可调和的矛盾
- 检测到伪造、泄密、越权行为
- confidentiality_attestation 缺失或矛盾

含义：论文任务存在严重问题，不可通过。

### 4.3 needs_more_evidence

条件：
- 未触发 fail_closed
- but required_evidence 不完整
- or 某些维度的评估不充分
- or citation check 未执行
- or 输入版本不明确

含义：未发现严重违规，但证据不足以做出 accepted 或 blocked 判断。

### 4.4 review_unverified

条件：
- evidence pack 不可读取
- contract_id 不存在于已注册合约中
- evidence pack 格式不可解析

含义：无法判断，需修复 evidence pack 后重新提交。

---

## 5. 与 control-plane 和 opencode 的接口关系

### 5.1 control-plane 如何消费本规范

```
control-plane 读取:
  - contract_id → 确定适用哪个 paper contract
  - contract_version → 版本锁定
  - required_evidence → 编排 evidence 收集流程
  - fail_closed_on → 编排安全检查
  - acceptance_criteria → 编排验收判定

control-plane 不关心:
  - 论文具体内容
  - 具体审查方法
  - 引用数据来源
```

### 5.2 opencode 如何消费本规范

```
opencode 读取:
  - task_type → 选择对应的审查/核验/改写方法
  - required_evidence → 生成对应 evidence 文件
  - prohibited_tasks → 不执行禁止操作

opencode 不关心:
  - contract 的完整定义
  - decision schema 的逻辑
```

---

## 6. 代码工作流证据 → 论文工作流证据的映射

```
TEST_OUTPUT.txt        → CITATION_CHECK_RESULT / REVIEW_REPORT
DIFF_STAT.txt          → REVISION_DIFF_SUMMARY
SAFETY_ATTESTATION.md  → CONFIDENTIALITY_ATTESTATION
FLOW_OUTCOME.json      → PAPER_FLOW_OUTCOME
DISPATCH_RESULT.json   → PAPER_REVIEW_RESULT
REVIEW_RUN_ID          → PAPER_REVIEW_RUN_ID
guard not removed      → author intent not violated / evidence not fabricated
stale logs blocked     → stale paper version blocked
missing evidence blocked → missing citation check / missing revision diff blocked
```

---

## 7. 已注册 Paper Contracts

| contract_id | 用途 |
|------------|------|
| PAPER_GENERAL_ACCEPTANCE_CONTRACT | 所有论文任务的基础规范 |
| CSSCI_REVIEW_CONTRACT | CSSCI 教育学论文审稿式评估 |
| THESIS_MIDTERM_REVIEW_CONTRACT | 博士论文中期考核文本审查 |
| CITATION_VERIFICATION_CONTRACT | 引用核验 |
| ACADEMIC_REVISION_CONTRACT | 论文润色、改写、结构调整 |
| CONFIDENTIALITY_CONTRACT | 论文及用户研究保密 |
| PAPER_EVIDENCE_PACK_CONTRACT | 论文证据包结构与完整性 |

详细定义见 `contracts/paper_acceptance_contracts.yaml`。

---

## 8. 安全边界

本规范层设计遵守以下安全边界：

| 边界 | 值 |
|------|-----|
| 处理真实私密论文 | false（contract 只定义规范，不处理数据） |
| live CDP 启用 | false |
| GPT submission 默认开启 | false |
| guard removal attempted | false |
| evidence cleanup attempted | false |
| 外部 API 引入 | false |
| 引用伪造 | false |
| 文献补造 | false |
| 自动投稿 | false |
