# DevFrame Agent Acceptance — Agent 工作协议

## 会话启动

每次会话启动，按此顺序：1) BOOT_CONTEXT.md（3K 冷启动入口）→ 2) memory/index.md（记忆索引）→ 3) 按需 PROJECT_HISTORY.md。不再使用 HANDOFF 文档。

## 核心协议

1. commit + push ≠ done。正确终点是 GPT accepted + ledger entry。
2. 每个任务闭环：authorization → execution → evidence → CDP submit → GPT review → closure。
3. pre-push gate step 2.6 强制检查 GPT 审查状态。未通过无法 push。
4. Web GPT = 审查者/决策者，Claude Code = 执行者。CDP = 仅提交 evidence pack。
5. PROJECT_HISTORY.md 必须包含 END_OF_PROJECT_HISTORY 标记。

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
