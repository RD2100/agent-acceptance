# Capability Risk Matrix -- CR0

> Batch CR-A, 2026-05-27
> Risk classification for all 17 registered capabilities.

## Risk Distribution

| Risk | Count | Capabilities |
|:---:|:---:|------|
| high | 7 | CodeGraph, test-frame, dev-frame, Local Skills, Memory, WorkQueue, Scripts |
| medium | 2 | PowerShell shell, Hooks Draft |
| low | 6 | rg/Grep/Read, JSON validation, Runtime Docs, Runtime Rules, Negative Tests, Reviewer Playbooks |

## Risk Detail

| Capability | Risk | Primary Threat | Current Control | Gate on Violation |
|---|---|---|---|---|
| CodeGraph | high | stale index used as fact | freshness check required; trusted=false for stale/unknown/empty | needs_revision |
| rg/Grep/Read | low | secret file access | Read tool constraint (.env etc. forbidden) | blocked (if secrets) |
| PowerShell | medium | mutation via Set-Content/Remove-Item | Phase 0-5 write restrictions | blocked |
| JSON validation | low | false parse success | ConvertFrom-Json + manual review | needs_revision |
| Runtime Docs | low | stale doc referenced | doc freshness check | needs_revision |
| Runtime Rules | low | rule misinterpretation | rule ID reference required | needs_revision |
| Negative Tests | low | N/A (reference only) | expected_gate_decision != pass enforced | N/A |
| Reviewer Playbooks | low | N/A (reference only) | human reviewer is gate authority | N/A |
| test-frame | high | aggregator/attribution execution | execution_policy=forbidden in R2 | blocked |
| dev-frame | high | smoke_test.py execution | execution_policy=forbidden in R3 | blocked |
| Local Skills | high | skill auto-load/execution | auto_use_allowed=false; execution_allowed=false; evolution quarantined | blocked |
| Memory | high | used_as_fact; memory write | write_allowed=false; used_as_fact=false in R6 | blocked |
| WorkQueue | high | task dispatch without approval | read_only in R7; consumption forbidden | blocked |
| Scripts | high | execution without ScriptSafetyRecord | not_run in R7; human gate required | blocked |
| Hooks Draft | medium | accidental registration | AUDIT-ONLY DRAFT; not registered | blocked |
| Phase 6 SourceLock | critical | clone without source URL / approval | Phase 6C blocked; planning != clone approval | blocked |

## Risk Mitigation Summary

- **All capabilities**: auto_use_allowed=false, execution_allowed=false, mutation_allowed=false
- **Critical/High**: all require human gate for any state escalation
- **Evidence required**: all capability usage must be documented in Capability Routing Audit
- **Fallback defined**: every preferred capability has a fallback
