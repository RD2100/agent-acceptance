INDEPENDENT REVIEW REQUEST: PRODUCTION-READINESS-AUTOMATION-A1

run_id: {{RUN_ID}}
task_id: {{TASK_ID}}

Review the attached evidence pack as an independent P0/P1 reviewer. Do not
trust narrative claims. Verify the implementation, tests, raw runner probes,
current Gate 0/dispatch artifacts, and readiness outputs.

Review focus:
1. Can local_governance become READY without current canonical tests and all
   three real task-runner probes?
2. Can controlled_pilot or formal_use become READY with missing, stale,
   malformed, contradictory, repo-escaping, or hash-mismatched evidence?
3. Does formal_use require two distinct sessions, existing session evidence,
   independent reviewer identity, exact Gate 0/dispatch hashes, and a current
   post-pilot production authorization?
4. Are current outputs honest: local_governance READY, controlled_pilot
   HUMAN_REQUIRED, formal_use HUMAN_REQUIRED?
5. Identify any unresolved P0/P1 security, fake-green, path traversal,
   timestamp, or authority-boundary defect.

Protected-document debt (CAP-009 numbering and cumulative-trigger wording) is
deliberately not edited because the task runner requires an exclusive lock
that is not available in this batch. Judge whether this is correctly excluded
from positive readiness evidence.

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
