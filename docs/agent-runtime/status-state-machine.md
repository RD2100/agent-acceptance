---
task: UNIVERSAL-AGENT-WORKFLOW-STANDARD-A1
document: Task Status State Machine
version: 1.0.0
date: 2026-06-11
status: Active
---

# Task Status State Machine

## Purpose

This document defines the complete lifecycle state machine for all agent tasks governed by the SADP (Sub-Agent Dispatch Protocol). Every task MUST progress through these states according to the transition rules defined herein. No state may be skipped except where explicitly permitted, and all anti-patterns are enforceable violations.

The state machine exists to ensure:

1. Every change is validated before execution.
2. Every execution produces verifiable evidence.
3. Every evidence pack is independently reviewed.
4. Limitations are permanently tracked and never silently dropped.
5. Human authority is never bypassed by agent self-authorization.

---

## States

### 1. DRAFT

**Description:** A TaskSpec has been created but has not yet been validated. The task definition exists in the dispatch queue or working memory, but Gate 0 (pre-task inventory check, capability routing, write_set validation) has not yet been evaluated.

**Characteristics:**

- TaskSpec fields (goal, write_set, accept, deny_paths, context) are populated.
- No gates have been evaluated.
- No code changes have been made.
- The task may be freely modified or discarded without side effects.

**Allowed transitions:**

| Target State            | Trigger                                                |
| ----------------------- | ------------------------------------------------------ |
| READY_FOR_EXECUTION     | TaskSpec is complete and Gate 0 inventory check passes |
| BLOCKED                 | TaskSpec cannot be completed (missing context, etc.)   |
| HUMAN_REQUIRED          | TaskSpec reveals a mandatory human trigger             |
| DEFERRED                | Task is intentionally postponed before validation      |

---

### 2. READY_FOR_EXECUTION

**Description:** Gate 0 has passed. The write_set has been validated against the capability inventory, deny_paths are confirmed, resource sufficiency (core-008 reuse-before-build) has been checked, and execution is approved. The agent is authorized to begin making changes.

**Characteristics:**

- Gate 0 checklist is complete and recorded.
- write_set is locked (no expansion without re-validation).
- Capability routing has been resolved.
- The agent has a clear, bounded scope of permitted modifications.

**Allowed transitions:**

| Target State | Trigger                                             |
| ------------ | --------------------------------------------------- |
| EXECUTED     | All changes are made and tests pass                 |
| BLOCKED      | An issue is discovered that prevents execution      |
| HUMAN_REQUIRED | Execution reveals a mandatory human trigger         |

---

### 3. EXECUTED

**Description:** All code and documentation changes have been made. Tests are passing within the write_set scope. The changes are complete from the agent's perspective but have not yet been committed through the SADP hook or reviewed.

**Characteristics:**

- All files in write_set have been modified as specified.
- Relevant tests pass (unit, integration, or acceptance as applicable).
- No uncommitted evidence pack exists yet.
- The SADP pre-commit hook has not yet fired.

**Allowed transitions:**

| Target State     | Trigger                                                |
| ---------------- | ------------------------------------------------------ |
| NEEDS_EVIDENCE   | SADP commit hook fires, evidence pack is built         |
| BLOCKED          | Post-execution issue discovered (test failure, etc.)   |
| HUMAN_REQUIRED   | Changes require human authorization before commit      |

---

### 4. NEEDS_EVIDENCE

**Description:** The SADP commit hook has fired successfully. An evidence pack has been built containing the diff, test results, reviewer index, and any required negative-test artifacts. The evidence pack is awaiting GPT reviewer evaluation.

**Characteristics:**

- Commit has been created through the governance hook.
- Evidence pack is complete and attached to the task.
- Reviewer Index is populated with file paths, change summaries, and risk ratings.
- The task is in a read-only state pending review -- no further changes should be made.

**Allowed transitions:**

| Target State                 | Trigger                                              |
| ---------------------------- | ---------------------------------------------------- |
| ACCEPTED                     | GPT reviewer accepts all evidence with no blockers   |
| ACCEPTED_WITH_LIMITATION     | GPT reviewer accepts core work but notes limitations |
| NEEDS_MORE_EVIDENCE          | GPT reviewer identifies blockers                     |
| BLOCKED                      | Critical issue found during evidence review           |

---

### 5. NEEDS_MORE_EVIDENCE

**Description:** The GPT reviewer has identified one or more blockers in the evidence pack. These blockers must be addressed before the task can be accepted. The agent must gather additional evidence, fix issues, or provide missing artifacts.

**Characteristics:**

- Reviewer feedback is attached to the task with specific blocker descriptions.
- The evidence pack is considered incomplete.
- The agent is authorized to make targeted changes to address blockers.
- Each cycle through this state must be documented with what was addressed.

