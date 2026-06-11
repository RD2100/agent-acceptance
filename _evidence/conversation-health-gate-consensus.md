# CONVERSATION-HEALTH-GATE 决策记录

> 来源: 3 轮 GPT 讨论 (2026-06-11)
> 对话: https://chatgpt.com/c/6a2a8cb1-b228-83aa-addb-79bda9aba043
> 状态: CONSENSUS REACHED
> 后续: CONVERSATION-HEALTH-GATE-A1 TaskSpec

---

## 1. 问题诊断

项目中已存在 `scripts/check_handoff_needed.py`，定义了 4 个强制切换阈值：

- `assistant_message_count >= 60` → force handoff
- `response_time_seconds >= 60` → force handoff
- `review_round_count >= 3` → force handoff
- `last_gpt_reply_bytes < 2000` → force handoff

**核心问题**: 这些阈值从未被主动执行。没有任何 hook、gate 或 workflow 步骤调用该脚本。

**实际案例**: V3 阶段旧对话 `6a297f76` 返回"你无权访问此对话"，agent 直接在侧边栏找到新对话 `6a2a8cb1` 继续工作，完全跳过了阈值检查和对话注册表更新。

**根因**: 知识存在于项目中但没有执行入口 — agent 的被动模式导致它不会主动阅读 `scripts/` 目录寻找有用工具。

---

## 2. 解决方案: 四层防御

### Layer 1: Pre-Task Hard Gate (C)

- `sadp_pre_task_enforcer.py` 集成 conversation health check
- `FORCE_HANDOFF` → **BLOCKED** (任务不得启动)
- 只读 `.ai/conversation/current.json`，**不发起 CDP 操作**
- `current.json missing` → WARNING / INIT_REQUIRED (不 BLOCKED)
- `current.json stale` → SUGGEST_HANDOFF

### Layer 2: Pre-GPT Gate (B')

- `scripts/pre_gpt_gate.py` 模块化 gate
- 过渡方案: 现有脚本开头 `from scripts.pre_gpt_gate import check_pre_gpt_gate`
- 目标架构: 统一 `submit_gpt_review.py` wrapper
- `current.json missing` 且无法刷新 → **BLOCKED**
- `current.json missing` 但 wrapper 可初始化 → 写入 evidence 后允许继续
- Submit wrapper 负责实时 CDP 指标采集和 `current.json` 更新

### Layer 3: Evidence Pack Hard Requirement

- `build_evidence_pack.py` 强制包含 `_evidence/conversation-health/latest.json`
- 缺失 → evidence incomplete → reviewer **不得 ACCEPTED**
- `FORCE_HANDOFF` 但无 handoff/migration record → **rejected**
- `review.yaml` 新增 `conversation_health` 字段:
  ```yaml
  conversation_health:
    checked: true
    decision: OK | FORCE_HANDOFF | SUGGEST_HANDOFF | UNKNOWN | HUMAN_REQUIRED
    action_taken: continued | handoff_generated | migration_record_created | blocked
    justification: ...
    latest_file: _evidence/conversation-health/latest.json
    checked_at: "2026-06-11T10:30:00Z"
  ```

### Layer 4: Pre-Commit Advisory (A)

- `pre-commit.governance.ps1` 新增 `conversation-health` ADVISORY stage
- 只做审计提醒，**不作为主门禁**
- 检查: missing health evidence → WARNING, stale metrics → WARNING

---

## 3. 阈值分级 (Policy-Driven)

阈值不硬编码，存放在 `configs/conversation-health-policy.yaml`。

### Force Handoff

| 条件 | 备注 |
|------|------|
| `assistant_message_count >= 60` | 仅当 `metrics_source` 为 `cdp_dom_count` 或 `wrapper_counter` |
| `review_round_count >= 3` | |
| `last_nav_result` in `[access_denied, not_found]` | passive recording |

### Suggest Handoff

