# Pre-GPT-Review Gate -- RD2100 Agent Runtime

> Version: 1.0 | 2026-06-11
> Status: ACTIVE (P0 enforcement)
> Scope: All evidence pack submissions to GPT independent reviewer
> Derived from: R15-R18 reviewer findings, SADP 0.R.2, operations-manual.md
> Protection level: SADP protected (docs/agent-runtime/ path, governancePatterns)

---

## 0. Purpose

Every submission to the GPT independent reviewer must be backed by a complete, machine-verifiable evidence pack. The pre-GPT-review gate enforces that all required evidence artifacts exist and are valid **before** the submission is sent to the reviewer. Submitting incomplete evidence wastes reviewer cycles, produces BLOCKED verdicts, and creates cascading correction rounds.

**Hard rule**: TEXT-ONLY SUMMARIES ARE EXPLICITLY FORBIDDEN. Every claim must be backed by a file in the evidence pack. A submission that consists only of a text description without supporting artifact files is an automatic BLOCKED verdict.

---

## 1. Required Evidence Artifacts

Every GPT review submission MUST include all of the following files in the evidence pack directory (`_evidence/<TASK-ID>/`). Missing any required file is a BLOCKING finding.

### 1.1 Evidence Pack ZIP File

| Field | Detail |
|-------|--------|
| **File** | `EVIDENCE_PACK_<TASK-ID>.zip` |
| **Content** | All evidence artifacts bundled for reviewer consumption |
| **Format rules** | Repo-relative paths (not `source/` or absolute paths); ZIP must be extractable and independently verifiable |
| **Why required** | The reviewer reads the ZIP as the primary evidence source. If the ZIP is missing or malformed, no review can proceed |

**Failure example (R15-BLOCKING-01)**: R15 evidence pack used non-repo-relative paths (`source/` instead of `scripts/`). The reviewer could not map ZIP contents to actual repository paths, producing BLOCKING-01. This was fixed in R16 by restructuring the ZIP with repo-relative paths.

### 1.2 diff.patch or diff-stat

| Field | Detail |
|-------|--------|
| **File** | `diff.patch` (full diff) or `diff-stat.txt` (summary with file-level statistics) |
| **Content** | The exact changes made by this task, scoped to the task's `write_set` |
| **Format rules** | Must be scoped to task-specific changes only; must not contain out-of-scope files |
| **Why required** | The reviewer uses the diff to verify that the agent modified only what it was authorized to modify |

**Failure example (R16-BLOCKING-04)**: The canonical `diff.patch` contained out-of-scope files -- files that were not part of the task's declared `write_set`. The reviewer flagged this as BLOCKING-04 because the diff scope did not match the task scope. Fixed in R17 by providing a manually scoped `diff.patch` containing only the task-relevant changes.

### 1.3 test-output.txt

| Field | Detail |
|-------|--------|
| **File** | `test-output.txt` |
| **Content** | Full pytest (or equivalent test framework) output with pass/fail counts, warnings, and execution time |
| **Format rules** | Must be actual command output, not a hand-written summary; must include the test command used |
| **Why required** | The reviewer verifies that existing tests pass and no regressions were introduced |

**Failure example (R16-BLOCKING-03)**: The evidence pack showed test results but the reviewer found the ZIP was "not independently reproducible" -- 205 tests passed, 47 failed when extracting and running from the ZIP alone. R16 had to explicitly declare the test environment to resolve this, and R17 acknowledged the limitation: "test results from full repo, not ZIP-independent."

### 1.4 safety-report.json

| Field | Detail |
|-------|--------|
| **File** | `safety-report.json` |
| **Content** | Security assessment including secret scan results, deny_paths coverage, file scope check results |
| **Format rules** | Must be valid pure JSON (no comments, no trailing commas, no appended text); all numeric counts must match the actual evidence files |
| **Why required** | Security is a P0 gate. The safety report is the structured security evidence |

**Failure example (R15-BLOCKING-03)**: The DRY_RUN JSON output was not pure -- it had a text summary appended to the JSON body. The reviewer rejected this as `R15-BLOCKING-03: DRY_RUN JSON not pure (appended summary)`. Fixed in R16 by ensuring all JSON files contain only valid JSON with no appended text.

**Failure example (R18 safety-report stale count)**: R18 follow-up reviewer noted: "safety-report.json 中 secret_scan.files_scanned 仍写 20，而实际 secret-scan-output.txt 覆盖 26 项." The safety report's internal count was stale compared to the actual scan evidence. The reviewer accepted the actual scan output as authoritative but recorded the inconsistency as a permanent limitation.

