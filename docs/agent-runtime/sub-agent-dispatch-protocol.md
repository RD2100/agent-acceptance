# Sub-Agent Dispatch Protocol (SADP) v1.0

> RD2100 Agent Runtime v2 | 2026-05-28
> Canonical root: `D:\agent-acceptance`
> Default development workflow for Codex + Claude Code collaboration

---

## 0. Overview

SADP defines the default pattern for multi-agent development:

```
[Codex Goal Agent]                      [Claude Code Agent]
     |                                         |
     |  1. Decompose goal ï¿½ï¿½ TaskSpec            |
     |  2. Dispatch TaskSpec to sub-agent       |
     |---------------------------------------->|
     |                                         | 3. Execute task with full context
     |                                         | 4. Collect evidence (test results, diffs)
     |                                         | 5. Produce ExecutionReport
     |  6. Receive ExecutionReport             |
     |<----------------------------------------|
     |  7. Evaluate against acceptance gates    |
     |  8. Issue next TaskSpec or mark complete |
```

**Roles:**
- **Codex Goal Agent** (planning tier): Decomposes goals, dispatches tasks, evaluates reports, maintains plan state. Uses `update_plan` and `create_goal` tools.
- **Claude Code Agent** (execution tier): Receives TaskSpec, executes implementation, collects evidence, returns ExecutionReport. Uses filesystem, git, test runners.
- **Human Reviewer** (oversight tier): Reviews ExecutionReports for P0/P1 tasks, approves gate decisions, signs off on capability registrations.

**Key Principle**: TaskSpec is a self-contained contract. The sub-agent receives ALL context it needs in the dispatch ï¿½ï¿½ it does not re-derive the goal.

---



### 0. Gate 0: Resource Sufficiency Check (BEFORE any TaskSpec)

Before creating any TaskSpec that adds, creates, or introduces something new, the plan agent MUST run the Resource Sufficiency Check per core-008:

```
1. Existence    ï¿½ï¿½ Does something already cover this need?
2. Coverage     ï¿½ï¿½ Can minimal change to existing cover it?
3. Composition  ï¿½ï¿½ Can existing resources be combined?
4. Protocol     ï¿½ï¿½ Does existing workflow already handle this?
5. Precedent    ï¿½ï¿½ Have lessons learned recorded this pattern?
```

If the check finds existing coverage ï¿½ï¿½ **Do not create TaskSpec. Return reuse plan.**

Execute agent MUST reject any additive TaskSpec that lacks documented sufficiency check.

### 0.1 Gate 0 Ledger (Mandatory TaskSpec Field)

Every TaskSpec MUST include a `gate_0` YAML block recording the outcome of the Gate 0 Resource Sufficiency Check.

```yaml
gate_0:
  triggered: true
  inventory_checked: true
  inventory_refs: [list of capability IDs checked]
  rules_checked: [list of rule IDs consulted]
  lessons_checked: [list of lesson IDs checked]
  sufficiency_result: sufficient | insufficient | partial
  decision: reuse | build_delta | escalate
  delta_justification: [required if decision is build_delta]
```

**Rule: missing `gate_0` => execute agent MUST reject.**

### 0.2 Conflict Registry (Mandatory TaskSpec Fields)

Every TaskSpec MUST declare its file access scope to enable safe parallel dispatch:

```yaml
conflict_registry:
  read_set: [files this task will read]
  write_set: [files this task will modify]
  protected_files_touched: true | false
  conflict_level: none | low | high
```

**Rules:**

1. **Write-set serialization**: If a task's `write_set` overlaps with another active task's `write_set`, tasks MUST be serialized (wait, do not parallel-execute).
2. **Protected files require exclusive lock**: The following files are protected and require an exclusive lock (no other task may read or write them concurrently):
   - `AGENTS.md`, `CLAUDE.md`, `capability-inventory.md`
   - The SADP protocol file (`sub-agent-dispatch-protocol.md`)
   - Core rules (`docs/agent-runtime/rules/core.md`)
   - Lessons log (`docs/agent-runtime/lessons-learned.md`)
3. **No git merge as primary resolution**: Agents MUST NOT rely on git merge as the primary conflict resolution mechanism. Serialization and exclusive locks are the mandatory approach.

