# Conversation Health Gate -- RD2100 Agent Runtime

> Version: 1.0 | 2026-06-11
> Status: ACTIVE (A1 scope -- Pre-Task + Evidence Pack enforcement)
> Scope: All GPT review conversations, all agents submitting evidence packs
> Derived from: SADP 0.R.2, runtime-invariants.md, pre-task-gate.md, pre-gpt-review-gate.md
> Protection level: SADP protected (docs/agent-runtime/ path, governancePatterns)

---

## 0. Purpose

Every GPT review conversation has a finite useful lifetime. Without proactive health checks, agents continue using degraded or inaccessible conversations, leading to:

- **Silent context loss** when conversations become inaccessible
- **Degraded GPT responses** from context window overflow
- **Missing handoff documentation** when switching conversations

This document defines the four-layer defense model for conversation health enforcement.

**Hard rule**: An agent that cannot prove its conversation is healthy must not proceed with work that depends on that conversation. Missing conversation-health evidence blocks acceptance at review.

---

## 1. Architecture: Four-Layer Defense

### 1.1 Layer 1: Pre-Task Hard Gate

| Field | Detail |
|-------|--------|
| **Location** | `scripts/sadp_pre_task_enforcer.py` pre_task phase |
| **Data source** | Reads ONLY `.ai/conversation/current.json` -- never opens CDP browser |
| **FORCE_HANDOFF** | `BLOCKED` (task cannot start) |
| **Missing/stale metrics** | `WARNING` (does not block task start) |
| **Principle** | Pre-task gate must be lightweight and offline-capable |

The pre-task gate is the first enforcement point. It inspects the last known conversation metrics without performing any network or browser interaction. If the metrics file indicates a force-handoff condition, the task is blocked before any work begins.

### 1.2 Layer 2: Pre-GPT Gate (A2 scope)

| Field | Detail |
|-------|--------|
| **Location** | `scripts/pre_gpt_gate.py` |
| **Data source** | Refreshes runtime metrics via CDP during GPT submission |
| **Outputs** | Writes `current.json` and `latest.json` evidence |
| **Legacy integration** | Legacy scripts import `check_pre_gpt_gate()` during transition |
| **Target architecture** | Unified `scripts/submit_gpt_review.py` wrapper |

The pre-GPT gate performs real-time metrics capture at the moment of GPT submission. This layer provides the most accurate and current conversation health data.

### 1.3 Layer 3: Evidence Pack Hard Requirement

| Field | Detail |
|-------|--------|
| **Location** | `scripts/build_evidence_pack.py` |
| **Requirement** | All evidence packs must include `_evidence/conversation-health/latest.json` |
| **Missing evidence** | Evidence incomplete -- reviewer cannot issue `ACCEPTED` |
| **FORCE_HANDOFF without migration** | Rejected -- no handoff/migration record means no valid conversation transition |

This is the enforcement backstop. Even if Layers 1 and 2 are bypassed or degraded, the evidence pack requirement ensures that no review can be accepted without conversation-health evidence.

### 1.4 Layer 4: Pre-Commit Advisory (A3 scope)

| Field | Detail |
|-------|--------|
| **Location** | `hooks/pre-commit.governance.ps1` |
| **Stage** | Adds `conversation-health` as `ADVISORY` stage |
| **Behavior** | Only audits and warns, not primary enforcement point |

The pre-commit advisory layer provides an additional signal but is not the primary enforcement mechanism. It mirrors the `test-governance` advisory pattern from hook-failure-semantics.md.

---

## 2. Threshold Policy

Thresholds are NOT hardcoded. They live in `configs/conversation-health-policy.yaml`.

### 2.1 Force Handoff (structural risk)

| Condition | Note |
|-----------|------|
| `assistant_message_count >= 60` | Only when `metrics_source` is `cdp_dom_count` or `wrapper_counter` |
| `review_round_count >= 3` | |
| `last_nav_result` in `[access_denied, not_found]` | Passive recording from submit wrapper |

### 2.2 Suggest Handoff (performance/quality risk)

| Condition | Note |
|-----------|------|
| `assistant_message_count >= 45` | |
| `response_time_seconds >= 60` | |
| `last_gpt_reply_bytes < 2000` | Single short reply alone does not force |
| `metrics_stale_hours >= 12` | |
| `assistant_message_count >= 60` with `manual_estimate` | Low credibility source |

### 2.3 Human Required (authentication issue)

| Condition | Note |
|-----------|------|
| `last_nav_result == auth_required` | Not a conversation length issue; requires human intervention |

### 2.4 Composite Force (combined degradation signal)

When multiple soft indicators align, they form a composite force signal:

```
FORCE_HANDOFF if:
    response_time_seconds >= 60
    AND last_gpt_reply_bytes < 2000
    AND review_round_count >= 2
    AND metrics_source != manual_estimate
```

This composite condition detects conversations that are technically accessible but producing degraded output.

