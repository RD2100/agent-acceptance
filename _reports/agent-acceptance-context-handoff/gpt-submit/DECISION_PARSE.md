# DECISION_PARSE — GPT 回复中的结构化决策

> Status: decision = unknown
> Reason: GPT 未收到上下文，无回复可解析

## 等待项

1. 用户手动提交上下文包给 GPT
2. GPT 返回结构化回复
3. 从此回复中解析:
   - 是否同意最小修改范围
   - 是否同意新增 files 清单
   - 是否同意 human_required 分类
   - 是否同意 AUTO_DECISION_LOG 字段
   - 是否有额外的建议

## 解析模板

```yaml
gpt_decision:
  timestamp: null
  decision_id: unknown
  verdict: unknown  # approve_minimal | revise | reject | need_more_info

  patch_scope_approved: unknown
  human_required_taxonomy_approved: unknown
  auto_decision_log_schema_approved: unknown
  stage_gate_definition_approved: unknown

  additional_requirements: []
  rejected_items: []
  deferred_to_dev_frame: []

  parse_notes: "GPT context not submitted"
```
