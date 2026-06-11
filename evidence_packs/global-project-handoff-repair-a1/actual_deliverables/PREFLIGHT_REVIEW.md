# Preflight Review

## Existing workflow components found

- `HANDOFF_SOURCE_OF_TRUTH.md` — exists=True — P1 GPT-approved artifact
- `LEGACY_HANDOFF_INVENTORY.md` — exists=True — P1 GPT-approved artifact
- `_reports/handoff-pipeline-refactor-a1/HANDOFF_EVIDENCE_MAP.json` — exists=True — P0/P1 evidence map artifact
- `_reports/handoff-pipeline-refactor-a1/HANDOFF_STALE_CHECK.md` — exists=True — P0 generated stale-check report
- `_reports/handoff-pipeline-refactor-a1/HANDOFF_SAFETY_SCAN.md` — exists=True — P0 generated safety-scan report
- `_reports/handoff-pipeline-refactor-a1/HANDOFF_DRAFT_FOR_GPT.md` — exists=True — P1 draft artifact with limitation
- `_reports/handoff-pipeline-refactor-a1/TARGETED_TEST_OUTPUT.txt` — exists=True — P0 targeted test output
- `_reports/handoff-pipeline-refactor-a1/SAFETY_ATTESTATION.md` — exists=True — P0 attestation
- `evidence_packs/handoff-pipeline-refactor-a1/PACK_MANIFEST.md` — exists=True — P0 evidence manifest
- `evidence_packs/handoff-pipeline-refactor-a1/CLOSURE_REPORT.md` — exists=True — P0 closure report with limitation
- `docs/WORKFLOW_AUDIT_LEDGER.yaml` — exists=True — P0/P3 workflow audit ledger
- `contracts/FLOW_OUTCOME.schema.json` — exists=True — P0 contract
- `contracts/DISPATCH_RESULT.schema.json` — exists=True — P0 contract
- `scripts/pre_gpt_review_gate.py` — exists=True — P0 reusable gate script
- `scripts/evidence_pack_linter.py` — exists=True — P0 reusable pack linter
- `scripts/review_queue.py` — exists=True — P0 reusable review queue
- `scripts/verify_gpt_reply.py` — exists=True — P0 reusable GPT reply verifier
- `scripts/handoff_compiler.py` — exists=True — P0 reusable handoff compiler wrapper
- `scripts/handoff_source_map.py` — exists=True — P0 reusable source-map builder
- `scripts/handoff_stale_check.py` — exists=True — P0 reusable stale checker
- `scripts/handoff_safety_scan.py` — exists=True — P0 reusable safety scanner
- `scripts/gpt_new_chat_attachment_submit.py` — exists=True — P0 reusable attachment-backed GPT submitter

## Directly reused

- `scripts/handoff_source_map.py`
- `scripts/handoff_stale_check.py`
- `scripts/handoff_safety_scan.py`
- `scripts/evidence_pack_linter.py`
- `scripts/pre_gpt_review_gate.py`
- `scripts/verify_gpt_reply.py`
- `HANDOFF_SOURCE_OF_TRUTH.md`
- `HANDOFF_APPROVAL_RECORD.json`
- `docs/WORKFLOW_AUDIT_LEDGER.yaml`

## Legacy/reference only

- `PROJECT_HISTORY.md`
- `PROJECT_HISTORY_FINAL.md`
- `HANDOFF.md`
- `HANDOFF_V5.md`
- `HANDOFF_V6.md`
- `HISTORY_ANALYSIS.md`
- `root GPT_*.txt unless verified and bound`
