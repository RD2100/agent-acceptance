---
Task: EVIDENCE-CAPTURE-STANDARD-A2
Document: Evidence Capture Standard
Version: 1.0.0
Date: 2026-06-12
Status: Active
---

# Evidence Capture Standard

## Purpose

This document defines the canonical evidence pack contract for all future agent tasks. An evidence pack is a structured collection of machine-verifiable artifacts that proves what an agent did and what state the workspace is in after execution.

Evidence packs must be:

1. **Complete** -- containing all required files for the task's claims
2. **Reviewable** -- structured for efficient GPT and human evaluation
3. **Schema-aware** -- conforming to published JSON and YAML schemas
4. **Resistant to missing/stale evidence acceptance** -- detecting and rejecting incomplete or outdated artifacts

This standard supersedes and extends the Evidence Pack Standard (UNIVERSAL-AGENT-WORKFLOW-STANDARD-A1). Where conflicts exist, this document takes precedence.

---

## Tiered Required Files

Evidence packs are organized into three tiers. Tier 0 files are mandatory for all packs. Tier 1 files are conditionally required based on task claims. Tier 2 files are optional but recommended.

### Tier 0: Required for ALL Evidence Packs (10 files)

Every evidence pack MUST contain all of the following files. Omission of any Tier 0 file is grounds for immediate rejection.

| # | File | Description |
|---|------|-------------|
| 1 | `review.yaml` | Machine-readable evidence metadata with `verdict_eligibility` field. MUST conform to `review.schema.yaml`. Profile: `ecs-v1`. |
| 2 | `final-report.md` | Execution summary covering what was done, what was verified, and what remains open. |
| 3 | `git-status-before.txt` | Pre-task workspace state captured via `git status --porcelain`. REQUIRED when workspace transition is claimed (e.g., "workspace went from dirty to clean"). |
| 4 | `git-status-after.txt` | Post-commit workspace state captured via `git status --porcelain`. MUST reflect state AFTER the final commit in scope. |
| 5 | `diff.patch` or `git-show.txt` | What changed in scope commits. Combined diff across all commits claimed in scope, OR full `git show` output for single-commit tasks. |
| 6 | `test-output.txt` or `no-test-rationale.md` | Raw pytest (or equivalent test runner) output captured from terminal. MUST be raw output, not a summary. If no tests were run, `no-test-rationale.md` MUST explicitly justify why. |
| 7 | `safety-report.json` | Valid JSON security assessment. MUST include fields for deny-list path checks (`deny_paths`), secret-scan results (`secret_scan`), and hook-integrity status (`hook_integrity`). |
| 8 | `secret-scan-output.txt` | Raw scanner output. REQUIRED when `deny_paths` or mock secret fixtures are involved in the task. MUST NOT be staged in git **unless explicitly covered by `allow_paths` in policy.yaml** (see DR-20260612-ALLOW-PATHS). |
| 9 | `task-spec.yaml` or `current-task.yaml` | TaskSpec snapshot at execution time. Contains task ID, goal, constraints, and acceptance criteria as they existed when work began. |
| 10 | `evidence-manifest.json` | Machine-readable manifest conforming to `evidence-manifest.schema.json`. Lists all files in the pack with classification, condition, and hash. |

**Key differences from Evidence Pack Standard:**

- `review.yaml` now includes `verdict_eligibility` (see Verdict Eligibility Rules)
- `evidence-manifest.json` is now Tier 0 (was not required before)
- `task-spec.yaml` is now Tier 0 (ensures task context is preserved)
- `git-status-before.txt` is Tier 0 when workspace transition claimed (was conditional before)

### Tier 1: Conditionally Required Files

The following files are REQUIRED when the conditions described apply. Failure to include a conditionally required file creates a limitation signal (see Verdict Eligibility Rules).

