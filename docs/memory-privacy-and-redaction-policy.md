# Memory Privacy and Redaction Policy

> 版本: 1.0.0-draft
> 权威来源: agent-acceptance

## 1. 默认原则

所有用户论文、博士论文、小论文、中期报告、未发表稿件**默认为 private**。
Memory layer 必须遵循此默认，未经显式授权不得降级为 public 或 team-readable。

## 2. 绝对禁止

以下内容**绝对不得**进入 memory：

| 类别 | 示例 | 原因 |
|------|------|------|
| 真实论文全文 | 用户论文的完整正文 | 用户隐私、知识产权 |
| 论文片段 | "某论文第三章提到……" | 可逆向识别 |
| 用户身份信息 | 姓名、学号、导师姓名、院校 | 隐私泄露 |
| 完整聊天 transcript | 整个对话记录 | 可能含论文全文、私密讨论 |
| API keys / secrets | 任何密钥 | 安全 |
| cookie / session / browser profile | 任何浏览数据 | 安全 |

## 3. 允许

| 类别 | 示例 | 条件 |
|------|------|------|
| 脱敏工作流教训 | "某任务出现 summary-only pack，GPT 判 review_unverified" | 不引用论文原文 |
| 通用失败模式 | "manifest 与 ZIP 不一致导致 GPT 判 blocked 3 次" | 不涉及用户 |
| 合约/模板设计经验 | "memory_compilation_contract 需要明确 source 必须可追溯" | 属于项目本身 |
| GPT review 中的审查意见 | "GPT 指出 pre_submission_check 需要在 build_evidence_pack 之后运行" | 不涉及论文内容 |

## 4. Redaction 示例

### 不允许

```
用户在论文"The Impact of Digital Technology on Classroom Interaction"中写道：
"本研究采用混合方法，通过问卷调查（N=300）和课堂观察（12节课）……"
```

### 允许

```
某 paper workflow 任务（REVIEW_RUN_ID: ref-paper-c7b7d692）中出现：
- synthetic paper 内容通过框架生成（synthetic_only=true）
- CSSCI 9 维度审查中 citation_reliability 评分"需要关注"
- 后续 GPT 审查 accepted
```

### 不允许

```
用户王某某的博士论文中期报告中提到她在做智慧教室方向的博士研究……
```

### 允许

```
某 thesis_midterm_review 任务中：
- 适用 THESIS_MIDTERM_REVIEW_CONTRACT
- gap_list 包含 3 个可操作项
- GPT 判 accepted
```

## 5. 引用规则

Memory entry 中如涉及具体任务，应引用：

- `REVIEW_RUN_ID`: 指向具体的 GPT review result
- `task_id`: 指向 WORKFLOW_AUDIT_LEDGER 中的任务
- 不复制全文，不引用论文正文

## 6. 安全边界

| 边界 | 值 |
|------|-----|
| 真实论文全文存储在 memory | false |
| 用户私有文本存储在 memory | false |
| 完整聊天 transcript 存储在 memory | false |
| 脱敏摘要存储在 memory | true（符合条件时） |
