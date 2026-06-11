# GPT Capture Reconciliation Report

**Report ID**: `RECON-20260609-001`  
**Task ID**: `GPT-CAPTURE-RECONCILIATION-HARDEN-A1`  
**Generated At**: `2026-06-09T11:09:01.084737+08:00`  
**Generator**: `scripts/generate_reconciliation_report.py`  
**Hardening Plan Reference**: `HANDOFF_WORKFLOW_HARDENING_PLAN.md section 5.4`

## Summary

| Metric | Count |
|--------|-------|
| Total Submissions | 25 |
| Total Captures | 25 |
| Total Verified | 13 |
| Total Valid Verdicts | 20 |
| Orphan Submissions | 0 |
| Orphan Captures | 0 |
| Unverified Captures | 3 |

## Verdict Distribution

| Verdict | Count |
|---------|-------|
| `accepted_with_limitation` | 13 |
| `(none)` | 5 |
| `blocked` | 4 |
| `review_unverified` | 3 |

## Reconciliation Detail

| # | Task ID | Round | Verdict | Status | END Marker | Next Auth | Verify | Closure |
|---|---------|-------|---------|--------|------------|-----------|--------|---------|
| 1 | `AA-FLOW-CONTRACT-CONTEXT-PACK` | R1 | `(none)` | `pre_standardization` | ✗ | ✗ | — | — |
| 2 | `AA-FLOW-CONTRACT-INTEGRATION` | R1 | `(none)` | `pre_standardization` | ✗ | ✗ | — | — |
| 3 | `AA-RUNNER-CONTRACT-CONTEXT-PACK` | R1 | `(none)` | `pre_standardization` | ✗ | ✗ | — | — |
| 4 | `AA-RUNNER-CONTRACT-INTEGRATION` | R1 | `(none)` | `pre_standardization` | ✗ | ✗ | — | — |
| 5 | `HANDOFF-PIPELINE-REFACTOR-A1` | ATTACHCHAT | `accepted_with_limitation` | `pre_standardization` | ✓ | ✓ | ✓ | — |
| 5 | `HANDOFF-PIPELINE-REFACTOR-A1` | NEWCHAT | `accepted_with_limitation` | `pre_standardization` | ✓ | ✓ | ✓ | — |
| 5 | `HANDOFF-PIPELINE-REFACTOR-A1` | NEWCHAT_INITIAL | `accepted_with_limitation` | `pre_standardization` | ✓ | ✗ | — | — |
| 5 | `HANDOFF-PIPELINE-REFACTOR-A1` | NEWCHAT_VERIFIED | `accepted_with_limitation` | `pre_standardization` | ✓ | ✓ | — | — |
| 5 | `HANDOFF-PIPELINE-REFACTOR-A1` | R1 | `(none)` | `pre_standardization` | ✗ | ✗ | ✗ | — |
| 5 | `HANDOFF-PIPELINE-REFACTOR-A1` | R2 | `review_unverified` | `pre_standardization` | ✓ | ✗ | — | — |
| 5 | `HANDOFF-PIPELINE-REFACTOR-A1` | R3 | `review_unverified` | `pre_standardization` | ✓ | ✗ | — | — |
| 5 | `HANDOFF-PIPELINE-REFACTOR-A1` | R4 | `review_unverified` | `pre_standardization` | ✓ | ✗ | — | — |
| 6 | `GLOBAL-PROJECT-HANDOFF-REPAIR-A1` | R1 | `accepted_with_limitation` | `complete` | ✓ | ✓ | ✓ | — |
| 7 | `GLOBAL-PROJECT-EVIDENCE-BINDING-A1` | R1 | `blocked` | `unverified_capture` | ✓ | ✓ | — | — |
| 8 | `EXISTING-WORKFLOW-DISCOVERY-SMOKE-A1` | R1 | `accepted_with_limitation` | `complete` | ✓ | ✓ | ✓ | — |
| 9 | `NEXT-AGENT-WORKFLOW-BOOTSTRAP-IMPLEMENT-A1` | R1 | `accepted_with_limitation` | `complete` | ✓ | ✓ | ✓ | — |
| 10 | `HANDOFF-WORKFLOW-HARDENING-PLAN-A1` | R1 | `blocked` | `blocked_chain_continuation` | ✓ | ✓ | ✓ | ✗ |
| 10 | `HANDOFF-WORKFLOW-HARDENING-PLAN-A1` | R2 | `accepted_with_limitation` | `complete` | ✓ | ✓ | ✓ | — |
| 11 | `GLOBAL-PROJECT-EVIDENCE-BINDING-A1-R2` | R1 | `blocked` | `unverified_capture` | ✓ | ✓ | — | — |
| 12 | `GLOBAL-PROJECT-EVIDENCE-BINDING-A1-R3` | R1 | `blocked` | `unverified_capture` | ✓ | ✓ | — | — |
| 13 | `GLOBAL-PROJECT-EVIDENCE-BINDING-A1-R4` | R1 | `accepted_with_limitation` | `complete` | ✓ | ✓ | ✓ | — |
| 14 | `HANDOFF-WORKFLOW-HARDENING-PLAN-A1-R2` | R2 | `accepted_with_limitation` | `complete` | ✓ | ✓ | ✓ | ✓ |
| 15 | `PROCESS-STATE-MACHINE-DEFINE-A1` | R1 | `accepted_with_limitation` | `complete` | ✓ | ✓ | ✓ | ✓ |
| 16 | `GPT-REVIEW-SUBMISSION-PARAMETERIZE-A1` | R1 | `accepted_with_limitation` | `verdict_mismatch` | ✓ | ✗ | ✗ | — |
| 16 | `GPT-REVIEW-SUBMISSION-PARAMETERIZE-A1` | R2 | `accepted_with_limitation` | `complete` | ✓ | ✓ | ✓ | ✓ |

