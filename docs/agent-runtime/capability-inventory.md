# Capability Inventory -- Cross-Platform

> Batch C3C, 2026-05-28
> 30 capabilities across Claude Code + Codex.
> All: auto_use_allowed=false, execution_allowed=false, mutation_allowed=false.

## Registration Procedure

This inventory is the single source of truth for all capabilities. No capability may be used unless it appears in this file with `Status: approved`.

### Adding a New Capability

1. **Propose**: Add an entry to this file with `Status: proposed`. Include all required fields: Platform, Type, Access, Risk, Preferred for, Forbidden for, Fallback, Human gate, Must explain if skipped, Evidence, and Capability Passport fields (verified_status, last_verified_at, confidence, usable_for_gate0, usable_for_execution).
2. **Review**: Submit the proposal to the human reviewer. The reviewer checks: (a) Platform field is correct, (b) Risk level matches existing classifications, (c) Phase 0-5 constraints are appropriate, (d) Forbidden actions are explicitly listed.
3. **Approve**: Reviewer changes `Status: proposed` �?`Status: approved` and signs off.
4. **Enable**: Enable the capability on the target platform (e.g., `codex plugin add` for Codex, `register-hooks.ps1` for Claude hooks).
5. **Verify**: Confirm the capability appears in `codex plugin list` (Codex) or relevant config (Claude). Update the Evidence field with the verification output.
6. **Report**: Include the new registration in the batch ExecutionReport.

### Capability Passport (Verification Fields)

Each capability entry must include verification fields in addition to the base fields (Platform, Type, Access, Risk, etc.):

| Field | Values | Purpose |
|-------|--------|---------|
| verified_status | unknown / verified / degraded / stale / broken | Whether capability has been proven available |
| last_verified_at | ISO-8601 date | When last verified |
| confidence | 0.0 �?1.0 | Evidence strength for current status |
| usable_for_gate0 | true / false | Can this capability be cited in Gate 0 sufficiency checks? |
| usable_for_execution | true / false | Can this capability be dispatched to in SADP? |

Rule: A capability with verified_status = unknown, stale, or broken must NOT be used as the sole basis to reject new construction in Gate 0 sufficiency checks.

### Capability Expiration Policy

Capabilities decay over time. A verified capability can become stale, and a stale capability can become broken.
The inventory must reflect reality, not declaration.

| Status | Meaning | Gate 0 Usage | Execution Usage |
|--------|---------|-------------|-----------------|
| verified | Proven available within expiry window | allowed | allowed |
| degraded | Partially available (some features broken) | partial_only | allowed_with_warning |
| stale | Not verified within expiry window | candidate_only (cannot be sole basis) | allowed_with_warning |
| broken | Known unavailable | forbidden | forbidden |
| unknown | Never verified, declaration only | candidate_only | forbidden |

**Expiry rules:**
- External dependency capabilities (API, MCP, CLI): expire after **30 days** without re-verification
- Local static capabilities (scripts, files, templates): expire after **90 days** without re-verification
- Any capability that fails 2 consecutive verification attempts �� auto-degrade to broken
- `last_verified_at` must be updated on every successful verification

**Gate 0 constraint:**
- `verified` �� may be cited as sufficient coverage evidence
- `degraded` �� may be cited for partial coverage only; must note which parts are unavailable
- `stale` or `unknown` �� may be cited only as candidates; must NOT be sole basis for rejecting new construction
- `broken` �� must not be cited at all

**Re-verification triggers:**
- Expiry window exceeded �� auto-mark stale
- Dependency change (MCP server update, CLI version change, API key rotation) �� force re-verify
- Capability cited in Gate 0 for the first time this session �� recommended re-verify


### Removing or Disabling a Capability

- Change `Status: approved` �?`Status: disabled` with a reason and date.
- Remove the capability from the target platform (e.g., `codex plugin disable` or edit `config.toml`).
- Do not delete the entry from this file -- disabled entries serve as a historical record.

### Platform Field Rules

| Platform | Meaning | Enablement |
|----------|---------|------------|
| Both | Available on Claude Code and Codex | Enable on both platforms (registration once, enablement per-platform) |
| Claude | Claude Code only | Enable via Claude-specific mechanism (hooks, MCP, settings.json) |
| Codex | Codex only | Enable via Codex-specific mechanism (plugins, config.toml) |

## Platform Key

| Label | Meaning |
|-------|---------|
| Both | Available on both platforms (same filesystem, same governance assets) |
| Claude | Claude Code only (hooks, settings.json) |
| Codex | Codex only (plugins, config.toml, in-app browser) |

---

## 1. CodeGraph
- **Platform**: Both
- **Type**: code_intelligence
- **Access**: read_only
- **Risk**: high
- **Preferred for**: structural code understanding, symbol lookup, caller/callee analysis
- **Forbidden for**: literal string search, current fact without freshness check, overriding filesystem/git
- **Fallback**: rg, Read, Grep
- **Human gate**: yes (reindex)
- **Must explain if skipped**: yes
- **Evidence**: codegraph_status output, index_freshness, target_root match

