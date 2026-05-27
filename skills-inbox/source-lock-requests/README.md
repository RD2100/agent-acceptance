# Source Lock Requests

> Phase 6A artifact directory -- RD2100 Agent Runtime v2
> Created: 2026-05-27

## Purpose

This directory holds `SourceLockRequest` records that are awaiting human reviewer approval before any git clone operation into quarantine.

A `SourceLockRequest` is filed when:
- A skill reaches Phase 0-5 disposition `candidate` or `defer`
- A human developer or planning agent requests Phase 6 Source Lock & Quarantine review
- A previously rejected skill is resubmitted with new evidence

## Current Status

**Empty.** No SourceLockRequest records have been filed as of 2026-05-27.

The Phase 6 pipeline has not yet received any skills deferred from Phase 0-5. The `skills-inbox/external/` directory is also empty.

## Process

```
[Request Filed] --> [Allowlist Check] --> [Reviewer Decision] --> [Queue Phase 6B]
       |                   |                      |                      |
       v                   v                      v                      v
  request_id.json    Matches pattern      approved                Clone into
  placed here        in allowlist.json    / rejected              quarantine/
```

### Step 1: Request Filed

A `SourceLockRequest` JSON file is placed in this directory. Use `example-source-lock-request.json` as the template.

### Step 2: Allowlist Check

A human reviewer compares the `source_url` in the request against the clone allowlist at `skills-inbox/allowlist.json`. See `docs/agent-runtime/phase-6a-approval-pack.md` for full criteria.

### Step 3: Reviewer Decision

The human reviewer fills in:
- `reviewer_decision`: `approved`, `rejected_allowlist`, `rejected_risk`, or `rejected_needs_info`
- `approved_by`: reviewer identifier (if approved)
- `approved_date`: ISO8601 timestamp (if approved)
- `constraints`: any additional constraints

### Step 4: Queued for Phase 6B

If `reviewer_decision` is `approved`, the request is ready for Phase 6B clone into `skills-inbox/quarantine/<skill-name>/repo/`. Phase 6B will:
1. Determine the target commit SHA
2. Clone into quarantine (read-only)
3. Create a `SourceLockRecord`
4. Begin static review (Phase 6C)

## Rejected Requests

Rejected requests remain in this directory for audit trail. The rejection reason is recorded in the JSON file. Rejected requests must NOT be cloned -- the rejection decision is final unless a new request is filed with changed circumstances.

## File Naming Convention

```
source-lock-requests/<request_id>.json
```

Where `<request_id>` follows the pattern: `slrq-YYYYMMDD-NNN` (e.g., `slrq-20260527-001`).

## EXPLICIT: No Clone in Phase 6A

**No git clone operation occurs during Phase 6A.** This directory is for paperwork only -- it holds human-review records that authorize (or deny) a future clone in Phase 6B.

The following are FORBIDDEN in this phase:
- `git clone`
- `git fetch`
- Downloading or copying source files
- Any code execution
- Any package installation

Phase 6A output is exactly one approved `SourceLockRequest` JSON file per skill. Nothing more.

## References

- `../docs/agent-runtime/phase-6a-approval-pack.md` -- Full Phase 6A approval workflow
- `../docs/agent-runtime/phase-6-source-lock-quarantine.md` -- Full Phase 6 design
- `../skills-inbox/allowlist.json` -- Clone allowlist
- `example-source-lock-request.json` -- Request JSON template (in this directory)
