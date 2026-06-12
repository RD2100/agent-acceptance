## HOOK-V241-REAL-INVOKE-PROBE-A1 -- Execution Report

**Date:** 2026-06-12
**HEAD at start:** 5eb84547
**Task type:** verification-probe
**Priority:** P1

---

### 1. Scope

Verify Hook v2.4.1 `AI_GUARD_FILE_LIST` environment variable passing under
real pre-commit hook invocation on Windows. Cover multi-file, long-path,
space-path, deny_paths blocking, and allow_paths narrow scope enforcement.

**Out of scope:** live dispatch, opencode run, external runtime, paper
workflow, hook logic modification, allow_paths expansion.

---

### 2. Probe Files Created

| File | Purpose |
|------|---------|
| `_tmp/hook-v241-probe-a1/clean.txt` | Normal clean file |
| `_tmp/hook-v241-probe-a1/long-path/sub1/sub2/sub3/sub4/clean.txt` | Deep nested path |
| `_tmp/hook-v241-probe-a1/path with spaces/clean file.txt` | Space-path handling |
| `_tmp/hook-v241-probe-a1/blocked-secret-file.txt` | deny_paths block test |
| `_tmp/hook-v241-probe-a1/secret-scan-output.txt` | allow_paths out-of-scope test |
| `_evidence/hook-v241-probe/secret-scan-output.txt` | allow_paths in-scope test |

All probe files deleted during cleanup. None remain on disk.

---

### 3. Probe Results

#### Probe 1: Pass Case (multi-file + long-path + space-path)

**Command:** `git commit -m "probe-v241: pass case (3 clean files, long-path, space-path)"`
**Exit code:** 0
**Commit:** `302ae1e` (created, then reset)

**Key output:**

```
[2/4] SADP audit...
[SADP-AUDIT] Staged files: 5
[SADP-AUDIT] V2: All 5 files covered by TaskSpec write_sets.
[SADP-AUDIT] Coverage map:
[SADP-AUDIT]   .ai/current-task.yaml -> current-task.yaml
[SADP-AUDIT]   _tmp/hook-v241-probe-a1/clean.txt -> current-task.yaml
[SADP-AUDIT]   _tmp/hook-v241-probe-a1/long-path/sub1/sub2/sub3/sub4/clean.txt -> current-task.yaml
[SADP-AUDIT]   _tmp/hook-v241-probe-a1/path with spaces/clean file.txt -> current-task.yaml
[SADP-AUDIT]   hooks/sealed-files-manifest.json -> current-task.yaml
AI Guard: 0 errors, 1 warning(s) - PASS with warnings
[SADP-AUDIT] STATUS: PASS

[3/4] Governance scan...
Summary: BLOCKED=0 ERROR=0 WARN=0 (1.7s)

[4/4] Conversation health advisory...
[ADVISORY] Conversation health OK

=== Pre-Commit PASS ===
[master 302ae1e] probe-v241: pass case (3 clean files, long-path, space-path)
 5 files changed
 create mode 100644 _tmp/hook-v241-probe-a1/clean.txt
 create mode 100644 _tmp/hook-v241-probe-a1/long-path/sub1/sub2/sub3/sub4/clean.txt
 create mode 100644 _tmp/hook-v241-probe-a1/path with spaces/clean file.txt
```

**Verdict:** PASS. Env var file passing works. Long-path (4-level deep) and
space-path both handled correctly. No command line length error. The 1
warning is `RESTRICTED: hooks/sealed-files-manifest.json requires human
review` -- expected for manifest auto-regeneration.

**Hook-output artifacts triggered:** Yes (rotating set: ai-guard, sadp-audit,
test-governance, conversation-health, latest.json modified).

---

#### Probe 2: Block Case (deny_paths secret-named file)

**Command:** `git commit -m "probe-v241: block case (deny_paths secret-named)"`
**Exit code:** 1

**Key output:**

