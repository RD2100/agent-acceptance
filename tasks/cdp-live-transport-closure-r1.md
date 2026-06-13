# TaskSpec: CDP-LIVE-TRANSPORT-CLOSURE-R1

- **ID**: CDP-LIVE-TRANSPORT-CLOSURE-R1
- **Batch**: controlled-multi-gpt-pilot
- **Risk**: high
- **Priority**: P1
- **Goal**: Repair the real CDP transport paths that fail against the authorized shared Chrome instance.
- **Context**: Real probes showed `websockets 16` proxy auto-detection breaking page WebSocket connections and Playwright HTTP endpoint discovery requesting an unsupported trailing-slash URL.
- **Allowed Files**:
  - .ai/current-task.yaml
  - scripts/cdp_write_adapter.py
  - scripts/cdp_playwright_sender.py
  - tests/test_cdp_write_adapter.py
  - tasks/cdp-live-transport-closure-r1.md
  - _evidence/CDP-LIVE-TRANSPORT-CLOSURE-R1/**
  - hooks/sealed-files-manifest.json
  - _evidence/hook-output/**
- **Forbidden**:
  - No binding or activation-record edits in this task
  - No destructive Git operations
  - No paper-workflow execution

- **Gate 0 Ledger**:
  ```yaml
  gate_0:
    triggered: true
    trigger_reason: "P1 real-path CDP transport failures"
    inventory_evidence:
      queried_sources:
        - scripts/cdp_write_adapter.py
        - scripts/cdp_playwright_sender.py
        - tests/test_cdp_write_adapter.py
      matched_capabilities:
        - shared_cdp_transport
        - playwright_cdp_sender
        - controlled_pilot_runtime
    rules_checked: [core-004, core-008, sec-002, review-001]
    sufficiency_decision: existing_sufficient
    decision: reuse
    delta_justification: "Repair existing transports only; no new runtime capability."
  ```

- **Conflict Registry**:
  ```yaml
  conflict_registry:
    read_set:
      - scripts/cdp_write_adapter.py
      - scripts/cdp_playwright_sender.py
      - tests/test_cdp_write_adapter.py
    write_set:
      - .ai/current-task.yaml
      - scripts/cdp_write_adapter.py
      - scripts/cdp_playwright_sender.py
      - tests/test_cdp_write_adapter.py
      - tasks/cdp-live-transport-closure-r1.md
      - _evidence/CDP-LIVE-TRANSPORT-CLOSURE-R1/**
      - hooks/sealed-files-manifest.json
      - _evidence/hook-output/**
    protected_files_touched: false
    conflict_level: low
  ```

- **Acceptance Gates**:
  1. Page-level CDP WebSocket connects directly without system proxy use.
  2. Playwright resolves the browser WebSocket endpoint from `/json/version`.
  3. Unit regressions cover both transport failures.
  4. A real shared-Chrome read probe succeeds through each transport.
  5. Disconnecting Playwright does not close the user-owned shared Chrome.
  6. Targeted and canonical tests report exact outcomes.

- **Expected Output**: Minimal transport fixes, regressions, real-path evidence, and a scoped commit.
- **Rollback**: Revert only the files listed in the write set.
- **Report To**: Current session