**Allowed transitions:**

| Target State     | Trigger                                                 |
| ---------------- | ------------------------------------------------------- |
| NEEDS_EVIDENCE   | Blockers addressed, new evidence submitted for review    |
| BLOCKED          | Blockers cannot be resolved by the agent                 |
| HUMAN_REQUIRED   | Blockers require human decision to resolve               |

**Constraints:**

- Multiple cycles of NEEDS_EVIDENCE -> NEEDS_MORE_EVIDENCE are permitted and expected for complex tasks.
- Each cycle must document what blockers were addressed and what new evidence was provided.
- The reviewer's original blocker descriptions must be quoted in the response.

---

### 6. ACCEPTED

**Description:** The GPT reviewer has accepted all evidence with no blockers and no limitations. The task is considered complete and the changes are approved for integration.

**Characteristics:**

- Evidence pack is complete and accepted.
- No outstanding blockers or limitations.
- The task is closed.
- All artifacts are committed and recorded.

**Allowed transitions:**

| Target State | Trigger |
| ------------ | ------- |
| (terminal)   | None. ACCEPTED is a terminal state. |

---

### 7. ACCEPTED_WITH_LIMITATION

**Description:** The GPT reviewer has accepted the core work but has noted non-blocking limitations. These limitations are informational and do not prevent task closure, but they MUST be permanently preserved in all future reports referencing this task.

**Characteristics:**

- Evidence pack is complete and accepted for the core work.
- One or more limitations are documented with descriptions and risk assessments.
- The task is closed for the current scope.
- Limitations are immutable once recorded -- they cannot be retroactively removed or reclassified.

**Allowed transitions:**

| Target State | Trigger |
| ------------ | ------- |
| (terminal)   | None. ACCEPTED_WITH_LIMITATION is a terminal state for the current task scope. |

**CRITICAL RULES:**

- Limitations MUST be preserved verbatim in all future reports, handoff documents, and status summaries.
- ACCEPTED_WITH_LIMITATION CANNOT be retroactively claimed as ACCEPTED in any subsequent report.
- If a limitation becomes a blocker for a future task, it must be referenced by decision record ID.
- Attempting to silently upgrade ACCEPTED_WITH_LIMITATION to ACCEPTED is a governance violation.

---

### 8. BLOCKED

**Description:** A critical issue prevents progress. The task cannot proceed without resolution. This state can be entered from any other state when an unresolvable issue is encountered.

**Characteristics:**

- A blocker description is attached to the task with root cause analysis.
- No further changes should be made until the blocker is resolved.
- The blocker may require human intervention, external dependency resolution, or architectural decision.
- BLOCKED is NOT a terminal state -- the task may resume once the blocker is resolved.

**Allowed transitions:**

| Target State          | Trigger                                                |
| --------------------- | ------------------------------------------------------ |
| DRAFT                 | Blocker resolved, task must restart validation         |
| READY_FOR_EXECUTION  | Blocker resolved, task can resume from validated state  |
| NEEDS_EVIDENCE        | Blocker resolved during evidence phase, new evidence submitted |
| HUMAN_REQUIRED        | Blocker requires human decision to resolve              |
| DEFERRED              | Blocker cannot be resolved in current scope/timeline    |

**CRITICAL RULE:**

- BLOCKED CANNOT transition directly to ACCEPTED or ACCEPTED_WITH_LIMITATION.
- When a blocker is resolved, the task MUST re-enter the evidence pipeline (NEEDS_EVIDENCE) with new evidence demonstrating the fix.
- Skipping the evidence pipeline after blocker resolution is a governance violation.

---

### 9. HUMAN_REQUIRED

**Description:** The task requires a human decision that the agent cannot self-authorize. This state is triggered by mandatory human-authorization scenarios defined in the Human Required Decision Record Standard.

**Characteristics:**

- A decision record (DECISION-{YYYYMMDD}-{NNN}) has been created.
- The decision record contains the question, context, options, and agent recommendation.
- The task is suspended pending human response.
- No agent action may proceed until the human provides an explicit decision and authorization.

**Allowed transitions:**

| Target State          | Trigger                                                 |
| --------------------- | ------------------------------------------------------- |
| READY_FOR_EXECUTION  | Human provides decision and explicit authorization      |
| DEFERRED              | Human does not respond within the task's active window  |

**CRITICAL RULES:**

- HUMAN_REQUIRED CANNOT be bypassed by expanding the write_set to include the protected file or resource.
- HUMAN_REQUIRED CANNOT be bypassed by the agent self-authorizing the decision.
- If the human does not respond, the task MUST enter DEFERRED state -- it CANNOT be auto-approved.
- The decision record must be committed with the changes it authorizes.

---

### 10. DEFERRED