## 1. TaskSpec Format

Every task dispatched from Codex Goal Agent to Claude Code Agent uses this format:

```markdown
## Task: [title]

- **ID**: task-[8-char-uuid]
- **Batch**: batch-[name]
- **Risk**: low | medium | high | critical
- **Priority**: P0 | P1 | P2 | P3
- **Goal**: [1-3 sentence concrete objective]
- **Context**: [what happened before this task, relevant state]
- **Allowed Files**: [explicit paths, never "any" or "all"]
- **Forbidden**: [explicit constraints: no edits to X, no package install, etc.]
- **Gate 0 Ledger**:
  ```yaml
  gate_0:
    triggered: true
    trigger_reason: [why Gate 0 was triggered]
    inventory_checked: true
    inventory_refs: [list of capability IDs checked]
    rules_checked: [list of rule IDs consulted]
    lessons_checked: [list of lesson IDs checked]
    sufficiency_result: sufficient | insufficient | partial
    decision: reuse | build_delta | escalate
    delta_justification: [required if decision is build_delta]
  ```
- **Conflict Registry**:
  ```yaml
  conflict_registry:
    read_set: [files this task will read]
    write_set: [files this task will modify]
    protected_files_touched: true | false
    conflict_level: none | low | high
  ```
- **Acceptance Gates**:
  1. [gate-1: e.g., `cargo build` exits 0]
  2. [gate-2: e.g., test X passes]
  3. ...
- **Expected Output**: [files created/modified, artifacts produced]
- **Rollback**: [command to undo if blocked]
- **Report To**: [where to return ExecutionReport ï¿½ï¿½ default: calling agent session]
```

### Example

```markdown
## Task: Add rate-limiting middleware

- **ID**: task-a1b2c3d4
- **Batch**: batch-api-hardening
- **Risk**: medium
- **Priority**: P1
- **Goal**: Add a rate-limiting middleware to the Express API that limits requests to 100/min per IP using express-rate-limit.
- **Context**: Previous task added helmet middleware. API entry is `src/app.ts:42`.
- **Allowed Files**:
  - `src/middleware/rateLimiter.ts` (new)
  - `src/app.ts` (add middleware registration only)
  - `tests/middleware/rateLimiter.test.ts` (new)
- **Forbidden**:
   - Do not modify any other middleware
   - Do not change the Express app structure
   - Do not add npm packages other than express-rate-limit
- **Gate 0 Ledger**:
  ```yaml
  gate_0:
    triggered: true
    trigger_reason: "New middleware introduced; Gate 0 required per core-008"
    inventory_checked: true
    inventory_refs:
      - rate-limiting (partial coverage via proxy, no in-app middleware)
      - express-middleware (existing helmet middleware)
    rules_checked:
      - core-008
      - coding-005
    lessons_checked:
      - LL-003
    sufficiency_result: insufficient
    decision: build_delta
    delta_justification: "No in-app rate-limiting exists; proxy config does not cover per-route limits"
  ```
- **Conflict Registry**:
  ```yaml
  conflict_registry:
    read_set:
      - src/app.ts
      - src/middleware/ (existing patterns)
    write_set:
      - src/middleware/rateLimiter.ts
      - src/app.ts
      - tests/middleware/rateLimiter.test.ts
    protected_files_touched: false
    conflict_level: low
  ```
- **Acceptance Gates**:
   1. `npm test -- tests/middleware/rateLimiter.test.ts` passes
   2. `npm run build` succeeds
   3. No regression in existing tests (`npm test`)
- **Expected Output**: rateLimiter.ts, updated app.ts, rateLimiter.test.ts
- **Rollback**: `git checkout -- src/app.ts && rm src/middleware/rateLimiter.ts tests/middleware/rateLimiter.test.ts`
- **Report To**: return ExecutionReport to this session
```

---

## 2. ExecutionReport Format

Every task completion returns this format:

```markdown
## ExecutionReport: [task-id]

- **Status**: PASS | FAIL | BLOCKED
- **Summary**: [1-3 sentences: what was done, what was found]
- **Changed Files**:
  - `path/to/file.ts` (+N lines, -M lines) ï¿½ï¿½ [what changed]
  - ...
- **Unchanged But Inspected**:
  - `path/to/file.ts` ï¿½ï¿½ [why inspected, why not changed]
- **Evidence**:
  - Test results: [command + output summary]
  - Build: [pass/fail]
  - Lint: [pass/fail + any new warnings]
- **Risks**:
  - [anything the next agent or reviewer should watch for]
- **Reviewer Index**:
  - `path/to/critical-change.ts` ï¿½ï¿½ [why review recommended]
  - ...
- **Next Steps Suggested**:
  - [optional: what logically follows]
- **Capabilities Used**:
  - [capability name] ï¿½ï¿½ [Status: approved]
```

### Example

```markdown
## ExecutionReport: task-a1b2c3d4

- **Status**: PASS
- **Summary**: Added rate-limiting middleware (100 req/min per IP). All tests pass, no regression.
- **Changed Files**:
  - `src/middleware/rateLimiter.ts` (+45 lines) ï¿½ï¿½ new middleware
  - `src/app.ts` (+3 lines, -0 lines) ï¿½ï¿½ registered middleware at line 48
  - `tests/middleware/rateLimiter.test.ts` (+62 lines) ï¿½ï¿½ 6 test cases
- **Evidence**:
  - `npm test -- tests/middleware/rateLimiter.test.ts`: 6/6 PASS
  - `npm test`: 47/47 PASS (no regression)
  - `npm run build`: success
- **Risks**: None. Rate limit window (1 min) may need tuning under real load.
- **Reviewer Index**:
  - `src/middleware/rateLimiter.ts:30-35` ï¿½ï¿½ sliding window logic, verify correctness
- **Capabilities Used**:
  - rg/Grep/Read ï¿½ï¿½ Status: approved
  - Shell (read-only) ï¿½ï¿½ Status: approved
```

---

## 3. Dispatch Flow

### 3.1 Codex Goal Agent (Plan ï¿½ï¿½ Dispatch)

1. **Goal agent** enters goal mode (`<goal_context>` active)
2. **Decomposes** goal into batch(es) of tasks using `update_plan`
3. **Dispatches** each task as a self-contained TaskSpec block
4. The sub-agent session receives the TaskSpec as its primary instruction
5. TaskSpec includes ALL context ï¿½ï¿½ sub-agent does not re-derive

### 3.2 Claude Code Agent (Execute ï¿½ï¿½ Report)

1. **Receives** TaskSpec as session instruction
2. **Reads** allowed files, notes forbidden constraints
3. **Executes** the task: reads, edits, tests
4. **Collects evidence**: test output, build results, git diff stats
5. **Returns** ExecutionReport to the goal agent session

### 3.3 Goal Agent (Evaluate ï¿½ï¿½ Next)


### 3.3a Plan Agent Review Procedure (Mandatory After Every ExecutionReport)

Before accepting an ExecutionReport and dispatching the next task, the plan agent MUST run this review checklist:

```yaml
plan_agent_review:
  gate_evaluation:
    - gate_id: [each acceptance gate from TaskSpec]
      status: pass | fail
      evidence: [actual output matching gate condition]
  
  regression_tests:
    audit_type: full | targeted
    checks:
      - R1: core_rules_integrity       # All existing rule IDs still present
      - R2: capability_inventory_count  # No capability entries lost
      - R3: lessons_integrity           # All lesson IDs still present
      - R4: file_size_sanity            # No file exploded beyond expected bounds
      - R5: markdown_structure          # All code blocks closed, no broken YAML
      - R6: task_template_intact        # TaskSpec format still valid after modifications
    result: pass | fail | false_positive

  changed_files_audit:
    - file: [path]
      expected_change: [what should have changed]
      actual_change: [what actually changed]
      unexpected_modifications: [files changed but not in TaskSpec allowed_files]

  decision: accept | reject | request_revision
```

**Regression Test Triggers:**
- `full` ¡ª after any task that modifies governance files (rules, protocols, inventory, lessons, AGENTS.md)
- `targeted` ¡ª after tasks that modify only application code (check only affected modules)

**Decision Rules:**
- All gates PASS + regression PASS ¡ú `accept`, dispatch next task
- Gate FAIL ¡ú `request_revision` back to execute agent with specific gate failure
- Regression FAIL ¡ú `reject`, halt batch, flag for human review
- Unexpected file modifications ¡ú `reject`, potential scope violation


