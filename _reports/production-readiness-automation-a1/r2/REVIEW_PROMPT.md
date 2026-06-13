INDEPENDENT R2 REVIEW REQUEST: PRODUCTION-READINESS-AUTOMATION-A1

run_id: {{RUN_ID}}
task_id: {{TASK_ID}}

R1 verdict was blocked. The two accepted P1 findings were:
1. Status-only synthetic runner JSON could satisfy local readiness.
2. Gate 0 and dispatch artifacts had no enforced freshness timestamp.

Review the attached R2 pack and verify the fixes rather than trusting this
summary. Specifically attempt to bypass:

- exact task-runner task ID, command, target file, exit code, and decisive
  output-marker checks for all three local probes;
- Gate 0 and dispatch `generated_at` checks for missing, stale, future,
  malformed, contradictory, and repo-escaping evidence;
- pilot binding to exact Gate 0 and dispatch SHA256 values;
- distinct sessions, referenced live-session evidence, independent reviewer,
  and post-pilot production authorization.

Confirm the current machine results remain honest:
- local_governance: READY
- controlled_pilot: HUMAN_REQUIRED
- formal_use: HUMAN_REQUIRED

Return this exact YAML-like block and end marker:

run_id: {{RUN_ID}}
task_id: {{TASK_ID}}
overall_judgment: accepted | accepted_with_limitation | blocked | review_unverified
evidence_pack_reviewed: true | false
attachment_reviewed: true | false
blocking_issues:
  - <P0/P1 issue or none>
required_fixes:
  - <required fix or none>
limitations:
  - <non-blocking limitation or none>
next_task_authorization:
  task_id: CONTROLLED-MULTI-GPT-PILOT-A1
  authorized: no
  execute_immediately: no
  ask_before_starting: yes
END_OF_GPT_RESPONSE
