# Paper Workflow Memory Rules

> 版本: 1.0.0
> 目标: 定义论文工作流中可记忆和禁止记忆的内容边界

## 绝对禁止进入记忆

| 类别 | 示例 |
|------|------|
| 真实论文全文 | 用户论文正文、章节、段落 |
| 论文片段 | "某论文第三章提到……" |
| 引用原文 | 论文中的具体引用表述 |
| 用户身份 | 姓名、学号、导师、院校 |
| 博士论文草稿 | 未发表的中期报告、开题报告 |
| 未发表稿件 | 投往期刊的稿件内容 |
| 审稿意见原文 | 匿名审稿人的具体意见 |
| 通讯信息 | 作者邮箱、投稿编号 |

## 允许进入记忆（脱敏后）

| 类别 | 示例 | 条件 |
|------|------|------|
| 审稿维度得分分布 | "citation_reliability 在 4 个任务中均为'需要关注'" | 不含论文内容 |
| 工作流教训 | "paper review task 中 manifest hash 不匹配导致 GPT 判 blocked" | 不含用户数据 |
| 模板使用经验 | "paper_iteration 模板在 init 后需要手动填写 PAPER_PROFILE.yaml" | 通用经验 |
| 合同适用记录 | "某 paper review 任务适用 CSSCI_REVIEW_CONTRACT" | 不引用论文 |
| 失败模式 | "synthetic paper 的 citation check 缺失导致 evidence 不完整" | synthetic only |
| 框架改进建议 | "paper review pipeline 缺少自动 citation verification 阶段" | 设计经验 |

## Memory Compiler 对论文源的特殊处理

`memory_compiler.py` 在处理 paper-* 相关 evidence pack 时：

1. **仅提取**：overall_judgment、blocking_reasons、missing_evidence 等结构字段
2. **禁止提取**：正文内容、引用表述、作者信息
3. **自动标记**：所有来自 paper 源的 memory entry 标记 `隐私分类: 论文相关`
4. **验证规则**：若提取到超过 200 连续中文字符的疑似正文内容 → 阻断并报警

## 与 MEMORY_PRIVACY_CONTRACT 的关系

本规则是 MEMORY_PRIVACY_CONTRACT 在论文场景的具体化。
所有论文相关 memory entry 必须通过 paper-specific redaction 后再写入。
