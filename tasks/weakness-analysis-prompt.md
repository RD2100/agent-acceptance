# agent-acceptance 治理框架弱点分析

## 背景

agent-acceptance 是一套 AI 辅助开发的治理框架，核心是 SADP（Sub-Agent Dispatch Protocol）：Gate 0 → TaskSpec → Execute → ExecutionReport → Audit → PASS/BLOCK/ESCALATE。

已部署项：
- AGENTS.md（P0 硬停规则 + 密钥安全规则 + 反过度工程守门）
- pre-commit hook（sadp-audit.ps1）
- CI gate（GitHub Actions）
- GitHub push protection
- workflow skill（@go 触发）

## 已识别的 6 个弱点

### 1. 核心悖论：Agent 自己审计自己
SADP 的 Plan Auditor 和 sadp-audit.ps1 都由同一个 agent 触发和运行。dispatch audit session 的动作仍是 agent 自主决定。agent 可以不 dispatch、可以伪造报告、可以手动改 verdict。真正的治理需要 agent 外部的触发点——CI、pre-commit hook 不能由 agent 绕过（但目前 `--no-verify` 可以绕过 hook）。

### 2. TaskSpec 是纸老虎
TaskSpec 要求声明 write_set，但实际写什么文件没有强制校验——只是事后 auditor 对比，auditor 可以被跳过。动态生成的文件不受约束，"Allowed Files" 豁免易膨胀。

### 3. 部署依赖人
新项目要 bootstrap 需要人手动跑脚本。没有"新项目自动接入"机制。workflow skill 刚刚部署但依赖 `@go` 显式触发。

### 4. 文档过密
docs/agent-runtime/ 下 40+ 文件，schemas/ 下 18 个，rules/ 下 7 个。大部分是规范文本不是运行代码，维护成本高，agent 不一定读全。

### 5. 非正式会话零覆盖
日常对话不触发 @go 时，不产生 TaskSpec、不经过 audit。agent 在非正式会话中执行危险操作（修改配置、写入密钥），治理框架完全看不到。

### 6. 审计链单向
Audit Record 记录了结果但没有反馈循环：FAIL 后无自动修复、ESCALATE 后无自动通知人、无累计指标。

## 要求

请从第三方视角：
1. 评价这 6 个弱点的严重性和优先级
2. 指出我可能遗漏的弱点
3. 提出具体的改造建议——不是"应该做"，而是"怎么做"
4. 区分哪些可以靠 agent 内部机制解决，哪些必须引入外部强制点
5. 给出改造的优先级排序

输出结构化分析，不要泛泛而谈。