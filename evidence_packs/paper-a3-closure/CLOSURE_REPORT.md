# PAPER-A3 Closure Report

Status: ready_for_gpt_review
Task: PAPER-A3 — paper task validator formal integration

## Changed Files

- scripts/validate_paper_task.py
- tests/test_paper_task_validator.py

## Summary

Added a local paper task validator for PAPER-A2 bundles. The validator accepts a directory or ZIP containing PAPER_TASK_INPUT.yaml, PAPER_TASK_OUTPUT.yaml, PRIVACY_ATTESTATION.yaml, and REDACTION_REPORT.yaml. It returns structured JSON and exits nonzero on blocking issues.

## Fail-Closed Coverage

- Blocks real_paper_full_text input.
- Blocks user_authorized_excerpt without explicit authorization.
- Blocks output privacy leak flags.
- Blocks forbidden payload keys such as raw_paper_text and paper_content.
- Blocks missing privacy attestation or redaction report files.
- Validates task_id/task_type consistency across the bundle.

## Important Boundary

This implementation does not mark PAPER-A3 closed. closed still requires GPT accepted plus ledger entry.
