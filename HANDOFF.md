Markdown# HANDOFF.md  # DevFrame / Agent-Acceptance / Control-Plane 项目交接文档> 本文件由 GPT 生成，用于新对话冷启动。  > Agent 只负责保存、传递、上传本文件，不得改写其中的事实判断、状态结论、安全边界和下一步任务授权。  > 新对话必须先读取本文件，并用 YAML 确认理解后，才能继续执行后续任务。  > 本文件的目标是解决当前对话上下文过长、GPT 回复可能被提前读取、agent 在任务边界处反复询问“是否继续”等问题。  ---# 1. 项目身份## 1.1 项目总称本项目属于 DevFrame 工作流治理与多智能体协作实验体系，当前主要围绕以下三个仓库或层级展开：1. `agent-acceptance`     负责合约、审查规则、证据包规范、GPT 审查模板、安全边界、workflow validator、memory layer 设计等规范层能力。2. `devframe-control-plane`     负责 pipeline 编排、stage executor、pack validate、submission adapter、reference paper pipeline、handoff 协议、CLI 入口等控制层能力。3. `dev-frame-opencode`     负责具体执行任务、代码修改、测试运行、产物生成等执行层能力。该层不应拥有最终治理权，不应直接提交 GPT，不应直接伪造 FLOW_OUTCOME 或 closure 状态。## 1.2 项目核心目标项目目标不是简单写脚本，而是建立一套可审计、可复用、可 fail-closed 的工作流治理系统，使 agent 在执行任务时不能仅凭自然语言声明完成，而必须提供可复核 evidence。项目的长期目标包括：- 让 GPT 审查从“人工反复驳回低级证据缺失”转向“基于完整证据包的高质量评审”。- 让 agent 执行任务时默认走框架路径，而不是手写临时 Playwright、手动 ZIP、手动 FLOW_OUTCOME。- 让任务状态 `ready_for_review`、`accepted`、`closed` 严格区分。- 让 summary-only evidence pack、closed_without_gpt_accepted、governance self-close 在本地提交前失败。- 让长对话超过阈值时自动 handoff，避免上下文过载导致 GPT 回复变慢、截断或被 agent 提前读取。- 让项目中的失败模式、审查结论、修复经验能够沉淀到 Memory Layer，但 memory 只能作为辅助上下文，不能替代 evidence 或 GPT accepted。---# 2. 三层架构## 2.1 第一层：agent-acceptance，合约与审查规范层`agent-acceptance` 是规范层和验收层，负责回答“什么可以被接受”。它的职责包括：- 定义 paper acceptance contracts。- 定义 workflow closure contracts。- 定义 framework usage contracts。- 定义 GPT review prompt template。- 定义 evidence pack schema。- 定义 workflow closure validator。- 定义 memory compilation contract。- 定义 privacy / redaction policy。- 定义 pre-submission checklist。- 定义 no-bypass submission 规则。- 定义 closed / accepted / ready_for_review 的状态约束。- 定义 retroactive review 的合法方式。- 定义 historical incomplete run 与 negative fixture 的分类方式。- 阻断 summary-only pack。- 阻断 closed_without_gpt_accepted。- 阻断 governance self-close。- 阻断未经授权的 direct Playwright / submit_to_gpt.py / connect_over_cdp。重要原则：```yamlagent_acceptance_principles:  - "agent summary is not evidence"  - "ready_for_review is not closed"  - "closed requires GPT accepted + ledger entry"  - "memory is not evidence"  - "memory cannot mark accepted"  - "summary-only evidence pack must fail locally"  - "governance tasks cannot self-close"  - "validator fail must fail-closed"
2.2 第二层：devframe-control-plane，编排与执行控制层
devframe-control-plane 是编排层，负责回答“如何按规范执行”。
它的职责包括：


解析 YAML pipeline。


执行 stage。


生成或验证 evidence pack。


调用 agent-acceptance 的 validator。


执行 devframe pack validate。


执行 reference_paper_review pipeline。


执行 pre_submission_check。


