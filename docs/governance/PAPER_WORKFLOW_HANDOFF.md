# 论文功能交接文档

日期：2026-06-09  
范围：仅交接论文功能状态、证据、边界和恢复路径  
当前模式：论文功能开发暂停；允许事实性治理/交接更新；真实论文执行仍然阻断

## 1. 当前结论

论文功能已经具备一套可审计的治理基础，包括合同、I/O 协议、隐私规则、validator、合成 dry-run、C4 局部评审工具、WriteLab 元数据交接边界、产品侧元数据 ZIP exporter、前端 metadata-only 下载入口和可复跑 synthetic E2E 证据链。

但当前不能把它视为“真实论文工作流已开放”。截至 2026-06-09，用户明确要求：先生成论文功能交接文档，暂时不开发论文功能。因此本文件只用于交接，不授权任何真实论文正文处理、live CDP、对外传输、自动 GPT 提交或含论文内容的 memory 写入。

## 2. 治理范围答案

是，以下三项都在目标治理范围内：

| 对象 | 当前治理状态 | 执行状态 |
|------|--------------|----------|
| `devframe-control-plane` | 已纳入外部 runtime 治理范围 | 默认只读/人类门控，不能直接运行 `D:\dev-frame\ai-workflow-hub` |
| `dev-frame-opencode` | 已作为拟议能力和 dispatch 边界纳入治理 | `opencode run` 仍需单独人类授权，不能隐式执行 |
| `paper-workflow` | 已纳入 pilot-only 治理范围 | 只允许 synthetic/sanitized/local 证据设计；真实论文执行仍为 NOGO |

关键解释：纳入治理范围不等于授权执行。治理范围的作用是让能力、边界、证据和人工门控可审计，防止绕过。

## 3. 这段时间论文功能做了什么

已完成或已记录的工作如下，均不得被解释为真实论文执行授权：

| 时间/阶段 | 做了什么 | 证据 |
|-----------|----------|------|
| 参考流水线阶段 | 建立参考论文 review pipeline，并在 `devframe-control-plane` 侧留下 7-stage 设计/执行记录。 | `docs/WORKFLOW_AUDIT_LEDGER.yaml` 中 `REF-PAPER-1`、`REF-PAPER-2B` |
| PAPER-A1 | 建立论文接受模型和 contract 设计。 | `docs/paper-workflow-acceptance.md`、`contracts/paper_acceptance_contracts.yaml` |
| PAPER-A3 / GROUP-02 | 将论文任务 validator 接入治理层，并做 residual backfill；只证明选定文件范围。 | `scripts/validate_paper_task.py`、`tests/test_paper_task_validator.py`、`evidence_packs/paper-a3-r2-closure/`、`evidence_packs/group-02-paper-a3-validator-residual/` |
| PAPER-C1 | 建立真实论文 pilot 安全协议；协议层 accepted，但没有开放真实执行。 | `docs/paper-c1-real-paper-pilot-safety-protocol.md`、`contracts/paper_c1_real_paper_pilot_safety_contract.yaml` |
| PAPER-C2 | 建立 synthetic-only 授权/脱敏 gate，为未来真实 pilot 做准备。 | `contracts/paper_c2_authorization_redaction_gate_contract.yaml`、`tests/test_paper_c2_authorization_redaction_gate.py` |
| PAPER-C3 | 生成 synthetic dry-run packet；auth gate 关闭。 | `evidence_packs/paper-c3-dry-run/DRY_RUN_REPORT.md`、`evidence_packs/paper-c3-dry-run/PILOT_RESULT.json` |
| C4 局部评审 | 增加 bounded section review、packet validator、revision blueprint 等本地工具；仅限 synthetic/sanitized 边界。 | `scripts/paper_c4_section_review.py`、`scripts/paper_c4_section_packet_validator.py`、`scripts/paper_c4_revision_blueprint.py`、`tests/test_paper_c4_section_review.py` |
| 合成 E2E 接管 | 跑通 synthetic/local slice：validator -> C4 review -> blueprint -> preflight -> go/nogo；最终真实 pilot 仍为 NOGO。 | `_reports/paper-controller-takeover-synthetic-e2e-a1/EXECUTION_REPORT.md` |
| WriteLab 合同 | 定义 WriteLab 诊断结果进入论文治理层的 metadata-only/synthetic-only handoff 合同和 validator。 | `contracts/writelab_paper_handoff_contract.yaml`、`scripts/validate_writelab_handoff.py`、`tests/test_writelab_handoff_validator.py`、`_reports/writelab-paper-handoff-contract-a1/EXECUTION_REPORT.md` |
| WriteLab exporter | 在 `D:\writelab` 侧增加 metadata-only ZIP exporter，并用 agent-acceptance validator 验证。 | `_reports/writelab-exporter-a1/EXECUTION_REPORT.md`、`_reports/writelab-exporter-a1/VALIDATION_OUTPUT.json` |
| WriteLab UI 下载入口 | 在 `D:\writelab` 诊断历史中增加 metadata-only 治理交接包下载动作。 | `_reports/writelab-ui-handoff-download-a1/EXECUTION_REPORT.md`、`_reports/writelab-ui-handoff-download-a1/VALIDATION_OUTPUT.json` |
| WriteLab synthetic E2E | 新增可复跑 synthetic 证据链：WriteLab TestClient 创建项目/诊断 -> 下载 metadata-only ZIP -> agent-acceptance validator -> marker scan -> artifact verifier。 | `_reports/writelab-synthetic-e2e-a1/EXECUTION_REPORT.md`、`_reports/writelab-synthetic-e2e-a1/VALIDATION_CLI_OUTPUT.json`、`_reports/writelab-synthetic-e2e-a1/ARTIFACT_VERIFY_OUTPUT.json` |

