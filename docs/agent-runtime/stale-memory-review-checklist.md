# Stale Memory Review Checklist -- R6

> Batch Y (R6), 2026-05-27
> Checklist for reviewing memory entries for staleness and conflict.

## Pre-Review

- [ ] Memory path recorded
- [ ] access_mode confirmed as read_only

## Staleness Check

| Check | Question | Status |
|-------|----------|:---:|
| Last reviewed | When was this memory last reviewed/updated? | |
| Age | How many days since last review? | |
| Source freshness | Has the source (filesystem, rules, code) changed since? | |
| Path validity | Are all paths referenced in the memory still valid? | |
| Claim accuracy | Do the claims in the memory match current state? | |

## Conflict Check

| Check | Question | Status |
|-------|----------|:---:|
| Filesystem | Does memory contradict current filesystem (Test-Path, ls)? | |
| Git | Does memory contradict git status/log? | |
| Rules | Does memory contradict current rules/*.md? | |
| Contracts | Does memory contradict current integration-contracts.md? | |
| Phase | Does memory reference a phase that has since advanced? | |

## Risk Assignment

| Stale Risk | Condition |
|:---:|-----------|
| high | >30 days, or path-dependent, or project-specific, or known contradiction |
| medium | 7-30 days, general applicability, no known contradiction |
| low | <7 days, structural/pointer, verified against current state |

## TTL Assignment

- [ ] TTL recommendation recorded
- [ ] Expiry action defined (re-read, mark stale, archive)

## Verification Gaps

- [ ] All gaps recorded (path not accessible, tool unavailable, content not exhaustively reviewed)
- [ ] No gap omitted or marked as pass without evidence

## Decision

- [ ] All entries have stale_risk, conflict_check, ttl_recommendation
- [ ] No entry has write_allowed=true or used_as_fact=true
- [ ] No memory contradiction ignored
- [ ] Result: pass_to_review / needs_revision