## Authorization Chain

```
HANDOFF-PIPELINE-REFACTOR-A1 (ATTACHCHAT, accepted_with_limitation)
  ──→ GENERATE-APPROVED-HANDOFF-A1 [✗ NOT FOUND]

HANDOFF-PIPELINE-REFACTOR-A1 (NEWCHAT, accepted_with_limitation)
  ──→ GENERATE-APPROVED-HANDOFF-A1 [✗ NOT FOUND]

HANDOFF-PIPELINE-REFACTOR-A1 (NEWCHAT_VERIFIED, accepted_with_limitation)
  ──→ GENERATE-APPROVED-HANDOFF-A1 [✗ NOT FOUND]

GLOBAL-PROJECT-HANDOFF-REPAIR-A1 (R1, accepted_with_limitation)
  ──→ GLOBAL-PROJECT-EVIDENCE-BINDING-A1 [✓]

GLOBAL-PROJECT-EVIDENCE-BINDING-A1 (R1, blocked)
  ──→ GLOBAL-PROJECT-EVIDENCE-BINDING-A1-R2 [✓]

EXISTING-WORKFLOW-DISCOVERY-SMOKE-A1 (R1, accepted_with_limitation)
  ──→ GLOBAL-PROJECT-EVIDENCE-BINDING-A1-R2 [✓]

NEXT-AGENT-WORKFLOW-BOOTSTRAP-IMPLEMENT-A1 (R1, accepted_with_limitation)
  ──→ GLOBAL-PROJECT-EVIDENCE-BINDING-A1-R2 [✓]

HANDOFF-WORKFLOW-HARDENING-PLAN-A1 (R1, blocked)
  ──→ HANDOFF-WORKFLOW-HARDENING-PLAN-A1-R2 [✓]

HANDOFF-WORKFLOW-HARDENING-PLAN-A1 (R2, accepted_with_limitation)
  ──→ PROCESS-STATE-MACHINE-DEFINE-A1 [✓]

GLOBAL-PROJECT-EVIDENCE-BINDING-A1-R2 (R1, blocked)
  ──→ GLOBAL-PROJECT-EVIDENCE-BINDING-A1-R3 [✓]

GLOBAL-PROJECT-EVIDENCE-BINDING-A1-R3 (R1, blocked)
  ──→ GLOBAL-PROJECT-EVIDENCE-BINDING-A1-R4 [✓]

HANDOFF-WORKFLOW-HARDENING-PLAN-A1-R2 (R2, accepted_with_limitation)
  ──→ PROCESS-STATE-MACHINE-DEFINE-A1 [✓]

PROCESS-STATE-MACHINE-DEFINE-A1 (R1, accepted_with_limitation)
  ──→ GPT-REVIEW-SUBMISSION-PARAMETERIZE-A1 [✓]

GPT-REVIEW-SUBMISSION-PARAMETERIZE-A1 (R2, accepted_with_limitation)
  ──→ GPT-CAPTURE-RECONCILIATION-HARDEN-A1 [✗ NOT FOUND]

```

## Anomalies

### HIGH (3)

- **GLOBAL-PROJECT-EVIDENCE-BINDING-A1** (R1): [unverified_capture] Capture exists but verify_gpt_reply.py was not run (no VERIFY_GPT_REPLY_OUTPUT file found).
- **GLOBAL-PROJECT-EVIDENCE-BINDING-A1-R2** (R1): [unverified_capture] Capture exists but verify_gpt_reply.py was not run (no VERIFY_GPT_REPLY_OUTPUT file found).
- **GLOBAL-PROJECT-EVIDENCE-BINDING-A1-R3** (R1): [unverified_capture] Capture exists but verify_gpt_reply.py was not run (no VERIFY_GPT_REPLY_OUTPUT file found).