| File | Condition |
|------|-----------|
| `runtime-evidence-index.json` | When runtime behavior is claimed (e.g., "hook blocks X", "script validates Y"). MUST conform to `runtime-evidence-index.schema.json`. |
| Negative-path evidence files | When negative-path scenarios exist (e.g., deny_list violations, schema rejections). One `.txt` file per scenario. |
| `hook-output/latest.json` | When hook behavior is modified or when claiming hook-related functionality. MUST be Phase A output from Evidence Capture Workflow. |
| `conversation-health/latest.json` | When conversation health is involved (e.g., claiming "conversation health improved"). MUST conform to conversation health schema. |
| `startup-read-latest.json` | When startup read gate is relevant (e.g., claiming "agent read governance files at startup"). |
| Full regression log | When claiming "full regression passed". MUST be raw test runner output for the complete test suite. |
| Migration record | When registry migration occurs (e.g., adding/removing capabilities from acceptance-script-registry.md). |
| Schema validation output | When schema changes are made (e.g., modifying `.schema.json` or `.schema.yaml` files). |

**Backward compatibility:** Existing `.txt` scenario files (old format) are still parseable and acceptable. The new `runtime-evidence-index.json` is an index that references these files, not a replacement.

### Tier 2: Optional but Recommended

These files enhance the evidence pack but are not required. Their absence does not impact verdict eligibility.

- Raw command logs (full terminal session capture)
- Screenshots of UI changes or visual regressions
- Debug output from failing tests (before fixes were applied)
- Coverage output (pytest-cov, istanbul, etc.)
- Performance metrics (timing comparisons, benchmark results)
- Linter output (eslint, pylint, etc.)

---

## Verdict Eligibility Rules

`verdict_eligibility` is a machine-computed field in `review.yaml` that classifies the evidence pack's completeness. It is a RECOMMENDATION to reviewers, not a final verdict.

### Eligibility Enum Values

| Value | Meaning | Reviewer Guidance |
|-------|---------|-------------------|
| `eligible_clean` | All Tier 0 files present, no blocking or limitation signals | May consider ACCEPTED |
| `eligible_with_limitations` | All Tier 0 files present, limitation signals present, no blocking signals | May consider ACCEPTED_WITH_LIMITATION |
| `needs_more_evidence` | Tier 0 files missing OR blocking signals present | Should consider NEEDS_REVISION |
| `not_eligible` | Critical failures (schema invalid, safety error, etc.) | Should consider REJECTED |

### Hard Blocking Signals

These signals force `verdict_eligibility: needs_more_evidence` or `not_eligible`:

| Signal | Trigger | Eligibility Impact |
|--------|---------|-------------------|
| `required_files_missing` | Any Tier 0 file absent from pack | `needs_more_evidence` |
| `modified_tracked_gt_zero` | `modified_tracked > 0` in safety-report.json without deferred record | `needs_more_evidence` |
| `tests_failed_without_explanation` | Test failures in test-output.txt without documented rationale | `needs_more_evidence` |
| `claimed_full_regression_but_log_missing` | Claiming "full regression passed" but no full regression log in pack | `needs_more_evidence` |
| `runtime_behavior_claimed_but_no_runtime_artifact` | Claiming runtime behavior but `runtime-evidence-index.json` missing | `needs_more_evidence` |
| `schema_invalid_manifest_or_review_yaml` | `evidence-manifest.json` or `review.yaml` fails schema validation | `not_eligible` |
| `safety_report_error` | `safety-report.json` contains error status or fails to parse | `not_eligible` |

### Limitation Signals

These signals allow `verdict_eligibility: eligible_with_limitations`:

| Signal | Trigger | Limitation Description |
|--------|---------|------------------------|
| `startup_read_missing` | `startup-read-latest.json` absent when startup read relevant | Cannot verify agent read governance files at startup |
| `conversation_health_suggest_handoff` | Conversation health indicates degradation | Task may require handoff to fresh session |
| `advisory_stage_warning` | Advisory hook stage (manifest-regen, test-governance) returned non-zero | Non-blocking hook issue detected |
| `only_targeted_tests_run` | test-output.txt shows subset of tests, not full suite | Regression coverage is limited |
| `runtime_behavior_proved_by_tests_only` | Runtime claims supported by unit tests but no scenario files | Runtime evidence is indirect |
| `missing_optional_files` | Tier 2 files absent | Pack lacks supplementary evidence |
| `ai_guard_warning_explained` | AI guard issued warning but agent provided documented explanation | Warning acknowledged and justified |

### Record-Only Signals

These signals are recorded but do not impact eligibility:

| Signal | Description |
|--------|-------------|
| `untracked_total` | Count of untracked files in git-status-after.txt |
| `session_artifacts` | Count of session artifacts (builder scripts, temp files) |
| `neg_009_count` | Count of neg-009 violations (if any) |
| `generated_at` | Timestamp when evidence pack was generated |
| `pack_size` | Total size of evidence pack in bytes |
| `zip_sha256` | SHA-256 hash of evidence pack ZIP (when ZIP format used) |

### Computing Verdict Eligibility

The `verdict_eligibility` field MUST be computed from the signals present in the evidence pack. The algorithm:

```
1. Check for not_eligible signals (schema_invalid, safety_report_error)
   → If any present: verdict_eligibility = "not_eligible"

2. Check for blocking signals (required_files_missing, modified_tracked_gt_zero, etc.)
   → If any present: verdict_eligibility = "needs_more_evidence"

3. Check for limitation signals (startup_read_missing, only_targeted_tests_run, etc.)
   → If any present: verdict_eligibility = "eligible_with_limitations"

4. Otherwise: verdict_eligibility = "eligible_clean"
```

**Forbidden:** Hardcoding `verdict_eligibility` without computing from signals. This is an anti-pattern (see Anti-Patterns section).

---

## Evidence Completeness Classification

Each file in the evidence pack is classified in `evidence-manifest.json` using the `completeness` field:

| Classification | Meaning | Example |
|----------------|---------|---------|
| `required` | Tier 0 file, must be present | `review.yaml`, `safety-report.json` |
| `conditional` | Tier 1 file, must be present when condition applies | `runtime-evidence-index.json` (when runtime behavior claimed) |
| `optional` | Tier 2 file, nice to have | Coverage output, performance metrics |
| `not_applicable` | Tier 1 file, condition does not apply | `conversation-health/latest.json` (when conversation health not involved) |
| `missing_but_limitation` | Missing conditional file, creates limitation signal | `startup-read-latest.json` absent when startup read relevant |
| `missing_blocking` | Missing required file, blocks eligibility | `review.yaml` absent |

**Example manifest entry:**

```json
{
  "file": "runtime-evidence-index.json",
  "tier": 1,
  "completeness": "conditional",
  "condition": "runtime_behavior_claimed",
  "condition_met": true,
  "present": true,
  "sha256": "abc123..."
}
```

---

## Full Regression Claims

When an evidence pack claims "full regression passed", the following rules apply:

1. **Full regression log MUST be included.** The complete test runner output for the entire test suite MUST be in the pack. Claiming "full regression passed" without the log is a blocking signal (`claimed_full_regression_but_log_missing`).

2. **Distinguish test scope in review.yaml.** The `test_scope` field MUST be one of:
   - `full_regression` -- complete test suite was run
   - `targeted_tests` -- subset of tests was run (specify which)
   - `no_test_rationale` -- no tests run, rationale provided in `no-test-rationale.md`

3. **Targeted tests must be explicit.** When `test_scope: targeted_tests`, the `tests_run` field MUST list the specific test files or test patterns executed.

4. **No false regression claims.** Claiming "full regression passed" when only targeted tests were run is an anti-pattern.

**Example review.yaml:**

```yaml
test_scope: full_regression
tests_run: "pytest tests/"
test_output_file: test-output.txt
test_result: passed
test_count:
  total: 142
  passed: 142
  failed: 0
  skipped: 3
```

---

## Runtime Evidence Format

Runtime evidence uses a dual-track system: human-readable `.txt` scenario files and machine-readable `runtime-evidence-index.json`.

### Scenario File Format (.txt)

Each scenario file MUST include a standardized header:

```
# Scenario: <scenario_name>
# Expected: <expected result description>
# Actual: <actual result description>
# Status: PASS | FAIL | SKIP
# Source: <command or script that produced this result>
# Generated: <ISO-8601 timestamp>
# Code version: <head_commit hash>

<scenario body: detailed output, logs, assertions>
```

**Example:**

```
# Scenario: hook_blocks_secret_staging
# Expected: pre-commit hook rejects commit with secret-scan-output.txt staged
# Actual: hook exited with code 1, commit blocked
# Status: PASS
# Source: bash test_hook_secret_staging.sh
# Generated: 2026-06-12T10:30:00Z
# Code version: abc123def

$ git add secret-scan-output.txt
$ git commit -m "test secret staging"
[pre-commit] BLOCKED: secret-scan-output.txt is on deny_list
[pre-commit] Commit rejected. Remove deny-listed files from staging.
Exit code: 1
```

