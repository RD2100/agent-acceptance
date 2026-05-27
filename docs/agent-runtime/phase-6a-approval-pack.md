# Phase 6A: Approval Pack -- RD2100 Agent Runtime v2

> Batch D6, 2026-05-27
> Review-only phase. This document defines the human approval workflow BEFORE any clone operation.
> Phase 6A does NOT authorize any clone. It only prepares the approval pack.

## Overview

Phase 6A is the human-review gate that sits between Phase 0-5 (classification) and Phase 6B (clone into quarantine). Before any git clone operation can occur, a human reviewer must:

1. Receive a `SourceLockRequest` form the requesting party
2. Verify the source URL against the clone allowlist
3. Assess the declared risk level and rationale
4. Approve or reject the clone request
5. If approved, record approval fields and queue for Phase 6B

No clone, no install, no execution happens during Phase 6A.

---

## Phase 6A Approval Workflow

### Step 1: Receive SourceLockRequest

A `SourceLockRequest` is filed into `skills-inbox/source-lock-requests/` by the requesting party. This can be a human developer, a planning agent, or the output of Phase 0-5 deferral. The request contains:

- `request_id`: unique identifier
- `skill_name`: the skill being requested for quarantine review
- `source_url`: canonical source URL (GitHub repo, skill hub, etc.)
- `proposed_commit_sha`: empty at filing time (Phase 6B resolves this)
- `requested_by`: who filed the request
- `request_date`: ISO8601 timestamp
- `risk_level`: `medium` | `high` | `critical` (from Phase 0-5 classification)
- `reason`: why this skill deserves Phase 6 review
- `constraints`: any reviewer-imposed constraints on the clone/review

### Step 2: Allowlist Verification

The human reviewer compares the `source_url` against entries in `skills-inbox/allowlist.json`. See **Allowlist Review Criteria** below.

If the source is NOT on the allowlist:
- Set `reviewer_decision` to `rejected_allowlist`
- Record rejection reason
- Phase 6 ends for this request. Do NOT proceed to clone.

### Step 3: Risk Assessment

The reviewer evaluates the declared `risk_level` and `reason` against the Phase 0-5 classification:

| Risk Level | Reviewer Action |
|------------|-----------------|
| `medium` | Confirm classification is consistent with Phase 0-5 tool analysis. Flag if underestimated. |
| `high` | Require explicit justification. Confirm all constraints are specified. |
| `critical` | Requires secondary reviewer unless pre-authorized by policy. Maximum constraints apply. |

### Step 4: Approve or Reject

The human reviewer sets `reviewer_decision` to one of:

| Decision | Meaning | Next Action |
|----------|---------|-------------|
| `approved` | SourceLockRequest is approved. Ready for Phase 6B clone. | Queue for Phase 6B. |
| `rejected_allowlist` | Source URL not on allowlist. | End Phase 6. Archive request. |
| `rejected_risk` | Risk level too high or unmitigated. | Return to requester with rationale. |
| `rejected_needs_info` | Request is incomplete. | Return to requester for clarification. |

### Step 5: Record Approval

If approved, the reviewer fills in:

- `reviewer_decision`: `approved`
- `approved_by`: reviewer name or identifier
- `approved_date`: ISO8601 timestamp of approval
- `constraints`: any additional constraints imposed by the reviewer

### Step 6: Queue for Phase 6B

The approved `SourceLockRequest` moves to `skills-inbox/quarantine/` processing queue. Phase 6B will:
1. Determine the target commit SHA
2. Clone into `skills-inbox/quarantine/<skill-name>/repo/`
3. Lock the clone read-only
4. Begin static review (Phase 6C)

---

## Human Approval Fields

Every `SourceLockRequest` must include these reviewer-completed fields before Phase 6B:

| Field | Description | Required | Filled By |
|-------|-------------|----------|-----------|
| `reviewer_decision` | `approved`, `rejected_allowlist`, `rejected_risk`, `rejected_needs_info` | Yes | Human reviewer |
| `approved_by` | Name or identifier of the approving reviewer | If `approved` | Human reviewer |
| `approved_date` | ISO8601 timestamp of approval decision | If `approved` | Human reviewer |
| `constraints` | Array of constraints imposed on the clone/review | Optional | Human reviewer |

### Constraint Types

Reviewers may impose constraints in the `constraints` array:

| Constraint | Description |
|------------|-------------|
| `max_depth: N` | Maximum clone depth (shallow clone) |
| `allowed_refs: [...]` | Allowed git refs for checkout |
| `require_signed_commits` | Require GPG-signed commits on the locked SHA |
| `require_secondary_review` | A second reviewer must also approve before Phase 6B |
| `no_submodules` | Do not clone git submodules |
| `no_lfs` | Do not fetch LFS objects |
| `block_network_in_review` | No outbound network access during Phase 6C static review |
| `manual_diff_required` | Human must review the full diff between locked commit and previous release |

---

## Allowlist Review Criteria

The human reviewer checks the `source_url` against `skills-inbox/allowlist.json`. Each allowlist entry defines:

### Matching Rules

| Pattern Type | Example | Match Behavior |
|-------------|---------|----------------|
| Exact URL | `https://github.com/anthropics/claude-code` | Matches only this exact URL |
| Wildcard domain | `https://github.com/anthropics/*` | Matches any path under `github.com/anthropics/` |
| Wildcard org | `https://github.com/trusted-org/skills/*` | Matches repos under `trusted-org/skills/` |

### Review Criteria Per Entry

| Criterion | Question | Reject If |
|-----------|----------|-----------|
| Source authenticity | Is this source known and verifiable? | Source URL is a lookalike, typo-squatting, or untraceable |
| Reason validity | Is the approval reason still current? | Allowlist entry is stale or superseded |
| Constraints match | Do the entry constraints align with the request risk? | Entry allows depth 3 but request needs depth 5 without justification |
| Reviewer currency | Is the approving reviewer still authorized? | Reviewer is no longer active or authorized |

### Allowlist Edge Cases

| Scenario | Action |
|----------|--------|
| Source not on allowlist, but trusted organization | Add to allowlist first, then approve request. Never bypass. |
| Source matches wildcard, but repo is new/unreviewed | Apply `require_review_before_clone` constraint. |
| Source was on allowlist but entry is now expired | Reject until allowlist entry is renewed. |
| Multiple wildcard entries match | Apply the most restrictive matching entry's constraints. |

---

## Gate to Phase 6B

**Before any clone operation, the following must be signed off:**

| Gate | Condition | Signed Off By |
|------|-----------|---------------|
| GA1: SourceLockRequest exists | Valid JSON in `skills-inbox/source-lock-requests/` | Requester |
| GA2: Allowlist verified | Source URL matches an approved allowlist entry | Human reviewer |
| GA3: Risk assessed | `risk_level` is confirmed appropriate by reviewer | Human reviewer |
| GA4: Reviewer decision recorded | `reviewer_decision` = `approved` | Human reviewer |
| GA5: Constraints set | Any additional constraints are documented | Human reviewer |
| GA6: Phase 6B queue | Approved request is ready for Phase 6B processing | System/Agent |

**All six gates must pass before Phase 6B clone begins.** Failure of any gate stops the pipeline.

---

## EXPLICIT: No Clone in Phase 6A

**Phase 6A does NOT authorize any clone operation.** It is a paperwork and human-review phase only.

The following remain **FORBIDDEN** during Phase 6A:

- `git clone` of any kind
- `git fetch` or `git remote add`
- Downloading or copying skill source files
- Any form of code execution
- Any form of package installation
- Any MCP configuration change
- Any hook registration

Phase 6A produces exactly one artifact: a signed-off `SourceLockRequest` with `reviewer_decision: "approved"`. Nothing more.

---

## Data Flow: Phase 6A within the Pipeline

```
Phase 0-5                        Phase 6A                     Phase 6B-6F
---------                        --------                     -----------

SkillIntakeRecord --------> SourceLockRequest --------> SourceLockRecord
  (defer/candidate)         (human review gate)           (clone + static review)

                             skills-inbox/
                               source-lock-requests/       quarantine/
                                 <request_id>.json           <skill-name>/
                                                               repo/ (read-only)
                                                               review/
```

---

## References

- `phase-6-source-lock-quarantine.md` -- Full Phase 6 design (6A-6F)
- `external-skill-intake.md` -- Phase 0-5 intake pipeline
- `skills-inbox/allowlist.json` -- Clone allowlist (template in `allowlist.example.json`)
- `skills-inbox/source-lock-requests/example-source-lock-request.json` -- Request template
- `integration-contracts.md` -- Contract 6 (SkillIntakeRecord), Contract 7 (ToolRiskRecord)
- `reviewer-playbook.md` -- Human reviewer procedures

---

> **Phase 6A is the human gate. No clone happens here. Only approval paperwork.**
