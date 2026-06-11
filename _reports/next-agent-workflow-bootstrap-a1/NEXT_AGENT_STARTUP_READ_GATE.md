# Next Agent Startup Read Gate

> task_id: NEXT-AGENT-WORKFLOW-BOOTSTRAP-IMPLEMENT-A1
> run_id: NEXT_AGENT_WORKFLOW_BOOTSTRAP_IMPLEMENT_A1_20260608_235642
> status: active bootstrap guidance
> purpose: 让下一个接手智能体直接读取仓库内完整流程，而不是依赖会话上下文或重新造流程。

## 必须先执行

```bash
cd "D:/agent-acceptance" && pwd && date && echo FRESH_SHELL_OK && git rev-parse --is-inside-work-tree
```

当前 harness 可能在每条 Bash 后重置 cwd；所有 Bash 命令必须显式以 `cd "D:/agent-acceptance" &&` 开头。

## 启动硬门槛

下一个 agent 在复述项目流程、判断状态、执行非平凡任务前，必须读取 `NEXT_AGENT_REQUIRED_READS.json` 中所有 `must_read_at_startup=true` 的文件，并填写 `STARTUP_READ_PROOF_TEMPLATE.json` 等价内容。

不得只根据：

- 用户粘贴的上下文；
- memory / compiled memory；
- 上一轮 agent 的自然语言总结；
- root `GPT_*.txt`；
- legacy `PROJECT_HISTORY*` / `HANDOFF*` / paste block；

来宣布项目状态、verdict、测试数量或 closure 状态。

## 必须复用的现有流程

- `HANDOFF_SOURCE_OF_TRUTH.md`：权威层级。
- `_reports/handoff-pipeline-refactor-a1/ATTACHMENT_BACKED_GPT_REVIEW_RUNBOOK.md`：附件版 GPT 审查流程。
- `scripts/verify_gpt_reply.py`：GPT 回复 verifier。
- `scripts/evidence_pack_linter.py` 与 `scripts/pre_gpt_review_gate.py`：提交前 gate。
- `_reports/global-project-handoff-repair-a1/*`：whole-project 修复层 P0/P1 证据。
- `_reports/global-project-evidence-binding-a1/*`：当前 blocked verdict 与 R2 输入。

## 语义保护

- `accepted_with_limitation` 不能写成 `accepted`。
- `blocked` 不能写成 success。
- `partial / needs_more_evidence` 不能写成 closed。
- `296 PASS` 不能写成 verified。
- production promotion 不能写成 approved。

## 当前 R2 前置事实

`GLOBAL-PROJECT-EVIDENCE-BINDING-A1` 当前 GPT verdict 是 `blocked`。R2 必须处理：

1. `HANDOFF_REPLY_V4.txt` deletion/scope conflict；
2. `SAFETY_ATTESTATION` 与 git evidence 冲突；
3. `SOURCE_MAP_EVIDENCE_BINDING_APPENDIX` 旧 ZIP 嵌入/manifest 不一致。

涉及恢复、checkout、删除、移动 legacy 文件时，必须 human_required。

## ready_for_gpt_review 规则

非平凡任务生成 pack 后，不应停在本地汇报；必须继续提交网页版 GPT 审查，确认附件可见、点击提交按钮、确认 user bubble/assistant response、捕获 run_id verdict，并运行 `scripts/verify_gpt_reply.py`。