调用 submission_adapter。


默认使用 dry-run submission。


在 validator fail 时 fail-closed。


将 WORKFLOW_CLOSURE_VALIDATION.yaml 纳入 reference pipeline 最终 evidence pack。


维护 CLI 入口。


维护 handoff transfer / bootstrap 流程。


重要限制：
YAMLcontrol_plane_limits:  - "不拥有规范最终解释权"  - "不应复制 agent-acceptance validator 逻辑"  - "应调用 agent-acceptance validator"  - "不应默认启用 live CDP"  - "不应直接处理真实论文"  - "不应让 pipeline 在 validator fail 后继续执行"
2.3 第三层：dev-frame-opencode，执行层
dev-frame-opencode 是执行层，负责回答“如何具体改文件、跑测试、生成产物”。
它可以：


修改代码。


修改文档。


运行测试。


生成 synthetic evidence。


生成 closure evidence pack。


按 GPT 任务书执行。


它不可以：


自己把任务标记为 accepted。


自己把 ready_for_review 当成 closed。


自己写假 GPT_REVIEW_RESULT。


手动伪造 FLOW_OUTCOME。


绕过 control-plane 的 submission_adapter。


直接写 Playwright 脚本提交 GPT。


删除、移动、重命名、清理历史 evidence。


处理真实论文或用户私密文本。


默认启用 live CDP。



3. 已完成事项与审查状态
以下是当前已知的关键任务状态。所有 accepted 任务都应在后续 WORKFLOW_AUDIT_LEDGER.yaml 或等价 ledger 中持续记录。
3.1 Push Blocker Resolution / Plan C
任务内容：


解决 pre-push governance gate 因两个历史 runs 目录阻断 push 的问题。


不删除 evidence。


不伪造 evidence。


不跳过 pre-push hook。


引入 run evidence classification。


最终策略：
YAMLclassification:  historical_incomplete_run:    meaning: "历史未闭合 run"    required:      - RUN_CLASSIFICATION.yaml      - INCOMPLETE_RUN_DECLARATION.md    rules:      - accepted: false      - review_verified: false  negative_test_fixture:    meaning: "故意无效的负向测试样例"    required:      - RUN_CLASSIFICATION.yaml      - NEGATIVE_FIXTURE_DECLARATION.md    rules:      - expected_invalid: true      - accepted: false      - review_verified: false
最终 GPT 审查：
YAMLREVIEW_RUN_ID: "push-blocker-resolution-final-review-v1"overall_judgment: "accepted"status: "closed"meaning: "Plan C 分类机制 accepted"
3.2 ARCH-GAP-A1：Framework Usage Enforcement
任务内容：


发现 agent 多次绕过三层架构，直接手写 Playwright、手动 ZIP、手动 FLOW_OUTCOME、手动提交 GPT。


新增 framework usage enforcement。


新增 no-bypass submission 规则。


新增 reference paper review pipeline 设计文档。


新增 check_submission_bypass.py。


形成 ARCH-GAP-A1 事后 GPT closure review。


关键产物：


docs/framework-usage-enforcement.md


contracts/framework_usage_contract.yaml


docs/reference-paper-review-pipeline.md


scripts/check_submission_bypass.py


tests/test_framework_usage.py


最终 GPT 审查：
YAMLREVIEW_RUN_ID: "arch-gap-a1-retroactive-closure-review-v1"overall_judgment: "accepted"retroactive_review: truestatus: "closed"
注意：
ARCH-GAP-A1 最初出现 self-referential failure：它定义禁止绕过框架，但自身曾未经过 GPT closure review 就被当成 ready_for_review / closed。后来通过事后 GPT accepted 补审修复。
3.3 REF-PAPER-1：Reference Paper Review Pipeline Design
任务内容：


设计 reference_paper_review.yaml。


起初只 dry-run，后来补交 evidence pack。


该 pipeline 后续通过 REF-PAPER-2B 实际执行闭环验证。


关键产物：


pipelines/reference_paper_review.yaml


DRY_RUN_OUTPUT.txt


