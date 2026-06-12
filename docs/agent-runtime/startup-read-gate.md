# Startup Read Gate -- RD2100 Agent Runtime

> Version: 1.0 | 2026-06-11
> Status: ACTIVE (P0 enforcement)
> Scope: All agents, all phases, all task types
> Derived from: R15-R18 reviewer findings, SADP 0.R, operations-manual.md
> Protection level: SADP protected (docs/agent-runtime/ path, governancePatterns)

---

## 0. Purpose

Every agent session begins with a cold start. Without a mandatory read sequence, agents drift into execution before understanding the current task, workspace state, active blockers, or write scope. This document defines the **mandatory startup read sequence** that every agent must complete before performing any work.

**Hard rule**: An agent that has not completed the startup read sequence MUST NOT modify any file, dispatch any task, or submit any evidence.

---

## 1. Mandatory Read Sequence

Every agent MUST read the following items in order before performing any work. Each item has a specific purpose and a concrete failure mode observed during R15-R18.

### 1.1 Current TaskSpec

| Field | Detail |
|-------|--------|
| **What to read** | The active TaskSpec file under `tasks/` or the dispatched TaskSpec in the agent's session context |
| **Required fields** | `task_id`, `write_set`, `gate_0` (with `inventory_evidence`), `conflict_registry`, `acceptance_gates`, known-dirty exclusions |
| **Why** | The TaskSpec is the contract between planner and executor. Without it, the agent does not know what it is authorized to change |
| **Verification** | Agent must be able to state its `task_id` and `write_set` before touching any file |

**Failure example (R17-R18)**: During R18 catch-up commits, the agent operated under `task_id: CONTEXT-COMPRESSION-A1` while performing workspace cleanup work spanning 6 commits and 3,634 files. The write_set expansion was so broad that GPT reviewer flagged it as `task_id mismatch` and required a `governance-decision-record.yaml` to document the deviation. The agent should have read (or created) a dedicated TaskSpec for the catch-up batch before beginning work, rather than reusing a stale task identity.

### 1.2 Operations Manual

| Field | Detail |
|-------|--------|
| **What to read** | `docs/agent-runtime/operations-manual.md` |
| **Required content** | Formal tool inventory, evidence pack linter, reusable scripts, current architecture |
| **Why** | Prevents redundant construction (core-008: Reuse-before-Build). The manual lists 20+ validated scripts that cover CDP automation, evidence packaging, and workspace management |
| **Verification** | Agent must check the operations manual tool inventory before creating any new script or utility |

**Failure example (R15)**: R15 evidence-integrity audit revealed that the agent had been producing text-only submissions from R3 through R14 -- 12 consecutive rounds without file-based evidence packs. The operations manual (created during R16-R17) now mandates evidence pack structure. Had the manual existed earlier and been read at startup, the R3-R14 evidence integrity gap (R15-INTEGRITY-01, severity P0_PROCESS) would have been prevented.

### 1.3 Latest Reviewer Verdict

| Field | Detail |
|-------|--------|
| **What to read** | The most recent GPT reviewer verdict from `_evidence/` or `_reports/` |
| **Required fields** | `verdict` (ACCEPTED / ACCEPTED_WITH_LIMITATION / BLOCKED / PARTIAL_ACCEPTANCE / HUMAN_REQUIRED), `blocking_findings`, `limitations`, `not_accepted`, `not_authorized` |
| **Why** | Reviewer verdicts carry forward blockers and limitations. An agent that ignores them will repeat rejected patterns |
| **Verification** | Agent must be able to state the current verdict and list all open blockers |

**Failure example (R16)**: R16 submission closed all 4 R15 blockers but introduced 4 new ones (R16-BLOCKING-01 through R16-BLOCKING-04). The R16 agent did not check whether R15-BLOCKING-02 (SADP 0.R.2 canonical files) was fully resolved -- it was only PARTIALLY_CLOSED (review.md was still missing). This cascading partial closure pattern occurred because the agent treated "closed" as binary rather than checking the specific closure status (CLOSED vs PARTIALLY_CLOSED vs CLOSED_WITH_LIMITATION).

### 1.4 Latest Final Report

| Field | Detail |
|-------|--------|
| **What to read** | The most recent `final-report.md` from the latest evidence directory |
| **Required fields** | Execution summary, commit chain, post-commit workspace state, blocker resolution status, internal consistency verification |
| **Why** | The final report is the executor's claim of what was done. Reading it prevents contradictory or overlapping work |
| **Verification** | Agent must be able to summarize the previous execution before starting new work |

