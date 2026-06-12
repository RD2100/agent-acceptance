# Codex 代码质量审查提示词

> 直接复制下方内容发送给 Codex 即可。

---

## 复制以下内容

```
对 agent-acceptance 仓库做一次代码质量审查。项目概况如下，请基于此上下文精准分析。

## 项目背景
这是一个 AI agent 治理框架，核心功能：
- SADP 工作流引擎（TaskSpec → 执行 → 测试 → 审查 → 归档）
- Shared-CDP 多项目 dispatch 系统（单 Chrome 实例 + ChatGPT conversation 隔离 + tab target resolver）
- ECS-A2 证据捕获标准（two-pass ZIP builder, manifest + SHA256）
- Governance hook 管线 v2.4.0（5 阶段：manifest-regen, sadp-audit, ai-guard, test-governance, conversation-health）
- 多项目注册表（PROJECT_REGISTRY.json + CONVERSATION_BINDING.json）

## 规模数据
- scripts/: 94 个 Python 文件，~24,570 行
- tests/: 74 个测试文件，~19,863 行，1260 个测试全部通过
- hooks/: 4 个 PowerShell 文件（pre-commit, pre-edit, pre-push, register）
- docs/agent-runtime/: ~60+ 个 Markdown 治理文档
- 仓库根目录: 84 个一次性脚本（_submit_*.py, _ask_*.py, _build_*.py, _capture_*.py 等）
- _evidence/: 104 个条目（证据目录 + ZIP 包）
- _reports/: 189 个条目
- 未跟踪文件: 193+

## 请逐项分析以下维度

### 1. 代码结构与架构
- scripts/ 下 94 个文件的职责划分是否合理？是否存在重复逻辑？
- 重点检查这些核心脚本的代码质量：
  - scripts/multi_project_router.py（路由核心）
  - scripts/dry_run_dispatch_10.py（dispatch 干跑）
  - scripts/tab_target_resolver.py（CDP tab 解析）
  - scripts/ai_guard.py（安全守卫）
  - scripts/build_evidence_pack.py（证据包构建器，72KB）
  - scripts/pre_commit_*.py 系列
- 模块耦合度：是否存在循环依赖？import 链是否清晰？

### 2. 根目录一次性脚本（84 个）
- 这些 _submit_*.py、_ask_*.py、_build_*.py、_capture_*.py 文件的代码质量如何？
- 是否存在大量重复代码（CDP 连接、Playwright 操作、响应捕获等）？
- 是否应该抽象为可复用的 CDP 交互层？给出具体的重复模式和数据。
- 哪些应该清理、哪些应该保留、哪些应该重构？

### 3. 测试质量
- 1260 个测试全部通过——但测试覆盖是否均匀？
- 核心路径（router、resolver、ai_guard、evidence_pack）是否有充分测试？
- 是否存在 mock 过度导致测试无意义的情况？
- 测试命名和组织是否规范？
- conftest.py 的 fixture 设计是否合理？

### 4. 安全与健壮性
- ai_guard.py 的安全检查是否覆盖所有敏感路径？
- CDP 交互（Playwright）是否有充分的错误处理和超时控制？
- JSON/YAML 解析是否有异常处理？
- 是否存在硬编码路径、密钥泄露、或注入风险？
- deny_paths 机制是否真正有效？

### 5. 可维护性
- 代码注释和 docstring 覆盖率如何？
- 是否存在过长的函数（>100 行）或过大的文件（>1000 行）？
- 魔法数字和硬编码是否应该提取为配置？
- 错误信息是否足够帮助调试？

### 6. 治理框架一致性
- .agent/PROJECT_REGISTRY.json 与 .ai/tasks/*.yaml 之间是否存在不一致？
- hooks/*.ps1 与 scripts/pre_commit_*.py 是否有职责重叠？
- docs/agent-runtime/ 中 60+ 个文档是否存在过时或重复？
- policies/ 目录中的策略文档是否与实际代码行为一致？

### 7. 技术债务评估
- 列出你认为最严重的 5 个技术债务，按严重程度排序
- 对每个债务给出：位置、影响范围、修复成本估算、不修的风险

### 8. 总体评分
请对以下维度分别打分（1-10）并简述理由：
- 代码质量（清洁度、一致性、可读性）
- 架构设计（模块划分、耦合度、扩展性）
- 测试质量（覆盖率、有效性、维护性）
- 安全性（输入验证、访问控制、注入防护）
- 可维护性（文档、注释、复杂度控制）
- 技术债务水平（1=无债务, 10=严重债务）

输出格式要求：
- 每个维度给出具体文件路径和行号引用
- 重复代码给出具体的相似度对比
- 安全问题给出 PoC 级别的示例
- 技术债务给出可操作的修复建议
- 最后给出一句话总结
```
