---
Task: EVIDENCE-CAPTURE-STANDARD-A2
Document: Evidence Pack Review Rules
Version: 1.0.0
Date: 2026-06-12
Status: Active
---

# Evidence Pack Review Rules

## Purpose

This document consolidates review evaluation rules for GPT and human reviewers into a single reference. Previously, these rules were scattered across the Evidence Pack Standard, Pre-GPT Review Gate, Evidence Capture Workflow, and reviewer-specific checklists. This document provides a unified evaluation protocol.

The evidence pack contract itself is defined in [Evidence Capture Standard](evidence-capture-standard.md). This document specifies how reviewers evaluate whether a submitted pack meets that contract.

---

## Pre-Review Checklist

Before evaluating content quality, the reviewer SHALL verify structural integrity. If any pre-review check fails, the pack SHALL NOT proceed to content evaluation.

### 1. Tier 0 File Presence

Verify that all Tier 0 files listed in `evidence-manifest.json` with `completeness: required` are physically present in the pack. Count the required files and compare against the manifest.

| Check | Pass Condition |
|-------|---------------|
| Required file count | Physical file count equals `evidence-manifest.json` `required_files` count |
| `review.yaml` present | File exists in pack root |
| `final-report.md` present | File exists in pack root |
| `git-status-after.txt` present | File exists in pack root |
| `diff.patch` or `git-show.txt` present | At least one exists in pack root |
| `test-output.txt` or `no-test-rationale.md` present | At least one exists in pack root |
| `safety-report.json` present | File exists in pack root |
| `evidence-manifest.json` present | File exists in pack root |
| `task-spec.yaml` or `current-task.yaml` present | At least one exists in pack root |
| `git-status-before.txt` present | File exists (when workspace transition claimed) |
| `secret-scan-output.txt` present | File exists (when `deny_paths` or mock fixtures involved) |

### 2. Parse Validity

All structured data files MUST parse without error.

| File Type | Validation |
|-----------|-----------|
| `*.json` | Parses as valid JSON (no comments, no trailing commas, no duplicate keys) |
| `*.yaml` | Parses as valid YAML 1.2 |
| `evidence-manifest.json` | Parses AND conforms to `evidence-manifest.schema.json` |
| `review.yaml` | Parses AND conforms to `review.schema.yaml` (profile: `ecs-v1`) |
| `safety-report.json` | Parses AND contains required fields (`deny_paths`, `secret_scan`, `hook_integrity`) |

### 3. Pre-Review Gate Decision

| Outcome | Action |
|---------|--------|
| All pre-review checks pass | Proceed to content evaluation |
| Any Tier 0 file missing | Halt. Record `required_files_missing` signal. Verdict eligibility: `needs_more_evidence`. |
| Any parse failure | Halt. Record `schema_invalid` signal. Verdict eligibility: `not_eligible`. |

---

## Verdict Eligibility Interpretation

The `verdict_eligibility` field in `review.yaml` is a machine-computed RECOMMENDATION. Reviewers interpret it as follows:

| verdict_eligibility | Reviewer Verdict Consideration | Conditions |
|---------------------|-------------------------------|------------|
| `eligible_clean` | May consider **ACCEPTED** | All consistency checks pass, content quality verified, no anti-patterns detected |
| `eligible_with_limitations` | May consider **ACCEPTED_WITH_LIMITATION** | Limitations are explicitly documented, each limitation is specific, bounded, and actionable |
| `needs_more_evidence` | Should consider **NEEDS_REVISION** | Blocking signals identified and listed, revision instructions specify which files or evidence are missing |
| `not_eligible` | Should consider **REJECTED** | Critical failures documented, rejection explains the root cause |

### Important Constraints

- `verdict_eligibility` is a RECOMMENDATION, not a final verdict. Reviewers MAY override the recommendation with documented justification.
- A pack with `eligible_clean` MAY still be rejected if content quality checks fail (e.g., phantom commits, false cleanliness claims).
- A pack with `eligible_with_limitations` SHALL NOT be accepted unless each limitation is explicitly acknowledged in the reviewer's verdict.
- The reviewer's final verdict MUST be recorded in the SADP 0.R.2 review artifact (separate from ECS `review.yaml`). See [Relationship to SADP 0.R.2](evidence-capture-standard.md#relationship-to-sadp-0r2-review-yaml).

---

## Evidence Consistency Checks

Numerical values MUST agree across the consistency ring. Disagreement is itself a failure condition, regardless of whether any individual file is internally correct.

### 4. Modified Tracked File Count

The count of modified tracked files MUST agree across all four sources:

| Source | Field or Method |
|--------|----------------|
| `safety-report.json` | `modified_tracked` field |
| `review.yaml` | `modified_tracked` field |
| `final-report.md` | Narrative count of modified tracked files |
| `evidence-manifest.json` | `workspace_state.modified_tracked` field |

**Failure:** If any source disagrees, record `consistency_modified_tracked_disagree` signal.

### 5. Untracked File Count

The count of untracked files MUST agree across all four sources:

| Source | Field or Method |
|--------|----------------|
| `git-status-after.txt` | Counted from porcelain output (lines starting with `??`) |
| `safety-report.json` | `post_commit_untracked` field |
| `review.yaml` | `post_commit_untracked` field |
| `evidence-manifest.json` | `workspace_state.untracked_total` field |

**Failure:** If any source disagrees, record `consistency_untracked_disagree` signal.

### 6. Commit Count

The count of commits in scope MUST agree across all four sources:

| Source | Field or Method |
|--------|----------------|
| `chain-evidence.json` | Array length |
| `git-log.txt` | Line count (one commit per line in `--oneline` format) |
| `review.yaml` | `commits_in_scope` field |
| `evidence-manifest.json` | `commits.count` field |

**Failure:** If any source disagrees, record `consistency_commit_count_disagree` signal.

### 7. Test Count

The test result counts MUST agree between sources:

| Source | Field or Method |
|--------|----------------|
| `test-output.txt` | Summary line from test runner (e.g., "142 passed, 3 skipped") |
| `review.yaml` | `test_count.total`, `test_count.passed`, `test_count.failed`, `test_count.skipped` |
| `safety-report.json` | `test_results` fields (when present) |

**Failure:** If any source disagrees, record `consistency_test_count_disagree` signal.

### Consistency Check Decision

| Outcome | Action |
|---------|--------|
| All consistency checks pass | Record `consistency_check_passed`. Proceed to content quality checks. |
| Any consistency check fails | Record the specific disagreement signal. This is a blocking signal. Verdict eligibility downgrades to `needs_more_evidence`. |

---

## Content Quality Checks

After structural and consistency validation, the reviewer evaluates the quality and completeness of the evidence content.

### 8. Commit Evidence Completeness

| Check | Pass Condition |
|-------|---------------|
| Per-commit evidence | Every commit in scope has a `git-show-{commit}.txt` file in the pack |
| Diff coverage | `diff.patch` covers every file touched by every scope commit. Partial diffs fail. |
| No phantom commits | No commit is referenced in `final-report.md`, `chain-evidence.json`, or `review.yaml` without corresponding evidence |
| Git-log coverage | Every scope commit appears in `git-log.txt` |

**Failure:** Missing per-commit evidence or phantom commits are blocking signals.

### 9. Workspace State Verification

| Check | Pass Condition |
|-------|---------------|
| No false cleanliness claims | "Workspace clean" is NOT claimed when `git-status-after.txt` shows untracked files or deferred files exist |
| Modified tracked accounting | If `modified_tracked > 0`, a deferred record or explicit rationale MUST exist |
| Untracked file accounting | Every untracked file in `git-status-after.txt` is accounted for (committed, removed, or deferred) |

### 10. Replay Detection

| Check | Pass Condition |
|-------|---------------|
| Replay labeling | Any replay output (re-executed hook output) is explicitly labeled as "replay" in its header |
| Original preference | If Phase A hook output exists in `_evidence/hook-output/`, it is used instead of replay |

**Failure:** Unlabeled replay output is a blocking signal. Replay output CANNOT substitute for original output when original was available.

### 11. Test Evidence Quality

| Check | Pass Condition |
|-------|---------------|
| Raw output | `test-output.txt` contains raw test runner output, not a summary or paraphrase |
| Scope accuracy | `test_scope` in `review.yaml` accurately reflects what was run (full_regression, targeted_tests, no_test_rationale) |
| Regression claim support | If "full regression passed" is claimed, the full regression log is included in the pack |

---

## Runtime Evidence Evaluation

When the evidence pack includes runtime behavior claims, the reviewer evaluates the runtime evidence track.

### 12. Runtime Evidence Index

| Check | Pass Condition |
|-------|---------------|
| Index present | `runtime-evidence-index.json` exists when runtime behavior is claimed |
| Index valid | File parses as valid JSON and conforms to `runtime-evidence-index.schema.json` |
| Scenario coverage | All runtime claims in `final-report.md` have corresponding scenario files referenced by the index |

### 13. Stale Evidence Detection

Apply deterministic staleness rules from the Evidence Capture Standard:

| Rule | Condition | Result |
|------|-----------|--------|
| Code version mismatch | Scenario header `Code version` != manifest `head_commit` | Scenario is STALE -- blocking signal |
| Missing timestamp | Scenario header lacks `Generated` field while runtime index requires it | Scenario is STALE -- blocking signal |
| Unindexed file | Scenario file exists but is not referenced by `runtime-evidence-index.json` | Scenario is UNINDEXED -- limitation signal |

### 14. Negative-Path Coverage

| Check | Pass Condition |
|-------|---------------|
| Claim type coverage | Negative-path scenarios cover all claim types (deny_list violations, schema rejections, hook blocks) |
| Scenario status | All negative-path scenarios have explicit PASS/FAIL/SKIP status |
| No false negatives | No negative-path scenario reports PASS for a behavior that should have been blocked |

---

## Verdict Decision Framework

