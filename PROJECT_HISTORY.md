# PROJECT_HISTORY.md — DevFrame Agent Acceptance + Control Plane
> 项目生存文档。每阶段完成后追加，永不删除。Agent 和 GPT 共享此文件理解项目全貌。
> Last updated: 2026-06-07T17:40:00+08:00
> Current stage: CONTEXT-COMPRESSION-A1 accepted (R6); pending binding/commit blocked by pre-commit gate ai_guard.py scope scan.
> 文档版本: v1

---

# DevFrame 项目交接文档 — HANDOFF V5

> 生成时间: 2026-06-06
> 目标: 维护项目完整上下文，新 agent 通过本文档 + CLAUDE.md 即可接手
> 对话上下文: 主对话 6a22dc07 (82 msgs) → handoff 至 6a23dd8c (13 msgs)
> 字符数: ~25,000

---

## 1. 项目身份（项目定位）

**DevFrame Control Plane** 是一个三层工作流治理体系：

| 层 | 仓库 | 职责 |
|------|------|------|
| 规范验收层 | agent-acceptance | 定义合约、验收规则、evidence pack schema、validator、memory |
| 编排控制层 | devframe-control-plane | pipeline 编排、runner、state machine、submission adapter、CLI、stage executor |
| 执行层 | dev-frame-opencode | 具体执行 agent 操作（本 session 基本未改动） |

核心价值主张：**把多阶段 Agent/GPT 工作流变成可冷启动、可迁移、可审核、可交接的 evidence-first 框架。**

---

## 2. 已完成任务及 GPT 审查状态

| 任务ID | 仓库 | 描述 | GPT审查 | 最终状态 | REVIEW_RUN_ID |
|--------|------|------|---------|---------|---------------|
| PAPER-A1 | agent-acceptance | 论文 acceptance contracts 设计 (7 合约) | accepted (3轮) | closed | paper-a1-contract-design-v1 |
| ARCH-GAP-A1 | agent-acceptance | 框架使用强制规范 + bypass 检测 | accepted (追审) | closed | arch-gap-a1-framework-enforcement-v1 |
| REF-PAPER-1 | devframe-control-plane | Reference paper review pipeline 设计 | accepted (追审) | closed | ref-paper-1-pipeline-v1 |
| REF-PAPER-2A | devframe-control-plane | Pipeline stage 执行实现 | superseded by 2B | superseded | ref-paper-2a-execution-v1 |
| REF-PAPER-2B | devframe-control-plane | 完整 7-stage pipeline + GPT 审查 | accepted (3轮) | closed | ref-paper-2b-closure-review-v1 |
| Push Blocker Resolution | agent-acceptance | 证据分类机制 (RUN_CLASSIFICATION) | accepted (3轮) | closed | push-blocker-resolution-v1 |
| MEMORY-A1 | agent-acceptance | Memory Layer 设计 (4 合约, 3 模板) | accepted (2轮) | closed | memory-a1-workflow-memory-design-v1 |
| WORKFLOW-HARDENING-A1 | agent-acceptance | SD-01/02/03 修复 (validator + contracts) | accepted (9轮) | closed | workflow-hardening-a1-v1 |
| WORKFLOW-HARDENING-A2 | agent-acceptance | validator 接入 pre-push gate (step 2.5) | accepted (batch R2) | closed | batch-closure-r2-review-v1 |
| CONTROL-PLANE-A1 | devframe-control-plane | validator 接入 devframe pack validate + pipeline | accepted (多轮) | closed | control-plane-a1-v1 |
| HANDOFF-A1 | agent-acceptance | 自动化对话交接 + GPT 回复完整性 guard | deployed | closed | — |
| MEMORY-A2 | agent-acceptance | Memory Compiler 原型 (14→15 lessons) | accepted (batch R2) | closed | batch-closure-r2-review-v1 |
| PAPER-MEMORY-C1 | agent-acceptance | 论文记忆隐私规则 | accepted (batch R1) | closed | batch-closure-review-3tasks-v1 |
| MEMORY-A3 | agent-acceptance | Memory Lint | deployed (needs_review→pass) | lint-only | — |
| PAPER-A2 | agent-acceptance | 论文 IO 协议 + 脱敏证据包 + 隐私阻断 | accepted (R2) | closed | paper-a2-io-redaction-protocol-v1 |
| REPO-ROUTING-A1 | agent-acceptance | Submission target schema + repo routing contract | accepted (v4) | closed | repo-routing-a1-v4-20260605 |
| PROJECT-HISTORY-BP | 两个仓库 | PROJECT_HISTORY.md as lived blueprint | accepted (v6) | closed | project-history-blueprint-v6-20260605 |
| PROJECT-HISTORY-GAPS | agent-acceptance | GPT review gate + auto-append + conversation registry | accepted (v4) | closed | project-history-gaps-closure-v4-20260605 |
| PAPER-B1 | devframe-control-plane | PAPER-A3 validator 接入 reference paper pipeline | accepted | closed | paper-b1-validator-pipeline-integration-v1 |
| PAPER-B2 | devframe-control-plane | synthetic-only validator-backed paper workflow v2 | accepted (R2) | closed | paper-b2-synthetic-workflow-v2-review-r2 |
| PAPER-C1 | agent-acceptance | 真实论文安全协议，protocol-only | accepted | closed | paper-c1-real-paper-pilot-safety-protocol-review-v1 |
| PAPER-A3 | agent-acceptance | 论文任务 validator 正式接入 | accepted (R2) | closed | paper-a3-r2-web-review |
| REVIEW-TEMPLATE-V2 | agent-acceptance | END_OF_GPT_RESPONSE + next_task_authorization + required_fixes | **未提交GPT** | **open** | — |

