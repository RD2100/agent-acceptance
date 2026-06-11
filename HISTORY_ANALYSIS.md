以下是建议并入当前 PROJECT_HISTORY.md 的精简版要点。我会只提取“有长期价值、当前蓝本可能缺失或需要校正”的信息，不重复已有论文功能细节。

一、建议合并的历史阶段

需要补入一个章节，建议标题为：

Markdown
## 历史主线补充：S3 / B2-B3 / Guarded Steady State 旧工作流

应合并这些阶段：

YAML
old_phases_to_merge:
  S2_human_required解除:
    status: accepted
    value: "确立了 forbidden scope、human attestation、不可凭 agent claim 解除阻塞的规则。"

  Framework_Freeze:
    status: completed
    value: "固化 Oracle GPT Review 自动化框架，暴露出 agent 只输出终端报告、不自动打包提交 GPT 的早期问题。"

  Reliability_Fix_v1:
    status: accepted
    value: "建立三层状态语义、flow state、decision dispatcher、ACK、URL fail-closed、断点恢复。"

  Post_Decision_Driver_Fix:
    status: accepted
    value: "修复 GPT accepted 后只写 ready_to_dispatch 但不继续调度的问题。"

  S3_Phase_1:
    status: accepted
    value: "发现 @go dispatch / fallback 路径不读取 FLOW_OUTCOME.json，要求进入 Oracle gate。"

  AA_1_Flow_Contract:
    status: accepted
    value: "agent-acceptance 定义 FLOW_OUTCOME、TASKSPEC、DISPATCH_RESULT 等合同与 terminal/dispatcher policy。"

  S3_Phase_2_Oracle_Gate:
    status: accepted
    value: "dev-frame-opencode 接入 agent-acceptance contracts，实现 oracle_gate，schema missing 从 fail-open 修为 fail-closed。"

  AA_2_Runner_Contract:
    status: accepted
    value: "定义 RUNNER_CONTRACT、RUNNER_STATE、RUNNER_STEP_RESULT 与 runner policies。"

  S3_Phase_3:
    status: historical_with_correction_needed
    value: "旧文档记录 v3 partial / v4 待修；当前项目若已有 v10 accepted，应在蓝本中注明：旧文档状态已过时，仅保留为历史 failure lineage。"

这些阶段说明了项目早期从“能不能提交 GPT”逐步演进到“自动读取 GPT decision 并继续执行 TaskSpec”的过程；这个目标和三层状态语义是当前 G0-H6 / paper pipeline / GPT review gate 的底层来源。旧文档明确要求区分 transport_status、business_decision、dispatch_status，并禁止把 transport success 当 business accepted。

PROJECT_HISTORY_DevFrame_OpenCo…

二、需要合并的阻塞项与未解决问题

建议合并为一个“Historical Blockers Registry”，不要全部展开细节，只保留可复用风险：

YAML
historical_blockers_to_merge:
  S3_Phase_3_v1:
    issue: "review pack 缺源码、测试源码、SOURCE_DIFF.patch，无法独立复核。"
    lesson: "execution pack 必须 non-summary-only。"

  S3_Phase_3_v2:
    issue: "TEST_OUTPUT 声称全绿，但实际 1 failed；RUNNER_STEP_RESULT 中 business_decision / dispatch_status 为 null。"
    lesson: "测试摘要必须与真实输出一致；schema 字段不得用 null 逃避。"

  S3_Phase_3_v3:
    issue: "RUNNER_STATE.json 不符合 RUNNER_STATE.schema.json；RUNNER_STATE_AFTER.json 实际是 step result；CONTRACT_VALIDATION 假 PASS。"
    lesson: "状态文件类型必须一致；contract validation 必须来自真实 schema 校验。"

  B2_Multi_Agent_Chain_Replay:
    issue: "早期 blocked，原因包括 RID match、route_decision_match、完整 chain tests、统计口径不一致。"
    final_status_in_doc: "后续追加区显示 B2 diagnostic replay accepted，但不解封 broader real-chain。"
    lesson: "diagnostic replay accepted 不等于 production-grade real chain accepted。"

  B3_Bounded_Real_Chain:
    issue: "B3 Round 1 closure accepted as chain demonstrated，但 captured verdict 仍 blocked；b3_execution_accepted=false。"
    lesson: "链路跑通不等于业务 verdict accepted。"

  Production_Promotion:
    issue: "C2 Broader Real-Chain Testing 与 C8 Open Gap Threshold 仍未满足。"
    status: "production_promotion_approved=false。"

  Guard_Removal_Evidence_Cleanup:
    issue: "guard removal、evidence cleanup、hardcoded driver replacement 均保持 blocked。"
    status: "不得因任一 readiness / score / pilot accepted 而自动解封。"

