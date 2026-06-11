# Universal Agent Workflow Standard

> **task_id**: UNIVERSAL-AGENT-WORKFLOW-STANDARD-A1
> **version**: 1.0
> **date**: 2026-06-11
> **canonical_root**: `D:\agent-acceptance`
> **status**: active
> **scope**: All AI agent sessions (executor, reviewer, finalizer, plan agent)
> **derived_from**: R15-R18 GPT review cycle failure analysis, SADP v1.0, operations-manual.md, runtime-invariants.md
> **reviewer_conversation**: 6a297f76-3e7c-83a5-a0e5-b4413d923c7e
> **supersedes**: ad-hoc per-session workflow conventions

---

This standard abstracts the lessons learned across the R15 through R18 GPT reviewer cycle into eight mandatory sections. Every AI agent session operating within this governance boundary MUST comply with all eight sections. Non-compliance at any gate produces a BLOCKED or NEEDS_EVIDENCE state; repeated non-compliance escalates to HUMAN_REQUIRED.

The failure modes cited in each section are drawn from actual R15-R18 evidence:

- **R15**: Evidence pack submitted with non-repo-relative ZIP paths (`source/` instead of `scripts/`), missing SADP 0.R.2 canonical files, impure JSON (summary appended to DRY_RUN output), and an unproven manual-only split from R14. Verdict: `PARTIAL_ACCEPTANCE_WITH_BLOCKERS`.
- **R16**: Closed R15 path and JSON-purity blockers but introduced new ones: `review.md` missing from evidence pack, SHA256 self-reference failures for `MANIFEST.json` and `hashes.sha256`, ZIP not independently reproducible (205 passed, 47 failed), and `diff.patch` containing out-of-scope files. Verdict: `PARTIAL_ACCEPTANCE_WITH_REMAINING_EVIDENCE_BLOCKERS`.
- **R17**: Closed all R16 blockers. Accepted with documented limitations: test results produced from full repo context rather than ZIP-independent replay, and governance pattern change deferred to a separate task. Verdict: `ACCEPTED_WITH_LIMITATION`.
- **R18**: Workspace closure cycle exposed register mismatches (27 untracked files not fully accounted for), a commit (`6022c187`) lacking per-commit diff/show evidence, and `PROJECT_REGISTRY.json` modified externally without explicit register documentation. Verdict escalated through 3 sub-rounds (CLEANUP, CLOSURE, EVIDENCE-MAINTENANCE) before achieving closure.

---

## 1. Startup Read Gate

Every agent session MUST complete the Startup Read Gate before performing any work. The gate ensures the agent has full situational awareness of the current task, workspace state, and governance context. An agent that begins modifying files without completing this gate is in violation.

### 1.1 Mandatory Read List

The agent MUST read ALL of the following before any write operation:

| # | Item | Source | Purpose |
|---|------|--------|---------|
| 1 | Current TaskSpec | `tasks/task-{id}.md` or dispatch payload | Defines task_id, write_set, acceptance_gates, forbidden paths |
| 2 | Operations manual | `docs/agent-runtime/operations-manual.md` | Existing tools, SOPs, reuse checklist (core-008) |
| 3 | Latest reviewer verdict | `_evidence/*/review.md` or `REVIEWER_INDEX.md` | Current blockers, accepted components, next authorized task |
| 4 | Latest final-report | `_evidence/*/final-report.md` | Closure state, limitations carried forward, deferred items |
| 5 | Current git status | `git status --short` output | Modified tracked, untracked files, branch state |
| 6 | Deferred-files register | `deferred-files-register.yaml` in evidence pack | Files permanently or temporarily excluded from commits |
| 7 | Project registry | `.agent/PROJECT_REGISTRY.json` | Active projects, binding states, dispatch eligibility |
| 8 | deny_paths policy | `SADP_POLICY.json` deny_paths / deny_list sections | Paths the agent must never write or must treat as read-only |

### 1.2 Gate Conditions

The agent CANNOT proceed to any file modification until ALL of the following are true:

```yaml
startup_read_gate:
  conditions:
    - task_id_known: true          # Agent knows which task it is executing
    - write_set_known: true        # Agent knows the approved file modification scope
    - blockers_known: true         # Agent has read all open blockers from reviewer
    - workspace_state_known: true  # Agent has captured git status --short
    - deny_paths_known: true       # Agent knows which paths are forbidden
  gate_status: PASS | FAIL
  fail_action: HALT — do not modify any file until all conditions met
```

### 1.3 R15-R18 Failure Mode: Uninformed Agent Start