**Failure example (R18 initial closure)**: R18-WORKSPACE-CLOSURE final-report claimed `Total entries in git status: 27` with a breakdown of `NEG-009: 17, Secret scan: 3, Session artifacts: 7`. But the subsequent R18 follow-up revealed the actual count was 26 untracked entries after proper reconciliation. The inconsistency between the initial report's claimed state and actual workspace state created BLOCKING-06 and BLOCKING-07 in the follow-up review.

### 1.5 Current `git status --porcelain`

| Field | Detail |
|-------|--------|
| **What to read** | Output of `git status --porcelain` at the moment the session begins |
| **Required content** | Full list of modified tracked files, untracked files, staged changes |
| **Why** | The workspace is the ground truth. Claims in reports and registers must match actual git state |
| **Verification** | Agent must capture and record git status as a baseline before any file modification |

**Failure example (R18 BLOCKING-07)**: GPT reviewer flagged `git status 与说明不一致` -- the git status output did not match the agent's written description. The R18 follow-up had to correct the count to 26 items and provide item-by-item registration. This blocker existed solely because the agent did not verify its workspace description against actual `git status --porcelain` output.

### 1.6 Deferred-Files Register

| Field | Detail |
|-------|--------|
| **What to read** | `deferred-files-register.yaml` from the latest evidence pack or workspace |
| **Required fields** | `total_untracked_entries`, categorized breakdown (NEG-009 fixtures, session artifacts, secret scan outputs, etc.), per-file path listing |
| **Why** | Untracked files that are not committed, not removed, and not registered are invisible liabilities. The register makes them visible |
| **Verification** | Agent must verify that every untracked file from `git status` is either committed, removed, or listed exactly once in the register |

**Failure example (R18 BLOCKING-06)**: The deferred-files-register.yaml was initially inconsistent with `git-status-after.txt`. The GPT reviewer required reconciliation: both files must show identical counts and paths. After correction, both showed 26 untracked entries with matching structure (`neg009_deferred: 17, gate0_deferred: 1, session_artifacts: 7, nul_device_file: 1`). The blocker was closed only after this alignment was verified.

### 1.7 Project Registry / Binding File

| Field | Detail |
|-------|--------|
| **What to read** | `.agent/PROJECT_REGISTRY.json` and relevant `.agent/CONVERSATION_BINDING.json` files |
| **When required** | When the task touches project routing, multi-project dispatch, or conversation binding |
| **Why** | The registry defines which projects exist, their routing targets, and their binding state. Modifying routing without reading the registry risks dispatching to wrong targets |
| **Verification** | Agent must confirm registry consistency if task scope includes routing changes |

**Failure example (R18 BLOCKING-03)**: `PROJECT_REGISTRY.json` was identified as an external modification not covered by the task's write_set. The R18 closure final-report had to explicitly document it: "PROJECT_REGISTRY.json explicitly documented as external modification." Had the agent read the registry at startup and included it in the write_set, this blocker would not have required a post-hoc explanation.

### 1.8 deny_paths / Protected Files Policy

