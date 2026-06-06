# PROJECT_HISTORY.md — DevFrame Agent Acceptance + Control Plane
> 项目生存文档。每阶段完成后追加，永不删除。Agent 和 GPT 共享此文件理解项目全貌。
> Last updated: 2026-06-07T06:37:59+08:00
> Current stage: PAPER-C2 accepted and closed; next GPT-authorized work requires a fresh task gate.
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

END_OF_PROJECT_HISTORY