```
[2/4] SADP audit...
[SADP-AUDIT] Staged files: 3
[SADP-AUDIT] Coverage map:
[SADP-AUDIT]   .ai/current-task.yaml -> current-task.yaml
[SADP-AUDIT]   _tmp/hook-v241-probe-a1/blocked-secret-file.txt -> current-task.yaml
[SADP-AUDIT]   hooks/sealed-files-manifest.json -> current-task.yaml
ERROR: DENIED: _tmp/hook-v241-probe-a1/blocked-secret-file.txt is on deny list
AI Guard: 1 error(s), 1 warning(s) - BLOCKED
[SADP-AUDIT] ai_guard.py found security issues.
[SADP-AUDIT] STATUS: BLOCKED
[BLOCKED] sadp-audit failed (exit=1). Fix issues before commit.
```

**Verdict:** PASS (correctly blocked). `blocked-secret-file.txt` matched
`*secret*` in deny_paths. No false PASS produced.

**Hook-output artifacts triggered:** Yes (sadp-audit timestamp file created).

---

#### Probe 3: allow_paths Narrow Scope (out-of-scope secret-named file)

**Command:** `git commit -m "probe-v241: allow_paths narrow (out-of-scope secret file)"`
**Exit code:** 1

**Key output:**

```
[2/4] SADP audit...
[SADP-AUDIT] Staged files: 3
[SADP-AUDIT] Coverage map:
[SADP-AUDIT]   .ai/current-task.yaml -> current-task.yaml
[SADP-AUDIT]   _tmp/hook-v241-probe-a1/secret-scan-output.txt -> current-task.yaml
[SADP-AUDIT]   hooks/sealed-files-manifest.json -> current-task.yaml
ERROR: DENIED: _tmp/hook-v241-probe-a1/secret-scan-output.txt is on deny list
AI Guard: 1 error(s), 1 warning(s) - BLOCKED
[SADP-AUDIT] STATUS: BLOCKED
[BLOCKED] sadp-audit failed (exit=1). Fix issues before commit.
```

**Verdict:** PASS (correctly blocked). `_tmp/` is not in allow_paths scope
(allow_paths only covers `_evidence/**` and `_archive/**`). The narrow
scope enforcement works as designed per DR-20260612-ALLOW-PATHS.

**Hook-output artifacts triggered:** Yes (sadp-audit timestamp file created).

---

#### Probe 4: allow_paths Positive + Two-Layer Enforcement

**Command:** `git commit -m "probe-v241: allow_paths positive (evidence secret-scan-output.txt)"`
**Exit code:** 1

**Key output:**

```
[2/4] SADP audit...
[SADP-AUDIT] Staged files: 3
[SADP-AUDIT] Coverage map:
[SADP-AUDIT]   .ai/current-task.yaml -> current-task.yaml
[SADP-AUDIT]   _evidence/hook-v241-probe/secret-scan-output.txt -> current-task.yaml
[SADP-AUDIT]   hooks/sealed-files-manifest.json -> current-task.yaml
AI Guard: 0 errors, 1 warning(s) - PASS with warnings
[SADP-AUDIT] ai_guard.py TaskSpec scope scan:
  _evidence/hook-v241-probe/secret-scan-output.txt NOT in any TaskSpec write_set
[SADP-AUDIT] STATUS: BLOCKED
[BLOCKED] sadp-audit failed (exit=1). Fix issues before commit.
```

**Verdict:** PASS (finding confirmed). Two independent enforcement layers
observed:

1. **ai_guard security scan (Layer 1):** PASS. `allow_paths` correctly
   overrode `deny_paths` for `_evidence/**/secret-scan-output.txt`. The
   allow_paths narrowing per DR-20260612 works as intended.
2. **SADP TaskSpec scope check (Layer 2):** BLOCKED. The file
   `_evidence/hook-v241-probe/secret-scan-output.txt` is not covered by any
   TaskSpec write_set. The current TaskSpec covers `_evidence/hook-output/**`
   but not `_evidence/hook-v241-probe/**`.

This is the expected behavior of defense-in-depth: security scan (ai_guard)
and scope enforcement (SADP audit) operate as independent layers. The
allow_paths override passed security but the file was still blocked by scope.

**Hook-output artifacts triggered:** Yes (sadp-audit timestamp files created).

---