TEST_OUTPUT.txt


DOCTOR_OUTPUT.txt


BYPASS_CHECK_OUTPUT.txt


最终 GPT 审查：
YAMLREVIEW_RUN_ID: "ref-paper-1-retroactive-pipeline-design-final-review-v1"overall_judgment: "accepted"retroactive_review: truestatus: "closed"
注意：
用户摘要曾提到 11-stage，但证据支持的是 7-stage reference pipeline。后续 ledger 中应以证据支持的 7-stage 为准，避免混淆。
3.4 REF-PAPER-2B：Reference Paper Pipeline Real Execution
任务内容：


reference paper pipeline 从 dry-run 进入真实 synthetic-only 执行。


7 stages 全部执行：


project_init


load_input


paper_review


build_evidence_pack


pre_submission_check


submission_dry_run


closure




生成 synthetic paper review 产物。


不处理真实论文。


不启用 live CDP。


submission_adapter dry-run。


生成 16 files evidence pack。


多轮修复 manifest、pipeline_run_id、safety attestation、TEST_OUTPUT、BYPASS_CHECK_OUTPUT 后 accepted。


最终 GPT 审查：
YAMLREVIEW_RUN_ID: "ref-paper-2b-final-resubmission-review-v1"overall_judgment: "accepted"status: "closed"
意义：
REF-PAPER-2B 证明 reference paper pipeline 可以实际执行，不再只是 YAML dry-run。
3.5 MEMORY-A1：Workflow Memory Compilation Layer Design
任务内容：


借鉴 claude-memory-compiler 的思想，但不直接引入 hooks。


设计 DevFrame Memory Layer。


Memory 只记录可复用教训，不替代 evidence。


Memory 不能替代 GPT accepted。


Memory 不能处理真实论文全文。


Memory 不能读取 raw full transcript。


Memory 不能自动外部上传。


Memory 不能自动 acceptEdits。


定义 memory source、entry、privacy、lint contracts。


定义 daily log、concept article、index 模板。


定义 privacy / redaction policy。


定义 memory lint rules。


提供 synthetic examples。


后续进行模板中文化、自由格式计划章节、pytest warning 清理。


关键 REVIEW_RUN_ID：
YAMLprimary_review:  REVIEW_RUN_ID: "memory-a1-workflow-memory-design-final-review-v1"  overall_judgment: "accepted"post_acceptance_fixes:  REVIEW_RUN_ID: "memory-a1-post-acceptance-fixes-review-v1"  overall_judgment: "accepted"
3.6 WORKFLOW-HARDENING-A1：Evidence-First Workflow Closure Validation
任务内容：


修复 MEMORY-A1 ledger 中记录的三个系统性缺陷：


SD-01 summary-only evidence pack pattern


SD-02 ready_for_review 被当作 closed


SD-03 self-referential failure




新增 workflow_closure_contract.yaml。


新增 validate_workflow_closure.py。


新增 closure report template。


新增 workflow state policy。


新增测试。


多轮修复 GPT_REVIEW_RESULT 与 ledger 绑定、validator fresh pass、manifest 自洽等问题。


最终 accepted。


最终 GPT 审查：
YAMLREVIEW_RUN_ID: "workflow-hardening-a1-final-closure-review-v1"overall_judgment: "accepted"status: "closed"SD_01: "fixed"SD_02: "fixed"SD_03: "fixed"
重要结果：
YAMLworkflow_hardening_a1_results:  summary_only_pack: "本地 validator 阻断"  ready_for_review_as_closed: "本地 validator 阻断"  governance_self_close: "本地 validator 阻断"  closed_requires:    - "GPT_REVIEW_RESULT accepted"    - "reviewer_type=gpt"    - "WORKFLOW_AUDIT_LEDGER binding"
3.7 WORKFLOW-HARDENING-A2：Pre-Push / Pre-Submission Integration
用户说明显示：
YAMLWORKFLOW_HARDENING_A2:  status: "deployed"  meaning: "workflow closure validator 已接入 pre-push gate step 2.5"
注意：
当前对话中没有完整的 A2 closure accepted YAML 细节，但用户明确表示 A2 deployed。后续新对话应尽量要求 agent 提供 ledger 或 evidence pack 以确认最终状态。
3.8 CONTROL-PLANE-A1：devframe-control-plane 接入 workflow closure validator
任务内容：


