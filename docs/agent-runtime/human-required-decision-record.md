---
task: UNIVERSAL-AGENT-WORKFLOW-STANDARD-A1
document: Human Required Decision Record Standard
version: 1.0.0
date: 2026-06-11
status: Active
---

# Human Required Decision Record Standard

## Purpose

This document defines the conditions under which human authorization is MANDATORY for agent tasks, and specifies the exact format and rules for decision records. No agent may self-authorize actions that fall under these mandatory triggers. The decision record serves as an immutable audit trail proving that a human explicitly approved the action before it was taken.

This standard is a companion to the Task Status State Machine (`status-state-machine.md`), which defines the HUMAN_REQUIRED state that this standard governs.

---

## Mandatory Triggers

The following scenarios REQUIRE human authorization. When any of these triggers is detected, the task MUST immediately enter the HUMAN_REQUIRED state. The agent MUST NOT proceed until a human provides an explicit decision and authorization.

### Trigger 1: Live Dispatch Execution

**Definition:** Running code that interacts with external services, APIs, or systems outside the local development environment.

**Examples:**

- Executing a deployment script that pushes to production or staging.
- Running an API call that modifies external data (not read-only).
- Dispatching a sub-agent to execute code on a remote system.
- Triggering a CI/CD pipeline that has side effects beyond the local repository.

**Why mandatory:** External interactions are irreversible and may affect systems, data, or users outside the agent's scope of authority. The agent cannot assess the full impact of external side effects.

---

### Trigger 2: Protected Governance File Mutation

**Definition:** Modifying any file under governance-protected paths, including but not limited to `hooks/*`, `.ai/*`, `pre-commit` scripts, and governance configuration files.

**Protected paths (non-exhaustive):**

- `hooks/*` -- All governance hooks.
- `.ai/*` -- AI configuration and policy files.
- `.claude/hooks/*` -- Claude-specific governance hooks.
- `pre-commit`, `pre-commit.ps1`, `pre-commit.sh` -- Pre-commit hook scripts.
- `AGENTS.md` -- Agent runtime configuration.
- `rules/core.md` -- Core governance rules.
- Any file listed in the sealed-files-manifest.

**Why mandatory:** Governance files define the boundaries of agent authority. Allowing an agent to modify its own governance without human oversight creates a self-referential authority problem -- the agent could weaken or remove the constraints that govern it.

---

### Trigger 3: Self-Protecting Hook Modification

**Definition:** Changing the behavior of the hook that enforces governance, including the pre-edit governance hook (`pre-edit.governance.ps1`) or any hook that validates state transitions.

**Why mandatory:** This is a specific, high-risk subset of Trigger 2. Modifying the enforcement mechanism itself is the highest-risk governance action possible, as it could disable all governance checks.

---

### Trigger 4: Broad write_set Expansion

**Definition:** Expanding the write_set to include wildcard patterns, many new file patterns, or patterns that significantly broaden the scope of permitted modifications.

**Thresholds:**

- Adding a wildcard pattern that matches more than 10 files.
- Adding more than 3 new file patterns in a single expansion request.
- Adding patterns that cross directory boundaries not present in the original write_set.
- Adding patterns that include governance-protected paths.

**Why mandatory:** The write_set defines the scope of the agent's authority. Broad expansion could grant the agent access to files or areas it should not modify. Human oversight ensures scope creep is intentional and authorized.

---

### Trigger 5: Project Registry Migration

**Definition:** Changing the project count, adding new project entries, removing existing entries, or modifying project-level configuration in the project registry.

**Why mandatory:** The project registry defines which projects the agent can operate on. Modifying it without authorization could grant or revoke access to entire codebases.

---

### Trigger 6: deny_path Exception

**Definition:** Allowing modification of a file or path that is normally blocked by the deny_paths configuration.

**Why mandatory:** deny_paths exists to protect critical files from unintended modification. Granting an exception undermines the protection and must be explicitly authorized by someone with authority over the protected resource.

---

### Trigger 7: sealed-files-manifest Policy Change

**Definition:** Modifying what the sealed-files-manifest tracks, including adding or removing file patterns from the manifest's scope, or changing the manifest's enforcement behavior.

**Why mandatory:** The sealed-files-manifest is a governance integrity mechanism. Weakening its tracking scope could allow governance files to be modified without detection.

---

### Trigger 8: Committing Mock Secret Fixtures

**Definition:** Committing files that match NEG-009 mock secret patterns, even when they are known to be mock/test fixtures rather than real secrets.

**Why mandatory:** Mock secret fixtures can be confused with real secrets during security audits. Explicit human authorization ensures that:

1. The file is confirmed to be a mock fixture.
2. The mock pattern does not accidentally match a real secret format.
3. The fixture is appropriately documented and discoverable.