## 4. 当前可用组件

| 区域 | 当前状态 | 主要路径 |
|------|----------|----------|
| 接受标准 | 已有规范层 | `docs/paper-workflow-acceptance.md`、`contracts/paper_acceptance_contracts.yaml` |
| 任务 I/O | 已有合同 | `docs/paper-task-io-protocol.md`、`contracts/paper_task_io_contract.yaml` |
| 脱敏证据包 | 已有合同 | `contracts/paper_redacted_evidence_pack_contract.yaml` |
| memory 隐私规则 | 已有规则 | `docs/paper-workflow-memory-rules.md` |
| 论文任务 validator | 已有脚本和测试 | `scripts/validate_paper_task.py`、`tests/test_paper_task_validator.py` |
| pilot 门控 | fail-closed 存在 | `scripts/paper_auth_gate.py`、`scripts/paper_pilot_preflight.py`、`scripts/paper_go_nogo.py` |
| C4 section review | bounded/local 存在 | `scripts/paper_c4_section_review.py`、`scripts/paper_c4_section_packet_validator.py` |
| C5/C6/C7 工具 | 本地 utility，未生产化 | `scripts/paper_c5_full_section_reader.py`、`scripts/paper_c6_revision_suggester.py`、`scripts/paper_c7_*` |
| 项目索引/引用辅助 | 本地 utility，需边界审查 | `scripts/paper_project_index.py`、`scripts/paper_citation_workspace.py` |
| WriteLab handoff | 元数据边界、后端 exporter、前端下载入口、synthetic E2E 证据链均已验证 | `contracts/writelab_paper_handoff_contract.yaml`、`scripts/validate_writelab_handoff.py`、`scripts/probe_writelab_handoff_e2e.py`、`D:\writelab\frontend\components\DiagnosisHistoryPanel.tsx` |

## 5. 当前硬边界

禁止：

- 处理真实论文完整正文或未授权摘录。
- 将论文内容传到外部服务或提交给 GPT。
- 对论文内容启用 live CDP、Playwright 自动提交或浏览器会话复用。
- 将论文正文、段落、引用原文、导师意见、私人备注、raw transcript 写入 memory、报告或测试样例。
- 把 synthetic dry-run、sanitized pilot 或 WriteLab metadata exporter 当成真实论文 pilot 通过。
- 把 WriteLab synthetic E2E probe 当成真实论文 pilot 通过。
- 读取或引用 `.ai/paper_authorization.json` 中的 secret/token。

允许但要保持谨慎：

- 阅读规范、合同、validator、测试和 evidence manifest。
- 运行 synthetic-only 或 sanitized-only 的本地验证。
- 更新治理/交接文档，但不得写入论文正文或私有内容。

需要单独人类授权：

- 任何真实论文全文/摘录处理。
- 任何对外传输、GPT 提交、live CDP。
- 任何含论文内容的 memory 写入。
- 将 C5/C6/C7 工具升级为生产工作流。

## 6. 最近验证状态

已有证据：

