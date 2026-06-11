# 流程硬化计划 — GPT-Agent 自动化交接流程

---

## 任务信息

| 字段 | 值 |
|------|-----|
| **task_id** | `HANDOFF-WORKFLOW-HARDENING-PLAN-A1` |
| **run_id** | `HANDOFF_WORKFLOW_HARDENING_PLAN_A1_20260609_012328` |
| **generated_at** | `2026-06-09T01:23:28+00:00` |
| **状态** | `plan`（本轮是计划任务，不直接实现硬化项） |
| **作者** | Agent (Claude Code) |
| **审批状态** | 待用户确认 |

---

## 一、当前 GPT-Agent 交接流程已完成的内容

经过多轮迭代（从 initial discovery 到 R4 审查循环），GPT-Agent 自动化交接流程已建立以下核心机制：

### 1.1 四层权威体系（P0/P1/P2/P3）

已在 `HANDOFF_SOURCE_OF_TRUTH.md` 中定义完整的权威层级：

- **P0（Canonical evidence sources）**：captured GPT verdicts（经 `verify_gpt_reply.py` 验证）、evidence packs、`TEST_OUTPUT` / `TARGETED_TEST_OUTPUT`、issue ledgers、manifests、git status / changed-files evidence
- **P1（GPT-reviewed handoff layer）**：GPT-approved `BOOT_CONTEXT.md`、GPT-approved handoff files、GPT-approved paste blocks、handoff approval records and manifests
- **P2（Recall layer）**：memory compiler / recall layer（`.claude/skills/claude-memory-compiler/knowledge/**`、`memory/index.md` 等）。Memory compiler output 仅可作为 recall context，不可作为 source of truth
- **P3（Legacy audit/reference layer）**：legacy `PROJECT_HISTORY*`、legacy `HANDOFF*`、legacy paste blocks、root-level `GPT_*.txt`（除非已在 evidence map 中验证并绑定）

冲突消解规则：P0 > P1 > P2 > P3。P3 材料不得覆盖 P0/P1 状态。同层以时间戳最新者为准。

### 1.2 附件版 GPT 审查 SOP 及固化脚本

- `ATTACHMENT_BACKED_GPT_REVIEW_RUNBOOK.md`：定义了完整的附件提交审查流程（10 步 SOP）
- `gpt_new_chat_attachment_submit.py`：入口脚本（当前为 1KB pointer），委托给 `_reports/handoff-pipeline-refactor-a1/_submit_new_chat_with_attachment_strict.py`
- 实际实现（`_submit_new_chat_with_attachment_strict.py`）支持：Playwright CDP 连接、新对话打开、composer 清空、附件上传确认、prompt 粘贴、可见按钮提交、user bubble 确认、run_id 匹配回复捕获
- **当前限制**：入口脚本尚未参数化，task_id / pack_path / run_id_path / output_path 均硬编码在实际实现中，复用到其他任务前需要参数化改造（详见 GAP-003）

### 1.3 GPT 回复 fail-closed 验证器

- `verify_gpt_reply.py`：对 GPT 回复进行结构化验证
- 验证维度：verdict 合法性（accepted / accepted_with_limitation / blocked / human_required）、run_id 一致性、END_OF_GPT_RESPONSE 标记存在性、必填字段完整性
- **fail-closed 原则**：任何验证失败均视为 `blocked`，不允许默认通过

### 1.4 Evidence Pack 工具链

- `evidence_pack_linter.py`：证据包结构和内容合规性检查
- `pre_gpt_review_gate.py`：提交 GPT 审查前的自动化门禁检查
- 检查项：文件完整性、hash 一致性、必填 section 存在性、引用有效性

### 1.5 Next-Agent 启动读门槛

- `NEXT_AGENT_REQUIRED_READS.json`：定义了 21 项必读文件清单
- 覆盖：治理规则、当前任务上下文、历史交接记录、安全约束
- 目标：确保下一个 agent 在开始工作前具备充分的项目上下文

### 1.6 已执行的 GPT 审查循环

至少两轮完整的 GPT 审查已成功执行并捕获 verdict：

| 任务 | Verdict | 关键发现 |
|------|---------|----------|
| `HANDOFF-PIPELINE-REFACTOR-A1` | `accepted_with_limitation` | 流程管线重构方向正确，但部分自动化脚本需补充边界测试 |
| `GLOBAL-PROJECT-EVIDENCE-BINDING-A1-R4` | `accepted_with_limitation` | 证据绑定机制完整，legacy 文件操作需额外安全约束 |

### 1.7 其他已建立机制

- **语义保护规则**：明确定义了不可破坏的语义约束（如不可伪造 verdict、不可跳过门禁）
- **Legacy handoff inventory**：已编制完整的遗留交接文件清单
- **Source evidence binding**：建立了源证据绑定机制，确保每个声明都有可追溯的证据支持

---

## 二、当前仍缺少的机制

尽管核心流程已可用，但以下 8 项关键机制仍然缺失：

### 缺口 1：无正式流程状态机（PROCESS_STATE_MACHINE）

当前流程的各阶段转换依赖隐式约定和 agent 的"理解"，没有显式的、可机器验证的状态机定义。这导致：
- 无法自动检测非法状态跳转
- 无法在自动化脚本中强制执行状态约束
- 新 agent 可能误解当前流程阶段

### 缺口 2：无 GPT 捕获对账报告（GPT_CAPTURE_RECONCILIATION_REPORT）

目前没有统一的对账视图来回答：
- 所有提交的 GPT 审查请求是否都有对应的响应捕获？
- 所有捕获的响应是否都经过了验证器？
- 是否存在"提交但未捕获"或"捕获但未验证"的孤立记录？

### 缺口 3：无标准化 pre/post changed-files 证明格式

当前文件变更证明分散在不同任务和脚本中，格式不统一：
- 有的用纯文本 diff 摘要
- 有的用自定义 JSON
- 缺乏统一的 schema 来描述"哪些文件变了、怎么变的、hash 前后值是什么"

