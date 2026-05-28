# resource-registry.md 引用次数统计

> 生成时间: 2026-05-28
> 方法: 全仓 grep `resource-registry\.md`，按文件聚合计数
> 总引用: 25 次，分布在 8 个文件中

## 按引用次数降序排列

| # | 文件 | 引用次数 |
|---|------|---------|
| 1 | `docs/agent-runtime/r0-negative-tests.md` | 15 |
| 2 | `docs/agent-runtime/r0-reviewer-checklist.md` | 4 |
| 3 | `docs/agent-runtime/historical-evidence-policy.md` | 1 |
| 4 | `docs/agent-runtime/resource-risk-matrix.md` | 1 |
| 5 | `docs/agent-runtime/resource-integration-status-index.md` | 1 |
| 6 | `docs/agent-runtime/resource-integration-reviewer-playbook.md` | 1 |
| 7 | `docs/agent-runtime/test-frame-evidence-map.md` | 1 |
| 8 | `docs/agent-runtime/test-frame-attribution-alignment.md` | 1 |

## 分析

- **r0-negative-tests.md** 是主要消费者（60%），每条负面测试用例都引用 resource-registry.md 作为 R0 规则来源
- **r0-reviewer-checklist.md** 是次要消费者（16%），在审查清单中多次引用
- 其余 6 个文件各引用 1 次，属于零散引用

## 路由决策

- 任务类型: 结构分析（字面字符串搜索）
- 使用工具: Grep（精确字符串匹配，非语义搜索）
- 跳过 CodeGraph: CodeGraph 适用于符号级代码搜索，对于文档间文本引用，Grep 是正确工具