将 agent-acceptance 的 workflow closure validator 接入 devframe-control-plane。


devframe pack validate 默认调用 workflow closure validator。


pack validate 对 summary-only、closed_without_gpt_accepted、governance self-close 本地阻断。


missing validator 默认 fail。


pipeline pre_submission_check 调用 validator。


validator fail 时 pipeline stage failed。


reference pipeline 最终 evidence pack 纳入 WORKFLOW_CLOSURE_VALIDATION.yaml。


多轮修复 stale 输出、manifest、pack validate pass、bad pack fail 输出、pipeline pack 自动纳入 validation 等问题。


最终 accepted。


最终 GPT 审查：
YAMLREVIEW_RUN_ID: "control-plane-a1-r9-final-closure-review-v1"overall_judgment: "accepted"status: "closed"
重要结果：
YAMLcontrol_plane_a1_results:  pack_validate_calls_workflow_validator: true  validator_fail_causes_pack_validate_fail: true  summary_only_pack_blocked: true  closed_without_gpt_accepted_blocked: true  governance_self_close_blocked: true  pre_submission_stage_calls_workflow_validator: true  validator_fail_causes_pipeline_stage_failed: true  reference_pipeline_final_pack_includes_WORKFLOW_CLOSURE_VALIDATION: true

4. 当前未解决问题
4.1 GPT 回复被提前读取问题
审计发现：
YAMLproblem:  observed_case: "paper-a1-contract-design-v1/GPT_REPLY.txt"  gpt_reply_size: "174 bytes"  risk: "agent 在 GPT 回复仅 174 bytes 时就开始执行"
这说明 agent 可能没有等待 GPT 回复完整生成，或者读取 GPT_REPLY.txt 的逻辑只看文件存在，不看完整性。
风险：


agent 读取不完整方案。


agent 执行截断的任务书。


agent 误以为 GPT 已给出 accepted / blocked / 任务计划。


造成后续 evidence pack 与真实 GPT 意图不一致。


在长对话中更容易出现，因为 GPT 响应时间 90s+，文件可能先写入部分内容。


必须解决：
YAMLmust_fix:  - "GPT_REPLY.txt 少于阈值不得执行"  - "缺结束标记不得执行"  - "缺 required YAML fields 不得执行"  - "长对话必须触发 handoff"
4.2 当前对话已严重超载
当前对话已积累约 82 条 assistant message，响应时间已达到 90s+。
风险：


GPT 回复变慢。


GPT 回复可能截断。


agent 可能提前读取。


历史上下文混杂。


审查状态容易混乱。


accepted / blocked / review_unverified 的标准可能漂移。


同一任务多轮修复时容易发生 stale evidence 或 stale output。


当前状态：
YAMLconversation_state:  assistant_messages: "82+"  response_time: "90s+"  handoff_required: true  urgency: "high"
4.3 缺少自动 handoff 机制
当前 handoff 虽然已有 T3 流程理念：
YAMLhandoff_protocol:  - "GPT writes HANDOFF.md"  - "Agent transfers as .md file attachment"  - "New conversation confirms understanding"  - "handoff_verified=true"  - "fail-closed if not confirmed"
但缺少自动阈值判断与脚本：


不会自动判断 assistant message count。


不会自动判断 response time。


不会自动判断 GPT_REPLY bytes。


不会自动判断 review rounds。


不会自动要求 current GPT 生成 HANDOFF.md。


不会自动验证 HANDOFF.md 完整性。


不会自动阻断未确认的新对话继续执行。


4.4 agent 在任务边界处反复询问“继续吗”
此前已重复发生多次：


R2 增强计划后 agent 问继续。


A2 完成后 agent 又问继续。


