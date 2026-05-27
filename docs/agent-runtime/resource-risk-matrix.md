# Resource Risk Matrix -- RD2100 Agent Runtime v2

> Batch R0-B, 2026-05-27
> Phase: R0 (Risk Classification Only -- no mitigation execution)
> Scope: All 13 risk categories across 8 registered resources

## Overview

This matrix classifies risks across all resource categories discovered in R0. It does not execute mitigations -- it informs which controls must be enforced and which gates must be passed before any resource becomes a runtime capability.

## Risk Matrix

---

### Risk Category 1: MCP (Blackboard)

| Field | Value |
|-------|-------|
| **risk_category** | MCP (Blackboard) |
| **affected_resources** | res-blackboard-mcp-001 |
| **risk_level** | critical |
| **primary_threat** | Unauthorized knowledge solidification (bb_solidify_knowledge) writes unvalidated knowledge into the shared Blackboard, poisoning cross-session intelligence. bb_event could trigger unexpected workflows. bb_claim_file / bb_release_file could disrupt concurrent sessions. |
| **current_control** | All mutating tools explicitly forbidden (bb_solidify_knowledge, bb_share_knowledge, bb_claim_file, bb_release_file, bb_acquire_build_lock, bb_release_build_lock, bb_event). Server.py not executed. MCP config not modified. |
| **control_gap** | bb_event tool existence not confirmed active. No runtime enforcement of forbidden tool list -- relies on agent discipline. |
| **forbidden_actions** | bb_solidify_knowledge, bb_share_knowledge, bb_claim_file, bb_release_file, bb_acquire_build_lock, bb_release_build_lock, bb_event, execute server.py, register MCP server, modify MCP config, write to blackboard state |
| **gate_decision** | If any forbidden Blackboard tool is invoked, the session is poisoned and must be audited. Knowledge solidification without validation can corrupt the shared knowledge base. Any detected violation requires human review before proceeding. |
| **next_phase_policy** | R1 elevates Blackboard to read-only snapshot mode. Snapshot state.json for evidence. Validate bb_* tool availability via contract mapping A3. bb_event tool status must be confirmed. Snapshot is read-only -- no write operations added. |

---

### Risk Category 2: Scripts (PowerShell runners)

| Field | Value |
|-------|-------|
| **risk_category** | Scripts (PowerShell runners) |
| **affected_resources** | res-agentacceptance-008 |
| **risk_level** | high |
| **primary_threat** | Untested PowerShell scripts in a dirty worktree (13M+6U) could mutate repository state, consume workqueues producing invalid dispatch evidence, or execute with stale configuration. Write-Report.ps1 could overwrite historical run records. |
| **current_control** | All 7 PowerShell scripts are forbidden from execution. Only source review and file-existence checks permitted. Workqueue JSON definitions can be read but not consumed. |
| **control_gap** | No dry-run has been performed. Script behavior is unverified in this runtime. Dirty baseline adds uncertainty about which script versions are canonical. |
| **forbidden_actions** | Execute Run-Smoke.ps1, Run-Batch.ps1, Run-WorkQueue.ps1, Run-AllQueues.ps1, Run-QueueGroup.ps1, Test-WorkQueue.ps1, Write-Report.ps1, consume workqueue (dispatch tasks), run any PowerShell script without explicit human approval |
| **gate_decision** | Any script execution before R7 violates the phase gate. Scripts must first be source-reviewed at R0, cataloged, then progressively tested through dry-run (R7). Premature execution risks corrupting evidence chains. |
| **next_phase_policy** | R7 introduces controlled execution with evidence collection. Dry-run WorkQueue processing only. Human-gated script execution. Each script must pass source review before dry-run. Run-Smoke.ps1 is first candidate. |

---

### Risk Category 3: Hooks (audit draft ps1)

| Field | Value |
|-------|-------|
| **risk_category** | Hooks (audit draft ps1) |
| **affected_resources** | res-agentacceptance-008 |
| **risk_level** | high |
| **primary_threat** | Hooks directory contains draft audit scripts (ps1). If auto-loaded, these could intercept git operations (commit, push) or inject behavior into the agent runtime before capability gates are passed. |
| **current_control** | hooks/ directory is untracked (dirty baseline, 6 untracked files include .claude/ and other infrastructure). No hook registration has occurred. Hooks are not loaded. |
| **control_gap** | hooks/ contents not inventoried in detail. Unknown hook scripts may exist. No hook policy enforcement -- relies on agent not loading them. |
| **forbidden_actions** | Register hooks, execute hook scripts, modify hook configuration, auto-load hooks on git events |
| **gate_decision** | Any hook registration before capability approval (R6-R7) is a bypass of promotion gates. Hooks at phase level are blind injections into the agent pipeline. |
| **next_phase_policy** | Hooks must be inventoried and source-reviewed (R5-R6 range). Any hook intended for production use must go through the full promotion gate chain. Hooks that modify git behavior (pre-commit, pre-push) require specific human approval. |

