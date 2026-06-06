# Concept: {{TITLE}}

memory_id: {{MEMORY_ID}}
memory_type: lesson | failure_pattern | design_decision | safety_rule | workflow_rule | gotcha
status: active | superseded | deprecated
source_review_run_ids:
  - {{REVIEW_RUN_ID_1}}
  - {{REVIEW_RUN_ID_2}}
related_tasks:
  - {{TASK_ID_1}}
  - {{TASK_ID_2}}
privacy_classification: private_by_default | team_readable

## Summary

<!-- 一句话概括。禁止包含真实论文内容。 -->

{{ONE_SENTENCE_SUMMARY}}

## When It Appears

<!-- 什么场景下会出现这个问题/模式。 -->

{{CONDITIONS}}

## Why It Matters

<!-- 为什么这是个重要教训。 -->

{{IMPACT}}

## Required Response

<!-- 下次遇到时应该怎么做。 -->

{{RESPONSE}}

## Evidence References

<!-- 指向 source review result，不是复制全文。 -->

| REVIEW_RUN_ID | Task | Judgment |
|--------------|------|----------|
| {{REVIEW_RUN_ID}} | {{TASK}} | {{JUDGMENT}} |

## Related Concepts

<!-- 链接到相关 memory entry。 -->

| memory_id | title | relationship |
|-----------|-------|-------------|
| {{MEMORY_ID}} | {{TITLE}} | {{RELATIONSHIP}} |

## Lint Notes

<!-- 已知的 lint 注意事项。 -->

- lint_status: {{LINT_STATUS}}
- last_lint: {{LAST_LINT_DATE}}
