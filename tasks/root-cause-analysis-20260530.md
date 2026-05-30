# 治理框架根因分析与优化路线（定稿 v9）

> 来源：三轮深度审计 + 外部专家分析
> 日期：2026-05-30
> 基线：commit 0f99283
> 修订 v1-v8：迭代修正 P0 计数、技术方案、rollout 顺序、编号体系、manifest 权威源、完成定义等
> 定稿 v9：2026-05-30 — Layer 3 CODEOWNERS 补 archive/future、Test-Manifest placeholder 输入输出契约、canary suite 结构化输出 + schemaVersion、Commit 4 验收补 ignore 违规检查、验证方法论措辞精确化、路径表达式统一

## 修订版结论

本次审计显示，RD2100 Agent Runtime v2 的主要风险不是规则数量不足，而是治理执行链尚未形成可信闭环。P0 规则中存在两个重复簇（core-001 覆盖 git-001/git-002，core-002 覆盖 sec-001/sec-005/research-001），约 5 条分域规则存在重复占位。更紧迫的风险在于：退出码捕获失真导致 batch/WorkQueue 验证结果不可信，唯一活跃 hook 可被 Bash 绕过，4 个 inactive hook 中 3 个阻断代码不可达，batch JSON 引用不存在资源，治理文档与规则、schema、manifest、能力清单之间缺少交叉验证。

修复顺序：先修复退出码与密钥扫描（测量基座），再建立 repo diff 层 gate，先清理已知问题再启用 blocking，随后降级旧 hook 并归档剩余资产，最后通过 drift check 防止漂移复发。

---

## 一、核心诊断

**结论先行：当前的问题不是"规则还不够多"，而是验证链本身不可被信任。**