### 1.5 chain-evidence.json

| Field | Detail |
|-------|--------|
| **File** | `chain-evidence.json` |
| **Content** | Commit chain evidence: every commit in scope with its hash, message, timestamp, and parent relationship |
| **Format rules** | Must be valid pure JSON; every commit claimed in scope must have corresponding `git show` evidence |
| **Why required** | The reviewer verifies that the commit chain is complete and no commits are hidden or fabricated |

**Failure example (R18 BLOCKING-02)**: Commit `6022c187` was named in the R18 submission but lacked `git show` evidence. The reviewer issued `BLOCKING-02: 6022c187 evidenced with git-show and diff-stat`. The follow-up submission had to include `diff-6022c187.patch` and `git-show-6022c187.txt` to close this blocker.

### 1.6 review.md

| Field | Detail |
|-------|--------|
| **File** | `review.md` |
| **Content** | Narrative review written by the reviewer role (not the executor); describes what was reviewed, findings, and verdict reasoning |
| **Format rules** | Must be written from the reviewer perspective; must not be authored by the executor |
| **Why required** | SADP 0.R mandates executor/reviewer separation. The review.md is the reviewer's narrative evidence |

**Failure example (R16-BLOCKING-01)**: R16 submission was missing `review.md` entirely. The reviewer flagged `R16-BLOCKING-01: review.md missing` because without it, there was no evidence of independent review -- only the executor's claims existed. This was a carry-over from R15-BLOCKING-02 which was only PARTIALLY_CLOSED. Fixed in R17 by creating the review.md file.

### 1.7 review.yaml

| Field | Detail |
|-------|--------|
| **File** | `review.yaml` |
| **Content** | Structured reviewer verdict in machine-readable format |
| **Required fields** | `reviewer_role`, `reviewer_id`, `executor_id`, `verdict` (pass/blocked/fail/escalate), `findings` list |
| **Format rules** | Must be valid YAML; reviewer_id must differ from executor_id |
| **Why required** | Machine-parseable verdicts enable automated compliance tracking across review rounds |

### 1.8 final-report.md

| Field | Detail |
|-------|--------|
| **File** | `final-report.md` |
| **Content** | Execution summary: task description, commits in scope, test results, post-commit workspace state, blocker resolution status, internal consistency verification |
| **Format rules** | Must report actual numbers that match all other evidence files; workspace state section must match `git-status-after.txt` |
| **Why required** | The final report is the executor's consolidated claim. All other evidence files should support it |

**Failure example (R18 initial closure inconsistency)**: The initial R18-WORKSPACE-CLOSURE final-report claimed `Total entries in git status: 27` (NEG-009: 17, Secret scan: 3, Session artifacts: 7). The follow-up R18-WORKSPACE-CLOSURE-SLIM corrected this to 28 total (NEG-009: 17, Secret scan: 3, Session artifacts: 8). The inconsistency between the two reports required explicit reconciliation in the follow-up evidence.

### 1.9 git-status-before.txt and git-status-after.txt

| Field | Detail |
|-------|--------|
| **Files** | `git-status-before.txt`, `git-status-after.txt` |
| **Content** | Full `git status --porcelain` output captured before and after task execution |
| **When required** | Whenever workspace state is part of the submission claim (especially closure claims) |
| **Format rules** | Must be actual command output, not hand-typed; must include timestamp of capture |
| **Why required** | Before/after git status proves what the task actually changed in the workspace |

**Failure example (R18 BLOCKING-07)**: GPT reviewer flagged `git status 与说明不一致` -- the agent's written description of workspace state did not match actual `git status` output. This was a blocker that required the agent to reconcile its description with actual command output and provide the corrected count with item-by-item registration.

### 1.10 deferred-files-register.yaml

| Field | Detail |
|-------|--------|
| **File** | `deferred-files-register.yaml` |
| **Content** | Complete register of all untracked files that remain in the workspace after task completion |
| **When required** | When any untracked files remain after task execution (i.e., workspace is not fully clean) |
| **Format rules** | Must be valid YAML; must list every untracked file path exactly once; categorized breakdown must sum to total |
| **Why required** | Untracked files are liabilities. The register makes them visible and accountable |

