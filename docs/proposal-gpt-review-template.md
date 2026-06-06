# Proposal: Unified GPT Review Prompt Template

> Status: draft-v1, submitted to GPT for co-design
> Goal: One template to rule all GPT review prompts, with task-specific extension

## Problem

Currently the project has **three incompatible GPT reply formats**:

| Format | Source | Key Fields |
|--------|--------|------------|
| SADP Review | `schemas/agent-runtime/review.schema.json` | `verdict: pass/blocked/fail`, `reviewer_role`, `findings[]` |
| Evidence Pack | `policies/EVIDENCE_PACK_CONTRACT.md` | `Overall Judgment: accepted/partial/blocked/human_required`, `allow_next_stage` |
| Task-specific (H3) | Manual ad-hoc | `h3_authorized: yes`, `acceptance_scope`, `allowed[]`, `prohibited[]` |

Each GPT review prompt is written from scratch, producing incompatible reply formats.

## Proposal: Two-Layer Template

**Layer 1 — Base (mandatory, same for all tasks):**
```yaml
REVIEW_RUN_ID: <task-id>
overall_judgment: accepted | blocked | human_required | review_unverified
reviewer_type: gpt | human | agent
evidence_inspected: [list of files actually read]
blocking_reasons: [list or "none"]
missing_evidence: [list or "none"]
scope_violation: true | false | n/a
fake_green_risk: true | false | n/a
required_next_action: <concrete step or "none">
allow_proceed: true | false
rationale: <explanation>
```

**Layer 2 — Task-specific (extends base):**
```yaml
# Task-specific fields go here, varying by task type.
# Examples:
task_type_specific:
  # For authorization-only tasks (like H3):
  authorized: yes | no
  acceptance_scope: "<description>"
  execution_completed: no
  allowed: [...]
  prohibited: [...]

  # For design reviews (like PAPER-A1):
  design_completeness: adequate | needs_more | insufficient
  contracts_coverage: adequate | needs_more
  fail_closed_rules_adequate: yes | no
  confidentiality_adequate: yes | no
```

## Design Principles

1. **Base fields are always required** — any parser can read `overall_judgment` without knowing the task type
2. **Task-specific fields are self-describing** — grouped under `task_type_specific:`
3. **Format is YAML** — machine-parseable, human-readable
4. **Template lives in ONE place** — `templates/GPT_REVIEW_PROMPT_TEMPLATE.md`
5. **Each task derives from template** — copy template, add task-specific fields at bottom

## Example: H3 Authorization Review

```yaml
REVIEW_RUN_ID: h3-paper-test-auth-v1-20260605
overall_judgment: accepted
reviewer_type: gpt
evidence_inspected:
  - H3_AUTHORIZATION.md
  - PACK_MANIFEST.md
  - VALIDATION_RESULT.json
blocking_reasons: none
missing_evidence: none
scope_violation: false
fake_green_risk: false
required_next_action: "Proceed with H3 execution within authorized scope"
allow_proceed: true
rationale: "H3 scope is authorization-only, template testing, no real paper. Evidence confirms safety boundaries."
task_type_specific:
  authorized: yes
  acceptance_scope: "template testing only — init paper_iteration, dry-run, verify no real content"
  execution_completed: no
  allowed:
    - "devframe init paper_iteration"
    - "generate PAPER_PROFILE / PAPER_STATE / PAPER_LEDGER"
    - "run paper_iteration dry-run"
  prohibited:
    - "process real paper text"
    - "connect live CDP"
    - "submit to GPT"
    - "guard removal"
    - "evidence cleanup"
```

## Example: PAPER-A1 Design Review

```yaml
REVIEW_RUN_ID: paper-a1-contract-design-v1
overall_judgment: accepted
reviewer_type: gpt
evidence_inspected:
  - contracts/paper_acceptance_contracts.yaml
  - schemas/paper_evidence_pack.schema.json
  - tests/test_paper_acceptance_contracts.py
  - examples/paper_acceptance_synthetic_case/SYNTHETIC_EVIDENCE_PACK.json
  - TEST_OUTPUT.txt
blocking_reasons: none
missing_evidence: none
scope_violation: false
fake_green_risk: false
required_next_action: "Commit and push evidence; proceed to runtime integration"
allow_proceed: true
rationale: "7 contracts structurally complete, schema validates, 14/14 tests pass, no real paper."
task_type_specific:
  design_completeness: adequate
  contracts_coverage: adequate
  fail_closed_rules_adequate: yes
  confidentiality_adequate: yes
  evidence_first_enforced: yes
  isomorphism_valid: yes
```

## Open Questions for GPT

1. Should `task_type_specific` be a flat map or grouped by `task_type` enum?
2. Should we use `overall_judgment` (lowercase, from EVIDENCE_PACK_CONTRACT) or `Overall Judgment` (title case, from the same doc)? The project mixes both.
3. Should `evidence_inspected` be a list of filenames or include SHA256 hashes?
4. Should the template include a `task_type` field that determines which specific fields are valid?
5. Should the template be a `.md` file (for human GPT prompts) or a `.schema.json` (for machine validation)?
