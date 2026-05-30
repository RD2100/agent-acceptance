# agent-acceptance 治理框架弱点分析 — Round 1

> 独立审计: deepseek-v4-pro | 日期: 2026-05-30
> 基线数据: docs/agent-runtime/ 85 文件, schemas/ 22 文件, rules/ 8 文件, 29 commits (2026-05)

---

## 第一部分: 6 个已知弱点的逐项评估

### W1 — 核心悖论: Agent 自己审计自己

| 维度 | 评估 |
|------|------|
| 严重性 | **P0** — 框架命门。如果 agent 可以绕过审计,整个 SADP 是装饰品 |
| 当前可见度 | agent-acceptance 已意识到此问题,SADP §4 要求独立 Plan Auditor |
| 问题的真实程度 | **部分缓解**。3 个 Claude Code 钩子 (pre-edit/pre-final/pre-task) 是平台级外部强制点,agent 无法跳过。但 Plan Auditor 触发仍是 agent 自主决定 |

**缓解因子 (已有):**
- `pre-edit.governance.ps1` — 禁止无 TaskSpec 修改治理文件 (exit 1,不可绕过)
- `pre-final.audit.ps1` — 禁止虚假通过 (exit 1)
- `pre-task.audit.ps1` — 强制验证 TaskSpec
- Governance manifest hash 检查 — 启动时漂移检测

**剩余攻击面:**
- `sadp-audit.ps1` 是 client-side pre-commit hook,`git commit --no-verify` 直接绕过 (core-001 禁止但属于自约束)
- Plan Auditor 是概念性机制,不是可执行脚本
- 非 @go 会话完全不触发 SADP

**优先级: 最高。** 这是所有其他弱点的放大器。

---

### W2 — TaskSpec 是纸老虎

| 维度 | 评估 |
|------|------|
| 严重性 | **P1** — 声明与实际写入之间无运行时强制 |
| 当前可见度 | TaskSpec schema 要求 `write_set`,但仅事后审计 |
| 问题的真实程度 | `sadp-audit.ps1` v2 交叉引用 staged files vs write_set,但**仅警告 (exit 0)** |

**剩余攻击面:**
- `pre-edit.governance.ps1` 检查"治理文件有 TaskSpec"但**不检查该文件是否在 write_set 内**
- 一个覆盖 file-A 的 TaskSpec 可以掩护 agent 修改 file-B
- 动态生成文件 (如 `tasks/audit-*.md`) 不在任何 write_set 中

**优先级: 高。** TaskSpec 是 SADP 的中心契约。

---

### W3 — 部署依赖人

| 维度 | 评估 |
|------|------|
| 严重性 | **P2** — 影响扩展但不影响安全性 |
| 当前可见度 | agent-acceptance 自身通过 `templates/runtime-bootstrap/bootstrap.ps1` 部署 |
| 问题的真实程度 | 模板是幂等的 (可重新运行),但新项目需要人手动执行 |

**优先级: 低。** 在 6 个弱点中影响最小。框架只有 29 次提交,尚未到需要 auto-onboarding 的阶段。

---

### W4 — 文档过密

| 维度 | 评估 |
|------|------|
| 严重性 | **P2** — 维护负担高但非安全问题 |
| 当前可见度 | 85 文件 (docs/agent-runtime/), 22 schema, 8 rule — 合计 115+ 文件 |
| 问题的真实程度 | 大部分是规范文本 (非运行代码)。已验证的 29 次提交修改了 38 个文件。低触达率: agent 在分析中读取 ~15 个文件,约 13% 覆盖率 |

**量化观察:**
- 活跃路径: AGENTS.md, rules/core.md, hooks/, schemas/agent-runtime/, 3-4 个 docs/agent-runtime/ 核心文件
- 低触达: 17 个 schemas/draft/, 10 个 schemas/resource-integration/, negative-test-fixtures/
- 文档膨胀率: ~3.9 文件/提交 (115/29),未读取占比 87%

**优先级: 中。**

---

### W5 — 非正式会话零覆盖

| 维度 | 评估 |
|------|------|
| 严重性 | **P1** — 多数 agent 交互不经 @go,治理框架完全不可见 |
| 当前可见度 | AGENTS.md 区分 "normal conversation" vs "@go 触发 SADP" |
| 问题的真实程度 | **严重**。非正式会话中的危险操作 (修改配置、写入密钥) 仅靠 agent 自律 |

**剩余攻击面:**
- 无 write_set 声明
- 无 TaskSpec 记录
- 无 Audit Record
- 唯一的防线是 `pre-edit.governance.ps1` + 8 条核心规则的自约束