- **Passport verified_status**: unknown
- **Passport last_verified_at**: 2026-06-12
- **Passport confidence**: 0.95
- **Passport usable_for_gate0**: false
- **Passport usable_for_execution**: false
- **Passport dependency_type**: external_dependency
- **Passport re_verification_note**: 2026-06-12 codex plugin list shows CodeGraph NOT installed. Downgraded from verified to unknown.

## 2. rg / Grep / Read (filesystem search)
- **Platform**: Both
- **Type**: search
- **Access**: read_only
- **Risk**: low
- **Preferred for**: literal string search, pattern matching, file content reading
- **Forbidden for**: structural code understanding (use CodeGraph first), secret file reading
- **Fallback**: Select-String (PowerShell)
- **Human gate**: no
- **Must explain if skipped**: no
- **Evidence**: command output

- **Passport verified_status**: verified
- **Passport last_verified_at**: 2026-05-28
- **Passport confidence**: 0.9
- **Passport usable_for_gate0**: true
- **Passport usable_for_execution**: true

## 3. PowerShell read-only commands
- **Platform**: Both
- **Type**: shell
- **Access**: read_only
- **Risk**: medium
- **Preferred for**: Test-Path, Get-Content, Get-FileHash, Measure-Object, Get-ChildItem
- **Forbidden for**: Set-Content, Remove-Item, Invoke-WebRequest, Start-Process, script execution
- **Fallback**: bash test/ls/wc
- **Human gate**: yes (any write command)
- **Must explain if skipped**: no
- **Evidence**: command output

- **Passport verified_status**: verified
- **Passport last_verified_at**: 2026-05-28
- **Passport confidence**: 0.95
- **Passport usable_for_gate0**: true
- **Passport usable_for_execution**: true

## 4. JSON Schema Validation
- **Platform**: Both
- **Type**: validation
- **Access**: read_only
- **Risk**: low
- **Preferred for**: schema parse audit, JSON structure validation, enum constraint check
- **Forbidden for**: schema modification without approval
- **Fallback**: manual review
- **Human gate**: no
- **Must explain if skipped**: no
JSON
- **Passport verified_status**: verified
- **Passport last_verified_at**: 2026-05-28
- **Passport confidence**: 0.9
- **Passport usable_for_gate0**: true
- **Passport usable_for_execution**: true

## 5. Runtime Docs
- **Platform**: Both
- **Type**: documentation
- **Access**: read_only
- **Risk**: low
- **Preferred for**: policy lookup, contract reference, gate definition, phase boundary check
- **Forbidden for**: current fact without cross-reference, overriding schemas
- **Fallback**: direct file read
- **Human gate**: no
- **Must explain if skipped**: no
- **Evidence**: doc path + section reference
- **Passport verified_status**: verified
- **Passport last_verified_at**: 2026-05-28
- **Passport confidence**: 0.9
- **Passport usable_for_gate0**: true
- **Passport usable_for_execution**: true
- **Passport dependency_type**: local_static

## 6. Runtime Rules
- **Platform**: Both
- **Type**: rules
- **Access**: read_only
- **Risk**: low
- **Preferred for**: rule violation check, coding standard, security hard stop, review gate
- **Forbidden for**: overriding reviewer decision, auto-approving gates
- **Fallback**: docs search
- **Human gate**: no
- **Must explain if skipped**: no
- **Evidence**: rule ID + file reference
- **Passport verified_status**: verified
- **Passport last_verified_at**: 2026-05-28
- **Passport confidence**: 0.95
- **Passport usable_for_gate0**: true
- **Passport usable_for_execution**: true
- **Passport dependency_type**: local_static

## 7. Negative Tests
- **Platform**: Both
- **Type**: testing
- **Access**: reference_only
- **Risk**: low
- **Preferred for**: validating reviewer checklists, gate enforcement testing
- **Forbidden for**: execution, substituting for actual tests
- **Fallback**: N/A
- **Human gate**: no
- **Must explain if skipped**: no
- **Evidence**: test ID + expected_gate_decision
- **Passport verified_status**: verified
- **Passport last_verified_at**: 2026-05-28
- **Passport confidence**: 0.7
- **Passport usable_for_gate0**: true
- **Passport usable_for_execution**: false
- **Passport dependency_type**: local_static

