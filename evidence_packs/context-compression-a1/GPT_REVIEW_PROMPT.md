# GPT Review Prompt — CONTEXT-COMPRESSION-A1

Please review the attached CONTEXT-COMPRESSION-A1 evidence pack.

## Review focus:
- Verify the implementation creates a privacy-safe context compression layer.
- Verify BOOT_CONTEXT.md exists and is 3000-6000 characters for cold start use.
- Verify memory/index.md, memory/tasks, and memory/knowledge are generated as structured compressed context, not raw transcript.
- Verify scripts/compress_project_context.py, scripts/build_boot_context.py, and scripts/validate_context_memory.py are included and functional.
- Verify privacy guard fails closed for raw_paper_text, private_user_text, raw_transcript, secrets/tokens, and real paper content.
- Verify tests pass (35 new tests + full suite 216 = no regressions).
- Verify the pack is not summary-only and includes actual deliverables (scripts + generated outputs + tests).
- Verify no dirty baseline files are included.

## Expected structured output:
```yaml
overall_judgment: accepted|blocked
reviewer_type: gpt
task_id: CONTEXT-COMPRESSION-A1
evidence_pack_reviewed: true
blocking_issues: []
required_fixes: []
next_task_authorization:
  authorized: yes|no
  execute_immediately: yes|no
  ask_before_starting: yes|no
```

End with END_OF_GPT_RESPONSE.