说明“直接执行”授权只在当前任务内部有效，跨任务边界失效。


根因：
YAMLroot_cause:  - "没有 next_task_authorization 机器可读块"  - "任务书写了直接执行，但 agent 在任务完成后把下一任务视为新授权边界"  - "没有 rolling authorization 机制"
建议：
每次 GPT accepted 之后，必须给出：
YAMLnext_task_authorization:  authorized: yes  execute_immediately: yes  ask_before_starting: no  task_id: "<NEXT_TASK_ID>"
但更优先的是当前 HANDOFF-A1：先解决长对话与 GPT_REPLY 完整性问题。

5. 安全边界
以下边界必须在所有后续任务中严格执行。
5.1 evidence 边界
禁止：
YAMLevidence_safety:  prohibited:    - "删除 evidence"    - "移动 evidence"    - "重命名 evidence"    - "清理 runs"    - "覆盖历史 evidence"    - "伪造 GPT accepted"    - "伪造测试输出"    - "伪造 FLOW_OUTCOME"    - "伪造 WORKFLOW_CLOSURE_VALIDATION"    - "补造不存在的历史 closure"
允许：
YAMLevidence_safety:  allowed:    - "新增 evidence"    - "新增声明文件"    - "新增 classification metadata"    - "新增 synthetic test fixture"    - "新增 validation output"    - "新增 closure pack"
5.2 guard 边界
禁止：
YAMLguard_safety:  prohibited:    - "移除 guard"    - "弱化 guard"    - "把 fail 改成 warning 以通过"    - "跳过 pre-push hook"    - "默认关闭 validator"    - "默认 allow missing validator"
若必须引入 skip 选项，必须满足：
YAMLskip_policy:  - "必须显式参数"  - "必须用于测试或明确授权"  - "必须在输出中标记 skipped_by_explicit_authorization"  - "不得默认 skip"
5.3 live CDP / 浏览器边界
禁止：
YAMLbrowser_safety:  prohibited:    - "启用 live CDP"    - "读取 cookies"    - "读取 session"    - "读取 browser profile"    - "直接 connect_over_cdp"    - "手写 Playwright 提交 GPT"    - "创建临时 submit_to_gpt.py 绕过 submission_adapter"
除非用户明确授权 live CDP pilot，否则所有 submission 都必须 dry-run。
5.4 论文与隐私边界
用户明确要求上传文本和论文内容保密。禁止：
YAMLprivacy_safety:  prohibited:    - "处理真实用户论文作为测试样例"    - "把用户论文写入 memory"    - "把用户论文作为他人参考素材"    - "读取真实博士论文/小论文全文进入项目 memory"    - "将私密文本上传外部服务"    - "将用户论文加入 synthetic fixture"
允许：
YAMLprivacy_safety:  allowed:    - "使用 synthetic paper"    - "记录脱敏后的 workflow lesson"    - "记录不含真实论文文本的审查经验"
5.5 任务执行授权边界
默认允许：
YAMLallowed_without_asking:  - "新增或修改文档"  - "新增或修改合约"  - "新增或修改 validator"  - "新增或修改测试"  - "新增 synthetic fixture"  - "构建 closure evidence pack"  - "运行 pytest"  - "运行 bypass checker"  - "运行 workflow closure validator"  - "运行 pack validate"
必须停下询问：
YAMLmust_stop_and_ask:  - "删除、移动、重命名、清理 evidence"  - "删除历史 runs"  - "覆盖历史 evidence"  - "移除或弱化 guard"  - "启用 live CDP"  - "读取 cookies/session/profile"  - "处理真实用户论文"  - "伪造 GPT accepted"  - "伪造测试输出"