1. **Receives** ExecutionReport
2. **Evaluates** against acceptance gates:
   - All gates PASS ï¿½ï¿½ mark task complete, dispatch next if any remain
   - Any gate FAIL ï¿½ï¿½ analyze, possibly revise TaskSpec and re-dispatch
   - BLOCKED ï¿½ï¿½ escalate to human reviewer
3. **Updates** `update_plan` with new status
4. **Dispatches** next task or marks goal complete

---

## 4. Integration Points

### 4.1 dev-frame (Task State Machine)

AI Workflow Hub (`D:\dev-frame\ai-workflow-hub`) manages task state:
- `tasks.yaml`: Task definitions with status, risk, dependencies
- `projects.yaml`: Project registry with enabled/disabled state
- SADP TaskSpec maps to ai-workflow-hub task format:
  - `TaskSpec.ID` ï¿½ï¿½ `tasks.yaml: id`
  - `TaskSpec.Risk` ï¿½ï¿½ `tasks.yaml: risk`
  - `TaskSpec.Goal` ï¿½ï¿½ `tasks.yaml: description`
  - `ExecutionReport.Status` ï¿½ï¿½ `tasks.yaml: status`

When a task completes, update `tasks.yaml` status in the project:
```yaml
- id: task-a1b2c3d4
  status: completed    # or failed, blocked
  last_run_id: run-[uuid]
```

### 4.2 test-frame (Evidence Collection)

TestFrame (`D:\test-frame`) provides evidence patterns:
- ExecutionReport.Evidence follows test-frame evidence provider contract
- Historical evidence (pre-existing test results) marked as `historical`
- Current evidence (this session) marked as `current, collected YYYY-MM-DD`
- GateResult: NEVER produced by sub-agent ï¿½ï¿½ reviewer decides

### 4.3 Capability Inventory

Every capability used in a task must appear in `capability-inventory.md` with `Status: approved`. The ExecutionReport.CapabilitiesUsed field enables automated capability audit (reviewer-playbook Step 8a).

---




### 4.6 Dispatch Model Selection (Decision Tree)

Before dispatching, consult [Dispatch Model Profiles](dispatch-model-profiles.md):

```
Task involves code files (.ps1/.py)?
  ï¿½ï¿½ï¿½ï¿½ Yes ï¿½ï¿½ Use deepseek-chat or execute directly (Codex)
  ï¿½ï¿½ï¿½ï¿½ No ï¿½ï¿½ Task involves .md files?
            ï¿½ï¿½ï¿½ï¿½ ï¿½ï¿½2 files ï¿½ï¿½ deepseek-v4-pro (fast, cheap)
            ï¿½ï¿½ï¿½ï¿½ 3-5 files ï¿½ï¿½ deepseek-chat (capable)
            ï¿½ï¿½ï¿½ï¿½ 6+ files ï¿½ï¿½ Codex direct (no tool timeout)
```

**Operational checks before dispatch:**
1. Close opencode desktop app (process conflict)
2. Keep prompt <500 chars
3. Target files <5KB each
4. Verify `opencode run "say ok"` returns quickly before real dispatch

**Failure fallback:** If dispatch times out twice, execute task directly as Codex goal agent and note in ExecutionReport.

### 4.7 Fallback Matrix

When a dispatch attempt fails, the agent MUST classify the failure type before applying fallback:

```
failure_classification:
  types: [api_key, cli_change, model_unavailable, timeout, unknown]
  rule: classify_before_fallback
  silent_fallback: forbidden  # applies to all risk levels
```

Fallback decisions MUST be recorded in ExecutionReport.

```yaml
fallback_policy:
  low_risk_docs:
    allowed_fallback: codex_direct
    require_audit: true
  medium_risk_code:
    allowed_fallback: backup_model_dry_run
    require_audit: true
    forbid: direct_write_without_review
  high_risk_architecture:
    allowed_fallback: pause_and_escalate
    require_audit: true
    forbid: auto_fallback, silent_fallback
  governance_modification:
    allowed_fallback: none
    require_audit: true
    forbid: any_auto_fallback
```

