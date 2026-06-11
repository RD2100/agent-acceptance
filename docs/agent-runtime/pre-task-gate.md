# Pre-Task Gate -- RD2100 Agent Runtime

> Version: 1.0 | 2026-06-11
> Status: ACTIVE (P0 enforcement)
> Scope: All agents, all task types, before any code or documentation modification
> Derived from: R15-R18 reviewer findings, SADP 0.R.2, runtime-invariants.md
> Protection level: SADP protected (docs/agent-runtime/ path, governancePatterns)

---

## 0. Purpose

The pre-task gate enforces that every agent verifies its authorization boundaries **before** modifying any file. This is the second enforcement point in the agent lifecycle, following the Startup Read Gate. An agent that passes the startup read but fails the pre-task gate will produce work that is rejected at review for scope violations, missing evidence, or unauthorized protected-file mutations.

**Hard rule**: No file may be created, modified, or deleted until all pre-task checks pass.

---

## 1. Pre-Task Check Sequence

### 1.1 task_id Matches Actual Work Scope

| Field | Detail |
|-------|--------|
| **Check** | The `task_id` in the active TaskSpec must describe the work the agent is about to perform |
| **Pass condition** | `task_id` objective aligns with the actual modification scope; no identity mismatch |
| **Fail condition** | Agent is performing work outside the `task_id` description, or is using a stale/recycled `task_id` |
| **Resolution on fail** | Create a new TaskSpec with an accurate `task_id`, or obtain human approval for scope extension |

**Failure example (R18 task_id mismatch)**: The R18 catch-up commit batch operated under `task_id: CONTEXT-COMPRESSION-A1` while performing workspace cleanup spanning 6 commits and 3,634 files across the entire repository. GPT reviewer flagged this as a limitation that must be carried forward: "current-task.yaml 的 task_id 仍为 CONTEXT-COMPRESSION-A1，而不是专门的 CATCH-UP-COMMIT-BATCH-R18 TaskSpec." The reviewer accepted it only because a `governance-decision-record.yaml` was created to document the mismatch, and explicitly stated this could not serve as a precedent for future work.

### 1.2 write_set Is Narrow and Task-Specific

| Field | Detail |
|-------|--------|
| **Check** | The `write_set` in `conflict_registry` must list specific file paths, not broad patterns or wildcards |
| **Pass condition** | Every path in `write_set` corresponds to a file the task will actually modify; no `**/*.md`, no `scripts/*`, no `docs/**` |
| **Fail condition** | `write_set` contains wildcards, directory globs, or "all files under X" patterns |
| **Resolution on fail** | Narrow the `write_set` to explicit file paths; if scope is genuinely broad, document the justification in a governance decision record |

**Failure example (R18 broad write_set)**: R18 workspace cleanup expanded the write_set to cover the entire repository. GPT reviewer accepted this only under an explicit one-time authorization: "write_set expansion 范围非常宽，只能在本次 catch-up batch 的 human/governance decision record 下接受，不能作为未来常规开发的默认授权边界." The reviewer's `not_authorized` list explicitly included: "future reuse of broad write_set patterns without new TaskSpec / decision record."

**Failure example (R16 diff.patch out of scope)**: R16-BLOCKING-04 found that the canonical `diff.patch` contained out-of-scope files -- files outside the declared `write_set`. This meant the agent modified files it did not declare, or the `write_set` was too narrow for the actual work. Either way, the inconsistency was a blocking finding.

### 1.3 Protected Files Identified BEFORE Editing

| Field | Detail |
|-------|--------|
| **Check** | Before any file modification, the agent must identify whether any target file is in the protected-files set |
| **Protected files** | `AGENTS.md`, `CLAUDE.md`, `rules/core.md`, `sub-agent-dispatch-protocol.md`, `capability-inventory.md`, `lessons-learned.md`, all files under `hooks/`, all files under `.ai/`, all JSON schemas under `schemas/` |
| **Pass condition** | No protected file in `write_set`, OR protected file explicitly authorized in TaskSpec with `protected_files_touched: true` |
| **Fail condition** | Agent modifies a protected file without declaring it in the TaskSpec |
| **Resolution on fail** | Stop immediately. Create amended TaskSpec with `protected_files_touched: true` and `conflict_level: high`. If the protected file is a governance file, obtain human approval |

**Failure example (R17 not-accepted boundary)**: R17 verdict ACCEPTED_WITH_LIMITATION included an explicit `not_accepted` list: "sadp-audit.ps1 governance pattern change" and "any self-protecting file mutation." The reviewer recognized that modifying `sadp-audit.ps1` -- a governance enforcement script -- constitutes a self-protecting mutation that requires separate authorization. The agent had not identified this file as protected before editing it.