6. 执行规则
6.1 Evidence-First
所有 accepted / blocked / review_unverified 结论必须基于实际 evidence。
禁止只凭 agent summary。
YAMLevidence_first:  rules:    - "agent summary is not evidence"    - "closure report is not actual deliverable"    - "safety attestation is not test output"    - "GPT_REVIEW_PROMPT is not evidence"    - "manifest must match ZIP bidirectionally"    - "hashes must be reproducible"    - "validator output must be fresh"    - "pack validate output must match current pack"
6.2 状态规则
YAMLworkflow_state_rules:  ready_for_review:    meaning: "准备提交 GPT 审查"    not_equal_to:      - "accepted"      - "closed"  accepted:    meaning: "GPT 基于 evidence pack 给出 accepted"    requires:      - "GPT_REVIEW_RESULT"      - "overall_judgment: accepted"      - "reviewer_type: gpt"  closed:    meaning: "accepted 已写入 ledger / state"    requires:      - "GPT accepted"      - "WORKFLOW_AUDIT_LEDGER binding"      - "evidence_pack_sha256"
6.3 validator 规则
validate_workflow_closure.py 已在 agent-acceptance 中 accepted，并已接入 control-plane pack validate。
它应阻断：
YAMLvalidator_blocks:  - "summary-only pack"  - "manifest mismatch"  - "hash mismatch"  - "closed_without_gpt_accepted"  - "accepted_without_review_result"  - "governance self-close"  - "retroactive review missing required fields"
6.4 framework 路径规则
正式任务不得绕过框架。
YAMLframework_usage:  official_path:    - "pipeline"    - "runner / stage_executor"    - "pack builder / pack validate"    - "workflow closure validator"    - "submission_adapter"    - "closure evidence pack"    - "GPT review"  bypass_forbidden:    - "manual ZIP as final proof"    - "manual FLOW_OUTCOME as authoritative"    - "direct Playwright GPT submission"    - "ad-hoc submit_to_gpt.py"
6.5 长对话规则
必须引入 handoff 阈值：
YAMLhandoff_thresholds:  hard:    assistant_message_count: ">= 60"    gpt_response_time_seconds: ">= 60"    review_rounds_same_task: ">= 3"    gpt_reply_bytes: "< 2000 for structured review/task plan"  current:    assistant_message_count: "82+"    response_time_seconds: "90+"    handoff_required: true
6.6 GPT reply 完整性规则
agent 不得在 GPT 回复不完整时执行。
YAMLgpt_reply_completeness:  min_bytes_for_review: 2000  min_bytes_for_task_plan: 3000  min_bytes_for_handoff: 8000  required_end_marker_for_handoff: "END_OF_HANDOFF"  if_reply_too_short: "do_not_execute"  if_missing_required_yaml_fields: "do_not_execute"  if_mid_code_block_or_mid_yaml: "do_not_execute"

7. 上下文压缩摘要
7.1 主要演进脉络
项目从最初的多智能体/控制平面自动化，逐步扩展到论文工作流、证据包治理、GPT 审查模板、workflow hardening、memory layer 设计、control-plane validator 集成。
关键转折点：


PAPER-A1 暴露 summary-only pack 问题。


Push Blocker 暴露历史 run 与 negative fixture 分类问题。


ARCH-GAP-A1 暴露 agent 绕过三层架构问题。


REF-PAPER-1 / 2B 建立 reference paper pipeline。


MEMORY-A1 建立 memory layer 设计。


WORKFLOW-HARDENING-A1 修复 SD-01/02/03。


CONTROL-PLANE-A1 将 validator 接入 pack validate / pipeline。


当前暴露新问题：GPT_REPLY 174 bytes 提前执行 + 长对话超载。


