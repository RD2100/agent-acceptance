## Human Gate Checklist

**Task ID:** PRE-EXECUTION-READINESS-SNAPSHOT-A1
**Generated:** 2026-06-12
**Purpose:** Items requiring explicit human confirmation before entering real multi-agent / multi-GPT pilot execution

**Current dispatch status: HUMAN_REQUIRED (per HANDOFF.md)**

### Authorization Gates

Each item below requires explicit YES/NO from the workspace owner. Default is NO for all items.

---

**1. Live Dispatch Authorization**

- [ ] Allow `live_dispatch_authorized: true` in TaskSpec
- [ ] Define authorized scope (which projects, which repos)
- [ ] Define duration limit for authorized dispatch window
- [ ] Define rollback/abort conditions
- [ ] Confirm: NO default authorization

Current status: `live_dispatch_authorized: false` in all TaskSpecs.

---

**2. `opencode run` Authorization**

- [ ] Allow `opencode run` for task execution
- [ ] Define which TaskSpecs may be dispatched via opencode
- [ ] Define model/resource limits
- [ ] Confirm: NO default authorization

Current status: Not authorized. No opencode runs have been executed.

---

**3. devframe-control-plane External Execution**

- [ ] Allow devframe-control-plane to execute external commands
- [ ] Define which external systems are accessible
- [ ] Define network/filesystem access boundaries
- [ ] Confirm: NO default authorization

Current status: RISK_REGISTER entry R-01 (mitigated_verified). No external execution authorized.

---

**4. dev-frame-opencode External Execution**

- [ ] Allow dev-frame-opencode to execute external commands
- [ ] Define scope of external execution
- [ ] Define monitoring/audit requirements
- [ ] Confirm: NO default authorization

Current status: RISK_REGISTER entry R-02. Not executed.

---

**5. Paper Workflow Real Execution**

- [ ] Allow paper workflow to process real paper content
- [ ] Allow external transmission of paper data
- [ ] Allow live CDP integration
- [ ] Define paper content boundaries and classification
- [ ] Confirm: NO default authorization (current = NOGO)

Current status: PAUSED per PAPER_WORKFLOW_HANDOFF.md. Real paper = NOGO. Recovery requires 8-step re-authorization process. `.ai/paper_authorization.json` has NOT been read.

---

**6. Authorization Scope Definition**

For each authorized capability above, define:

- [ ] Authorized projects/repos
- [ ] Allowed write paths
- [ ] Duration limit
- [ ] Maximum concurrent dispatches
- [ ] Audit/logging requirements

---

**7. Rollback / Abort Conditions**

- [ ] Define what triggers automatic abort
- [ ] Define human override mechanism
- [ ] Define data preservation on abort
- [ ] Define post-abort notification path

---

### Explicit Prohibitions

The following are explicitly prohibited without separate human authorization:

- Default authorization of any kind
- Implicit authorization through task execution
- Authorization by inference from prior task completion
- Batch authorization without per-item confirmation
- Authorization of paper workflow through non-paper TaskSpec completion
- Modification of `.ai/paper_authorization.json` without explicit instruction

### Current Readiness Level

This checklist documents PRE-EXECUTION readiness only. No items are currently authorized. The repository is in a clean, reviewable state suitable for:

- Read-only inspection and report generation
- TaskSpec status triage (advisory only)
- Governance policy review
- Test suite execution (local, no external calls)

The repository is NOT in a state suitable for:

- Live multi-agent dispatch
- External runtime execution
- Paper workflow processing
- Any operation requiring network access to external services