**Failure example (R18 governance decision required)**: R18 follow-up had to create `governance-decision-record.yaml` specifically to document that protected files were touched during the catch-up batch. This record explicitly listed: "protected files, write_set expansion, task_id mismatch." If protected files had been identified at pre-task time, the decision record would have been created proactively rather than reactively.

### 1.4 human_required Decision Record Exists When Needed

| Field | Detail |
|-------|--------|
| **Check** | If any of the following conditions apply, a `human_required` decision record must exist before the agent proceeds |
| **Trigger conditions** | Live dispatch; protected governance file mutation; self-protecting hook modification; broad write_set expansion; project registry migration; deny_path exception; sealed-files-manifest policy change; committing mock secret fixtures; changing finalizer blocking rules |
| **Pass condition** | Decision record exists with explicit human approval for the specific action |
| **Fail condition** | Action proceeds without a decision record, or decision record exists but lacks human approval signature |
| **Resolution on fail** | Stop. Create decision record. Wait for human approval. Do not proceed |

**Failure example (R18 NEW-BLOCKING-08)**: GPT reviewer issued `R18-NEW-BLOCKING-08: 缺少 human/governance decision record` because the agent performed protected-file mutations, write_set expansion, and task_id override without any human decision record. The blocker was only closed after `governance-decision-record.yaml` was added to the evidence pack. This was a retroactive fix for a check that should have been performed pre-task.

**Failure example (R17 HUMAN_REQUIRED)**: R17 verdict designated the next task as `OPERATIONS-MANUAL-AUDIT-PATTERN-BIND-A1` with status `HUMAN_REQUIRED`. This meant no agent could proceed with that task until a human explicitly approved it. Any agent starting that task without verifying the HUMAN_REQUIRED status would be in direct violation.

### 1.5 Expected Evidence Directory Declared

| Field | Detail |
|-------|--------|
| **Check** | The agent must declare where evidence will be stored before any work begins |
| **Required path** | `_evidence/<TASK-ID>/` following the SADP 0.R.2 evidence directory convention |
| **Pass condition** | Evidence directory path is declared in the TaskSpec or execution plan |
| **Fail condition** | No evidence directory declared, or evidence scattered across workspace without structure |
| **Resolution on fail** | Declare `_evidence/<TASK-ID>/` directory. Create it. All evidence artifacts go there |

**Failure example (R15 evidence structure)**: R15-BLOCKING-02 found that SADP 0.R.2 canonical files were missing from the evidence pack. The evidence pack (EVIDENCE_PACK_R15.zip, 77 files, 221KB) was structurally rich but lacked the required canonical files (diff.patch, test-output.txt, safety-report.json, chain-evidence.json, review.md, review.yaml, final-report.md). This omission indicates the evidence directory was not pre-planned with the required structure -- files were assembled ad-hoc rather than following a declared evidence layout.

### 1.6 live_dispatch Remains NOT_AUTHORIZED Unless Explicitly Approved

| Field | Detail |
|-------|--------|
| **Check** | `live_dispatch` authorization status must be verified. Default is `NOT_AUTHORIZED` |
| **Pass condition** | `live_dispatch: AUTHORIZED` exists in the latest reviewer verdict with explicit human approval, OR the task does not involve live dispatch |
| **Fail condition** | Agent performs live dispatch without explicit AUTHORIZED status, or assumes authorization from a different task's verdict |
| **Resolution on fail** | Stop immediately. Live dispatch without authorization is a P0 violation |

**Failure example (R17-R18 persistent NOT_AUTHORIZED)**: Every reviewer verdict from R2 through R18 maintained `live_dispatch: NOT_AUTHORIZED`. The R17 verdict explicitly listed "live dispatch" under `not_accepted`. The R18 final verdict repeated it: `not_authorized: [live dispatch]`. This persistent status means any agent performing live dispatch during this entire period would be in direct violation of the reviewer's explicit boundary. No task in R2-R18 had live dispatch authorization.

---

## 2. Pre-Task Gate Checklist (Machine-Verifiable)

```yaml
pre_task_gate:
  task_id_matches_scope: true | false
  task_id: "<current_task_id>"
  task_id_objective: "<1-sentence description>"
  
  write_set_narrow: true | false
  write_set_paths: [<explicit_file_paths>]
  write_set_wildcards: [] | [<forbidden_patterns>]
  
  protected_files_identified: true | false
  protected_files_in_scope: [] | [<protected_file_paths>]
  protected_files_authorized: true | false | n/a
  
  human_required_check:
    triggers_present: [] | [<trigger_conditions>]
    decision_record_exists: true | false | n/a
    decision_record_path: "<path>" | null
    human_approved: true | false | n/a
  
  evidence_directory_declared: true | false
  evidence_directory_path: "_evidence/<TASK-ID>/"
  
  live_dispatch_status: NOT_AUTHORIZED | AUTHORIZED
  live_dispatch_verdict_source: "<verdict_file_or_round>"
```

