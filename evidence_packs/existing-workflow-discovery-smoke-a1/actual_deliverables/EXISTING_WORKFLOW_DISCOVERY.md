# Existing Workflow Discovery — EXISTING-WORKFLOW-DISCOVERY-SMOKE-A1

- run_id: EXISTING_WORKFLOW_DISCOVERY_SMOKE_A1_20260608_234421
- generated_at: 2026-06-08T15:44:21.534906+00:00
- scope: 只读为主的流程发现与复用能力测试
- reused_existing_workflow: true
- not_a_formal_fix_task: true

## 已发现的现有流程组件

| 组件 | 路径 | 存在 | 作用 | 证据层级 |
|---|---|---:|---|---|
| source_of_truth_hierarchy | `HANDOFF_SOURCE_OF_TRUTH.md` | True | 定义 P0/P1/P2/P3 权威层级、approval rule、coding-agent 禁止自批准。 | P1 |
| handoff_approval_record | `HANDOFF_APPROVAL_RECORD.json` | True | 记录 HANDOFF-PIPELINE-REFACTOR-A1 的 verified GPT verdict、run_id、限制和 hash。 | P1 |
| attachment_review_runbook | `_reports/handoff-pipeline-refactor-a1/ATTACHMENT_BACKED_GPT_REVIEW_RUNBOOK.md` | True | 附件版 GPT 审查 SOP：fresh shell、run_id、新对话、附件可见、点击提交、确认 user bubble、捕获并 verifier。 | P1 |
| gpt_reply_verifier | `scripts/verify_gpt_reply.py` | True | fail-closed 校验 captured GPT reply：END marker、overall_judgment、task_id、next_task_authorization。 | P0 |
| attachment_submit_entrypoint | `scripts/gpt_new_chat_attachment_submit.py` | True | 附件提交入口，指向已验证 strict submitter；后续需参数化复用。 | P0 |
| pre_gpt_review_gate | `scripts/pre_gpt_review_gate.py` | True | 提交 GPT 前 gate：复用 evidence_pack_linter 并检查 actual_deliverables 与 manifest。 | P0 |
| evidence_pack_linter | `scripts/evidence_pack_linter.py` | True | 检查 evidence pack 必备文件、目录、summary-only 风险和 stale/failing output。 | P0 |
| global_repair_gpt_record | `_reports/global-project-handoff-repair-a1/GPT_REVIEW_RECORD.json` | True | GLOBAL-PROJECT-HANDOFF-REPAIR-A1 的 GPT 审查记录与 required fix。 | P0 |
| global_repair_verify_output | `_reports/global-project-handoff-repair-a1/VERIFY_GPT_REPLY_OUTPUT.txt` | True | GLOBAL-PROJECT-HANDOFF-REPAIR-A1 verifier 通过证据。 | P0 |
| global_repair_pre_gpt_gate | `_reports/global-project-handoff-repair-a1/PRE_GPT_GATE_OUTPUT.txt` | True | GLOBAL-PROJECT-HANDOFF-REPAIR-A1 linter/gate 通过证据。 | P0 |
| global_repair_execution_report | `_reports/global-project-handoff-repair-a1/EXECUTION_REPORT.md` | True | GLOBAL-PROJECT-HANDOFF-REPAIR-A1 执行报告、限制、next task。 | P0 |
| global_repair_pack_manifest | `_reports/global-project-handoff-repair-a1/PACK_MANIFEST.md` | True | GLOBAL-PROJECT-HANDOFF-REPAIR-A1 evidence pack manifest。 | P0 |
| whole_project_source_map | `_reports/global-project-handoff-repair-a1/WHOLE_PROJECT_SOURCE_OF_TRUTH_MAP.json` | True | whole-project claims 到 P0/P1/P3/unverified evidence 的映射。 | P0 |
| whole_project_stale_claims | `_reports/global-project-handoff-repair-a1/WHOLE_PROJECT_STALE_CLAIMS_REGISTER.json` | True | stale/unverified claims register，保护 296 PASS、production promotion 等限制。 | P0 |
| whole_project_test_ledger | `_reports/global-project-handoff-repair-a1/WHOLE_PROJECT_TEST_LEDGER.json` | True | 测试 ledger，明确 13 passed 与 12/13 mismatch，296 PASS 不验证。 | P0 |
| evidence_binding_gpt_result | `_reports/global-project-evidence-binding-a1/GPT_REVIEW_RESULT.txt` | True | 最近 GLOBAL-PROJECT-EVIDENCE-BINDING-A1 GPT blocked verdict。 | P0 |
| evidence_binding_verify_output | `_reports/global-project-evidence-binding-a1/VERIFY_GPT_REPLY_OUTPUT.txt` | True | 最近 blocked verdict 的 verifier 输出。 | P0 |
| evidence_binding_pack_manifest | `_reports/global-project-evidence-binding-a1/PACK_MANIFEST.md` | True | 最近 evidence-binding pack manifest。 | P0 |
| evidence_binding_execution_report | `_reports/global-project-evidence-binding-a1/EXECUTION_REPORT.md` | True | 最近 evidence-binding 执行报告。 | P0 |
| evidence_binding_changed_files | `_reports/global-project-evidence-binding-a1/CHANGED_FILES_EVIDENCE.json` | True | changed-files evidence，含 HANDOFF_REPLY_V4.txt deletion conflict。 | P0 |
| evidence_binding_protected_status | `_reports/global-project-evidence-binding-a1/PROTECTED_LEGACY_FILES_STATUS.json` | True | protected legacy files status。 | P0 |
| evidence_binding_source_appendix | `_reports/global-project-evidence-binding-a1/SOURCE_MAP_EVIDENCE_BINDING_APPENDIX.json` | True | source map evidence binding appendix，含旧 ZIP 嵌入声明。 | P0 |