| 条件 | 备注 |
|------|------|
| `assistant_message_count >= 45` | |
| `response_time_seconds >= 60` | |
| `last_gpt_reply_bytes < 2000` | 单次短回复不强制 |
| `metrics_stale_hours >= 12` | |
| `assistant_message_count >= 60` + `metrics_source=manual_estimate` | 低可信度不触发 FORCE |

### Composite Force

同时满足以下条件:
- `response_time_seconds >= 60`
- `last_gpt_reply_bytes < 2000`
- `review_round_count >= 2`
- `metrics_source` 不是 `manual_estimate`

### Human Required

| 条件 | 备注 |
|------|------|
| `last_nav_result == auth_required` | 认证异常，非对话过长 |

### last_nav_result 枚举

| 值 | 处理 |
|----|------|
| `ok` | 正常 |
| `access_denied` | FORCE_HANDOFF |
| `not_found` | FORCE_HANDOFF |
| `timeout` | SUGGEST_HANDOFF / RETRY_REQUIRED |
| `auth_required` | HUMAN_REQUIRED |
| `cdp_unavailable` | SUGGEST_HANDOFF |
| `unknown` | WARNING |

---

## 4. 数据源

### .ai/conversation/current.json

统一 metrics source of truth:

```json
{
  "schema_version": "conversation-health.v1",
  "conversation_id": "6a2a8cb1",
  "chat_url": "https://chatgpt.com/c/6a2a8cb1-...",
  "status": "active",
  "last_known_metrics": {
    "assistant_message_count": 42,
    "review_round_count": 2,
    "last_response_time_seconds": 38.4,
    "last_gpt_reply_bytes": 5812
  },
  "last_nav_result": "ok",
  "last_health_decision": "OK",
  "last_health_reasons": [],
  "last_checked_at": "2026-06-11T10:30:00Z",
  "metrics_source": "cdp_dom_count",
  "metrics_freshness": "fresh"
}
```

### metrics_source 可信度

| 来源 | 可信度 | 可否触发 FORCE |
|------|--------|----------------|
| `cdp_dom_count` | 最高 | 是 |
| `wrapper_counter` | 中等 | 是 |
| `manual_estimate` | 低 | 否 (仅 SUGGEST) |

### 关键规则

- **Pre-Task must not open CDP browser.** 只读 last known state.
- **Pre-GPT/CDP wrapper** 负责实时 CDP 指标采集和 `current.json` 更新.
- **chat_url 可达性** 通过 submit/capture 被动记录，不在 Pre-Task 主动验证.

---

## 5. Migration Record

对话切换时必须生成:

```yaml
schema_version: conversation-migration.v1
task_id: TASK-ID

old_conversation:
  conversation_id: 6a297f76
  chat_url: https://chatgpt.com/c/6a297f76-...
  previous_status: active
  failure_reason: access_denied
  detected_at: "2026-06-11T10:20:00Z"
  detected_by: pre_gpt_gate

new_conversation:
  conversation_id: 6a2a8cb1
  chat_url: https://chatgpt.com/c/6a2a8cb1-...
  new_status: active

migration:
  migration_time: "2026-06-11T10:25:00Z"
  migration_reason: old_chat_inaccessible
  context_transferred:
    - V1-V5 review history
    - latest verdict
    - open blockers
    - current task state
  handoff_generated: false
  handoff_not_generated_reason: "context preserved in working evidence, same task round"
  operator: agent

registry_update:
  old_marked_as: migrated
  new_marked_as: active
  updated_registry_path: .ai/conversation/current.json

evidence:
  source_error_file: _evidence/conversation-health/nav-error-20260611T102000.txt
  health_decision_file: _evidence/conversation-health/latest.json
```

存放位置: `_evidence/conversation-health/migration-records/{timestamp}.yaml`

