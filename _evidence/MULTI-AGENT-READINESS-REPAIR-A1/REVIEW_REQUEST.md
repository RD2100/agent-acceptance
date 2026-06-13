# Independent Review Request

run_id: {{RUN_ID}}
task_id: {{TASK_ID}}

You are the independent reviewer. Treat executor summaries as claims, not facts.

Review the attached `diff.patch` and these raw artifacts:

- `02-target-tests.txt`
- `03-full-tests.txt`
- `04-preflight-cli.txt`
- `05-plan-validator.txt`
- `06-diff-check.txt`
- `07-ai-guard.txt`
- `safety-report.json`
- `chain-evidence.json`
- `REVIEWER_INDEX.md`

Focus on fake-green resistance, authorization freshness, evidence-path traversal, READY state semantics, schema compatibility, exception handling, and executor/reviewer identity separation.

Required output:

1. Findings first, ordered P0 to P3, with file and line references.
2. Explicit verdict: `pass`, `blocked`, `fail`, or `escalate`.
3. A YAML block with:

```yaml
reviewer_role: reviewer
reviewer_id: chatgpt-conversation-6a297f76-3e7c-83a5-a0e5-b4413d923c7e
executor_id: codex-desktop-multi-agent-readiness-repair-a1
run_id: {{RUN_ID}}
task_id: {{TASK_ID}}
overall_judgment: accepted | accepted_with_limitation | blocked | review_unverified
verdict: pass | blocked | fail | escalate
reviewed_inputs:
  - diff.patch
  - 02-target-tests.txt
  - 03-full-tests.txt
  - safety-report.json
  - chain-evidence.json
findings: []
```

Do not approve merely because tests pass. Block on any unresolved P0/P1 finding.

End the complete response with this exact marker:

END_OF_GPT_RESPONSE
