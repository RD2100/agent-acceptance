# GPT 审查提示词模板

> 模板版本: gpt-review-template-v1
> 权威来源: agent-acceptance
> 适用范围: 所有任务类型的 GPT 审查提示词
> 使用方式: 复制此模板，替换占位符，添加 task_type_specific 字段

---

## 提示词作者须知

1. 将此模板复制到你的 `GPT_REVIEW_PROMPT.md`
2. 替换所有 `{{占位符}}` 为实际值
3. 在 `## 任务特定上下文` 下描述 GPT 需要审查的内容
4. 在 `task_type_specific` 下定义本任务类型独有的审查维度
5. `## 要求的回复格式` 章节**不可修改** — 这是规范化 schema
6. 将 evidence pack ZIP 与此提示词一起提交，本文件作为第一个文件

---

## Evidence Pack 上下文

| 字段 | 值 |
|------|-----|
| REVIEW_RUN_ID | `{{审查运行ID}}` |
| task_type | `{{任务类型}}` |
| review_stage | `{{审查阶段}}` |
| contract_id | `{{合约ID或空}}` |
| contract_version | `{{合约版本或空}}` |
| evidence_pack_path | `{{证据包路径}}` |
| evidence_pack_sha256 | `{{证据包SHA256或空}}` |
| submitted_at | `{{提交时间ISO8601}}` |

## Evidence Pack 内容清单

| 文件 | 角色 | SHA256 |
|------|------|--------|
| `{{文件路径}}` | `{{角色}}` | `{{SHA256或空}}` |
<!-- 对 pack 中每个文件重复此表行 -->

## 任务特定上下文

<!-- 描述：已完成的工作、GPT 需要审查的内容、相关约束 -->

{{任务特定上下文}}

---

## 要求的回复格式

以下 base 字段**所有任务类型都必须填写**。
标注 `| 可为空` 的字段是可选的：不适用时填写 `null`（YAML 空值，不要加引号）。

```yaml
REVIEW_RUN_ID: "{{审查运行ID}}"
template_version: "gpt-review-template-v1"
task_type: "{{任务类型}}"
review_stage: "{{审查阶段}}"
overall_judgment: "accepted | blocked | human_required | review_unverified"
reviewer_type: "gpt | human | agent"
contract_id: {{合约ID或空}}
contract_version: {{合约版本或空}}
# evidence_pack 可选 — 无 pack 时填 null，有 pack 时填嵌套字段
evidence_pack: null
#
# 有 pack 时，将上面 null 替换为：
# evidence_pack:
#   path: "pack/path.zip"
#   sha256: "abc123..."
#   manifest_valid: true
evidence_inspected:
  - path: "{{文件路径}}"
    sha256: {{SHA256或空}}
    inspected: true | false
    role: "{{角色}}"
blocking_reasons: []
missing_evidence: []
scope_violation: true | false
fake_green_risk: true | false
safety_boundaries_respected: true | false
required_next_action: "{{具体下一步}}"
allow_proceed: true | false
review_unverified_reason: {{原因或空}}
created_at: "{{ISO8601时间戳}}"
rationale: "{{解释说明}}"
task_type_specific:
  "{{任务类型}}":
    # 此键必须与 task_type 字段的值一致。
    # Schema 约束键为合法的 task_type 枚举值；
    # 应用层代码约束键等于 task_type 字段值（JSON Schema 的固有限制）。
    # 提示词作者在此处定义本任务特有的字段。
```

## 规则

- `overall_judgment: accepted` → `allow_proceed` 必须为 `true`
- `overall_judgment: blocked` → `allow_proceed` 必须为 `false`
- `overall_judgment: human_required` → `allow_proceed` 必须为 `false`（除非显式授权）
- `overall_judgment: review_unverified` → `allow_proceed` 必须为 `false`，且 `review_unverified_reason` 必须非空
- `blocking_reasons` 必须为 `[]`（空列表），**绝不**使用字符串 `"none"`
- `missing_evidence` 必须为 `[]`（空列表），**绝不**使用字符串 `"none"`
- `evidence_inspected` 必须列出 GPT 实际阅读的每个证据文件
- SHA256 不可用时填 `null` — **绝不伪造 hash**
- **Agent 陈述不是证据** — GPT 必须检查实际文件内容
- **绝不**建议 guard removal、evidence cleanup 或默认开启 live CDP