**规则**:
- `handoff_generated: false` 允许，但**必须有解释**
- `FORCE_HANDOFF` due to length/round threshold → handoff 应该生成
- migration record 不能成为逃避 handoff 的通道

---

## 6. check_handoff_needed.py 升级

### CLI

```bash
python scripts/check_handoff_needed.py \
  --input .ai/conversation/current.json \
  --write _evidence/conversation-health/latest.json \
  --fail-on-force \
  --mode pre-task \
  --max-staleness-hours 12 \
  --composite \
  --json
```

### 输出 Decision

```json
{
  "schema_version": "conversation-health-decision.v1",
  "decision": "FORCE_HANDOFF",
  "severity": "BLOCKING",
  "reasons": [
    {
      "code": "review_round_count_exceeded",
      "actual": 3,
      "threshold": 3,
      "policy": "force"
    }
  ],
  "recommended_action": "generate_handoff",
  "checked_at": "2026-06-11T10:30:00Z",
  "source": ".ai/conversation/current.json"
}
```

### 退出码

| Code | Meaning |
|------|---------|
| 0 | OK / SUGGEST (when `--fail-on-force` is false) |
| 1 | FORCE_HANDOFF (when `--fail-on-force` is true) |
| 2 | Invalid input / schema error |
| 3 | Missing required metrics in strict mode |

---

## 7. 任务拆分

### A1: Data + Decision + Pre-Task + Evidence Pack (最小可接受闭环)

产物:
1. `schemas/agent-runtime/conversation-health.schema.json`
2. `schemas/agent-runtime/conversation-health-decision.schema.json`
3. `configs/conversation-health-policy.yaml`
4. `docs/agent-runtime/conversation-health-gate.md`
5. `.ai/conversation/current.json.example`
6. `scripts/check_handoff_needed.py` (升级)
7. `scripts/sadp_pre_task_enforcer.py` (集成 health check)
8. `scripts/build_evidence_pack.py` (强制包含 health evidence)
9. `tests/test_conversation_health_gate.py`
10. Negative-path runtime evidence (9 scenarios)

A1 可定义 `pre_gpt_gate.py` 接口，但**不迁移 CDP 脚本**。

### A2: Pre-GPT + CDP Metrics Refresh + Legacy Integration

产物:
1. `scripts/pre_gpt_gate.py` (完整实现)
2. `scripts/submit_gpt_review.py` (thin wrapper)
3. 更新 2-3 个高频 `_submit_*.py`
4. Legacy 脚本加 deprecation notice
5. `_evidence/conversation-health/latest.json` 自动写入

### A3: Pre-Commit Advisory + Registry Reconciliation

产物:
1. `hooks/pre-commit.governance.ps1` 新增 conversation-health ADVISORY stage
2. `scripts/reconcile_conversation_registry.py`
3. `docs/agent-runtime/conversation-registry-lifecycle.md`
4. `docs/agent-runtime/startup-read-gate.md` 新增第 7 项

---

## 8. Negative-Path Evidence (A1 验收必须)

| # | 场景 | 期望 |
|---|------|------|
| 1 | `current.json` missing → WARNING / INIT_REQUIRED | decision != FORCE |
| 2 | `current.json` stale (>12h) → SUGGEST_HANDOFF | decision == SUGGEST |
| 3 | `assistant_message_count=60` + `cdp_dom_count` → FORCE_HANDOFF | decision == FORCE |
| 4 | `review_round_count=3` → FORCE_HANDOFF | decision == FORCE |
| 5 | `last_nav_result=access_denied` → FORCE_HANDOFF | decision == FORCE |
| 6 | `last_nav_result=auth_required` → HUMAN_REQUIRED | decision == HUMAN_REQUIRED |
| 7 | Invalid `current.json` → validator error | exit != 0 |
| 8 | Evidence pack missing `conversation-health/latest.json` → incomplete | evidence check fails |
| 9 | FORCE_HANDOFF but no handoff/migration → rejected | pre-task BLOCKED |
