# GPT 审查提示词模板

> 模板版本: gpt-review-template-v1
> 权威来源: agent-acceptance
> 适用范围: 所有任务类型的 GPT 审查提示词
> 使用方式: 复制此模板，替换占位符，添加 task_type_specific 字段
> **语言要求: 除字段名和枚举值必须使用英文外，所有文本内容必须使用中文**

---

## 提示词作者须知

1. 将此模板复制到你的 `GPT_REVIEW_PROMPT.md`
2. 替换所有 `{{占位符}}` 为实际值。**注意**：`{{任务类型}}`、`{{审查阶段}}`、`{{角色}}` 等枚举占位符必须填入 schema 规定的英文枚举值（如 `design_review`、`authorization`），不能填入中文自由文本
3. 在 `## 任务特定上下文` 下用中文描述 GPT 需要审查的内容
4. 在 `task_type_specific` 下定义本任务类型独有的审查维度（维度名可用英文，说明用中文）
5. `## 要求的回复格式` 章节**不可修改** — 这是规范化 schema
6. 将 evidence pack ZIP 与此提示词一起提交，本文件作为第一个文件

---

## Evidence Pack 上下文

| 字段 | 值 |
|------|-----|
| 审查运行ID | `{{审查运行ID}}` |
| 任务类型 | `{{任务类型}}` |
| 审查阶段 | `{{审查阶段}}` |
| 合约ID | `{{合约ID或空}}` |
| 合约版本 | `{{合约版本或空}}` |
| 证据包路径 | `{{证据包路径}}` |
| 证据包SHA256 | `{{证据包SHA256或空}}` |
| 提交时间 | `{{ISO8601时间戳}}` |

## 证据包内容清单

| 文件 | 用途 | SHA256 |
|------|------|--------|
| `{{文件路径}}` | `{{角色}}` | `{{SHA256或空}}` |
<!-- 对 pack 中每个文件重复此表行 -->

## 任务特定上下文

<!-- 用中文描述：已完成的工作、GPT 需要审查的内容、相关约束 -->

{{任务特定上下文}}

---

## 要求的回复格式

以下字段名和枚举值**必须保持英文**（schema 兼容性要求）。
**所有文本内容字段 — rationale、required_next_action、review_unverified_reason、blocking_reasons 列表条目、missing_evidence 列表条目、task_type_specific 中的维度说明 — 必须使用中文。**

```yaml
REVIEW_RUN_ID: "{{审查运行ID}}"
template_version: "gpt-review-template-v1"
task_type: "{{任务类型}}"
review_stage: "{{审查阶段}}"
overall_judgment: "accepted | blocked | human_required | review_unverified"
reviewer_type: "gpt | human | agent"
contract_id: {{合约ID或空}}
contract_version: {{合约版本或空}}
# evidence_pack 可选：无 pack 时填 null，有 pack 时将 null 替换为下方嵌套结构
evidence_pack: null
#
# 有 pack 时：
# evidence_pack:
#   path: "pack路径"
#   sha256: "abc123..."
#   manifest_valid: true
evidence_inspected:
  - path: "{{文件路径}}"
    sha256: {{SHA256或空}}
    inspected: true | false
    role: "{{角色}}"
blocking_reasons: []
# 阻断原因列表，用中文填写每条原因
missing_evidence: []
# 缺失证据列表，用中文填写每条缺失项
scope_violation: true | false
fake_green_risk: true | false
safety_boundaries_respected: true | false
required_next_action: "{{具体下一步（用中文填写）}}"
allow_proceed: true | false
review_unverified_reason: {{原因或空（用中文填写）}}
created_at: "{{ISO8601时间戳}}"
rationale: "{{解释说明（用中文填写）}}"
task_type_specific:
  "{{任务类型}}":
    # 此键必须与 task_type 字段值一致
    # 此处定义本任务特有的审查维度，维度说明用中文
```

## 规则

- `overall_judgment: accepted` → `allow_proceed` 必须为 `true`
- `overall_judgment: blocked` → `allow_proceed` 必须为 `false`
- `overall_judgment: human_required` → `allow_proceed` 必须为 `false`（除非显式授权）
- `overall_judgment: review_unverified` → `allow_proceed` 必须为 `false`，且 `review_unverified_reason` 必须非空
- `blocking_reasons` 必须为 `[]`（空列表），**绝不**使用字符串 `"none"`；条目**用中文**
- `missing_evidence` 必须为 `[]`（空列表），**绝不**使用字符串 `"none"`；条目**用中文**
- `evidence_inspected` 必须列出 GPT 实际阅读的每个证据文件
- SHA256 不可用时填 `null` — **绝不伪造 hash**
- **Agent 陈述不是证据** — GPT 必须检查实际文件内容
- `rationale`、`required_next_action`、`review_unverified_reason` **必须用中文**
- **绝不**建议 guard removal、evidence cleanup 或默认开启 live CDP