### 4.4 WorkQueue (Task Dispatch Queue)

Agent WorkQueue (`D:\agent-acceptance\agent-workqueue`) provides tier-graded task management:
- Tasks flow: WorkQueue.create ï¿½ï¿½ SADP dispatch ï¿½ï¿½ Claude Code execute ï¿½ï¿½ ExecutionReport ï¿½ï¿½ WorkQueue.complete
- Priority tiers: P0 (critical) ï¿½ï¿½ P1 (high) ï¿½ï¿½ P2 (normal) ï¿½ï¿½ P3 (low)
- Each task gets a WorkQueue ID that maps to TaskSpec.ID
- Dry-run mode: inspect queue without dispatch (Phase 0-5 authorized)

### 4.5 Scripts (Verification Runners)

PowerShell runners (`D:\agent-acceptance\scripts`) provide automated verification:
- Source inspection authorized (read script contents, understand what it does)
- Execution requires ScriptSafetyRecord + separate human gate
- Script paths documented in capability-inventory.md

## 5. Bootstrap Integration

When a project is bootstrapped with `bootstrap.ps1`, the generated AGENTS.md includes:

```markdown
## Default Development Process: Sub-Agent Dispatch

This project uses the [Sub-Agent Dispatch Protocol](docs/agent-runtime/sub-agent-dispatch-protocol.md).
The Codex goal agent plans and dispatches; the Claude Code agent executes and reports.

- All tasks dispatched via TaskSpec format (self-contained contract)
- All results returned via ExecutionReport format (evidence-backed)
- Capability usage tracked against capability-inventory.md
- Acceptance gates must pass before next dispatch
```

---

## 6. Phase 0-5 Constraints

- TaskSpec dispatch does NOT violate Phase 0-5 boundaries:
  - No package install unless explicitly authorized in Forbidden section (default: forbidden)
  - No git mutations unless explicitly authorized (default: no commit without human gate)
  - No capability use without inventory registration (core-007)
- ExecutionReport preserves audit trail for human review
- All evidence is verifiable: test commands with output, file paths with line counts

---

## 7. E2E Acceptance Test

To verify the protocol works end-to-end:

1. Codex goal agent creates a TaskSpec for a trivial task (e.g., "add a comment to README.md")
2. Claude Code agent receives, executes, returns ExecutionReport
3. Goal agent evaluates, marks complete

Expected: full cycle completes within one goal turn, all gates PASS.

---

> 
## 8. Phase Exit Authorization (2026-05-28)

Reviewer: RD. The following Phase 0-5 constraints are lifted for SADP operation:

| Capability | Previous | Now | Scope |
|------------|----------|-----|-------|
| dev-frame | design_only | adapter_dry_run | Read-only command inspection |
| test-frame | historical_only | current_evidence | Read evidence/reports/test-results |
| WorkQueue | read_only | dry_run_dispatch | Inspect tasks, no execution |
| Scripts | not_run | source_inspection | Read source, no execution |
| SADP | protocol_only | full_dispatch | TaskSpec ï¿½ï¿½ ExecutionReport cycle |

Test execution, package install, git mutations, and MCP changes remain forbidden without separate human gate.


**Version**: 1.0 | **Status**: approved | **Replaces**: ad-hoc goal-mode handoffs


### 4.7 Fallback Matrix

When SADP dispatch fails, agent must classify and route per risk level:

```yaml
fallback_policy:
  low_risk_docs:
    allowed_fallback: codex_direct
    require_audit: true
  medium_risk_code:
    allowed_fallback: backup_model_dry_run
    forbid: direct_write_without_review
    require_audit: true
  high_risk_architecture:
    allowed_fallback: pause_and_escalate
    forbid: auto_fallback, silent_fallback
    require_audit: true
  governance_modification:
    allowed_fallback: none
    forbid: any_auto_fallback
    require_audit: true
```

**Rules:**
1. Classify failure type (api_key_expired, cli_changed, model_unavailable, timeout, unknown) before choosing fallback.
2. Silent fallback is forbidden at all risk levels. Every fallback must be recorded in ExecutionReport.
3. Governance modification tasks (rules, protocols, AGENTS.md, CLAUDE.md) have zero allowed fallback ¡ª must escalate to human.