---

## 3. Data Source

`.ai/conversation/current.json` is the unified metrics source of truth.

### 3.1 Access Rules

| Layer | Access pattern |
|-------|---------------|
| Pre-Task gate | Reads last known state only (no CDP) |
| Pre-GPT / CDP wrapper | Performs real-time metrics capture |
| Evidence pack | Packages `latest.json` from most recent capture |

### 3.2 Metrics Source Credibility

Source credibility is ranked:

```
cdp_dom_count > wrapper_counter > manual_estimate
```

**Hard constraint**: `manual_estimate` cannot trigger `FORCE_HANDOFF` alone. It can only contribute to `SUGGEST_HANDOFF` or the composite force condition when combined with higher-credibility signals.

### 3.3 Chat URL Accessibility

`chat_url` accessibility is passively recorded through submit failures. The system does not proactively probe conversation URLs -- it records navigation results as they occur during normal GPT submission workflow.

---

## 4. Navigation Result Handling

| Result | Action |
|--------|--------|
| `ok` | Normal operation |
| `access_denied` | `FORCE_HANDOFF` |
| `not_found` | `FORCE_HANDOFF` |
| `timeout` | `SUGGEST_HANDOFF` / `RETRY_REQUIRED` |
| `auth_required` | `HUMAN_REQUIRED` |
| `cdp_unavailable` | `SUGGEST_HANDOFF` |
| `unknown` | `WARNING` |

Navigation results are recorded in `current.json` and flow through the threshold evaluation. An `access_denied` or `not_found` result triggers force handoff regardless of other metrics.

---

## 5. Conversation Migration

When a conversation switch occurs, a migration record is **REQUIRED**.

### 5.1 Migration Record

| Field | Detail |
|-------|--------|
| **Location** | `_evidence/conversation-health/migration-records/{timestamp}.yaml` |
| **Required fields** | `old_conversation`, `new_conversation`, `failure_reason`, `registry_update`, `context_transferred` |
| **handoff_generated: false** | Allowed but must include explanation |
| **Force handoff due to length/round threshold** | Should generate handoff |

### 5.2 Migration Record Format

```yaml
old_conversation:
  chat_url: "https://chatgpt.com/c/..."
  final_metrics:
    assistant_message_count: 62
    review_round_count: 3
new_conversation:
  chat_url: "https://chatgpt.com/c/..."
  started_at: "2026-06-11T10:00:00Z"
failure_reason: "force_handoff: assistant_message_count >= 60"
registry_update:
  updated: true
  registry_file: ".ai/conversation/current.json"
context_transferred:
  summary: "Task X in progress, evidence pack 80% complete"
  files: ["_evidence/TASK-ID/context-summary.md"]
handoff_generated: true
```

---

## 6. Task Scope

| Phase | Scope | Content |
|-------|-------|---------|
| **A1 (current)** | Data + Decision + Pre-Task + Evidence Pack | Threshold policy, current.json schema, pre-task gate integration, evidence pack hard requirement |
| **A2 (future)** | Pre-GPT wrapper + CDP metrics + legacy script integration | Real-time metrics capture, `submit_gpt_review.py` unified wrapper, `check_pre_gpt_gate()` import for legacy scripts |
| **A3 (future)** | Pre-commit advisory + registry reconciliation + startup-read-gate item 7 | Advisory hook stage, conversation registry consistency checks, startup gate integration |

---

## 7. Enforcement Philosophy

The core principle is **Evidence-First**:

- Do not just require agents to run checks.
- Make it impossible to form acceptable evidence WITHOUT the check.
- Reviewer rule: no conversation-health evidence means the reviewer cannot issue `ACCEPTED`.

This transforms passive knowledge (scripts exist but nobody calls them) into active enforcement (missing evidence blocks acceptance).

### 7.1 Comparison: Passive vs. Active Enforcement

| Aspect | Passive (anti-pattern) | Active (this design) |
|--------|----------------------|---------------------|
| Script exists | Yes | Yes |
| Script is called | Hopeful | Required by evidence chain |
| Missing check | Warning at best | Evidence incomplete, BLOCKED |
| Reviewer can accept | Yes (oversight risk) | No (hard gate on evidence) |

### 7.2 Anti-Patterns (DO NOT)

1. **Do not** allow evidence packs to be accepted without conversation-health evidence.
2. **Do not** hardcode thresholds in scripts; all thresholds belong in `configs/conversation-health-policy.yaml`.
3. **Do not** let the pre-task gate open CDP connections; it must remain offline-capable.
4. **Do not** allow `manual_estimate` to trigger force handoff alone; it lacks credibility.
5. **Do not** skip migration records when switching conversations; unrecorded switches create audit gaps.

---

## Version History

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2026-06-11 | Initial document. Defines four-layer defense model, threshold policy, navigation result handling, migration requirements, and task scope (A1). |