### MEDIUM (9)

- **HANDOFF-PIPELINE-REFACTOR-A1** (ATTACHCHAT): [pre_standardization] Pre-RECORD era: no GPT_REVIEW_RECORD.json. Multiple iterative sub-rounds (R1-R4, NEWCHAT_INITIAL, NEWCHAT_VERIFIED, ATTACHCHAT). Formal verify_gpt_reply.py was not standardized yet.
- **HANDOFF-PIPELINE-REFACTOR-A1** (NEWCHAT): [pre_standardization] Pre-RECORD era: no GPT_REVIEW_RECORD.json. Multiple iterative sub-rounds (R1-R4, NEWCHAT_INITIAL, NEWCHAT_VERIFIED, ATTACHCHAT). Formal verify_gpt_reply.py was not standardized yet.
- **HANDOFF-PIPELINE-REFACTOR-A1** (NEWCHAT_INITIAL): [pre_standardization] Pre-RECORD era: no GPT_REVIEW_RECORD.json. Multiple iterative sub-rounds (R1-R4, NEWCHAT_INITIAL, NEWCHAT_VERIFIED, ATTACHCHAT). Formal verify_gpt_reply.py was not standardized yet.
- **HANDOFF-PIPELINE-REFACTOR-A1** (NEWCHAT_VERIFIED): [pre_standardization] Pre-RECORD era: no GPT_REVIEW_RECORD.json. Multiple iterative sub-rounds (R1-R4, NEWCHAT_INITIAL, NEWCHAT_VERIFIED, ATTACHCHAT). Formal verify_gpt_reply.py was not standardized yet.
- **HANDOFF-PIPELINE-REFACTOR-A1** (R1): [pre_standardization] Pre-RECORD era: no GPT_REVIEW_RECORD.json. Multiple iterative sub-rounds (R1-R4, NEWCHAT_INITIAL, NEWCHAT_VERIFIED, ATTACHCHAT). Formal verify_gpt_reply.py was not standardized yet.
- **HANDOFF-PIPELINE-REFACTOR-A1** (R2): [pre_standardization] Pre-RECORD era: no GPT_REVIEW_RECORD.json. Multiple iterative sub-rounds (R1-R4, NEWCHAT_INITIAL, NEWCHAT_VERIFIED, ATTACHCHAT). Formal verify_gpt_reply.py was not standardized yet.
- **HANDOFF-PIPELINE-REFACTOR-A1** (R3): [pre_standardization] Pre-RECORD era: no GPT_REVIEW_RECORD.json. Multiple iterative sub-rounds (R1-R4, NEWCHAT_INITIAL, NEWCHAT_VERIFIED, ATTACHCHAT). Formal verify_gpt_reply.py was not standardized yet.
- **HANDOFF-PIPELINE-REFACTOR-A1** (R4): [pre_standardization] Pre-RECORD era: no GPT_REVIEW_RECORD.json. Multiple iterative sub-rounds (R1-R4, NEWCHAT_INITIAL, NEWCHAT_VERIFIED, ATTACHCHAT). Formal verify_gpt_reply.py was not standardized yet.
- **GPT-REVIEW-SUBMISSION-PARAMETERIZE-A1** (R1): [verdict_mismatch] Verifier failed (exit≠0) but GPT verdict was accepted_with_limitation.

### LOW (4)

- **AA-FLOW-CONTRACT-CONTEXT-PACK** (R1): [pre_standardization] Pre-standardization format (.md): no RECORD, no RUN_ID, no structured END_OF_GPT_RESPONSE. Cannot be fully verified by current verify_gpt_reply.py.
- **AA-FLOW-CONTRACT-INTEGRATION** (R1): [pre_standardization] Pre-standardization format (.md): no RECORD, no RUN_ID, no structured END_OF_GPT_RESPONSE. Cannot be fully verified by current verify_gpt_reply.py.
- **AA-RUNNER-CONTRACT-CONTEXT-PACK** (R1): [pre_standardization] Pre-standardization format (.md): no RECORD, no RUN_ID, no structured END_OF_GPT_RESPONSE. Cannot be fully verified by current verify_gpt_reply.py.
- **AA-RUNNER-CONTRACT-INTEGRATION** (R1): [pre_standardization] Pre-standardization format (.md): no RECORD, no RUN_ID, no structured END_OF_GPT_RESPONSE. Cannot be fully verified by current verify_gpt_reply.py.

## Process Flow

```
Submission → Capture → Verification → Verdict

  [25 submissions] → [25 captures] → [13 verified] → [20 verdicts]

  Orphan submissions: 0
  Orphan captures:    0
  Unverified:         3
```

---

*Report generated by `generate_reconciliation_report.py` at `2026-06-09T11:09:01.084737+08:00`*

END_OF_RECONCILIATION_REPORT