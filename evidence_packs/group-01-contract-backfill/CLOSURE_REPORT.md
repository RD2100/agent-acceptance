task_id: GROUP-01
task_name: AA-FLOW-RUNNER-CONTRACT-BACKFILL
primary_repo: agent-acceptance
review_origin: DIRTY-WORKTREE-SPLIT-A1 accepted
status: ready_for_review
final_status: ready_for_review
backfill: true

# GROUP-01 Closure Report

This evidence pack isolates GROUP-01 from the dirty worktree as a reviewable backfill unit.
It does not stage or commit the whole dirty tree, and it does not mutate historical evidence.

Scope:
- flow / runner / taskspec contract backfill
- policies backfill
- schema/policy fixtures and tests

Explicit non-scope:
- runs/*/POST_REVIEW_ROUTE.json changes
- HANDOFF_REPLY_V4.txt deletion
- archive/draft-hooks changes
- tools/ai_guard.py, tools/go_evidence.py, chain-evidence schema changes
- memory outputs
- paper validator residual files
- tmp/cache/root scratch files

Verification:
- TARGETED_TEST_OUTPUT.txt: targeted GROUP-01 tests, 60 passed, no warnings from GROUP-01 test files.
- FULL_TEST_OUTPUT.txt / TEST_OUTPUT.txt: full test suite, 170 passed, 21 warnings; remaining warnings come from non-GROUP-01 legacy tests.
- BYPASS_CHECK_OUTPUT.txt: GROUP-01 selected-files-only bypass pass.
- BYPASS_SCOPE_NOTE.txt: documents why bypass evidence is scoped to selected files.
- NO_HISTORICAL_EVIDENCE_MUTATION.txt: forbidden historical evidence not staged.
- NO_WHOLE_DIRTY_TREE_COMMIT.txt: staged set restricted to GROUP-01.

Backfill note:
- This pack should be reviewed as historical/backfill capability capture, not as a brand-new unrelated feature.
