# TaskSpec: CDP-REVIEW-SECURITY-REREVIEW-R1

- **ID**: CDP-REVIEW-SECURITY-REREVIEW-R1
- **Batch**: cdp-review-security-rereview
- **Risk**: high
- **Priority**: P1
- **Goal**: Close residual fail-open, prompt-injection, and evidence-attribution defects left by commit 38292166.
- **Context**: Security rereview reproduced empty-dispatch fake success, ambiguous reviewer selection, delimiter spoofing, and self-referential target attribution.
- **Allowed Files**:
  - scripts/cdp_dispatch_runner.py
  - scripts/cdp_review_api.py
  - scripts/cdp_playwright_sender.py
  - tests/test_cdp_write_adapter.py
  - tasks/cdp-review-security-rereview-r1.md
  - _evidence/CDP-REVIEW-SECURITY-REREVIEW-R1/**
  - _reports/cdp-review-security-rereview-r1/**
- **Forbidden**:
  - No external CDP or ChatGPT runtime execution
  - No edits to live conversation bindings or existing CDP evidence
  - No destructive git operations or dependency changes

- **Gate 0 Ledger**:
  ```yaml
  gate_0:
    triggered: true
    trigger_reason: "P1 security correction after independent rereview"
    inventory_evidence:
      queried_sources:
        - scripts/cdp_dispatch_runner.py
        - scripts/cdp_review_api.py
        - scripts/cdp_playwright_sender.py
        - tests/test_cdp_write_adapter.py
      matched_capabilities:
        - cdp_review_dispatch
        - prompt_injection_guard
        - evidence_attribution
      compared_against_request:
        - "Reject empty and ambiguous reviewer dispatch"
        - "Block prompt injection before external send"
        - "Derive actual attribution from browser/CDP state"
    rules_checked: [core-004, core-008, sec-002, review-001]
    sufficiency_decision: existing_sufficient
    decision: reuse
    delta_justification: "Targeted hardening of existing code paths; no new capability or dependency required."
  ```

- **Conflict Registry**:
  ```yaml
  conflict_registry:
    read_set:
      - scripts/cdp_dispatch_runner.py
      - scripts/cdp_review_api.py
      - scripts/cdp_playwright_sender.py
      - tests/test_cdp_write_adapter.py
    write_set:
      - scripts/cdp_dispatch_runner.py
      - scripts/cdp_review_api.py
      - scripts/cdp_playwright_sender.py
      - tests/test_cdp_write_adapter.py
      - tasks/cdp-review-security-rereview-r1.md
      - _evidence/CDP-REVIEW-SECURITY-REREVIEW-R1/**
      - _reports/cdp-review-security-rereview-r1/**
    protected_files_touched: false
    conflict_level: low
  ```

- **Acceptance Gates**:
  1. Empty or ambiguous reviewer resolution fails closed at CLI and API boundaries.
  2. Suspicious report content is never dispatched automatically.
  3. URL conversation identity is parsed exactly, not matched by substring.
  4. Actual target identity is obtained from CDP and compared with expected binding.
  5. Evidence hashes use full SHA-256 digests.
  6. Real-path regression tests expose each original failure mode.
  7. Targeted and canonical test suites pass without new warnings.
  8. Execution report and Reviewer Index list exact evidence and known gaps.

- **Expected Output**: Minimal security correction, regression tests, and auditable report artifacts.
- **Rollback**: Revert only the files listed in write_set.
- **Report To**: Current session