---

## 3. 当前所有仓库 commit 状态

| 仓库 | 最新 commit | 分支 | 推送状态 |
|------|-----------|------|---------|
| agent-acceptance | `bc841e9d` | master | pushed |
| devframe-control-plane | `11f9b30` | main | pushed |

---

## 4. 待处理问题

### 4.1 未提交 GPT 审查的任务

- **REVIEW-TEMPLATE-V2** (commit `bc841e9d`): 模板 + schema + validator 修改已 push 但从未构建 evidence pack 并提交 GPT。必须补审。

### 4.2 结构性缺陷：GPT 审查被系统跳过

这是贯穿整个 session 的核心问题。agent 反复将 `tests pass + commit + push` 当作任务终点，而跳过 GPT 审查。原因：GPT 审查在流程中是"软约束"（无 gate 强制执行），而 commit/push 是"硬约束"（pre-commit/pre-push gate 强制）。

GPT 诊断（见 `docs/GPT_STRUCTURAL_FIX.txt`）：
- 状态机缺失：没有 `gpt_accepted` 状态和 `push_allowed` 门禁
- pre-push gate 不检查 GPT accepted
- agent 可以在 `ready_for_review` 状态下就 commit/push

### 4.3 已知系统性缺陷 (SD)

| 缺陷 | 状态 | 修复状况 |
|------|------|---------|
| SD-01: summary-only evidence pack | fixed | validator 检测 + pre-push gate 阻断 |
| SD-02: ready_for_review 被当作 closed | fixed | WORKFLOW_STATE_CONTRACT + validator |
| SD-03: self-referential failure | fixed | GOVERNANCE_TASK_REVIEW_CONTRACT + 追审 |
| SD-04: GPT 审查被跳过 | resolved | PROJECT-HISTORY-GAPS v4 accepted (GPT review gate hardened, 3 checks) |
| SD-05: agent 在 GPT 回复未完成时执行 (新) | partially fixed | capture_gpt_reply.py + validate_gpt_reply_completeness.py 已部署 |
| SD-06: accepted 后不给出 next_task_authorization (新) | partially fixed | 模板+schema 已更新，GPT 尚未确认遵从 |

---

## 5. 安全边界（完整清单）

### 5.1 绝对禁止

| 规则 | 说明 |
|------|------|
| 不得删除、移动、重命名 evidence | H4 Archive Governance |
| 不得清理 runs | 历史 evidence 不可触碰 |
| 不得伪造 GPT accepted | 必须基于真实 GPT 审查 |
| 不得伪造 FLOW_OUTCOME | 必须由框架生成 |
| 不得伪造 WORKFLOW_CLOSURE_VALIDATION | 必须由 validator 生成 |
| 不得移除或弱化 guard | guard_removal_approved: false (permanently blocked) |
| 不得默认开启 live CDP | 需要显式 --safety-flag |
| 不得处理真实论文全文 | paper workflow 必须 synthetic_only |
| 不得处理用户私密数据 | cookie/session/browser profile/api keys |
| 不得上传到外部服务 | 除非显式授权 |
| 不得手写 Playwright 绕过 bridge | 必须通过 submission_adapter 或 playwright_bridge |
| 不得跳过 bypass checker | 每次提交前必须运行 |

### 5.2 Evidence-First 原则

1. **Agent 陈述不是证据** — GPT 必须检查实际文件
2. **closed == GPT accepted + ledger entry** — ready_for_review ≠ closed
3. **summary-only pack 必须在本地 fail** — 不得提交到 GPT
4. **manifest 必须与 ZIP 双向一致** — 所有 SHA256 可复核
5. **WORKFLOW_CLOSURE_VALIDATION 必须 fresh** — 不能是 stale 旧数据





---

---

## 6. Execution Rules

1. agent summary is not evidence; final status must be backed by files, hashes, tests, and GPT review.
2. ready_for_review is not closed.
3. closed requires GPT accepted plus ledger entry.
4. evidence pack must not be summary-only.
5. manifest / ZIP / SHA256 must be bidirectionally consistent and fresh.
6. GPT_REPLY shorter than 2000 bytes or missing END_OF_GPT_RESPONSE must not be executed.
7. More than 60 assistant messages requires handoff.
8. HANDOFF.md must be >= 8000 bytes and contain END_OF_HANDOFF.
9. accepted must include next_task_authorization.
10. blocked must include required_fixes and resubmission_requirements.

## 7. 所有已部署 Validator / Gate / Checker

| 脚本 | 位置 | 用途 |
|------|------|------|
| validate_workflow_closure.py | agent-acceptance/scripts/ | SD-01/02/03 检查 (summary-only, closed_without_gpt, governance self-close) |
| check_submission_bypass.py | agent-acceptance/scripts/ | 检测未授权 Playwright/CDP 绕过 |
| validate_gpt_reply_completeness.py | agent-acceptance/scripts/ | 检测 GPT 回复完整性 (min size, end marker, required fields) |
| check_handoff_needed.py | agent-acceptance/scripts/ | 检测是否需要对话交接 (阈值 60 msgs) |
| validate_handoff.py | agent-acceptance/scripts/ | 验证 HANDOFF.md (size, structure, END_OF_HANDOFF marker) | 

