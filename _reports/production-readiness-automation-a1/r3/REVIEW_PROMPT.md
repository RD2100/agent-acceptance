INDEPENDENT R3 REVIEW REQUEST: PRODUCTION-READINESS-AUTOMATION-A1

run_id: {{RUN_ID}}
task_id: {{TASK_ID}}

R1 and R2 both returned blocked. This R3 pack should be reviewed only against
the remaining R2 blockers:

1. READY dispatch could rely on a nested source_preflight that was not bound to
   the current Gate 0 artifact.
2. formal_use could rely on timestamp-less or stale live-session evidence.

Verify from the attachment that:
- scripts/multi_agent_dispatch_plan.py records source_preflight path, SHA256,
  and generated_at.
- schemas/agent-runtime/multi-agent-dispatch-plan.schema.json requires those
  fields.
- scripts/production_readiness_gate.py validates source_preflight path,
  SHA256, generated_at, overall, human_gate_required, and read-only status
  against the separately supplied preflight file.
- scripts/production_readiness_gate.py validates session evidence verified_at,
  freshness, future timestamps, and mismatch against pilot agent_sessions.
- tests cover repo-escaping, hash mismatch, path mismatch, stale/missing/future/
  malformed dispatch/preflight/session evidence.
- Current outputs remain honest: local_governance READY, controlled_pilot
  HUMAN_REQUIRED, formal_use HUMAN_REQUIRED.

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
