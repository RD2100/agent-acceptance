# TaskSpec: SHARED-CDP-GPT-REVIEW-DRY-RUN-2-A1

- **ID**: SHARED-CDP-GPT-REVIEW-DRY-RUN-2-A1
- **Batch**: SHARED-CDP-V2-REVIEW
- **Risk**: low
- **Priority**: P1
- **Goal**: Execute dry-run dispatch for all 10 registered projects against live Chrome CDP, verify fail-closed classification, and submit report to ChatGPT reviewer.

- **Gate 0 Ledger**:
  ```yaml
  gate_0:
    triggered: true
    trigger_reason: "ChatGPT R10 recommended next: verify dry-run dispatch end-to-end"
    inventory_evidence:
      queried_sources:
        - capability-inventory.md
        - scripts/dry_run_dispatch_10.py
        - scripts/multi_project_router.py
        - scripts/tab_target_resolver.py
        - scripts/gate0_preflight_10.py
        - tests/test_dry_run_dispatch_v2.py
      matched_capabilities:
        - "dry_run_dispatch_10.py: existing dry-run dispatch script for all 10 projects"
        - "multi_project_router.py: build_dispatch_packet with fail-closed gates"
        - "tab_target_resolver.py: canonical CDP tab resolution"
        - "test_dry_run_dispatch_v2.py: 16 tests covering classification"
      sufficiency_decision: existing_sufficient
    rules_checked:
      - rules/core.md
    lessons_checked:
      - docs/agent-runtime/lessons-learned.md
    decision: proceed
  ```

- **Conflict Registry**:
  ```yaml
  conflict_registry:
    read_set:
      - scripts/dry_run_dispatch_10.py
      - scripts/multi_project_router.py
      - scripts/tab_target_resolver.py
      - scripts/gate0_preflight_10.py
      - .agent/PROJECT_REGISTRY.json
      - .agent/CONVERSATION_BINDING.json
    write_set:
      - _reports/multi-project-batch-init-a1/DRY_RUN_DISPATCH_10.json
    conflict_level: low
    protected_files_touched: []
  ```

- **Acceptance Gates**:
  1. dry_run_dispatch_10.py executes against live Chrome CDP without errors
  2. agent-acceptance (active binding) classified as dispatchable
  3. 9 pending_binding projects classified as non_dispatchable_pending
  4. No false-positive dispatchable classifications
  5. JSON report generated with all 10 project results
  6. Full regression suite still passes
