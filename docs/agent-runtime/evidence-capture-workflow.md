---
Task: EVIDENCE-CAPTURE-STANDARD-A1
Document: Evidence Capture Workflow
Version: 1.0.0
Date: 2026-06-11
Status: Active
---

# Evidence Capture Workflow

## 1. Overview

The evidence capture workflow has two phases:

- **Phase A: Automatic Hook Output Persistence** -- runs at every commit, captures raw hook output to `_evidence/hook-output/` without requiring any agent action.
- **Phase B: Evidence Pack Building** -- runs when submitting to GPT reviewer, assembles a complete evidence pack from committed artifacts plus persisted hook output.

Phase A solves the "replay evidence" problem documented in R18: when hook output was not captured at execution time, agents had to re-run the hook after the fact, producing replay output that could not substitute for original output (Evidence Pack Standard, Validation Rule 8).

Phase B solves the "one-off builder script" problem: agents were creating task-specific `_build_*.py` scripts for every evidence pack, each one becoming an untracked artifact that polluted the workspace (Evidence Generation Hygiene, Anti-Pattern: Builder Amnesia).

---

## 2. Phase A: Hook Output Persistence

### How It Works

The pre-commit hook (`hooks/pre-commit.governance.ps1`) now automatically captures the output of every stage it runs. No configuration is required -- it happens on every `git commit`.

### Output Files

| File | Source | When Created |
|------|--------|--------------|
| `_evidence/hook-output/sadp-audit-{timestamp}.txt` | `scripts/sadp-audit.ps1` stdout + stderr | Every commit where sadp-audit runs |
| `_evidence/hook-output/ai-guard-{timestamp}.txt` | `tools/ai_guard.py` stdout + stderr | Every commit where ai_guard runs |
| `_evidence/hook-output/test-governance-{timestamp}.txt` | `scripts/Test-Governance.ps1` output | Every commit where governance scan runs |
| `_evidence/hook-output/latest.json` | Combined JSON summary | Every commit (overwritten each time) |

### JSON Summary Schema

`latest.json` is overwritten on every commit. It contains:

```json
{
  "timestamp": "2026-06-11T14:30:00Z",
  "hook_version": "2.1.0",
  "stages": [
    {
      "name": "manifest-regen",
      "exit_code": 0,
      "output_file": null,
      "duration_ms": 0
    },
    {
      "name": "sadp-audit",
      "exit_code": 0,
      "output_file": "_evidence/hook-output/sadp-audit-20260611-143000.txt",
      "duration_ms": 1250
    },
    {
      "name": "ai-guard",
      "exit_code": 0,
      "output_file": "_evidence/hook-output/ai-guard-20260611-143000.txt",
      "duration_ms": 800
    },
    {
      "name": "test-governance",
      "exit_code": 0,
      "output_file": "_evidence/hook-output/test-governance-20260611-143000.txt",
      "duration_ms": 500
    }
  ],
  "git_context": {
    "branch": "main",
    "commit_count": 142,
    "staged_file_count": 5
  },
  "overall_result": "PASS"
}
```

### Key Design Decisions

1. **Additive, not disruptive.** The hook still prints output to the console as before. Persistence is a side effect, not a replacement.
2. **Files are NOT git-added.** `_evidence/hook-output/` is for local evidence capture only. The hook never stages these files. They should be consumed by the evidence pack builder (Phase B) or by manual inspection.
3. **Timestamped files prevent overwrite.** Each run creates new timestamped files. `latest.json` is the only file that is overwritten, serving as a stable pointer for automation.
4. **Graceful degradation.** If a script is missing (e.g., `sadp-audit.ps1` not found), a placeholder file is written indicating the skip. The hook continues as before.
5. **PowerShell 5.1 compatible.** Uses only built-in cmdlets (`Out-File`, `ConvertTo-Json`, `Get-Date`, `Measure-Object`). No PowerShell 7 features.

### When the Hook Blocks

If sadp-audit fails (non-zero exit), the hook:
1. Still writes `latest.json` with `overall_result: "BLOCKED"`
2. Still writes all captured output files
3. Exits with code 1 (blocks the commit)

This ensures evidence is captured even for failed runs, which is valuable for debugging and for understanding what went wrong.

---

## 3. Phase B: Evidence Pack Building

### Prerequisites

Before building an evidence pack, ensure:
- All scope commits are complete (Evidence Generation Hygiene, Rule 5: Generate After Last Commit)
- Hook output files exist in `_evidence/hook-output/` for the commits in scope
- The workspace is in its final state (no pending staging, no unfinished cleanup)

### Using the Reusable Builder