## 8. Reviewer Playbooks
- **Platform**: Both
- **Type**: review
- **Access**: reference_only
- **Risk**: low
- **Preferred for**: reviewer decision-making, gate evaluation
- **Forbidden for**: auto-approving gates, skipping reviewer
- **Fallback**: verification-gates.md
- **Human gate**: no
- **Must explain if skipped**: no
- **Evidence**: playbook reference + decision path
- **Passport verified_status**: verified
- **Passport last_verified_at**: 2026-05-28
- **Passport confidence**: 0.85
- **Passport usable_for_gate0**: true
- **Passport usable_for_execution**: true
- **Passport dependency_type**: local_static

## 10. test-frame
- **Platform**: Both
- **Type**: evidence
- **Access**: read_only (docs + directory listing)
- **Risk**: high
- **Preferred for**: evidence provider candidate reference
- **Forbidden for**: aggregator execution, attribution execution, CLI execution, orchestrator execution, test execution, producing GateResult
- **Fallback**: historical evidence
- **Human gate**: yes (any execution)
- **Must explain if skipped**: no
- **Evidence**: R2 policy docs
- **Passport verified_status**: verified
- **Passport last_verified_at**: 2026-05-28
- **Passport confidence**: 0.8
- **Passport usable_for_gate0**: true
- **Passport usable_for_execution**: false
- **Passport dependency_type**: local_static

## 11. dev-frame
- **Platform**: Both
- **Type**: orchestration
- **Access**: read_only (docs + directory listing)
- **Risk**: high
- **Preferred for**: orchestration adapter candidate reference
- **Forbidden for**: smoke_test.py execution, ai-workflow-hub execution, ai-workflow-hub-e2e execution, producing GateResult
- **Fallback**: historical smoke_report.txt
- **Human gate**: yes (any execution)
- **Must explain if skipped**: no
- **Evidence**: R3 policy docs
- **Passport verified_status**: verified
- **Passport last_verified_at**: 2026-05-28
- **Passport confidence**: 0.8
- **Passport usable_for_gate0**: true
- **Passport usable_for_execution**: false
- **Passport dependency_type**: local_static

## 12. Local Skills
- **Platform**: Both
- **Type**: skill
- **Access**: reference_only
- **Risk**: high
- **Preferred for**: skill classification reference, R5 intake lookup
- **Forbidden for**: execution, auto-load, installation, skill-evolver, recursive-improve, skill-installer
- **Fallback**: N/A
- **Human gate**: yes (any skill execution)
- **Must explain if skipped**: no (not expected to be used)
- **Evidence**: R5 intake docs
- **Passport verified_status**: verified
- **Passport last_verified_at**: 2026-05-28
- **Passport confidence**: 0.9
- **Passport usable_for_gate0**: true
- **Passport usable_for_execution**: false
- **Passport dependency_type**: local_static

## 13. RD2100 Memory
- **Platform**: Both
- **Type**: memory
- **Access**: read_only
- **Risk**: high
- **Preferred for**: context reference (read-only)
- **Forbidden for**: memory write, used_as_fact without cross-reference
- **Fallback**: filesystem/git verification
- **Human gate**: yes (any write)
- **Must explain if skipped**: no
- **Evidence**: R6 policy docs, stale_risk, conflict_check
- **Passport verified_status**: verified
- **Passport last_verified_at**: 2026-05-28
- **Passport confidence**: 0.9
- **Passport usable_for_gate0**: true
- **Passport usable_for_execution**: false
- **Passport dependency_type**: local_static

## 14. WorkQueue
- **Platform**: Both
- **Type**: workqueue
- **Access**: read_only (inspect definitions)
- **Risk**: high
- **Preferred for**: queue definition reference
- **Forbidden for**: task dispatch, queue consumption, queue modification
- **Fallback**: N/A
- **Human gate**: yes (any consumption)
- **Must explain if skipped**: no
- **Evidence**: R7 policy docs

- **Passport verified_status**: degraded
- **Passport last_verified_at**: 2026-06-12
- **Passport confidence**: 0.5
- **Passport usable_for_gate0**: false
- **Passport usable_for_execution**: false
- **Passport re_verification_note**: 2026-06-12 confirmed queue definitions present (workqueue-controlled-use-policy.md, memory entries). Status remains degraded by design.

## 15. Scripts (PowerShell runners)
- **Platform**: Both
- **Type**: script
- **Access**: human_gated (not_run)
- **Risk**: high
- **Preferred for**: N/A (not authorized for execution)
- **Forbidden for**: execution without ScriptSafetyRecord + human gate
- **Fallback**: N/A
- **Human gate**: yes (per-script, per-execution)
- **Must explain if skipped**: no
- **Evidence**: R7 ScriptSafetyRecord
- **Passport verified_status**: verified
- **Passport last_verified_at**: 2026-05-28
- **Passport confidence**: 0.9
- **Passport usable_for_gate0**: true
- **Passport usable_for_execution**: false
- **Passport dependency_type**: local_static

