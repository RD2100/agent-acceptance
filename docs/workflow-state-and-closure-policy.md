# Workflow State and Closure Policy

> 版本: 1.0.0
> 权威来源: agent-acceptance
> 目的: 固化 SD-01/SD-02/SD-03 修复方案

## 1. 工作流状态定义

| 状态 | 含义 | 谁可以设置 |
|------|------|-----------|
| `planned` | 任务已定义，尚未执行 | 规划 agent / 人工 |
| `executed` | 任务已执行，尚未自检 | 执行 agent |
| `self_verified` | 本地测试、gate、validator 通过 | 执行 agent（需附 evidence） |
| `ready_for_review` | 证据包就绪，等待 GPT 审查 | 执行 agent |
| `review_unverified` | GPT 无法基于证据确认 | GPT |
| `blocked` | GPT 或本地 gate 发现阻断问题 | GPT / validator |
| `accepted` | GPT 基于证据包给出 accepted 判决 | GPT |
| `closed` | accepted + 已写入 workflow ledger | 框架（非 agent 手写） |

## 2. 状态转移规则

```
planned → executed → self_verified → ready_for_review → (GPT review) → accepted → (ledger write) → closed
                                                                      ↘ blocked
                                                                      ↘ review_unverified
```

| 转移 | 条件 |
|------|------|
| `ready_for_review` → `accepted` | GPT_REVIEW_RESULT 存在，overall_judgment=accepted |
| `accepted` → `closed` | 已写入 WORKFLOW_AUDIT_LEDGER，accepted_review_run_id 可追溯 |
| `ready_for_review` → `blocked` | GPT 或 validator 返回 blocked |
| `ready_for_review` → `review_unverified` | GPT 返回 review_unverified |

## 3. 阻断条件（SD-02 修复）

| 条件 | 严重度 | 说明 |
|------|--------|------|
| `closed_without_gpt_accepted` | FAIL | final_status=closed 但没有 GPT accepted |
| `accepted_without_gpt_review_result` | FAIL | 声称 accepted 但无 GPT_REVIEW_RESULT |
| `ready_for_review_counted_as_closed` | FAIL | final_status=closed 但 gpt_review_submitted=false |
| `closed_without_workflow_ledger_entry` | FAIL | closed 但没有 WORKFLOW_AUDIT_LEDGER 记录 |

## 4. Summary-Only Evidence Pack 阻断（SD-01 修复）

以下文件**不算**实际产物：GPT_REVIEW_PROMPT.md、CLOSURE_REPORT.md、SAFETY_ATTESTATION.md、PACK_MANIFEST.md。

证据包如果**只有**上述文件，必须被阻断。

| 条件 | 严重度 |
|------|--------|
| `summary_only_pack` | FAIL |
| `missing_actual_deliverables` | FAIL |
| `manifest_zip_mismatch` | FAIL |
| `claimed_tests_pass_without_test_output` | FAIL |
| `claimed_bypass_pass_without_bypass_output` | FAIL |

## 5. 治理任务禁止自闭合（SD-03 修复）

凡修改以下路径的任务，**必须**有 GPT closure review，不得自我闭合：

- contracts/**
- policies/**
- schemas/**
- templates/GPT_REVIEW_PROMPT_TEMPLATE.md
- scripts/validate_*
- scripts/check_*
- docs/*governance*
- docs/*workflow*
- docs/*memory*

**事后补审**（retroactive review）允许，但必须：
- 标注 `retroactive_review: true`
- 记录 `prior_status`（补审前的状态）
- 记录 `corrected_status`（补审后的状态）
- 记录 `reason_for_retroactive_review`
- 不得声称原始流程当时已正常 closed

## 6. 安全边界

本策略不授权：删除/移动/重命名 evidence、移除/弱化 guard、默认开启 live CDP、处理真实论文或私密文本。
