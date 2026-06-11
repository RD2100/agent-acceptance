---
Task: UNIVERSAL-AGENT-WORKFLOW-STANDARD-A1
Document: Evidence Pack Standard
Version: 1.0.0
Date: 2026-06-11
Status: Active
---

# Evidence Pack Standard

## Purpose

This document defines the minimum requirements for evidence packs submitted to GPT reviewer. An evidence pack is a structured collection of machine-verifiable artifacts that proves, beyond narrative assertion, what an agent did and what state the workspace is in after execution.

Text-only summaries without supporting files are explicitly forbidden. A submission that lacks a conforming evidence pack SHALL be rejected at gate and SHALL NOT be forwarded for reviewer evaluation.

Evidence packs serve three functions:

1. **Traceability** -- every claim maps to a file, and every file maps to a verifiable source.
2. **Consistency** -- numerical values reported across multiple files MUST agree; disagreement is itself a failure condition.
3. **Reproducibility** -- a reviewer SHALL be able to reconstruct the execution timeline from the pack contents alone, without access to the original session.

---

## Minimum Required Files

Every evidence pack MUST contain all of the following files. Omission of any single file is grounds for immediate rejection.

| # | File | Description |
|---|------|-------------|
| 1 | `diff.patch` or `diff-stat-combined.txt` | Shows what changed in scope commits. Combined diff or diff-stat across all commits claimed in scope. |
| 2 | `test-output.txt` | Actual pytest (or equivalent test runner) output captured from the terminal. MUST be raw output, not a summary or paraphrase. |
| 3 | `safety-report.json` | Valid JSON document containing the security assessment. MUST include fields for deny-list path checks, secret-scan results, and hook-integrity status. |
| 4 | `chain-evidence.json` | Valid JSON document listing all commits in scope. Each entry MUST include commit hash, author, timestamp, and subject line. |
| 5 | `review.md` | Narrative review of changes. Provides human-readable context but SHALL NOT substitute for structured data. |
| 6 | `review.yaml` | Structured verdict with machine-parseable fields. MUST include verdict (pass/fail), commit count, file counts, and scope alignment assessment. |
| 7 | `final-report.md` | Execution summary covering what was done, what was verified, and what remains open. |
| 8 | `git-log.txt` | Git log output showing the commit chain for all commits claimed in scope. MUST use `--oneline` or equivalent format. |
| 9 | `git-status-after.txt` | Post-commit workspace state captured via `git status`. MUST reflect the state AFTER the final commit in scope. |

---

## Conditional Files

The following files are REQUIRED when the conditions described apply. Failure to include a conditionally required file is equivalent to omitting a required file.

| File | Condition |
|------|-----------|
| `git-status-before.txt` | REQUIRED when a workspace state transition is claimed (e.g., "workspace went from dirty to clean"). |
| `deferred-files-register.yaml` | REQUIRED when untracked files remain at submission time. This file MUST list every untracked file that is not committed or removed. REQUIRED for all closure claims where `modified_tracked != 0` or untracked files exist. |
| `secret-scan-output.txt` | REQUIRED when `deny_paths` or mock secret fixtures are involved in the task. MUST contain raw scanner output. SHALL NOT be staged in git (will be blocked by deny_list). |
| `ai-guard-scope-check-output.txt` | REQUIRED when scope checking is part of the claim being submitted. |
| `sadp-audit-raw.txt` | Pre-commit hook output. MUST be the original raw output captured at hook execution time. If replay output is provided instead, it MUST be clearly labeled as "replay" (see Validation Rule 8). |
| `git-show-{commit}.txt` | REQUIRED for each commit claimed in scope. One file per commit, named with the short hash. Contains the full `git show` output for that commit. |
| `diff-{commit}.patch` or `diff-stat-{commit}.txt` | REQUIRED for each commit claimed in scope. Provides per-commit diff evidence in addition to the combined diff. |

---

## Validation Rules

An evidence pack SHALL be validated against the following rules before reviewer evaluation begins. Violation of any rule is a hard failure.

1. **JSON validity.** All `.json` files MUST parse as valid JSON. No comments, no trailing commas, no duplicate keys at the same level.

2. **YAML validity.** All `.yaml` files MUST parse successfully under a conformant YAML 1.2 parser.

3. **Commit evidence completeness.** Every commit claimed in scope MUST have a corresponding `git-show-{commit}.txt` file in the evidence pack. A commit referenced in `chain-evidence.json` or `final-report.md` without matching evidence SHALL cause rejection.

4. **Git-log coverage.** Every final commit named in the submission MUST appear in `git-log.txt`. No exceptions.

5. **Untracked file accounting.** Every untracked file present in `git-status-after.txt` MUST be accounted for by exactly one of the following dispositions:
   - Committed in a subsequent scope commit (with evidence), OR
   - Explicitly removed (with evidence), OR
   - Listed exactly once in `deferred-files-register.yaml`.

6. **Closure gate: modified_tracked = 0.** A closure claim (task-complete verdict) REQUIRES `modified_tracked = 0` in the safety report. If staged or modified tracked files remain, the pack FAILS.

