# Resource Registry -- RD2100 Agent Runtime v2

> Batch R0-B, 2026-05-27
> Phase: R0 (Registry & Classification Only)
> Status: registered (no execution, no enablement, no configuration)
> Schema: resource-registry-record.schema.json

## R0 Hard Boundary

Register != Enable. Candidate != Adapter. Adapter != Capability. No resource may be executed, enabled, installed, or configured at R0. All capability enablement is deferred to R1-R7.

## Registry Records

---


| Field | Value |
|-------|-------|
| **resource_type** | mcp_server |
| **path_status** | exists |
| **runtime_layer** | collaboration |
| **access_mode** | snapshot_only, human_gated |
| **risk_level** | critical |
| **lifecycle_state** | registered |
| **promotion_status** | registered |
| **human_gate_required** | true |
| **next_phase** | R1 |

#### Allowed Actions


#### Forbidden Actions

- bb_release_build_lock
- execute server.py
- register MCP server
- modify MCP config

#### Contract & Evidence

| Field | Value |
|-------|-------|
| **contract_mapping** | integration-contracts.md Appendix A3 |
| **evidence_requirements** | state.json existence, session registration log |
| **local_verification_status** | verified |

---

### Resource 2: dev-frame

| Field | Value |
|-------|-------|
| **resource_id** | `res-devframe-002` |
| **resource_name** | dev-frame |
| **resource_type** | repository |
| **path_or_reference** | D:\dev-frame |
| **path_status** | exists |
| **runtime_layer** | orchestration |
| **access_mode** | read_only, dry_run_candidate |
| **risk_level** | high |
| **lifecycle_state** | registered |
| **promotion_status** | registered |
| **human_gate_required** | true |
| **next_phase** | R3 |

#### Allowed Actions

- read_directory_structure
- read_CLAUDE.md
- read_smoke_report.txt
- git_status
- git_log (read-only)

#### Forbidden Actions

- execute smoke_test.py
- execute any ai-workflow-hub code
- execute ai-workflow-hub-e2e tests
- git commit
- git push
- modify any file in dev-frame
- npm install
- pip install
- run codegraph tests

#### Contract & Evidence

| Field | Value |
|-------|-------|
| **contract_mapping** | integration-contracts.md Appendix A1 |
| **evidence_requirements** | smoke_report.txt (2026-05-27: 3/3 PASS), CLAUDE.md |
| **local_verification_status** | verified |
| **verification_gaps** | not a git repo (loose collection), contains 4 independent git repos |

---

### Resource 3: test-frame

| Field | Value |
|-------|-------|
| **resource_id** | `res-testframe-003` |
| **resource_name** | test-frame |
| **resource_type** | test_framework |
| **path_or_reference** | D:\test-frame |
| **path_status** | exists |
| **runtime_layer** | evidence |
| **access_mode** | read_only |
| **risk_level** | high |
| **lifecycle_state** | registered |
| **promotion_status** | registered |
| **human_gate_required** | true |
| **next_phase** | R2 |

#### Allowed Actions

- read_directory_structure
- read README.md
- read ARCHITECTURE.md
- read PIPELINE.md
- run git_status --short
- validate test-fixture JSON

#### Forbidden Actions

- execute orchestrator
- execute aggregator
- execute attribution
- execute CLI
- run pytest
- run npm test
- execute playwright tests
- execute any test runner
- modify test results
- modify reports

#### Contract & Evidence

| Field | Value |
|-------|-------|
| **contract_mapping** | integration-contracts.md Appendix A4 |
| **evidence_requirements** | ARCHITECTURE.md, PIPELINE.md, test-results existence |
| **local_verification_status** | verified |
| **verification_gaps** | no test execution has been performed in this runtime, reports directory contains historical data only |

---

### Resource 4: CodeGraph

| Field | Value |
|-------|-------|
| **resource_id** | `res-codegraph-004` |
| **resource_name** | CodeGraph |
| **resource_type** | code_intelligence |
| **path_or_reference** | .codegraph/codegraph.db (agent-acceptance: 0 files indexed, dev-frame: 410 files, test-frame: 102 files) |
| **path_status** | exists |
| **runtime_layer** | intelligence |
| **access_mode** | read_only |
| **risk_level** | high |
| **lifecycle_state** | registered |
| **promotion_status** | registered |
| **human_gate_required** | true |
| **next_phase** | R4 |

