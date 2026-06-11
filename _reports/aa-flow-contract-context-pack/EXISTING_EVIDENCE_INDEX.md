# Existing Evidence Index

> Cross-referencing dev-frame-opencode evidence relevant to AA-1

---

## S2 Evidence

| Evidence | Path | Exists | Purpose |
|----------|------|--------|---------|
| S2 GPT review result | `/d/dev-frame-opencode/_reports/gpt-reviews/s2-gpt-review-result.md` | yes | GPT's S2 review reply text |
| S2 GPT review decision | `/d/dev-frame-opencode/_reports/gpt-reviews/s2-gpt-review-decision.md` | yes | Parsed decision: `blocked`, S2=no, S3=no |
| S2 full flow report | `/d/dev-frame-opencode/_reports/gpt-reviews/s2-full-review-flow-report.md` | yes | Flow status, submit evidence, decision |
| S2 full flow log | `/d/dev-frame-opencode/_reports/gpt-reviews/s2-full-review-flow-log.md` | yes | Timestamped event log |
| S2 evidence pack manifest | `/d/dev-frame-opencode/_reports/s2-gpt-review-evidence-pack/PACK_MANIFEST.md` | yes | Pack contents list |
| S2 evidence pack zip | `/d/dev-frame-opencode/s2-gpt-review-evidence-pack.zip` | yes | Submitted to GPT |

## S3 Evidence

| Evidence | Path | Exists | Purpose |
|----------|------|--------|---------|
| S3 Phase 1 review pack zip | `/d/dev-frame-opencode/s3-phase1-review-pack.zip` | yes | S3 Phase 1 evidence |
| S3 Phase 1 GPT accepted | Referenced in flow reports | reported | GPT accepted S3 Phase 1 |
| S3 Phase 2 GPT allowed | Referenced in flow reports | reported | GPT allowed S3 Phase 2 |

## Oracle Automation Tools

| Evidence | Path | Exists | Purpose |
|----------|------|--------|---------|
| oracle_flow_state.py | `/d/dev-frame-opencode/tools/oracle_flow_state.py` | yes | Flow state management |
| oracle_decision_dispatcher.py | `/d/dev-frame-opencode/tools/oracle_decision_dispatcher.py` | yes | Decision → dispatch |
| oracle_post_decision_driver.py | `/d/dev-frame-opencode/tools/oracle_post_decision_driver.py` | yes | Post-GPT-decision driver |
| oracle_gpt_full_review_flow.py | `/d/dev-frame-opencode/tools/oracle_gpt_full_review_flow.py` | yes | Full review: submit → monitor → parse |
| oracle_chatgpt_cdp_handoff.py | `/d/dev-frame-opencode/tools/oracle_chatgpt_cdp_handoff.py` | yes | Chrome CDP handoff to ChatGPT |
| oracle_gpt_reply_monitor.py | `/d/dev-frame-opencode/tools/oracle_gpt_reply_monitor.py` | yes | Monitor GPT for new reply |

## Flow State Files

| Evidence | Path | Exists | Purpose |
|----------|------|--------|---------|
| FLOW_OUTCOME.json | Not found at expected paths | unknown | Current flow outcome state |
| ACTION_LOG.md | Not found at expected paths | unknown | Current action log |
| S3_PHASE2_TASKSPEC.md | Not found at expected paths | unknown | Generated next-stage task spec |

## Key Observation

The oracle scripts exist and are functional. The structural gaps are NOT in the scripts — they are in the absence of contracts that the scripts should read and enforce. This is exactly what AA-1 addresses.
