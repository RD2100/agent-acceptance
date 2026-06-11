verdict: PASS

changed files:
- `_reports/runtime-governance-architecture-rereview-a1/ARCHITECTURE_REVIEW.md` only.

critical paths:
- `docs/agent-runtime/tool-policy.md:90-102`
- `docs/agent-runtime/capability-inventory.md:632-649`, `docs/agent-runtime/capability-inventory.md:668`
- `docs/agent-runtime/sub-agent-dispatch-protocol.md:553-564`, `docs/agent-runtime/sub-agent-dispatch-protocol.md:603-609`
- `docs/MULTI_AGENT_MULTI_GPT_PILOT_PLAN.md:21-27`, `docs/MULTI_AGENT_MULTI_GPT_PILOT_PLAN.md:80-85`, `docs/MULTI_AGENT_MULTI_GPT_PILOT_PLAN.md:96-111`
- `.agent/CONVERSATION_BINDING.json`
- `.agent/CONVERSATION_REGISTRY.schema.json`
- `scripts/multi_agent_gate0_preflight.py:94-104`, `scripts/multi_agent_gate0_preflight.py:167-193`, `scripts/multi_agent_gate0_preflight.py:250-263`
- `scripts/multi_agent_dispatch_plan.py:1-5`, `scripts/multi_agent_dispatch_plan.py:116-119`, `scripts/multi_agent_dispatch_plan.py:428-436`, `scripts/multi_agent_dispatch_plan.py:461-473`, `scripts/multi_agent_dispatch_plan.py:511-514`
- `scripts/validate_multi_agent_dispatch_plan.py:55-84`
- `docs/governance/RISK_REGISTER.md:5-13`
- `docs/governance/VERIFY_MATRIX.md:5-19`
- `docs/governance/HANDOFF.md:5-17`, `docs/governance/HANDOFF.md:37-45`

checks run:
- `rg -n --hidden -e "devframe-control-plane|dev-frame-opencode|paper-workflow|CAP-029|HUMAN_REQUIRED|executed_external_runtime|pending_review|mitigated_verified|external runtime|external_runtime|opencode|D:\\dev-frame|paper" <allowed files>` -> exit 0; located all relevant governance/runtime references.
- `rg -n --hidden -e "authorized|authorization|execute|execution|blocked|defer|disabled|read-only|read_only|handoff|governance|scope|status|active|inactive|registered|human" <allowed files>` -> exit 0; no contradictory execution grant found in the reviewed set.
- Targeted `rg -n -C` context reads for tool policy, capability inventory, SADP, pilot plan, Gate 0 preflight, dispatch plan, and dispatch validator -> exit 0.
- `Get-Content` on `.agent/CONVERSATION_BINDING.json`, `.agent/CONVERSATION_REGISTRY.schema.json`, `docs/governance/RISK_REGISTER.md`, `docs/governance/VERIFY_MATRIX.md`, and the first 60 lines of `docs/governance/HANDOFF.md` -> exit 0.
- Not run by design: `opencode run`, `D:\dev-frame` commands, cross-repo smoke/pytest, live CDP, paper workflow, real paper probes, and local test execution.

findings:
- No P0 findings.
- No P1 findings.
- No P2 findings.
- P3 clarity note: `capability-inventory.md` keeps CAP-029 outside the passport summary totals while also documenting CAP-029 separately as proposed/not executable. This is acceptable because the detailed CAP-029 entry and line 668 are explicit, but future maintenance should keep the exclusion note adjacent to any summary count changes.

