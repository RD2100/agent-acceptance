# Capability Routing Status Index -- CR5

> Batch CR-B, 2026-05-27

## Track Status

| Batch | Name | Status | Key Deliverable |
|:---:|------|:---:|------|
| CR0 | Capability Inventory | pass_to_review | 17 capabilities registered |
| CR1 | Routing Matrix | pass_to_review | 13 task types mapped |
| CR2 | Prompt Contract | pass_to_review | Agent + reviewer prompts |
| CR3 | Negative Tests | pass_to_review | 30 tests, 16 hard stops |
| CR4 | Reviewer Playbook | pass_to_review | Quick + deep review |
| CR5 | Final Audit | pass_to_review | Audit + handoff |

## Capability Summary

| Capability | Risk | Access | Auto-use? | Execution? |
|------------|:---:|:---:|:---:|:---:|
| CodeGraph | high | read_only | false | false |
| rg/Grep/Read | low | read_only | false | false |
| PowerShell | medium | read_only | false | false |
| JSON Schema Validation | low | read_only | false | false |
| Runtime Docs | low | read_only | false | false |
| Runtime Rules | low | read_only | false | false |
| Negative Tests | low | reference_only | false | false |
| Reviewer Playbooks | low | reference_only | false | false |
| Blackboard MCP | critical | snapshot_only | false | false |
| test-frame | high | read_only | false | false |
| dev-frame | high | read_only | false | false |
| Local Skills | high | reference_only | false | false |
| Memory | high | read_only | false | false |
| WorkQueue | high | read_only | false | false |
| Scripts | high | human_gated | false | false |
| Hooks Draft | medium | reference_only | false | false |
| Phase 6 SourceLock | critical | reference_only | false | false |

## Quick Reference

- **Agent prompt**: `coding-agent-capability-prompt.md`
- **Routing matrix**: `task-capability-routing-matrix.md`
- **Audit template**: `capability-routing-report-template.md`
- **Reviewer checklist**: `capability-routing-reviewer-checklist.md`
- **Negative tests**: `capability-routing-negative-tests.md`