关键信号：
- Batch/WorkQueue 退出码失真——所有任务判决不可靠
- pre-edit hook 可被 Bash 工具绕过——唯一活跃 enforcement 点有已知绕过路径
- 4 个 inactive hook 中 3 个为 dead-blocking hook（阻断代码不可达），1 个为 unregistered-but-usable hook（pre-final，fake-green 检测可达但未注册）
- 规则/文档/schema/计数互相漂移——同一个事实在多个文件中不一致
- 7 个文件硬编码了 `C:\Users\RD\` 路径——换机即失效

**根因一句话：这是一个"文档型治理系统"伪装成"执行型治理系统"的问题。**

---

## 二、五个系统性根因

### 根因一：权威源不清，导致治理资产互相复制、互相漂移

`rules/README.md`、`rules/*.md`、manifest、schema、capability registry、batch JSON 都在重复表达同一批治理事实。

具体表现：
- P0 计数矛盾：`core.md:157` 将 P1 的 core-004 计入 P0
- Phase 0-5 边界：`review.md`/`research.md` 与 `README.md` 不一致
- 能力清单：汇总表、护照摘要、详细条目三处数据矛盾
- manifest 哈希仅覆盖 2 个文件，遗漏 87% 治理面

### 根因二：验证框架没有验证自己，导致"测试系统失真"

- `Run-Batch.ps1:108`：`$LASTEXITCODE` 永远过期，`$actualExit` 始终为 0
- `Run-WorkQueue.ps1:139`：`State -eq 'Completed'` 对所有正常结束返回 true
- `sadp-audit.ps1:139`：`$block = $false` 覆盖 V2 strict mode 阻断赋值
- `sadp-audit.ps1`：`exit 2` 从未调用，WARN 时 exit 0

### 根因三：enforcement 放在 agent 自愿经过的路径上

`pre-edit hook` 只拦截 Write/Edit 工具，Bash 写文件可绕过。正确边界应是 **repo diff**。

### 根因四：规则体系追求覆盖感

17 条 P0 展开为约 11 个独立概念。两个重复簇：core-001 与 git-001/git-002，core-002 与 sec-001/sec-005/research-001。根规则、分域规则和解释性规则共同占用 P0 配额。

P0 应区分两类：**安全阻断型 P0**（破坏性 git、密钥泄露、命令注入、路径遍历、伪造验证结果）和 **治理完整性 P0**（Phase 边界、能力注册、验证链完整性）。

### 根因五：保留无效资产，制造虚假治理覆盖率

| 无效资产 | 详情 |
|---------|------|
| 4 个 inactive hook 中 3 个 dead-blocking | ~300 行死代码 |
| `batch-local-quality.json` | 11/12 任务引用不存在资源 |
| `schemas/draft/` + `schemas/resource-integration/` | 27 个 schema，无消费者 |
| `evidence-index.schema.json` | 文档声称字段实际不存在 |
| `governance-manifest.md` | 仅覆盖 2 个文件且 hash 过期。此为历史文档，**active manifest 权威源为 `hooks/sealed-files-manifest.json`** |

---

## 三、验证方法论

三轮独立审计。已确认的代码 bug 和跨文件矛盾均经逐行代码验证；后续修复路线为基于这些问题的架构性处置方案。

### 编号体系

| 编号前缀 | 含义 | 数量 |
|---------|------|:---:|
| **CB1-CB6** | 原始代码 Bug | 6 |
| **CF1-CF5** | 跨文件矛盾 | 5 |
| **IC1** | 完整性控制缺陷（manifest 覆盖不足 + hash 过期） | 1 |
| **SF1-SF6** | 结构性修复 | 6 |

### 原始代码 Bug（CB1-CB6）

| # | 位置 | 问题 |
|---|------|------|
| CB1 | `Run-Batch.ps1:108` | `$LASTEXITCODE` 永远过期 |
| CB2 | `Run-WorkQueue.ps1:139` | `State -eq 'Completed'` 对所有正常结束返回 true |
| CB3 | `sadp-audit.ps1:139` | `$block = $false` 覆盖 V2 阻断赋值 |
| CB4 | `sadp-audit.ps1` | `exit 2` 从未调用，与项目约定相反 |
| CB5 | `ai_guard.py` | 未 `chdir(repo_root)`，密钥扫描静默跳过 |
| CB6 | `batch-local-quality.json` | 11/12 任务引用不存在资源 |

### 跨文件矛盾（CF1-CF5）

| # | 问题 | 决策 |
|---|------|------|
| CF1 | `core.md:157` P0 count 含 P1 的 core-004 | core.md 内部 P0 count 改为 6，不改变全局统计口径 |
| CF2 | `review.md:4` "all rules active" | 改为 "P0/P1 active; P2-P4 within approved task scope" |
| CF3 | `research.md:4` 同上 | 同上 |
| CF4 | Memory 写入 AGENTS.md vs hook 冲突 | Phase 0-5：memory writes blocked by default |
| CF5 | 能力清单三处数据矛盾 | 详细条目 = source of truth；删除汇总表 verified 列；护照摘要从详细条目生成。纳入 Commit 4 drift check（第 5 项） |

### 完整性控制缺陷（IC1）

| # | 问题 | 修复 |
|---|------|------|
| IC1 | manifest 仅覆盖 2 个文件且 hash 过期 | 历史文档标注 legacy。active manifest 统一为 `hooks/sealed-files-manifest.json`。自动化由 Commit 4 建立 |

### 结构性修复（SF1-SF6）

| # | 问题 | 修复 |
|---|------|------|
| SF1 | 7 个文件硬编码路径 | 改为 `$PSScriptRoot` 或环境变量 |
| SF2 | `integration-contracts.md` schema 路径错误 | 与 Commit 2b schema 迁移同一 commit 完成 |
| SF3 | `integration-contracts.md` 引用不存在文件 | 删除或标注 Phase 6 |
| SF4 | `SKILL.md` 死引用 | 删除 |
| SF5 | `evidence-index.schema.json` 字段过期 | **决策：Phase 0-5 不扩展 schema。从 integration-contracts.md 删除 freshness/currency_basis/approved_run_id 声称。Phase 6 如需，通过 schema migration 加字段。** |
| SF6 | schema README 计数错误 | 更新为 9 |

---

## 四、优先级判断：如果只能修 3 件事

### 第一件：修复执行基座，统一退出码语义

**统一退出码**：0 PASS / 1 BLOCKED / 2 INFRA_ERROR

**核心修复**：
- CB1-CB2：Run-Batch/WorkQueue 退出码捕获
- CB3-CB4：sadp-audit `$block` 覆盖 + 退出码统一
- CB5：ai_guard.py `cwd=str(repo_root)` + `repo_root / relative_path`

**退出码封装**：新增 `scripts/lib/Process.psm1`，导出 `Invoke-CheckedCommand`。静态检查使用 PowerShell AST，禁止治理脚本裸读 `$LASTEXITCODE`（Process.psm1、comments、markdown、tests 除外）。

**E2E canary**：
```
case-001 ~ case-004: exit 0/1/2/timeout 行为正确
case-005 ~ case-006: sadp-audit strict violation / warning only
case-007 ~ case-008: ai_guard 密钥检测 + 子目录运行
```

### 第二件：enforcement 从"工具层"迁移到"repo diff 层"

**模块化 gate 系统**：

```
scripts/Test-Governance.ps1              # orchestrator
scripts/checks/Test-ProtectedPaths.ps1
scripts/checks/Test-Secrets.ps1          # 调用 ai_guard.py，不重复实现规则
scripts/checks/Test-Manifest.ps1         # Commit 2a 为 placeholder；Commit 4 正式接入
scripts/checks/Test-RulesConsistency.ps1
scripts/checks/Test-BatchReferences.ps1
scripts/checks/Test-DocsExist.ps1
scripts/checks/Test-FakeGreen.ps1
scripts/checks/Test-SchemaDocsConsistency.ps1
```

**关键子检查器输入与判定规则**：

`Test-Secrets.ps1` — 调用 `ai_guard.py` 并解析结果，不重复实现规则。**必须通过 `Invoke-CheckedCommand` 调用**，不能直接调用 python 后读取 `$LASTEXITCODE`。退出码映射：

```
ai_guard exit 0   → no violation  → Test-Secrets PASS
ai_guard exit 1   → secret found  → Test-Secrets BLOCKED
ai_guard exit 2   → scanner error → Test-Secrets INFRA_ERROR
ai_guard 其他退出码或无法启动     → Test-Secrets INFRA_ERROR
```

`Test-FakeGreen.ps1` — 只检查结构化 JSON report（ExecutionReport / batch result JSON / WorkQueue report），不检查 markdown。三类 report 均需声明 `schemaVersion`；未声明的按 legacy report 处理。判定依据：

```
- actualExit != expectedExit 但 finalStatus == PASS  → BLOCKED
- child task status 为 FAILED/BLOCKED 但 parent summary 为 PASS → BLOCKED
- auditor BLOCKED 但 execution summary 为 PASS → BLOCKED
- 声明为 current schema version 的 report，判定所需字段缺失 → INFRA_ERROR
- legacy report（无 schemaVersion 或非 current），字段缺失 → warning only，不参与 blocking
```

**Test-Governance 分阶段定义**：

```
Commit 2c 后：Test-Governance = authoritative diff gate（不含完整 manifest enforcement）。
             Test-Manifest.ps1 只输出 warning，不参与 Test-Governance 的 blocking exit code 计算。
Commit 4 后：Test-Governance + Test-GovernanceDrift = complete governance gate。
             Test-Manifest.ps1 正式接入 blocking 判定。
```

**Test-Governance vs Test-GovernanceDrift 职责边界**：

```
Test-Governance.ps1：增量 diff 检查，阻断本次变更。
Test-GovernanceDrift.ps1：全量漂移检查，周期性 CI 全量一致性。
权威实现只有一份，通过 scripts/checks/shared/ 共享纯函数解析器。
shared/ 只允许放 Parse-RuleIds、Parse-Priority、Resolve-ExpectedFiles 等纯函数。
不得放 orchestrator、I/O 副作用、CI 退出码逻辑。
```

**pre-edit 灰度迁移**：`Test-PreEditParity.ps1` 构造违规样本集对比两个入口。所有 canary 在临时隔离环境中运行。

**升级为 blocking 的条件**：
- Commit 2b 完成（已知问题已清理）
- 所有 8 个 E2E canary 通过
- Test-PreEditParity 持续 3 次独立 CI run 零漏报（至少覆盖 pull_request 或 PR-like 环境、push/branch 环境、manual workflow_dispatch；若项目暂未启用 PR，用临时分支 + workflow_dispatch 模拟 PR-like diff；至少一次 clean clone 环境）
- 3 个 self-canary 全部通过
- **Commit 2c 升级条件不包含 manifest mismatch canary**（manifest 自动化由 Commit 4 建立）

最终定位：

```
pre-edit.governance.ps1 = advisory early warning（降级后）
Test-Governance.ps1     = authoritative diff gate
Test-GovernanceDrift.ps1 = authoritative drift gate
GitHub Actions          = merge gate
```

### 第三件：建立 drift check

**Manifest 权威源**：`hooks/sealed-files-manifest.json`。旧 `governance-manifest.md` 标注 legacy。

**Manifest 自排除规则**：`Update-GovernanceManifest.ps1` 在展开 `expected-files.txt` 时，必须优先将 `hooks/sealed-files-manifest.json` 从 sealed_files 候选集中**硬编码移除**。该排除不可被 `manifest-ignore.txt` 覆盖或取消。manifest 自身不自哈希。

**manifest-ignore.txt 硬约束**：只能排除 archive/、future/、test fixtures（`scripts/tests/*.tests.ps1`）、临时输出目录（runs/、reports/、.backup/）。不得排除 rules/、hooks/、scripts/、governance/、.github/workflows/、AGENTS.md、.ai/policy.yaml。`Test-GovernanceManifest.ps1` 检查 ignore 规则是否合规。

**expected-files.txt**（glob pattern，由 Update 脚本 `Get-ChildItem -Recurse` + 自定义 glob resolver 显式递归解析，不依赖 shell 展开）：

```
rules/*.md
hooks/*.ps1
hooks/*.json
.ai/policy.yaml
.github/workflows/*.yml
scripts/**/*.ps1
scripts/**/*.psm1
governance/*.txt
governance/*.json
schemas/agent-runtime/*.json
docs/agent-runtime/*.md
batches/*.json
AGENTS.md
```

`batches/future/*.json` 不进入 active manifest（与 `archive/**` 和 `*/future/**` 一致）；若保留，仅作为 future/reference 资产。旧 `docs/agent-runtime/governance-manifest.md` 标注 legacy 后仍可被 `docs/agent-runtime/*.md` 匹配进入 manifest hash 保护范围，但其内容不参与 hash 权威判断（权威源为 `hooks/sealed-files-manifest.json`）。

**Test-GovernanceDrift.ps1**（5 项检查）：

```
1. rules/*.md rule id ↔ rules/README.md 双向核对
   格式约束：rules/*.md 中每条规则必须使用固定格式（Rule ID、Priority、Status 三个字段均需可解析）；
   缺失字段视为 INFRA_ERROR。
2. P0/P1 计数 vs README 声明（从 markdown 解析）
3. Phase 0-5 文案跨文件一致性（8 个规则文件）
4. manifest coverage check（覆盖面 + 存在性 + hash 一致性 + 反向检查）
5. capability inventory summary vs detailed entries consistency（CF5 长期防复发）
   格式约束：能力详细条目必须包含机器可解析的 CAP-ID 与 status 字段；
   护照摘要只能由这些字段聚合生成，不得手写。
```

> **快照声明**：本报告数字均为 2026-05-30 快照，不替代后续 drift check 实时结果。

---

## 五、架构决策：删除还是保留？

### inactive hook 处置

| Hook | 阻断可达？ | 处置 |
|------|:---:|------|
| `pre-final.audit.ps1` | 是（unregistered-but-usable） | fake-green 逻辑迁移到 `Test-FakeGreen.ps1`，外壳归档 |
| `pre-task.audit.ps1` | **否**（dead-blocking） | → `archive/draft-hooks/` |
| `pre-tool.audit.ps1` | **否**（dead-blocking） | → `archive/draft-hooks/` |
| `skill-intake-scan.audit.ps1` | **否**（dead-blocking） | → `archive/draft-hooks/` |

### batch JSON 处置

Commit 2b：`batch-local-quality.json` 移至 `batches/future/`，active=false。Commit 3 不再处理 batch。

### schema 处置

Commit 2b：`schemas/draft/` + `schemas/resource-integration/` 移至 `archive/schemas/`。SF2 同步完成路径更新。

### archive/ 与 future/ 最小治理策略

```
- 不计入 active governance surface
- 不参与 blocking gate
- 可被 manifest-ignore.txt 排除出 active manifest
- 但仍应由 CODEOWNERS 覆盖（修改不触发 blocking gate，但需 human review）
- 必须有 README 标注来源、迁移日期、恢复条件
- 恢复到 active surface 前必须补齐消费者、负例测试和 CI 接入
```

> `archive/**` 与 `*/future/**` 统一适用上述策略。

---

## 六、"agent 在治理 agent"的自指天花板

三层边界模型：Agent 自律层 → 仓库状态层 → 外部权限层。

**sealed-files-manifest.json 自身不自哈希**。其可信性依赖 CODEOWNERS、branch protection 与 required review。Layer 3 配置完成前，不得声称 manifest 具备强完整性保护。

### Layer 3 人工配置清单

```
- [ ] Branch protection (main):
      - required checks: AI Guard, Test-Governance (2c), Test-GovernanceDrift (Commit 4)
      - 禁止 direct push / force push

- [ ] CODEOWNERS（含 required review）：
      - rules/ hooks/ scripts/ .github/workflows/ governance/ batches/
      - schemas/agent-runtime/ docs/agent-runtime/
      - archive/ **/future/
      - AGENTS.md .ai/policy.yaml
      → 以上全部 @human-reviewer