output summary:
- `devframe-control-plane`, `dev-frame-opencode`, and `paper-workflow` are in governance scope, not execution scope. The binding file declares all three under `governance_scope.external_runtimes`, with `human_gate_required=true`; the schema requires `default_execution_policy=human_gated_for_external_runtime_execution` and `human_gate_required=true`.
- Tool policy is consistent with the requested boundary. `D:\dev-frame\ai-workflow-hub` is governed/read-only by default; `opencode run` is proposed/human-gated; cross-repo smoke/pytest is human-gated; paper workflow is pilot-only unless authorized and forbids real user paper processing, live CDP, and ad-hoc Playwright/GPT submission without an extra human gate.
- CAP-029 cannot be misread as executable in the reviewed files. Its detailed entry is `Status: proposed`, `Access: human_gated (not executable by default)`, `Passport verified_status: unknown`, and `Passport usable_for_execution: false`; the inventory states it is excluded from approved execution totals and is not executable in Phase 0-5.
- Gate 0 preserves the required semantics. If CAP-029 is not approved/execution-usable, `multi_agent_gate0_preflight.py` records `human_required`, returns overall `HUMAN_REQUIRED`, and emits `executed_external_runtime=false`.
- Dispatch planning preserves the required semantics. `multi_agent_dispatch_plan.py` states it does not dispatch agents or execute external runtimes, propagates `HUMAN_REQUIRED` from the preflight, sets `executed_external_runtime=false`, exits 2 for `HUMAN_REQUIRED`, and rejects any plan that claims external runtime execution.
- Consumer validation preserves the required semantics. `validate_multi_agent_dispatch_plan.py` validates schema first, then calls the semantic `validate_plan`; that semantic validator rejects `executed_external_runtime` claims and unexpected source preflight execution.
- No reviewed document contains a direct contradiction where one path blocks execution while another grants execution. The closest potentially ambiguous items are activation/checklist language and historical evidence records, but both are constrained by explicit "human gate required", "not executable readiness", or "do not claim yet" language.

artifacts:
- This report: `_reports/runtime-governance-architecture-rereview-a1/ARCHITECTURE_REVIEW.md`

known gaps:
- This was a bounded architecture rereview over the user-approved file list only.
- No tests, scripts, external runtime probes, CDP sessions, paper workflow, or real cross-repo commands were executed.
- `RISK_REGISTER.md` and `VERIFY_MATRIX.md` were not modified in this review.
- Dispatch plan JSON schema internals were not inspected because the schema file was outside the approved read list.
- This PASS does not authorize CAP-029 execution, `opencode run`, dev-frame writes/execution, real paper processing, live CDP, or cross-repo smoke/pytest.

governance recommendation:
- It is safe to mark the following `RISK_REGISTER.md` rows from `mitigated_pending_review` to `mitigated_verified`: `devframe-control-plane`, `dev-frame-opencode`, `paper-workflow`, `multi-agent pilot startup`, and `multi-agent dispatch planning`.
- The `Runtime policy` row in `VERIFY_MATRIX.md` can be accepted from `pending_review` to `passed` or equivalent reviewer-accepted status based on this architecture review. If a matching `runtime policy` row is later added to `RISK_REGISTER.md`, mark it `mitigated_verified`.
- Keep CAP-029 as `proposed`, `human_gated`, and `usable_for_execution=false` until a separate human-approved task explicitly authorizes the exact `opencode run` command class and evidence record.
- Keep paper workflow limited to handoff/governance updates, synthetic fixtures, sanitized examples, and evidence contract design unless a separate human gate authorizes real paper handling.

reviewer index:
- Changed files: `_reports/runtime-governance-architecture-rereview-a1/ARCHITECTURE_REVIEW.md`.
- Critical code paths: `scripts/multi_agent_gate0_preflight.py`, `scripts/multi_agent_dispatch_plan.py`, `scripts/validate_multi_agent_dispatch_plan.py`.
- Critical policy paths: `docs/agent-runtime/capability-inventory.md`, `docs/agent-runtime/tool-policy.md`, `docs/agent-runtime/sub-agent-dispatch-protocol.md`, `docs/MULTI_AGENT_MULTI_GPT_PILOT_PLAN.md`, `.agent/CONVERSATION_BINDING.json`, `.agent/CONVERSATION_REGISTRY.schema.json`.
- Tests run: none; intentionally read-only per task boundary.
- Generated artifacts: this architecture review report only.
- Known gaps: no external runtime execution, no live tests, no schema file outside approved scope, no governance source file updates.
- Suggested review focus: if applying the recommendation, update only the risk/status rows named above; do not change CAP-029 execution fields or weaken paper/live-CDP/opencode human gates.