| capture_gpt_reply.py | agent-acceptance/scripts/ | 可靠 GPT 回复捕获 (等 END marker) |
| memory_compiler.py | agent-acceptance/scripts/ | 从 GPT review 和 ledger 提取 lessons |
| memory_lint.py | agent-acceptance/scripts/ | Memory entry 一致性检查 |
| pre-push.governance.ps1 | agent-acceptance/hooks/ | Pre-push gate (5 steps, step 2.5 = closure validation) |
| Test-ReviewerEvidence.ps1 | agent-acceptance/scripts/ | Evidence 分类验证 (completed/historical/negative) |
| stage_executor.py | devframe-control-plane/control_plane/ | Pipeline stage 执行 + pre_submission_check |
| pack validate (CLI) | devframe-control-plane/control_plane/cli.py | 调用 workflow closure validator |

---

## 8. 对话管理规则

| 规则 | 阈值 | 行为 |
|------|------|------|
| 强制 handoff | assistant_message_count >= 60 | 当前 GPT 生成 HANDOFF.md → 开新对话 → 交接 |
| 强制 handoff | GPT 响应时间 >= 60s | 同上 |
| 强制 handoff | 同任务审查轮次 >= 3 | 同上 |
| 强制 handoff | GPT_REPLY < 2000 bytes | 同上 (且不执行) |
| 建议 handoff | assistant_message_count >= 45 | 建议交接 |
| GPT 回复完整性 | 必须包含 END_OF_GPT_RESPONSE | 否则不执行 |
| 捕获逻辑 | 等待 END_OF_GPT_RESPONSE | 稳定后等 90s 再捕获 |

---

## 9. 对话注册表

| 对话 ID | 用途 | 消息数 | 状态 |
|----------|------|--------|------|
| 6a22dc07 | 主对话 (已超载) | 82 | closed |
| 6a23dd8c | 当前活跃 | ~25 | active |
| 6a23d48d | Handoff 确认 | ~13 | handed-off |

---

## 10. 当前任务链和下一步

### 10.1 当前对话状态

- 主对话: `https://chatgpt.com/c/6a22dc07-18a4-83a3-a922-7c9ab770db3d` (82 msgs, 已超载, 不应再使用)
- 新对话: `https://chatgpt.com/c/6a23dd8c-4550-83a8-bdee-76ca5a982edb` (13 msgs, 当前活跃)
- Handoff 对话: `https://chatgpt.com/c/6a23d48d-1b98-83a9-93be-69cab7efddd4` (已确认理解)
- 最新 Handoff 对话: `https://chatgpt.com/c/6a23dd8c-4550-83a8-bdee-76ca5a982edb` (中文bootstrap, 已确认)

### 10.2 推荐下一步任务

按优先级排序：

1. **PAPER-C2**: 真实论文流程授权 — 从 synthetic-only 扩展到 bounded real-paper implementation
2. 将 PAPER-C1 accepted 写入 PROJECT_HISTORY / ledger
3. 补充 REVIEW-TEMPLATE-V2 历史追溯（已不再阻塞主线）

已完成 (accepted): GPT-REVIEW-GATE-A1 (gate hardened, 3 checks), PAPER-A3 R2, PROJECT_HISTORY Blueprint v6, Gaps Closure v4, REPO-ROUTING-A1 v4, PAPER-B1, PAPER-B2 R2, PAPER-C1

---

## 11. 关键教训

### 11.1 不要把 ready_for_review 当 closed

至少 3 个任务 (ARCH-GAP-A1, REF-PAPER-1, REF-PAPER-2A) 曾被标注为 ready_for_review 但未提交 GPT 审查就声称 done。closed 的唯一路径是 GPT accepted + ledger entry。

### 11.2 不要提交 summary-only evidence pack

至少 4 次 (PAPER-A1, Push Blocker, REF-PAPER-2B, CONTROL-PLANE-A1) 第一次提交的证据包只有 CLOSURE_REPORT + SAFETY_ATTESTATION + PACK_MANIFEST，没有实际产物文件。每次都导致 GPT 判 review_unverified。validator 现在会检测到这个模式。

### 11.3 GPT 审查不可跳过

commit + push ≠ done。正确终点是 GPT accepted。pre-push gate 现在有 step 2.5 (closure validation)，但还没有 GPT accepted 检查——这是 GPT-REVIEW-GATE-A1 要修复的。

### 11.4 Stale VALIDATION 危害

CONTROL-PLANE-A1 经历了 4+ 轮 blocked，核心原因都是 WORKFLOW_CLOSURE_VALIDATION.yaml 和 PACK_VALIDATE_OUTPUT.txt 是 stale 旧数据。证据包构建顺序必须是：全部文件 → manifest → validator → fresh validation → 替换 stale → manifest 重建。

### 11.5 不要等 GPT 回复未完成就执行

GPT_REPLY.txt 曾只有 174 bytes 时 agent 就开始执行。capture_gpt_reply.py 现在等待 END_OF_GPT_RESPONSE 标记。validate_gpt_reply_completeness.py 检查最小字节数。

---

## 12. 新对话 Bootstrap 提示词

开启新对话时，使用以下提示词上传 HANDOFF.md：

```
请阅读附件 HANDOFF.md（约 25KB，含 END_OF_HANDOFF 标记）。用以下中文 YAML 格式回复确认理解：

用以下中文 YAML 格式回复确认理解：

审查运行ID: handoff-verify-{时间戳}
交接理解判决: 已理解 | 未理解
项目身份已理解: 是 | 否
三层架构已理解: 是 | 否
已完成阶段已理解: 是 | 否
当前状态已理解: 是 | 否
安全边界已理解: 是 | 否
下一步任务已理解: 是 | 否
可以继续执行: 是 | 否
说明: 用中文说明对项目和当前任务链的整体理解，至少 5 句话
```