### 缺口 4：无 GPT review 回归测试用例集

`verify_gpt_reply.py` 和 `pre_gpt_review_gate.py` 没有配套的测试用例集：
- 无法验证脚本在边界条件下的行为
- 无法防止未来修改引入回归
- 无法证明验证器本身的正确性

### 缺口 5：无 HUMAN_REQUIRED_DECISION_RECORD 模板

当流程需要人工介入时（如 legacy 文件操作、部署决策），没有标准化的记录模板：
- 人工决策的上下文、选项、最终选择缺乏结构化记录
- 审计链在人工介入点出现断裂

### 缺口 6：无项目治理仪表盘（PROJECT_GOVERNANCE_DASHBOARD）

缺乏可视化视图来展示：
- 各任务的流程状态
- 门禁通过率
- 待处理的人工决策
- GPT 审查的历史趋势

### 缺口 7：无独立交接流程完成标准文档

交接完成标准目前嵌入在 approval rule 中，没有独立文档：
- 难以单独引用和版本控制
- 新 agent 难以快速理解"什么条件下交接算完成"

### 缺口 8：next_task_authorization 在 R4 断裂

R4 审查循环暴露出 `next_task_authorization` 机制的断裂：
- 当前任务完成后，下一个任务的授权缺乏显式的、可验证的传递机制
- 可能导致未经授权的任务被执行，或已授权的任务被遗漏

---

## 三、缺口影响分析

从四个维度分析各缺口的影响：

### 3.1 正确性（Correctness）

| 缺口 | 影响 | 说明 |
|------|------|------|
| **缺口 1** PROCESS_STATE_MACHINE | **高** | 无状态机意味着无法自动检测非法状态跳转（如从 `draft` 直接跳到 `closed`），流程正确性完全依赖 agent 的"自觉"，这是最脆弱的保障方式 |
| **缺口 3** CHANGED_FILES_SCHEMA | **中** | 格式不统一导致变更证明可能被遗漏或误读，直接影响变更完整性判断 |
| **缺口 8** next_task_authorization | **高** | 任务授权链断裂可能导致未授权执行，这是正确性和安全性的双重风险 |

### 3.2 可审计性（Auditability）

| 缺口 | 影响 | 说明 |
|------|------|------|
| **缺口 2** GPT_CAPTURE_RECONCILIATION | **高** | 无法回答"所有审查是否都走完了全流程"这一核心审计问题 |
| **缺口 3** CHANGED_FILES_SCHEMA | **中** | 审计人员需要理解多种格式才能追溯变更，增加审计成本和错误风险 |
| **缺口 5** HUMAN_REQUIRED_DECISION_RECORD | **高** | 人工介入是审计链的关键节点，缺乏记录等于审计链断裂 |
| **缺口 7** 完成标准文档 | **低** | 标准已嵌入 approval rule，审计时可追溯，但独立性和可维护性不足 |

### 3.3 自动化可靠性（Automation Reliability）

| 缺口 | 影响 | 说明 |
|------|------|------|
| **缺口 1** PROCESS_STATE_MACHINE | **高** | 状态机是所有自动化脚本的基础前提——没有它，自动化脚本不知道当前处于什么阶段，也无法决定下一步该执行什么 |
| **缺口 4** 回归测试用例集 | **高** | 验证脚本本身没有测试保护，任何修改都可能引入未知的回归，自动化信任度低 |
| **缺口 3** CHANGED_FILES_SCHEMA | **中** | 缺乏统一 schema 导致自动化脚本需要处理多种格式，增加复杂度和出错概率 |

### 3.4 安全性（Safety）

| 缺口 | 影响 | 说明 |
|------|------|------|
| **缺口 1** PROCESS_STATE_MACHINE | **高** | 非法状态跳转可能被利用来绕过安全门禁（如跳过 GPT 审查直接关闭） |
| **缺口 8** next_task_authorization | **高** | 授权链断裂意味着可能执行未经审查的任务，直接违反治理原则 |
| **缺口 5** HUMAN_REQUIRED_DECISION_RECORD | **中** | 人工决策缺乏记录可能导致安全敏感操作（如 legacy 文件删除）的决策过程不可追溯 |

### 影响汇总矩阵

| 缺口 | 正确性 | 可审计性 | 自动化可靠性 | 安全性 | 综合 |
|------|--------|----------|-------------|--------|------|
| 1. PROCESS_STATE_MACHINE | 高 | 中 | 高 | 高 | **关键** |
| 2. GPT_CAPTURE_RECONCILIATION | 低 | 高 | 中 | 低 | **重要** |
| 3. CHANGED_FILES_SCHEMA | 中 | 中 | 中 | 低 | **重要** |
| 4. 回归测试用例集 | 低 | 中 | 高 | 中 | **重要** |
| 5. HUMAN_REQUIRED_DECISION_RECORD | 低 | 高 | 低 | 中 | **补充** |
| 6. 治理仪表盘 | 低 | 中 | 低 | 低 | **增强** |
| 7. 完成标准文档 | 低 | 低 | 低 | 低 | **补充** |
| 8. next_task_authorization | 高 | 中 | 中 | 高 | **关键** |

---

## 四、优先级排序

### P0 — 高优先级（必须在本批次解决）

这三项是所有后续自动化和硬化工作的基础前提：

#### P0-1: PROCESS_STATE_MACHINE.md/json

- **理由**：所有自动化脚本和正确性验证的基础。没有状态机，后续的每个硬化项都缺乏流程阶段感知能力。
- **依赖**：无前置依赖，可立即开始。
- **产出**：`PROCESS_STATE_MACHINE.md`（人类可读）+ `PROCESS_STATE_MACHINE.json`（机器可读）

#### P0-2: pre/post changed-files 证明标准化（CHANGED_FILES_SCHEMA）