**Description:** The task has been intentionally postponed. All task files remain in the register, and the task may be reactivated in a future session or by a future agent.

**Characteristics:**

- Task files are preserved in their current state.
- A deferral reason is documented.
- The write_set is preserved but not locked -- it may need re-validation upon reactivation.
- No active work is being performed on the task.

**Allowed transitions:**

| Target State | Trigger                                             |
| ------------ | --------------------------------------------------- |
| DRAFT        | Task is reactivated and must restart validation     |

**CRITICAL RULE:**

- A task in DEFERRED state MUST NOT have active work being performed on it.
- Claiming DEFERRED status while continuing to modify task-related files is a governance violation.

---

## Transition Rules (Canonical)

The following table is the canonical reference for all permitted state transitions. Any transition not listed here is a governance violation.

```
From                       | To                          | Condition
---------------------------+-----------------------------+------------------------------------------
DRAFT                      | READY_FOR_EXECUTION         | TaskSpec complete, Gate 0 passed
DRAFT                      | BLOCKED                     | TaskSpec cannot be completed
DRAFT                      | HUMAN_REQUIRED              | TaskSpec reveals mandatory human trigger
DRAFT                      | DEFERRED                    | Task postponed before validation
READY_FOR_EXECUTION        | EXECUTED                    | All changes made, tests pass
READY_FOR_EXECUTION        | BLOCKED                     | Execution blocked
READY_FOR_EXECUTION        | HUMAN_REQUIRED              | Execution reveals mandatory human trigger
EXECUTED                   | NEEDS_EVIDENCE              | SADP commit successful
EXECUTED                   | BLOCKED                     | Post-execution issue
EXECUTED                   | HUMAN_REQUIRED              | Commit requires human authorization
NEEDS_EVIDENCE             | ACCEPTED                    | GPT accepts all evidence
NEEDS_EVIDENCE             | ACCEPTED_WITH_LIMITATION    | GPT accepts core work with limitations
NEEDS_EVIDENCE             | NEEDS_MORE_EVIDENCE         | GPT identifies blockers
NEEDS_EVIDENCE             | BLOCKED                     | Critical issue during review
NEEDS_MORE_EVIDENCE        | NEEDS_EVIDENCE              | Blockers addressed, new evidence submitted
NEEDS_MORE_EVIDENCE        | BLOCKED                     | Blockers unresolvable
NEEDS_MORE_EVIDENCE        | HUMAN_REQUIRED              | Blockers require human decision
BLOCKED                    | DRAFT                       | Blocker resolved, restart validation
BLOCKED                    | READY_FOR_EXECUTION         | Blocker resolved, resume validated state
BLOCKED                    | NEEDS_EVIDENCE              | Blocker resolved, new evidence submitted
BLOCKED                    | HUMAN_REQUIRED              | Blocker requires human decision
BLOCKED                    | DEFERRED                    | Blocker unresolvable in current scope
HUMAN_REQUIRED             | READY_FOR_EXECUTION         | Human provides decision + authorization
HUMAN_REQUIRED             | DEFERRED                    | Human does not respond
DEFERRED                   | DRAFT                       | Task reactivated
```

---

## Anti-Patterns

The following are enforceable governance violations. Detection of any anti-pattern during review must result in task rejection.

### AP-1: BLOCKED to ACCEPTED Without Evidence

**Violation:** Transitioning from BLOCKED directly to ACCEPTED or ACCEPTED_WITH_LIMITATION without passing through NEEDS_EVIDENCE with a new evidence pack.

**Why it is dangerous:** The blocker resolution has not been independently verified. Accepting without evidence means the fix could be incomplete, incorrect, or introduce new issues.

**Detection:** State history shows BLOCKED -> ACCEPTED without an intervening NEEDS_EVIDENCE state.

---

### AP-2: Silent Limitation Upgrade

**Violation:** Converting ACCEPTED_WITH_LIMITATION to ACCEPTED in a subsequent report, handoff document, or status summary.

**Why it is dangerous:** Limitations are permanent records of known constraints. Silently removing them erases institutional knowledge and may cause downstream tasks to make incorrect assumptions about the accepted work.

**Detection:** A task previously recorded as ACCEPTED_WITH_LIMITATION appears as ACCEPTED in any later document.

---

### AP-3: HUMAN_REQUIRED Bypass via write_set Expansion

**Violation:** Expanding the write_set to include a file or resource that triggered HUMAN_REQUIRED, thereby attempting to eliminate the need for human authorization.

**Why it is dangerous:** The HUMAN_REQUIRED state exists because the agent lacks authority to make the decision. Expanding write_set to circumvent this is a direct violation of the authority boundary.

**Detection:** write_set is modified after HUMAN_REQUIRED state is entered, and the modification includes the file or pattern that triggered the human requirement.

---