验收条件：`交接理解判决: 已理解` 且 `可以继续执行: 是` → agent 直接继续执行，不得再次确认。

---

## 13. 证据包构建检查清单

每次提交 GPT 前必须确认：

| # | 检查项 | ✓ |
|---|--------|---|
| 1 | 所有实际产物文件在 ZIP 中 | |
| 2 | PACK_MANIFEST.md 列出全部文件 | |
| 3 | ZIP 与 manifest 双向一致 | |
| 4 | 每个文件 SHA256 可复核（PACK_MANIFEST.md 自身用 self_excluded） | |
| 5 | WORKFLOW_CLOSURE_VALIDATION.yaml 是 fresh pass（非 stale） | |
| 6 | PACK_VALIDATE_OUTPUT.txt 是 fresh pass（非 stale） | |
| 7 | 非 summary-only（有 actual deliverables） | |
| 8 | TEST_OUTPUT.txt 存在 | |
| 9 | BYPASS_CHECK_OUTPUT.txt 存在 | |
| 10 | SAFETY_ATTESTATION.md 存在 | |
| 11 | CLOSURE_REPORT.md 存在 | |
| 12 | GPT_REVIEW_PROMPT.md 存在 | |
| 13 | 提交 GPT 前本地运行 validator pass | |
| 14 | GPT 回复 >= 2000 bytes 且含 END_OF_GPT_RESPONSE | |

---

---

## 15. Historical Lineage Supplement: S3 / B2-B3 / Guarded Steady State

> ????: 2026-06-06T14:35:39Z
> 来源: GPT 对 4972 行旧对话历史文档的蒸馏分析
> 本节记录项目早期（dev-frame-opencode / agent-acceptance 分离之前）的关键阶段。
> 这些阶段奠定了当前 G0-H6 pipeline、三层状态语义、Evidence-First 和 GPT Review Gate 的基础。

### 早期关键阶段

| 阶段 | 状态 | 核心价值 |
|------|------|----------|
| S2 human_required 解除 | accepted | 确立了 forbidden scope、human attestation、不可凭 agent claim 解除阻塞 |
| Framework Freeze | completed | 固化 Oracle GPT Review 自动化框架，暴露 agent 只输出终端报告不自动打包的问题 |
| Reliability Fix v1 | accepted | 建立三层状态语义、flow state、decision dispatcher、ACK、URL fail-closed |
| Post-Decision Driver Fix | accepted | 修复 GPT accepted 后只写 ready_to_dispatch 但不继续调度 |
| S3 Phase 1 | accepted | 发现 @go dispatch/fallback 路径不读取 FLOW_OUTCOME.json |
| AA-1 Flow Contract | accepted | agent-acceptance 定义 FLOW_OUTCOME、TASKSPEC、DISPATCH_RESULT 合同 |
| S3 Phase 2 Oracle Gate | accepted | dev-frame-opencode 接入 contracts，schema missing fail-closed |
| AA-2 Runner Contract | accepted | 定义 RUNNER_CONTRACT、RUNNER_STATE、RUNNER_STEP_RESULT |

### 继承的核心原则

以下原则来自旧工作流，在当前 G0-H6 pipeline 中依然生效：

1. 必须区分 transport_status、business_decision、dispatch_status
2. transport success ≠ business accepted
3. ready_to_dispatch ≠ dispatched
4. Markdown report ≠ machine-readable authority
5. 自动化判断依据是 FLOW_OUTCOME.json，不是自然语言 SUCCESS

### 旧阻塞项登记（已解决，保留为经验）

| 阻塞项 | 旧阶段 | 当前状态 |
|--------|--------|----------|
| forbidden scope 文件修改 | pre-S2 | 已解决 (human attestation) |
| agent 只输出报告不自动提交 | Framework Freeze | 已解决 (CDP + Playwright) |
| schema missing fail-open | S3 Phase 2 | 已解决 (fail-closed) |
| null 值通过 schema | S3 Phase 3 v2 | 已解决 (改为 unknown) |
| accepted + terminal=true 矛盾 | S3 Phase 3 v3 | 已解决 (v4) |
| B2 多轮 blocked | B2 Chain Replay | 历史记录 |

### 当前蓝本状态

旧文档中的 S3 Phase 3 v4 待修复 状态已过时。当前项目已完成 G0-H6 + T1-T3 pipeline。旧阶段仅保留为历史 lineage。





## PAPER-C1 Closure Binding (2026-06-06)

Status: accepted and closed after GPT review.

This entry is an append-only closure binding for PAPER-C1. Pre-existing dirty
baseline changes in `PROJECT_HISTORY.md` were recorded before this binding in
`_reports/paper-c1-closure-binding/BASELINE_STATUS_BEFORE.txt`,
`BASELINE_DIFF_BEFORE.patch`, and `BASELINE_HASHES_BEFORE.txt`.

Binding:

```yaml
task_id: PAPER-C1
primary_repo: agent-acceptance
overall_judgment: accepted
reviewer_type: gpt
review_run_id: paper-c1-real-paper-pilot-safety-protocol-review-v1
accepted_time: "2026-06-06T22:59:14.9368451+08:00"
evidence_pack: evidence_packs/paper-c1-closure/closure-pack.zip
evidence_pack_sha256: "0083fbed23fce1e56690add15364a27a6bdc6f6d5283ed882929c12f6b0df454"
gpt_review_result: evidence_packs/paper-c1-closure/GPT_REVIEW_RESULT.txt
gpt_review_result_sha256: "289449be9bed4f22f09898009598ed9544be2820a59265539570c7a1cdcf926f"
implementation_commit: "f47c8d2"
pushed_to_github: true
closure_scope: "protocol-only; no real paper execution enabled"
```