- **理由**：统一 JSON schema 是所有变更证明的基础。证据包、审查报告、审计对账都依赖标准化的变更描述。
- **依赖**：无前置依赖，可与 P0-1 并行。
- **产出**：`CHANGED_FILES_SCHEMA.json` + 生成/解析工具函数

#### P0-3: gpt_new_chat_attachment_submit.py 参数化

- **理由**：当前脚本硬编码了部分参数，无法被不同任务复用。参数化是实现"任何任务都能一键提交 GPT 审查"的前提。
- **依赖**：建议在 P0-2 完成后实施（以便输出格式对齐 schema），但可提前开始。
- **产出**：参数化后的 `gpt_new_chat_attachment_submit.py` + 使用说明

### P1 — 中优先级（核心功能补全）

#### P1-1: GPT_CAPTURE_RECONCILIATION_REPORT

- **理由**：端到端审计对账是治理合规的核心要求。在 P0 项完成后，对账报告可以基于标准化的数据源构建。
- **依赖**：P0-1（状态机提供流程阶段信息）、P0-2（schema 提供变更描述标准）。
- **产出**：`GPT_CAPTURE_RECONCILIATION_REPORT.md` + 生成脚本

#### P1-2: GPT review 回归测试用例集

- **理由**：保护已有脚本不被未来修改破坏。这是自动化信任度的关键保障。
- **依赖**：可独立开始，但建议在 P0-3 完成后补充参数化相关的测试用例。
- **产出**：`tests/test_verify_gpt_reply.py` + `tests/test_pre_gpt_review_gate.py` + fixture 数据

### P2 — 可后置（完善性增强）

#### P2-1: HUMAN_REQUIRED_DECISION_RECORD_TEMPLATE

- **理由**：审计完整性需要，但当前人工介入场景较少，可后置到实际遇到人工决策时再标准化。
- **依赖**：无强依赖。
- **产出**：`HUMAN_REQUIRED_DECISION_RECORD_TEMPLATE.md`

#### P2-2: PROJECT_GOVERNANCE_DASHBOARD

- **理由**：可视化增强，提升治理透明度，但不影响流程正确性和安全性。
- **依赖**：建议在 P0 + P1 全部完成后实施，以便仪表盘能展示完整的治理数据。
- **产出**：`PROJECT_GOVERNANCE_DASHBOARD.md` + 可选的 HTML 可视化

#### P2-3: HANDOFF_WORKFLOW_COMPLETION_CRITERIA

- **理由**：已在 approval rule 中部分覆盖，独立文档化是规范化补充。
- **依赖**：P0-1（状态机定义完成后可精确描述完成条件）。
- **产出**：`HANDOFF_WORKFLOW_COMPLETION_CRITERIA.md`

---

## 五、各硬化项详细方案

### 5.1 PROCESS_STATE_MACHINE

#### 状态定义

```
draft ──→ gate_passing ──→ gpt_reviewing ──→ accepted
                                          ├──→ accepted_with_limitation
                                          ├──→ blocked
                                          └──→ human_required
                                                      │
accepted ──→ closed                                  │
accepted_with_limitation ──→ closed                  │
blocked ──→ draft (修正后重新提交)                    │
human_required ──→ gate_passing (人工决策后继续) ─────┘
```

#### 状态说明

| 状态 | 含义 | 进入条件 | 退出条件 |
|------|------|----------|----------|
| `draft` | 任务初始化，evidence pack 尚未完成 | 任务创建 | evidence pack 通过 linter |
| `gate_passing` | 正在通过 pre-GPT 门禁检查 | evidence pack linter PASS | pre_gpt_review_gate 全部 PASS |
| `gpt_reviewing` | 已提交 GPT 审查，等待响应 | 门禁通过 + GPT 提交确认 | GPT 响应被 verify_gpt_reply.py 验证 |
| `accepted` | GPT 审查无条件通过 | verdict = `accepted` | 可进入 `closed` |
| `accepted_with_limitation` | GPT 审查有条件通过 | verdict = `accepted_with_limitation` | limitation 被处理后可进入 `closed` |
| `blocked` | GPT 审查拒绝 | verdict = `blocked` | 修正后回到 `draft` |
| `human_required` | 需要人工介入 | verdict = `human_required` 或安全规则触发 | 人工决策记录后回到 `gate_passing` |
| `closed` | 任务交接完成 | 所有条件满足 | **终态，不可退出** |

#### 不可逆约束

- `closed` 是终态，不可回退到任何状态
- `accepted` / `accepted_with_limitation` 不可回退到 `gpt_reviewing`
- `blocked` 只能回到 `draft`，不可跳到 `gate_passing` 或更远

#### 安全门禁

- 任何状态转换都必须有对应的 evidence 记录
- `gpt_reviewing → accepted*` 必须经过 `verify_gpt_reply.py` 验证
- `human_required` 状态下的任何操作都必须有 `HUMAN_REQUIRED_DECISION_RECORD`

#### 产出格式

建议同时生成两种格式：

- **`PROCESS_STATE_MACHINE.md`**：人类可读，包含状态图（Mermaid）、转换表、约束说明
- **`PROCESS_STATE_MACHINE.json`**：机器可读，可被自动化脚本加载用于状态校验

JSON schema 示例：

```json
{
  "states": ["draft", "gate_passing", "gpt_reviewing", "accepted", "accepted_with_limitation", "blocked", "human_required", "closed"],
  "initial": "draft",
  "final": ["closed"],
  "transitions": [
    {
      "from": "draft",
      "to": "gate_passing",
      "guard": "evidence_pack_linter_pass AND evidence_pack_complete",
      "evidence_required": true
    }
  ],
  "invariants": [
    "closed 状态不可退出",
    "gpt_reviewing 到 accepted* 必须经过 verify_gpt_reply.py"
  ]
}
```

---

### 5.2 CHANGED_FILES_SCHEMA

#### 目标

定义统一的 JSON schema，用于描述任何任务执行前后的文件系统变更。

