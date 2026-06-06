# Daily Memory Log — {{YYYY-MM-DD}}

> memory_type: daily_log
> privacy_classification: private_by_default
> synthetic_only: true（如涉及真实论文则不可填写此字段）

## Source Reviews

<!-- 每行一个 source review。禁止包含真实论文全文。 -->

| review_run_id | task_id | repo | judgment | source_pack | privacy_ok |
|--------------|---------|------|----------|-------------|------------|
| {{REVIEW_RUN_ID}} | {{TASK_ID}} | {{REPO}} | {{JUDGMENT}} | {{PACK_PATH}} | yes / no |

## Lessons Observed

<!-- 每条 lesson 必须引用 source。禁止引用真实论文内容。 -->

| lesson_id | lesson | source_review_run_id | should_compile |
|-----------|--------|---------------------|----------------|
| {{LESSON_ID}} | {{LESSON}} | {{REVIEW_RUN_ID}} | yes / no |

## Failure Patterns

<!-- 重复出现的失败模式。2 次以上应标记 repeated: yes。 -->

| pattern | repeated | related_tasks | required_gate_update |
|---------|----------|---------------|---------------------|
| {{PATTERN}} | yes / no | {{TASK_IDS}} | {{GATE_UPDATE}} |

## Follow-up Tasks

| task_id | reason | depends_on |
|---------|--------|------------|
| {{TASK_ID}} | {{REASON}} | {{DEPENDS}} |

## Redaction Notes

- private_content_seen: yes / no
- private_content_stored: no（必须为 no）
- redaction_applied: {{描述脱敏处理}}
