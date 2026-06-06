# GPT 审查提示词模板

> 模板版本: gpt-review-template-v1
> 权威来源: agent-acceptance
> 适用范围: 所有任务类型的 GPT 审查提示词
> 使用方式: 复制此模板，替换占位符，添加 task_type_specific 字段
> **语言要求: 除 schema 字段名和 schema/contract 规定的枚举值为英文外，所有文本内容必须使用中文**

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
    role: "{{角色（说明性文本用中文，如为机器枚举则用英文）}}"
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
    # 字段名可用英文；若字段值非 schema/contract 枚举，则字段值用中文
    # 此处定义本任务特有的审查维度
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

---

## 提交方自检清单（提交 GPT 前必须逐项确认）

提交 evidence pack 给 GPT 审查时，提交提示词**必须**包含以下内容。缺任一项 = 提交不完整。

### 必须包含的信息

| # | 检查项 | 说明 |
|---|--------|------|
| 1 | 当前任务状态 | 完成的工作、产出文件列表、自检结果（测试/gate/bypass） |
| 2 | 已知 open 缺陷 | 从 WORKFLOW_AUDIT_LEDGER 中列出所有 status=open 的系统缺陷（如 SD-01/02/03），说明本任务是否已修复 |
| 3 | 明确的审查请求 | GPT 需要判断什么？需要给出什么格式的结论？ |
| 4 | 请求后续计划 | 如果 accepted，下一步应该做什么？如果 blocked，具体修复方案是什么？ |
| 5 | 证据包完整性声明 | 确认 evidence pack 非 summary-only，manifest 双向一致 |

### 严禁的提交模式

| # | 禁止 | 正确做法 |
|---|------|---------|
| 1 | 只提交 closure report/safety attestation，无实际产物 | 必须包含实际修改/新增的文件 |
| 2 | 不提 open 缺陷 | 必须明确列出当前 open 缺陷及其修复状态 |
| 3 | 不请求后续计划 | 必须要求 GPT 给出下一步具体方案 |
| 4 | 写 final_status: closed 但无 GPT accepted | closed 必须先有 GPT accepted |
| 5 | 用英文写 task_type_specific 字段名 | task_type_specific 区域字段名用中文 |

### 推荐提交提示词结构

```
1. 本任务做了什么（3-5 句）
2. 证据包内容（文件数量、manifest 状态）
3. 自检结果（测试/gate/bypass 结果）
4. 当前 open 系统性缺陷及修复状态
5. 明确请求：请审查 X/Y/Z，给出判决 + 下一步具体计划
6. 约束：不接受建议 guard removal/evidence cleanup/live CDP
```