#### Schema 定义

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "ChangedFilesEvidence",
  "description": "pre/post 文件变更证明的标准格式",
  "type": "object",
  "required": ["task_id", "snapshot_before", "snapshot_after", "changes"],
  "properties": {
    "task_id": {
      "type": "string",
      "description": "关联的任务 ID"
    },
    "snapshot_before": {
      "type": "string",
      "format": "date-time",
      "description": "变更前快照时间戳 (ISO 8601)"
    },
    "snapshot_after": {
      "type": "string",
      "format": "date-time",
      "description": "变更后快照时间戳 (ISO 8601)"
    },
    "changes": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["path", "change_type"],
        "properties": {
          "path": {
            "type": "string",
            "description": "文件路径（相对于项目根目录）"
          },
          "change_type": {
            "type": "string",
            "enum": ["added", "modified", "deleted", "renamed", "permission_changed"],
            "description": "变更类型"
          },
          "sha256_before": {
            "type": ["string", "null"],
            "pattern": "^[a-f0-9]{64}$",
            "description": "变更前文件 SHA-256 hash（added 类型为 null）"
          },
          "sha256_after": {
            "type": ["string", "null"],
            "pattern": "^[a-f0-9]{64}$",
            "description": "变更后文件 SHA-256 hash（deleted 类型为 null）"
          },
          "tracked": {
            "type": "boolean",
            "description": "文件是否在版本控制跟踪范围内"
          },
          "rename_from": {
            "type": ["string", "null"],
            "description": "renamed 类型时的原路径"
          },
          "permission_before": {
            "type": ["string", "null"],
            "description": "permission_changed 类型时的原权限（如 0644）"
          },
          "permission_after": {
            "type": ["string", "null"],
            "description": "permission_changed 类型时的新权限"
          },
          "evidence_ref": {
            "type": ["string", "null"],
            "description": "关联的证据引用（如 diff 文件路径或 evidence pack 中的 section ID）"
          }
        }
      }
    },
    "summary": {
      "type": "object",
      "properties": {
        "total_added": { "type": "integer" },
        "total_modified": { "type": "integer" },
        "total_deleted": { "type": "integer" },
        "total_renamed": { "type": "integer" },
        "total_permission_changed": { "type": "integer" }
      }
    }
  }
}
```

#### 生成方式

建议提供 Python 工具函数：

```python
def generate_changed_files_evidence(
    task_id: str,
    before_snapshot: dict[str, str],  # path -> sha256
    after_snapshot: dict[str, str],   # path -> sha256
    tracked_files: set[str] | None = None,
) -> dict:
    """生成符合 CHANGED_FILES_SCHEMA 的变更证明。"""
    ...
```

---

### 5.3 GPT 提交脚本参数化

#### 当前问题

`gpt_new_chat_attachment_submit.py` 中存在硬编码：
- evidence pack 路径固定
- prompt 模板内嵌
- 输出路径硬编码
- 无法指定 task_id 和 run_id

#### 参数化方案

命令行接口设计：

```bash
python gpt_new_chat_attachment_submit.py \
    --task-id "HANDOFF-WORKFLOW-HARDENING-PLAN-A1" \
    --pack-path "./evidence_packs/handoff_workflow_hardening_plan_a1/" \
    --run-id-path "./run_id.txt" \
    --output-path "./gpt_responses/handoff_workflow_hardening_plan_a1_r1.txt" \
    --prompt-template "./templates/gpt_review_prompt.md" \
    [--dry-run] \
    [--timeout 300]
```

#### 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `--task-id` | 是 | 任务 ID，用于 prompt 注入和输出文件命名 |
| `--pack-path` | 是 | evidence pack 目录路径 |
| `--run-id-path` | 是 | run_id 文件路径（读取后注入 prompt） |
| `--output-path` | 是 | GPT 响应输出保存路径 |
| `--prompt-template` | 否 | 自定义 prompt 模板路径（默认使用内置模板） |
| `--dry-run` | 否 | 仅生成 prompt 和附件清单，不实际提交 |
| `--timeout` | 否 | 提交超时时间（秒），默认 300 |

#### 模板变量

prompt 模板中支持以下变量替换：

- `{{TASK_ID}}` — 替换为 task_id
- `{{RUN_ID}}` — 替换为从 run_id_path 读取的内容
- `{{PACK_MANIFEST}}` — 替换为 evidence pack 的 manifest 内容
- `{{TIMESTAMP}}` — 替换为提交时间戳

---

### 5.4 GPT_CAPTURE_RECONCILIATION_REPORT

#### 目标

提供端到端的审计对账视图，确保每次 GPT 审查请求都有完整的 提交 -> 捕获 -> 验证 -> verdict 链路。

#### 对账维度

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────┐
│  Submission  │ ──→ │   Capture   │ ──→ │ Verification│ ──→ │ Verdict │
│  (提交记录)  │     │  (捕获记录)  │     │  (验证记录)  │     │ (结论)  │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────┘
```

#### 对账报告结构

```json
{
  "report_id": "RECON-20260609-001",
  "generated_at": "2026-06-09T01:23:28+00:00",
  "summary": {
    "total_submissions": 5,
    "total_captures": 5,
    "total_verified": 5,
    "total_verdicts": 5,
    "orphan_submissions": 0,
    "orphan_captures": 0,
    "unverified_captures": 0
  },
  "reconciliation": [
    {
      "task_id": "HANDOFF-PIPELINE-REFACTOR-A1",
      "round": 1,
      "submitted_at": "2026-06-08T10:00:00+00:00",
      "captured_at": "2026-06-08T10:05:00+00:00",
      "verified_at": "2026-06-08T10:05:30+00:00",
      "verdict": "accepted_with_limitation",
      "status": "complete",
      "anomalies": []
    }
  ],
  "anomalies": []
}
```

#### 异常类型

