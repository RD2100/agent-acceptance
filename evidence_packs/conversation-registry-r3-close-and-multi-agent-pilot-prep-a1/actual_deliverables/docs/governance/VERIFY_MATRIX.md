# Verification Matrix

| Module | Requirement | Evidence Command Or File | Current Result | Status |
|--------|-------------|--------------------------|----------------|--------|
| Conversation Registry | Fresh scaffold includes `governance_scope` for all three runtime entries. | `python -m pytest tests\test_conversation_registry.py tests\test_cross_project_scaffold.py -q` | 129 passed | passed |
| Conversation Registry | Missing `governance_scope` fails closed. | `tests/test_conversation_registry.py::TestExternalRuntimeGovernanceScope::test_missing_governance_scope_fails_validation` | Covered by target test run | passed |
| Conversation Registry | Missing `dev-frame-opencode` fails closed. | `tests/test_conversation_registry.py::TestExternalRuntimeGovernanceScope::test_missing_opencode_runtime_fails_validation` | Covered by target test run | passed |
| Conversation Registry | Root `.agent/CONVERSATION_BINDING.json` validates with all runtime IDs. | `python scripts\validate_conversation_registry.py .agent\CONVERSATION_BINDING.json --project-root D:\agent-acceptance` | `valid=true`, `schema_validated=true`, runtime_count=3 | passed |
| Runtime policy | `opencode run`, ai-workflow-hub execution, cross-repo smoke, and paper workflow are explicitly gated. | `docs/agent-runtime/tool-policy.md` | Updated; requires human/reviewer acceptance before execution use | pending_review |
| Pilot plan | Multi-agent pilot checks capability inventory, tool policy, and governed runtime scope. | `python -m pytest tests\test_validate_run_id_consistency.py tests\test_conversation_registry.py tests\test_cross_project_scaffold.py -q` | 143 passed | passed |
| Evidence pack | Pre-GPT review gate accepts the pack for submission. | `python scripts\pre_gpt_review_gate.py evidence_packs\conversation-registry-r3-close-and-multi-agent-pilot-prep-a1` | `gate_passed=true`; warnings=[] | passed |
| Cross-repo script guards | Default script execution does not run sibling repo commands. | `python -m pytest tests\test_cross_repo_execution_guards.py tests\test_smoke_suite.py -q` | 12 passed | passed |
| Cross-repo script CLI | Default CLI returns `HUMAN_REQUIRED` instead of executing. | `python scripts\cross_repo_verify.py`; `python scripts\multi_repo_smoke.py` | exit code 2 for both; `executed=false` | passed |