In the R15 cycle, the agent submitted an evidence pack with `source/` paths instead of `scripts/` paths. Root cause: the agent did not read the operations manual (which documents the canonical `scripts/` directory structure) before assembling the pack. In R18-CLEANUP, the agent initially failed to account for 23 untracked files because it started committing without reading the deferred-files register from the prior round.

**Rule**: If the agent discovers mid-task that it missed a required read, it MUST halt, record the gap, re-read, and re-evaluate whether work done so far remains valid.

---

## 2. Pre-Task Gate

Before any code or documentation file is modified, the agent MUST pass the Pre-Task Gate. This gate validates that the proposed work is authorized, scoped, and documented.

### 2.1 Gate Checklist

```yaml
pre_task_gate:
  checks:
    - id: PT-01
      name: task_id_matches
      description: The task_id in the current TaskSpec matches the work being performed.
      pass_condition: task_id in evidence files equals task_id in dispatch payload.
      fail_action: HALT — wrong task context.

    - id: PT-02
      name: write_set_is_narrow
      description: The write_set contains only files necessary for the stated goal.
      pass_condition: Every file in write_set has a stated purpose in the TaskSpec goal or acceptance gates.
      fail_action: NARROW — remove unnecessary files from write_set before proceeding.

    - id: PT-03
      name: protected_files_identified
      description: Any protected file in the write_set is explicitly flagged.
      pass_condition: protected_files_touched field is accurate; protected files listed individually.
      fail_action: HALT — protected file modification requires Human Required Decision Record.

    - id: PT-04
      name: human_required_record_exists
      description: When the write_set includes protected files or governance patterns, a Human Required Decision Record exists.
      pass_condition: Record present with decision, rationale, approver_id, timestamp.
      fail_action: BLOCK — cannot modify protected files without human authorization.

    - id: PT-05
      name: evidence_directory_declared
      description: The evidence directory path is declared before work begins.
      pass_condition: _evidence/{ROUND_ID}/ directory exists or is created with documented naming convention.
      fail_action: CREATE — establish evidence directory before any file modification.

    - id: PT-06
      name: live_dispatch_unauthorized
      description: Live dispatch (sending messages to external services, invoking CDP, triggering Chrome) is not performed unless explicitly approved.
      pass_condition: No live dispatch capability used without a Human Required Decision Record authorizing it.
      fail_action: BLOCK — live dispatch without authorization is a P0 violation.
```

### 2.2 R15-R18 Failure Mode: Ungoverned Write Scope

In R16, the agent included out-of-scope files in `diff.patch` (R16-BLOCKING-04). The write_set was not narrow: files unrelated to the operations-manual task appeared in the canonical diff. In R18-CLEANUP, `hooks/sealed-files-manifest.json` was auto-regenerated by the SADP hook during a commit, introducing an unplanned governance file modification that the agent did not anticipate or register.

**Rule**: If a hook, pre-commit script, or automated process modifies a file outside the declared write_set, the agent MUST halt, register the unexpected modification, and re-evaluate the Pre-Task Gate before continuing.

---

## 3. Pre-GPT-Review Gate

Before submitting any evidence pack to the GPT reviewer, the agent MUST pass the Pre-GPT-Review Gate. This gate validates that the evidence pack is complete, machine-parseable, and independently verifiable. Text-only summaries are explicitly forbidden as the sole basis for a reviewer verdict.

### 3.1 Mandatory Evidence Pack Contents

Every submission to the GPT reviewer MUST include all of the following files:

| # | File | Format | Required | Purpose |
|---|------|--------|----------|---------|
| 1 | `diff.patch` | Unified diff | Yes | Shows exact file changes in scope |
| 2 | `test-output.md` | Markdown with command + exit code | Yes | Test execution evidence |
| 3 | `safety-report.json` | Valid JSON | Yes | Workspace state: modified_tracked, untracked, deny_paths, deny_list counts |
| 4 | `chain-evidence.json` | Valid JSON | Yes | Causal chain: task -> changes -> tests -> verdict |
| 5 | `review.md` | Markdown | Yes | Executor's self-review (not a substitute for reviewer verdict) |
| 6 | `review.yaml` | Valid YAML | Yes | Machine-readable reviewer evidence per SADP 0.R.2 |
| 7 | `final-report.md` | Markdown | Yes | Deterministic artifact summary per SADP 0.R.3 |
| 8 | `git-status-before.txt` | Plain text | Yes | `git status --short` captured before first modification |
| 9 | `git-status-after.txt` | Plain text | Yes | `git status --short` captured after last commit |
| 10 | `deferred-files-register.yaml` | Valid YAML | Yes | All files excluded from commits with categorization and rationale |

