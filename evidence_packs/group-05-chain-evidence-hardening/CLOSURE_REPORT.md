task_id: GROUP-05
task_name: CHAIN-EVIDENCE-HARDENING
primary_repo: agent-acceptance
review_origin: DIRTY-WORKTREE-SPLIT-A1 triage
status: ready_for_review
final_status: ready_for_review

# GROUP-05 Closure Report

This pack isolates chain-evidence governance hardening.

Scope:
- schemas/agent-runtime/chain-evidence.schema.json
- tools/ai_guard.py
- tools/go_evidence.py
- tests/test_chain_evidence_hardening.py

Change intent:
- validate reviewer and rerun metadata consistently
- fail closed on malformed chain-evidence reviewer/rerun states
- write rerun metadata during finalize
- treat rerun_verified_at as ordered after created_at, not necessarily after reviewed_at
- prove the behavior with targeted negative tests and an existing run evidence probe
