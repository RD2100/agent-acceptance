# TaskSpec: SHARED-CDP-V2-REVIEW-FINDINGS-FIX-A1 — Fix 7 Blocking Review Findings

- **ID**: SHARED-CDP-V2-REVIEW-FINDINGS-FIX-A1
- **Batch**: shared-cdp-v2-governance
- **Risk**: high
- **Priority**: P0
- **Goal**: Fix 7 blocking issues identified by ChatGPT independent reviewer in the formal code review of the v2 Shared CDP architecture. Includes fail-closed dispatch gates, canonical resolver unification, CDP security hardening, webSocketDebuggerUrl redaction, and follow-up security cleanup (10 FAIL items) + port/scheme policy consistency.
- **Context**: The v2 Shared CDP architecture (10 projects sharing one Chrome on port 9222) was implemented but never formally reviewed. ChatGPT reviewer returned BLOCKED verdict with 7 blocking findings. This TaskSpec covers the retroactive SADP-compliant fix cycle across 3 review rounds.
- **Allowed Files**:
  - scripts/tab_target_resolver.py (modify — canonical resolver)
  - scripts/multi_project_router.py (modify — router)
  - scripts/dry_run_dispatch_10.py (modify — dry-run classifier)
  - scripts/gate0_preflight_10.py (modify — preflight check)
  - tests/test_dispatch_packet_v2.py (modify)
  - tests/test_dry_run_dispatch_v2.py (new)
  - tests/test_tab_target_resolver.py (modify)
  - tests/test_gate0_preflight_v2.py (modify)
  - tests/test_router_10_project_stress.py (modify)
  - tests/test_multi_project_isolation.py (modify)
  - .agent/MULTI_PROJECT_RESOURCE_POLICY.json (modify — port range update)
- **Forbidden**:
  - Do not modify core rules
  - Do not modify SADP protocol
  - Do not modify PROJECT_REGISTRY.json
  - Do not modify CONVERSATION_BINDING.json
  - No live dispatch (human gate required)

- **Gate 0 Ledger**:
  ```yaml
  gate_0:
    triggered: true
    trigger_reason: "P0 blocking findings in formal code review — 7 issues including security and correctness"

    inventory_evidence:
      queried_sources:
        - capability-inventory.md (checked: no existing CDP tab resolver capability)
        - sub-agent-dispatch-protocol.md (checked: SADP format requirements)
        - lessons-learned.md (checked: LL-009 external enforcement gap)
        - scripts/tab_target_resolver.py (existing canonical resolver — reuse target)
        - scripts/multi_project_router.py (existing private resolver — to be removed)
        - scripts/gate0_preflight_10.py (existing private list_cdp_pages — to be removed)
        - .agent/MULTI_PROJECT_RESOURCE_POLICY.json (port policy source of truth)
      matched_capabilities:
        - tab_target_resolver.resolve_tab_target (existing, reused as canonical)
        - tab_target_resolver.list_cdp_pages (existing, reused as canonical)
      compared_against_request:
        - "fail-closed dispatch gates (target_id, tab_match_status, target_url)"
        - "canonical import from tab_target_resolver (eliminate duplicates)"
        - "CDP localhost-only validation with port range"
        - "webSocketDebuggerUrl redaction"
        - "conversation_id redaction in reports"
        - "URL normalization for matching"

    rules_checked:
      - core-008 (Reuse-before-Build: reuse tab_target_resolver as canonical)
      - core-003 (Phase Boundary: all gates must pass before completion)
      - core-006 (Evidence Before Claim: test output required)
    lessons_checked:
      - LL-009 (external enforcement gap — not applicable, this is code fix)

    sufficiency_decision: existing_capabilities_sufficient_with_modification
    decision: modify_existing
    delta_justification: "tab_target_resolver already provides canonical resolution. Fix requires hardening (validate_cdp_endpoint, URL normalization) and consumer migration (router, gate0, dry_run import from canonical). No new modules needed."
  ```

- **Conflict Registry**:
  ```yaml
  conflict_registry:
    read_set:
      - scripts/tab_target_resolver.py
      - scripts/multi_project_router.py
      - scripts/dry_run_dispatch_10.py
      - scripts/gate0_preflight_10.py
      - tests/test_dispatch_packet_v2.py
      - tests/test_gate0_preflight_v2.py
      - tests/test_router_10_project_stress.py
      - tests/test_multi_project_isolation.py
      - .agent/MULTI_PROJECT_RESOURCE_POLICY.json
      - .agent/PROJECT_REGISTRY.json (read only)
      - .agent/CONVERSATION_BINDING.json (read only)
    write_set:
      - scripts/tab_target_resolver.py
      - scripts/multi_project_router.py
      - scripts/dry_run_dispatch_10.py
      - scripts/gate0_preflight_10.py
      - tests/test_dispatch_packet_v2.py
      - tests/test_dry_run_dispatch_v2.py
      - tests/test_tab_target_resolver.py
      - tests/test_gate0_preflight_v2.py
      - tests/test_router_10_project_stress.py
      - tests/test_multi_project_isolation.py
      - .agent/MULTI_PROJECT_RESOURCE_POLICY.json
    protected_files_touched: false
    conflict_level: medium
    conflict_notes: "4 source files + 6 test files modified. No governance files touched. All changes are additive hardening + bug fixes."
  ```

- **Acceptance Gates**:
  1. All 7 blocking findings from ChatGPT review are FIXED with code evidence
  2. All private duplicate implementations removed (router, gate0 → canonical imports)
  3. validate_cdp_endpoint() restricts to localhost + port range 9222-9231
  4. webSocketDebuggerUrl redacted in all resolver outputs
  5. conversation_id redacted in all reports
  6. URL normalization strips query params, fragments, trailing slashes
  7. Fail-closed dispatch: target_id=None → dispatchable=false
  8. Fail-closed dispatch: tab_match_status != exact_match → dispatchable=false
  9. Gate 1 (Target Tests): all targeted tests pass
  10. Gate 2 (Full Suite): full test suite passes with 0 failures
  11. Gate 4 (Security): Security checklist all PASS
  12. Port range aligned with 10-project plan (9222-9231)
  13. Scheme validation error message consistent with accepted schemes

- **Expected Output**: Fixed code + full test suite green + evidence pack + ChatGPT review verdict
- **Rollback**: git checkout affected files
- **Report To**: ChatGPT conversation 6a26cc03 (independent reviewer)