### 4. Summary Table

| Probe | Staged Files | Expected | Actual | Exit | Verdict |
|-------|-------------|----------|--------|------|---------|
| 1 (pass) | 3 clean + manifest + current-task | PASS | PASS | 0 | PASS |
| 2 (deny) | 1 secret-named + current-task | BLOCKED | BLOCKED | 1 | PASS |
| 3 (narrow) | 1 out-of-scope secret + current-task | BLOCKED | BLOCKED | 1 | PASS |
| 4 (two-layer) | 1 in-scope evidence secret + current-task | security PASS, scope BLOCK | security PASS, scope BLOCK | 1 | PASS |

All 4 probes produced expected results.

---

### 5. Cleanup

**Probe commit reset:** `git reset --hard HEAD~1` removed Probe 1 commit
`302ae1e`. Probes 2-4 never created commits (blocked by hook).

**Files deleted:**

- `_tmp/hook-v241-probe-a1/` (entire directory tree)
- `_evidence/hook-v241-probe/` (entire directory)

**Staging reset:** `git reset HEAD` cleared all staged probe files.

**current-task.yaml:** Restored to pre-probe state (HOOK-V241 TaskSpec with
write_set intact for report output).

**sealed-files-manifest.json:** Auto-regenerated by hook during Probe 1,
restored to HEAD state after reset.

---

### 6. Final Worktree State

```
HEAD: 5eb84547
Modified (pre-existing rotating artifact):
  _evidence/hook-output/latest.json
Untracked (pre-existing rotating artifacts from probe hook runs):
  _evidence/hook-output/ai-guard-<timestamp>.txt (multiple)
  _evidence/hook-output/sadp-audit-<timestamp>.txt (multiple)
  _evidence/hook-output/conversation-health-<timestamp>.txt (multiple)
  _evidence/hook-output/test-governance-<timestamp>.txt (multiple)
New (this task):
  _reports/hook-v241-real-invoke-probe-a1/EXECUTION_REPORT.md
```

No residual staged files. No probe files remain.

---

### 7. Declarations

**Hook/policy/code modified:** No. Zero modifications to hooks, ai_guard.py,
policy.yaml, or any business code during this probe.

**Hook-output rotating files triggered:** Yes. Each probe commit attempt
(successful or blocked) generated hook-output artifacts. These are rotating
artifacts that cannot be eliminated without disabling hook evidence capture.

**Residual staged files:** None. `git status` shows only rotating hook-output
artifacts and this report file.

**Full test suite pass:** NOT claimed. This report only covers real hook
invocation probes, not the full test suite.

**Live dispatch:** NOT executed. No external runtime, opencode, or paper
workflow invoked.

---

### 8. Findings

**F1 -- env var passing confirmed reliable.** The `AI_GUARD_FILE_LIST`
environment variable approach (v2.4.1) works correctly under real pre-commit
hook invocation on Windows. Multi-file, long-path (4-level nesting), and
space-path cases all passed without command line length errors.

**F2 -- deny_paths enforcement intact.** Files matching `*secret*` pattern
are correctly blocked with explicit `DENIED` error message.

**F3 -- allow_paths narrow scope enforced.** `_tmp/` directory is correctly
excluded from allow_paths override. Only `_evidence/**` and `_archive/**`
scoped files benefit from the override.

**F4 -- two independent enforcement layers confirmed.** ai_guard security
scan and SADP TaskSpec scope check operate as separate layers. A file can
pass security (via allow_paths) but still be blocked by scope. This is
defense-in-depth working as designed.

**F5 -- space-path handling confirmed.** Paths containing spaces
(`path with spaces/clean file.txt`) are correctly handled by the env var
approach. The newline-separated env var avoids the argument-splitting issues
that would affect command line passing.

---

### 9. Recommended Next

1. `TASKSPEC-STATUS-CLOSEOUT-A1` -- apply triage recommendations
2. `MULTI-AGENT-GATE0-FRESH-SNAPSHOT-A1` -- fresh gate-0 evaluation
3. Human authorization checklist confirmation
4. Real multi-agent pilot (after all above complete)