旧文档对 S3 v3 的阻塞描述特别值得保存：RUNNER_STATE_AFTER.json 不是 runner state、CONTRACT_VALIDATION.md 声称通过但真实校验失败、SOURCE_DIFF.patch 为空。这个应并入当前“stale validation / fake green”教训库。

PROJECT_HISTORY_DevFrame_OpenCo…

B2/B3 部分也要合并，但要写清边界：B2 后来作为 diagnostic replay accepted，但不解封 broader real-chain；B3 Round 1 证明 CDP submit→capture→parse→route→ledger 链路，但 captured verdict 仍 blocked，不能写成 b3_execution_accepted=true。

PROJECT_HISTORY_DevFrame_OpenCo…

 

PROJECT_HISTORY_DevFrame_OpenCo…

三、值得保留的关键教训

建议并入当前 Lessons Learned 或 Systemic Defects：

YAML
lessons_to_preserve:
  evidence_first:
    - "不能凭 agent summary 判定 accepted。"
    - "必须检查 evidence pack、日志、测试输出、schema 校验、diff、manifest。"
    - "agent 声明与证据冲突时，相信 evidence。"

  state_semantics:
    - "transport success ≠ business accepted。"
    - "ready_to_dispatch ≠ dispatched。"
    - "TaskSpec generated ≠ TaskSpec executed。"
    - "Markdown report ≠ machine-readable authority。"

  schema_fail_closed:
    - "schema missing / invalid 必须 fail-closed。"
    - "null 字段不能伪装成合法状态。"
    - "状态文件必须匹配对应 schema，不得把 step result 当 runner state。"

  evidence_pack_integrity:
    - "review pack 必须包含源码、测试、diff、manifest、真实 validation 输出。"
    - "TEST_OUTPUT、COMMAND_LOG、PACK_MANIFEST、VALIDATION_RESULT 口径必须一致。"
    - "summary-only pack 必须 blocked。"

  gpt_reply_and_cdp:
    - "CDP 是 ChatGPT 自动提交主通道；computer-use MCP / fallback 不得冒充自动化成功。"
    - "GPT reply 必须完整捕获并匹配 REVIEW_RUN_ID。"
    - "submit 后必须 poll、persist、route、ledger，不得停在文件存在。"

  bounded_real_chain:
    - "bounded pilot accepted 不等于 broader real-chain unblocked。"
    - "diagnostic replay accepted 不等于 production promotion。"
    - "readiness score 是诊断，不是生产批准。"

旧文档本身明确把 Evidence-First 写成项目原则，并强调不能把 transport success 当 business accepted。这个原则应与当前的 GPT review gate、PROJECT_HISTORY 活蓝本、paper workflow 一并保留。

PROJECT_HISTORY_DevFrame_OpenCo…

四、S3 / B3 与当前 G0-H6 pipeline 的关系

建议在当前 PROJECT_HISTORY.md 中这样写：