```bash
python scripts/build_evidence_pack.py \
  --task-id MY-TASK-A1 \
  --commits abc123 def456 \
  --base <base-commit> \
  --out _evidence/MY-TASK-A1 \
  --zip _evidence/EVIDENCE_PACK_MY_TASK_A1.zip \
  --hook-log _evidence/hook-output/latest.json
```

### Parameter Reference

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--task-id` | Yes | Task identifier (e.g., `MY-TASK-A1`). Used for naming output files and the ZIP archive. |
| `--commits` | Yes | Space-separated list of commit short hashes in scope. The builder generates `git-show-{hash}.txt` and `diff-{hash}.patch` for each. |
| `--base` | Yes | Base commit to diff against. Combined diff is generated from `base..HEAD` or `base..last-commit`. |
| `--out` | Yes | Output directory for the evidence pack files. Created if it does not exist. |
| `--zip` | No | Path for the output ZIP archive. If provided, all evidence files are bundled into a ZIP. |
| `--hook-log` | No | Path to `latest.json` from Phase A. If provided, the builder copies the original hook output files into the evidence pack as `sadp-audit-raw.txt` and `ai-guard-scope-check-output.txt`. |

### What the Builder Generates

The builder produces all files required by the Evidence Pack Standard:

**Minimum required files:**

| File | How Generated |
|------|---------------|
| `diff.patch` | `git diff {base}..{last-commit}` |
| `diff-stat-combined.txt` | `git diff --stat {base}..{last-commit}` |
| `test-output.txt` | Runs pytest (or configured test runner) and captures raw output |
| `safety-report.json` | Checks deny_list paths, secret-scan status, hook integrity, workspace state |
| `chain-evidence.json` | Builds from `--commits` list with hash, author, timestamp, subject |
| `review.md` | Narrative template pre-filled with commit summaries |
| `review.yaml` | Structured verdict with counts from git state |
| `final-report.md` | Execution summary template |
| `git-log.txt` | `git log --oneline {base}..{last-commit}` |
| `git-status-after.txt` | `git status --porcelain` post-commit |

**Conditional files (generated when conditions apply):**

| File | Condition |
|------|-----------|
| `git-status-before.txt` | When `--base` state differs from clean |
| `deferred-files-register.yaml` | When untracked files remain |
| `sadp-audit-raw.txt` | When `--hook-log` is provided and points to valid output |
| `ai-guard-scope-check-output.txt` | When `--hook-log` references ai-guard output |
| `git-show-{commit}.txt` | For each commit in `--commits` |
| `diff-{commit}.patch` | For each commit in `--commits` |

---

## 4. Migration Guide

### Before: One-Off Build Scripts

```
# Old pattern (FORBIDDEN - creates untracked artifacts)
cat > _build_my_task_evidence.py << 'EOF'
import subprocess, json, os
# ... 200 lines of hardcoded commit hashes and paths ...
EOF
python _build_my_task_evidence.py
# _build_my_task_evidence.py is now an untracked file
# Must be committed, removed, or registered
```

Problems with the old pattern:
- Each script is hardcoded for a specific task's commits and paths
- The script itself becomes an untracked file requiring lifecycle management
- Multiple rounds of evidence generation create accumulating builder scripts
- Scripts are not reusable across tasks

### After: Reusable Builder

```bash
# New pattern (REQUIRED)
python scripts/build_evidence_pack.py \
  --task-id MY-TASK-A1 \
  --commits abc123 def456 \
  --base aabbcc \
  --out _evidence/MY-TASK-A1 \
  --zip _evidence/EVIDENCE_PACK_MY_TASK_A1.zip \
  --hook-log _evidence/hook-output/latest.json