- `_reports/paper-controller-takeover-synthetic-e2e-a1/EXECUTION_REPORT.md`：synthetic/local slice PASS；`paper_go_nogo.py` 返回 `go=false`，真实 pilot BLOCKED。
- `_reports/writelab-paper-handoff-contract-a1/EXECUTION_REPORT.md`：WriteLab metadata-only handoff validator PASS；真实论文内容 NOGO。
- `_reports/writelab-exporter-a1/EXECUTION_REPORT.md`：WriteLab 后端 metadata-only ZIP exporter PASS；validator、marker scan、paper safety tests 均通过。
- `_reports/writelab-ui-handoff-download-a1/EXECUTION_REPORT.md`：WriteLab 前端 metadata-only 下载入口 PASS；frontend tests、typecheck、build、backend tests、validator、marker scan、paper safety tests 均通过。
- `_reports/writelab-synthetic-e2e-a1/EXECUTION_REPORT.md`：WriteLab synthetic E2E probe PASS；真实 FastAPI route 创建 synthetic project/report、下载 metadata-only ZIP、agent-acceptance validator PASS、marker scan PASS、artifact verifier PASS，临时 SQLite/DB 已删除并有回归测试。
- `docs/governance/VERIFY_MATRIX.md`：记录 paper pause、real execution gate、WriteLab handoff contract/exporter/UI download/synthetic E2E 状态。

建议恢复前先跑的窄验证：

```powershell
python -m pytest tests\test_paper_task_validator.py tests\test_paper_privacy_boundaries.py tests\test_paper_memory_rules.py -q
```

```powershell
python -m pytest tests\test_paper_auth_gate.py tests\test_paper_go_nogo.py tests\test_paper_c4_section_review.py -q
```

```powershell
python scripts\paper_go_nogo.py
```

预期解释：如果没有新的、明确的、当前有效的人类授权，`paper_go_nogo.py` 返回 NOGO 是正确状态，不是失败。

## 7. 已知风险和技术债

| 项 | 等级 | 当前处理 |
|----|------|----------|
| 论文交接被误读成真实执行授权 | P1 | 本文件和 `HANDOFF.md` 明确写为 paused / handoff-only。 |
| C4 dirty baseline | P2 | `scripts/paper_c4_section_packet_validator.py`、`tests/test_paper_c4_section_review.py` 已有未提交改动；没有明确 ownership 前不要叠加实现。 |
| C4 outline parsing | P2 | 当前对单行枚举 outline 可能低估步骤数；见 `_reports/paper-controller-takeover-synthetic-e2e-a1/EXECUTION_REPORT.md`。 |
| C4 sanitized content marker scan | P2 | 需要增强内容级 marker 扫描，但不要在交接文档中写入敏感 marker payload。 |
| C5/C6/C7 utility 生产化 | P2 | 目前只能当本地工具；生产化前必须做安全/隐私/证据审查。 |
| WriteLab live browser smoke | P3 | 后端 exporter 和前端下载入口已实现并测试；本轮未跑 live browser click smoke，因为 Browser/Playwright 工具不可用。 |

## 8. 恢复论文功能时的下一步

若用户之后明确恢复论文功能开发，第一步不要处理真实论文。建议从 synthetic-only E2E 重新开始：

1. 重新确认用户授权范围；如果涉及真实论文，先走独立人类 gate。
2. 使用 synthetic fixture 创建或复用 `PAPER_TASK_INPUT.yaml`。
3. 运行 `scripts/validate_paper_task.py`。
4. 运行 bounded C4 section review。
5. 生成 revision blueprint。
6. 生成 evidence pack 和 privacy attestation。
7. 运行 `scripts/paper_go_nogo.py`。
8. 只有证据支持时，才更新治理日志。

可并行的未来任务池：

| 任务 | 写入边界 | 是否可并行 | 备注 |
|------|----------|------------|------|
| Synthetic E2E rerun | 新 `_reports/` 子目录 | 是 | 不处理真实论文。 |
| C4 validator hardening | 现有 C4 dirty 文件 | 否 | 需要先确认 dirty baseline ownership。 |
| C5/C6/C7 readiness review | 新只读报告目录 | 是 | 先审查，不改生产路径。 |
| WriteLab live browser smoke | `D:\writelab` 前端 | 是 | 工具可用后点击诊断历史下载动作，确认请求 metadata-only ZIP endpoint。 |

## 9. Reviewer Index

交接文档涉及路径：

- `docs/governance/PAPER_WORKFLOW_HANDOFF.md`
- `docs/governance/HANDOFF.md`
- `docs/governance/VERIFY_MATRIX.md`
- `docs/governance/PROGRESS_LOG.md`
- `docs/governance/RISK_REGISTER.md`
- `docs/governance/TECH_DEBT.md`

审查重点：

- 文档是否仍明确 paper development paused。
- 是否有任何真实论文正文、摘录、导师意见、身份信息或 raw transcript 被写入交接文档。
- 是否把 synthetic/sanitized/metadata-only 证据误写成真实论文执行成功。
- 是否把 `devframe-control-plane`、`dev-frame-opencode`、`paper-workflow` 的治理纳入误写成执行授权。