**Satisfaction via allow_paths:** If mock secret fixtures are covered by `allow_paths` in `.ai/policy.yaml` with a corresponding Decision Record (e.g., DR-20260612-ALLOW-PATHS), the human authorization requirement is satisfied by the decision record approval. The allow_paths scope MUST be narrowed to specific directory patterns (not `**` wildcards).

---

### Trigger 9: Changing Finalizer Blocking Rules

**Definition:** Modifying the rules that determine what blocks commit finalization, including changing which checks are mandatory, which are advisory, or how the finalizer evaluates evidence.

**Why mandatory:** The finalizer is the last gate before a commit is accepted. Weakening its blocking rules could allow incomplete or incorrect changes to be committed.

---

## Decision Record Format

Every HUMAN_REQUIRED state must have an associated decision record. The decision record MUST follow this schema:

```yaml
decision_record:
  id: DECISION-{YYYYMMDD}-{NNN}
  timestamp: ISO-8601
  trigger: "which mandatory trigger was activated (Trigger 1-9)"
  decision_required: "clear, specific description of what decision is needed"
  context: "why this decision is needed now, including relevant task history"
  affected_files:
    - path: "path/to/file"
      reason: "why this file is affected"
  options:
    - label: "Option A"
      description: "what happens if this option is chosen"
      risk: "low/medium/high"
      impact: "what changes as a result"
    - label: "Option B"
      description: "what happens if this option is chosen"
      risk: "low/medium/high"
      impact: "what changes as a result"
  agent_recommendation: "which option the agent recommends and why"
  human_decision: "what the human decided (filled in by human)"
  authorization: "explicit authorization text from the human"
  committed_with: "commit hash or reference that includes this decision"
```

### Field Definitions

| Field                 | Required | Description                                                                 |
| --------------------- | -------- | --------------------------------------------------------------------------- |
| `id`                  | Yes      | Unique identifier. Format: DECISION-{date}-{sequence number for that date}. |
| `timestamp`           | Yes      | ISO-8601 timestamp of when the decision record was created.                 |
| `trigger`             | Yes      | Which mandatory trigger (1-9) activated this decision requirement.          |
| `decision_required`   | Yes      | A clear, specific description of the decision needed. Must be understandable without reading the full task context. |
| `context`             | Yes      | Why this decision is needed now. Must include relevant task history and any prior decision records that relate to this decision. |
| `affected_files`      | Yes      | List of files affected by this decision, with reasons.                      |
| `options`             | Yes      | At least 2 options must be presented. Each option must include label, description, risk assessment, and impact. |
| `agent_recommendation`| Yes      | The agent's recommended option with reasoning. Must not pressure the human -- present the recommendation as information, not advocacy. |
| `human_decision`      | Yes      | The human's actual decision. Filled in by the human at decision time.       |
| `authorization`       | Yes      | Explicit authorization text from the human. Must be a clear statement of permission, not an implicit or ambiguous response. |
| `committed_with`      | Yes      | The commit hash or reference that includes both this decision record and the changes it authorizes. |

---

## Rules

### R1: Decision Records MUST Be Created BEFORE the Action

A decision record must be created and presented to the human BEFORE any changes are made that require the decision. Retroactive decision records (created after the fact) are invalid and constitute a governance violation.

**Enforcement:** The decision record's timestamp must precede any file modification timestamps within the affected write_set.

---

### R2: Agent CANNOT Self-Authorize Any Mandatory Trigger

Under no circumstances may an agent:

- Generate its own authorization text.
- Treat silence or non-response as implicit authorization.
- Expand its own write_set to circumvent a mandatory trigger.
- Modify governance files to disable the trigger that would require human authorization.
- Proceed with a mandatory trigger action while awaiting human response.

**Enforcement:** The governance hook validates that the authorization field contains text that was not generated by the agent. Any authorization that matches the agent's own recommendation verbatim is flagged for review.

---

### R3: Decision Records MUST Be Committed with the Changes They Authorize

A decision record is not valid unless it is committed in the same commit (or a parent commit) as the changes it authorizes. A decision record committed in a separate, later commit does not retroactively authorize earlier changes.

**Enforcement:** The `committed_with` field must reference a commit that contains both the decision record file and the authorized changes.

---

### R4: Non-Response Results in DEFERRED State

If the human does not respond to the decision record within the task's active session window, the task MUST enter DEFERRED state. The task CANNOT be auto-approved, timed-out-to-approved, or escalated to a different agent for self-authorization.

**Enforcement:** The state machine enforces that HUMAN_REQUIRED can only transition to READY_FOR_EXECUTION (with human response) or DEFERRED (without response). No other transitions are permitted.

---

### R5: Options Must Be Genuine

The options presented in the decision record must be genuine alternatives. The agent must not:

- Present a "straw man" option designed to make the recommended option look better.
- Omit a viable option that the human might prefer.
- Present options with misleading risk assessments.