```

Advantages:
- `scripts/build_evidence_pack.py` is a tracked, committed tool -- it is not an untracked artifact
- All task-specific values are passed as parameters, not hardcoded
- One script handles all evidence packs regardless of task
- The `--hook-log` flag automatically integrates Phase A output

### Migration Steps

1. Stop creating `_build_*.py` files in the project root or `_reports/` directory.
2. Ensure `scripts/build_evidence_pack.py` exists and is tracked in git.
3. For each new evidence pack, invoke the reusable builder with the appropriate parameters.
4. If the reusable builder lacks a feature needed for a specific task, extend the builder rather than creating a new script. Submit a PR to add the capability.
5. Existing `_build_*.py` files in `_reports/` directories may remain as historical reference but should not be used for new evidence packs.

---

## 5. Evidence File Specification

### Required Files

| # | File | Source | Validation Rule |
|---|------|--------|-----------------|
| 1 | `diff.patch` or `diff-stat-combined.txt` | `git diff {base}..{last}` | Must cover every file touched by every scope commit. Partial diffs fail. |
| 2 | `test-output.txt` | pytest / test runner raw output | Must be raw terminal output. Summaries or paraphrases fail. |
| 3 | `safety-report.json` | Builder-generated | Valid JSON. Must include deny_list checks, secret-scan results, hook-integrity status. |
| 4 | `chain-evidence.json` | Builder-generated from `--commits` | Valid JSON array. Each entry: hash, author, timestamp, subject. |
| 5 | `review.md` | Builder-generated template | Narrative. Not machine-validated but must exist. |
| 6 | `review.yaml` | Builder-generated | Valid YAML. Must include verdict, commit count, file counts, scope alignment. |
| 7 | `final-report.md` | Builder-generated template | Must cover what was done, what was verified, what remains open. |
| 8 | `git-log.txt` | `git log --oneline {base}..{last}` | Every scope commit must appear. |
| 9 | `git-status-after.txt` | `git status --porcelain` post-commit | Must reflect state AFTER final scope commit. |

### Conditional Files

| File | Trigger Condition | Validation |
|------|-------------------|------------|
| `git-status-before.txt` | Workspace state transition claimed | Must show pre-transition state |
| `deferred-files-register.yaml` | Untracked files remain at submission | Every untracked file in `git-status-after.txt` must be listed. Listed count must match safety-report and review.yaml. |
| `secret-scan-output.txt` | deny_paths or mock secret fixtures involved | Raw scanner output. MUST NOT be git-staged. |
| `ai-guard-scope-check-output.txt` | Scope checking is part of the claim | Must be original output, not replay (unless labeled) |
| `sadp-audit-raw.txt` | Pre-commit hook output required | Must be original hook output. Replay output must be labeled "replay". |
| `git-show-{commit}.txt` | Each commit claimed in scope | One file per commit. Full `git show` output. |
| `diff-{commit}.patch` | Each commit claimed in scope | One file per commit. Per-commit diff. |

### Hook Output Files (Phase A)

These files are generated by the pre-commit hook and stored locally. They are NOT part of the evidence pack until Phase B copies them in.

| File | Generated By | Consumed By |
|------|--------------|-------------|
| `sadp-audit-{timestamp}.txt` | `pre-commit.governance.ps1` Stage 2 | Builder `--hook-log` flag -> `sadp-audit-raw.txt` |
| `ai-guard-{timestamp}.txt` | `pre-commit.governance.ps1` Stage 2 | Builder `--hook-log` flag -> `ai-guard-scope-check-output.txt` |
| `test-governance-{timestamp}.txt` | `pre-commit.governance.ps1` Stage 3 | Informational / debugging |
| `latest.json` | `pre-commit.governance.ps1` all stages | Builder `--hook-log` parameter input |

---

## 6. Consistency Rules

All numerical values must agree across the **consistency ring**:

| File | Role |
|------|------|
| `git-status-after.txt` | Ground truth for workspace state |
| `deferred-files-register.yaml` | Accounting for every untracked file |
| `safety-report.json` | Machine-parseable safety assessment |
| `review.yaml` | Structured verdict |
| `final-report.md` | Human-readable narrative |

### Fields That MUST Agree

| Concept | Appears In | Agreement Rule |
|---------|-----------|----------------|
| Untracked files after final commit | `git-status-after.txt` (counted), `safety-report.json` (`post_commit_untracked`), `review.yaml` (`post_commit_untracked`), `final-report.md` (narrative) | All four values must be identical |
| Deferred files | `deferred-files-register.yaml` (listed count), `safety-report.json` (`deferred_count`), `review.yaml` (`deferred_count`), `final-report.md` (narrative) | All four values must be identical |
| Commits in scope | `chain-evidence.json` (array length), `git-log.txt` (line count), `review.yaml` (`commits_in_scope`), `final-report.md` (narrative) | All four values must be identical |
| Modified tracked files | `safety-report.json` (`modified_tracked`), `review.yaml` (`modified_tracked`), `final-report.md` (narrative) | All three values must be identical |

### Validation

The evidence pack linter (`scripts/evidence_pack_linter.py`) checks consistency automatically. If any value in the consistency ring disagrees, the pack FAILS validation regardless of whether any individual file is internally correct.

### Common Failure Pattern

The most common consistency failure is generating evidence before the final commit (premature evidence). The evidence reflects pre-commit state, but the final commit changes the workspace. Post-commit reality no longer matches the evidence. This is why Evidence Generation Hygiene Rule 5 mandates: generate AFTER the last commit.

---

## 7. Anti-Patterns

### 7.1 Creating One-Off Build Scripts (Forbidden)

**Wrong:**
```bash
cat > _build_my_task_r3_evidence.py << 'EOF'
# Hardcoded commits, paths, task-specific logic
EOF
python _build_my_task_r3_evidence.py
```

**Right:**
```bash
python scripts/build_evidence_pack.py --task-id MY-TASK-A1 --commits abc123 def456 --base aabbcc --out _evidence/MY-TASK-A1
```

One-off scripts become untracked artifacts. Each evidence generation round creates a new script, leading to accumulating builders (Evidence Generation Hygiene, Failure Mode: R18 Accumulating Session Artifacts).

### 7.2 Generating Evidence Before Final Commit (Forbidden)

**Wrong:**
```
1. Make changes
2. Generate evidence pack    <-- captures pre-commit state
3. git add . && git commit   <-- changes workspace state
4. Submit to GPT             <-- evidence no longer matches reality
```

**Right:**
```
1. Make changes
2. git add . && git commit   <-- all scope commits complete
3. Generate evidence pack    <-- captures true post-commit state
4. Submit to GPT
```

Numbers in the evidence will disagree with post-commit reality if evidence is generated before the final commit (Evidence Pack Standard, Anti-Pattern 6).

### 7.3 Using Replay Evidence Without Labeling (Forbidden)

When original hook output was not captured at execution time and the hook is re-run after the fact, the output is "replay" output. Replay output MUST be labeled as such in its header.

**Wrong:**
```
# sadp-audit output
PASS - all checks passed
```

**Right:**
```
# sadp-audit output (REPLAY - re-executed 2026-06-11T15:00:00Z)
# Original hook output was not captured at commit time
PASS - all checks passed
```

Phase A (automatic hook output persistence) eliminates the need for replay by capturing output at execution time. If Phase A output exists in `_evidence/hook-output/`, it MUST be used instead of replay.

### 7.4 Forgetting to Pass --hook-log (Data Loss)

**Wrong:**
```bash
python scripts/build_evidence_pack.py \
  --task-id MY-TASK-A1 \
  --commits abc123 \
  --base aabbcc \
  --out _evidence/MY-TASK-A1
