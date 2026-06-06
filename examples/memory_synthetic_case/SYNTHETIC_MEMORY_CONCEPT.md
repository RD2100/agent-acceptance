# Concept: Summary-Only Evidence Pack Pattern

memory_id: SYN-MEM-001
memory_type: failure_pattern
status: active
source_review_run_ids:
  - syn-review-001
related_tasks:
  - SYN-TASK-001
privacy_classification: team_readable

## Summary

Agent 多次提交只包含 closure report + attestation + manifest 的 evidence pack，
不含任何实际产物文件。GPT 每次都判 review_unverified 或 blocked。

## When It Appears

- 任务执行完成后，agent 手写 closure report 和 safety attestation
- agent 跳过构建证据包的步骤（或手动 ZIP 时漏掉实际产物）
- pre-submission gate 未生效或未运行
- 提交 GPT 前未做 manifest 与 ZIP 双向一致性检查

## Why It Matters

这是 Evidence-First 最核心的违规模式。GPT 每次都正确驳回，
但 agent 在多个任务中重复同样错误。说明需要 pre-submission
自动化阻断，而不是依赖 GPT 事后发现。

## Required Response

1. 强制运行 pre-submission gate 在 GPT 提交前
2. pack builder 必须自动收集实际产物文件
3. manifest 必须由 builder 生成，不由 agent 手写
4. pre-submission check 必须拒绝 summary-only pack

## Evidence References

| REVIEW_RUN_ID | Task | Judgment |
|--------------|------|----------|
| syn-review-001 | SYN-TASK-001 | blocked（synthetic） |

## Related Concepts

| memory_id | title | relationship |
|-----------|-------|-------------|
| SYN-MEM-002 | ready_for_review_not_closed | same_root_cause |
| SYN-MEM-003 | manifest_zip_mismatch | related |

## Lint Notes

- lint_status: pass
- last_lint: 2026-06-06