## PAPER-C2 Closure Binding (2026-06-07)

Status: accepted and closed after web GPT review.

This entry is an append-only closure binding for PAPER-C2. It binds the
synthetic-only authorization/redaction gate implementation to the reviewed
evidence pack and GPT acceptance result. The task does not authorize or enable
real-paper full-text processing.

Binding:

```yaml
task_id: PAPER-C2
primary_repo: agent-acceptance
overall_judgment: accepted
reviewer_type: gpt
review_run_id: paper-c2-authorization-redaction-gate-review-v1
accepted_time: "2026-06-07T06:37:59.5011596+08:00"
evidence_pack: evidence_packs/paper-c2-closure/closure-pack.zip
evidence_pack_sha256: "608ee85798ef6999a0363d51bf3f8da4088e3a03c5d1f0cef1a5d65086e49c66"
gpt_review_result: evidence_packs/paper-c2-closure/GPT_REVIEW_RESULT.txt
gpt_review_result_sha256: "f5fa4effadcb6b8eb5149f3d367fef7fe0eee8cc13901222d1c92156b119baea"
web_gpt_submission_result: evidence_packs/paper-c2-closure/WEB_GPT_SUBMISSION_RESULT.json
web_gpt_submission_result_sha256: "7990b6923340997b9fc3ffbceaa5908a9fe4ef513f03163496d7e8a012572eae"
implementation_commit: "e935181"
pushed_to_github: true
closure_scope: "synthetic-only authorization/redaction gate; no real-paper execution enabled"
```

## GROUP-01 Acceptance Binding (2026-06-07)

Status: accepted by web GPT as an isolated backfill group.

This entry binds GROUP-01 only. It must not be interpreted as acceptance of the
whole dirty worktree or of excluded dirty groups.

Binding:

```yaml
task_id: GROUP-01
task_name: AA-FLOW-RUNNER-CONTRACT-BACKFILL
primary_repo: agent-acceptance
overall_judgment: accepted
reviewer_type: gpt
accepted_time: "2026-06-07T08:14:48.8956773+08:00"
evidence_pack: evidence_packs/group-01-contract-backfill/closure-pack.zip
evidence_pack_sha256: "390654644cd913c461f6dc970684d461021d61b06e5ac9cd773343b6c8630465"
gpt_review_result: evidence_packs/group-01-contract-backfill/GPT_REVIEW_RESULT.txt
gpt_review_result_sha256: "d4840cfd1c3f3ed423e548378e75967bf25b2e18f390a7e7590804a7933f5a8c"
web_gpt_submission_result: evidence_packs/group-01-contract-backfill/WEB_GPT_SUBMISSION_RESULT.json
web_gpt_submission_result_sha256: "3fb22bb777e0bd73b598433d5d8b3f84b088921d76e198546ff843415c743d5a"
binding_record: _reports/group-01-contract-backfill-binding/GROUP_01_BINDING_RECORD.yaml
scope_limit: "only GROUP-01 selected files"
whole_dirty_worktree_accepted: false
implementation_commit: "fc2b217"
pushed_to_github: true
```

## GROUP-02 Acceptance Binding (2026-06-07)

Status: accepted by web GPT as PAPER-A3 residual/backfill.

This entry binds GROUP-02 only. It must not be interpreted as acceptance of the
whole dirty worktree or of excluded dirty groups.

Binding:

```yaml
task_id: GROUP-02
task_name: PAPER-A3-VALIDATOR-RESIDUAL
primary_repo: agent-acceptance
overall_judgment: accepted
reviewer_type: gpt
accepted_time: "2026-06-07T08:45:54.8518156+08:00"
evidence_pack: evidence_packs/group-02-paper-a3-validator-residual/closure-pack.zip
evidence_pack_sha256: "c8f1824f88de2ed9460b98d29a32481f4f9d920b6da62eaa4322ed7fb7006e99"
gpt_review_result: evidence_packs/group-02-paper-a3-validator-residual/GPT_REVIEW_RESULT.txt
gpt_review_result_sha256: "3de168c85747d18f1ef9d463d378e6b6467f25a34e7e2dcecb5342f7d792c7fd"
web_gpt_submission_result: evidence_packs/group-02-paper-a3-validator-residual/WEB_GPT_SUBMISSION_RESULT.json
web_gpt_submission_result_sha256: "7a9d248f9fdfbbab8028ff1f283ba0be8e727e296f452e1dd9f90f6c5175c56d"
binding_record: _reports/group-02-paper-a3-validator-residual-binding/GROUP_02_BINDING_RECORD.yaml
scope_limit: "only GROUP-02 selected files"
whole_dirty_worktree_accepted: false
implementation_commit: "6304a63"
pushed_to_github: true
```

## GROUP-03 Acceptance Binding (2026-06-07)

Status: accepted by web GPT as frozen generated memory output review.

This entry binds GROUP-03 only. It must not be interpreted as acceptance of the
whole dirty worktree or as acceptance of new memory compiler functionality.

Binding:

```yaml
task_id: GROUP-03
task_name: MEMORY-A2-COMPILER-OUTPUT
primary_repo: agent-acceptance
overall_judgment: accepted
reviewer_type: gpt
accepted_time: "2026-06-07T09:16:30+08:00"
evidence_pack: evidence_packs/group-03-memory-a2-output/closure-pack.zip
evidence_pack_sha256: "e125f992d45060ca8e6d287dcd1c4b2dc3de4d5818e1da0d60f5bddfb8c1881c"
gpt_review_result: evidence_packs/group-03-memory-a2-output/GPT_REVIEW_RESULT.txt
gpt_review_result_sha256: "2e9c0df8a1e2c239b3228201930b40d4fa7c18b1032af1f9d9dc431d6a899af1"
web_gpt_submission_result: evidence_packs/group-03-memory-a2-output/WEB_GPT_SUBMISSION_RESULT.json
web_gpt_submission_result_sha256: "45004e11efcd84dedf047ee193da84116d24b065988ab7781b3df3193b8ca86c"
binding_record: _reports/group-03-memory-a2-output-binding/GROUP_03_BINDING_RECORD.yaml
scope_limit: "only GROUP-03 selected files"
whole_dirty_worktree_accepted: false
implementation_commit: "e98676f"
pushed_to_github: true
```

## GROUP-06 Acceptance Binding (2026-06-07)

Status: accepted by web GPT as workflow closure validator hardening.

This entry binds GROUP-06 only. It must not be interpreted as acceptance of the
whole dirty worktree or of excluded dirty groups.

Binding:

```yaml
task_id: GROUP-06
task_name: VALIDATE-WORKFLOW-CLOSURE-CONTROL-PLANE-PATTERN
primary_repo: agent-acceptance
overall_judgment: accepted
reviewer_type: gpt
accepted_time: "2026-06-07T09:30:30+08:00"
evidence_pack: evidence_packs/group-06-workflow-closure-control-plane-pattern/closure-pack.zip
evidence_pack_sha256: "75351ab5c5c45b3e2ac489bdbafd4c6a3b31a1727bfdf55ae487cff02b6e760e"
gpt_review_result: evidence_packs/group-06-workflow-closure-control-plane-pattern/GPT_REVIEW_RESULT.txt
gpt_review_result_sha256: "771df59136d78a944f7bb2e0bfcef7f147be4f3b6dbf1b7b6653ba9b02ca7c89"
web_gpt_submission_result: evidence_packs/group-06-workflow-closure-control-plane-pattern/WEB_GPT_SUBMISSION_RESULT.json
web_gpt_submission_result_sha256: "37d9b31db6766d991a2615cb994d0d499169b93191a0e698ab1878c691a2ea9d"
binding_record: _reports/group-06-workflow-closure-control-plane-pattern-binding/GROUP_06_BINDING_RECORD.yaml
scope_limit: "only GROUP-06 selected files"
whole_dirty_worktree_accepted: false
implementation_commit: "10b9e8c"
pushed_to_github: true
```

## GROUP-04 Acceptance Binding (2026-06-07)

Status: accepted by web GPT as capability inventory/routing cleanup with historical audit preserved.

This entry binds GROUP-04 only. It must not be interpreted as acceptance of the
whole dirty worktree, archive hook changes, or tools governance changes.

Binding:

```yaml
task_id: GROUP-04
task_name: AGENT-RUNTIME-CAPABILITY-CLEANUP
primary_repo: agent-acceptance
overall_judgment: accepted
reviewer_type: gpt
accepted_time: "2026-06-07T12:05:40+08:00"
evidence_pack: evidence_packs/group-04-agent-runtime-capability-cleanup/closure-pack.zip
evidence_pack_sha256: "82998c458a1fb14448b7d8839bc2e9f7b0b5da24169465a01e3a9948fc64020d"
gpt_review_result: evidence_packs/group-04-agent-runtime-capability-cleanup/GPT_REVIEW_RESULT.txt
gpt_review_result_sha256: "69cc53e531fbdbfac7758a02ebad298084f529bab4f2e1cb715c6ad190450fa9"
web_gpt_submission_result: evidence_packs/group-04-agent-runtime-capability-cleanup/WEB_GPT_SUBMISSION_RESULT.json
web_gpt_submission_result_sha256: "3a14812e4f76f85ec2762c7b2855c983e21c5e81a4afc99bf499769bc84d6ab6"
binding_record: _reports/group-04-agent-runtime-capability-cleanup-binding/GROUP_04_BINDING_RECORD.yaml
scope_limit: "only GROUP-04 selected files"
whole_dirty_worktree_accepted: false
implementation_commit: "1b78ce5"
pushed_to_github: true
```

## GROUP-05 Acceptance Binding (2026-06-07)

Status: accepted by web GPT as chain-evidence schema/runtime hardening.

This entry binds GROUP-05 only. It must not be interpreted as acceptance of the
whole dirty worktree or of excluded dirty groups.

Binding:

```yaml
task_id: GROUP-05
task_name: CHAIN-EVIDENCE-HARDENING
primary_repo: agent-acceptance
overall_judgment: accepted
reviewer_type: gpt
accepted_time: "2026-06-07T12:57:50+08:00"
evidence_pack: evidence_packs/group-05-chain-evidence-hardening/closure-pack.zip
evidence_pack_sha256: "c21e633ef347d31f71cfb42eeff66ecb70df2889fe41464144a85b668413b473"
gpt_review_result: evidence_packs/group-05-chain-evidence-hardening/GPT_REVIEW_RESULT.txt
gpt_review_result_sha256: "ee905c6e7a22044248765fbc02301ccba42f41b94ce6db844f8a1f39ffa1cf7d"
web_gpt_submission_result: evidence_packs/group-05-chain-evidence-hardening/WEB_GPT_SUBMISSION_RESULT.json
web_gpt_submission_result_sha256: "a6da306149cb82fe7473150a011e94e802ab896deec4e70daafa066f65d9d95c"
binding_record: _reports/group-05-chain-evidence-hardening-binding/GROUP_05_BINDING_RECORD.yaml
scope_limit: "only GROUP-05 selected files"
whole_dirty_worktree_accepted: false
implementation_commit: "abcee11"
pushed_to_github: true
supersedes: "prior local-only GROUP-05 accepted pack before rerun-timestamp semantic correction"
```

