# TaskSpec: CDP-REVIEW-SECURITY-CLOSURE-R2

- **ID**: CDP-REVIEW-SECURITY-CLOSURE-R2
- **Batch**: cdp-review-security-closure
- **Risk**: high
- **Priority**: P1
- **Goal**: Close the remaining CDP target-spoofing, ambiguous response-capture, clipboard-residue, and reporting-integrity findings after commit b3311061.
- **Context**: Independent rereview proved that a non-ChatGPT URL containing `chatgpt.com/c/<id>` was accepted as a reviewer target and that capture selected the first prefix match.
- **Allowed Files**:
  - scripts/cdp_write_adapter.py
  - scripts/cdp_review_api.py
  - scripts/cdp_playwright_sender.py
  - tests/test_cdp_write_adapter.py
  - _reports/SECURITY-HARDENING-REPORT-20260613.md
  - _evidence/CDP-REVIEW-SECURITY-REREVIEW-R1/EXECUTION_REPORT.md
  - tasks/cdp-review-security-rereview-r1.md
  - tasks/cdp-review-security-closure-r2.md
  - _evidence/CDP-REVIEW-SECURITY-CLOSURE-R2/**
- **Forbidden**:
  - No external CDP or ChatGPT runtime execution
  - No mutation of activation records, live-session evidence, or prior GPT responses
  - No destructive git operations or dependency changes

- **Gate 0 Ledger**:
  ```yaml
  gate_0:
    triggered: true
    trigger_reason: "P1 security closure after commit-level rereview"
    inventory_evidence:
      queried_sources:
        - scripts/cdp_write_adapter.py
        - scripts/cdp_review_api.py
        - scripts/cdp_playwright_sender.py
        - tests/test_cdp_write_adapter.py
        - _reports/SECURITY-HARDENING-REPORT-20260613.md
      matched_capabilities:
        - cdp_target_resolution
        - review_response_capture
        - evidence_integrity
      compared_against_request:
        - "Reject non-ChatGPT target spoofing"
        - "Reject ambiguous or unbound response capture"
        - "Remove review prompt from the system clipboard"
        - "Correct false-green report claims"
    rules_checked: [core-004, core-008, sec-002, review-001]
    sufficiency_decision: existing_sufficient
    decision: reuse
    delta_justification: "Centralize URL validation at the existing CDPPage boundary and reuse unique reviewer resolution."
  ```

- **Conflict Registry**:
  ```yaml
  conflict_registry:
    read_set:
      - scripts/cdp_write_adapter.py
      - scripts/cdp_review_api.py
      - scripts/cdp_playwright_sender.py
      - tests/test_cdp_write_adapter.py
      - _reports/SECURITY-HARDENING-REPORT-20260613.md
      - _evidence/CDP-REVIEW-SECURITY-REREVIEW-R1/EXECUTION_REPORT.md
    write_set:
      - scripts/cdp_write_adapter.py
      - scripts/cdp_review_api.py
      - scripts/cdp_playwright_sender.py
      - tests/test_cdp_write_adapter.py
      - _reports/SECURITY-HARDENING-REPORT-20260613.md
      - _evidence/CDP-REVIEW-SECURITY-REREVIEW-R1/EXECUTION_REPORT.md
      - tasks/cdp-review-security-rereview-r1.md
      - tasks/cdp-review-security-closure-r2.md
      - _evidence/CDP-REVIEW-SECURITY-CLOSURE-R2/**
    protected_files_touched: false
    conflict_level: low
  ```

- **Acceptance Gates**:
  1. Non-ChatGPT URLs cannot produce a conversation ID or enter target discovery.
  2. Response capture requires one prefix match and the verified reviewer target.
  3. The system clipboard is cleared after paste, including failure paths.
  4. Existing legitimate ChatGPT URLs and unique capture continue to work.
  5. The original PoCs no longer reproduce through production entry points.
  6. Targeted tests pass with RuntimeWarning treated as error.
  7. Reports state exact commit scope and test results without fake green.
  8. Canonical regression result and external-runtime proof gaps are recorded honestly.

- **Expected Output**: Minimal code fixes, real-path regression tests, corrected reports, and closure evidence.
- **Rollback**: Revert only the files listed in write_set.
- **Report To**: Current session