### 3.2 Forbidden Submission Patterns

The following patterns are explicitly forbidden:

```yaml
forbidden_patterns:
  - id: FP-01
    name: text_only_summary
    description: Submitting a text-only summary without file-based evidence.
    rationale: Text summaries cannot be independently verified. R3-R14 operated under this pattern; R15-INTEGRITY-01 retroactively flagged all prior rounds as not independently verifiable.
    
  - id: FP-02
    name: self_attested_boolean
    description: Using boolean fields (e.g., "tests_passed: true") without supporting command output.
    rationale: Boolean self-attestation is invalid per SADP 0.1 Gate 0 Ledger rules.
    
  - id: FP-03
    name: impure_json
    description: JSON files with appended prose summaries or non-JSON content.
    rationale: R15-BLOCKING-03 — DRY_RUN JSON had summary text appended, breaking JSON.parse().
    
  - id: FP-04
    name: unparseable_yaml
    description: YAML files that fail YAML.parse() validation.
    rationale: Machine-readable evidence must be parseable to enable automated audit.
```

### 3.3 R15-R18 Failure Mode: Incomplete Evidence Pack

R15 submitted 77 files but was missing all SADP 0.R.2 canonical files (review.md, review.yaml, final-report.md, chain-evidence.json). R16 fixed the path structure but forgot review.md entirely (R16-BLOCKING-01). It took three rounds (R15, R16, R17) to achieve a complete evidence pack.

**Rule**: Run `python scripts/pre_gpt_review_gate.py` (or equivalent evidence pack linter) before every submission. If any canonical file is missing or unparseable, the submission is BLOCKED.

---

## 4. Evidence Pack Standard

This section defines the minimum validation rules for evidence pack integrity. Every file in the pack must satisfy its format contract. Every git operation must have corresponding evidence. Every workspace file must be accounted for exactly once.

### 4.1 Format Validation Rules

```yaml
format_validation:
  json_files:
    rule: Must pass JSON.parse() with no trailing content.
    files: [safety-report.json, chain-evidence.json]
    fail_action: NEEDS_EVIDENCE — fix and resubmit.
    
  yaml_files:
    rule: Must pass YAML.parse() with no duplicate keys.
    files: [review.yaml, deferred-files-register.yaml]
    fail_action: NEEDS_EVIDENCE — fix and resubmit.
    
  patch_files:
    rule: Must be valid unified diff format. Must contain only in-scope files.
    files: [diff.patch, diff-*.patch]
    fail_action: NEEDS_EVIDENCE — regenerate with correct scope.
    
  text_files:
    rule: Must be non-empty, UTF-8 encoded.
    files: [git-status-before.txt, git-status-after.txt, git-show-*.txt, test-output.md]
    fail_action: NEEDS_EVIDENCE — regenerate.
```

### 4.2 Git Evidence Rules

```yaml
git_evidence_rules:
  - id: GE-01
    name: every_commit_has_git_show
    rule: Every commit hash referenced in the evidence pack MUST have a corresponding git-show-{hash}.txt file.
    failure_mode: R18-BLOCKING-02 — commit 6022c187 had no diff or git-show evidence.
    
  - id: GE-02
    name: every_final_commit_in_git_log
    rule: The final commit hash MUST appear in a git-log capture included in the pack.
    rationale: Proves the commit chain is complete and no commits are missing from the evidence.
    
  - id: GE-03
    name: every_untracked_accounted_once
    rule: Every untracked file in git-status-after MUST appear in exactly one category of the deferred-files-register: committed, removed, or registered_deferred.
    failure_mode: R18-BLOCKING-01 — 27 untracked files existed but the register did not account for all of them.
    
  - id: GE-04
    name: modified_tracked_zero_for_closure
    rule: When claiming workspace closure, modified_tracked count MUST be 0.
    rationale: Non-zero modified tracked files means uncommitted work exists. Closure claims are invalid.
    
  - id: GE-05
    name: clean_workspace_requires_no_deferred
    rule: An agent CANNOT claim "clean workspace" status while deferred files exist. Must claim "registered_closure" instead.
    failure_mode: R18 initially claimed "clean" with 27 untracked files. Corrected to "registered_closure."
    
  - id: GE-06
    name: replay_evidence_labeled
    rule: Evidence generated from replay (re-running tests after the fact, regenerating diffs from cached state) MUST be labeled as replay with original timestamp and replay timestamp both recorded.
    rationale: Replay evidence has different trust properties than live evidence. Reviewer must know which is which.
```

