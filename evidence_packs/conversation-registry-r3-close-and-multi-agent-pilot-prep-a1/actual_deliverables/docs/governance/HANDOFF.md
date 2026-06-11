# Governance Handoff

## Current Slice

Task: extend Conversation Registry and pilot governance so `devframe-control-plane`, `dev-frame-opencode`, and `paper-workflow` are explicitly in scope while remaining human-gated.

## Changed Areas

- Registry/schema/scaffold now model `governance_scope.external_runtimes`.
- Validator checks required runtime IDs and human-gate invariants.
- Tests cover missing scope, missing opencode runtime, and runtime human-gate drift.
- Runtime docs distinguish in-scope governance from execution authorization.
- Cross-repo verification scripts now default to `HUMAN_REQUIRED` and require explicit authorization records before running sibling repo tests/smoke.

## Do Not Claim Yet

- Do not claim full-suite pass.
- Do not claim opencode execution is approved.
- Do not claim dev-frame writes or ai-workflow-hub execution are allowed.
- Do not claim real paper workflow or live CDP has been authorized.
- Do not claim cross-repo pytest/smoke has run; the updated scripts intentionally block by default.

## Verification Completed

Targeted tests:

```powershell
python -m pytest tests\test_conversation_registry.py tests\test_cross_project_scaffold.py -q
```

Result: 129 passed.

Related tests:

```powershell
python -m pytest tests\test_validate_run_id_consistency.py tests\test_conversation_registry.py tests\test_cross_project_scaffold.py -q
```

Result: 143 passed.

Root binding validation:

```powershell
python scripts\validate_conversation_registry.py .agent\CONVERSATION_BINDING.json --project-root D:\agent-acceptance
```

Result: `valid=true`, `schema_validated=true`, runtime_count=3.

Pre-GPT/evidence pack gate has been run:

```powershell
python scripts\pre_gpt_review_gate.py evidence_packs\conversation-registry-r3-close-and-multi-agent-pilot-prep-a1
```

Result: `gate_passed=true`, `warnings=[]`. Next step is external review, not pilot execution.
