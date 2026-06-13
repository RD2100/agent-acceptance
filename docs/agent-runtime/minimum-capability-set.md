# Minimum Capability Set -- RD2100 Agent Runtime

> Created: 2026-06-12
> Basis: Actual dispatch call chain analysis (Phase 0-5 local governance operations)
> Authority: Replaces fixed count threshold (>=20) in VM-004 with mode-based requirement

## Design Principle

The fixed threshold ">= 20 verified capabilities" is replaced with:
**"All capabilities required for the target operation mode must be verified."**

Two modes are defined. A capability is required for a mode only if the actual
dispatch call chain invokes it. Capabilities not in any required set are
classified as optional or de-scoped.

---

## Mode 1: Local Governance (current authorized operations)

Operations: read-only inspection, local test execution, TaskSpec management,
governance policy review, documentation work, pre-commit hook enforcement.

### Required capabilities (all must be verified):

| CAP ID | Name | Type | Rationale |
|--------|------|------|-----------|
| CAP-002 | rg / Grep / Read | search | Core file inspection |
| CAP-003 | JSON validation | validation | Schema/data validation |
| CAP-004 | Runtime Docs | docs | Governance documentation reference |
| CAP-005 | Runtime Rules | rules | Rule enforcement |
| CAP-006 | Negative Tests | fixtures | Test gate decisions |
| CAP-007 | Reviewer Playbooks | review | Review authority |
| CAP-010 | test-frame | evidence | Test orchestration |
| CAP-015 | Scripts | script | Source inspection only |
| CAP-016 | Hooks | hook | Pre-commit governance gate |
| CAP-018 | Sealed Files Manifest | governance | File integrity verification |
| CAP-019 | Hook Registration Script | governance | Hook management |
| CAP-028 | Sub-Agent Dispatch (SADP) | orchestration | Dispatch protocol reference |

**Count: 12 capabilities required, all local_static, all verified.**

### Not required (excluded from local governance mode):

| CAP ID | Name | Reason excluded |
|--------|------|-----------------|
| CAP-001 | CodeGraph | Code intelligence not needed for governance review |
| CAP-008 | Memory | Write-forbidden; read-only reference not dispatch-critical |
| CAP-011 | dev-frame | Execution forbidden (R3) |
| CAP-012 | Local Skills | Execution forbidden |
| CAP-013 | Memory (duplicate) | Write-forbidden |
| CAP-014 | WorkQueue | Consumption forbidden; definitions reference-only |
| CAP-017 | SourceLock | Phase 6 only |
| CAP-020~027 | External plugins | Not installed; not needed for local governance |
| CAP-029 | dev-frame-opencode Dispatch | Requires human gate; pilot-only |

---

## Mode 2: Controlled Pilot (future, requires human authorization)

Operations: Multi-agent dispatch via SADP, controlled external runtime invocation,
capability routing with evidence collection.

### Required capabilities (all Mode 1 + additional):

All Mode 1 capabilities (12), plus:

| CAP ID | Name | Type | Rationale |
|--------|------|------|-----------|
| CAP-014 | WorkQueue | workqueue | Task queue consumption for dispatch |
| CAP-029 | dev-frame-opencode Dispatch | orchestration | Worker dispatch |

(Note: CAP-028 is already included via Mode 1, not listed again.)

### Conditionally required (based on pilot scope):

| CAP ID | Name | Condition |
|--------|------|-----------|
| CAP-001 | CodeGraph | If code intelligence needed for dispatch planning |
| CAP-020 | coderabbit | If AI code review needed |
| CAP-021 | codex-security | If security scanning needed (already installed) |
| CAP-023 | github | If PR creation needed |

### Not required for pilot (de-scoped):

| CAP ID | Name | Reason |
|--------|------|--------|
| CAP-017 | SourceLock | Phase 6 only |
| CAP-022 | supabase | No Phase 0-5 database use case |
| CAP-024 | browser | No automated browsing use case |
| CAP-025 | superpowers | Methodology reference only |
| CAP-026 | linear | No task tracking use case |
| CAP-027 | notion | No knowledge management use case |

---

## VM-004 Threshold Update

**Old threshold:** >= 20 verified capabilities
**New threshold:** All capabilities in the required set for the target mode must be verified.

| Mode | Required verified count | Current verified in set | Status |
|------|------------------------|------------------------|--------|
| Local Governance | 12 | 12 | **PASS** |
| Controlled Pilot | 14 (12 from Mode 1 + CAP-014 + CAP-029) | 12 (CAP-014 degraded, usable_for_gate0=false) | **GAP** (CAP-014 usable_for_gate0=false) |

This replaces the fixed count threshold. The capability inventory passport
summary should report per-mode coverage rather than raw count.

---

## De-scoped capabilities (external plugins, not installed)

These capabilities remain in the inventory as `unknown` (not installed).
They are formally de-scoped from both Local Governance and Controlled Pilot
minimum required sets. CAP-001 and CAP-023 are conditionally required for
Controlled Pilot (see above) but not installed, so pilot tasks requiring
them must install the plugin first. If a future task requires any de-scoped
capability, the plugin must be installed and the passport re-verified.

CAP-020 (coderabbit), CAP-022 (supabase),
CAP-024 (browser), CAP-025 (superpowers),
CAP-026 (linear), CAP-027 (notion)

---

## Decision Record

- **Decision:** Replace fixed count threshold with mode-based requirement
- **Rationale:** Fixed count of 20 is meaningless without context. 12 verified
  local capabilities are sufficient for all authorized operations. External
  plugins that are not installed should not count toward or against a threshold.
- **Authority:** Human reviewer approval required for this document
- **Date:** 2026-06-12