### 4.3 Hash Integrity Rules

```yaml
hash_integrity:
  - id: HI-01
    name: no_self_referential_hashes
    rule: A file MUST NOT contain its own hash. MANIFEST.json and hashes.sha256 MUST be excluded from the hash list they define.
    failure_mode: R16-BLOCKING-02 — SHA256 self-reference fails for MANIFEST.json and hashes.sha256. These files were included in their own hash computation, creating a logical impossibility.
    solution: Exclude metadata files from their own hash lists. Document the exclusion.
    
  - id: HI-02
    name: hashes_match_content
    rule: Every hash recorded in hashes.sha256 MUST match the actual file content when verified with sha256sum.
    fail_action: NEEDS_EVIDENCE — regenerate hashes from final file state.
```

### 4.4 R15-R18 Failure Mode: Evidence Integrity Cascade

The R15-INTEGRITY-01 finding was retroactive: it affected rounds R3 through R14, all of which had submitted text-only evidence that was not independently verifiable. This created an evidence integrity cascade where prior verdicts had to be maintained with an explicit limitation tag (`MAINTAINED_WITH_EVIDENCE_INTEGRITY_LIMITATION`). The corrective action (file-based evidence packs starting from R15) was only fully validated at R17 when the reviewer confirmed `CORRECTIVE_EVIDENCE_ACCEPTED_R17`.

**Rule**: Any evidence integrity gap discovered retroactively MUST be recorded as a `retroactive_erratum` with affected rounds, severity, status, and impact assessment. The erratum remains open until the reviewer explicitly accepts the corrective evidence.

---

## 5. State Machine

Every task, finding, and workspace item operates within a defined state machine. State transitions MUST follow the rules below. Invalid transitions are governance violations.

### 5.1 State Definitions

```yaml
states:
  - id: DRAFT
    description: Task or finding created but not yet validated. No work performed.
    
  - id: READY_FOR_EXECUTION
    description: Pre-Task Gate passed. Write_set approved. Agent authorized to begin work.
    
  - id: EXECUTED
    description: Work completed. Evidence collected. Not yet reviewed.
    
  - id: NEEDS_EVIDENCE
    description: Reviewer found missing or invalid evidence. Agent must supply before verdict.
    
  - id: NEEDS_MORE_EVIDENCE
    description: Evidence exists but is insufficient for a confident verdict. Specific gaps documented.
    
  - id: ACCEPTED
    description: Reviewer verdict: all gates pass, no limitations. Task complete.
    
  - id: ACCEPTED_WITH_LIMITATION
    description: Reviewer verdict: gates pass with documented limitations that do not block closure.
    
  - id: BLOCKED
    description: A P0/P1 finding prevents progress. Requires new evidence or human intervention.
    
  - id: HUMAN_REQUIRED
    description: Agent cannot proceed without human authorization. A Human Required Decision Record is mandatory.
    
  - id: DEFERRED
    description: File or task intentionally postponed. Remains visible in deferred-files register.
```

### 5.2 Transition Rules

```yaml
transitions:
  - from: DRAFT
    to: READY_FOR_EXECUTION
    requires: Pre-Task Gate PASS (all PT-01 through PT-06)
    
  - from: READY_FOR_EXECUTION
    to: EXECUTED
    requires: Work completed, evidence pack assembled, Pre-GPT-Review Gate PASS
    
  - from: EXECUTED
    to: ACCEPTED
    requires: Reviewer verdict = pass, all findings resolved, no limitations
    
  - from: EXECUTED
    to: ACCEPTED_WITH_LIMITATION
    requires: Reviewer verdict = pass with documented limitations
    preserves: Limitations MUST be carried forward in final-report.md and REVIEWER_INDEX.md.
    
  - from: EXECUTED
    to: NEEDS_EVIDENCE
    requires: Reviewer identifies missing or invalid evidence files
    
  - from: NEEDS_EVIDENCE
    to: EXECUTED
    requires: Agent supplies requested evidence, re-passes Pre-GPT-Review Gate
    
  - from: BLOCKED
    to: ACCEPTED
    requires: NEW evidence that resolves the blocking finding. Cannot reuse prior evidence.
    rationale: R15-R17 cycle — each round required genuinely new evidence to close prior blockers.
    
  - from: BLOCKED
    to: NEEDS_EVIDENCE
    requires: Partial resolution identifies additional evidence gaps
    
  - from: HUMAN_REQUIRED
    to: READY_FOR_EXECUTION
    requires: Human Required Decision Record with approved decision, approver_id, timestamp
    constraint: HUMAN_REQUIRED CANNOT be bypassed by expanding the write_set. The decision record must exist regardless of scope changes.
    
  - from: DEFERRED
    to: READY_FOR_EXECUTION
    requires: New TaskSpec that includes the deferred item in its write_set
    
  - from: ACCEPTED_WITH_LIMITATION
    to: ACCEPTED
    requires: New evidence that resolves all documented limitations
    constraint: Limitations are preserved until explicitly resolved. They do not expire.
```

