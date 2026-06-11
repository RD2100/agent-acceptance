# Governance Decision Log

| Date | Module | Decision | Reason | Verification Hook | Risk |
|------|--------|----------|--------|-------------------|------|
| 2026-06-09 | External runtime scope | `devframe-control-plane`, `dev-frame-opencode`, and `paper-workflow` are in target governance scope. | The pilot depends on control-plane provenance, agent dispatch, and paper workflow review paths; leaving them as informal references permits bypass. | `validate_conversation_registry.py` checks `governance_scope.external_runtimes`; pytest covers missing scope/runtime. | P2 |
| 2026-06-09 | Execution policy | Scope inclusion does not authorize execution. | Current phase forbids implicit cross-repo writes, cross-repo smoke, live CDP, real paper processing, and unapproved `opencode run`. | `tool-policy.md`, `capability-inventory.md`, `MULTI_AGENT_MULTI_GPT_PILOT_PLAN.md`. | P1 if violated |
| 2026-06-09 | Capability status | `dev-frame-opencode Dispatch` is registered as proposed, not executable. | Inventory must name the capability before use, but execution requires reviewer/human gate. | CAP-029 entry and `usable_for_execution=false`. | P2 |