| Field | Detail |
|-------|--------|
| **What to read** | Protected files list from `rules/core.md`, governance hooks (`hooks/pre-edit.governance.ps1`), and SADP deny_paths definitions |
| **Required content** | Files that cannot be committed, files that require TaskSpec for modification, files under governance protection (AGENTS.md, CLAUDE.md, rules/*, SADP, schemas, lessons) |
| **Why** | Modifying a protected file without authorization is a P0 violation. The agent must know what is off-limits before it begins editing |
| **Verification** | Agent must list protected files it will NOT touch, and confirm TaskSpec authorization for any it will touch |

**Failure example (R17 limitation)**: R17 ACCEPTED_WITH_LIMITATION verdict explicitly stated: "sadp-audit.ps1 governance pattern change -- NOT ACCEPTED" and "any self-protecting file mutation -- NOT ACCEPTED." The reviewer drew a hard boundary around governance files. The subsequent R18 task required a `governance-decision-record.yaml` to document that protected files were touched, and the limitation was carried forward: "treating reconstructed hook logs as the normal evidence standard" was NOT AUTHORIZED.

### 1.9 Conversation Health State

| Field | Detail |
|-------|--------|
| **What to read** | `.ai/conversation/current.json` and `_evidence/conversation-health/latest.json` (when present), plus conversation-health policy summary from `configs/conversation-health-policy.yaml` |
| **Required fields** | Current decision (`OK` / `SUGGEST_HANDOFF` / `FORCE_HANDOFF` / `HUMAN_REQUIRED` / `UNKNOWN`), metrics freshness, `last_nav_result`, whether handoff or migration is required |
| **Why** | The agent must know whether the current conversation is stale, degraded, or requires handoff before beginning work. Without this awareness, the agent may invest significant effort into a conversation that should be migrated. Startup Read Gate is an awareness/read gate — enforcement remains in A1 Pre-Task, A2 Pre-GPT, and Evidence Pack rules |
| **Verification** | Agent must report the current conversation-health decision and freshness. `UNKNOWN` must not be silently treated as `OK` — it must be explicitly flagged as `WARNING` |

**Failure example (A3 R2 limitation)**: A3 R2 evidence pack had no runtime artifact showing conversation-health with `exit_code!=0`. The GPT reviewer noted: "nonzero conversation-health advisory behavior is covered by tests and schema simulation, not by a real hook-output runtime artifact." Had the startup-read check been in place during A3, the agent would have had an additional evidence trail of conversation-health state transitions throughout the session.

---

## 2. Hard Stop Conditions

An agent CANNOT proceed to any execution phase if any of the following are true:

| Condition | Blocked State | Resolution |
|-----------|--------------|------------|
| Agent cannot state its current `task_id` | NO_TASK | Read or create TaskSpec |
| Agent cannot state its current `write_set` | NO_SCOPE | Read TaskSpec `conflict_registry.write_set` |
| Agent cannot list current open blockers | BLIND_TO_BLOCKERS | Read latest reviewer verdict |
| Agent cannot describe current workspace state | BLIND_TO_WORKSPACE | Run `git status --porcelain` and capture output |
| Agent has not read the operations manual | REUSE_BLIND | Read operations-manual.md tool inventory |
| Agent has not checked deferred-files register | UNTRACKED_BLIND | Read deferred-files-register.yaml |

**No exception path exists.** An agent that proceeds without completing the startup read sequence is in violation of this gate, and its output is subject to BLOCKED verdict at review.

---

## 3. Startup Read Checklist (Machine-Verifiable)

```yaml
startup_read_gate:
  task_spec_read: true | false
  task_id_known: "<task_id>" | null
  write_set_known: [<file_list>] | null
  operations_manual_read: true | false
  latest_verdict_read: true | false
  latest_verdict_status: "<verdict>" | null
  open_blockers_known: [<blocker_ids>] | []
  latest_final_report_read: true | false
  git_status_captured: true | false
  git_status_baseline: "<porcelain_output_or_path>" | null
  deferred_register_read: true | false
  deferred_register_total: <count> | null
  registry_read: true | false | n/a
  deny_paths_known: true | false
  startup_read_health_checked: true | false
  startup_read_health_decision: "OK" | "SUGGEST_HANDOFF" | "FORCE_HANDOFF" | "HUMAN_REQUIRED" | "UNKNOWN" | null
  startup_read_health_severity: "INFO" | "WARNING" | "BLOCKING" | null
  startup_read_health_freshness: "fresh" | "stale" | "unknown" | null
  startup_read_health_evidence_file: "_evidence/conversation-health/startup-read-latest.json" | null
```

All fields marked `true` (or with non-null values where applicable) are required before execution may begin.

---

## 4. Derived Rules

| Rule ID | Source | Enforcement |
|---------|--------|-------------|
| core-008 | Reuse-before-Build | Operations manual read at startup |
| SADP 0.1 | Gate 0 mandatory | TaskSpec read + inventory_evidence check |
| SADP 0.2 | Conflict Registry | write_set known before any file modification |
| SADP 0.R | Mandatory Reviewer Node | Reviewer verdict read + blockers acknowledged |
| INV-003 | Write Scope Containment | write_set compared against actual git diff at startup |

---

## 5. Anti-Patterns

| Anti-Pattern | Description | Observed In |
|--------------|-------------|-------------|
| **Cold Start Edit** | Agent begins editing files immediately without reading any context | R17 initial behavior before correction |
| **Stale Task Identity** | Agent operates under a task_id that does not match actual work scope | R18 CONTEXT-COMPRESSION-A1 mismatch |
| **Blocker Amnesia** | Agent ignores previous reviewer blockers and repeats rejected patterns | R16 partial closure of R15-BLOCKING-02 |
| **Workspace Assumption** | Agent describes workspace state from memory rather than running git status | R18 BLOCKING-07 count mismatch |
| **Register Ignorance** | Agent does not check deferred-files register and creates duplicate untracked files | R18 BLOCKING-06 register/status inconsistency |
| **Health Blindness** | Agent begins work without checking conversation-health state, missing stale/degraded signals | A3 R2 limitation — no startup evidence trail |

---

> **Summary**: The startup read gate is a P0 enforcement point. No agent may produce code, evidence, or submissions without first completing the full read sequence. Every R15-R18 failure mode traced back to an incomplete startup read has been documented as a concrete failure example in this standard.
