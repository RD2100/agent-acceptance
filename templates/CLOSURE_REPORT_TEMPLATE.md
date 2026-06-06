# Closure Report — {{任务名称}}

> REVIEW_RUN_ID: {{审查运行ID}}
> 仓库: {{仓库名}}
> 分支: {{分支名}}
> Commit: {{提交SHA}}
> 推送状态: 已推送/未推送

## 状态声明

| 字段 | 值 | 说明 |
|------|-----|------|
| task_status | ready_for_review / blocked | 当前任务状态 |
| gpt_review_submitted | 是/否 | 是否已提交 GPT 审查 |
| gpt_review_result | accepted / blocked / review_unverified / not_submitted | GPT 审查结果 |
| final_status | ready_for_review / accepted / closed / blocked | 最终状态 |

### 状态规则

1. **未提交 GPT 审查**时，final_status 不得写 `closed` 或 `accepted`
2. **GPT 未返回 accepted**时，final_status 不得写 `accepted` 或 `closed`
3. **只有 accepted 已写入 workflow ledger**后，final_status 才能写 `closed`
4. 违反以上任一条 = SD-02 缺陷，validator 应阻断

## 交付物清单

| 文件 | 状态 |
|------|------|
| {{文件路径}} | {{created/modified}} |

## 自检结果

| 检查 | 结果 |
|------|------|
| 测试 | {{测试结果}} |
| Bypass checker | {{绕过检测结果}} |
| Workflow closure validator | {{闭合验证结果}} |
| Manifest 双向一致 | 是/否 |
| Evidence pack 非 summary-only | 是/否 |

## 已知系统性缺陷

| 缺陷ID | 名称 | 本任务是否修复 | 修复后状态 |
|--------|------|--------------|-----------|
| SD-01 | summary-only evidence pack | 是/否 | {{状态}} |
| SD-02 | ready_for_review 被当作 closed | 是/否 | {{状态}} |
| SD-03 | self-referential failure | 是/否 | {{状态}} |

## 安全证言

| 边界 | 值 |
|------|-----|
| evidence_deleted | 否 |
| evidence_moved | 否 |
| evidence_renamed | 否 |
| evidence_fabricated | 否 |
| guard_removed | 否 |
| guard_weakened | 否 |
| live_cdp_enabled | 否 |
| real_user_data_processed | 否 |

## 下一步请求

<!-- 明确请求 GPT：审查什么、给出什么结论、推荐什么后续步骤 -->

{{下一步请求}}

## 备注

{{备注}}