### 5.3 Forbidden Transitions

```yaml
forbidden_transitions:
  - from: BLOCKED
    to: ACCEPTED_WITH_LIMITATION
    rationale: A blocked finding must be fully resolved, not partially accepted.
    
  - from: HUMAN_REQUIRED
    to: EXECUTED
    rationale: Human authorization cannot be skipped. Write_set expansion does not eliminate the need for human approval.
    failure_mode: An agent might try to "work around" a HUMAN_REQUIRED state by broadening its write_set to exclude the protected file. This is forbidden.
    
  - from: DEFERRED
    to: ACCEPTED
    rationale: Deferred items must be executed or explicitly abandoned, not silently accepted.
    
  - from: NEEDS_EVIDENCE
    to: ACCEPTED
    rationale: Cannot skip the EXECUTED state. Evidence must be assembled and re-reviewed.
```

### 5.4 R15-R18 Failure Mode: Invalid State Transitions

In R17, the verdict was `ACCEPTED_WITH_LIMITATION`. A subsequent task attempted to treat this as fully `ACCEPTED` and proceed without addressing the two documented limitations (test results from full repo not ZIP-independent; governance pattern change deferred). The state machine requires limitations to be explicitly resolved before transitioning from `ACCEPTED_WITH_LIMITATION` to `ACCEPTED`.

In R18-WORKSPACE-CLOSURE, the agent claimed closure (implying `ACCEPTED`) while the register still showed discrepancies (implying `BLOCKED`). The correct state was `NEEDS_EVIDENCE` until the register was reconciled, which required the CLOSURE and EVIDENCE-MAINTENANCE sub-rounds.

---

## 6. Human Required Decision Record

Certain actions are beyond agent authority and require explicit human authorization. A Human Required Decision Record (HRDR) MUST exist before these actions are performed.

### 6.1 Mandatory HRDR Triggers

The following actions REQUIRE a Human Required Decision Record:

| # | Action | Rationale | R15-R18 Precedent |
|---|--------|-----------|-------------------|
| 1 | **Live dispatch** | Sending messages to external services (ChatGPT via CDP, API calls, webhook triggers) | R17 explicitly excluded live dispatch from accepted scope |
| 2 | **Protected file mutation** | Modifying AGENTS.md, CLAUDE.md, rules/core.md, capability-inventory.md, sub-agent-dispatch-protocol.md, lessons-learned.md | Core governance principle: agents must not self-modify governance |
| 3 | **Self-protecting hook modification** | Modifying hooks/pre-edit.governance.ps1, scripts/sadp-audit.ps1, or any script that enforces governance patterns | R18-CLEANUP: sadp-audit.ps1 modification flagged as P0_GOVERNANCE without HRDR |
| 4 | **Broad write_set expansion** | Adding files to write_set beyond the original TaskSpec scope after execution has begun | R16-BLOCKING-04: diff.patch contained out-of-scope files |
| 5 | **Project registry migration** | Changing project count, binding_status, or dispatch classification in PROJECT_REGISTRY.json | R18: PROJECT_REGISTRY.json modified (10 -> 11 projects) without explicit HRDR |
| 6 | **deny_path exception** | Writing to a path that appears in the deny_paths or deny_list policy | Hard governance boundary — no exception without human approval |
| 7 | **Sealed-files-manifest policy change** | Modifying hooks/sealed-files-manifest.json or the policy that governs sealed file protection | Self-protecting pattern — agent must not alter its own constraints |
| 8 | **Committing mock secret fixtures** | Adding files that match secret-scan deny_list patterns to version control | R18: secret-scan-output.txt files were deny-listed; committing them requires explicit authorization |
| 9 | **Changing finalizer rules** | Modifying the finalizer gate criteria in SADP 0.R.3 | Finalizer rules are the last governance checkpoint; altering them requires human oversight |

### 6.2 HRDR Format

