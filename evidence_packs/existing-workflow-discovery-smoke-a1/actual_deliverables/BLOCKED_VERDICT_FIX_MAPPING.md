# Blocked Verdict Fix Mapping — GLOBAL-PROJECT-EVIDENCE-BINDING-A1

## 1. HANDOFF_REPLY_V4.txt deletion evidence conflict

- GPT 原始 blocking issue：`changed-files evidence shows tracked deletion of HANDOFF_REPLY_V4.txt, so the pack cannot independently verify that all legacy HANDOFF-related files were not deleted.`
- 对应证据文件：
  - `_reports/global-project-evidence-binding-a1/GPT_REVIEW_RESULT.txt`
  - `_reports/global-project-evidence-binding-a1/VERIFY_GPT_REPLY_OUTPUT.txt`
  - `_reports/global-project-evidence-binding-a1/CHANGED_FILES_EVIDENCE.json`
  - `_reports/global-project-evidence-binding-a1/GIT_STATUS_EVIDENCE.txt`
- 应复用组件：`HANDOFF_SOURCE_OF_TRUTH.md`、`CHANGED_FILES_EVIDENCE.json`、`PROTECTED_LEGACY_FILES_STATUS.json`、`scripts/verify_gpt_reply.py`、pre-GPT gate。
- 最小修复：明确 `HANDOFF_REPLY_V4.txt` 是否属于 protected legacy handoff 范围；若不属于，提供 P0 scope evidence；若属于，需恢复该文件后重新生成 git evidence。
- 高风险需确认：恢复/checkout/移动/删除 legacy 文件；任何 `git checkout`、`git reset`、`git clean`。
- 可自动执行：读取 git evidence、生成 scope appendix、更新 R2 报告/manifest/safety scan、重新打包、GPT 审查。

## 2. SAFETY_ATTESTATION 与 git evidence 冲突

- GPT 原始 blocking issue：`SAFETY_ATTESTATION claims legacy files were not deleted/moved/renamed/rewritten, but git changed-files evidence contains D HANDOFF_REPLY_V4.txt.`
- 对应证据文件：
  - `evidence_packs/global-project-evidence-binding-a1/SAFETY_ATTESTATION.md`
  - `_reports/global-project-evidence-binding-a1/CHANGED_FILES_EVIDENCE.json`
  - `_reports/global-project-evidence-binding-a1/GPT_REVIEW_RESULT.txt`
- 应复用组件：`HANDOFF_SOURCE_OF_TRUTH.md`、`ATTACHMENT_BACKED_GPT_REVIEW_RUNBOOK.md`、`scripts/evidence_pack_linter.py`、`scripts/pre_gpt_review_gate.py`。
- 最小修复：R2 attestation 不能笼统声称所有 legacy 文件未删除；必须改为与 git evidence 一致：核心 tracked protected 文件 clean，`HANDOFF_REPLY_V4.txt` 状态需 scope 判定或 human gate。
- 高风险需确认：为消除冲突而执行任何 destructive git 或 legacy 文件改动。
- 可自动执行：重写 R2 attestation 文案、重新 safety scan、manifest、pack、pre-GPT gate。

## 3. SOURCE_MAP_EVIDENCE_BINDING_APPENDIX 旧 ZIP 嵌入声明不一致

- GPT 原始 blocking issue：`SOURCE_MAP_EVIDENCE_BINDING_APPENDIX claims the prior GLOBAL_PROJECT_HANDOFF_REPAIR_A1 ZIP is embedded in the pack, but the referenced copy_path is not present in the attached ZIP or PACK_MANIFEST.`
- 对应证据文件：
  - `_reports/global-project-evidence-binding-a1/SOURCE_MAP_EVIDENCE_BINDING_APPENDIX.json`
  - `_reports/global-project-evidence-binding-a1/PACK_MANIFEST.md`
  - `evidence_packs/global-project-evidence-binding-a1/GLOBAL-PROJECT-EVIDENCE-BINDING-A1_20260608_233125.zip`
  - `_reports/global-project-evidence-binding-a1/GPT_REVIEW_RESULT.txt`
- 应复用组件：source map appendix 生成逻辑、PACK_MANIFEST、evidence pack linter、pre-GPT gate。
- 最小修复：二选一：要么真的把旧 ZIP 嵌入 R2 pack 并写入 PACK_MANIFEST；要么把 `embedded_in_pack` 改为 false/sha256-only，删除不实 copy_path 声明。
- 高风险需确认：无破坏性文件操作；但若要删除旧错误 pack，应先确认。本轮/R2 可生成新 pack，不删除旧 pack。
- 可自动执行：生成新的 appendix、manifest、zip 内容核验、GPT 审查。
