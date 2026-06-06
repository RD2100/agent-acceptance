# GPT Review Prompt — PAPER-A1 Contract Design

> This review follows the standard Evidence Pack Contract format per policies/EVIDENCE_PACK_CONTRACT.md.

## Background

The agent-acceptance project has been extended with a Paper Acceptance Contract layer.
This is a design-only task — no runtime execution, no real paper processing, no external API.

## What's In This Pack

14 files including all actual deliverables (not just summaries):

**Evidence files:**
- PACK_MANIFEST.md — manifest of all files in this pack
- GPT_REVIEW_PROMPT.md — this prompt
- TEST_OUTPUT.txt — fresh pytest output (73/73 PASS)
- SAFETY_ATTESTATION.md — safety boundary attestation
- FLOW_OUTCOME.json — machine-readable outcome
- CLOSURE_REPORT.yaml — structured closure report

**Actual deliverables (for direct inspection):**
- contracts/paper_acceptance_contracts.yaml — 7 full contracts (GENERAL, CSSCI_REVIEW, THESIS_MIDTERM, CITATION_VERIFICATION, ACADEMIC_REVISION, CONFIDENTIALITY, EVIDENCE_PACK)
- docs/paper-workflow-acceptance.md — design rationale + architecture boundaries
- schemas/paper_evidence_pack.schema.json — evidence pack JSON Schema
- tests/test_paper_acceptance_contracts.py — 14 structural tests
- examples/paper_acceptance_synthetic_case/SYNTHETIC_*.{md,json,yaml} — 4 synthetic example files

**Fixes applied since previous review:**
1. Removed broken allOf rule from schema that rejected valid evidence packs
2. ZIP layout mirrors repo structure (can extract and run tests directly)

## What GPT Must Judge

1. Are the 7 contracts sufficient for paper task acceptance?
2. Is the code-to-paper isomorphism correctly established?
3. Do fail_closed rules cover safety boundaries?
4. Is the confidentiality contract adequate?
5. Is Evidence-First enforced in the paper context?
6. Can the SYNTHETIC_EVIDENCE_PACK.json validate against the schema?

## Required Output Format (per EVIDENCE_PACK_CONTRACT.md)

```
Overall Judgment: [accepted / partial / blocked / human_required]
allow_next_stage: [true / false]
Blocking Reasons: [list or "none"]
Missing Evidence: [list or "none"]
Scope Violation: [true / false / unknown]
Fake-Green Risk: [true / false / unknown]
Required Next Action: [concrete step or "none"]
```

## Rules

- Do NOT request real paper content (design-only task)
- Do NOT suggest guard removal or evidence cleanup
- Do NOT suggest enabling live CDP or GPT submission by default
- Agent summary is not evidence — judge based on actual contract YAML, schema, and test code in the ZIP
- If blocking: specify exactly which contract/schema clause fails and why