## 16. Governance Hooks
- **Platform**: Claude
- **Type**: hook
- **Access**: pre-edit: active (registered, blocking). Other 4: reference_only (audit-only draft)
- **Risk**: medium
- **Preferred for**: pre-edit: governance gate (blocks memory/sealed/secrets edits). Drafts: audit reference
- **Forbidden for**: registering additional hooks without human gate, draft hook execution
- **Fallback**: N/A
- **Human gate**: yes (any new registration beyond pre-edit)
- **Must explain if skipped**: no
- **Evidence**: pre-edit: settings.json + hook-diag-*.txt. Drafts: hook file + AUDIT-ONLY DRAFT header
- **Passport verified_status**: verified
- **Passport last_verified_at**: 2026-05-28
- **Passport confidence**: 0.9
- **Passport usable_for_gate0**: true
- **Passport usable_for_execution**: true
- **Passport dependency_type**: local_static

## 17. Phase 6 SourceLock / Quarantine
- **Platform**: Both
- **Type**: source_lock
- **Access**: reference_only (design only)
- **Risk**: critical
- **Preferred for**: external skill intake planning reference
- **Forbidden for**: clone, install, execute, enable MCP, run external code
- **Fallback**: N/A
- **Human gate**: yes (clone, any Phase 6C action)
- **Must explain if skipped**: no
- **Evidence**: Phase 6 design docs, SourceLockRecord schema
- **Passport verified_status**: stale
- **Passport last_verified_at**: 2026-06-12
- **Passport confidence**: 0.3
- **Passport usable_for_gate0**: false
- **Passport usable_for_execution**: false
- **Passport dependency_type**: local_static
- **Passport re_verification_note**: 2026-06-12 confirmed source-lock-record.schema.json exists (4.7 KB). Phase 6 not yet active. Status remains stale by design.

## 18. Sealed Files Manifest
- **Platform**: Claude
- **Type**: governance_manifest
- **Access**: reference_only
- **Risk**: medium
- **Preferred for**: determining which files are sealed against unauthorized edits
- **Forbidden for**: modification without human approval
- **Fallback**: hardcoded 7 core files in pre-edit hook
- **Human gate**: yes (any manifest modification)
- **Must explain if skipped**: no
- **Evidence**: sealed-files-manifest.json (22 files, 3 dirs, 2 memory paths)
- **Passport verified_status**: verified
- **Passport last_verified_at**: 2026-05-28
- **Passport confidence**: 0.9
- **Passport usable_for_gate0**: true
- **Passport usable_for_execution**: true
- **Passport dependency_type**: local_static

## 19. Hook Registration Script
- **Platform**: Claude
- **Type**: governance_script
- **Access**: human_gated (not auto-executed)
- **Risk**: high
- **Preferred for**: registering pre-edit governance hook in Claude Code settings.json
- **Forbidden for**: auto-execution, registering hooks beyond pre-edit, modifying settings without backup
- **Fallback**: manual merge via registration-config.json
- **Human gate**: yes (per-execution)
- **Must explain if skipped**: no
- **Evidence**: register-hooks.ps1 + settings.json.bak.<timestamp>
- **Passport verified_status**: verified
- **Passport last_verified_at**: 2026-05-28
- **Passport confidence**: 0.85
- **Passport usable_for_gate0**: true
- **Passport usable_for_execution**: false
- **Passport dependency_type**: local_static

---

## 20. coderabbit
- **Platform**: Codex
- **Type**: plugin (ai_code_review)
- **Access**: read_only (code review suggestions only; does not mutate code)
- **Risk**: low
- **Preferred for**: AI code review, complements `rules/review.md` P0/P1 gate enforcement
- **Forbidden for**: auto-committing changes, modifying code without human approval
- **Fallback**: manual review against reviewer-playbook.md
- **Human gate**: no (review-only; does not modify state)
- **Must explain if skipped**: no
- **Phase 0-5**: allowed (read-only review, no mutation)
- **Evidence**: codex plugin list output
- **Passport verified_status**: unknown
- **Passport last_verified_at**: 2026-06-12
- **Passport confidence**: 0.9
- **Passport usable_for_gate0**: false
- **Passport usable_for_execution**: false
- **Passport dependency_type**: external_dependency
- **Passport re_verification_note**: 2026-06-12 codex plugin list shows coderabbit NOT installed. Downgraded from verified to unknown.

## 21. codex-security
- **Platform**: Codex
- **Type**: plugin (security_scanning)
- **Access**: read_only (security analysis only; does not mutate code)
- **Risk**: low
- **Preferred for**: security scanning, complements `rules/security.md` sec-001~008 hard stops
- **Forbidden for**: auto-fixing security issues without human approval, modifying config
- **Fallback**: manual STRIDE/FMEA review
- **Human gate**: no (scan-only; does not modify state)
- **Must explain if skipped**: no
- **Phase 0-5**: allowed (read-only scan, no mutation)
- **Evidence**: codex plugin list output
- **Passport verified_status**: verified
- **Passport last_verified_at**: 2026-06-12
- **Passport confidence**: 0.9
- **Passport usable_for_gate0**: true
- **Passport usable_for_execution**: true
- **Passport dependency_type**: external_dependency
- **Passport re_verification_note**: 2026-06-12 codex plugin list confirms installed, enabled (c6ea566d). Status verified.