```yaml
human_required_decision_record:
  decision_id: HRDR-{sequential_id}
  action_requested: [description of the action requiring authorization]
  trigger_category: [one of the 9 mandatory triggers above]
  risk_assessment:
    blast_radius: [files/systems affected]
    reversibility: reversible | partially_reversible | irreversible
    precedent: [prior HRDR IDs for similar decisions, or "none"]
  approver:
    approver_id: [human reviewer identifier]
    approved_at: [ISO-8601 timestamp]
    approval_channel: [conversation URL, session ID, or direct instruction reference]
  conditions:
    - [any conditions or limitations on the approval]
  expiration:
    expires_at: [ISO-8601 timestamp or "single_use"]
    scope: [specific task_id or "session"]
```

### 6.3 R15-R18 Failure Mode: Missing HRDR for Governance Pattern Changes

The R15 reviewer explicitly flagged that `scripts/sadp-audit.ps1` was modified without a Human Required Decision Record (listed as `P0_GOVERNANCE: self-protecting sadp-audit.ps1 modified without human_required approval`). This finding was carried as a blocker from R15 through R17 and ultimately resolved by splitting the task: the operations manual content was accepted, but the governance pattern change in sadp-audit.ps1 was deferred to a separate task (`OPERATIONS-MANUAL-AUDIT-PATTERN-BIND-A1`) with `status: HUMAN_REQUIRED`.

**Rule**: An agent that discovers it has performed an action requiring an HRDR without one MUST immediately halt, report the violation, and await human authorization before continuing. Retroactive HRDR creation is permitted only if the human reviewer explicitly approves it.

---

## 7. Workspace Closure Standard

Workspace closure is a deterministic state that can be verified mechanically. An agent claiming closure MUST satisfy the conditions below. Ambiguous or partially-verified closure claims are governance violations.

### 7.1 Closure States

```yaml
closure_states:
  - id: CLEAN
    name: Fully Clean
    conditions:
      - modified_tracked: 0
      - untracked_files: 0
    claim_allowed: "clean workspace"
    evidence_required: git-status-after.txt showing empty output
    
  - id: REGISTERED_CLOSURE
    name: Registered Closure
    conditions:
      - modified_tracked: 0
      - untracked_files: N (where N > 0)
      - all_untracked_in_register: true
    claim_allowed: "registered closure"
    evidence_required: >
      git-status-after.txt showing N untracked files,
      deferred-files-register.yaml accounting for all N files,
      safety-report.json with matching counts.
    register_categories:
      - deny_paths: Files blocked by deny_paths policy (e.g., NEG-009 fixtures)
      - deny_list: Files blocked by deny_list policy (e.g., secret-scan outputs)
      - pending_commit: Files to be committed in the next session
      - permanently_deferred: Files intentionally excluded with documented rationale
      
  - id: NOT_CLOSED
    name: Not Closed
    conditions:
      - modified_tracked: "> 0"
      - or:
        - untracked_files_not_in_register: "> 0"
    claim_allowed: "dirty workspace" or "not closed"
    evidence_required: git-status-after.txt showing the discrepancy
    
  - id: PERMANENTLY_DEFERRED
    name: Permanently Deferred
    conditions:
      - modified_tracked: 0
      - untracked_files: N
      - all_untracked_category: permanently_deferred or deny_paths or deny_list
    claim_allowed: "permanently deferred"
    evidence_required: deferred-files-register.yaml with permanent rationale for each file
```

### 7.2 Closure Verification Protocol

Before claiming any closure state, the agent MUST run:

```yaml
closure_verification:
  step_1:
    action: Capture git status --short
    output: git-status-after.txt
    validate: Output matches safety-report.json counts exactly.
    
  step_2:
    action: Count modified tracked files
    expected: 0 for any closure claim
    fail_action: Cannot claim closure. State = NOT_CLOSED.
    
  step_3:
    action: Enumerate all untracked files
    expected: Every untracked file appears in deferred-files-register.yaml exactly once
    fail_action: Cannot claim closure. State = NOT_CLOSED.
    
  step_4:
    action: Cross-reference safety-report.json with deferred-files-register.yaml
    expected: Counts match: modified_tracked + untracked = total entries in register
    fail_action: Register mismatch. State = NOT_CLOSED.
    
  step_5:
    action: Determine closure state
    mapping:
      - modified_0 + untracked_0: CLEAN
      - modified_0 + all_untracked_registered: REGISTERED_CLOSURE
      - modified_0 + all_untracked_permanent: PERMANENTLY_DEFERRED
      - modified_nonzero OR unregistered_untracked: NOT_CLOSED
```

### 7.3 Forbidden Closure Claims