7. **No false cleanliness claims.** "Workspace clean" SHALL NOT be claimed when `deferred-files-register.yaml` is non-empty or when `git-status-after.txt` shows untracked files. Claiming cleanliness while deferring files is an anti-pattern (see Anti-Patterns section).

8. **Replay labeling.** When pre-commit hook output is captured via replay (re-execution after the fact) rather than original hook invocation, the output file MUST be labeled as "replay" in its header. Replay output CANNOT substitute for original raw hook output when original output was available at execution time.

9. **Internal numerical consistency.** All evidence files MUST report internally consistent numbers. The same counts (modified files, untracked files, deferred files, commits in scope) MUST appear identically across `git-status-after.txt`, `deferred-files-register.yaml`, `safety-report.json`, `review.yaml`, and `final-report.md`. Disagreement on any numerical value constitutes a validation failure regardless of individual file correctness.

---

## Internal Consistency Requirement

The following files form the **consistency ring**. Every numerical value reported in any one of these files MUST match the corresponding value in all others:

- `git-status-after.txt`
- `deferred-files-register.yaml`
- `safety-report.json`
- `review.yaml`
- `final-report.md`

### Specific fields that MUST agree

| Concept | Where it appears |
|---------|-----------------|
| Number of untracked files after final commit | `git-status-after.txt` (counted), `safety-report.json` (`post_commit_untracked`), `review.yaml` (`post_commit_untracked`), `final-report.md` (narrative count) |
| Number of deferred files | `deferred-files-register.yaml` (listed count), `safety-report.json` (`deferred_count`), `review.yaml` (`deferred_count`), `final-report.md` (narrative count) |
| Number of commits in scope | `chain-evidence.json` (array length), `git-log.txt` (line count), `review.yaml` (`commits_in_scope`), `final-report.md` (narrative count) |
| Number of modified tracked files | `safety-report.json` (`modified_tracked`), `review.yaml` (`modified_tracked`), `final-report.md` (narrative) |

If the values in the consistency ring disagree, the evidence pack FAILS validation regardless of whether any individual file is internally correct.

---

## Anti-Patterns (Forbidden)

The following practices are explicitly forbidden. Detection of any anti-pattern SHALL result in immediate rejection of the evidence pack.

1. **Text-only submission.** Submitting a narrative summary without a conforming evidence pack. Every submission MUST include actual files, not descriptions of what the files would contain.

2. **Phantom commits.** Claiming more commits in scope than are evidenced. If a commit is mentioned in `final-report.md`, `chain-evidence.json`, or `review.yaml` but lacks a corresponding `git-show-{commit}.txt`, the pack is invalid.

3. **Arithmetic errors.** Internal contradictions in numerical breakdowns. For example, claiming "17 staged + 2 untracked = 21 total" when 17 + 2 = 19, not 21.

4. **False zero-untracked claims.** Stating `post_commit_untracked = 0` or "0 untracked files" while `git-status-after.txt` shows untracked files present.

5. **Staged secret-scan output.** Including `secret-scan-output.txt` in git staging. This file SHALL be excluded from version control because its contents may trigger deny_list violations.

6. **Premature evidence generation.** Generating evidence files BEFORE the final commit is made. This causes post-commit state mismatch because the evidence will not reflect changes introduced by the final commit. Evidence MUST be generated AFTER all scope commits are complete.

---

## Failure Mode Examples (from R15-R18)

The following real-world failure modes are documented to prevent recurrence.

### R18 Follow-Up: Incomplete diff.patch

`diff.patch` was incomplete -- it omitted 10 file paths including `hooks/sealed-files-manifest.json`. The combined diff MUST cover every file touched by every commit in scope. Partial diffs are not acceptable.

### R18 Workspace Cleanup: Register vs. git-status mismatch

The deferred files register listed 19 files, while `git-status-after.txt` showed 20 untracked files. The discrepancy was a missing third `secret-scan-output.txt` file that was neither registered nor committed. All untracked files MUST be accounted for (see Validation Rule 5).

### R18 Closure: Replay evidence substituted for original hook output

`ai-guard-scope-check-output.txt` and `sadp-audit-raw.txt` contained output from commit `bc974d2f` replay rather than the current commits in scope. Replay output MUST be labeled as such (Validation Rule 8) and CANNOT replace original output when original output was available.

### R18 Closure: review.yaml vs. register numerical disagreement

`review.yaml` reported `post_commit_untracked = 21` while `deferred-files-register.yaml` showed `deferred = 19`. This violates the internal consistency requirement (Validation Rule 9). Both files MUST agree on the count of untracked/deferred files.

---

## Submission Checklist

Before submitting an evidence pack, the agent SHALL verify:

- [ ] All 9 minimum required files are present
- [ ] All applicable conditional files are present
- [ ] Every `.json` file parses without error
- [ ] Every `.yaml` file parses without error
- [ ] Every commit in scope has a `git-show-{commit}.txt` file
- [ ] Every commit in scope appears in `git-log.txt`
- [ ] All untracked files in `git-status-after.txt` are accounted for
- [ ] Numerical values in the consistency ring agree across all five files
- [ ] No replay output is presented as original without labeling
- [ ] No anti-patterns are present
- [ ] Evidence was generated AFTER the final scope commit
