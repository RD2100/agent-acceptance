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


## Repo Routing (REPO-ROUTING-A1)

每个任务必须声明 primary_repo 和路径边界：
- schemas/SUBMISSION_TARGET.schema.json 定义格式
- contracts/REPO_ROUTING_CONTRACT.md 定义规则
- 缺 submission_target → pre-push gate 阻断
- 路径越界 → pre-push gate 阻断
- 跨仓任务必须在 evidence pack 中绑定每个仓库的 git_tree_sha