## 22. supabase
- **Platform**: Codex
- **Type**: plugin (database_backend)
- **Access**: human_gated (database operations)
- **Risk**: high
- **Preferred for**: database/API operations (Phase 1+ data layer)
- **Forbidden for**: schema migration, data mutation, table creation without human gate in Phase 0-5
- **Fallback**: N/A (no Phase 0-5 use case)
- **Human gate**: yes (any database write operation)
- **Must explain if skipped**: no
- **Phase 0-5**: restricted (writes blocked)
- **Evidence**: codex plugin list output
- **Passport verified_status**: unknown
- **Passport last_verified_at**: 2026-06-12
- **Passport confidence**: 0.9
- **Passport usable_for_gate0**: false
- **Passport usable_for_execution**: false
- **Passport dependency_type**: external_dependency
- **Passport re_verification_note**: 2026-06-12 codex plugin list shows supabase NOT installed. Downgraded from verified to unknown.

## 23. github
- **Platform**: Codex
- **Type**: plugin (git_platform)
- **Access**: human_gated (git operations)
- **Risk**: high
- **Preferred for**: GitHub integration (Phase 1+)
- **Forbidden for**: push, force-push, delete branch, modify protected branches in Phase 0-5
- **Fallback**: local git CLI (read-only in Phase 0-5)
- **Human gate**: yes (push, PR creation, branch deletion)
- **Must explain if skipped**: no
- **Phase 0-5**: restricted (writes blocked)
- **Evidence**: codex plugin list output
- **Passport verified_status**: unknown
- **Passport last_verified_at**: 2026-06-12
- **Passport confidence**: 0.9
- **Passport usable_for_gate0**: false
- **Passport usable_for_execution**: false
- **Passport dependency_type**: external_dependency
- **Passport re_verification_note**: 2026-06-12 codex plugin list shows github NOT installed. Downgraded from verified to unknown.

## 24. browser
- **Platform**: Codex
- **Type**: plugin (browser_automation)
- **Access**: human_gated (in-app browser)
- **Risk**: medium
- **Preferred for**: localhost testing, in-app webpage inspection (Phase 2+)
- **Forbidden for**: automated browsing of external sites, form submission without human gate
- **Fallback**: N/A (no Phase 0-5 use case)
- **Human gate**: yes (any browser navigation to external URLs)
- **Must explain if skipped**: no
- **Phase 0-5**: restricted (localhost only)
- **Evidence**: codex plugin list output
- **Passport verified_status**: unknown
- **Passport last_verified_at**: 2026-06-12
- **Passport confidence**: 0.9
- **Passport usable_for_gate0**: false
- **Passport usable_for_execution**: false
- **Passport dependency_type**: external_dependency
- **Passport re_verification_note**: 2026-06-12 codex plugin list shows browser (openai-curated) NOT installed. browser (openai-bundled) is installed/enabled but is a separate marketplace entry. Downgraded from verified to unknown.

## 25. superpowers
- **Platform**: Codex
- **Type**: plugin (dev_methodology)
- **Access**: reference_only (methodology guidance; not a tool)
- **Risk**: low
- **Preferred for**: TDD, debugging, code review methodology guidance
- **Forbidden for**: N/A (methodology only; no executable surface)
- **Fallback**: manual methodology docs
- **Human gate**: no
- **Must explain if skipped**: no
- **Phase 0-5**: allowed (methodology reference)
- **Evidence**: codex plugin list output
- **Passport verified_status**: unknown
- **Passport last_verified_at**: 2026-06-12
- **Passport confidence**: 0.9
- **Passport usable_for_gate0**: false
- **Passport usable_for_execution**: false
- **Passport dependency_type**: external_dependency
- **Passport re_verification_note**: 2026-06-12 codex plugin list shows superpowers NOT installed. Downgraded from verified to unknown.

## 26. linear
- **Platform**: Codex
- **Type**: plugin (project_management)
- **Access**: human_gated (external SaaS)
- **Risk**: medium
- **Preferred for**: Phase 1+ multi-agent task tracking
- **Forbidden for**: automated task creation/modification without human gate
- **Fallback**: N/A (no Phase 0-5 use case)
- **Human gate**: yes (any write to Linear)
- **Must explain if skipped**: no
- **Phase 0-5**: restricted (no use case; kept for Phase 1+)
- **Evidence**: codex plugin list output
- **Passport verified_status**: unknown
- **Passport last_verified_at**: 2026-06-12
- **Passport confidence**: 0.9
- **Passport usable_for_gate0**: false
- **Passport usable_for_execution**: false
- **Passport dependency_type**: external_dependency
- **Passport re_verification_note**: 2026-06-12 codex plugin list shows linear NOT installed. Downgraded from verified to unknown.