---

### Risk Category 4: Skills (local skills collection)

| Field | Value |
|-------|-------|
| **risk_category** | Skills (local skills collection) |
| **affected_resources** | res-localskills-005 |
| **risk_level** | high |
| **primary_threat** | Skills are executable code loaded at session start. skill-installer can install arbitrary skills from GitHub. skill-auto-evolve can mutate existing skills. skill-creator can generate new skills. Uncontrolled skill loading is a code execution vector. |
| **current_control** | All skill mutation/installation tools forbidden (skill-installer, skill-creator, skill-evolver, skill-auto-evolve, skill-share, connect-apps, setup-pre-commit, update-config). Only reference (names, triggers, risk classifications) permitted. No auto-load. |
| **control_gap** | Physical ~/.claude/skills/ directory not scanned for unknown installations. Skill manifest derived from system prompt, not from filesystem audit. Skills loaded by the system at session start are outside agent control. |
| **forbidden_actions** | Execute skill-installer, skill-creator, skill-evolver, skill-auto-evolve, skill-share, connect-apps, setup-pre-commit, update-config, auto-load any skill, execute external skill code |
| **gate_decision** | Any skill installation or mutation at R0 is a capability bypass. Skill code execution before evaluation (R5) can inject behavior into the runtime. |
| **next_phase_policy** | R5 evaluates skills-inbox/ and produces SkillIntakeRecords. No installation until intake evaluation is complete. Skill intake requires human approval. Skill auto-evolve remains forbidden until capability_approved lifecycle state. |

---

### Risk Category 5: Memory (RD2100 + project-local)

