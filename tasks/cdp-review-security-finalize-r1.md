# TaskSpec: CDP-REVIEW-SECURITY-FINALIZE-R1

- **ID**: CDP-REVIEW-SECURITY-FINALIZE-R1
- **Batch**: cdp-review-security-closure
- **Risk**: high
- **Priority**: P1
- **Goal**: Persist independent reviewer evidence, reconcile the active task boundary, and prepare the completed CDP security closure for a scoped commit.
- **Context**: CDP-REVIEW-SECURITY-CLOSURE-R2 finished its implementation and deterministic checks. An independent reviewer has now returned a pass verdict with one P3 residual risk.
- **Allowed Files**:
  - .ai/current-task.yaml
  - scripts/cdp_write_adapter.py
  - scripts/cdp_review_api.py
  - scripts/cdp_playwright_sender.py
  - tests/test_cdp_write_adapter.py
  - _reports/SECURITY-HARDENING-REPORT-20260613.md
  - _evidence/CDP-REVIEW-SECURITY-REREVIEW-R1/EXECUTION_REPORT.md
  - _evidence/CDP-REVIEW-SECURITY-CLOSURE-R2/**
  - _evidence/CDP-REVIEW-SECURITY-FINALIZE-R1/**
  - tasks/cdp-review-security-rereview-r1.md
  - tasks/cdp-review-security-closure-r2.md
  - tasks/cdp-review-security-finalize-r1.md
  - hooks/sealed-files-manifest.json
  - _evidence/hook-output/**
- **Forbidden**:
  - No external CDP or ChatGPT runtime execution
  - No activation-record or live-session-evidence mutation
  - No destructive Git operations

- **Gate 0 Ledger**:
  ```yaml
  gate_0:
    triggered: true
    trigger_reason: "Finalize P1 security closure with independent reviewer artifacts"
    inventory_evidence:
      queried_sources:
        - tasks/cdp-review-security-closure-r2.md
        - _evidence/CDP-REVIEW-SECURITY-CLOSURE-R2/EXECUTION_REPORT.md
        - _evidence/CDP-REVIEW-SECURITY-CLOSURE-R2/REVIEWER_INDEX.md
      matched_capabilities:
        - independent_security_review
        - cdp_target_resolution
        - evidence_integrity
    rules_checked: [core-004, core-008, review-001]
    sufficiency_decision: existing_sufficient
    decision: reuse
    delta_justification: "No code delta; persist independent review and exact final status."
  ```

- **Conflict Registry**:
  ```yaml
  conflict_registry:
    read_set:
      - scripts/cdp_write_adapter.py
      - scripts/cdp_review_api.py
      - scripts/cdp_playwright_sender.py
      - tests/test_cdp_write_adapter.py
      - _evidence/CDP-REVIEW-SECURITY-CLOSURE-R2/EXECUTION_REPORT.md
      - _evidence/CDP-REVIEW-SECURITY-CLOSURE-R2/REVIEWER_INDEX.md
    write_set:
      - .ai/current-task.yaml
      - scripts/cdp_write_adapter.py
      - scripts/cdp_review_api.py
      - scripts/cdp_playwright_sender.py
      - tests/test_cdp_write_adapter.py
      - _reports/SECURITY-HARDENING-REPORT-20260613.md
      - _evidence/CDP-REVIEW-SECURITY-REREVIEW-R1/EXECUTION_REPORT.md
      - _evidence/CDP-REVIEW-SECURITY-CLOSURE-R2/**
      - _evidence/CDP-REVIEW-SECURITY-FINALIZE-R1/**
      - tasks/cdp-review-security-rereview-r1.md
      - tasks/cdp-review-security-closure-r2.md
      - tasks/cdp-review-security-finalize-r1.md
      - hooks/sealed-files-manifest.json
      - _evidence/hook-output/**
    protected_files_touched: false
    conflict_level: low
  ```

- **Acceptance Gates**:
  1. Reviewer evidence identifies a separate reviewer and the reviewed inputs.
  2. Reviewer verdict contains no unresolved P0/P1 finding.
  3. Execution Report and Reviewer Index state the exact test and review outcomes.
  4. The scoped staged diff contains no unrelated historical artifacts.
  5. Commit-time governance hooks pass.

- **Expected Output**: `review.md`, `review.yaml`, reconciled reports, and one scoped security closure commit.
- **Rollback**: Revert only the files listed in the write set.
- **Report To**: Current session
