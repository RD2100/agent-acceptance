YAML
overall_judgment: accepted

recommendation: |
  这个方案合理，而且应该尽快做。当前“每次从零生成 HANDOFF.md”的模式已经暴露出明显上限：长对话越长，GPT 越难完整复述项目历史；同一批架构、规则、安全边界被反复生成，既浪费上下文，也容易产生遗漏、改写和状态漂移。
  
  建议采用“三文件分工”：
  1. README.md 面向普通用户，说明项目是什么、怎么运行、怎么快速开始。
  2. PROJECT_HISTORY.md 面向 agent 和 GPT，作为长期维护的项目蓝本，记录架构、阶段历史、规则、缺陷、教训、当前状态和下一步任务。
  3. HANDOFF.md 只作为跨对话快照，不再手工从零生成，而是从 PROJECT_HISTORY.md 提取当前必要内容生成。
  
  但需要补充一条关键原则：PROJECT_HISTORY.md 是“项目上下文真相源”，不是“验收真相源”。真正的 accepted / closed 仍然必须以 evidence pack、GPT_REVIEW_RESULT、WORKFLOW_AUDIT_LEDGER 和 hash 绑定为准。PROJECT_HISTORY.md 不能替代 evidence，也不能替代 GPT accepted。

project_history_structure: |
  建议采用“稳定蓝本 + 追加日志 + 当前索引”的混合结构，而不是完全散乱的纯追加式。
  
  推荐结构如下：

  1. 文件头部元信息
     - 文档名称
     - 当前版本
     - 最近更新时间
     - 当前推荐任务
     - 当前开放缺陷数量
     - END_OF_PROJECT_HISTORY 标记要求

  2. 项目身份与三层架构
     - agent-acceptance：合约与审查规范层
     - devframe-control-plane：编排与执行控制层
     - dev-frame-opencode：执行层
     - 各层允许事项与禁止事项

  3. 不变量与硬规则
     - Evidence-First
     - closed = GPT accepted + ledger binding
     - ready_for_review ≠ closed
     - tests passed ≠ accepted
     - commit/push ≠ closed
     - validator fail-closed
     - memory is not evidence
     - GPT 审查不可跳过
     - END_OF_GPT_RESPONSE / END_OF_HANDOFF 强制

  4. 当前状态索引
     - 当前 accepted 的最后任务
     - 当前 unverified / blocked 的任务
     - 当前推荐下一步
     - 当前仓库状态摘要
     - 当前最高优先级缺陷

  5. 任务注册表
     每个任务一条记录：
     - task_id
     - task_name
     - REVIEW_RUN_ID
     - judgment: accepted | blocked | review_unverified | unverified
     - status: closed | ready_for_review | blocked | open
     - evidence_pack_path
     - evidence_pack_sha256
     - git_tree_sha
     - 关键产物
     - 后续影响

  6. SD 缺陷注册表
     每个系统性缺陷一条记录：
     - SD 编号
     - 缺陷名称
     - 严重程度
     - 发现来源
     - 当前状态
     - 修复任务
     - GPT 审查结果
     - 是否已进入 validator/gate

  7. 已部署 validator / gate / checker 注册表
     - validate_workflow_closure.py
     - check_submission_bypass.py
     - pre-push step 2.5
     - devframe pack validate
     - memory compiler / lint
     - paper privacy schema/tests
     - 待新增 validate_gpt_review_gate.py

  8. 论文功能专章
     - PAPER-A1
     - REF-PAPER-1 / 2B
     - PAPER-MEMORY-C1
     - PAPER-A2
     - 当前能力边界
     - 真实论文处理禁令
     - 后续 PAPER-A3 / PAPER-B1 的条件

  9. 对话与 handoff 规则
     - 60 条 assistant message 触发 handoff
     - 响应超过 60 秒触发 handoff
     - 同一任务审查超过 3 轮触发 handoff
     - HANDOFF.md 必须含 END_OF_HANDOFF
     - GPT 回复必须含 END_OF_GPT_RESPONSE

  10. 追加式事件日志
      每次任务完成后追加一条，不删除旧记录：
      - 日期
      - task_id
      - REVIEW_RUN_ID
      - judgment
      - 关键变更
      - evidence pack
      - 测试结果
      - 新增缺陷或修复缺陷
      - next_task_authorization

  11. 最近一次 handoff 快照生成记录
      - 生成时间
      - 来源 PROJECT_HISTORY.md commit
      - 生成的 HANDOFF.md sha256
      - 使用的提取规则

  12. END_OF_PROJECT_HISTORY

