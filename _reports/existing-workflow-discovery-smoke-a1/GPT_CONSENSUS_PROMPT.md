GPT CONSENSUS REQUEST: NEXT AGENT WORKFLOW BOOTSTRAP

run_id: NEXT_AGENT_WORKFLOW_BOOTSTRAP_CONSENSUS_20260608_235000_RD

task_id: NEXT-AGENT-WORKFLOW-BOOTSTRAP-CONSENSUS-A1

Context:
A Claude Code agent previously summarized the project workflow mostly from conversation context. The user correctly pointed out that the agent only formally read the repository workflow files later during EXISTING-WORKFLOW-DISCOVERY-SMOKE-A1.

User question:
How can we ensure the next handoff/maintenance agent directly reads the complete existing workflow at startup, instead of relying on conversation context or reinventing the process?

Known project constraints:
- Default language for user-facing docs/reports/runbooks: Chinese.
- Current project directory: D:/agent-acceptance.
- Every Bash command must explicitly begin with: cd "D:/agent-acceptance" && ...
- Do not redesign GPT-agent handoff workflow.
- Reuse existing files/processes:
  - HANDOFF_SOURCE_OF_TRUTH.md
  - HANDOFF_APPROVAL_RECORD.json
  - _reports/handoff-pipeline-refactor-a1/ATTACHMENT_BACKED_GPT_REVIEW_RUNBOOK.md
  - scripts/verify_gpt_reply.py
  - scripts/gpt_new_chat_attachment_submit.py
  - scripts/pre_gpt_review_gate.py
  - scripts/evidence_pack_linter.py
  - _reports/global-project-handoff-repair-a1/GPT_REVIEW_RECORD.json
  - _reports/global-project-handoff-repair-a1/VERIFY_GPT_REPLY_OUTPUT.txt
  - _reports/global-project-handoff-repair-a1/PRE_GPT_GATE_OUTPUT.txt
  - _reports/global-project-handoff-repair-a1/EXECUTION_REPORT.md
  - _reports/global-project-handoff-repair-a1/PACK_MANIFEST.md
  - _reports/global-project-handoff-repair-a1/WHOLE_PROJECT_SOURCE_OF_TRUTH_MAP.json
  - _reports/global-project-handoff-repair-a1/WHOLE_PROJECT_STALE_CLAIMS_REGISTER.json
  - _reports/global-project-handoff-repair-a1/WHOLE_PROJECT_TEST_LEDGER.json
  - _reports/global-project-evidence-binding-a1/GPT_REVIEW_RESULT.txt
  - _reports/global-project-evidence-binding-a1/VERIFY_GPT_REPLY_OUTPUT.txt
  - _reports/global-project-evidence-binding-a1/PACK_MANIFEST.md
  - _reports/global-project-evidence-binding-a1/EXECUTION_REPORT.md
  - _reports/global-project-evidence-binding-a1/CHANGED_FILES_EVIDENCE.json
  - _reports/global-project-evidence-binding-a1/PROTECTED_LEGACY_FILES_STATUS.json
  - _reports/global-project-evidence-binding-a1/SOURCE_MAP_EVIDENCE_BINDING_APPENDIX.json
- Non-trivial tasks must auto-submit GPT review once ready_for_gpt_review.
- Only irreversible/high-risk operations should ask user confirmation.
- Do not delete/move/rename/rewrite legacy PROJECT_HISTORY / HANDOFF / PASTE_BLOCK files.
- No git reset/clean/checkout/commit/push without explicit user approval.

Please propose a consensus plan with two parts:

A. Minimal durable mechanism so the next agent is forced/strongly guided to read the full workflow directly from repo files before summarizing or executing.
B. Exact implementation steps Claude Code should perform now, using only safe local reversible changes unless clearly marked human_required.

Prefer reuse over new construction. If a new small file is necessary, justify why existing components are insufficient.

Return ONLY this block:

run_id: NEXT_AGENT_WORKFLOW_BOOTSTRAP_CONSENSUS_20260608_235000_RD
task_id: NEXT-AGENT-WORKFLOW-BOOTSTRAP-CONSENSUS-A1
overall_judgment: accepted | accepted_with_limitation | blocked | review_unverified
consensus_reached: true | false
recommended_mechanism: <short name>
reuse_components:
  - <existing component>
new_artifacts_if_any:
  - <path or none>
implementation_steps:
  - <step>
human_required_steps:
  - <step or none>
risk_controls:
  - <control>
acceptance_criteria:
  - <criterion>
limitations:
  - <limitation or none>
next_task_authorization:
  task_id: NEXT-AGENT-WORKFLOW-BOOTSTRAP-IMPLEMENT-A1 | none
  authorized: 已授权 | 未授权
  execute_immediately: 是 | 否
  ask_before_starting: 是 | 否
END_OF_GPT_RESPONSE