#### Allowed Actions

- codegraph_status
- codegraph_search
- codegraph_context
- codegraph_callers
- codegraph_callees
- codegraph_impact
- codegraph_node
- codegraph_explore
- codegraph_files

#### Forbidden Actions

- reindex
- init new index
- delete index
- modify codegraph.db
- rebuild index

#### Contract & Evidence

| Field | Value |
|-------|-------|
| **contract_mapping** | integration-contracts.md Appendix A2 |
| **evidence_requirements** | codegraph_status output, file count per indexed project |
| **local_verification_status** | verified |
| **verification_gaps** | agent-acceptance index is empty (0 files), sqlite3 not available for direct query |

---

### Resource 5: Local Skills

| Field | Value |
|-------|-------|
| **resource_id** | `res-localskills-005` |
| **resource_name** | Local Skills |
| **resource_type** | skills_collection |
| **path_or_reference** | ~/.claude/skills/ (plus system prompt skill manifest) |
| **path_status** | exists (skills manifest in system prompt; physical path not verified) |
| **runtime_layer** | capability |
| **access_mode** | reference_only |
| **risk_level** | high |
| **lifecycle_state** | registered |
| **promotion_status** | registered |
| **human_gate_required** | true |
| **next_phase** | R5 |

#### Allowed Actions

- reference skill names
- reference trigger conditions
- reference risk classifications from skill-trigger-matrix.md

#### Forbidden Actions

- execute skill-installer
- execute skill-creator
- execute skill-evolver
- execute skill-auto-evolve
- execute skill-share
- execute connect-apps
- execute setup-pre-commit
- execute update-config
- auto-load any skill
- execute external skill code

#### Contract & Evidence

| Field | Value |
|-------|-------|
| **contract_mapping** | skill-trigger-matrix.md, external-skill-intake.md, skill-intake-record.schema.json |
| **evidence_requirements** | skill-trigger-matrix.md classification table |
| **local_verification_status** | needs_local_verification |
| **verification_gaps** | ~/.claude/skills/ physical directory not scanned, skill manifest from system prompt only, physical path integrity not confirmed |

---

### Resource 6: RD2100 Memory

| Field | Value |
|-------|-------|
| **resource_id** | `res-rd2100memory-006` |
| **resource_name** | RD2100 Memory |
| **resource_type** | memory_system |
| **path_or_reference** | C:\Users\RD\.codex\memories\RD2100-memory\ |
| **path_status** | exists |
| **runtime_layer** | memory |
| **access_mode** | read_only |
| **risk_level** | high |
| **lifecycle_state** | registered |
| **promotion_status** | registered |
| **human_gate_required** | true |
| **next_phase** | R6 |

#### Allowed Actions