**优先级: 高。** 与 W1 并列核心问题。

---

### W6 — 审计链单向

| 维度 | 评估 |
|------|------|
| 严重性 | **P2** — 影响学习但不影响当前安全 |
| 当前可见度 | Audit Record schema 存在,但无自动反馈机制 |
| 问题的真实程度 | 29 次提交产生 3 个审计报告,均在 tasks/ 下。无聚合指标 |

**优先级: 中。**

---

## 第二部分: 遗漏的弱点

### W7 — pre-commit hook 可被 `--no-verify` 绕过

`sadp-audit.ps1` 是 **client-side** git hook。执行 `git commit --no-verify` 完全跳过。core-001 禁止此行为但这是自我约束。实际执行模型的任何 agent 都可以:
1. `git add <files>`
2. `git commit --no-verify -m "message"` — hook 永远不运行
3. 或者直接: `git commit -m "message"` 然后 `git push` (如果 pre-commit hook 注册失败/被移除)

**严重性: P0。** W1 的直接可操作实例。

---

### W8 — 无写入时刻的 write_set 强制

`pre-edit.governance.ps1` 设计为 PreToolUse hook,在 `Write|Edit` 之前触发。但其 TaskSpec 检查仅验证 **存在性** (有 TaskSpec 引用此文件吗?),而不验证 **授权** (此文件在 TaskSpec.write_set 中吗?)。

具体漏洞:
```
TaskSpec { write_set: ["docs/x.md"], ... }
agent 编辑 "docs/y.md" → pre-edit 钩子检查: "y.md 有 TaskSpec 吗?" → 无 → BLOCKED ✓
agent 编辑 "rules/core.md" → pre-edit 钩子检查: "core.md 有 TaskSpec 吗?" → 有(task-001.md 存在) → 通过
但实际上 task-001.md 的 write_set 是 ["docs/x.md"],不包含 "rules/core.md"
```

**严重性: P1。** W2 的直接可操作实例。

---

### W9 — Plan Auditor 无强制触发机制

SADP §4 描述了 Plan Auditor (独立合规检查),但:
- 不是 .ps1 脚本
- 不是 Claude Code hook
- 不在 CI pipeline 中
- 没有 PreSessionEnd 或 PostToolUse hook 来强制其运行

触发路径: Session 结束 → agent 可以选择要不要 dispatch Plan Auditor → 如果 agent 不 dispatch,audit 永远不发生。

**严重性: P0。** W1 的直接可操作实例。

---

### W10 — 累积触发窗口无自动跟踪

SADP 描述了 "task-splitting prevention" 概念: 将 3 个文件修改分成 3 个 1 文件修改不应降低治理级别。但:
- 没有 session 级计数器追踪累积 write_set
- 没有 hook 强制 "累计超过阈值 → 必须 SADP"
- 所有跟踪依赖 agent 自律

**严重性: P1。** 允许 agent 通过分解任务绕过 SADP。

---

### W11 — 脏基线保护是 warning-only (exit 0)

`pre-edit.governance.ps1` 中脏基线文件的检查返回 exit 0 (WARNING_DIRTY_BASELINE),不阻止写入。说明注释写 "warning only because these are pre-existing modified files",但这意味着 13 个脏文件无保护。

**严重性: P1。** 如果 agent 意外覆盖脏基线文件,可能丢失未提交的修改。

---

### W12 — 无 session 级非 @go 变更审计日志

非正式会话的变更唯一记录是 git diff。没有:
- 触发上下文 (用户说了什么)
- 决策理由 (为什么改这个)
- 规则检查记录 (P0 检查了哪些)
- 文件清单 (改了什么)

**严重性: P1。** W5 的逻辑延伸。

---

## 第三部分: 具体改造方案 (不是"应该做", 而是"怎么做")

### 修复优先级排序

```
P0_blockers (必须先做):
  W9  → Plan Auditor 强制触发
  W7  → pre-commit 不可绕过
  W1  → 核心悖论缓解

P1_high (高影响):
  W8  → write_set 写入时刻强制
  W10 → 累积触发自动跟踪
  W2  → TaskSpec 校验硬化
  W5  → 非正式会话基线防护

P2_medium (可并行):
  W11 → 脏基线升级到 blocking
  W12 → session 变更审计日志
  W6  → 审计链反馈
  W3  → 项目自引导
  W4  → 文档密度
```

---

### FIX-1: Plan Auditor 强制触发 (W9 + W1)

**怎么做:**