7.2 已修复的系统性缺陷
YAMLfixed_systemic_defects:  SD_01:    name: "summary-only evidence pack pattern"    fixed_by: "WORKFLOW-HARDENING-A1"    status: "fixed"  SD_02:    name: "ready_for_review treated as closed"    fixed_by: "WORKFLOW-HARDENING-A1"    status: "fixed"  SD_03:    name: "self-referential failure"    fixed_by: "WORKFLOW-HARDENING-A1"    status: "fixed"
7.3 当前新系统性缺陷
YAMLopen_systemic_defects:  SD_04:    name: "GPT reply incomplete but executed"    evidence: "paper-a1-contract-design-v1/GPT_REPLY.txt only 174 bytes"    risk: "agent executes incomplete plan"    required_fix: "GPT reply completeness guard"  SD_05:    name: "conversation overload without automatic handoff"    evidence: "82+ assistant messages, 90s+ response time"    risk: "slow response, truncation, state drift"    required_fix: "automatic handoff threshold + HANDOFF.md protocol"  SD_06:    name: "task boundary authorization loss"    evidence: "agent repeatedly asks continue after explicit task plans"    risk: "execution loop stalls"    required_fix: "next_task_authorization / rolling authorization"
7.4 当前最优下一步
当前不建议继续 MEMORY-A2 或 PAPER-WORKFLOW 扩展。
必须先做：
YAMLnext_task:  task_id: "HANDOFF-A1"  goal: "自动化对话交接与 GPT 回复完整性保护"  reason:    - "当前对话已严重超载"    - "agent 曾读取 174 bytes GPT_REPLY"    - "必须防止不完整 GPT 回复被执行"    - "必须建立自动 handoff 流程"

8. 下一任务：HANDOFF-A1
8.1 任务名称
YAMLtask_id: "HANDOFF-A1"task_name: "自动化对话交接与 GPT 回复完整性保护"repo: "优先 devframe-control-plane；必要规范同步到 agent-acceptance"task_type: "handoff_automation / reply_completeness_guard / no_live_cdp / no_real_user_data"authorization:  authorized: yes  execute_immediately: yes  ask_before_starting: no
8.2 任务目标
HANDOFF-A1 必须实现：


GPT 回复完整性检测。


长对话 handoff 触发检测。


HANDOFF.md 结构验证。


新对话启动协议。


不完整 GPT_REPLY 阻断执行。


82 条 assistant message 触发 handoff。


174 bytes GPT_REPLY 阻断。


新对话未确认理解前，不得继续执行。


自动化脚本与测试。


8.3 建议新增脚本
YAMLscripts:  - "scripts/validate_gpt_reply_completeness.py"  - "scripts/check_handoff_needed.py"  - "scripts/validate_handoff.py"
8.4 GPT 回复完整性检测
新增 scripts/validate_gpt_reply_completeness.py。
检查：
YAMLgpt_reply_guard_checks:  - "GPT_REPLY.txt exists"  - "file_size >= min_bytes"  - "structured review must contain required YAML fields"  - "handoff must contain END_OF_HANDOFF"  - "not truncated mid-yaml"  - "not truncated mid-code-block"  - "not only 1-3 short lines"
默认阈值：
YAMLthresholds:  review_min_bytes: 2000  task_plan_min_bytes: 3000  handoff_min_bytes: 8000  require_end_marker_for_handoff: true
失败行为：
YAMLon_fail:  - "do not execute"  - "write GPT_REPLY_COMPLETENESS_RESULT.yaml"  - "mark GPT_REPLY_INCOMPLETE"  - "request retry or regeneration"
8.5 Handoff 触发检测
新增 scripts/check_handoff_needed.py。
输入：
YAMLinputs:  - "assistant_message_count"  - "response_time_seconds"  - "review_round_count"  - "last_gpt_reply_bytes"
规则：
YAMLhandoff_needed_if:  - "assistant_message_count >= 60"  - "response_time_seconds >= 60"  - "review_round_count >= 3"  - "last_gpt_reply_bytes < 2000"
当前应触发：
YAMLcurrent_case:  assistant_message_count: "82+"  response_time_seconds: "90+"  handoff_needed: true
8.6 Handoff 文档验证
新增 scripts/validate_handoff.py。
检查：
YAMLhandoff_validation:  - "HANDOFF.md exists"  - "size >= 8000 bytes"  - "contains END_OF_HANDOFF"  - "contains project identity"  - "contains architecture"  - "contains completed phases"  - "contains current status"  - "contains unresolved problems"  - "contains safety boundaries"  - "contains execution rules"  - "contains next task"  - "contains new conversation prompt"
8.7 新对话启动提示词
新对话第一条消息必须为：
请阅读附件 HANDOFF.md，理解项目身份、架构、已完成阶段、当前状态、安全边界和推荐下一步。请使用 YAML 回复确认：overall_judgment: accepted | blocked | review_unverifiedhandoff_understood: yes | noproject_identity_understood: yes | noarchitecture_understood: yes | nocompleted_phases_understood: yes | nocurrent_state_understood: yes | nosafety_boundaries_understood: yes | nonext_steps_understood: yes | noready_for_next_authorization: yes | norationale: "<中文说明>"
只有新 GPT 回复：
YAMLoverall_judgment: acceptedhandoff_understood: yesready_for_next_authorization: yes
agent 才能继续执行 HANDOFF-A1 或后续任务。
8.8 HANDOFF-A1 测试要求
新增测试：
YAMLtests:  - "174 bytes GPT_REPLY -> fail"  - "完整 YAML review -> pass"  - "missing overall_judgment -> fail"  - "assistant messages 82 -> handoff_needed"  - "assistant messages 30 -> no handoff"  - "HANDOFF.md missing END_OF_HANDOFF -> fail"  - "HANDOFF.md below 8000 bytes -> fail"  - "valid HANDOFF.md -> pass"
8.9 HANDOFF-A1 验收标准
YAMLacceptance_criteria:  - "174 bytes GPT_REPLY 被阻断"  - "缺 required YAML fields 被阻断"  - "assistant_message_count >= 60 触发 handoff"  - "response_time >= 60s 触发 handoff"  - "HANDOFF.md 低于 8000 bytes 被阻断"  - "HANDOFF.md 缺 END_OF_HANDOFF 被阻断"  - "新对话未确认理解前不得继续"  - "不启用 live CDP"  - "不处理真实论文"

