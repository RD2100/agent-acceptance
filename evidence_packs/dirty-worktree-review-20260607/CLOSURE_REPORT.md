# Dirty Worktree Review Pack

task_id: DIRTY-WORKTREE-REVIEW-20260607
primary_repo: agent-acceptance
review_type: gpt_dirty_baseline_triage

Scope:
- Review current uncommitted tracked changes and selected untracked source/task/test/policy files.
- Do not mark any implementation accepted; this is triage/review guidance for dirty baseline handling.
- Identify which changes belong together, which are stale/noise, which require tests, and which must not be committed.

Included:
- TRACKED_DIRTY_DIFF.patch: full tracked dirty diff.
- tracked_current/: current copies of tracked modified files.
- tracked_deleted/: HEAD copies of tracked deleted files.
- UNTRACKED_ALL_FILES.txt: full untracked inventory.
- UNTRACKED_SELECTED_FILES.txt and untracked_selected/: selected source/spec/test/policy untracked files, excluding caches/tmp/old evidence/debug transcripts.

Safety:
- No real paper content is intentionally included.
- No browser cookies/session/profile are included.
- .tmpconfig, .tmpdata, __pycache__, pyc, previous evidence packs, and generated _reports packs are excluded from selected file content.