| 异常类型 | 含义 | 严重性 |
|----------|------|--------|
| `orphan_submission` | 提交记录存在但无对应捕获 | 高 |
| `orphan_capture` | 捕获记录存在但无对应提交 | 高 |
| `unverified_capture` | 捕获记录存在但未经验证器验证 | 高 |
| `verdict_mismatch` | 验证器 verdict 与 GPT 原始回复不一致 | 中 |
| `stale_submission` | 提交超过指定时间仍无捕获 | 中 |

---

### 5.5 GPT Review 回归测试

#### 最小测试用例集

##### 针对 `verify_gpt_reply.py`

| 测试 ID | 测试名称 | 输入 | 预期结果 |
|---------|----------|------|----------|
| `VRT-001` | 正常 accepted 回复 | 完整的合法 GPT 回复，verdict = `accepted` | PASS, verdict = `accepted` |
| `VRT-002` | 正常 accepted_with_limitation | 完整的合法回复，附带 limitation 列表 | PASS, verdict = `accepted_with_limitation` |
| `VRT-003` | 缺少 run_id | 回复中 run_id 字段缺失 | FAIL, 错误类型 = `missing_run_id` |
| `VRT-004` | run_id 不匹配 | 回复中 run_id 与期望值不一致 | FAIL, 错误类型 = `run_id_mismatch` |
| `VRT-005` | 缺少 END_OF_GPT_RESPONSE | 回复中没有 END_OF_GPT_RESPONSE 标记 | FAIL, 错误类型 = `missing_eor_marker` |
| `VRT-006` | 空文件输入 | 0 字节文件 | FAIL, 错误类型 = `empty_input` |
| `VRT-007` | verdict 展平攻击 | 回复中 verdict 被篡改为非法值（如 `ACCEPTED` 全大写、`pass` 非标准值） | FAIL, 错误类型 = `invalid_verdict` |
| `VRT-008` | 过期回复（stale reply） | 回复中的 timestamp 早于当前任务的提交时间 | FAIL, 错误类型 = `stale_reply` |
| `VRT-009` | 截断的回复 | 回复在 verdict 之后被截断 | FAIL, 错误类型 = `truncated_response` |
| `VRT-010` | 非法 verdict 值 | verdict = `rejected`（不在合法枚举中） | FAIL, 错误类型 = `invalid_verdict` |

##### 针对 `pre_gpt_review_gate.py`

| 测试 ID | 测试名称 | 输入 | 预期结果 |
|---------|----------|------|----------|
| `PGT-001` | 完整 evidence pack | 所有必填文件齐全 | PASS |
| `PGT-002` | 缺少 manifest | manifest.json 不存在 | FAIL, 缺失项 = `manifest` |
| `PGT-003` | hash 不一致 | 某文件的 sha256 与 manifest 记录不匹配 | FAIL, 不一致文件列表 |
| `PGT-004` | 空 evidence pack | 目录存在但为空 | FAIL, 缺失全部必填文件 |
| `PGT-005` | 引用无效 | evidence pack 中引用了不存在的文件 | FAIL, 无效引用列表 |

#### 测试框架

建议使用 `pytest` + `conftest.py` 提供 fixture：

```python
# conftest.py
import pytest

@pytest.fixture
def valid_gpt_reply():
    """返回一个完整的合法 GPT 回复文本。"""
    ...

@pytest.fixture
def sample_evidence_pack(tmp_path):
    """在临时目录中创建完整的 evidence pack 结构。"""
    ...
```

---

### 5.6 HUMAN_REQUIRED_DECISION_RECORD_TEMPLATE

#### 使用场景

当流程进入 `human_required` 状态时，必须使用此模板记录人工决策。常见场景：

- Legacy 文件的删除/移动/重命名操作
- 296 PASS 验证的最终处置决策
- GPT 审查中的 `human_required` verdict 后续处理
- 安全敏感操作的授权

#### 模板结构

```markdown
# 人工决策记录

## 基本信息
- **决策 ID**: HRD-{task_id}-{sequence}
- **关联任务**: {task_id}
- **决策时间**: {ISO 8601 timestamp}
- **决策人**: {human decision maker}
- **流程状态**: human_required → (决策后目标状态)

## 决策上下文
### 触发原因
{为什么流程进入了 human_required 状态}

### 可选方案
1. **方案 A**: {描述} — 影响: {分析}
2. **方案 B**: {描述} — 影响: {分析}
3. **方案 C**: {描述} — 影响: {分析}

### 约束条件
- {列出影响决策的约束}

## 最终决策
- **选择方案**: {A/B/C/其他}
- **决策理由**: {为什么选择这个方案}
- **执行步骤**: {决策后的具体操作步骤}

## 风险评估
- **已识别风险**: {列出风险}
- **缓解措施**: {如何降低风险}
- **回退方案**: {如果决策导致问题，如何回退}

## 证据
- **支持文件**: {列出相关证据文件路径}
- **审查记录**: {GPT 审查引用（如有）}
```

---

### 5.7 Startup Read Gate — 从强引导到可检查门禁

#### 当前状态

`NEXT_AGENT_REQUIRED_READS.json` 目前是一个引导性文档，列出了 21 项必读文件清单。Agent 被"期望"在启动时阅读这些文件，但没有机制验证是否真正完成。

#### 问题

- 依赖 agent 的"自觉"行为，无法保证执行
- 新 agent 可能跳过部分或全部必读文件
- 无法审计"agent 是否在充分理解上下文后才开始工作"

#### 建议方案：可机器验证的启动门禁

##### 5.7.1 启动证明文件（Startup Proof）

Agent 在启动后、开始任何实质性工作前，必须生成一个启动证明文件：

```json
{
  "agent_id": "claude-code-20260609",
  "task_id": "HANDOFF-WORKFLOW-HARDENING-PLAN-A1",
  "startup_timestamp": "2026-06-09T01:00:00+00:00",
  "reads_completed": [
    {
      "file": "D:/agent-acceptance/rules/core.md",
      "read_at": "2026-06-09T01:00:05+00:00",
      "summary_hash": "sha256:abc123..."
    }
  ],
  "total_required": 21,
  "total_completed": 21,
  "gate_status": "pass"
}
```

