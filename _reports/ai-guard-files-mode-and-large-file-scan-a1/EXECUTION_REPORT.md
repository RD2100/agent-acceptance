# Execution Report: AI-GUARD-FILES-AND-LARGE-SECRET-SCAN-A1

## Task Summary

| Field | Value |
|-------|-------|
| **Task ID** | AI-GUARD-FILES-AND-LARGE-SECRET-SCAN-A1 |
| **Priority** | P1 |
| **Source** | Codex code quality review (2026-06-12) |
| **Executor** | GPT (QoderWork session) |
| **Date** | 2026-06-12 |
| **Status** | COMPLETED |

## Scope

Fix two P1 governance bugs in `tools/ai_guard.py` identified by Codex review. Strict scope: two bugs only, no scope creep.

### P1 #1: `--files` flag silently ignored
The pre-commit hook calls `python tools/ai_guard.py --files <staged_files>`, but `main()` treated `--files` as an unknown mode name, falling through to the default full-scan (git diff) path. The explicitly passed file list was never scanned.

### P1 #2: Large files silently skipped in secret scan
`scan_secrets()` had `if full_path.stat().st_size > 1_000_000: continue`, silently skipping any file over 1MB. Secrets in large log files or data files were invisible to governance checks.

## Changes

| File | Change | Lines |
|------|--------|-------|
| `tools/ai_guard.py` | Added `run_files_mode()` function; added `--files` branch in `main()`; replaced `scan_secrets()` whole-file read with streaming line-by-line | +69/-9 |
| `tests/test_ai_guard_staged_scope.py` | Added `TestFilesMode` (6 tests), `TestLargeFileSecretScan` (2 tests), static assertion in `TestFailClosed` | +149 |
| `tests/test_hook_failure_semantics.py` | Added `test_hook_calls_ai_guard_with_files_flag` static assertion | +6 |

**Total**: 3 files, +215/-9 lines

## Implementation Detail

### Phase 1: `--files` mode (`tools/ai_guard.py`)

New function `run_files_mode(args, policy, repo_root)`:
- Normalizes backslash paths to forward slash
- Drops empty entries
- Runs `deny_paths`, `restricted_paths`, `secret_patterns` checks on listed files only
- Does NOT check TaskSpec `allow_write` (not applicable for pre-commit hook context)
- `--files` with no arguments returns PASS with "0 file(s) checked"

In `main()`, `--files` is recognized before `evidence` and before `run_diff_mode`:
```python
if mode == "--files":
    run_files_mode(args, policy, repo_root)
```

### Phase 3: Streaming secret scan (`tools/ai_guard.py`)

Replaced in `scan_secrets()`:
```python
# BEFORE: load entire file, skip if >1MB
if full_path.stat().st_size > 1_000_000:
    continue
content = f.read()
for line_number, line in enumerate(content.splitlines(), 1):

# AFTER: streaming line-by-line, no size limit
with open(str(full_path), "r", encoding="utf-8", errors="ignore") as f:
    for line_number, line in enumerate(f, 1):
```

Benefits: no memory spike on large files, no arbitrary size limit, correct line numbers for findings.

## Verification

### Tests (53 total for target files)

| Test Suite | Baseline | New | Status |
|------------|----------|-----|--------|
| `test_ai_guard_staged_scope.py` | 7 passed | +9 (TestFilesMode: 6, TestLargeFileSecretScan: 2, TestFailClosed: 1) | All 16 passed |
| `test_hook_failure_semantics.py` | 36 passed | +1 (test_hook_calls_ai_guard_with_files_flag) | All 37 passed |
| **Total** | **43** | **+10** | **53 passed** |

### Full suite regression
- 1268 passed, 2 failed (pre-existing: `test_router_10_project_stress.py` — dev-frame-writing registry status)
- Confirmed 2 failures exist on unmodified baseline (git stash + retest)
- **Zero new failures introduced**

### PoC Verification

| PoC | Command | Expected | Actual |
|-----|---------|----------|--------|
| `--files` no args | `python tools/ai_guard.py --files` | PASS, 0 file(s) checked | PASS |
| `--files` nonexistent | `python tools/ai_guard.py --files __not_real__` | PASS, 1 file(s) checked | PASS |
| `--files` real file | `python tools/ai_guard.py --files tools/ai_guard.py` | PASS, 1 file(s) checked | PASS |
| Large file secret | 1.22MB file, secret at line 25001 | Detected at line 25001 | PASS |
| py_compile | All 3 modified files | No syntax errors | PASS |
| git diff --check | Whitespace only | No errors | PASS (LF/CRLF only) |

### Hook compatibility
The pre-commit hook (`hooks/pre-commit.governance.ps1` line 110) already calls:
```powershell
$output = python $scriptPath --files $files 2>&1 | Out-String
```
No hook changes needed — `--files` is now properly handled by `ai_guard.py`.

## Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| `--files` with filenames containing spaces (PowerShell array expansion) | Low | Pre-existing PowerShell limitation; not in scope for this fix |
| Streaming scan slower than bulk read for small files | Negligible | Python file iterator is buffered; benchmark impact unmeasurable |
| Unknown mode fallthrough unchanged | None | Explicitly preserved backward compatibility; only `--files` added as special case |

## Deferred Items (not in scope)

- `WORKSPACE-CLOSURE-UNTRACKED-TRIAGE-A1` (P1)
- `HOOK-FAILURE-SEMANTICS-FINALIZE-A1` (P1)
- Root CDP script cleanup
- `build_evidence_pack.py` decomposition
- P2/P3 items from Codex review (backslash test fragility, py_compile in CI, etc.)

## Conclusion

Both P1 governance bugs are fixed with minimal, targeted changes. All 53 target tests pass. Full suite has zero new regressions. The fix is backward-compatible with existing hook infrastructure.