handoff_vs_blueprint_relationship: |
  PROJECT_HISTORY.md 应该是长期蓝本，HANDOFF.md 应该是从蓝本中提取出来的跨对话工作快照。
  
  新 agent 理想情况下只需要读 HANDOFF.md 就能继续工作。HANDOFF.md 必须包含当前任务所需的最小完整上下文：项目身份、三层架构、当前状态、开放缺陷、安全边界、执行规则、下一步任务、bootstrap prompt 和 END_OF_HANDOFF。
  
  但是，如果新 agent 要做历史审计、追溯某个 REVIEW_RUN_ID、检查某个旧阶段为什么 accepted，或者修复跨阶段缺陷，就应该读取 PROJECT_HISTORY.md。也就是说：
  
  - HANDOFF.md = 当前对话启动包，面向“马上接着干”
  - PROJECT_HISTORY.md = 项目长期蓝本，面向“完整追溯和持续维护”
  - README.md = 用户说明书，面向“项目是什么、怎么用”
  
  HANDOFF.md 不应包含蓝本全部内容，否则又会回到 15,000+ 字符重复生成的问题。它应该包含：
  1. 固定不变量摘要
  2. 当前状态
  3. 最近已 accepted 任务
  4. 当前开放缺陷
  5. 下一任务 TaskSpec 摘要
  6. 安全边界
  7. 新对话 bootstrap prompt
  8. END_OF_HANDOFF
  
  PROJECT_HISTORY.md 才保存完整历史。

existing_handoff_handling: |
  现有 HANDOFF.md 不应丢弃，也不应继续作为每次覆盖的主文件。建议把它作为 PROJECT_HISTORY.md 的初始蓝本导入。
  
  具体做法：
  1. 新建 PROJECT_HISTORY.md。
  2. 将现有 HANDOFF.md 内容整理为 PROJECT_HISTORY.md 的 baseline section。
  3. 在文件头标注：
     “本文件初始版本由 HANDOFF.md 导入，后续以追加与索引更新方式维护。”
  4. 保留原 HANDOFF.md 作为历史快照，例如 archive/handoffs/HANDOFF_2026-06-06_initial.md。
  5. 后续 HANDOFF.md 不再手写维护，而由脚本或固定模板从 PROJECT_HISTORY.md 生成。
  6. 每次任务 GPT accepted 后，必须追加 PROJECT_HISTORY.md，而不是等到换对话时再让 GPT 从记忆中重写。

具体修复方案: |
  建议新增一个任务：HISTORY-A1。
  
  task_id: HISTORY-A1
  task_name: 项目活蓝本与 handoff 生成机制
  目标:
    - 建立 PROJECT_HISTORY.md 作为长期蓝本
    - 将现有 HANDOFF.md 导入为初始 baseline
    - 定义 README.md / PROJECT_HISTORY.md / HANDOFF.md 三者分工
    - 新增 handoff 生成规则
    - 新增 PROJECT_HISTORY.md 追加规则
    - 新增 validate_project_history.py 和 validate_handoff.py
    - 防止 HANDOFF.md 每次从零生成
  
  必须实现:
    - PROJECT_HISTORY.md 含 END_OF_PROJECT_HISTORY
    - HANDOFF.md 含 END_OF_HANDOFF
    - PROJECT_HISTORY.md 不得记录真实论文内容
    - PROJECT_HISTORY.md 不得替代 evidence pack
    - accepted 任务追加时必须带 REVIEW_RUN_ID
    - closed 任务必须带 GPT accepted 依据
    - unverified commit 必须明确标为 unverified
    - 生成 HANDOFF.md 时必须从 PROJECT_HISTORY.md 提取，而不是从 GPT 记忆重写
  
  建议新增文件:
    - PROJECT_HISTORY.md
    - docs/handoff-generation-policy.md
    - scripts/generate_handoff_from_history.py
    - scripts/validate_project_history.py
    - scripts/validate_handoff.py
    - tests/test_project_history_structure.py
    - tests/test_handoff_generation.py
  
  验收标准:
    - 现有 HANDOFF.md 已导入 PROJECT_HISTORY.md
    - HANDOFF.md 可以从 PROJECT_HISTORY.md 生成
    - HANDOFF.md 不需要包含全部历史，只包含当前继续执行所需上下文
    - PROJECT_HISTORY.md 包含所有 accepted task 的 REVIEW_RUN_ID
    - PROJECT_HISTORY.md 区分 accepted / blocked / unverified
    - 缺 END_OF_PROJECT_HISTORY 时 fail
    - 缺 END_OF_HANDOFF 时 fail
    - pytest 通过
    - bypass check 通过
    - evidence pack 包含实际生成的 PROJECT_HISTORY.md 和 HANDOFF.md

最关键的一点是：PROJECT_HISTORY.md 可以成为“上下文蓝本”，但不能成为“验收凭证”。验收仍然必须回到 evidence pack、GPT_REVIEW_RESULT、WORKFLOW_AUDIT_LEDGER、hash 和 validator。这样既能解决长对话 handoff 反复重写的问题，也不会破坏 Evidence-First 原则。