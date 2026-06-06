# Memory Lint Rules

> 版本: 1.0.0-draft
> 用途: 定义 memory 的 lint 检查规则，确保 memory 一致性

## 规则分级

- **FAIL**: 阻断性错误，memory 存在严重问题
- **NEEDS_REVIEW**: 需要人工审核
- **WARNING**: 非阻断但建议修正

## 规则列表

### L-001: lesson_without_source_review
- 级别: FAIL
- 检查: 每条 memory entry 是否有 source_review_run_id
- 违反: memory entry 声称 lesson 但没有引用任何 source

### L-002: private_text_in_memory
- 级别: FAIL
- 检查: memory entry 是否包含真实论文全文、用户身份、用户私密文本
- 违反: 检测到疑似私密内容

### L-003: claims_accepted_without_gpt_review
- 级别: FAIL
- 检查: memory entry 是否声称任务 accepted，但 source_review_run_id 指向的 GPT review 不是 accepted
- 违反: 状态矛盾

### L-004: contradictory_lessons
- 级别: FAIL
- 检查: 两条 memory entry 是否互相矛盾
- 示例: entry-01 说"summary-only pack 应被 pre-submission gate 阻断"，entry-02 说"summary-only pack 作为草稿可以接受"

### L-005: memory_claims_authority_over_evidence
- 级别: FAIL
- 检查: memory entry 是否声称自己是权威 evidence 或替代 GPT accepted
- 违反: "根据 memory entry X，任务 Y 应视为 accepted"

### L-006: broken_internal_links
- 级别: FAIL
- 检查: memory entry 中的 source_review_run_id 或 task_id 引用是否有效
- 违反: 引用的 review 或 task 不存在

### L-007: repeated_failure_without_gate
- 级别: NEEDS_REVIEW
- 检查: 同一 failure pattern 出现 2 次以上但没有 linked gate（pre-submission check 或 contract 修正）
- 违反: 知道有重复缺陷但未采取阻断措施

### L-008: orphan_memory_entries
- 级别: WARNING
- 检查: memory entry 没有被任何 index 引用，也没有关联到其他 entry
- 违反: 孤立的 lesson

### L-009: deprecated_entry_still_marked_active
- 级别: FAIL
- 检查: 已标记 deprecated 的 entry 在 index 中仍为 active
- 违反: 状态不一致

### L-010: accepted_task_without_memory_summary
- 级别: WARNING
- 检查: WORKFLOW_AUDIT_LEDGER 中 status=closed 的任务是否有对应的 memory entry
- 违反: 已闭合但未沉淀教训

### L-011: stale_policy_reference
- 级别: NEEDS_REVIEW
- 检查: memory entry 引用的 contract/policy 版本是否已被更新
- 违反: 引用了旧版本的规范

### L-012: orphan_concept_without_backlinks
- 级别: WARNING
- 检查: memory concept 是否被其他 entry 引用
- 违反: 孤立的概念，无人引用

## Lint 输出格式

```yaml
MEMORY_LINT_RESULT:
  result: pass | fail | needs_review
  checks_run: N
  errors:
    - rule: L-001
      level: FAIL
      memory_id: "MEM-001"
      description: "lesson without source_review_run_id"
  warnings:
    - rule: L-010
      level: WARNING
      task_id: "ARCH-GAP-A1"
      description: "accepted task without memory summary"
  needs_review:
    - rule: L-007
      level: NEEDS_REVIEW
      pattern: "summary-only evidence pack"
      occurrence_count: 4
```