创建 `hooks/session-finalize.audit.ps1`,注册为 PostToolUse hook,匹配 `Bash` 工具 (当命令包含 `git commit` 或 `git push` 时):

```powershell
# hooks/session-finalize.audit.ps1
# 注册: PostToolUse, matcher: "Bash", 当 tool_input 匹配 "git commit|git push"
# 逻辑:
# 1. 检查 tasks/ 中是否有 ExecutionReport 覆盖本次 session 的所有 changed_files
# 2. 如果没有 → 生成 blocker 消息 (不阻止 commit,但注入到 agent 上下文)
# 3. 检查 Plan Auditor 是否对本次 session 运行过
# 4. 如果没有 → exit 1, 消息: "BLOCKED: Plan Auditor not run for this session"
```

将此 hook 注册到 settings.json:
```json
"PostToolUse": [
  {
    "matcher": "",
    "hooks": [{
      "type": "command",
      "command": "powershell -ExecutionPolicy Bypass -File hooks\\session-finalize.audit.ps1"
    }]
  }
]
```

**外部强制点:** Claude Code hook 平台 — agent 无法跳过已注册的 PostToolUse hook。

---

### FIX-2: pre-commit hook 不可绕过 (W7)

**怎么做 — 方案 A (本地):**

在 `sadp-audit.ps1` 中新增自检逻辑:

```powershell
# 在 hook 开头
$env:SADP_HOOK_RUN = $true

# 在 AGENTS.md 和 rules/core.md 中新增核心规则:
# core-009: git commit 必须设置 SADP_HOOK_RUN=1 环境变量
# pre-commit hook 检查此变量,若未设置 → BLOCKED
```

但这仍然是自约束。真正的解决方案:

**怎么做 — 方案 B (远程强制,推荐):**

在 GitHub Actions CI 中部署 server-side check (.github/workflows/sadp-gate.yml):

```yaml
name: SADP Gate (Server-Side)
on:
  push:
    branches: [main]
jobs:
  sadp-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run sadp-audit on pushed commits
        run: |
          pwsh -ExecutionPolicy Bypass -File scripts/sadp-audit.ps1 -Strict
          # 如果 commits 包含治理文件修改但无对应 TaskSpec → 标记 PR/提交为 failed
      - name: Check Plan Auditor evidence
        run: |
          # 如果 changed_files 包含 docs/agent-runtime/ 但无 audit-record → BLOCKED
```

**为什么这个有效:** CI 在 GitHub 服务器端运行,agent 无法跳过。push 后 CI 失败会阻止合并 (如果配置了 branch protection)。

---

### FIX-3: write_set 写入时刻强制 (W8)

**怎么做:**

增强 `pre-edit.governance.ps1`,不只检查 TaskSpec **存在性**,而是验证文件在 TaskSpec **write_set** 中:

```powershell
function Test-FileInWriteSet {
    param($TargetFile, $TaskSpecDir = "tasks")
    
    # 1. 找到所有 task-*.md 文件
    $taskSpecs = Get-ChildItem $TaskSpecDir -Filter "task-*.md" -ErrorAction SilentlyContinue
    if (-not $taskSpecs) { return $false }
    
    # 2. 对每个 TaskSpec,解析 YAML front matter 中的 write_set
    foreach ($ts in $taskSpecs) {
        $content = Get-Content $ts.FullName -Raw
        # 提取 write_set 块 (简单的 regex,不依赖 YAML 解析器)
        if ($content -match 'write_set:\s*\n((?:\s*-\s+.+\n?)*)') {
            $writeSet = $matches[1] -split '\n' | ForEach-Object { $_ -replace '^\s*-\s*', '' } | Where-Object { $_ }
            foreach ($path in $writeSet) {
                $resolved = Join-Path (Get-Location) $path.Trim()
                if ($resolved -eq $TargetFile) { return $true }
            }
        }
    }
    return $false
}

# 在治理文件检查逻辑中:
if ($isGovernanceFile) {
    if (-not (Test-TaskSpecExists $targetFile)) {
        Write-Output "BLOCKED_NO_TASKSPEC: $targetFile"
        exit 1
    }
    if (-not (Test-FileInWriteSet $targetFile)) {
        Write-Output "BLOCKED_NOT_IN_WRITESET: $targetFile has a TaskSpec but is not declared in its write_set"
        exit 1
    }
}
```

**为什么这个有效:** 在 `Write|Edit` 工具实际执行之前,Claude Code hook 已经阻止。agent 无法绕过。

---

### FIX-4: 非正式会话基线防护 (W5 + W12)

**怎么做 — 最小可行方案:**