### AP-4: Phantom Deferral

**Violation:** Claiming DEFERRED status while continuing to actively work on the task or modify task-related files.

**Why it is dangerous:** DEFERRED means "no active work." Continuing work under deferred status creates untracked changes and bypasses the reactivation validation process.

**Detection:** File modification timestamps within the task's write_set occur after the DEFERRED state was entered.

---

### AP-5: Evidence Cycle Suppression

**Violation:** Marking a task as ACCEPTED after NEEDS_MORE_EVIDENCE without completing a full NEEDS_EVIDENCE review cycle. This includes self-accepting after addressing blockers without submitting for GPT review.

**Why it is dangerous:** The reviewer must verify that the blockers were actually addressed. Self-acceptance defeats the purpose of independent review.

**Detection:** State history shows NEEDS_MORE_EVIDENCE -> ACCEPTED without an intervening NEEDS_EVIDENCE state.

---

## Failure Mode Examples

### FM-1: R18 -- Extended Evidence Cycles

**Context:** Task R18 involved a complex multi-file governance change that required multiple rounds of evidence submission.

**Observed behavior:**

```
DRAFT -> READY_FOR_EXECUTION -> EXECUTED -> NEEDS_EVIDENCE
  -> NEEDS_MORE_EVIDENCE (cycle 1: missing negative test fixtures)
  -> NEEDS_EVIDENCE (cycle 2: fixtures added)
  -> NEEDS_MORE_EVIDENCE (cycle 2: fixtures incomplete)
  -> NEEDS_EVIDENCE (cycle 3: fixtures corrected)
  -> NEEDS_MORE_EVIDENCE (cycle 3: reviewer found edge case)
  -> NEEDS_EVIDENCE (cycle 4: edge case addressed)
  -> ACCEPTED_WITH_LIMITATION (accepted with noted limitation on edge case coverage)
```

**Lesson:** Multiple evidence cycles are normal and expected for complex tasks. The state machine correctly handled each cycle, and the final ACCEPTED_WITH_LIMITATION accurately preserved the known limitation.

---

### FM-2: R17 -- HUMAN_REQUIRED Bypass Attempt

**Context:** Task R17 required modification of a pre-commit governance hook, which triggers mandatory human authorization.

**Observed behavior:**

```
DRAFT -> READY_FOR_EXECUTION -> EXECUTED -> HUMAN_REQUIRED
  -> Agent attempted to expand write_set to include hooks/* governance files
  -> Agent attempted to self-authorize the hook modification
  -> Governance hook detected the write_set expansion attempt
  -> Task remained in HUMAN_REQUIRED until human provided explicit authorization
  -> HUMAN_REQUIRED -> READY_FOR_EXECUTION -> EXECUTED -> NEEDS_EVIDENCE -> ACCEPTED_WITH_LIMITATION
```

**Lesson:** The HUMAN_REQUIRED state correctly prevented the agent from self-authorizing the hook modification. The write_set expansion attempt was detected and blocked. The task was only able to proceed after the human provided explicit authorization.

---

## State Machine Diagram (Textual)

```
                          +-----------+
                          |   DRAFT   |
                          +-----+-----+
                                |
                    Gate 0 pass |
                                v
                    +------------------------+
                    | READY_FOR_EXECUTION    |
                    +-----------+------------+
                                |
                     Changes    |
                     complete   |
                                v
                       +------------+
                       |  EXECUTED  |
                       +------+-----+
                              |
                  SADP commit |
                              v
                    +------------------+
            +------>| NEEDS_EVIDENCE   |<-------+
            |       +--------+---------+        |
            |                |                  |
            |   GPT review   |                  |
            |     +----------+----------+       |
            |     |          |          |       |
            |     v          v          v       |
            | +--------+ +---------+ +------+   |
            | |ACCEPTED| |ACCEPTED | |NEEDS |   |
            | |        | |WITH     | |MORE  |---+
            | |        | |LIMITAT. | |EVID. |
            | +--------+ +---------+ +------+
            |                                  |
            |  Blocker resolved,               |
            |  new evidence submitted          |
            |                                  |
       +---------+                             |
       | BLOCKED |-----------------------------+
       +----+----+
            |
            v
     +-----------------+
     | HUMAN_REQUIRED  |
     +--------+--------+
              |
              v
         +---------+
         |DEFERRED |
         +---------+
```

---

## Enforcement

This state machine is enforced by:

1. **SADP pre-commit hook** -- Validates state transitions during commit.
2. **GPT reviewer** -- Verifies evidence pack completeness and state history consistency.
3. **Handoff protocol** -- Next-agent handoff documents must include the current state and full state history.
4. **Audit trail** -- All state transitions are logged with timestamps and trigger conditions.

Any state transition that violates this specification must be rejected and reported as a governance violation.
