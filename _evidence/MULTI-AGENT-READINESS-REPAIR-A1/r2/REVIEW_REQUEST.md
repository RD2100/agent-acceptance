# Independent Correction Review Request

run_id: {{RUN_ID}}
task_id: {{TASK_ID}}

You are the independent reviewer for correction round R2. Treat executor summaries as claims, not facts.

The attached archive includes the corrected diff.patch, raw verification artifacts, and the original blocked review as R1_REVIEW.md and R1_REVIEW.yaml.

Verify these prior findings:

1. P1-AUTH-FRESHNESS-FUTURE-APPROVAL
2. P2-TASK-PROTECTED-FILE-STATUS-MISMATCH
3. P2-SECRET-SCAN-INCOMPLETE as an explicitly preserved limitation
4. P3-MISSING-FUTURE-AUTHORIZATION-TEST

Findings must come first and include file and line references. Block on any unresolved P0/P1 issue.

Return a YAML block containing:

reviewer_role: reviewer
reviewer_id: chatgpt-conversation-6a297f76-3e7c-83a5-a0e5-b4413d923c7e
executor_id: codex-desktop-multi-agent-readiness-repair-a1
run_id: {{RUN_ID}}
task_id: {{TASK_ID}}
overall_judgment: accepted | accepted_with_limitation | blocked | review_unverified
verdict: pass | blocked | fail | escalate
reviewed_inputs:
  - diff.patch
  - R1_REVIEW.md
  - R1_REVIEW.yaml
  - 01-target-tests.txt
  - 02-full-tests.txt
  - safety-report.json
  - chain-evidence.json
findings: []

End the complete response with this exact marker:

END_OF_GPT_RESPONSE