```yaml
forbidden_claims:
  - claim: "clean workspace"
    when: untracked_files > 0
    rationale: Untracked files exist. Workspace is not clean. Use "registered closure" instead.
    failure_mode: R18 claimed "clean" with 27 untracked files. Reviewer rejected as BLOCKING-01.
    
  - claim: "workspace closed"
    when: modified_tracked > 0
    rationale: Modified tracked files indicate uncommitted work. Closure is invalid.
    
  - claim: "all files accounted for"
    when: any untracked file is not in deferred-files-register
    rationale: Unregistered untracked files are unaccounted artifacts.
    failure_mode: R18 initially missed 3 "other unexpected files" that were not in any register category.
    
  - claim: "registered closure"
    when: register exists but counts do not match git-status-after
    rationale: Internal consistency violation. All numbers must agree.
```

### 7.4 R15-R18 Failure Mode: Closure Claim Inflation

R18-WORKSPACE-CLOSURE initially claimed closure while `PROJECT_REGISTRY.json` showed as a modified tracked file (modified by an external process during the session). The agent had to produce a CLOSURE sub-round that explicitly documented this external modification in the register before the reviewer accepted the closure state. Similarly, commit `6022c187` was missing per-commit diff/show evidence, requiring the agent to generate `diff-6022c187.patch` and `git-show-6022c187.txt` retroactively.

The R18 cycle required three sub-rounds (CLEANUP, CLOSURE, EVIDENCE-MAINTENANCE) before achieving `REGISTERED_CLOSURE` with all 27 untracked files properly categorized: 17 deny_paths (NEG-009 fixtures), 3-5 deny_list (secret-scan outputs), and the remainder as session artifacts pending next commit.

**Rule**: Closure state MUST be determined by mechanical verification, not by agent assertion. The agent runs the closure verification protocol and reports the result. If the result is NOT_CLOSED, the agent MUST NOT claim closure regardless of how close the workspace appears.

---

## 8. Evidence Generation Hygiene

Generating evidence must not itself create new governance problems. This section defines hygiene rules that prevent recursive artifact pollution: the situation where the act of producing evidence creates new untracked files that themselves need evidence.

### 8.1 Builder Script Policy

```yaml
builder_script_policy:
  preferred:
    description: Use pre-existing tracked tools from scripts/ directory.
    examples:
      - scripts/evidence_pack_linter.py
      - scripts/pre_gpt_review_gate.py
      - scripts/sadp-audit.ps1
    rule: These are committed, tested, and covered by existing test suites.
    
  acceptable:
    description: Run temporary scripts outside the repository when possible.
    location: workspace scratch directory (outside canonical root)
    rule: Scripts run from outside the repo do not create untracked files inside it.
    
  restricted:
    description: Builder scripts created inside the repository.
    rule: Any script created inside D:\agent-acceptance MUST be one of:
      - committed: Added to version control with tests
      - removed: Deleted after use, with deletion recorded
      - registered: Listed in deferred-files-register.yaml with rationale
    failure_mode: R18 generated 7 "session artifact" scripts during evidence assembly. These became untracked files that needed to be committed in a subsequent sub-round.
```

### 8.2 Evidence Pack Assembly Rules

```yaml
assembly_rules:
  - id: EA-01
    name: no_new_untracked_without_registering
    rule: Generating the evidence pack MUST NOT create new untracked files without registering them in deferred-files-register.yaml.
    procedure: >
      Before running any evidence generation command, predict its output files.
      If output files will land inside the repository, add them to the register
      BEFORE generation. After generation, verify the register matches.
      
  - id: EA-02
    name: final_evidence_after_last_commit
    rule: The final evidence pack (safety-report.json, git-status-after.txt, deferred-files-register.yaml) MUST be generated AFTER the last commit in scope.
    rationale: Evidence generated before the final commit will not reflect the post-commit workspace state, creating a mismatch.
    failure_mode: R18 generated safety-report.json before the final commit, then the commit itself changed the workspace state. The report showed stale counts.
    
  - id: EA-03
    name: no_recursive_evidence
    rule: Generating evidence about evidence generation is forbidden. The evidence pack documents the task work, not the pack assembly process.
    rationale: Recursive evidence creates an infinite regress: evidence about evidence about evidence. The pack must have a clear termination point.
    
  - id: EA-04
    name: replay_labeling
    rule: When evidence is regenerated after the fact (re-running tests, re-capturing git status), it MUST be labeled:
      - original_timestamp: when the action actually occurred
      - replay_timestamp: when the evidence was regenerated
      - replay_reason: why regeneration was necessary
    rationale: Replay evidence has different trust properties. The reviewer must know whether evidence was captured live or reconstructed.
```

