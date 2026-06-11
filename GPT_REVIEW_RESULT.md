结论：这份 PROJECT_HISTORY.md 目前不建议直接作为 sound 的蓝本使用，需要先修复。 核心问题不是历史蒸馏内容本身，而是合并时出现了明显的结构破坏、重复插入和状态过时。

PROJECT_HISTORY

主要问题
1. 文档结构被破坏

“历史主线补充：S3 / B2-B3 / Guarded Steady State 旧工作流”被插入了多次，而且插在不该出现的位置：一次插在“执行规则”第 8 条后面，一次插在 validator 表格中间，一次插在 bootstrap prompt 的代码块内部，最后又在文末重复一次。文件中也出现了多个 END_OF_PROJECT_HISTORY，其中至少一个出现在文档中部，导致后续内容逻辑上被放在结束标记之后。

这必须修。PROJECT_HISTORY.md 只能有一个历史补充章节，也只能在全文最后有一个 END_OF_PROJECT_HISTORY。

2. 当前状态严重过时

文档开头写“当前阶段：HANDOFF-A1 完成 → 等待 GPT-REVIEW-GATE-A1”，但当前实际已经远远超过这个阶段：PROJECT_HISTORY Blueprint v6、Gaps Closure v4、PAPER-A3 R2、REPO-ROUTING-A1 v4、PAPER-B1、PAPER-B2 R2、PAPER-C1 都已经被接受。当前文档仍把下一步写成 GPT-REVIEW-GATE-A1 / REVIEW-TEMPLATE-V2 / MEMORY-A3 / PAPER-B1，这已经不符合当前项目状态。

建议把当前阶段更新为：

YAML
当前阶段: PAPER-C1 accepted → 准备 PAPER-C2 或按用户选择继续论文功能

并把 GPT-REVIEW-GATE-A1 从“下一步任务”改为“已由 Gaps Closure v4 接受的历史治理能力”，除非仓库中仍未落地。

3. HANDOFF / PROJECT_HISTORY marker 语义混乱

文档中有“HANDOFF.md 必须 >= 8000 bytes 且包含”后面直接插入了 S3 历史补充，导致这一条规则不完整。后面 bootstrap prompt 又说上传 HANDOFF.md “含 END_OF_PROJECT_HISTORY 标记”，这明显错误。正确规则应是：

YAML
PROJECT_HISTORY.md: "必须包含 END_OF_PROJECT_HISTORY"
HANDOFF.md: "必须包含 END_OF_HANDOFF"
GPT_REPLY: "必须包含 END_OF_GPT_RESPONSE"

当前写法会误导新 agent。

4. 已完成任务表缺少最新 accepted 任务

表格只更新到 PAPER-A3，并且仍把 REVIEW-TEMPLATE-V2 作为 open。缺少至少这些后续关键任务：

YAML
missing_accepted_tasks:
  - PROJECT_HISTORY Blueprint v6
  - PROJECT_HISTORY Gaps Closure v4
  - REPO-ROUTING-A1 v4
  - PAPER-B1
  - PAPER-B2 R2
  - PAPER-C1

其中 PAPER-B1、PAPER-B2 R2、PAPER-C1 是论文功能当前路线的关键节点，缺失会导致新 agent 误以为论文功能还停留在 PAPER-A3 之后。当前文档中确实只列到了 PAPER-A3。

PROJECT_HISTORY

5. PAPER-A3 / PAPER-A2 等 REVIEW_RUN_ID 需要校准

文档中 PAPER-A3 的 REVIEW_RUN_ID 写成 paper-a3-r2-web-review，但当前审查链中更准确的口径应是 paper-a3-validator-integration-v1-r2。PAPER-A2 也建议写完整为 paper-a2-io-redaction-protocol-v1-r2-review，避免后续证据包追溯时找不到对应审查。当前表格里的若干 REVIEW_RUN_ID 是简写或旧名。

PROJECT_HISTORY

6. 旧 S3/B2-B3 与 G0-H6 的关系基本方向对，但表述过度简化

“旧阶段仅保留为历史 lineage”这个方向是对的；“S3/B2-B3 奠定 G0-H6 的三层状态语义、Evidence-First、GPT Review Gate 基础”也合理。问题在于文档只写“B2 多轮 blocked | 历史记录”，没有保留关键边界：

YAML
needed_boundary:
  - "B2 diagnostic replay accepted 不等于 broader real-chain unblocked"
  - "B3 Round 1 closure accepted 不等于 b3_execution_accepted"
  - "production_promotion_approved=false"
  - "broader_real_chain_testing_unblocked=false"
  - "guard_removal_approved=false"
  - "evidence_cleanup_approved=false"

这些边界在旧历史文档中很重要，当前合并版过于压缩，容易让人误以为旧线已经完全无风险关闭。

PROJECT_HISTORY_DevFrame_OpenCo…

结构上建议怎么修

建议不要再在现有文本中局部打补丁，而是做一次轻量整理：

YAML
recommended_fix:
  1: "保留文件头和 1-14 主章节，但清除中间重复插入的历史补充段。"
  2: "把 S3/B2-B3 历史补充只保留一次，放在测试状态之后、END_OF_PROJECT_HISTORY 之前。"
  3: "全文只保留一个 END_OF_PROJECT_HISTORY，必须在最后一行。"
  4: "修正 HANDOFF / PROJECT_HISTORY / GPT_REPLY 三种 END marker 语义。"
  5: "更新已完成任务表，补入 REPO-ROUTING-A1、PAPER-B1、PAPER-B2、PAPER-C1。"
  6: "更新当前阶段和下一步，不再写等待 GPT-REVIEW-GATE-A1。"
  7: "将旧 S3/B2-B3 写成 Historical Lineage，不作为当前状态。"
是否缺少关键信息

缺少。最关键缺失是论文功能当前状态和REPO-ROUTING-A1 后的 submission_target 规则。现在文档还没有体现：

YAML
critical_missing:
  - "REPO-ROUTING-A1 v4 accepted：所有 TaskSpec 必须声明 submission_target。"
  - "PAPER-B1 accepted：PAPER-A3 validator 已接入 devframe-control-plane pipeline。"
  - "PAPER-B2 R2 accepted：synthetic-only validator-backed workflow v2 已完成。"
  - "PAPER-C1 accepted：真实论文试运行安全协议已完成，但仍 protocol-only，不允许真实论文执行。"
  - "下一步应是 PAPER-C2 或用户重新指定的论文功能任务，而不是 PAPER-B1。"
最终判断
YAML
overall_judgment: blocked
project_history_sound: no
reason: "内容方向大体正确，但结构损坏、重复插入、END marker 错位、当前状态过时、缺少最新 accepted 任务。"
recommended_action: "先做 PROJECT_HISTORY-CLEANUP-A1，清理结构并更新当前状态，再作为正式蓝本使用。"

一句话概括：这份文档的历史补充内容本身有价值，但合并方式出了问题；现在它不是一个可靠的活蓝本，需要先清理重复段、修正结束标记、更新当前任务状态。