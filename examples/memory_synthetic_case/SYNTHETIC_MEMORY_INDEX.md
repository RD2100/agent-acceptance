# Memory Index (Synthetic)

> synthetic_only: true
> contains_real_user_data: false
> contains_private_paper_text: false
> last_updated: 2026-06-06
> total_entries: 3
> privacy_classification: private_by_default

## Concepts

| memory_id | title | memory_type | status |
|-----------|-------|-------------|--------|
| SYN-MEM-001 | Summary-Only Evidence Pack Pattern | failure_pattern | active |
| SYN-MEM-002 | ready_for_review_not_closed | workflow_rule | active |
| SYN-MEM-003 | Manifest ZIP Mismatch Detection | gotcha | active |

## Failure Patterns

| memory_id | pattern | occurrence_count | linked_gate | status |
|-----------|---------|-----------------|-------------|--------|
| SYN-MEM-001 | summary-only pack | 4 | pre-submission gate (needs strengthening) | active |

## Workflow Rules

| memory_id | rule | source | status |
|-----------|------|--------|--------|
| SYN-MEM-002 | closed == GPT accepted；ready_for_review != closed | syn-review-002 | active |

## Safety Rules

| memory_id | rule | severity | status |
|-----------|------|----------|--------|
| none | — | — | — |

## Gotchas

| memory_id | gotcha | related_tasks |
|-----------|--------|---------------|
| SYN-MEM-003 | Manifest 列 8 文件 ZIP 只有 3 文件 → GPT 判 blocked | SYN-TASK-001, PAPER-A1, push-blocker |

## Follow-up Tasks

| task_id | reason | depends_on |
|---------|--------|------------|
| SYN-FOLLOW-01 | pre-submission gate strengthening | SYN-MEM-001 |
| SYN-FOLLOW-02 | closure template fix | SYN-MEM-002 |

## Deprecated / Superseded

| memory_id | title | deprecation_reason | superseded_by |
|-----------|-------|-------------------|---------------|
| none | — | — | — |