**Failure example (R18 BLOCKING-06)**: The `deferred-files-register.yaml` did not initially match `git-status-after.txt`. The reviewer required reconciliation: both files had to show identical counts and paths. After correction, both showed 26 untracked entries with matching structure: `neg009_deferred: 17, gate0_deferred: 1, session_artifacts: 7, nul_device_file: 1`.

### 1.11 secret-scan-output.txt

| Field | Detail |
|-------|--------|
| **File** | `secret-scan-output.txt` |
| **Content** | Output of secret scanning tool covering all files in the workspace |
| **When required** | When `deny_paths` policy is active, or when mock secret fixtures are part of the test infrastructure |
| **Format rules** | Must cover every file in the workspace; per-file results (CLEAN, SKIPPED, FOUND); summary counts must match actual file count |
| **Why required** | Proves no real secrets were accidentally committed alongside test fixtures |

**Failure example (R18 stale scan count)**: The `safety-report.json` claimed `secret_scan.files_scanned: 20` but the actual `secret-scan-output.txt` covered 26 files. The reviewer noted this as a limitation: "以 secret-scan-output.txt 和 deferred-files-register.yaml 为准" -- meaning the raw scan output is authoritative over the summary report, but the inconsistency is a permanent record.

---

## 2. Forbidden Submission Patterns

The following submission patterns are explicitly forbidden and will receive an automatic BLOCKED verdict:

| Forbidden Pattern | Description | Why Forbidden |
|-------------------|-------------|---------------|
| **Text-only summary** | Submission consists only of a text description without artifact files | No independent verification possible |
| **Partial evidence** | Some required files present, others missing without justification | Incomplete evidence cannot be independently verified |
| **Stale evidence** | Evidence files contain numbers that contradict each other | Internal inconsistency indicates fabrication or carelessness |
| **Self-referencing hashes** | SHA256 hashes that include the hash file itself in the hash computation | Logically impossible to verify |
| **Replay-only evidence** | All hook evidence is replay-style with no original raw hook output | Replay evidence is reconstructed, not captured at execution time |

**Failure example (R15 text-only history)**: Rounds R3 through R14 (12 consecutive rounds) submitted text-only evidence without ZIP-based evidence packs. R15-INTEGRITY-01 (severity P0_PROCESS) retroactively flagged all 12 rounds as `MAINTAINED_WITH_EVIDENCE_INTEGRITY_LIMITATION`. The impact statement was explicit: "prior text-only submissions not independently verifiable" and "existing technical verdicts maintained but with evidence gap."

**Failure example (R16-BLOCKING-02 self-referencing hashes)**: The SHA256 hash file (`hashes.sha256`) and the manifest (`MANIFEST.json`) included their own hashes in the hash computation, creating a self-referencing loop. The reviewer flagged this as logically unverifiable. Fixed in R17 by excluding MANIFEST.json and hashes.sha256 from the hash list.

---

## 3. Pre-Submission Checklist (Machine-Verifiable)

```yaml
pre_gpt_review_gate:
  evidence_pack_zip:
    exists: true | false
    path: "<zip_file_path>"
    size_kb: <number>
    file_count: <number>
    paths_repo_relative: true | false
  
  diff_patch:
    exists: true | false
    scoped_to_write_set: true | false
    out_of_scope_files: [] | [<file_paths>]
  
  test_output:
    exists: true | false
    actual_command_output: true | false
    pass_count: <number>
    fail_count: <number>
    warning_count: <number>
  
  safety_report:
    exists: true | false
    valid_json: true | false
    secret_scan_count_matches: true | false
    reported_count: <number>
    actual_scan_count: <number>
  
  chain_evidence:
    exists: true | false
    valid_json: true | false
    commits_claimed: [<commit_hashes>]
    git_show_evidence_for_all: true | false
    missing_git_show: [] | [<commit_hashes>]
  
  review_md:
    exists: true | false
    reviewer_perspective: true | false
  
  review_yaml:
    exists: true | false
    valid_yaml: true | false
    reviewer_id_differs_from_executor: true | false
    verdict: pass | blocked | fail | escalate
  
  final_report:
    exists: true | false
    workspace_state_matches_git_status_after: true | false
    commit_count_matches_chain_evidence: true | false
  
  git_status:
    before_exists: true | false
    after_exists: true | false
  
  deferred_register:
    required: true | false
    exists: true | false | n/a
    valid_yaml: true | false | n/a
    matches_git_status_after: true | false | n/a
  
  secret_scan:
    required: true | false
    exists: true | false | n/a
    covers_all_files: true | false | n/a
  
  internal_consistency:
    all_counts_agree: true | false
    discrepancies: [] | [<description_of_mismatch>]
```