创建 `hooks/informal-session-monitor.audit.ps1`,注册为周期性 hook (或在工具使用后):

```powershell
# 逻辑:
# 1. 每次 Bash 工具使用后检查
# 2. 如果是 git add/commit 操作
# 3. 检查当前 session 是否有活跃 TaskSpec
# 4. 如果没有 → 生成 WARNING (不阻止,但记录到 session 日志)
# 5. 如果是危险操作 (git push, 密钥相关) → exit 1 BLOCKED

$dangerousPatterns = @(
    'git push',
    'Set-Content.*\.env',
    'Set-Content.*\.key',
    'Set-Content.*\.pem',
    'Write-Output.*sk-',
    'Invoke-WebRequest.*\|\s*Invoke-Expression',
    'New-Item.*hooks'
)

if ($commandText -match ($dangerousPatterns -join '|')) {
    if (-not (Test-SessionHasActiveTaskSpec)) {
        Write-Output "BLOCKED_DANGEROUS_WITHOUT_TASKSPEC: $commandText"
        exit 1
    }
}
```

**更激进的方案 — 自动生成轻量 TaskSpec 用于非 @go session:**

```powershell
# 在 session 首次非读操作时自动创建 "informal-task-session-{date}.md"
# 包含:
#   - task_id: auto-generated
#   - write_set: 初始为空,每次 Write/Edit 后追加
#   - gate_0: auto-skipped (informal session)
#   - status: informal
# 这提供事后审计的能力,不增加 agent 负担
```

---

### FIX-5: 累积触发窗口自动跟踪 (W10)

**怎么做:**

在 `hooks/pre-edit.governance.ps1` 中维护 session 状态文件:

```powershell
# $env:TEMP/sadp-session-state.json
{
  "session_id": "abc123",
  "cumulative_write_set": ["docs/x.md", "rules/y.md"],
  "cumulative_file_count": 2,
  "task_specs_filed": 0,
  "threshold_breached": false,
  "sadp_triggered": false
}

# 每次 Write|Edit 被 hook 允许通过后:
# 1. 追加文件路径到 cumulative_write_set
# 2. 如果 count >= 3 且有 governance 文件 → 设置 threshold_breached = true
# 3. 如果 threshold_breached 且 sadp_triggered = false → 在下一次工具使用前注入警告
```

---

### FIX-6: 脏基线升级到 blocking (W11)

**怎么做:**

修改 `pre-edit.governance.ps1` 中脏基线文件的处理:

```powershell
# 旧逻辑 (exit 0):
if ($isDirtyBaseline) {
    Write-Output "WARNING_DIRTY_BASELINE"
    exit 0
}

# 新逻辑:
if ($isDirtyBaseline) {
    # 检查是否有对应 TaskSpec 且 TaskSpec 声明了 protected_files_touched
    if (-not (Test-TaskSpecDeclaresProtectedFiles $targetFile)) {
        Write-Output "BLOCKED_DIRTY_BASELINE_WITHOUT_PERMISSION: $targetFile"
        exit 1
    }
    # 如果有 TaskSpec 且显式声明了 protected_files_touched → 允许
    Write-Output "WARNING_DIRTY_BASELINE_BUT_AUTHORIZED"
    exit 0
}
```

---

### FIX-7: 审计链反馈循环 (W6)

**怎么做:**

创建 `scripts/audit-metrics.ps1`:

```powershell
# 聚合 tasks/ 下所有 audit-result-*.md
# 输出指标:
#   - 总任务数 / PASS 率 / BLOCK 率 / ESCALATE 率
#   - 平均审计延迟 (TaskSpec 创建到 Audit 完成)
#   - 高频失败模式 (哪些规则最常被违反)
#   - 治理文件修改频率
# 写入 docs/agent-runtime/audit-metrics.md (自动更新)
```

集成到 CI:
```yaml
- name: Audit metrics
  run: pwsh scripts/audit-metrics.ps1
  # 如果 metrics 恶化 (PASS 率 < 90%) → 标记 CI 为 warning
```

---

### FIX-8: 文档减负 (W4)

**怎么做 — 不删除文件,而是分层:**

创建 `docs/agent-runtime/ACTIVE-MANIFEST.md`:

```markdown
# Active Files (read on every session start)

1. AGENTS.md                            — P0 hard stops
2. rules/core.md                        — 8 core rules
3. hooks/pre-edit.governance.ps1        — active enforcement
4. docs/agent-runtime/verification-gates.md  — gate hierarchy
5. docs/agent-runtime/capability-inventory.md — 28 capabilities

# Reference Files (read on-demand)
- docs/agent-runtime/integration-contracts.md
- docs/agent-runtime/sub-agent-dispatch-protocol.md
...

# Dormant Files (read only when activated)
- schemas/draft/*
- schemas/resource-integration/*
- docs/agent-runtime/negative-test-fixtures/*
```