# No --hook-log flag! Original hook output is not included in the pack.
```

**Right:**
```bash
python scripts/build_evidence_pack.py \
  --task-id MY-TASK-A1 \
  --commits abc123 \
  --base aabbcc \
  --out _evidence/MY-TASK-A1 \
  --hook-log _evidence/hook-output/latest.json
# Original hook output is copied into the evidence pack.
```

Without `--hook-log`, the evidence pack lacks `sadp-audit-raw.txt` and `ai-guard-scope-check-output.txt`. The Evidence Pack Standard requires these files when pre-commit hook output is relevant to the submission.

### 7.5 Staging Evidence Output Files (Forbidden)

The files in `_evidence/hook-output/` are for local evidence capture only. They MUST NOT be added to git staging by the hook or by the agent. The hook enforces this by never running `git add` on evidence files.

If an agent manually runs `git add .` or `git add _evidence/`, the hook output files will be staged. This is wrong because:
- Hook output files are intermediate artifacts, not deliverables
- They may contain paths or content that triggers deny_list violations
- They belong in the evidence pack ZIP, not in version control

---

## 8. Hook Failure Semantics

Output persistence is not merely logging — it is a structured enforcement mechanism. The pre-commit hook (v2.3.0) implements fail-closed semantics for all required governance stages:

- **Blocking stages**: sadp-audit, ai-guard. Any non-zero exit code from these stages causes `overall_result: BLOCKED` and hook exit 1, which rejects the commit.
- **Advisory stages**: manifest-regen, test-governance. Exit codes are logged but do not block the commit.

Raw hook output should be captured when available. The files in `_evidence/hook-output/` are original captures produced at commit time, not replay output generated after the fact. Each file header includes `Source: pre-commit hook (original)` to distinguish original from replay.

`latest.json` is a structured index that references the individual stage output files. It is not a replacement for full raw console logs. Evidence packs should include both `latest.json` and the raw stage outputs when submitting to GPT review.

Replay-style evidence (re-running the hook after the commit to capture output) must be explicitly labeled as replay. The Evidence Pack Standard (Validation Rule 8) rejects replay evidence as a substitute for original output.

For the complete failure semantics specification, see [Hook Failure Semantics](hook-failure-semantics.md).

A validation script (`scripts/validate_hook_output.py`) verifies that `latest.json` conforms to the schema and that nonzero blocking-stage exit codes correspond to `overall_result: BLOCKED`.

---

## Related Documents

- [Evidence Pack Standard](evidence-pack-standard.md)
- [Evidence Generation Hygiene](evidence-generation-hygiene.md)
- [Workspace Closure Standard](workspace-closure-standard.md)
- [Universal Agent Workflow Standard](universal-agent-workflow-standard.md)
- [Pre-GPT Review Gate](pre-gpt-review-gate.md)
- [Hook Failure Semantics](hook-failure-semantics.md)