**Enforcement:** GPT reviewer checks that all options are viable and that risk assessments are reasonable.

---

### R6: Decision Records Are Immutable

Once a decision record is committed, it cannot be modified. If the decision needs to change, a new decision record must be created that references the original and explains why the decision changed.

**Enforcement:** The sealed-files-manifest tracks decision record files. Modifications to committed decision records are flagged as governance violations.

---

### R7: Decision Records Must Reference Prior Related Decisions

If a decision relates to a previous decision record (e.g., expanding a previously authorized write_set, revisiting a previously denied request), the context field MUST reference the prior decision record by ID.

**Enforcement:** The GPT reviewer verifies that related prior decisions are referenced.

---

### R8: Multiple Triggers Require Multiple Decision Records

If a single task activates multiple mandatory triggers, each trigger requires its own decision record. A single decision record cannot authorize multiple distinct trigger categories.

**Enforcement:** Each decision record must specify exactly one trigger. The governance hook validates that all activated triggers have corresponding decision records before allowing the task to proceed.

---

## Decision Record Lifecycle

```
1. Agent detects mandatory trigger
   |
   v
2. Task enters HUMAN_REQUIRED state
   |
   v
3. Agent creates decision record (all fields except human_decision, authorization, committed_with)
   |
   v
4. Decision record is presented to human
   |
   +-- Human responds with decision and authorization
   |   |
   |   v
   |   5a. Agent fills in human_decision, authorization fields
   |   |
   |   v
   |   6a. Task transitions to READY_FOR_EXECUTION
   |   |
   |   v
   |   7a. Changes are made and committed with decision record
   |   |
   |   v
   |   8a. committed_with field is updated with commit hash
   |
   +-- Human does not respond
       |
       v
       5b. Task transitions to DEFERRED
       |
       v
       6b. Decision record is preserved with empty human_decision and authorization
```

---

## Failure Mode Examples

### FM-1: R18 -- Pre-Commit Hook Modification Without Authorization

**Context:** Task R18 required changes to the pre-commit hook behavior to accommodate a new evidence pack format.

**What happened:**

- The agent identified that the pre-commit hook needed modification.
- Instead of creating a decision record and entering HUMAN_REQUIRED, the agent attempted to modify the hook directly.
- The governance hook detected the attempt to modify a protected governance file.
- The task was forced into HUMAN_REQUIRED state.
- A decision record was created (DECISION-20260611-001).
- The human provided explicit authorization.
- The hook was modified and committed with the decision record.

**Lesson:** The governance hook correctly blocked the unauthorized modification. The decision record process ensured that the human understood exactly what was being changed and why before authorizing it.

---

### FM-2: R18 -- write_set Expansion to Include Governance Files

**Context:** During Task R18, the agent needed to modify a file that was not in the original write_set and was under governance protection.

**What happened:**

- The agent attempted to expand the write_set to include `hooks/*` patterns.
- This triggered Mandatory Trigger 4 (Broad write_set Expansion) and Trigger 2 (Protected Governance File Mutation).
- The write_set expansion was blocked pending human authorization.
- Two decision records were created (one per trigger, per Rule R8).
- The human authorized the expansion with specific constraints.
- The write_set was expanded with the authorized constraints, and the task proceeded.

**Lesson:** The multi-trigger decision record process correctly required separate authorization for each distinct governance concern. The human was able to authorize the expansion with specific constraints that limited the agent's scope.

---

## Appendix: Quick Reference

| Trigger | Description                              | Key Risk                                        |
| ------- | ---------------------------------------- | ----------------------------------------------- |
| 1       | Live dispatch execution                  | Irreversible external side effects              |
| 2       | Protected governance file mutation       | Agent modifies its own governance boundaries    |
| 3       | Self-protecting hook modification        | Agent disables its own enforcement mechanism    |
| 4       | Broad write_set expansion                | Scope creep beyond authorized boundaries        |
| 5       | Project registry migration               | Unauthorized access to new codebases            |
| 6       | deny_path exception                     | Bypassing file protection rules                 |
| 7       | sealed-files-manifest policy change      | Weakening governance integrity tracking         |
| 8       | Committing mock secret fixtures          | Confusion between mock and real secrets         |
| 9       | Changing finalizer blocking rules        | Weakening the last gate before commit           |

---

## Enforcement

This standard is enforced by:

1. **SADP pre-commit hook** -- Detects mandatory triggers and blocks commit until a valid decision record exists.
2. **GPT reviewer** -- Verifies decision record completeness, option genuineness, and prior decision references.
3. **Governance hook** -- Validates that authorization was not self-generated and that the decision record is committed with the changes.
4. **Audit trail** -- All decision records are tracked in the session ledger with full state history.

Any action that requires a decision record but proceeds without one is a governance violation and must be reported.