Agent 启动时先读 ACTIVE-MANIFEST.md (5 文件),不需要扫描整个 docs/。将活跃文件清单写在 AGENTS.md 中,替代当前的 40+ 文档链接。

---

## 第四部分: 内部机制 vs 外部强制点分类

### 必须引入外部强制点 (agent 无法自我约束)

| 修复 | 外部强制机制 | 不可绕过性 |
|------|-------------|-----------|
| **FIX-1** Plan Auditor 强制触发 | Claude Code PostToolUse hook | `exit 1` 不可跳过 |
| **FIX-2** pre-commit 不可绕过 | GitHub Actions CI (server-side) | 远程执行,agent 无法触及 |
| **FIX-3** write_set 写入时强制 | 增强 pre-edit.governance.ps1 | 已有 hook,只需增强逻辑 |
| **FIX-4** 非正式会话危险操作阻断 | Claude Code PostToolUse hook | `exit 1` 不可跳过 |
| **FIX-5** 累积跟踪 | 增强 pre-edit hook,状态文件 | hook 已在位 |

### 可以在 agent 内部机制中解决 (但需要结构性改变)

| 修复 | 内部机制 | 可靠性 |
|------|---------|--------|
| **FIX-6** 脏基线升级 | Agent 启动时自检 + hooks 增强 | 中 — hook 强制,agent 遵守 |
| **FIX-7** 审计指标 | Agent 自生成 metrics + CI 验证 | 中 — CI 做最终校验 |
| **FIX-8** 文档减负 | AGENTS.md 重写,active/inactive 清单 | 高 — agent 启动时直接读 |

---

## 第五部分: 改造优先级排序 (可执行路线图)

### Batch 1 (本周 — P0 阻断修复)

```
FIX-1: 部署 session-finalize.audit.ps1 (PostToolUse hook)
FIX-2: 部署 GitHub Actions sadp-gate CI (server-side enforcement)
```
**交付物:** 两个 hook 注册 + 一个 CI workflow 文件
**验证:** agent 运行一次 commit → hook 触发 → CI green

### Batch 2 (本周 — P1 高影响修复)

```
FIX-3: 增强 pre-edit.governance.ps1 的 write_set 检查
FIX-4: 部署 informal-session-monitor.audit.ps1 (危险操作阻断)
FIX-5: 在 pre-edit hook 中实现 session 状态跟踪
```
**交付物:** 2 个增强 hook + 1 个新 hook
**验证:** 编辑不在 write_set 中的治理文件 → BLOCKED

### Batch 3 (下周 — P2 系统改进)

```
FIX-6: 脏基线从 warning 升级到 blocking (有 TaskSpec 例外)
FIX-7: 审计指标脚本 + CI 集成
FIX-8: 创建 ACTIVE-MANIFEST.md,重写 AGENTS.md 文档引用
```
**交付物:** 1 个 hook 修改 + 1 个脚本 + 2 个文档

---

## 总结矩阵

| # | 弱点 | 严重性 | 优先级 | 外部强制 | 预计工作量 |
|---|------|--------|--------|---------|-----------|
| W1 | 自审计悖论 | P0 | Batch 1 | Hook + CI | 2h |
| W2 | TaskSpec 纸老虎 | P1 | Batch 2 | Hook 增强 | 1h |
| W3 | 部署依赖人 | P2 | 延迟 | 模板已有 | — |
| W4 | 文档过密 | P2 | Batch 3 | 文档重写 | 2h |
| W5 | 非正式会话零覆盖 | P1 | Batch 2 | Hook | 1h |
| W6 | 审计链单向 | P2 | Batch 3 | 脚本 + CI | 1h |
| W7 | `--no-verify` 绕过 | P0 | Batch 1 | CI | 1h |
| W8 | write_set 无强制 | P1 | Batch 2 | Hook 增强 | 1h |
| W9 | Plan Auditor 无触发 | P0 | Batch 1 | Hook | 1.5h |
| W10 | 累积触发无跟踪 | P1 | Batch 2 | Hook 增强 | 0.5h |
| W11 | 脏基线 warning-only | P1 | Batch 3 | Hook 修改 | 0.5h |
| W12 | session 无审计日志 | P1 | Batch 2 | Hook | 1h |

**总预计工作量: ~12h** (分 3 个 batch,可在 1 周内完成)