##### 5.7.2 门禁检查脚本

`startup_read_gate.py`：

```bash
python startup_read_gate.py \
    --task-id "HANDOFF-WORKFLOW-HARDENING-PLAN-A1" \
    --proof-path "./startup_proofs/handoff_workflow_hardening_plan_a1.json" \
    --required-reads "./NEXT_AGENT_REQUIRED_READS.json"
```

检查项：
1. 启动证明文件是否存在
2. 所有 21 项必读文件是否都在 reads_completed 中
3. 每个文件的 summary_hash 是否与实际文件内容匹配（证明 agent 确实读取了最新版本）
4. startup_timestamp 是否在当前任务创建时间之后
5. gate_status 是否为 `pass`

##### 5.7.3 集成点

- **PROCESS_STATE_MACHINE** 中，`draft → gate_passing` 转换的 guard 条件之一：`startup_read_gate PASS`
- **pre_gpt_review_gate.py** 增加检查项：验证启动证明存在且完整

---

## 六、安全操作分类

### 6.1 安全本地改动（可自动执行）

以下操作不涉及外部状态变更或高风险文件操作，agent 可以自动执行而无需人工授权：

| 操作类别 | 具体操作 | 理由 |
|----------|----------|------|
| **文件读取** | 读取项目中任何文件 | 只读操作，无副作用 |
| **报告生成** | 生成报告文件到 `_reports/` 目录 | 新增文件，不影响已有内容 |
| **证据包操作** | 新增 evidence pack 到 `evidence_packs/` | 新增文件，不影响已有内容 |
| **本地验证** | 运行 verifier、linter、测试脚本 | 只读验证，不修改项目文件 |
| **打包操作** | 生成 manifest、计算 hash、打包 ZIP | 生成辅助文件 |
| **GPT 审查提交** | 提交 GPT 审查请求并捕获响应 | 外部读取操作（不修改外部系统） |
| **报告修正** | 修正非 legacy、非高风险的报告内容 | 限于 `_reports/` 下的新增文件 |

### 6.2 必须 human_required 的操作

以下操作具有不可逆性或高安全风险，必须由人工确认后才能执行：

| 操作类别 | 具体操作 | 理由 |
|----------|----------|------|
| **Legacy 文件操作** | 删除、移动、重命名、覆盖 legacy 文件 | 不可逆，可能破坏历史审计链 |
| **Git 破坏性操作** | `git reset`、`git clean`、`git checkout`（覆盖）、`git restore` legacy 文件 | 不可逆，可能丢失历史数据 |
| **版本控制提交** | `git commit`、`git push` | 产生不可逆的版本控制记录 |
| **部署操作** | 任何形式的部署（staging/production） | 影响外部系统状态 |
| **外部系统变更** | 修改外部系统状态（API 调用、配置变更等） | 影响超出项目范围 |
| **证据伪造** | 伪造或补造测试输出、baseline、GPT verdict | 严重违反治理原则，破坏审计完整性 |

### 6.3 灰色地带处理原则

对于不明确属于上述两类的操作，遵循以下原则：

1. **默认保守**：不确定时，视为 `human_required`
2. **可逆性测试**：如果操作完全可逆且不影响 legacy 文件，可归为安全操作
3. **范围限制**：如果操作仅限于 `_reports/` 或 `evidence_packs/` 目录下的新增文件，通常为安全操作
4. **显式记录**：灰色地带决策必须记录在 evidence pack 中，说明分类理由

---

## 七、后续任务路线

### 第一批：可自动进入 GPT 审查循环

这批任务属于 P0 优先级，且产出物不涉及 legacy 文件操作，agent 可以自动执行并提交 GPT 审查。

#### 任务 1: PROCESS_STATE_MACHINE 定义 + CHANGED_FILES_SCHEMA 标准化

- **输入**：本文档第五章 5.1 和 5.2 的详细方案
- **产出**：
  - `PROCESS_STATE_MACHINE.md` — 人类可读状态机文档（含 Mermaid 状态图）
  - `PROCESS_STATE_MACHINE.json` — 机器可读状态机定义
  - `CHANGED_FILES_SCHEMA.json` — JSON schema 定义文件
  - `changed_files_utils.py` — 生成/验证工具函数
- **验收标准**：JSON schema 通过 `jsonschema` 库验证；状态机定义覆盖所有已识别的状态转换
- **预计 GPT 审查轮次**：1 轮

#### 任务 2: GPT 提交脚本参数化

- **输入**：本文档第五章 5.3 的参数化方案
- **产出**：
  - 参数化后的 `gpt_new_chat_attachment_submit.py`
  - `gpt_submit_usage.md` — 使用说明文档
- **验收标准**：支持所有定义的命令行参数；`--dry-run` 模式可正确生成 prompt 和附件清单
- **预计 GPT 审查轮次**：1 轮

### 第二批：需 GPT 审查后授权

这批任务依赖第一批的产出物，且涉及更复杂的集成逻辑，建议在第一批通过 GPT 审查后再启动。

#### 任务 3: GPT_CAPTURE_RECONCILIATION_REPORT 实现

- **输入**：本文档第五章 5.4 的对账报告方案 + 第一批产出的 schema
- **产出**：
  - `generate_reconciliation_report.py` — 对账报告生成脚本
  - 首份对账报告（覆盖所有已有的 GPT 审查记录）
- **验收标准**：报告覆盖所有已知提交记录；无遗漏的 orphan 记录（或 orphan 被显式标记和解释）
- **依赖**：PROCESS_STATE_MACHINE.json（提供流程阶段信息）、CHANGED_FILES_SCHEMA（标准化变更描述）

#### 任务 4: GPT review 回归测试用例

