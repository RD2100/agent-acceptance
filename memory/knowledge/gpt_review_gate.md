# GPT Review Gate

> 主题: gpt_review_gate
> 关联任务: 全部 GROUP tasks, PAPER-A2, PAPER-C1, PAPER-C2
> 最后更新: 2026-06-07
> 阅读时机: 准备提交证据包给 GPT 前

## 审查流程

1. 构建 evidence pack ZIP（包含 actual deliverables + test output + safety attestation）
2. 生成 GPT_REVIEW_PROMPT.md（审查要点 + 判定标准）
3. CDP 提交：Chrome --remote-debugging-port=9222，Playwright connect_over_cdp
4. 当前活跃 GPT 对话：https://chatgpt.com/c/6a23dd8c-4550-83a8-bdee-76ca5a982edb
5. 等待 60-90 秒，捕获 GPT 回复全文 + 计算 SHA256

## 关键规则

- GPT 必须返回结构化 YAML：overall_judgment + blocking_issues + required_fixes
- 必须是 evidence-first：GPT 能看到 actual deliverables，不只是 summary
- 如果 2 轮后 GPT 仍在格式细节上 blocked：使用 accept_with_evidence_limitation
- 每次 CDP 提交必须保存 GPT_REPLY.txt + SHA256

## 审查失败模式

- summary-only pack：GPT 看不到 actual deliverables → blocked
- raw git evidence 缺失：只给结论不给原始输出 → blocked
- 包含 dirty baseline 文件：超出 accepted scope → blocked