- [ ] GitHub token 权限：
      - 默认 permissions: contents: read
      - 仅确需写入的 job 单独授最小写权限

- [ ] Secret scanning：
      - push protection（block 模式）+ alerts
```

---

## 七、最小可执行改造路线

### Commit Group 1：恢复测量可信度

#### 1a：退出码基座 + smoke batch
- `scripts/lib/Process.psm1` + `Invoke-CheckedCommand`
- 统一 exit code + 修 Run-Batch/Run-WorkQueue
- 新增 `batches/batch-smoke.json`
- PowerShell AST 静态检查

**验收**：case-001 ~ case-004 通过。

#### 1b：sadp-audit 一致性
- 修 `$block` 覆盖 + 退出码统一

**验收**：case-005 ~ case-006 通过。

#### 1c：ai_guard.py 测量可靠性
- `subprocess.run(cwd=str(repo_root))` + `repo_root / relative_path`

**验收**：case-007 ~ case-008 通过。

#### 1d：矛盾修复 + manifest legacy 处理
- CF1-CF5 + SF1 + SF3-SF6 修复
- SF2 延后至 Commit 2b
- IC1：旧 manifest 标注 legacy，自动化由 Commit 4 建立
- **SF5 决策**：从 integration-contracts.md 删除声称，不扩展 schema
- 手工 drift checklist

**验收**：CF1-CF5 + SF1 + SF3-SF6 修复。IC1 legacy 标注完成。

### Commit 2a：Test-Governance + Test-PreEditParity（advisory）

- `scripts/checks/` 8 个子检查器
- `Test-Manifest.ps1` 为 placeholder：只验证接口存在和 report 格式，不执行真实 manifest coverage/hash 判定（Commit 4 正式接入）
- `scripts/Test-Governance.ps1`（advisory，3 个 self-canary）
- `scripts/Test-PreEditParity.ps1`
- `scripts/tests/Invoke-GovernanceCanarySuite.ps1`（创建临时 repo + 注入样本 + 运行 canary + 清理）
- pre-edit 保持 blocking

**验收**：self-canary 全部通过。Test-PreEditParity 零漏报。canary 隔离运行。

### Commit 2b：清理已知问题（blocking 前）

- `batch-local-quality.json` 移至 `batches/future/`
- schemas 移至 `archive/schemas/` + SF2 同步
- draft hook 移至 `archive/draft-hooks/`
- schema README 计数更新

**验收**：Test-Governance advisory 零 false violation。8 个 E2E canary 通过。

### Commit 2c：Test-Governance 升级为 blocking

**升级条件**：Commit 2b 完成 + 8 canary 通过 + 3 次 CI 零漏报（3 个触发源，至少一次 clean clone）+ self-canary 通过。不包含 manifest mismatch canary。

**动作**：Test-Governance blocking（exit 1），CI required check。

### Commit 3：降级 pre-edit + 归档

- pre-edit 降级为 advisory
- Test-PreEditParity 移至 `scripts/tests/` 保留 1 周期

### Commit 4：治理漂移自动检测

- `governance/expected-files.txt` + `manifest-ignore.txt`（含硬约束检查）
- `Update-GovernanceManifest.ps1`（硬编码排除 manifest 自身）
- `Test-GovernanceManifest.ps1`（Update 后 git diff 非空 = CI fail）
- `Test-GovernanceDrift.ps1`（5 项检查，含 capability inventory consistency）
- `Test-Manifest.ps1` 从 placeholder 升级为正式接入
- `scripts/checks/shared/` 纯函数解析器
- CI required check

**验收**：5 项 drift check 全部通过。manifest 未同步、rules 不一致、能力清单矛盾均被 CI 阻断。manifest-ignore.txt 试图排除 rules/hooks/scripts/governance/workflows 等受保护路径时 CI 失败。

---

## 八、总结

**标准：只保留能在 clean clone 上运行、能产生真实退出码、能被 CI 强制执行、能被负例测试证明有效的治理资产。**

---

## 九、Phase 0-5 治理去幻觉化完成定义

```
- [ ] 1. clean clone 上 Invoke-GovernanceCanarySuite.ps1 → 全 suite 可完整运行（含 batch-smoke）
      并生成结构化 canary report（记录每个 case 的 actualExit、expectedExit、status）