## WorkQueue Integrity Acceptance Binding (2026-06-07)

Status: accepted by web GPT as the current WorkQueue integrity slice.

This entry binds only the current WorkQueue integrity slice. It must not be
interpreted as completion of all future specialized WorkQueue batches.

Binding:

```yaml
task_id: t-workqueue-integrity-20260601
primary_repo: agent-acceptance
overall_judgment: accepted
reviewer_type: gpt
accepted_time: "2026-06-07T15:36:00+08:00"
evidence_pack: evidence_packs/t-workqueue-integrity-20260607-review/closure-pack.zip
evidence_pack_sha256: "05375bcfbdebe94d10c5aaeef20052c7c65d54857b6736b5413c6383709aaf65"
gpt_review_result: evidence_packs/t-workqueue-integrity-20260607-review/GPT_REVIEW_RESULT.txt
gpt_review_result_sha256: "d2aca05fe87dc3cdf10345a4ae18ed0c8406686a743858b28dda9f8b72e72e8b"
web_gpt_submission_result: evidence_packs/t-workqueue-integrity-20260607-review/WEB_GPT_SUBMISSION_RESULT.json
web_gpt_submission_result_sha256: "9e1a7925c8a4d677ef6048cecccbb831e8007fea30c4b7d3e64b8b5279300302"
binding_record: _reports/t-workqueue-integrity-20260601-binding/WORKQUEUE_INTEGRITY_BINDING_RECORD.yaml
scope_limit: "current WorkQueue integrity slice only"
whole_dirty_worktree_accepted: false
implementation_commit: "361a2c9"
pushed_to_github: true
```

## WorkQueue Specialized Closure Binding (2026-06-07)

Status: accepted by web GPT as the combined WorkQueue specialized-batches and queue-propagation closure slice.

This entry binds only the specialized WorkQueue follow-on path. It must not be
interpreted as acceptance of unrelated governance cleanup or the whole dirty
worktree.

Binding:

```yaml
task_id: t-workqueue-specialized-batches-20260607
primary_repo: agent-acceptance
overall_judgment: accepted
reviewer_type: gpt
accepted_time: "2026-06-07T16:18:00+08:00"
evidence_pack: evidence_packs/t-workqueue-specialized-batches-20260607-closure/closure-pack.zip
evidence_pack_sha256: "a2ad67b86b53fe6fb18f4841d65f65291addefa8a358c1e4f2c7ec58524a8d26"
gpt_review_result: evidence_packs/t-workqueue-specialized-batches-20260607-closure/GPT_REVIEW_RESULT.txt
gpt_review_result_sha256: "d5c44aa2dd7991613e5fdff7132496b30cde1c9ffcadf207e090909bbcd5adbe"
web_gpt_submission_result: evidence_packs/t-workqueue-specialized-batches-20260607-closure/WEB_GPT_SUBMISSION_RESULT.json
web_gpt_submission_result_sha256: "490da89f8e59965e8589e880f6012cc9debdf6384191921a382e9ea273c1cbb"
binding_record: _reports/t-workqueue-specialized-batches-20260607-binding/WORKQUEUE_SPECIALIZED_BATCHES_BINDING_RECORD.yaml
scope_limit: "specialized WorkQueue batches plus queue-level exit propagation only"
whole_dirty_worktree_accepted: false
implementation_commit: "50f6b25"
pushed_to_github: true
```

## CONTEXT-COMPRESSION-A1 Acceptance Binding (2026-06-07)

Status: accepted by web GPT as privacy-safe context compression layer (R6).

This entry binds CONTEXT-COMPRESSION-A1 only. It must not be interpreted as acceptance of the
whole dirty worktree or of excluded dirty groups.

Binding:

```yaml
task_id: CONTEXT-COMPRESSION-A1
task_name: "Long Conversation Context Compression Layer"
primary_repo: agent-acceptance
overall_judgment: accepted
reviewer_type: gpt
review_rounds: 6
accepted_time: "2026-06-07T17:35:00+08:00"
evidence_pack: evidence_packs/context-compression-a1/closure-pack-r6.zip
evidence_pack_sha256: "0dc2c3359f12dd7f4e31d78e00291961383ac5ca1c47fc3e847ba12778ce375e"
gpt_review_result: evidence_packs/context-compression-a1/GPT_REVIEW_RESULT_R6.txt
gpt_review_result_sha256: "99e0ac7942c6dd13f1cd1c939e5e3babc0925999a20291ca5392810151b5e2f3"
scope_limit: "only CONTEXT-COMPRESSION-A1 selected files"
whole_dirty_worktree_accepted: false
implementation_commit: "NOT YET COMMITTED (pre-commit gate blocked)"
pushed_to_github: false
commit_blocker: >
  Pre-commit gate ai_guard.py scans entire working tree (git diff HEAD),
  not just staged files (git diff --cached). 7 dirty-worktree files
  (HANDOFF_REPLY_V4.txt, archive/draft-hooks/*.ps1 x3, runs/*/POST_REVIEW_ROUTE.json x2,
  hooks/sealed-files-manifest.json) are modified in working tree but NOT staged.
  All 107 staged files are clean and covered by TaskSpec write_set.
  GPT adjudication requested but not yet received.
resolution_candidates:
  - "stash dirty files → commit → unstash"
  - "fix ai_guard.py to scan staged-only (separate task AI-GUARD-STAGED-SCOPE-A1)"
  - "GPT authorization for --no-verify"
```

