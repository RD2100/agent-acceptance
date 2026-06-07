# Paper Privacy Boundary

> 主题: paper_privacy
> 关联任务: PAPER-A2, PAPER-A3, PAPER-C1, PAPER-C2
> 最后更新: 2026-06-07
> 阅读时机: 涉及论文相关任务时

## 核心规则

论文隐私采取 protocol-only 模式。论文仅用于设计协议和安全边界，不进行真实文本处理。

## 禁止内容

以下内容不得出现在任何 memory、evidence pack 或代码提交中：
- 真实论文全文
- 用户论文片段
- 博士论文正文
- raw transcript
- private user text
- cookie / session / browser profile 数据
- api key / token / secret

## 已闭合的论文任务

- PAPER-C1: 真实论文安全协议（protocol-only，accepted）
- PAPER-C2: synthetic-only authorization/redaction gate（closed）
- PAPER-A3: 论文任务 validator 正式接入（accepted R2）
- PAPER-A2: 论文 IO 协议 + 脱敏证据包 + 隐私阻断（accepted R2）

## 当前状态

论文处理被 freeze。不进行 PAPER-C3 / 真实论文处理。所有 attention 转向治理基础设施。
