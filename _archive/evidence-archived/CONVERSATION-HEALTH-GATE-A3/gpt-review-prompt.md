请对 CONVERSATION-HEALTH-GATE-A3 R1 证据包进行正式审查。

## 任务概要
CONVERSATION-HEALTH-GATE-A3: Pre-Commit Advisory + Registry Reconciliation

## 交付内容

### 1. Pre-Commit Advisory (Layer 4)
- `hooks/pre-commit.governance.ps1` 升级到 v2.4.0，新增 Stage 4 `[4/4] conversation-health advisory`
- Stage 4 是 ADVISORY only — 永远不会 block commit（exit code 仅记录，不影响 overall_result）
- `scripts/pre_commit_health_advisory.py` — 读取 `latest.json`/`current.json`，调用 `check_handoff_v2(mode="advisory")` 产生诊断输出
- fail-graceful: 内部错误时 exit 0（advisory 不 block）

### 2. Registry Reconciliation
- `scripts/reconcile_conversation_registry.py` — 交叉检查 conversation-health 状态与 CONVERSATION_BINDING.json
- 5 种检查: data_availability, conversation_id_match, degraded_health_with_active_binding, one_agent_one_conversation policy, capture_policy enforcement
- advisory only — 不修改文件，仅报告不一致

### 3. Schema + 文档更新
- `schemas/agent-runtime/evidence-capture.schema.json`: maxItems 4→5, 新增 `conversation-health` 到 stage name enum
- `docs/agent-runtime/hook-failure-semantics.md`: 新增 conversation-health advisory 说明, 版本历史 v2.4.0
- `tests/test_hook_failure_semantics.py`: 更新断言匹配 v2.4.0

### 4. 测试
- 35 新测试 (20 advisory + 15 reconciliation)
- 全量回归: 1163 passed, 0 failed, 21 warnings (A1: 1098 + A2: 30 + A3: 35)
- A1/A2 non-regression 测试: manual_estimate 仍 cap at SUGGEST, auth_required 仍 HUMAN_REQUIRED

## 关键设计决策
1. Advisory 语义: Layer 4 不是主 enforcement point（Layer 1-3 是），advisory 仅提供 commit-time 额外信号
2. metrics dict 传入 check_handoff_v2(): 复用 A1 decision engine 完全相同的阈值逻辑
3. Hook v2.4.0 的 overall_result 逻辑不变: 仅 sadp-audit 和 ai-guard 能 BLOCK
4. Registry reconciliation 是 read-only: 不修改任何输入文件

## 证据包
- ZIP: EVIDENCE_PACK_CONVERSATION_HEALTH_GATE_A3.zip
- Files: 29
- SHA-256: 5e078fe506af3b77cda9e412d936af337c1655d89cea7bc71de892b62b685340
- modified_tracked: 0
- Commit: c5adb084

## Commit Chain
fbb08f0 (A1 ACCEPTED) → 593d78f → 9336d56 → be0491f (A2 ACCEPTED) → d9faf05 (A2 verdict) → c5adb08 (A3 R1)

请逐项审查并给出 verdict: ACCEPTED 或 NEEDS_REVISION (附具体 blocker)。

END_OF_SUBMISSION