- **输入**：本文档第五章 5.5 的测试用例设计
- **产出**：
  - `tests/conftest.py` — 测试 fixture
  - `tests/test_verify_gpt_reply.py` — 验证器测试（10+ 用例）
  - `tests/test_pre_gpt_review_gate.py` — 门禁测试（5+ 用例）
  - `tests/fixtures/` — 测试数据目录
- **验收标准**：所有定义的测试用例全部 PASS；覆盖所有边界条件
- **依赖**：建议在任务 2（脚本参数化）完成后补充参数化相关测试

### 需用户确认的任务

以下任务涉及 legacy 文件操作或高层治理决策，必须由用户确认后才能执行：

#### 任务 5: HANDOFF_REPLY_V4.txt 最终处置

- **问题**：`HANDOFF_REPLY_V4.txt` 当前状态为 `tracked_deleted_human_required`（git tracked 但文件已删除，需要人工决策恢复或处置），不是普通的待处置 legacy 文件
- **当前状态**：文件在 git 历史中存在但工作树中已删除，git status 显示为 `D`（deleted）。不得自动执行 `git restore` / `git checkout` 恢复此文件
- **需确认**：是否恢复原文件？是否归档？是否用新格式替代？任何处置方案都必须经过人工确认

#### 任务 6: 296 PASS 验证决策

- **问题**：296 项 PASS 验证结果的最终处置——是否需要逐一复核？是否接受批量确认？
- **需确认**：复核策略（全量/抽样/仅异常项）、确认阈值

#### 任务 7: whole-project/global 状态退出条件定义

- **问题**：项目整体何时可以宣布"交接流程硬化完成"？
- **需确认**：全局完成条件的定义、谁来判定、是否需要外部审查

---

## 八、本轮必须回答的 11 个问题

### Q1: 当前交接流程的完成度是多少？

**答**：核心流程框架已完成（约 70%），具体包括：四层权威体系、附件版 GPT 审查 SOP、fail-closed 验证器、evidence pack 工具链、next-agent 启动读门槛、source evidence binding。已成功执行至少两轮 GPT 审查并捕获 verdict。但仍缺少状态机、对账报告、标准化 schema、回归测试等硬化机制（约 30%）。详见本文档第一章和第二章。

### Q2: 哪些缺口如果不修复会导致流程失败？

**答**：三个关键缺口：
1. **PROCESS_STATE_MACHINE（缺口 1）**：没有状态机，自动化脚本无法感知流程阶段，非法状态跳转无法被检测，是所有后续自动化的基础前提。
2. **next_task_authorization 断裂（缺口 8）**：任务授权链断裂可能导致未授权执行或已授权任务遗漏。
3. **回归测试用例集（缺口 4）**：验证脚本无测试保护，任何修改都可能引入回归，自动化信任度无法建立。

### Q3: 硬化项之间的依赖关系是什么？

**答**：

```
PROCESS_STATE_MACHINE (P0-1) ──────┐
                                   ├──→ GPT_CAPTURE_RECONCILIATION (P1-1)
CHANGED_FILES_SCHEMA (P0-2) ───────┘
                                   ├──→ 回归测试 (P1-2) [补充参数化测试]
gpt_submit 参数化 (P0-3) ──────────┘

HUMAN_REQUIRED_DECISION_RECORD (P2-1) — 独立
PROJECT_GOVERNANCE_DASHBOARD (P2-2) — 依赖 P0 + P1 全部完成
HANDOFF_WORKFLOW_COMPLETION_CRITERIA (P2-3) — 依赖 PROCESS_STATE_MACHINE
```

### Q4: 哪些硬化项可以并行实施？

**答**：
- **P0-1 (PROCESS_STATE_MACHINE)** 和 **P0-2 (CHANGED_FILES_SCHEMA)** 可以完全并行，无相互依赖。
- **P0-3 (脚本参数化)** 可以与 P0-1 并行启动，但建议在 P0-2 完成后对齐输出格式。
- **P2-1 (HUMAN_REQUIRED_DECISION_RECORD)** 独立于其他所有项，可以随时实施。

### Q5: 每个硬化项的预估工作量是多少？

**答**：

| 硬化项 | 预估文件数 | 预估代码行 | 复杂度 |
|--------|-----------|-----------|--------|
| P0-1 PROCESS_STATE_MACHINE | 2 (.md + .json) | ~200 | 中 |
| P0-2 CHANGED_FILES_SCHEMA | 2 (.json + .py) | ~300 | 中 |
| P0-3 脚本参数化 | 1-2 (.py + .md) | ~200 | 低-中 |
| P1-1 对账报告 | 2 (.py + .md) | ~400 | 中-高 |
| P1-2 回归测试 | 3+ (conftest + 2 test files + fixtures) | ~500 | 中 |
| P2-1 决策记录模板 | 1 (.md) | ~80 | 低 |
| P2-2 仪表盘 | 1-2 (.md + .html) | ~300 | 中 |
| P2-3 完成标准 | 1 (.md) | ~100 | 低 |

### Q6: 安全操作分类是否完整？

**答**：本文档第六章覆盖了三大类操作（安全可自动执行、必须 human_required、灰色地带）。分类基于两个核心原则：(1) 可逆性——不可逆操作必须 human_required；(2) legacy 文件保护——涉及 legacy 文件的任何修改操作必须 human_required。该分类已覆盖了当前已识别的所有操作场景，但建议在实际执行中遇到新的操作类型时及时补充。

### Q7: next_task_authorization 断裂如何修复？

**答**：建议在 PROCESS_STATE_MACHINE 中增加 `authorization_transfer` 机制：
1. 当前任务进入 `closed` 状态时，必须显式生成 `next_task_authorization` 记录
2. 该记录包含：下一个任务 ID、授权来源（哪个任务的 verdict 授权了下一个任务）、授权时间戳
3. 下一个任务在进入 `draft` 状态时，必须验证 `next_task_authorization` 记录存在且有效
4. 无有效授权的任务不允许进入 `gate_passing` 状态