YAML
relationship_old_s3_b3_to_current_g0_h6:
  summary: "S3 / B3 是 G0-H6 之前的历史验证链路，不是当前 G0-H6 的同名阶段。"
  S3:
    role: "早期 runner / dispatcher / TaskSpec 自动续跑能力的来源。"
    contributed_to_G0_H6:
      - "三层状态语义"
      - "FLOW_OUTCOME / DISPATCH_RESULT / RUNNER_STATE / RUNNER_STEP_RESULT schema 思路"
      - "terminal=false 继续执行"
      - "next_task_spec_path 强制消费"
      - "schema fail-closed"
      - "max_steps / resume semantics"
    merge_policy: "作为 historical lineage 合并，不覆盖当前 G0-H6 状态。"

  B2:
    role: "历史多 pack / 多 agent chain replay，用于检查 route / ledger / RID / decision chain。"
    contributed_to_G0_H6:
      - "route-ledger consistency"
      - "RID exact match"
      - "diagnostic replay 边界"
      - "historical_exception / legacy_warn 分类"
    merge_policy: "可作为 G0-H6 中 replay / audit / route verification 的前身。"

  B3:
    role: "bounded real-chain / CDP submit-capture-parse-route-ledger 试验。"
    contributed_to_G0_H6:
      - "CDP submit -> capture -> parse -> route -> ledger 链路证明"
      - "captured verdict 与 closure accepted 的区分"
      - "broader real-chain 不得自动解封"
    merge_policy: "作为当前 live/CDP/handoff 机制的历史前身；不得写成 production-ready。"

  current_G0_H6:
    role: "当前标准化后的 pipeline / handoff / paper workflow / control-plane 体系。"
    should_absorb:
      - "S3 的 runner/status 语义"
      - "B2 的 replay/audit 语义"
      - "B3 的 CDP/capture/route/ledger 证据要求"
    should_not_absorb:
      - "旧 S3 v3 partial 作为当前状态"
      - "B3 execution accepted=false 被误写为 accepted"
      - "production_promotion 或 broader_real_chain 解封"

一句话：S3 是“自动执行与 runner 状态机”的祖先；B2 是“route/ledger/replay 审计”的祖先；B3 是“真实 CDP 链路验证”的祖先；G0-H6 是把这些历史能力重新整理后的当前标准流程。 旧文档中还明确指出 devframe-control-plane v0.1.0-rc 是伴随控制平面项目，不能自动写成 agent-acceptance 主线 production promotion，这一点也应保留。

PROJECT_HISTORY_DevFrame_OpenCo…

五、建议实际合并到 PROJECT_HISTORY.md 的内容

可以追加一个短章节，不要整篇复制：

Markdown
## Historical Lineage: S3 / B2-B3 / Guarded Steady State

### 要合并的结论
- S2、Framework Freeze、Reliability Fix、Post-Decision Driver、S3 Phase 1、AA-1、S3 Phase 2、AA-2 是当前 workflow/gate/schema 思想的历史来源。
- S3 Phase 3 旧记录中存在 v1-v3 partial 与 v4 修复要求；若当前项目已有后续 accepted 记录，应标记旧状态为 historical stale，不作为当前状态。
- B2 diagnostic replay 后续 accepted，但不解封 broader real-chain。
- B3 Round 1 closure accepted as chain demonstrated，但 captured verdict blocked，b3_execution_accepted=false。
- Tasks 1-10 accepted、submission guard 标准目标 10/10 guarded、P3 guard merge 有功能完成迹象，但 formal closure 曾 blocked，不得包装成 production promotion。
- 当前旧线阻塞仍包括 C2 Broader Real-Chain Testing、C8 Open Gap Threshold、production promotion、guard removal、evidence cleanup。

### 要合并的教训
- Evidence-First。
- transport success ≠ business accepted。
- ready_to_dispatch ≠ dispatched。
- TaskSpec generated ≠ TaskSpec executed。
- schema/validator 必须 fail-closed。
- GPT reply 必须完整捕获并绑定 REVIEW_RUN_ID。
- readiness score / diagnostic replay / bounded pilot 不能等同 production approval。
六、不建议合并或只放附录的内容
YAML
do_not_merge_as_main_state:
  - "旧文档中 S3 Phase 3 v3 partial / v4 待修的当前状态描述，除非标注 historical stale。"
  - "所有 2026-06-04 阶段的长 REVIEW_RUN_ID 列表，除非做索引表。"
  - "对话 A-F 预留区。"
  - "大量 pack 文件名清单。"
  - "重复的三层架构定义，当前 PROJECT_HISTORY 已有则只补差异。"
  - "任何 production readiness achieved / broader real-chain unblocked 的暗示。"

最应该合并的是“历史阶段索引 + 阻塞项 + 教训 + S3/B2/B3 到 G0-H6 的关系”，而不是把 5000 行全文并入当前蓝本。