| Field | Value |
|-------|-------|
| **risk_category** | Memory (RD2100 + project-local) |
| **affected_resources** | res-rd2100memory-006 |
| **risk_level** | high |
| **primary_threat** | Write operations to RD2100 memory (MEMORY.md, ACTIVE.md, memory/*.md, agent-state.db) could corrupt the long-term memory store. bb_solidify_knowledge could poison the shared knowledge base. recursive-improve and dream-reflection could auto-mutate agent behavior rules without human review. |
| **current_control** | All memory write operations forbidden. Only read access permitted: MEMORY.md index, memory/*.md files (no secrets), ACTIVE.md, MEMORY-CALL-GUIDE.md. agent-state.db read-only if accessible. |
| **control_gap** | agent-state.db not accessible for verification. Project-local memory (D--agent-acceptance) is empty -- no project-specific memory exists. Global memory is read-only but physical write protection is not enforced at filesystem level. |
| **forbidden_actions** | Write memory/*.md, write MEMORY.md, write ACTIVE.md, write agent-state.db, bb_solidify_knowledge, execute recursive-improve, execute dream-reflection, execute memory-bridge write operations |
| **gate_decision** | Any memory write at R0 is irreversible corruption of the evidence base. Memory writes require R6 gates (MemoryUpdateRecords proposed only, human-approved). |
| **next_phase_policy** | R6 maps memory system layers (file, structured, collaborative). Produces MemoryUpdateRecords (proposed only -- no writes). Validates memory architecture. No memory writes until capability_approved lifecycle state. |

---

### Risk Category 6: CodeGraph (code intelligence)

| Field | Value |
|-------|-------|
| **risk_category** | CodeGraph (code intelligence) |
| **affected_resources** | res-codegraph-004 |
| **risk_level** | high |
| **primary_threat** | Reindex or rebuild index could corrupt existing codegraph.db files across three projects (particularly dev-frame at 13.5MB/410 files and test-frame at 1.8MB/102 files). agent-acceptance index is empty (0 files), making it a low-risk candidate for reindex, but no reindex is permitted at R0. |
| **current_control** | All CodeGraph write operations forbidden (reindex, init new index, delete index, modify codegraph.db, rebuild index). Only read operations permitted (codegraph_status, codegraph_search, codegraph_context, etc.). |
| **control_gap** | agent-acceptance index is stale (0 files indexed despite .codegraph/codegraph.db existing at 139KB). sqlite3 not available for direct query to verify DB integrity. Stale index detection not implemented -- relies on human noticing. |
| **forbidden_actions** | Reindex, init new index, delete index, modify codegraph.db, rebuild index |
| **gate_decision** | Reindexing any project at R0 before stale-aware policy (R4) risks overwriting active indexes. Index modification is a database write that cannot be undone without backup. |
| **next_phase_policy** | R4 implements stale index detection. Automatic reindex trigger policy (human-gated). Contract mapping A2 verified with freshness checks. Reindex is only permitted when index age exceeds threshold AND human approves. |

---

### Risk Category 7: WorkQueue (task dispatch)

| Field | Value |
|-------|-------|
| **risk_category** | WorkQueue (task dispatch) |
| **affected_resources** | res-agentacceptance-008 |
| **risk_level** | high |
| **primary_threat** | Consuming workqueue JSONs (dispatch tasks) before scripts are verified could execute unvalidated task definitions with unapproved PowerShell scripts. The workqueue contains 5 tier-graded queue definitions designed for automated dispatch -- premature consumption bypasses all promotion gates. |
| **current_control** | WorkQueue JSON definitions can be read (source review) but not consumed. No task dispatch permitted. Scripts that consume workqueues (Run-WorkQueue.ps1, Run-AllQueues.ps1, Run-QueueGroup.ps1) are forbidden from execution. |
| **control_gap** | No dry-run of workqueue processing has been performed. Queue definitions exist but their structural validity (against queue schema) has not been verified. Dirty baseline (5 modified queue JSONs) means workqueue state may not reflect canonical definitions. |
| **forbidden_actions** | Consume workqueue (dispatch tasks), execute Run-WorkQueue.ps1, execute Run-AllQueues.ps1, execute Run-QueueGroup.ps1 |
| **gate_decision** | Consuming a workqueue at R0 dispatches tasks without capability gates. This is equivalent to running unapproved scripts with unapproved orchestration. |
| **next_phase_policy** | R7 introduces dry-run WorkQueue processing with evidence collection. Queue structural validation occurs before any dispatch. Only human-gated execution permitted. Queue definitions must be verified against schema before dry-run. |

---

### Risk Category 8: Templates (AGENTS, queue templates)

| Field | Value |
|-------|-------|
| **risk_category** | Templates (AGENTS, queue templates) |
| **affected_resources** | res-agentacceptance-008 |
| **risk_level** | medium |
| **primary_threat** | Modifying templates could change the structural contract for AGENTS.md and queue definitions, leading to downstream consumers (agents, scripts) operating on invalid or unexpected input shapes. Templates are untracked (new in dirty baseline) and their structural validity is unverified. |
| **current_control** | Templates can be read but not modified. No template-based generation is performed. templates/ directory is untracked -- modifications would be local only. |
| **control_gap** | Template structural validity not verified against schemas. Templates are new additions (dirty baseline) and may not be final versions. No schema validation has been run. |
| **forbidden_actions** | Modify templates, generate from templates without validation |
| **gate_decision** | Modifying templates before schema validation (R5-R7) could propagate invalid contracts. Template changes must be validated against their target schemas. |
| **next_phase_policy** | Templates must be validated against queue JSON schema and AGENTS.md specification (R5-R7 range). Any template modification requires human approval. Templates stay read-only until capability_approved lifecycle state for the affected resource. |

---

### Risk Category 9: Historical Runs (runs/ directory)

| Field | Value |
|-------|-------|
| **risk_category** | Historical Runs (runs/ directory) |
| **affected_resources** | res-agentacceptance-008 |
| **risk_level** | medium |
| **primary_threat** | Treating historical run records as current evidence could lead to decisions based on stale data. Historical runs reflect a prior session state, not the current dirty baseline (13M+6U). Run record timestamps may not match the current runtime clock. |
| **current_control** | Historical runs are explicitly identified as historical -- not treated as current. No run record modification permitted. runs/ directory is read-only. |
| **control_gap** | Run record freshness not systematically verified. No timestamp validation against current session. No mechanism to mark runs as superseded. |
| **forbidden_actions** | Treat historical runs as current, modify historical run records, delete run records |
| **gate_decision** | Using historical runs as current evidence produces false verification signals. Any capability decision based on stale run data must be rejected. |
| **next_phase_policy** | R7 introduces current-run evidence collection. Fresh runs are produced under controlled conditions with timestamp verification. Historical runs are archived, not consumed. Run freshness is validated against session start time. |

---

### Risk Category 10: Evidence Providers (test-frame)

| Field | Value |
|-------|-------|
| **risk_category** | Evidence Providers (test-frame) |
| **affected_resources** | res-testframe-003 |
| **risk_level** | high |
| **primary_threat** | test-frame contains full test execution capability (orchestrator, aggregator, attribution, CLI) targeting external systems (Android apps, WeChat MiniPrograms, H5 pages, backend APIs). Accidental test execution could trigger real API calls, cloud device provisioning, or crash monitoring alerts. Reports directory contains historical data -- using it as current evidence without re-execution produces false signals. |
| **current_control** | All test execution tools forbidden (orchestrator, aggregator, attribution, CLI, pytest, npm test, playwright). Only read-only access permitted: directory structure, documentation (README, ARCHITECTURE, PIPELINE), git status, JSON fixture validation. |
| **control_gap** | No test execution has been performed in this runtime. Reports directory contains historical data only. test-frame has not been connected as an evidence provider -- its discoverer has not been run. |
| **forbidden_actions** | Execute orchestrator, aggregator, attribution, CLI, run pytest, run npm test, execute playwright tests, execute any test runner, modify test results, modify reports |
| **gate_decision** | Any test execution at R0 contacts external systems without capability gates. This could trigger real alerts (Sentry, Bugly), consume cloud device quota (WeTest), or send traffic to live APIs. |
| **next_phase_policy** | R2 runs discoverer to identify test suites and produce evidence index records. No test execution -- discovery is read-only. Evidence provider integration requires full gate chain (R2 through R6). Test execution is only permitted after capability_approved lifecycle state. |

---

### Risk Category 11: UI Automation (computer-use MCP)

| Field | Value |
|-------|-------|
| **risk_category** | UI Automation (computer-use MCP) |
| **affected_resources** | res-agentacceptance-008 (indirect -- if computer-use tools interact with scripts) |
| **risk_level** | critical |
| **primary_threat** | computer-use MCP tools (screenshot, left_click, type, key, mouse_move, open_application) can interact with the host desktop. Combined with unapproved script execution, this creates a full UI automation surface that could manipulate running applications, read sensitive screen content, or inject keystrokes into other processes. |
| **current_control** | computer-use MCP tools are available in the deferred tool manifest but not activated for resource operations. All resource access is read-only. Script execution is forbidden. No UI automation has been used against any registered resource. |
| **control_gap** | computer-use tools exist in the deferred tool manifest and could be invoked. No explicit gate prevents computer-use + script execution chaining. No screen content audit trail exists. |
| **forbidden_actions** | Use computer-use tools (screenshot, click, type, key, mouse, open_application) against registered resources, chain computer-use with resource operations |
| **gate_decision** | UI automation combined with resource access is a desktop-level escalation. Any detected chaining of computer-use + resource execution requires immediate session audit. |
| **next_phase_policy** | Computer-use tools remain outside the resource promotion chain. They are only permitted when explicitly requested by human reviewer. No automated UI interaction with registered resources is ever permitted in any phase. |

---

### Risk Category 12: Package Managers (npm, pip, yarn)

| Field | Value |
|-------|-------|
| **risk_category** | Package Managers (npm, pip, yarn) |
| **affected_resources** | res-devframe-002, res-testframe-003, res-agentacceptance-008 |
| **risk_level** | high |
| **primary_threat** | npm install, pip install, or yarn install could modify project dependencies, pull unapproved packages, or trigger postinstall scripts that execute arbitrary code. Package installation changes the runtime environment without going through any promotion gate. |
| **current_control** | npm install and pip install are explicitly forbidden for dev-frame. Package manager usage is not permitted at R0. Python environment and Node.js environment are assumed pre-existing but not modified. |
| **control_gap** | No lockfile audit has been performed (package-lock.json, yarn.lock, requirements.txt state unknown). No dependency vulnerability scan exists. Package manager availability is not gated -- they exist on the system PATH. |
| **forbidden_actions** | npm install, pip install, yarn install, modify package.json, modify requirements.txt, run postinstall scripts |
| **gate_decision** | Package installation at R0 is an unapproved environment mutation. Any package installed without gate review becomes part of the runtime without capability validation. |
| **next_phase_policy** | Package managers remain forbidden through R7 unless explicitly approved for a specific phase gate. Dependency audit is required before any installation. Lockfile integrity must be verified. Package installation requires human approval and is only permitted for resources at capability_approved lifecycle state. |

---

### Risk Category 13: External Sources (GitHub repos)

| Field | Value |
|-------|-------|
| **risk_category** | External Sources (GitHub repos) |
| **affected_resources** | res-devframe-002 (ai-workflow-hub, ai-workflow-hub-e2e, codegraph sub-repos), res-agentacceptance-008 (remote: RD2100/agent-acceptance) |
| **risk_level** | medium |
| **primary_threat** | Git fetch/pull from external remotes could introduce unapproved code changes from upstream. ai-workflow-hub and ai-workflow-hub-e2e are independent repos inside dev-frame -- their upstream state is unverified. agent-acceptance secondary clone uses SSH remote (different auth method) -- pushing to it could create remote divergence. |
| **current_control** | Git operations limited to read-only: git_status, git_log. No fetch, pull, push, commit, or remote modification permitted. Secondary clone (D:\dev-frame\agent-acceptance) is acknowledged but not operated on. |
| **control_gap** | Upstream state of sub-repos (ai-workflow-hub, ai-workflow-hub-e2e, codegraph) is not compared against local state. No freshness check for remotes. SSH remote for secondary clone is not verified as accessible. |
| **forbidden_actions** | Git fetch, git pull, git push, git commit (to dev-frame sub-repos), modify remotes, merge upstream changes |
| **gate_decision** | Pulling from external remotes introduces code changes without any promotion gate. Pushing to remotes publishes unapproved state. Any remote interaction before capability gates is a source-of-truth bypass. |
| **next_phase_policy** | Git operations remain read-only through R7. Remote interaction (fetch, pull) requires human approval and is only permitted for resources at capability_approved lifecycle state with explicit reviewer authorization. Push is never automated -- always human-gated. |

---

## Risk Summary Matrix

| # | Risk Category | Affected Resources | Risk Level | Primary Threat Class | Gate Severity |
|---|---------------|-------------------|------------|---------------------|---------------|
| 1 | MCP (Blackboard) | res-blackboard-mcp-001 | critical | Knowledge poisoning, session disruption | Session audit required |
| 2 | Scripts (PowerShell) | res-agentacceptance-008 | high | Unvalidated code execution, evidence corruption | Phase gate violation |
| 3 | Hooks (audit ps1) | res-agentacceptance-008 | high | Blind pipeline injection, git interception | Capability bypass |
| 4 | Skills (local) | res-localskills-005 | high | Arbitrary code execution, mutation | Capability bypass |
| 5 | Memory (RD2100) | res-rd2100memory-006 | high | Memory store corruption, knowledge poisoning | Irreversible corruption |
| 6 | CodeGraph | res-codegraph-004 | high | Index corruption (3 DBs) | Data loss |
| 7 | WorkQueue | res-agentacceptance-008 | high | Unapproved task dispatch | Capability bypass |
| 8 | Templates | res-agentacceptance-008 | medium | Invalid contract propagation | Contract corruption |
| 9 | Historical Runs | res-agentacceptance-008 | medium | Stale evidence, false verification | False signal |
| 10 | Evidence Providers | res-testframe-003 | high | External system contact, false evidence | External impact |
| 11 | UI Automation | res-agentacceptance-008 (indirect) | critical | Desktop-level escalation, screen reading | Session audit required |
| 12 | Package Managers | res-devframe-002, res-testframe-003, res-agentacceptance-008 | high | Unapproved dependency mutation, postinstall code exec | Environment mutation |
| 13 | External Sources | res-devframe-002, res-agentacceptance-008 | medium | Upstream code injection, remote divergence | Source-of-truth bypass |

## Critical/High Risk Enforcement

All 2 critical-risk categories and 10 high-risk categories require:

1. **Human gate**: Any capability progression requires explicit human reviewer approval
2. **Gate chain**: No resource may skip promotion gates (1-6) to reach capability
3. **Forbidden action list**: Explicitly enumerated and enforced per resource
4. **Evidence requirements**: Must be satisfied before next phase transition

## Phase Transition Policy

| Current Phase | Permitted Operations | Gate Type |
|---------------|---------------------|-----------|
| R0 (current) | Register, classify, assess risk | No execution, no enablement |
| R1 | Snapshot Blackboard state | Read-only, human-gated |
| R2 | Discover test-frame suites | Read-only, no execution |
| R3 | Draft orchestration adapter | Dry-run candidate, human-gated |
| R4 | Stale index detection | Read-only check, human-gated reindex |
| R5 | Skill/Rules intake evaluation | Reference only, no installation |
| R6 | Memory context map | Proposed records only, no writes |
| R7 | Controlled script/dry-run | Human-gated execution with evidence |

## Verification

- [x] All 13 risk categories covered with required fields
- [x] Each category has: risk_category, affected_resources, risk_level, primary_threat, current_control, control_gap, forbidden_actions, gate_decision, next_phase_policy
- [x] Critical risk categories (MCP, UI Automation) identified with session-level audit severity
- [x] No mitigation actions executed at R0 -- classification only
- [x] Consistent with resource-registry.md forbidden_actions lists
- [x] Phase transition policy aligns with resource-integration-plan.md gates 1-6