After completing all checks, the reviewer renders a final verdict using the following framework:

### ACCEPTED

All of the following MUST be true:

- `verdict_eligibility` is `eligible_clean`
- All pre-review checks pass (Section: Pre-Review Checklist)
- All consistency checks pass (Section: Evidence Consistency Checks)
- All content quality checks pass (Section: Content Quality Checks)
- No anti-patterns detected
- Runtime evidence checks pass (when applicable)

### ACCEPTED_WITH_LIMITATION

All of the following MUST be true:

- `verdict_eligibility` is `eligible_clean` or `eligible_with_limitations`
- All pre-review checks pass
- All consistency checks pass
- No blocking signals present
- Limitation signals are present and each limitation is:
  - **Specific** -- clearly states what evidence or capability is limited
  - **Bounded** -- states what is still accepted despite the limitation
  - **Actionable** -- states what would remove the limitation in a future revision

### NEEDS_REVISION

Any of the following triggers this verdict:

- `verdict_eligibility` is `needs_more_evidence`
- Blocking signals are present (even if verdict_eligibility was not computed correctly)
- Consistency checks fail
- Content quality checks reveal missing commit evidence or phantom commits

The reviewer MUST list each blocking signal and specify what evidence is needed to resolve the revision.

### REJECTED

Any of the following triggers this verdict:

- `verdict_eligibility` is `not_eligible`
- Schema validation fails for `evidence-manifest.json` or `review.yaml`
- Safety report contains error status
- Anti-patterns are detected (phantom commits, false cleanliness, hardcoded consistency, stale runtime evidence)

The reviewer MUST document the critical failure(s) that caused rejection.

---

## Limitation Documentation

When issuing ACCEPTED_WITH_LIMITATION, each limitation MUST be documented with three components:

### Specific (What is limited)

Describe exactly which evidence or capability has limited coverage. Avoid vague statements like "some tests were not run." Instead: "Only targeted tests were run (tests/test_hook.py, tests/test_schema.py); the remaining 38 test files were not executed."

### Bounded (What is still accepted)

State what the evidence DOES prove despite the limitation. Example: "The targeted tests prove hook blocking behavior for deny_list paths and schema validation for review.yaml. These are the two capabilities modified in this task."

### Actionable (What would remove the limitation)

State what action would resolve the limitation in a future revision. Example: "Run the full test suite (pytest tests/) and include the output as test-output.txt. This would upgrade the pack from eligible_with_limitations to eligible_clean."

### Limitation Documentation Template

```markdown
### Limitation 1: Only Targeted Tests Run

**Specific:** test-output.txt contains results for 2 test files (tests/test_hook.py, tests/test_schema.py) out of 40 total test files in the repository.

**Bounded:** The two test files cover the hook blocking behavior and schema validation changes made in this task. The 38 untested files were not modified by the scope commits.

**Actionable:** Run `pytest tests/` to execute the full suite and regenerate test-output.txt with complete results.
```

---

## Reviewer Workflow Summary

```
1. PRE-REVIEW
   ├── Check Tier 0 file presence (Section: Pre-Review Checklist, Step 1)
   ├── Validate parse correctness (Section: Pre-Review Checklist, Step 2)
   └── Gate: if any fail → halt, record signal, set verdict eligibility

2. CONSISTENCY
   ├── Check modified_tracked agreement (Section: Check 4)
   ├── Check untracked count agreement (Section: Check 5)
   ├── Check commit count agreement (Section: Check 6)
   └── Check test count agreement (Section: Check 7)

3. CONTENT QUALITY
   ├── Verify commit evidence completeness (Section: Check 8)
   ├── Verify workspace state claims (Section: Check 9)
   ├── Detect unlabeled replay output (Section: Check 10)
   └── Verify test evidence quality (Section: Check 11)

4. RUNTIME EVIDENCE (when applicable)
   ├── Evaluate runtime evidence index (Section: Check 12)
   ├── Detect stale evidence (Section: Check 13)
   └── Verify negative-path coverage (Section: Check 14)

5. VERDICT
   ├── Read verdict_eligibility from review.yaml
   ├── Apply verdict decision framework (Section: Verdict Decision Framework)
   ├── Document limitations (if ACCEPTED_WITH_LIMITATION)
   └── Record final verdict in SADP 0.R.2 review artifact
```

---

## Related Documents

- [Evidence Capture Standard](evidence-capture-standard.md) -- the canonical evidence pack contract
- [Evidence Pack Standard](evidence-pack-standard.md) -- the predecessor standard (extended by ECS)
- [Evidence Capture Workflow](evidence-capture-workflow.md) -- Phase A/B capture workflow
- [Evidence Generation Hygiene](evidence-generation-hygiene.md) -- generation rules and anti-patterns
- [Pre-GPT Review Gate](pre-gpt-review-gate.md) -- gate evaluation protocol
- [Reviewer Playbook](reviewer-playbook.md) -- general reviewer guidance
- [Universal Agent Workflow Standard](universal-agent-workflow-standard.md) -- overarching workflow standard