## 27. notion
- **Platform**: Codex
- **Type**: plugin (knowledge_management)
- **Access**: human_gated (external SaaS)
- **Risk**: medium
- **Preferred for**: knowledge management, complements `docs/` system (Phase 1+)
- **Forbidden for**: automated page creation/modification without human gate
- **Fallback**: local docs/ Markdown files
- **Human gate**: yes (any write to Notion)
- **Must explain if skipped**: no
- **Phase 0-5**: restricted (no use case; kept for Phase 1+)
- **Evidence**: codex plugin list output
- **Passport verified_status**: unknown
- **Passport last_verified_at**: 2026-06-12
- **Passport confidence**: 0.9
- **Passport usable_for_gate0**: false
- **Passport usable_for_execution**: false
- **Passport dependency_type**: external_dependency
- **Passport re_verification_note**: 2026-06-12 codex plugin list shows notion NOT installed. Downgraded from verified to unknown.

---

## Summary

| # | Capability | Platform | Type | Risk | Status | Phase 0-5 |
|---|-----------|:---:|------|:---:|:---:|:---:|
| 1 | CodeGraph | Both | code_intelligence | high | approved | read-only |
| 2 | rg/Grep/Read | Both | search | low | approved | read-only |
| 3 | Shell (read-only) | Both | shell | medium | approved | read-only |
| 4 | JSON Validation | Both | validation | low | approved | read-only |
| 5 | Runtime Docs | Both | docs | low | approved | read-only |
| 6 | Runtime Rules | Both | rules | low | approved | read-only |
| 7 | Negative Tests | Both | testing | low | approved | reference |
| 8 | Reviewer Playbooks | Both | review | low | approved | reference |
| 10 | test-frame | Both | evidence | high | approved | read+current_evidence |
| 11 | dev-frame | Both | orchestration | high | approved | adapter_dry_run |
| 12 | Local Skills | Both | skill | high | approved | reference_only |
| 13 | Memory | Both | memory | high | approved | read-only |
| 14 | WorkQueue | Both | workqueue | high | approved | dry_run_dispatch |
| 15 | Scripts | Both | script | high | approved | source_inspection |
| 16 | Hooks | Claude | hook | medium | approved | pre-edit active |
| 17 | Phase 6 SourceLock | Both | source_lock | critical | approved | design_only |
| 18 | Sealed Files Manifest | Claude | governance | medium | approved | active |
| 19 | Hook Registration Script | Claude | governance | high | approved | human_gated |
| 20 | coderabbit | Codex | ai_review | low | approved | allowed |
| 21 | codex-security | Codex | security | low | approved | allowed |
| 22 | supabase | Codex | database | high | approved | restricted |
| 23 | github | Codex | git | high | approved | restricted |
| 24 | browser | Codex | browser | medium | approved | restricted |
| 25 | superpowers | Codex | methodology | low | approved | allowed |
| 26 | linear | Codex | pm | medium | approved | restricted |
| 28 | Sub-Agent Dispatch | Both | orchestration | medium | approved | read-only |
| 27 | notion | Codex | knowledge | medium | approved | restricted |
| 29 | dev-frame-opencode Dispatch | Both | orchestration | high | proposed | human-gated |
| 30 | CDP Write Adapter | Both | orchestration | high | verified | human-gated |

> Verified status removed from summary table. See Capability Passport Summary below for verification status. Detailed entries are the source of truth.

## Risk Distribution

| Risk | Count | Capabilities |
|:---:|:---:|------|
| critical | 1 | Phase 6 SourceLock |
| high | 12 | CodeGraph, test-frame, dev-frame, Local Skills, Memory, WorkQueue, Scripts, Hook Registration Script, supabase, github, dev-frame-opencode Dispatch, CDP Write Adapter |
| medium | 6 | Shell, Hooks, Sealed Manifest, browser, linear, notion |
| low | 9 | rg/Grep, JSON, Docs, Rules, Negative Tests, Playbooks, coderabbit, codex-security, superpowers |


## 28. Sub-Agent Dispatch Protocol (SADP)
- **Platform**: Both
- **Type**: orchestration
- **Access**: read_only (docs + protocol reference)
- **Risk**: medium
- **Preferred for**: default multi-agent task dispatch (Codex goal agent �� Claude Code agent)
- **Forbidden for**: execution without TaskSpec, producing GateResult, capability use without core-007 registration
- **Fallback**: ad-hoc goal-mode handoff
- **Human gate**: no (protocol reference only)
- **Must explain if skipped**: yes (if TaskSpec format not used, explain why)
- **Evidence**: sub-agent-dispatch-protocol.md exists (194 lines), bootstrap copies it, AGENTS.md references it as default process

