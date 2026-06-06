# Automated Handoff Protocol

> 版本: 1.0.0
> 目标: 长对话自动交接至新 GPT 对话，防止上下文膨胀和回复截断

## 触发阈值

| 条件 | 级别 | 行为 |
|------|------|------|
| assistant_message_count >= 60 | 强制 | 必须 handoff |
| response_time >= 60s | 强制 | 必须 handoff |
| review_rounds >= 3 | 强制 | 必须 handoff |
| GPT_REPLY < 2000 bytes | 强制 | 必须 handoff（且不执行） |
| assistant_message_count >= 45 | 建议 | 建议 handoff |
| response_time >= 40s | 建议 | 建议 handoff |
| resubmissions >= 2 | 建议 | 建议 handoff |

## 流程

```
1. check_handoff_needed.py → handoff_needed=true
2. agent 请求当前 GPT 生成 HANDOFF.md
3. GPT 输出 HANDOFF.md，结尾含 END_OF_HANDOFF
4. agent 验证：validate_handoff.py → valid=true, size >= 8000
5. agent 验证：validate_gpt_reply_completeness.py → complete=true
6. agent 开启新 ChatGPT 对话
7. agent 上传 HANDOFF.md 作为 .md 文件附件
8. agent 输入 bootstrap prompt
9. 新 GPT 回复 YAML 确认理解
10. overall_judgment=accepted, handoff_understood=yes → 继续执行
```

## GPT 回复完整性 guard

执行前必须检查 GPT_REPLY.txt：

| 检查 | 标准 |
|------|------|
| 最小字节数 | review >= 2000, task_plan >= 3000, handoff >= 8000 |
| 结束标记 | review: END_OF_GPT_RESPONSE, handoff: END_OF_HANDOFF |
| 必要字段 | review: overall_judgment/blocking_reasons/required_next_action/allow_proceed |

不满足任一条件 → 不得执行，等待或重试。

## Bootstrap 提示词模板

新对话第一条消息必须使用以下格式。**字段名和字段值必须全部使用中文**：

```
请阅读附件 HANDOFF.md（项目交接文档）。用以下中文 YAML 格式回复确认理解：

审查运行ID: handoff-verify-{时间戳}
交接理解判决: 已理解 | 未理解
项目身份已理解: 是 | 否
三层架构已理解: 是 | 否
已完成阶段已理解: 是 | 否
当前状态已理解: 是 | 否
安全边界已理解: 是 | 否
下一步任务已理解: 是 | 否
可以继续执行: 是 | 否
说明: 用中文说明对项目和当前任务链的整体理解，至少 5 句话
```

验收条件：`交接理解判决: 已理解` 且 `可以继续执行: 是` → agent 直接继续执行下一任务，不得再次确认。