### Runtime Evidence Index (runtime-evidence-index.json)

The index file MUST conform to `runtime-evidence-index.schema.json`:

```json
{
  "schema_version": "1.0.0",
  "head_commit": "abc123def",
  "generated_at": "2026-06-12T10:35:00Z",
  "scenarios": [
    {
      "name": "hook_blocks_secret_staging",
      "file": "hook-blocks-secret-staging.txt",
      "status": "PASS",
      "type": "negative_path",
      "claim": "pre-commit hook rejects commit with secret-scan-output.txt staged"
    }
  ]
}
```

### Backward Compatibility

Existing `.txt` scenario files (old format without full header) are still parseable and acceptable. The runtime evidence index references these files by name. When creating new scenario files, use the standardized header format.

---

## Stale Evidence Detection

Stale evidence occurs when scenario files reference an outdated code version. The following deterministic rules detect staleness:

| Rule | Condition | Result |
|------|-----------|--------|
| Code version mismatch | Scenario header `Code version` != manifest `head_commit` | Scenario is stale |
| Missing generated_at | Scenario file lacks `Generated` header while runtime index requires it | Scenario is stale |
| Unindexed file | Scenario file exists in `extra/` but not referenced by `runtime-evidence-index.json` | Scenario is unindexed |

**Stale evidence handling:**

- Stale scenarios MUST be regenerated before inclusion in the evidence pack
- Unindexed scenarios MUST be added to the index or removed from the pack
- The `stale_scenarios` field in `review.yaml` MUST list any stale scenarios detected

**Example detection:**

```
Scenario file: hook-blocks-secret-staging.txt
  Code version in header: abc123def
  head_commit in manifest: xyz789abc
  → STALE (mismatch)

Scenario file: validation-rejects-bad-schema.txt
  Generated header: (absent)
  Runtime index requires generated_at: true
  → STALE (missing timestamp)
```

---

## Consistency Ring

All numerical values MUST agree across the following files:

- `git-status-after.txt`
- `safety-report.json`
- `review.yaml`
- `final-report.md`
- `evidence-manifest.json`

### Fields That MUST Agree

| Concept | Where it appears |
|---------|-----------------|
| Number of untracked files after final commit | `git-status-after.txt` (counted), `safety-report.json` (`post_commit_untracked`), `review.yaml` (`post_commit_untracked`), `final-report.md` (narrative count), `evidence-manifest.json` (`workspace_state.untracked_total`) |
| Number of modified tracked files | `safety-report.json` (`modified_tracked`), `review.yaml` (`modified_tracked`), `final-report.md` (narrative), `evidence-manifest.json` (`workspace_state.modified_tracked`) |
| Number of commits in scope | `chain-evidence.json` (array length), `git-log.txt` (line count), `review.yaml` (`commits_in_scope`), `final-report.md` (narrative count), `evidence-manifest.json` (`commits.count`) |
| Number of files changed | `diff.patch` (file count), `safety-report.json` (`files_changed`), `review.yaml` (`files_changed`), `evidence-manifest.json` (`commits.files_changed`) |

### Consistency Check Computation

The `consistency_check.all_files_agree` field in `review.yaml` MUST be COMPUTED from actual data, never hardcoded:

```yaml
consistency_check:
  all_files_agree: true  # COMPUTED, not hardcoded
  checks:
    - field: modified_tracked
      safety_report: 0
      review_yaml: 0
      final_report: 0
      manifest: 0
      agree: true
    - field: untracked_total
      git_status_after: 5
      safety_report: 5
      review_yaml: 5
      manifest: 5
      agree: true
```

**Forbidden:** Hardcoding `all_files_agree: true` without computing from actual values. This is an anti-pattern.

---

## Relationship to SADP 0.R.2 Review YAML

The ECS `review.yaml` and the SADP 0.R.2 `review.yaml` are currently NOT equivalent:

| Aspect | ECS review.yaml | SADP 0.R.2 review.yaml |
|--------|-----------------|------------------------|
| Profile | `ecs-v1` | `sadp-0r2` |
| Purpose | Evidence pack metadata | Reviewer protocol artifact |
| Scope | Pack completeness and eligibility | Reviewer evaluation and verdict |
| Required fields | `verdict_eligibility`, `pack_files`, `consistency_check` | `reviewer_verdict`, `findings`, `recommendation` |

