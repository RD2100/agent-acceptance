# GPT Review Prompt - PAPER-C1

Please review this evidence pack for PAPER-C1.

Expected review output:

overall_judgment: accepted | blocked
reviewer_type: gpt
task_id: PAPER-C1
review_run_id: paper-c1-real-paper-pilot-safety-protocol-review-v1
primary_repo: agent-acceptance
evidence_pack_reviewed: true
blocking_issues: []
required_fixes: []

Review criteria:

1. PAPER-C1 remains protocol-only and does not enable real-paper execution.
2. The protocol explicitly blocks real paper full text, user private text, memory writes containing paper content, external upload, live CDP, and historical evidence cleanup.
3. The contract is machine-readable and fail-closed.
4. Negative privacy fixtures use synthetic placeholders only.
5. Tests cover protocol, contract, authorization, fixture safety, and fail-closed mapping.
6. Evidence pack includes actual deliverables, tests, outputs, diff, manifest, safety attestation, and the PAPER-B2 GPT authorization for PAPER-C1.
7. The closure report does not self-close; final_status must remain ready_for_review until GPT accepted and ledger binding happen.

Please also provide next_task_authorization if accepted.