### 8.3 Anti-Pollution Protocol

```yaml
anti_pollution_protocol:
  before_evidence_generation:
    - step: Predict output files
      action: List all files that evidence generation commands will create.
    - step: Predict output locations
      action: Determine whether each output file lands inside or outside the repo.
    - step: Register predicted files
      action: Add any in-repo outputs to deferred-files-register.yaml BEFORE generation.
      
  during_evidence_generation:
    - step: Use --output-dir flags
      action: Direct evidence outputs to the _evidence/ directory (tracked) or workspace scratch (outside repo).
    - step: Avoid ad-hoc scripts in repo root
      action: If a one-off script is needed, create it in workspace scratch, run it, delete it.
      
  after_evidence_generation:
    - step: Verify no surprise files
      action: Run git status --short and compare against predicted outputs.
    - step: Reconcile discrepancies
      action: If unexpected files appeared, register them or remove them immediately.
    - step: Final cross-check
      action: safety-report.json counts match git-status-after.txt match deferred-files-register.yaml.
```

### 8.4 R15-R18 Failure Mode: Recursive Artifact Pollution

The R18 cycle is the canonical example of recursive artifact pollution:

1. **R18-CLEANUP**: The agent committed 6 session artifact scripts, creating commit `104ac8b1`. The commit itself generated evidence directories (`R18-followup-cleanup/`, `R18-FOLLOWUP-FINAL/`), which became new untracked files.
2. **R18-CLOSURE**: The agent created `diff-6022c187.patch` and `git-show-6022c187.txt` as retroactive evidence for an earlier commit. These evidence files became new untracked files that needed to be registered.
3. **R18-EVIDENCE-MAINTENANCE**: The agent committed 60 session artifact files from the closure process. This commit (`efd5b96e`) itself generated a new post-commit state that needed fresh evidence.

Each sub-round of evidence generation created new artifacts that required their own evidence, creating a three-step cascade before the workspace reached REGISTERED_CLOSURE.

The R16 cycle exhibited a different pollution pattern: the agent included `MANIFEST.json` and `hashes.sha256` in their own hash computation, creating a self-referential integrity check that was logically impossible to satisfy. This was resolved in R17 by excluding metadata files from their own hash lists.

**Rule**: Before any evidence generation activity, run the anti-pollution protocol. Predict outputs, register them, generate, and verify. If the generation creates more than 3 unexpected files, halt and reassess the generation approach.

---

## Appendix A: Quick Reference Card

```
+------------------+----------------------------------------------------------+
| Gate / Standard  | One-Line Rule                                            |
+------------------+----------------------------------------------------------+
| Startup Read     | Read 8 items before touching anything.                   |
| Pre-Task         | 6 checks pass before first file edit.                    |
| Pre-GPT-Review   | 10 canonical files, all parseable, no text-only.         |
| Evidence Pack    | JSON parses, YAML parses, every commit evidenced,        |
|                  | every untracked registered once, no self-ref hashes.     |
| State Machine    | 10 states, forbidden transitions enforced,               |
|                  | BLOCKED->ACCEPTED needs new evidence.                    |
| HRDR             | 9 trigger categories, no action without record.          |
| Workspace Closure| 4 states, mechanical verification, no false claims.      |
| Evidence Hygiene | Predict outputs, register before generate,               |
|                  | final evidence after last commit, no recursion.          |
+------------------+----------------------------------------------------------+
```

## Appendix B: R15-R18 Verdict Timeline

```
R15  PARTIAL_ACCEPTANCE_WITH_BLOCKERS
     4 blockers: paths, canonical files, JSON purity, manual-only split
     Retroactive erratum R15-INTEGRITY-01 (affects R3-R14)

R16  PARTIAL_ACCEPTANCE_WITH_REMAINING_EVIDENCE_BLOCKERS
     R15: 2 closed, 1 partial, 1 with limitation
     New: 4 blockers: review.md, self-ref hash, ZIP reproducibility, scope

R17  ACCEPTED_WITH_LIMITATION
     All R16 blockers closed
     Limitations: test env, governance pattern change deferred

R18  REGISTERED_CLOSURE (after 3 sub-rounds)
     CLEANUP: committed session artifacts, addressed 5 non-blocking items
     CLOSURE: reconciled register (27 untracked), evidenced all commits
     EVIDENCE-MAINTENANCE: committed 60 session files, reached stable state
```

---

**Version**: 1.0 | **Status**: active | **Enforcement**: All sections P0 unless marked otherwise.