All fields must evaluate to a passing state before any file modification may occur.

---

## 3. Gate Decision Matrix

| Check | Pass | Fail | Severity |
|-------|------|------|----------|
| task_id matches scope | Continue | BLOCKED | P0 |
| write_set narrow | Continue | BLOCKED | P0 |
| Protected files identified | Continue | BLOCKED | P0 |
| human_required record exists | Continue | BLOCKED | P0 |
| Evidence directory declared | Continue | WARNING | P2 |
| live_dispatch authorized | Continue (if not dispatching) | BLOCKED | P0 |

---

## 4. Scope Creep Prevention

Scope creep is the most common pre-task gate violation. The agent begins with a narrow task and gradually expands its scope through "while I'm here" modifications.

### 4.1 Scope Creep Indicators

| Indicator | Detection Method |
|-----------|-----------------|
| `git diff --name-only` exceeds `write_set` | Compare actual modified files against declared write_set |
| New files created outside `write_set` | Check `git status --porcelain` for new untracked files not in expected output |
| Protected files modified without authorization | Check `git diff --name-only` against protected files list |
| Cumulative `write_set` across tasks >= 3 | SADP cumulative trigger window (anti task-splitting) |

### 4.2 Historical Scope Creep Pattern

```
R18 Workspace Cleanup Scope Expansion:

  Declared task: CONTEXT-COMPRESSION-A1 (context compression optimization)
  Actual work:   Full workspace cleanup, 6 commits, 3,634 files
  
  Scope expansion chain:
    Commit 1 (511c54ab):  100 files  -- initial cleanup
    Commit 2 (283b5834):  751 files  -- expanded to scripts/
    Commit 3 (dae0e9fb):  1061 files -- expanded to full docs/
    Commit 4 (a9ad148d):  81 files   -- test evidence
    Commit 5 (3fc33dac):  1610 files -- expanded to full repository
    Commit 6 (4efcbac9):  31 files   -- mixed-scope cleanup
  
  Total: 3,634 files across 6 commits
  Authorization: governance-decision-record.yaml (retroactive)
  Reviewer verdict: ACCEPTED_WITH_LIMITATION
  Limitation: "broad write_set expansion valid only for this R18 catch-up batch"
```

This pattern is accepted as historical catch-up but MUST NOT be repeated. The pre-task gate would have prevented this by flagging the task_id/scope mismatch before Commit 1.

---

## 5. Integration with SADP

| SADP Section | Pre-Task Gate Mapping |
|--------------|---------------------|
| SADP 0.1 (Gate 0) | Pre-task gate verifies `gate_0.inventory_evidence` exists in TaskSpec |
| SADP 0.2 (Conflict Registry) | Pre-task gate verifies `write_set` is narrow and `conflict_level` is accurate |
| SADP 0.R (Reviewer Node) | Pre-task gate verifies latest reviewer verdict has no unresolved blockers |
| SADP 0.R.2 (Evidence Pack) | Pre-task gate verifies evidence directory is declared |
| SADP 3.3a (Plan Auditor) | Pre-task gate is the executor-side complement to the plan-side auditor |

---

## 6. Anti-Patterns

| Anti-Pattern | Description | Observed In |
|--------------|-------------|-------------|
| **Scope Drift** | Agent gradually expands work beyond write_set through "helpful" additions | R18 six-commit expansion from 100 to 3,634 files |
| **Task Identity Recycling** | Agent reuses old task_id for new unrelated work | R18 CONTEXT-COMPRESSION-A1 used for workspace cleanup |
| **Protected File Surprise** | Agent discovers a file is protected after already modifying it | R17 sadp-audit.ps1 modification without authorization |
| **Decision Record Avoidance** | Agent proceeds without creating human_required record to avoid waiting | R18 NEW-BLOCKING-08: decision record missing |
| **Evidence Afterthought** | Agent creates evidence directory after work is done, losing early-stage evidence | R15 missing canonical files in evidence pack |

---

> **Summary**: The pre-task gate is a P0 enforcement point that prevents scope creep, unauthorized protected-file mutation, and missing evidence planning. Every R15-R18 scope violation traced to inadequate pre-task verification is documented as a concrete failure mode. An agent that passes this gate has explicit authorization for every file it will touch.