- **Passport verified_status**: verified
- **Passport last_verified_at**: 2026-05-28
- **Passport confidence**: 0.9
- **Passport usable_for_gate0**: true
- **Passport usable_for_execution**: true

## 29. dev-frame-opencode Dispatch
- **Status**: approved
- **Platform**: Both
- **Type**: orchestration
- **Access**: human_gated (not executable by default)
- **Risk**: high
- **Preferred for**: TaskSpec-bound worker dispatch when SADP explicitly selects opencode and records chain evidence
- **Forbidden for**: direct GPT submission, writing authoritative closure artifacts, bypassing submission_adapter, bypassing reviewer node, running without TaskSpec, running without tool-policy authorization
- **Fallback**: Codex direct execution with explicit fallback record, or blocked/human_required for governance modifications
- **Human gate**: yes (any `opencode run` execution or external runtime invocation)
- **Must explain if skipped**: yes
- **Evidence**: dependency-canaries.md, sub-agent-dispatch-protocol.md dispatch checks, Conversation Registry `governance_scope`

- **Passport verified_status**: verified
- **Passport last_verified_at**: 2026-06-10
- **Passport confidence**: 0.8
- **Passport usable_for_gate0**: true
- **Passport usable_for_execution**: true
- **Passport dependency_type**: external_dependency

### Status Legend

| Status | Meaning |
|--------|---------|
| approved | Reviewer-approved and enabled on target platform |
| proposed | Awaiting reviewer approval; not yet enabled |
| disabled | Previously approved, now disabled (kept for historical record) |
| rejected | Proposal rejected; capability must not be used |


---

## 30. CDP Write Adapter
- **Status**: approved
- **Platform**: Both
- **Type**: orchestration
- **Access**: human_gated (injects prompts into independent ChatGPT browser sessions via Chrome DevTools Protocol)
- **Risk**: high
- **Preferred for**: dispatching TaskSpecs to independent ChatGPT conversations for real multi-GPT execution
- **Forbidden for**: dispatching without TaskSpec, dispatching without dry-run validation, modifying ChatGPT DOM without injection verification, bypassing governance pipeline (Gate 0 → dispatch plan → adapter)
- **Fallback**: sub-agent dispatch via QoderWork Task tool (honest declaration: not independent multi-GPT)
- **Human gate**: yes (any live dispatch; dry-run allowed without gate)
- **Must explain if skipped**: yes (if using sub-agent dispatch instead, must declare honestly)
- **Evidence**: scripts/cdp_write_adapter.py, scripts/cdp_dispatch_runner.py, tests/test_cdp_write_adapter.py (18 tests)
- **Dependency**: Chrome with --remote-debugging-port=9222, websockets Python library ≥ 13, ChatGPT tabs open in Chrome

- **Passport verified_status**: verified
- **Passport last_verified_at**: 2026-06-13
- **Passport confidence**: 0.9
- **Passport usable_for_gate0**: true
- **Passport usable_for_execution**: true
- **Passport dependency_type**: external_dependency
- **Passport re_verification_note**: 2026-06-13 verified CDP WebSocket connectivity (websockets 16.0, Chrome 149), text injection via execCommand, Enter-key submission, response capture. 18 tests pass including 4 live integration tests.


---


## Capability Passport Summary (2026-06-12)

Evidence-based verification status. **30 of 30 registered** (updated 2026-06-13, CAP-030 added for CDP Write Adapter).
CAP-029 is approved on 2026-06-10 and is included in approved execution totals.
CAP-030 is verified on 2026-06-13 after successful live multi-GPT review cycle (4 reports dispatched via Playwright CDP, 4 CONDITIONAL_APPROVE responses received).

| Status | Count | IDs |
|--------|:-----:|-----|
| verified | 19 | CAP-002~008, CAP-010~013, CAP-015~016, CAP-018~019, CAP-021, CAP-028~030 |
| degraded | 1 | CAP-014 (WorkQueue: confirmed definitions present, still degraded) |
| broken | 0 | (none) |
| stale | 1 | CAP-017 (Phase 6 SourceLock: confirmed schema present, still stale) |
| unknown | 8 | CAP-001, CAP-020, CAP-022~027 (not installed in codex; re-verified 2026-06-12) |

| Type | Count | Expiry |
|------|:-----:|--------|
| local_static | 20 | 90 days |
| external_dependency | 11 | 30 days |

**Rule**: unknown/stale/broken must NOT be sole basis to reject new construction in Gate 0.