All required fields must evaluate to `true` before submission. Any `false` on a required field is a BLOCKING finding.

---

## 4. Evidence Artifact Dependency Graph

```
diff.patch ──────────> write_set (from TaskSpec)
     │                        │
     v                        v
test-output.txt        conflict_registry
     │
     v
safety-report.json ──> secret-scan-output.txt
     │                        │
     v                        v
chain-evidence.json    deferred-files-register.yaml
     │                        │
     v                        v
git-show-*.txt         git-status-after.txt
     │                        │
     v                        v
review.md ──────────> review.yaml ──────────> final-report.md
                                              │
                                              v
                                       git-status-before.txt
                                       git-status-after.txt
```

Every arrow represents a consistency check. If the source and target report different numbers, the submission has an internal consistency violation.

---

## 5. Submission State Machine

```
                DRAFT
                  │
          ┌───────┴────────┐
          │ Pre-GPT Gate    │
          │ (this document) │
          └───────┬────────┘
                  │
          ┌───────┴────────────────────┐
          │                            │
     All checks pass             Any check fails
          │                            │
          v                            v
   READY_FOR_REVIEW            NEEDS_MORE_EVIDENCE
          │                            │
          v                            │
   Submit to GPT reviewer              │
          │                            │
          v                            │
   ┌──────┴──────┐                     │
   │             │                     │
ACCEPTED    BLOCKED ───────────────────┘
   │             │
   │        (fix and re-submit)
   v
ACCEPTED_WITH_LIMITATION
   │
   v
(limitations carried forward to next round)
```

**Transition rules**:
- BLOCKED cannot become ACCEPTED without new evidence files (not just new text descriptions)
- ACCEPTED_WITH_LIMITATION must preserve its limitations in all future reports
- NEEDS_MORE_EVIDENCE requires the specific missing files to be added before re-submission
- No state transition is valid if it skips the pre-GPT gate checklist

---

## 6. Integration with SADP 0.R.2

| SADP 0.R.2 Canonical File | This Gate Section | Status |
|---------------------------|-------------------|--------|
| `diff.patch` | 1.2 | Required |
| `test-output.txt` | 1.3 | Required |
| `safety-report.json` | 1.4 | Required |
| `chain-evidence.json` | 1.5 | Required |
| `review.md` | 1.6 | Required |
| `review.yaml` | 1.7 | Required |
| `final-report.md` | 1.8 | Required |

Additional files required by this gate beyond SADP 0.R.2 minimum:

| Additional File | This Gate Section | When Required |
|-----------------|-------------------|---------------|
| `EVIDENCE_PACK_<ID>.zip` | 1.1 | Always |
| `git-status-before.txt` | 1.9 | Workspace state claims |
| `git-status-after.txt` | 1.9 | Workspace state claims |
| `deferred-files-register.yaml` | 1.10 | Untracked files remain |
| `secret-scan-output.txt` | 1.11 | deny_paths or mock fixtures |

---

## 7. Anti-Patterns

| Anti-Pattern | Description | Observed In |
|--------------|-------------|-------------|
| **Text-Only Submission** | Agent sends text description of work without artifact files | R3-R14 (12 rounds of text-only evidence) |
| **Post-Hoc Evidence Assembly** | Agent creates evidence files after the fact rather than during execution | R15 missing canonical files |
| **Stale Count Syndrome** | Summary reports contain old numbers while raw evidence has been updated | R18 safety-report.json count=20 vs scan count=26 |
| **Self-Referencing Integrity** | Hash files include themselves in their own hash computation | R16-BLOCKING-02 MANIFEST.json and hashes.sha256 |
| **Diff Scope Drift** | diff.patch includes files outside the declared write_set | R16-BLOCKING-04 out-of-scope files in diff |
| **Missing Chain Links** | Commit named in submission but no git-show evidence provided | R18 BLOCKING-02 commit 6022c187 |

---

> **Summary**: The pre-GPT-review gate enforces that every submission to the GPT reviewer contains a complete, internally consistent, file-based evidence pack. Text-only summaries are explicitly forbidden. Every R15-R18 evidence submission failure is documented as a concrete failure mode. A submission that passes this gate has all required files, valid formats, and internally consistent numbers.