- [ ] 2. E2E canary：
      case-001 ~ case-004: exit 0/1/2/timeout 行为正确
      case-005 ~ case-006: sadp-audit strict / warning 行为正确
      case-007 ~ case-008: ai_guard 密钥检测 + 子目录运行行为正确

- [ ] 3. Bash 写 protected path 被 Test-Governance（blocking mode）exit 1 阻断

- [ ] 4. secret canary 被 ai_guard 标记，并被 Test-Governance blocking gate 阻断
      （Test-Secrets.ps1 通过 Invoke-CheckedCommand 调用 ai_guard.py，退出码映射见第四节）

- [ ] 5. active blocking hooks 中无不可达阻断逻辑
      （advisory hooks 不计入阻断能力，但必须声明不会作为 enforcement 证据）

- [ ] 6. 所有 active batch 引用路径存在（Test-BatchReferences.ps1 通过）

- [ ] 7. active schema 文档/example/consumer 字段与实体一致
      （Test-SchemaDocsConsistency.ps1 通过）

- [ ] 8. manifest 覆盖所有 expected governance files 且 hash 最新
      （Update-GovernanceManifest 后 git diff 为空）
      注意：sealed-files-manifest.json 不自哈希，其可信性依赖 Layer 3 CODEOWNERS + branch protection。

- [ ] 9. rules/README/Phase/P0-P1 计数 + capability inventory summary vs detailed entries 均无漂移
      （Test-GovernanceDrift.ps1 5 项全部通过）

- [ ] 10. main 分支启用 required checks（AI Guard + Test-Governance + Test-GovernanceDrift）
       并对 rules/hooks/scripts/governance/workflows/batches/schemas/docs + archive/future 路径
       启用 CODEOWNERS required review
```

这样 RD2100 Agent Runtime v2 才会从"文档上很完整的治理框架"，转向"执行上可信的验收框架"。
