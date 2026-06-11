# GPT Review Prompt — PAPER-A3 R2

Please review the attached PAPER-A3 R2 evidence pack.

Expected judgment fields:
- overall_judgment: accepted | blocked | review_unverified
- blocking_reasons
- required_next_action
- allow_proceed
- next_task_authorization if accepted
- required_fixes and resubmission_requirements if blocked

R2 review focus:
1. Did R2 resolve PAPER-A3-BLOCKER-01 by including the actual test files corresponding to TARGETED_TEST_OUTPUT.txt?
2. Did R2 resolve PAPER-A3-BLOCKER-02 by including validator schema dependencies and synthetic fixtures?
3. Did R2 resolve PAPER-A3-BLOCKER-03 by adding negative tests for missing REDACTION_REPORT, output missing evidence_basis, output claims accepted/closed, paper_content memory write, paper_excerpt memory write, citation_original_text memory write, and external_upload enabled?
4. Does scripts/validate_paper_task.py formally enforce PAPER-A2 paper task input/output/privacy boundaries?
5. Is this evidence pack non-summary-only and internally verifiable?

This task is not closed unless GPT returns accepted and the ledger is updated.
END_OF_GPT_RESPONSE