9. 新对话启动提示词
Agent 在保存并上传本文件到新对话后，应发送以下消息：
请阅读附件 HANDOFF.md，理解项目身份、三层架构、已完成阶段、当前未解决问题、安全边界、执行规则和下一任务 HANDOFF-A1。请使用 YAML 回复确认：overall_judgment: accepted | blocked | review_unverifiedhandoff_understood: yes | noproject_identity_understood: yes | noarchitecture_understood: yes | nocompleted_phases_understood: yes | nocurrent_state_understood: yes | nosafety_boundaries_understood: yes | nonext_steps_understood: yes | noready_for_next_authorization: yes | norationale: "<中文说明>"
新对话只有在确认理解后，才能继续执行 HANDOFF-A1。

10. 最终状态摘要
YAMLhandoff_summary:  project_identity: "DevFrame 三层工作流治理体系"  current_conversation_status: "overloaded"  assistant_messages: "82+"  response_time: "90s+"  handoff_required: trueaccepted_tasks:  - REVIEW_RUN_ID: "push-blocker-resolution-final-review-v1"  - REVIEW_RUN_ID: "arch-gap-a1-retroactive-closure-review-v1"  - REVIEW_RUN_ID: "ref-paper-1-retroactive-pipeline-design-final-review-v1"  - REVIEW_RUN_ID: "ref-paper-2b-final-resubmission-review-v1"  - REVIEW_RUN_ID: "memory-a1-workflow-memory-design-final-review-v1"  - REVIEW_RUN_ID: "memory-a1-post-acceptance-fixes-review-v1"  - REVIEW_RUN_ID: "workflow-hardening-a1-final-closure-review-v1"  - REVIEW_RUN_ID: "control-plane-a1-r9-final-closure-review-v1"fixed_systemic_defects:  - "SD-01 summary-only evidence pack"  - "SD-02 ready_for_review treated as closed"  - "SD-03 self-referential failure"open_systemic_defects:  - "SD-04 GPT reply incomplete but executed"  - "SD-05 conversation overload without handoff"  - "SD-06 task boundary authorization loss"next_task:  task_id: "HANDOFF-A1"  authorized: yes  execute_immediately: yes  ask_before_starting: no
END_OF_HANDOFF
