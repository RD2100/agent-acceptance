# Paper Task Input/Output Protocol

> 版本: 1.0.0-draft
> 适用范围: 所有论文任务的标准化输入输出
> 安全边界: 不处理真实论文全文；real_paper_full_text 输入必须 fail-closed

## 1. 论文任务类型

| 类型 | 含义 | 典型场景 |
|------|------|---------|
| cssci_review | CSSCI 期刊审稿式评估 | 投稿前论文质量评估 |
| thesis_midterm_review | 博士论文中期考核评估 | 中期考核文本审查 |
| academic_revision | 学术修改与表达优化 | 润色、结构调整 |
| citation_verification | 引用核验 | 参考文献真实性检查 |
| paper_structure_diagnosis | 论文结构诊断 | 章节逻辑、论证链检查 |

## 2. 输入协议

所有论文任务输入必须包含：

```yaml
task_id: "string"
task_type: "enum"
paper_data_classification: "synthetic | redacted | user_authorized_excerpt | real_paper_full_text"
user_authorization: "explicit | none | synthetic"
input_materials: []
privacy_constraints: []
memory_policy: "none | redacted_workflow_lesson_only"
expected_outputs: []
```

### 2.1 数据分级规则

| 分级 | 允许范围 | 阻断规则 |
|------|---------|---------|
| synthetic | 测试/fixture/evidence pack | — |
| redacted | evidence pack（脱敏后） | 不得包含可逆向识别文本 |
| user_authorized_excerpt | 当前任务 | 必须有 explicit 授权 |
| real_paper_full_text | **本轮阻断** | 不得进入测试/fixture/memory/evidence pack |

### 2.2 阻断条件

| 条件 | 严重度 |
|------|--------|
| real_paper_full_text 输入 | FAIL |
| user_authorized_excerpt 缺 authorization | FAIL |
| raw_paper_text 进入 evidence pack | FAIL |
| paper_content 写入 memory | FAIL |
| 缺 privacy_constraints | FAIL |

## 3. 输出协议

所有论文任务输出必须包含：

```yaml
task_id: "string"
task_type: "enum"
output_summary: "string"
findings: []
evidence_basis: "string"
privacy_redaction_status: "full | partial | none"
manual_review_required: true | false
limitations: []
```

### 3.1 各任务类型特有输出

| 任务类型 | 必有输出 |
|---------|---------|
| cssci_review | overall_assessment, main_contribution, major_problems, revision_priorities, publishability_judgment |
| thesis_midterm_review | research_progress, problem_analysis, framework_suggestions, next_plan, risk_points |
| academic_revision | revision_goal, problems_identified, revised_version, revision_rationale |
| citation_verification | citation_status, retrievability, claim_support, suspicious_items |
| paper_structure_diagnosis | structure_assessment, logic_chain, section_alignment, redundancy_gap |

## 4. 隐私阻断规则

| 规则 | 阻断条件 |
|------|---------|
| real_paper_full_text 阻断 | paper_data_classification=real_paper_full_text → FAIL |
| 缺用户授权阻断 | paper_data_classification=user_authorized_excerpt 且 user_authorization!=explicit → FAIL |
| evidence pack 泄露阻断 | evidence pack 中含 raw_paper_text → FAIL |
| memory 写入阻断 | memory_write 含 paper_content → FAIL |
| 隐私证言缺失 | PRIVACY_ATTESTATION.yaml 缺失 → FAIL |