## AI-GUARD-STAGED-SCOPE-A1 Acceptance Binding (2026-06-07)

Status: accepted by web GPT (R4). Fixes ai_guard task mode to scan staged files only.

```yaml
task_id: AI-GUARD-STAGED-SCOPE-A1
task_name: "Fix ai_guard pre-commit scope to staged-files-only"
overall_judgment: accepted
reviewer_type: gpt
review_rounds: 4
evidence_pack: evidence_packs/ai-guard-staged-scope-a1/closure-pack-r4.zip
evidence_pack_sha256: "79e0e821c49f3a8a10b707d7987e77e96d26fe4696d718acd069139e60c2b962"
gpt_review_result: evidence_packs/ai-guard-staged-scope-a1/GPT_REVIEW_RESULT_R4.txt
scope_limit: "only AI-GUARD-STAGED-SCOPE-A1 selected files"
whole_dirty_worktree_accepted: false
implementation_commit: "b517d26a"
pushed_to_github: false
```

## GPT-REVIEW-QUEUE-A1 Acceptance Binding (2026-06-07)

Status: accepted_with_limitation (scope creep R3, core functionality complete).

```yaml
task_id: GPT-REVIEW-QUEUE-A1
task_name: "GPT Review Queue with Lifecycle Management"
overall_judgment: accepted_with_limitation
reviewer_type: gpt
review_rounds: 3
evidence_pack: evidence_packs/gpt-review-queue-a1/closure-pack-r3.zip
scope_limit: "only GPT-REVIEW-QUEUE-A1 selected files"
whole_dirty_worktree_accepted: false
implementation_commit: "b517d26a"
pushed_to_github: false
```

## Session Summary (2026-06-07)

```yaml
session_tasks_completed:
  - CONTEXT-COMPRESSION-A1 (R6 accepted)
  - AI-GUARD-STAGED-SCOPE-A1 (R4 accepted)
  - POST-COMMIT-VERIFICATION-A1 (verified)
  - GPT-REVIEW-QUEUE-A1 (accepted_with_limitation)

session_stats:
  commits: 2 (df530cfc, b517d26a)
  tests: 247 PASS
  ai_guard: PASS (staged-only mode)
  dirty_baseline: "7 files protected, not committed"
```

## AI-WORKFLOW-HUB-RESTORE Acceptance Binding (2026-06-08)

Status: accepted by web GPT (batch review R2). Restored missing modules after dev-frame-opencode restructuring.

```yaml
task_id: AI-WORKFLOW-HUB-RESTORE
task_name: "Restore render_full_governance_md and issue_ledger"
primary_repo: dev-frame-opencode (ai-workflow-hub)
overall_judgment: accepted
reviewer_type: gpt
evidence_pack: evidence_packs/batch-review-20260608/batch-review-r2.zip
impact: "23 failures → 147 PASS, monorepo smoke FAIL → PASS"
implementation_commit: "52487a2f"
pushed_to_github: false
```

## Batch Review Acceptance Binding (2026-06-08)

Status: Batch review R3. Multiple tasks accepted by web GPT with captured replies.

```yaml
batch_id: BATCH-FINAL-20260608
gpt_reply_source: "GPT conversation 6a23dd8c, replies 55-57"
gpt_reply_55_sha256: "549a924bbed73aa17438eb48f29a91e3..."
gpt_reply_56_sha256: "698a09386368732001b4cdd324dbef0d..."
overall_verdict: >
  TASKSPEC-VALIDATOR: accepted_with_limitation
  INFRASTRUCTURE-SCRIPTS: accepted_with_limitation
  PAPER-SAFETY: accepted_with_limitation
  CONTROL-PLANE-SCRIPTS: accepted_with_limitation
  CONTROL-PLANE-BYPASS: accepted_with_limitation
  REVIEW-QUEUE: accepted_with_limitation
  CODEGRAPH-FORK-POOL: review_unverified
evidence_pack: evidence_packs/batch-final-20260608/final-batch-r3.zip
whole_dirty_worktree_accepted: false
p0_rule_applied: "GPT replies captured with SHA256 before reporting verdict"
```

## PAPER-C4-BOUNDED-SECTION-REVIEW-A1 Acceptance Binding (2026-06-08)

Status: accepted_with_limitation (GPT R5, code proof inline verified).

```yaml
task_id: PAPER-C4-BOUNDED-SECTION-REVIEW-A1
task_name: "Bounded paper section review workflow"
overall_judgment: accepted_with_limitation
review_rounds: 5
evidence_pack: evidence_packs/paper-c4-section-review/closure-pack-r2.zip
scope: "synthetic/sanitized section-level review only, no real paper ingestion"
whole_dirty_worktree_accepted: false
implementation_commit: "876e07b3"
pushed_to_github: true
```

## C7-Collaborative-Loop M3 Closure (2026-06-08)

```yaml
task_id: PAPER-M3-P1-RESOLUTION-A1
module: M3
section: 高等教育提质扩容的必然逻辑-实然之境
rounds: 3
final_verdict: pass_with_limitation
gpt_reply_sha256: "2432938330ee4960..."
gpt_response: _reports/m3_round3_gpt_response.txt
resolution: "Title/content alignment resolved. Bidirectional mechanism chain defined. Citation function map with 5 categories."
closed_at: "2026-06-08T08:30:00Z"
```

END_OF_PROJECT_HISTORY
