# 6.4 Evidence Capture Readiness

**Task:** LIVE-DISPATCH-READINESS-REVIEW-A1
**Date:** 2026-06-12
**Sources:** `.ai/tasks/evidence-capture-standard-a2.yaml`, `schemas/agent-runtime/evidence-manifest.schema.json`, `scripts/build_evidence_pack.py`

## ECS-A2 Status

| Field | Value |
|---|---|
| Task ID | EVIDENCE-CAPTURE-STANDARD-A2 |
| Status | accepted_with_limitation |
| GPT Review Rounds | 5 (R1-R4 needs_revision, R5 accepted_with_limitation) |
| Test Results | 1260 passed, 0 failed |
| Commits | 6 (b474d4b -> ceb9ed0 -> 148c550 -> 442ad78 -> 13a7f4b -> c96de98) |

## Evidence Infrastructure Inventory

| Component | Path | Status |
|---|---|---|
| Evidence manifest schema | `schemas/agent-runtime/evidence-manifest.schema.json` | Active |
| Pack builder | `scripts/build_evidence_pack.py` (~1800 lines) | Active |
| Runtime evidence index schema | `schemas/agent-runtime/runtime-evidence-index.schema.json` | Active |
| Evidence pack linter | `scripts/evidence_pack_linter.py` | Active (in deny_paths) |
| Pack info section | file_count (int, required), zip_size_bytes (int, required), zip_sha256 (optional), content_sha256 (optional) | Schema-aligned |

## Key Capabilities

- **Two-pass ZIP build:** Pass 1 generates ZIP for size calculation, patches manifest with metadata, pass 2 rebuilds ZIP with patched manifest.
- **content_sha256:** Deterministic hash of all pack files except evidence-manifest.json. Solves the chicken-and-egg problem of zip_sha256 self-reference.
- **Runtime evidence indexing:** `runtime-evidence-index.json` maps scenario names to actual exit codes from hook output.
- **Top-level verdict eligibility:** Builder classifies packs as eligible_with_limitations, eligible, or not_eligible based on evidence completeness.

## GPT-Acknowledged Limitations (from ECS-A2 R5)

1. `startup_read_suggest_handoff` -- Startup read suggests handoff pattern not fully validated
2. `registered_closure_not_fully_clean` -- Registered closure state not fully clean
3. `zip_sha256_informational_not_self_referential` -- zip_sha256 is informational only due to circular dependency
4. `missing_git_show_for_13a7f4b` -- Missing git-show evidence for one commit

## Live Dispatch Evidence Capture Readiness

For a live dispatch event, the evidence capture system would need to:

1. **Capture dispatch packet** -- Router and dry-run scripts demonstrate this capability
2. **Record GPT response** -- CDP capture scripts exist (multiple variants)
3. **Build evidence pack** -- `build_evidence_pack.py` is proven (1260 tests pass)
4. **Generate manifest** -- Two-pass ZIP with content_sha256 is operational
5. **Submit for GPT review** -- Multiple submission scripts exist

## Findings

| # | Finding | Severity |
|---|---|---|
| F-6.4-1 | ECS-A2 accepted_with_limitation -- evidence standard is formally reviewed | PASS |
| F-6.4-2 | 1260 tests passing, zero failures | PASS |
| F-6.4-3 | Two-pass ZIP with content_sha256 solves circular dependency | PASS |
| F-6.4-4 | 4 GPT-acknowledged limitations are non-blocking for live dispatch | INFO |
| F-6.4-5 | All infrastructure components exist and are functional | PASS |

## Verdict

**Section verdict: PASS** -- Evidence capture infrastructure is mature and formally reviewed. The 4 GPT limitations are informational and do not block live dispatch evidence capture.
