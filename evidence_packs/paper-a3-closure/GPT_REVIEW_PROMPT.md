# GPT Review Prompt — PAPER-A3

Please review the attached PAPER-A3 evidence pack.

Expected judgment fields:
- overall_judgment: accepted | blocked | review_unverified
- blocking_reasons
- required_next_action
- allow_proceed
- next_task_authorization if accepted
- required_fixes and resubmission_requirements if blocked

Review focus:
1. Does scripts/validate_paper_task.py formally enforce PAPER-A2 paper task input/output/privacy boundaries?
2. Does it fail closed for real_paper_full_text, unauthorized excerpts, output leaks, forbidden raw payload keys, and missing privacy files?
3. Are tests/test_paper_task_validator.py sufficient real-path tests of both function and CLI behavior?
4. Is this evidence pack non-summary-only and internally verifiable?

This task is not closed unless GPT returns accepted and the ledger is updated.
END_OF_GPT_RESPONSE