## 本项目已有 GPT review 闭环组成

1. `HANDOFF_SOURCE_OF_TRUTH.md` 定义 P0/P1/P2/P3 权威层级和 approval rule。
2. 任务执行生成 evidence pack、manifest、safety scan、targeted test output、execution report。
3. `scripts/evidence_pack_linter.py` 检查 pack 必备结构，避免 summary-only。
4. `scripts/pre_gpt_review_gate.py` 在提交 GPT 前做 gate。
5. 附件版 runbook 要求 fresh shell、唯一 run_id、新/指定 GPT 对话、附件可见、点击提交按钮、确认 user bubble/assistant response。
6. GPT 回复必须包含 run_id、task_id、overall_judgment、END_OF_GPT_RESPONSE。
7. `scripts/verify_gpt_reply.py` fail-closed 校验 captured reply；不通过不得报告 accepted/closed。
8. GPT verdict、verify output、review record、pack manifest 进入 P0/P1 证据层。

## 本轮会复用的组件

- `HANDOFF_SOURCE_OF_TRUTH.md`
- `_reports/handoff-pipeline-refactor-a1/ATTACHMENT_BACKED_GPT_REVIEW_RUNBOOK.md`
- `scripts/verify_gpt_reply.py`
- `scripts/gpt_new_chat_attachment_submit.py`
- `scripts/evidence_pack_linter.py`
- `scripts/pre_gpt_review_gate.py`
- `_reports/global-project-handoff-repair-a1/*` 的 review/gate/source-map/stale/test-ledger 证据
- `_reports/global-project-evidence-binding-a1/*` 的 blocked verdict、changed-files、protected status、source appendix

## 不能替代 source-of-truth 的组件

- memory / compiled memory 只能 recall，不能定案。
- legacy `PROJECT_HISTORY*` / `HANDOFF*` / paste block 只能 P3 audit/reference。
- 未经 verifier 的 root `GPT_*.txt` 不能作为当前 verdict。
- 对话里的 `296 PASS` 仍是 unverified conversational claim。

## 重新造轮子的风险

存在风险：如果直接根据对话重写提交流程、重新写 verifier、重新定义 source-of-truth，可能绕开已验证 runbook/gate/verifier，导致旧回复误捕获、附件未确认、blocked 被包装成 success。

## 避免重新造轮子的方式

- R2 只复用现有 runbook、verifier、linter、pre-GPT gate、source-of-truth map。
- 对 blocked 三个问题做最小 evidence 修复，不新建 review workflow。
- 不改写 legacy 文件；如需恢复/移动/删除 `HANDOFF_REPLY_V4.txt`，属于高风险 git/legacy 操作，先问用户。
- 保留 `blocked`、`accepted_with_limitation`、`partial/needs_more_evidence` 原状态，不美化。