**Current state:** Both files coexist. Evidence packs include ECS `review.yaml`. SADP reviewers produce SADP 0.R.2 `review.yaml` as part of their evaluation.

**Future alignment:** Task SADP-REVIEW-YAML-ALIGNMENT-A1 will define the merge strategy to unify these formats.

---

## Anti-Patterns (Forbidden)

The following practices are explicitly forbidden. Detection of any anti-pattern SHALL result in immediate rejection of the evidence pack.

### A1: Text-Only Submission

Submitting a narrative summary without a conforming evidence pack. Every submission MUST include actual files, not descriptions of what the files would contain.

### A2: Phantom Commits

Claiming more commits in scope than are evidenced. If a commit is mentioned in `final-report.md`, `chain-evidence.json`, or `review.yaml` but lacks corresponding evidence (`git-show-{commit}.txt` or `diff-{commit}.patch`), the pack is invalid.

### A3: Arithmetic Errors

Internal contradictions in numerical breakdowns. For example, claiming "17 staged + 2 untracked = 21 total" when 17 + 2 = 19, not 21.

### A4: False Zero-Untracked Claims

Stating `post_commit_untracked = 0` or "0 untracked files" while `git-status-after.txt` shows untracked files present.

### A5: Staged Secret-Scan Output

Including `secret-scan-output.txt` in git staging. This file SHALL be excluded from version control because its contents may trigger deny_list violations.

### A6: Premature Evidence Generation

Generating evidence files BEFORE the final commit is made. This causes post-commit state mismatch because the evidence will not reflect changes introduced by the final commit. Evidence MUST be generated AFTER all scope commits are complete.

### A7: Missing Evidence Manifest

Submitting an evidence pack without `evidence-manifest.json`. The manifest is now Tier 0 and required for all packs.

### A8: False Clean Eligibility Claim

Claiming `verdict_eligibility: eligible_clean` when Tier 0 files are missing or blocking signals are present. The eligibility value MUST be computed from signals, not manually asserted.

### A9: Hardcoded Consistency Check

Setting `consistency_check.all_files_agree: true` without computing from actual field values across the consistency ring. The check MUST be derived from data, not hardcoded.

### A10: Replay Evidence Without Labeling

When pre-commit hook output is captured via replay (re-execution after the fact) rather than original hook invocation, the output file MUST be labeled as "replay" in its header. Replay output CANNOT substitute for original raw hook output when original output was available at execution time.

### A11: Stale Runtime Evidence

Including scenario files where `Code version` != manifest `head_commit`. Stale scenarios MUST be regenerated before inclusion in the pack.

---

## Submission Checklist

Before submitting an evidence pack, the agent SHALL verify:

- [ ] All 10 Tier 0 files are present
- [ ] All applicable Tier 1 files are present (check conditions)
- [ ] `evidence-manifest.json` parses as valid JSON and conforms to schema
- [ ] `review.yaml` parses as valid YAML and conforms to schema
- [ ] `verdict_eligibility` is computed from signals (not hardcoded)
- [ ] `consistency_check.all_files_agree` is computed from actual values (not hardcoded)
- [ ] Every commit in scope has corresponding evidence (`git-show-{commit}.txt` or `diff-{commit}.patch`)
- [ ] Every commit in scope appears in `git-log.txt`
- [ ] `test_scope` field accurately reflects tests run (full_regression, targeted_tests, no_test_rationale)
- [ ] No replay output is presented as original without labeling
- [ ] No stale scenario files (Code version matches head_commit)
- [ ] No anti-patterns are present
- [ ] Evidence was generated AFTER the final scope commit

---

## Related Documents

- [Evidence Pack Standard](evidence-pack-standard.md)
- [Evidence Capture Workflow](evidence-capture-workflow.md)
- [Evidence Generation Hygiene](evidence-generation-hygiene.md)
- [Evidence Pack Review Rules](evidence-pack-review-rules.md)
- [Universal Agent Workflow Standard](universal-agent-workflow-standard.md)
- [Workspace Closure Standard](workspace-closure-standard.md)
- [Pre-GPT Review Gate](pre-gpt-review-gate.md)
