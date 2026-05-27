# FMEA Risk Analysis -- RD2100 Agent Runtime v2

> Batch D5, 2026-05-27
> Scope: Bootstrap Phase 0-5 constraints
> Methodology: FMEA (Failure Mode and Effects Analysis) per AIAG-VDA FMEA Handbook

## Overview

This FMEA analyzes failure modes in the RD2100 Agent Runtime v2 bootstrap phase (Phase 0-5). The analysis covers the execution framework, tool policy enforcement, memory protection, skill intake, integration contracts, and human reviewer workflows.

**RPN Legend**: S = Severity, O = Occurrence, D = Detection, RPN = S x O x D
**Thresholds**: High RPN >= 200, Medium 100-199, Low < 100

---

## Sorting Strategy

Entries are sorted by RPN descending within each risk tier. Ties are broken by Severity (highest first), then Occurrence, then Detection.

---

## FMEA Table

| # | Failure Mode | Cause | Effect | S | O | D | RPN | Preventive Control | Detective Control | Owner | Phase |
|---|-------------|-------|--------|---|---|---|---|-------------------|-------------------|-------|-------|
| 1 | Agent executes forbidden tool (skill-installer, update-config, bb_solidify_knowledge) | Prompt injection overrides tool-policy.md; AGENTS.md constraint bypassed; multi-step jailbreak | Critical: agent installs untrusted skill that registers MCP hooks, exfiltrates secrets, or mutates global config permanently | 10 | 5 | 9 | **450** | Tool policy documented in tool-policy.md; forbidden skills listed with rationale in skill-trigger-matrix.md; Phase 0-5 hard-boundary constraints in CLAUDE.md | Human reviewer must compare ExecutionReport actions against tool-policy.md; Blackboard audit trail (bb_share_decision) for state changes; PRE/POST git diff comparison | Human Reviewer + Runtime Architect | Phase 0-5 |
| 2 | Agent modifies dirty baseline (file system mutation of README.md, scripts/, agent-workqueue/, .claude/, .codegraph/) | Agent ignores Hard Boundaries; agent confuses approved output paths with baseline paths; missing constraint enforcement in prompt | Working state corrupted; commits contaminated; reviewer cannot trust delta; rollback requires git restores that agent itself cannot do | 10 | 6 | 7 | **420** | Hard Boundaries explicitly listed in batch task prompt; approved output paths enumerated; dry-run default for all runners | git status --short PRE vs POST comparison; git diff verification before report submission; human reviewer gate check on file changes | Human Reviewer + Executor Agent | Phase 0-5 |
| 3 | Agent reports fake green (exit code 0 when actual result is FAILED or BLOCKED) | Agent fabricates verification results to appear successful; agent omits failing checks from report; agent misrepresents dry-run as real execution | Reviewer approves broken release; undetected security/config issues propagate to production; trust in agent reporting collapses | 10 | 5 | 8 | **400** | Exit code contract: 0=PASS, 1=BLOCKED, 2=FAILED; no-fake-green rule in operating-model.md; tier escalation with human gate at Tier 2 | Cross-reference all gate_results in ExecutionReport against actual git status; compare reported exit codes against raw command output; reviewer spot-checks evidence artifacts | Human Reviewer | All phases |
| 4 | Reviewer fails to detect agent violation (false-negative gate check) | Reviewer fatigue/distraction; report too large or verbose obscures violations; reviewer does not cross-reference all contract fields; time pressure causes skipped checks | Agent violations go undetected; forbidden tool execution accepted; fake green approved; baseline mutations committed | 10 | 6 | 6 | **360** | Structured ExecutionReport template with mandatory sections; clear gate_result fields with pass/fail/blocked; reviewer checklist (P0 mandatory, P1 recommended, P2-P3 advisory) | Second-reviewer protocol (planning agent validates execution agent report); Blackboard anomaly detection (bb_validate_knowledge); audit trail completeness check | Human Reviewer + Planning Agent | All phases |
| 5 | Agent self-approves (agent marks its own WorkDone or sets ExecutionReport status to accepted) | Agent invokes TaskComplete/TaskUpdate with success status regardless of actual outcome; agent writes ExecutionReport with status="accepted" bypassing human reviewer | All gate checks bypassed; no human oversight; agent becomes self-certifying; governance framework nullified | 10 | 4 | 8 | **320** | ExecutionReport status transitions only by human: proposed->submitted (agent), reviewed->accepted/rejected (human); TaskSpec status must be verified by human reviewer | ExecutionReport.status audit: check that status transition from "submitted" to "reviewed" requires human action; compare report timestamp vs reviewer activity timestamp | Human Reviewer + Runtime Policy | Phase 0-5 |
| 6 | Agent clones external repository | Agent executes `git clone` or `git fetch` against untrusted remote; agent uses `git submodule add`; CodeGraph MCP triggers automatic fetch | Untrusted code enters workspace; supply chain attack vector; Phase 0-5 quarantine bypassed; external dependencies introduced without review | 10 | 4 | 7 | **280** | git clone shadow-banned in tool-policy.md Phase 0-5 FORBIDDEN; skill-intake pipeline defers all external code to Phase 6; external-skill-intake.md explicitly forbids cloning | .git/config or new .gitmodules detected by git status; unexpected directories appearing in PRE/POST file listing; Blackboard audit of network activity | Human Reviewer + Runtime Architect | Phase 0-5 |
| 7 | Agent installs packages (npm/pip/yarn) | Agent executes npm install/pip install despite Phase 0-5 prohibition; prompt injection convinces agent it is in Phase 6+; agent invokes external skill that triggers install | Dependencies mutated; supply chain risk; project environment polluted; local global state changed; future builds behave differently | 10 | 5 | 5 | **250** | Package managers listed in FORBIDDEN section of tool-policy.md with explicit examples; Phase read-only policy documented in memory-architecture.md | node_modules/, __pycache__/, Pipfile, package.json changes detected by git status; new binary artifacts in PRE/POST comparison; disk usage change | Human Reviewer + Runtime Architect | Phase 0-5 |
| 8 | Agent registers hooks (git hooks, husky, lint-staged, Claude Code harness hooks) | Agent executes `git config core.hooksPath`, `npx husky install`, `npx mrm lint-staged`; agent modifies settings.json harness hooks; agent creates .git/hooks/ scripts | Pre-commit/pre-push hooks intercept all git operations; malicious hook exfiltrates on every commit; hook masking of unauthorized changes; persistent behavioral modification | 10 | 3 | 6 | **180** | Hook registration shadow-banned in tool-policy.md FORBIDDEN; setup-pre-commit skill classified as Deferred in skill-trigger-matrix.md; git-guardrails skill deferred | .git/hooks/ directory content check; `git config --list` for core.hooksPath; settings.json diff; hooksPath check in .git/config | Human Reviewer | Phase 0-5 |
| 9 | Agent modifies MCP configuration (settings.json, .cursor/mcp.json, .claude/mcp/ entries) | Agent invokes update-config skill despite being Forbidden; agent writes directly to MCP config file paths; agent invokes Edit tool on MCP config JSON | New MCP servers connected without review; unauthorized tools become available to agent; agent expands its own capability surface silently; persistence across sessions | 10 | 3 | 6 | **180** | update-config skill classified as Forbidden in skill-trigger-matrix.md; MCP config mutation listed in FORBIDDEN category of tool-policy.md | MCP config file checksum comparison PRE/POST; diff of .claude/settings.json and .cursor/mcp.json; Blackboard anomaly alert for unexpected tool additions | Human Reviewer + Runtime Architect | Phase 0-5 |
| 10 | Agent calls bb_solidify_knowledge (permanent Blackboard write) | Agent ignores Phase 0-5 write restriction; agent transitions memory from proposed to solidified without human approval; agent invokes forbidden skill that triggers solidify | False or unverified knowledge permanently published to Blackboard; subsequent agents receive corrupted knowledge base; cross-session contamination; reviewer decision bypassed | 9 | 4 | 5 | **180** | bb_solidify_knowledge explicitly FORBIDDEN in memory-architecture.md and tool-policy.md; MemoryUpdateRecord protocol requires human approval before write | Blackboard audit log showing solidify calls; cross-reference SolidifyKnowledge events against approved MemoryUpdateRecords; anomaly if solidify count > 0 in Phase 0-5 | Human Reviewer + Blackboard Admin | Phase 0-5 |
| 11 | Gate bypass (agent skips P0 verification gate and proceeds to next task) | Agent claims gate was "skipped" due to time constraints; agent fabricates GateResult with "pass" without actual check; agent reuses old GateResult from prior batch | Critical P0 issues (security, data loss, secrets leak) pass through undetected; chain of trust broken; release pipeline accepts unsafe artifacts | 10 | 3 | 5 | **150** | Gate-level classification: P0=blocking, P1=warning, P2=advisory, P3=informational; P0 gate fail/blocked must escalate per operating-model.md; ExecutionReport includes all GateResults | Cross-reference GateResult.gate_level against gate_sequence; verify P0 gates listed before P1/P2/P3; check that SKIPPED P0 has explicit human justification | Human Reviewer + Planning Agent | Phase 0-5 |
| 12 | Agent writes outside approved scope (approves own file paths beyond explicit allowlist) | Agent misinterprets "approved scope" boundary; agent creates files under unlisted subdirectories; path traversal attack through crafted file names (../../ etc.) | Files written to memory/, .claude/rules/, .codegraph/, or system directories; baseline contamination; configuration corruption; privilege boundary crossed | 9 | 4 | 4 | **144** | Approved output paths explicitly enumerated in batch task prompt; Write/Edit tool should validate target path against allowlist; dry-run default requiring -Real flag | PRE/POST git status --short diff catches unexpected file additions; path prefix validation against approved output path list; Blackboard anomaly alert | Human Reviewer + Executor Agent | Phase 0-5 |
| 13 | Agent reads secrets (.env, *.key, *.pem, tokens, credentials) | Agent invokes Read tool on secret-bearing files; glob-based search for credential patterns; agent uses Grep for "API_KEY", "SECRET", "TOKEN" across codebase | Credentials exfiltrated into conversation context; secrets appear in ExecutionReport or Blackboard; PII/credential leak; supply chain compromise vector | 9 | 5 | 3 | **135** | Read tool constrained: cannot read .env, *.key, *.pem, tokens in tool-policy.md; Hard Boundaries explicitly state "Do NOT read secrets"; file extension blocklist | Partial: only if reviewer compares Read tool calls against known secret file paths; Blackboard log of read operations; low detection because Read tool does not self-report what it reads | Human Reviewer + Agent Runtime | Phase 0-5 |
| 14 | Agent executes dangerous git (reset --hard, clean -f, push --force, stash, commit) | Agent invokes Bash with destructive git command; agent mistakes "clean up workspace" for git clean; agent pushes to protected branch | Irrecoverable data loss (working tree destroyed); force push overwrites remote history; unauthorized commits contaminate baseline; reviewer cannot verify original state | 9 | 3 | 5 | **135** | Dangerous git commands explicitly FORBIDDEN in tool-policy.md; git-guardrails skill deferred to Phase 6+; no auto-commit policy | git reflog shows destructive operations; remote push audit log; PRE/POST commit SHA comparison; Bash command history audit | Human Reviewer + Runtime Architect | Phase 0-5 |
| 15 | Schema validation bypassed (contract JSON produced without structural validation) | Agent writes contract JSON manually without schema checker; agent omits required fields to save tokens; agent uses wrong enum values that reviewer does not catch | Invalid contract data propagated downstream; future parsing failures; type mismatches cause tool errors; traceability lost when task_id/report_id format inconsistent | 8 | 6 | 4 | **192** | 8 core contracts defined in integration-contracts.md with required fields and validation rules; enum constraints documented per contract | Schema validation at reviewer gate (manual or automated); field-level spot check against contract spec; required field existence check | Human Reviewer + Validation Tooling | Phase 0-5 |
| 16 | ExecutionReport missing required sections (summary, status, gate_results, evidence references) | Agent generates truncated report under context pressure; agent omits sections it cannot fill (no evidence); agent claims "see above" instead of structured fields | Reviewer cannot assess completeness; missing gate_results hides violations; incomplete audit trail; report fails downstream processing | 8 | 5 | 4 | **160** | ExecutionReport contract (Contract 5) defines required fields: report_id, batch_id, generated_at, status, summary; structured template provided | Section existence check before submission; mandatory field count comparison against contract spec; reviewer checklist includes "all sections present?" | Human Reviewer + Executor Agent | Phase 0-5 |
| 17 | Path drift causes wrong file write (agent resolves path to wrong canonical root) | $CANONICAL_ROOT resolution error; environment variable conflict between devFrame and dev-frame; agent uses relative path from wrong CWD | Files written to wrong project directory (D:\devFrame instead of D:\dev-frame); outputs invisible to reviewer; production configs corrupted in sibling project | 8 | 4 | 5 | **160** | Canonical root D:\agent-acceptance\ hardcoded in operating-model.md; absolute paths required in batch task; $env:CANONICAL_ROOT environment variable | PRE/POST git status on both projects; path prefix validation against expected root; cross-reference file creation location vs task-approved paths | Human Reviewer + Executor Agent | Phase 0-5 |
| 18 | MemoryUpdateRecord written without approval (agent bypasses proposed-only protocol and writes to memory/*.md or agent-state.db) | Agent invokes Write on memory file despite constraint; agent believes "record proposed" means "write immediately"; agent misinterprets "save for later" as current-phase action | Corrupted memory files; false knowledge persisted; agent-state.db polluted with unapproved entries; future agents load bad memories; reviewer loses sole authority over memory | 8 | 4 | 4 | **128** | MemoryUpdateRecord protocol (Contract 8) enforces proposed-only in Phase 0-5; memory-architecture.md lists forbidden write operations; status enum constrains to "proposed" | PRE/POST diff of memory/*.md directory; agent-state.db schema change detection; SQLite journal check for unexpected writes; file modification timestamp audit | Human Reviewer + Memory Admin | Phase 0-5 |
| 19 | Agent installs skill via skill-installer or direct skill file placement | Agent invokes skill-installer despite Forbidden classification; agent clones GitHub skill repo into installed skills dir; agent copies skill files into ~/.claude/skills/ | Unreviewed skill code executes in every session; persistent agent behavior modification; P0 risk: skill can define auto-triggers, modify MCP, register hooks | 10 | 2 | 7 | **140** | skill-installer classified as Forbidden in skill-trigger-matrix.md; external-skill-intake.md pipeline defers all installs to Phase 6+; no Phase 0-5 install allowed | ~/.claude/skills/ directory monitoring; new skill directory detection; git status on skills-inbox/external/; Blackboard audit for InstallSkill events | Human Reviewer + Skill Admin | Phase 0-5 |
| 20 | PRE/POST git status mismatch (files changed between start and end of agent execution without report) | Agent makes side-effect writes not in ExecutionReport; agent triggers implicit file saves (IDE, editor); background process modifies file during execution; agent uses Write without including in report | Hidden mutations that reviewer cannot see; trust broken between agent and reviewer; mismatched state between PRE and POST snapshots | 7 | 5 | 4 | **140** | Explicit PRE-status capture before any writes; agent instructed to list all file changes in report; dry-run default preventing unintended writes | git status --short PRE vs POST diff; git diff --stat comparison; unreported delta detection using file count difference | Human Reviewer + Executor Agent | All phases |
| 21 | CodeGraph returns stale data (index out of sync with actual codebase) | CodeGraph MCP server not re-indexed after code changes; agent workspace changes not propagated to codegraph index; index corruption or partial index error | Agent makes decisions on stale symbol information; caller/callee graphs incomplete; impact analysis misses critical dependencies; false confidence in code understanding | 7 | 5 | 4 | **140** | codegraph_status check before critical queries; codegraph_files verification before accepting results; use codegraph_context with fresh bounds | Cross-reference codegraph search results against Grep results on actual files; verify symbol existence with Read tool; stale index detected by mismatch count | Agent + CodeGraph Admin | Phase 0-5 |
| 22 | Blackboard unavailable (bb_* MCP tools timeout or return errors) | Blackboard MCP server down; network partition between agent and Blackboard; Blackboard state.json corrupted; auth token expired | Session cannot register (bb_register fails); decisions not logged; bug patterns not shared; cross-session knowledge lost; audit trail incomplete for this session | 6 | 4 | 5 | **120** | Blackboard status check (bb_status) at session start; graceful degradation: agent continues without Blackboard but marks ExecutionReport with "Blackboard unavailable" note | bb_heartbeat periodic check detects mid-session drops; ExecutionReport includes Blackboard availability status; reviewer notified of missing audit entries | Agent + Blackboard Admin | Phase 0-5 |
| 23 | Session boundary violated (agent actions from one session leak into another) | Agent reads previous session state without re-registering; agent continues task from prior session without fresh bb_register; shared workspace state not cleaned between sessions | Stale context pollutes new session; authorization from old session assumed valid; Blackboard state conflated between sessions; duplicate task execution | 7 | 4 | 4 | **112** | bb_register required at every session start per operating-model.md; session_id must be unique; task dispatch must verify session registration | Blackboard session log shows registration gaps; task_id prefix includes session timestamp; reviewer checks that tasks reference correct session | Human Reviewer + Agent Runtime | Phase 0-5 |
| 24 | Phase boundary violated (agent applies Phase 6+ policy during Phase 0-5 bootstrap) | Agent reads future-phase sections in documents and enforces them; agent misunderstands "reference only" as "active"; AGENTS.md stale links reference phase 6 tools | Agent attempts Phase 6 write operations prematurely; memory files modified before approval; external skills installed before quarantine; confusion about which rules are active | 8 | 3 | 4 | **96** | Phase-split documentation: "ACTIVE" vs "REFERENCE ONLY" sections clearly marked; memory-architecture.md explicitly labels "Future Phase -- NOT ACTIVE"; skill-trigger-matrix classification system | Reviewer checks agent tool calls against active phase policy list; cross-reference actions with Phase 0-5 permitted tools; anomalous tool call detection | Human Reviewer + Runtime Architect | Phase 0-5 |
| 25 | AGENTS.md becomes stale (links broken, references to non-existent files) | Agent modifies AGENTS.md to add new rules but does not update linked documents; file rename/move breaks AGENTS.md anchors; external document URLs rot | Agent follows broken links to wrong or empty files; governance rules become unreachable; agent operates under incomplete constraints | 6 | 5 | 3 | **90** | AGENTS.md treated as read-mostly during bootstrap; link validation documented in docs quality gate; claude-md-docs skill recommended for doc maintenance | Broken link detection via Read attempts on AGENTS.md links; head request for external URLs; reviewer manually validates key references during gate check | Doc Maintainer | Phase 0-5 |
| 26 | Skill intake pipeline bypassed (skill used without SkillIntakeRecord) | Agent invokes skill directly without recording in intake pipeline; agent discovers skill in system prompt and uses it without classification; agent assumes skill is safe because it is listed | Unclassified skill executed without risk review; no SkillIntakeRecord created; no ToolRiskRecord assessment; audit trail broken; reviewer unaware of skill usage | 8 | 3 | 3 | **72** | External skills require SkillIntakeRecord (Contract 6) before use; pipeline stages: Discovery -> Record -> Classify -> Risk Review -> Defer; skill-trigger-matrix provides pre-classification | Audit of Skill tool calls vs SkillIntakeRecord list; discrepancy between skills used and skills recorded; Blackboard log of unknown skill invocations | Human Reviewer + Skill Admin | Phase 0-5 |
| 27 | PowerShell hook accidentally registered (agent or skill sets up CC harness hooks) | Agent uses Bash to write to settings.json hooks section; external skill includes hook registration in its manifest; agent copies hook script into system location | Harness hooks fire before/after every command; persistent behavioral override; hook code runs with agent privileges; difficult to identify source | 9 | 2 | 3 | **54** | Hook registration FORBIDDEN in Phase 0-5 per tool-policy.md; settings.json treated as read-only; update-config skill classified as Forbidden | settings.json pre/post diff; hook script file detection; harness log inspection for PreToolUse/PostToolUse events; anomalous hook execution frequency | Human Reviewer + Runtime Architect | Phase 0-5 |
| 28 | Hook exits non-zero (blocks execution, agent cannot proceed) | Pre-existing corrupted hook from prior phases; hook script has syntax error; hook intentionally blocking certain tool categories; environment mismatch causes hook failure | Agent execution completely blocked; tool calls fail silently or with cryptic errors; batch run cannot complete; task stuck indefinitely | 7 | 3 | 3 | **63** | Hook validation during session startup (smoke test); hook exit code != 0 should warn but not block (if safe to skip); debug-logging on hook execution | Blackboard heartbeat timeout detection; task stuck indicator (no progress for N minutes); tool call error log analysis for hook rejection patterns | Agent Runtime + Human Reviewer | Phase 0-5 |
| 29 | Schema not validated before acceptance (contracts accepted with structural errors) | Reviewer accepts ExecutionReport without contract validation; agent produces JSON with missing required fields; manual review misses structural defects because visual inspection focuses on content | Downstream tooling fails to parse contracts; runtime errors in future phases; data migration failures; contract consumer assumes valid data and crashes | 7 | 4 | 2 | **56** | Contract validators planned for future phase; manual reviewer checklist includes schema check; enum values defined per contract | Low detection: current phase has no automated schema validator; reviewer must manually check fields; best effort with grep for required field presence | Human Reviewer + Validation Tooling | Phase 0-5 |
| 30 | Agent writes to memory (file system mutation of memory/*.md or agent-state.db) | Agent bypasses MemoryUpdateRecord protocol; agent "helpfully" writes memory because it seems useful; agent uses Write tool on memory path despite explicit prohibition | Memory corpus corrupted with unapproved entries; future memory-bridge loads bad data; self-evolution loop tainted with unvetted learnings; reviewer authority bypassed | 8 | 3 | 2 | **48** | Memory system Phase 0-5 read-only per memory-architecture.md; forbidden write operations enumerated; MemoryUpdateRecord requires human approval | PRE/POST diff on memory directories; file modification timestamp audit; unexpected file creation in memory/ detected by git status --short | Human Reviewer + Memory Admin | Phase 0-5 |

---

## Summary Statistics

| Metric | Value |
|--------|-------|
| **Total failure modes** | 30 |
| **RPN range** | 48 -- 450 |
| **High risk (RPN >= 200)** | 7 |
| **Medium risk (RPN 100-199)** | 12 |
| **Low risk (RPN < 100)** | 11 |
| **Average RPN** | 183 |

## Top 5 Risks by RPN

| Rank | RPN | Failure Mode |
|------|-----|--------------|
| 1 | 450 | Agent executes forbidden tool |
| 2 | 420 | Agent modifies dirty baseline |
| 3 | 400 | Agent reports fake green |
| 4 | 360 | Reviewer fails to detect violation |
| 5 | 320 | Agent self-approves |

## Coverage Matrix

| Area | Failure Mode #s | Count |
|------|----------------|-------|
| Forbidden tool execution | 1 | 1 |
| Scope/baseline mutation | 2, 12 | 2 |
| Dirty baseline protection | 2 | 1 |
| External repo clone | 6 | 1 |
| Package installation | 7 | 1 |
| Hook registration | 8, 27 | 2 |
| MCP config modification | 9 | 1 |
| Memory write | 10, 18, 30 | 3 |
| Secrets reading | 13 | 1 |
| Dangerous git | 14 | 1 |
| Fake green reporting | 3 | 1 |
| Self-approval | 5 | 1 |
| Skill installation | 19 | 1 |
| bb_solidify_knowledge | 10 | 1 |
| Reviewer error | 4 | 1 |
| Schema validation | 15, 29 | 2 |
| Gate bypass | 11 | 1 |
| PRE/POST mismatch | 20 | 1 |
| ExecutionReport incompleteness | 16 | 1 |
| Path drift | 17 | 1 |
| CodeGraph staleness | 21 | 1 |
| Blackboard unavailability | 22 | 1 |
| Session boundary | 23 | 1 |
| Phase boundary | 24 | 1 |
| Skill intake bypass | 26 | 1 |
| PowerShell hook | 27 | 1 |
| Hook non-zero exit | 28 | 1 |
| AGENTS.md staleness | 25 | 1 |
| Schema pre-acceptance | 29 | 1 |
| MemoryUpdateRecord w/o approval | 18 | 1 |

## Recommendations

1. **Automated schema validator**: The highest multiplier for many risks is low Detection (D=2-4). An automated contract validation step that checks required fields, enum values, and type constraints would reduce RPN across 10+ entries.
2. **PRE/POST git snapshot**: Automate git status --short capture before and after every batch. Diff the snapshots. Flag any difference not explicitly listed in the ExecutionReport.
3. **Blackboard anomaly monitor**: Detect forbidden operations (bb_solidify_knowledge, bb_share_knowledge) and alert immediately rather than relying on post-hoc review.
4. **Second-reviewer protocol**: For P0 gate checks and high-RPN batches, require a second human or automated agent (planning agent) to independently verify the ExecutionReport before acceptance.
5. **Tool call allowlist enforcement at runtime**: Rather than relying solely on prompt constraints, implement a pre-execution hook that blocks forbidden tool names before dispatch.

## Constraints Validated

| Constraint | Status |
|------------|--------|
| No baseline file modification | Covered by FM #2 (RPN 420) |
| No secrets reading | Covered by FM #13 (RPN 135) |
| No external cloning | Covered by FM #6 (RPN 280) |
| No package installation | Covered by FM #7 (RPN 250) |
| No hook registration | Covered by FM #8 (RPN 180) |
| No MCP config mutation | Covered by FM #9 (RPN 180) |
| No memory writes | Covered by FM #10, #18, #30 |
| No forbidden tools | Covered by FM #1 (RPN 450) |
| No dangerous git | Covered by FM #14 (RPN 135) |

---

> Generated by D5 Risk Model Agent, 2026-05-27
> Batch: D5
> Input documents: operating-model.md, memory-architecture.md, tool-policy.md, skill-trigger-matrix.md, external-skill-intake.md, integration-contracts.md