- read MEMORY.md index
- read memory/*.md files (no secrets)
- read ACTIVE.md
- read MEMORY-CALL-GUIDE.md
- query agent-state.db (read-only, if accessible)

#### Forbidden Actions

- write memory/*.md
- write MEMORY.md
- write ACTIVE.md
- write agent-state.db
- execute recursive-improve
- execute dream-reflection
- execute memory-bridge write operations

#### Contract & Evidence

| Field | Value |
|-------|-------|
| **contract_mapping** | memory-architecture.md, integration-contracts.md Contract 8 |
| **evidence_requirements** | MEMORY.md index, ACTIVE.md |
| **local_verification_status** | verified |
| **verification_gaps** | agent-state.db not accessible, project-local memory (D--agent-acceptance) is empty, global memory is read-only in Phase 0-5 |

---

### Resource 7: Claude Plans/Rules

| Field | Value |
|-------|-------|
| **resource_id** | `res-clauderules-007` |
| **resource_name** | Claude Plans/Rules |
| **resource_type** | rules_config |
| **path_or_reference** | C:\Users\RD\.claude\rules\ + C:\Users\RD\.claude\CLAUDE.md + C:\Users\RD\.claude\ACTIVE.md |
| **path_status** | exists (referenced via CLAUDE.md; physical path not fully verified) |
| **runtime_layer** | governance |
| **access_mode** | reference_only |
| **risk_level** | medium |
| **lifecycle_state** | registered |
| **promotion_status** | registered |
| **human_gate_required** | true |
| **next_phase** | R5 |

#### Allowed Actions

- read CLAUDE.md (global)
- read ACTIVE.md
- reference rule names and priorities

#### Forbidden Actions

- modify CLAUDE.md
- modify ACTIVE.md
- modify .claude/rules/*
- modify .claude/projects/*/memory/*

#### Contract & Evidence

| Field | Value |
|-------|-------|
| **contract_mapping** | rules/README.md, AGENTS.md |
| **evidence_requirements** | CLAUDE.md presence, ACTIVE.md presence |
| **local_verification_status** | needs_local_verification |
| **verification_gaps** | C:\Users\RD\.claude\rules\ not scanned, project-level CLAUDE.md state unverified, physical path integrity not confirmed |

---

### Resource 8: agent-acceptance Native (scripts, workqueue, templates, runs)

| Field | Value |
|-------|-------|
| **resource_id** | `res-agentacceptance-008` |
| **resource_name** | agent-acceptance Native (scripts, workqueue, templates, runs) |
| **resource_type** | native_runtime |
| **path_or_reference** | D:\agent-acceptance (scripts/, agent-workqueue/, templates/, runs/) |
| **path_status** | exists |
| **runtime_layer** | execution |
| **access_mode** | read_only, human_gated |
| **risk_level** | high |
| **lifecycle_state** | registered |
| **promotion_status** | registered |
| **human_gate_required** | true |
| **next_phase** | R7 |

#### Allowed Actions

- read scripts (source review)
- read workqueue JSON definitions
- read templates
- git_status --short
- verify file existence

#### Forbidden Actions

- execute Run-Smoke.ps1
- execute Run-Batch.ps1
- execute Run-WorkQueue.ps1
- execute Run-AllQueues.ps1
- execute Run-QueueGroup.ps1
- execute Test-WorkQueue.ps1
- execute Write-Report.ps1
- consume workqueue (dispatch tasks)
- modify templates
- treat historical runs as current
- run any PowerShell script without explicit human approval

#### Contract & Evidence

| Field | Value |
|-------|-------|
| **contract_mapping** | integration-contracts.md Contracts 1-5, operating-model.md |
| **evidence_requirements** | scripts directory listing, agent-workqueue JSON definitions, runs/ directory listing |
| **local_verification_status** | verified |
| **verification_gaps** | no dry-run has been performed, scripts not tested, workqueue not consumed, 13M+6U dirty baseline present |

---

## Summary

| # | Resource ID | Name | Type | Layer | Risk | Access | Human Gate | Next Phase |
|---|-------------|------|------|-------|------|--------|:----------:|------------|
| 2 | res-devframe-002 | dev-frame | repository | orchestration | high | read_only | Y | R3 |
| 3 | res-testframe-003 | test-frame | test_framework | evidence | high | read_only | Y | R2 |
| 4 | res-codegraph-004 | CodeGraph | code_intelligence | intelligence | high | read_only | Y | R4 |
| 5 | res-localskills-005 | Local Skills | skills_collection | capability | high | reference_only | Y | R5 |
| 6 | res-rd2100memory-006 | RD2100 Memory | memory_system | memory | high | read_only | Y | R6 |
| 7 | res-clauderules-007 | Claude Plans/Rules | rules_config | governance | medium | reference_only | Y | R5 |
| 8 | res-agentacceptance-008 | agent-acceptance Native | native_runtime | execution | high | human_gated | Y | R7 |

**Gate Status**: All 8 resources at Gate 0 (registered). No resource has been promoted to candidate. All promotion to later stages requires human gate.

## Verification

- [x] All 8 resources registered with schema-conformant records
- [x] Every resource has: access_mode, risk_level, forbidden_actions, next_phase
- [x] All 7 high/critical resources have human_gate_required: true
- [x] No scripts executed in Batch R0-B
- [x] No MCP/hooks/memory modified in Batch R0-B
- [x] No write to C:\Users\RD