**Verification evidence**:
- Local static (20): 12 Test-Path confirmed 2026-05-28, 5 session-usage confirmed, 2 reference-only (docs exist), 1 stale (Phase 6 not yet active). CAP-014 re-verified 2026-06-12.
- External dependency (11): 1 confirmed installed (CAP-021 codex-security, 2026-06-12), 8 not installed (CAP-001, CAP-020, CAP-022~027, downgraded to unknown 2026-06-12), 1 confirmed 2026-06-10 (CAP-029), 1 verified 2026-06-13 (CAP-030 CDP Write Adapter: websockets+Chrome 149, 18 tests)

## External Skills Intake (Phase 0-5: classification only)

> No install, no clone, no execution. All dispositions in skills-inbox/external/candidate-index.md.

| # | Skill | Disposition | Risk | Phase Target |
|---|-------|-------------|------|--------------|
| 1 | ECC | defer | high | Phase 6: quarantine clone + static scan |
| 2 | Taste-Skill | candidate | medium | Phase 6: SkillIntakeRecord + review |
| 3 | AnySearch Skill | defer | high | Phase 6: network-isolated quarantine |
| 4 | AnySearch MCP Server | reject | critical | N/A (MCP config mutation out of scope) |
| 5 | Understand Anything | candidate | medium | Phase 6: codebase search integration |
| 6 | Anthropic Cybersecurity | reject | critical | N/A (security tool execution out of scope) |
| 7 | Andrej Karpathy Skills | reference_only | medium | Indefinite |
| 8 | UI-TARS Desktop | reject | critical | N/A (desktop automation out of scope) |
| 9 | addyosmani-agent-skills-zh | defer | high | Phase 6: quarantine + sub-skill classification |

### Taste-Skill Sub-Skills (Phase 6 classification pending)

13 sub-skills in skills-inbox/taste-skill/skills/: brandkit, brutalist-skill, gpt-tasteskill,
image-to-code-skill, imagegen-frontend-mobile, imagegen-frontend-web, minimalist-skill,
output-skill, redesign-skill, soft-skill, stitch-skill, taste-skill, taste-skill-v1.

All deferred to Phase 6 for individual SkillIntakeRecord creation.

### Disposition Summary

| Disposition | Count |
|-------------|:-----:|
| reference_only | 1 |
| candidate | 2 |
| defer | 3 |
| reject | 3 |

**Phase 0-5 rule**: External skills must not be installed, cloned, or executed.
All entries remain at their current disposition until Phase 6 Source Lock review.

## Taste-Skill Sub-Skills Classification (Batch C3E, 2026-05-28)

> 13 sub-skills from \skills-inbox/taste-skill/skills/\. All deferred to Phase 6 for SkillIntakeRecord creation.
> Phase 0-5: classification only. No install, no execution.

| # | Skill | Type | Risk | Disposition | Description |
|---|-------|------|------|-------------|-------------|
| 1 | brandkit | image_generation | medium | candidate | Premium brand-kit image generation |
| 2 | brutalist-skill | frontend_design | medium | candidate | Brutalist web design system |
| 3 | gpt-tasteskill | ux_animation | medium | candidate | UX/UI + GSAP animation engineering |
| 4 | image-to-code-skill | image_to_code | medium | candidate | Website image-to-code generation |
| 5 | imagegen-frontend-mobile | image_generation | medium | candidate | Mobile app screen concept generation |
| 6 | imagegen-frontend-web | image_generation | medium | candidate | Web design reference image generation |
| 7 | minimalist-skill | frontend_design | low | candidate | Clean editorial-style interfaces |
| 8 | output-skill | code_output | low | candidate | Override LLM truncation, enforce complete output |
| 9 | redesign-skill | frontend_design | medium | candidate | Website upgrade/redesign to premium quality |
| 10 | soft-skill | design_teaching | low | candidate | Teaches AI high-end agency design patterns |
| 11 | stitch-skill | design_system | medium | candidate | Google Stitch semantic design system |
| 12 | taste-skill | frontend_design | medium | candidate | Anti-slop frontend (landing pages, portfolios) |
| 13 | taste-skill-v1 | frontend_design | low | reference_only | Legacy v1, preserved for backward compat |

### Disposition Summary

| Disposition | Count | Skills |
|-------------|:-----:|--------|
| candidate | 12 | brandkit, brutalist-skill, gpt-tasteskill, image-to-code-skill, imagegen-frontend-mobile, imagegen-frontend-web, minimalist-skill, output-skill, redesign-skill, soft-skill, stitch-skill, taste-skill |
| reference_only | 1 | taste-skill-v1 (legacy compat only) |

### Risk Distribution

| Risk | Count |
|------|:-----:|
| medium | 9 |
| low | 4 |

### Phase 6 Next Steps

1. Create SkillIntakeRecord for each of 12 candidate sub-skills
2. Quarantine clone + static AST scan for any sub-skill with code execution surface
3. Sandbox review for image-generation sub-skills (dependency: imagegen availability)
4. taste-skill-v1 remains reference_only unless a project explicitly needs v1 behavior
