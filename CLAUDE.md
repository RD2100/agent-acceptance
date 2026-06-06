# DevFrame Agent Acceptance — Agent 工作协议

## 会话启动

每次会话启动，先按 README.md 中的读取顺序加载上下文（PROJECT_HISTORY.md → HANDOFF_V5.md → devframe-control-plane/PROJECT_HISTORY.md）。

## 核心协议

1. commit + push ≠ done。正确终点是 GPT accepted + ledger entry。
2. 每个任务闭环：authorization → execution → evidence → CDP submit → GPT review → closure。
3. pre-push gate step 2.6 强制检查 GPT 审查状态。未通过无法 push。
4. 对话超过 60 条 assistant message → 强制 handoff。
5. HANDOFF.md 必须包含 END_OF_HANDOFF 标记。
6. PROJECT_HISTORY.md 必须包含 END_OF_PROJECT_HISTORY 标记。

## 禁止

- 跳过 GPT 审查
- guard removal / evidence cleanup
- 提交真实用户数据/cookies/session
- 未经授权修改 CURRENT_ROUTE.json

## 测试

```bash
cd D:\agent-acceptance && python -m pytest tests/ -q
```