### Q8: Startup Read Gate 如何从引导升级为强制？

**答**：详见本文档 5.7 节。核心方案：
1. 定义启动证明 JSON 格式，要求 agent 记录每个必读文件的读取时间和内容 hash
2. 实现 `startup_read_gate.py` 脚本，自动验证启动证明的完整性和准确性
3. 在 PROCESS_STATE_MACHINE 中将 `startup_read_gate PASS` 设为 `draft → gate_passing` 的必要条件
4. 在 `pre_gpt_review_gate.py` 中增加启动证明检查项

### Q9: GPT 审查循环的退出条件是什么？

**答**：
- **单任务退出条件**：GPT verdict 为 `accepted` 或 `accepted_with_limitation`（limitation 已处理），且 `verify_gpt_reply.py` 验证 PASS
- **循环上限**：同一任务最多 3 轮 GPT 审查。3 轮后仍为 `blocked` 的任务自动进入 `human_required` 状态
- **全局退出条件**：需用户确认（见任务 7），建议至少包括：所有 P0 项通过 GPT 审查 + 所有 P1 项通过 GPT 审查 + 对账报告无 orphan 记录

### Q10: 如何确保硬化计划本身的可审计性？

**答**：
1. 本文档作为计划任务的产出物，本身需要提交 GPT 审查
2. 所有后续硬化任务的 evidence pack 必须引用本文档的 task_id
3. 对账报告（P1-1 实现后）必须覆盖本批次所有任务
4. 每个硬化项的验收标准在本文档中已明确定义，可机器检查

### Q11: 本批次硬化完成后的最终状态是什么？

**答**：完成全部 P0 + P1 项后，交接流程将达到以下状态：

- **流程状态机**：显式定义，可机器验证，所有自动化脚本可感知流程阶段
- **变更证明**：统一 JSON schema，所有任务使用相同格式描述文件变更
- **GPT 提交**：完全参数化，任何任务可一键提交审查
- **审计对账**：端到端对账报告，无 orphan 提交/捕获/验证记录
- **回归保护**：验证脚本有完整测试覆盖，修改安全可验证
- **任务授权**：next_task_authorization 机制完整，无授权链断裂
- **启动门禁**：可机器验证的启动读门槛，agent 启动行为可审计

P2 项可在后续批次中逐步完成，不影响流程的正确性和安全性。

---

## 附录 C：R1 审查经验教训 — Capture 误取问题

### 问题描述

在 R1 提交过程中，Playwright 脚本的 `msgs.last.inner_text()` 在延续性对话中捕获了错误的 assistant 消息：取到了 assistant[3]（一个 Qwen 提示词模板），而不是 assistant[4]（本次提交的真正 verdict）。

### 根因分析

1. **提交确认正常**：user_count 增加了，user bubble 出现了
2. **GPT 回复正常**：verdict 作为新的 assistant 消息出现
3. **Capture 逻辑有缺陷**：`msgs.last` 在 GPT 回复仍在生成时可能指向旧消息
4. **run_id 匹配失败**：脚本记录了 `run_id_match: false` 但仍继续了稳定性等待

### 修复建议

1. **提交前记录 `before_assistant_count`**：capture 循环只检查 `index >= before_assistant_count` 的消息
2. **强制 run_id 匹配**：将 run_id 匹配作为硬门槛，不匹配则继续等待而非接受
3. **添加 capture reconciliation**：提交后对比 `before/after` assistant 消息计数，确认新消息确实出现
4. **固化到 runbook**：将 `before_assistant_count` 记录机制加入 `ATTACHMENT_BACKED_GPT_REVIEW_RUNBOOK.md`

### 与 GAP-004 的关系

此问题属于 GAP-004（GPT_CAPTURE_RECONCILIATION_REPORT）的实际案例。当前 capture 机制缺乏端到端的对账验证，导致误取无法被自动检测。

---

## 附录 A：术语表

| 术语 | 定义 |
|------|------|
| **Evidence Pack** | 结构化的证据包，包含任务执行过程中产生的所有证据文件 |
| **GPT Review** | 将 evidence pack 提交至 GPT 进行结构化审查的过程 |
| **Verdict** | GPT 审查的结论，合法值：`accepted`、`accepted_with_limitation`、`blocked`、`human_required` |
| **Fail-closed** | 验证失败时默认拒绝的安全原则 |
| **Legacy 文件** | 项目历史遗留文件，受特殊保护规则约束 |
| **Gate** | 流程中的自动化检查点，必须全部 PASS 才能进入下一阶段 |
| **Orphan 记录** | 对账中发现的孤立记录（有提交无捕获、有捕获无验证等） |
| **Source Evidence Binding** | 源证据绑定机制，确保每个声明都有可追溯的证据 |

## 附录 B：相关文件索引

| 文件 | 路径 | 说明 |
|------|------|------|
| 权威源定义 | `HANDOFF_SOURCE_OF_TRUTH.md` | 四层权威体系 |
| GPT 审查 SOP | `ATTACHMENT_BACKED_GPT_REVIEW_RUNBOOK.md` | 附件版审查流程 |
| GPT 提交脚本 | `gpt_new_chat_attachment_submit.py` | 自动化提交脚本 |
| GPT 回复验证器 | `verify_gpt_reply.py` | fail-closed 验证 |
| Evidence Pack Linter | `evidence_pack_linter.py` | 证据包检查 |
| Pre-GPT Review Gate | `pre_gpt_review_gate.py` | 提交前门禁 |
| Next-Agent 必读清单 | `NEXT_AGENT_REQUIRED_READS.json` | 21 项必读文件 |

---

*文档生成时间: 2026-06-09T01:23:28+00:00*
*Task ID: HANDOFF-WORKFLOW-HARDENING-PLAN-A1*
*Run ID: HANDOFF_WORKFLOW_HARDENING_PLAN_A1_20260609_012328*
