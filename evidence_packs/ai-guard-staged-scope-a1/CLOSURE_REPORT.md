# CLOSURE REPORT — AI-GUARD-STAGED-SCOPE-A1

```yaml
task_id: AI-GUARD-STAGED-SCOPE-A1
task_name: "Fix ai_guard pre-commit scope to staged-files-only"
final_status: ready_for_review
review_round: R3
```

## Summary

Fixed ai_guard.py so that `task` mode scans ONLY staged files for all checks (scope, deny, restrict, secrets). Dirty unstaged files no longer block clean staged commits. Added separate `audit` mode for full-tree security scans. Added `--root` flag for test fixture support.

## Changes

### tools/ai_guard.py
- `task` mode: `git_staged_files()` (staged only) for ALL checks
- New `audit` mode: `git_changed_files()` (full tree) for repo-wide audits
- Added `--root` CLI flag for testability
- Guard NOT disabled. NOT weakened. Fail-closed preserved.

### tests/test_ai_guard_staged_scope.py (new, 7 tests)
- unstaged secret does NOT block clean staged commit → PASS
- staged forbidden marker BLOCKS commit → PASS
- task mode ignores unstaged secret → PASS
- audit mode catches working-tree secret → PASS
- 3 structural fail-closed checks → PASS

## Verification

| Check | Result |
|-------|--------|
| Task mode: staged only | YES (0 errors with CONTEXT-COMPRESSION-A1 TaskSpec) |
| Audit mode: full tree | YES (separate mode, not mixed with commit) |
| Targeted tests | 7 PASS |
| Full test suite | 239 PASS |
| Guard disabled | NO |
| Guard weakened to warning | NO |
| Dirty baseline touched | NO |
