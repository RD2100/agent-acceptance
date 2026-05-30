# 第二轮：落地环境适配与工具链选型

你在上一轮给出了很好的三层架构方案，但有几个假设在我的实际环境中不成立。请针对以下约束重新评估。

## 我的实际环境

- **操作系统**：Windows（不是 Linux）
- **GitHub 账号**：个人账号（Free plan），不是 Organization
- **编程工具**：Codex 桌面端（内置 sandbox/approval 机制，可限制代理的文件系统和网络访问）
- **现有资产**：已有 pre-commit 扫描脚本、CI workflow、workflow skill（通过 `@go` 触发）

## 需要修正的问题

### 1. 沙箱方案：你提到的 Landlock/bubblewrap 是 Linux 独占

Windows 上没有这些内核级机制。用什么替代？
- Docker Desktop for Windows？
- Windows Sandbox？
- Codex 自带的文件系统 sandbox 是否已足够？
- 还是采用更轻量的方案，比如 PowerShell 脚本在执行前检查命令是否触及禁止路径？

### 2. GitHub Free 个人账号的限制

- GitHub Free 不支持 rulesets
- 不支持 required status checks（免费版只有基本的 branch protection）
- 不支持 organization-level reusable workflows
- 不支持 audit log API
- push protection 和 secret scanning 对公开仓库免费可用

在这些限制下，P0 保护主干方案是否还能做？怎么做？

### 3. Codex 自带的 sandbox/approval 能否复用？

Codex 桌面端有文件系统沙箱和审批机制。在不需要自建 `governor` 执行器的前提下，能否直接利用它来限制代理的文件写入范围和危险操作？如果 Codex sandbox 已经解决了"代理不能写超出范围的文件"，我们还需要 Docker 吗？

### 4. 现有 `@go` workflow skill 的去留

我已经有一个可用的 workflow skill，它提供：
- `@go` 触发
- TaskSpec 生成
- `opencode run` 自动分发任务
- 审计判定

在新架构中，它是保留不变、升级整合、还是被替换？如果整合，它在三层架构中属于哪一层？

### 5. OPA/Rego 是否过重？

我是单人开发者。OPA/Rego 的学习成本、维护成本和部署复杂度对我而言是否过高？能否用 Python 脚本或 CI YAML 中的条件判断替代？如果可以，请给出替代方案。

### 6. 成本重新评估

在 Windows + GitHub Free + 单人开发的约束下，最小可行版本 5 件事还剩几件能做？每件的具体实现方式是什么？哪些需要暂时放弃？

## 要求

1. 不要复述上一轮已经说过的内容
2. 针对 Windows 和 GitHub Free 约束给具体方案
3. 区分"现在就做"和"等有 Organization/企业版再做"
4. 对 Codex 自带的 sandbox 进行评估——能用就不要重复造轮子
5. 最终给出一个调整后的优先级排序