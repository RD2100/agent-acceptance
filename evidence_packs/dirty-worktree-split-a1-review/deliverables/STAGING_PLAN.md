# DIRTY-WORKTREE-SPLIT-A1 Staging Plan

task_id: DIRTY-WORKTREE-SPLIT-A1
source_review: evidence_packs/dirty-worktree-review-20260607/GPT_REVIEW_RESULT_PASTED.txt
review_verdict: triage_only
created_from: DIRTY-WORKTREE-REVIEW-20260607

## Decision

Do not commit the current dirty worktree as one batch.

The dirty baseline contains unrelated tracked governance edits, historical run
evidence edits, generated memory output, archive hook edits, selected untracked
contracts/tests/policies, and noisy temporary/cache/evidence directories. These
must be split into separate reviewable tasks.

## Hard Blocks Before Any Commit

- Do not include `.tmpconfig/`, `.tmpdata/`, `__pycache__/`, `*.pyc`, or the
  dirty-worktree review pack itself in normal feature commits.
- Do not commit `HANDOFF_REPLY_V4.txt` deletion without a separate
  archive-governance task or a safe restore/isolation decision.
- Do not commit direct edits to `runs/*/POST_REVIEW_ROUTE.json`; use sidecar
  correction or append-only project/ledger notes if correction is needed.
- Do not mix archive hook governance changes with unrelated code or policy work.
- Do not mix `tools/ai_guard.py`, `tools/go_evidence.py`, and
  `schemas/agent-runtime/chain-evidence.schema.json` with low-risk backfill.

## Recommended Commit Groups

### GROUP-01: AA-FLOW-RUNNER-CONTRACT-BACKFILL

Status: coherent candidate.

Files:
- `contracts/DISPATCH_RESULT.schema.json`
- `contracts/FLOW_OUTCOME.schema.json`
- `contracts/RUNNER_CONTRACT.schema.json`
- `contracts/RUNNER_STATE.schema.json`
- `contracts/RUNNER_STEP_RESULT.schema.json`
- `contracts/TASKSPEC.schema.json`
- `contracts/README.md`
- `policies/*.md`
- `tests/test_dispatch_result_schema.py`
- `tests/test_flow_outcome_schema.py`
- `tests/test_taskspec_schema.py`
- `tests/test_runner_contract_schema.py`
- `tests/test_runner_state_schema.py`
- `tests/test_runner_step_result_schema.py`
- `tests/test_dispatcher_policy.py`
- `tests/test_next_taskspec_consumption_policy.py`
- `tests/test_run_until_terminal_policy.py`
- `tests/test_terminal_state_policy.py`
- `tests/fixtures/*.json`

Required evidence:
- Dedicated TaskSpec marking this as backfill if historically accepted.
- Targeted tests for all listed schema/policy test files.
- Full test output.
- Evidence pack with actual deliverables, diff, manifest, hash, safety scan,
  and GPT review.

### GROUP-02: PAPER-A3-VALIDATOR-RESIDUAL

Status: coherent candidate, requires hash/diff check.

Files:
- `scripts/validate_paper_task.py`
- `tests/test_paper_task_validator.py`

Required evidence:
- Compare against accepted PAPER-A3 R2 evidence pack files.
- Confirm no real paper text, raw paper text, or user private text.
- Run paper validator targeted tests.
- Submit as PAPER-A3 residual/binding cleanup, not mixed with governance.

### GROUP-03: MEMORY-A2-COMPILER-OUTPUT

Status: coherent candidate, generated output.

Files:
- `memory/daily/2026-06-06.md`
- `memory/knowledge/index.md`

Required evidence:
- Confirm source review/ledger records exist.
- Run memory lint.
- Confirm no real paper text, user private text, or raw transcript.
- Prefer regeneration under a formal memory task if reproducible.

### GROUP-04: AGENT-RUNTIME-CAPABILITY-CLEANUP

Status: needs separate review.

Files:
- `docs/agent-runtime/capability-inventory.md`
- `docs/agent-runtime/routing-matrix-summary.md`
- `audit/blackboard-cleanup-audit-20260531.md`

Required evidence:
- State whether Blackboard MCP is permanently removed or phase-disabled.
- Prove this is not weakening active guards.
- Keep separate from archive hook forbidden-logic changes.

### GROUP-05: CHAIN-EVIDENCE-HARDENING

Status: high risk candidate.

Files:
- `schemas/agent-runtime/chain-evidence.schema.json`
- `tools/ai_guard.py`
- `tools/go_evidence.py`
- `.ai/tasks/t-chain-evidence-hardening-20260601.yaml`
- `.ai/tasks/t-rerun-chain-evidence-guard-20260601.yaml`
- `.ai/tasks/t-review-chain-evidence-hardening-20260601.yaml`
- `.ai/tasks/t-review-rerun-chain-evidence-guard-20260601.yaml`

Required evidence:
- Targeted tests for reviewer fields, rerun verification, rerun summary, and
  final batch status synthesis.
- Negative tests for missing reviewer fields, invalid datetime, unexpected
  fields, stale rerun, and missing/invalid reviewer verdict.
- Proof `ai_guard` fails closed, not silently warns.
- Dedicated GPT review before commit.

### GROUP-06: VALIDATE-WORKFLOW-CLOSURE-CONTROL-PLANE-PATTERN

Status: small coherent candidate.

Files:
- `scripts/validate_workflow_closure.py`

Required evidence:
- Test coverage that `control_plane/` counts as an actual deliverable.
- Submit as a small validator hardening task.

### GROUP-07: AI-TASKS-BACKLOG

Status: metadata candidate.

Files:
- `.ai/tasks/*.yaml`

Required evidence:
- Classify each task as historical, active, superseded, or ready_for_review.
- Do not delete or move stale tasks; mark superseded if needed.
- Commit separately as task registry/backlog update.

### GROUP-08: SUBMIT-PROPOSAL-TO-GPT

Status: needs path decision.

Files:
- `docs/submit_proposal_to_gpt.py`

Required evidence:
- Decide whether it is documentation example or executable script.
- If executable, move to `scripts/` only under a separate authorized task.
- If historical example, do not commit it as production docs.

## Immediate Safe Next Step

Start with GROUP-01 only after freezing the baseline and confirming no historical
evidence edits are staged. GROUP-01 has the clearest boundary and the most
complete apparent test coverage.

Do not stage any file outside the selected group for the next commit.

