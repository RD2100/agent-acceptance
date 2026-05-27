# Phase 6B Handoff -- RD2100 Agent Runtime v2

> Handoff prepared: 2026-05-27
> Handoff agent: K2 Handoff Agent
> Receiving agent: Phase 6C Security Review Agent (or human reviewer)

---

## 1. Handoff Purpose

This document is the handoff package for the next executor agent or human reviewer continuing Phase 6C. All Phase 0-5 and Phase 6A/6B planning work is complete. Phase 6C is blocked pending human input.

No clone, no install, and no execution has been performed. Phase 6C requires explicit per-project source URLs and clone approval from a human reviewer before any git operation.

---

## 2. Must Read First

Read these files in order before proceeding:

1. `AGENTS.md` -- Runtime bootstrap, hard stops, Phase 0-5 boundary
2. `docs/agent-runtime/runtime-v2-final-status.md` -- Runtime v2 completion status across all phases
3. `docs/agent-runtime/phase-6-source-lock-quarantine.md` -- Full Phase 6 design (6A through 6F): allowlist verification, source lock, static review checklist, quarantine directory policy, scope boundary enforcement, Phase 7 gate
4. `docs/agent-runtime/phase-6a-approval-matrix.md` -- Phase 6A human reviewer decisions (5 projects: 2 approved for planning, 3 deferred)
5. `docs/agent-runtime/phase-6b-source-lock-plan.md` -- Phase 6B planning output (2 source lock plans created, pending human review)
6. `skills-inbox/allowlist.draft.json` -- Draft allowlist with reviewer decisions applied (2 `planning_approved`, 3 `deferred`)
7. `skills-inbox/source-lock-plans/INDEX.md` -- Source lock plan registry (2 plans created, 3 projects deferred)

---

## 3. Current Decisions Table

All 9 external projects from `skills-inbox/external/candidate-index.md`, with their current Phase 6A disposition and Phase 6B status. No clone has been authorized for any project.

| # | Project | Risk | Phase 6A Disposition | Phase 6A Decision | Phase 6B Status |
|---|---------|------|----------------------|-------------------|-----------------|
| 1 | ECC | high | defer | **defer** | DEFERRED. Re-evaluate after medium-risk cycle completes. |
| 2 | Taste-Skill | medium | candidate | **approve_for_source_lock_planning** | Plan created (SLP-Taste-Skill-20260527). Pending human review. |
| 3 | AnySearch Skill | high | defer | **defer** | DEFERRED. Re-evaluate after medium-risk cycle and network isolation patterns established. |
| 4 | AnySearch MCP Server | critical | reject | **reject** (permanent) | N/A. Permanently rejected. MCP config mutation is out of scope. |
| 5 | Understand Anything | medium | candidate | **approve_for_source_lock_planning** | Plan created (SLP-Understand-Anything-20260527). Pending human review. |
| 6 | Anthropic Cybersecurity Skills | critical | reject | **reject** (permanent) | N/A. Permanently rejected. Security tool execution is out of scope. |
| 7 | Andrej Karpathy Skills | medium | reference_only | **reference_only** (no action) | N/A. Remains reference_only indefinitely unless domain priority changes. |
| 8 | UI-TARS Desktop | critical | reject | **reject** (permanent) | N/A. Permanently rejected. Desktop automation is out of scope. |
| 9 | addyosmani-agent-skills-zh | high | defer | **defer** | DEFERRED. Re-evaluate after medium-risk cycle and sub-skill categorization methodology defined. |

### Disposition Summary

| Disposition | Count | Projects |
|-------------|-------|----------|
| `approve_for_source_lock_planning` | 2 | Taste-Skill (#2), Understand Anything (#5) |
| `defer` | 3 | ECC (#1), AnySearch Skill (#3), addyosmani-agent-skills-zh (#9) |
| `reject` (permanent) | 3 | AnySearch MCP Server (#4), Anthropic Cybersecurity Skills (#6), UI-TARS Desktop (#8) |
| `reference_only` | 1 | Andrej Karpathy Skills (#7) |

Only projects #2 (Taste-Skill) and #5 (Understand Anything) have active Phase 6B source lock plans and are eligible for Phase 6C. All other projects are deferred, rejected, or reference-only.

---

## 4. Phase 6C Preconditions

**ALL of the following must be true before any git clone operation proceeds in Phase 6C.**

1. **Source URL supplied by human for each approved project.** The `source_url` field is currently `"<url not provided in candidate index>"` in both `allowlist.draft.json` and the source lock plan JSONs. A human reviewer must provide the canonical source URL (GitHub repo URL) for Taste-Skill and Understand Anything.

2. **Source URL verified against allowlist.draft.json entry.** The human-supplied URL must be verified against the corresponding entry in `skills-inbox/allowlist.draft.json`. The entry's `source_url` field must be updated from the placeholder to the verified URL. The `clone_allowed` flag must remain `false` until Phase 6C explicit approval.

3. **Explicit human approval for clone_to_quarantine (per project).** Separate Phase 6C clone approval is required for each project. Phase 6A/6B approval only authorized source lock planning -- it did NOT authorize a clone. The human reviewer must set a per-project clone approval flag before the Phase 6C agent may execute `git clone`.

4. **Quarantine path prepared (skills-inbox/quarantine/<project>/repo/).** The quarantine directory structure must be created and permission-verified before clone. The planned paths are:
   - `skills-inbox/quarantine/Taste-Skill/repo/`
   - `skills-inbox/quarantine/Understand-Anything/repo/`
   After creation, the agent's access must be verified as read-only for the `repo/` subdirectory. See `phase-6-source-lock-quarantine.md` Phase 6D for the full quarantine directory policy and permission matrix.

5. **Phase 6C Security Review agent launched (read-only pre-clone check).** Before any clone, the Phase 6C agent must perform a pre-clone security read of the target source URL (browser/open the repo page, not clone). This is a read-only look-at-the-repo-in-browser check: verify the repo exists, is not empty, is not archived/deleted, and has a plausible commit history. No `git clone` or `git ls-remote` or any network-level tool access to the repo. This is a human-eyeball-equivalent check only.

---

## 5. Phase 6C Must Not Do

The Phase 6C executor agent must NOT perform any of the following. These are permanent Phase 6 scope boundaries.

- NO install (npm, pip, yarn, gem, cargo, or any package manager)
- NO test execution (no `npm test`, `pytest`, `go test`, or any test runner)
- NO build (no `npm run build`, `make`, `cmake`, or any compilation)
- NO MCP enable or config modification (no changes to `settings.json`, `mcpServers`, or any MCP configuration file)
- NO hook registration (no `husky install`, `pre-commit install`, `git config core.hooksPath`, or any hook setup)
- NO source promotion (quarantine -> installed skills directory; promotion is Phase 7+)
- NO skill activation (no `skill-installer install`, no enabling/exposing any quarantined skill to the agent runtime)
- NO code execution from quarantine (quarantine is read-only; no `node`, `python`, `bash` on quarantined files)
- NO submodule or LFS clone that bypasses the allowlist (see Phase 6B integrity checks in `phase-6-source-lock-quarantine.md`)
- NO git operations beyond `clone --no-checkout` and `checkout <sha>` within the quarantine directory

---

## 6. Expected Phase 6C Outputs (Per Project)

For each project that receives Phase 6C clone approval, the executor agent must produce all of the following outputs. Outputs are written to `skills-inbox/quarantine/<project>/review/`.

1. **SourceLockRecord JSON** (`review/source-lock-record.json`) -- Completed per the schema in `schemas/agent-runtime/source-lock-record.schema.json`. Must include: `record_id`, `skill_name`, `source_url`, `locked_commit_sha`, `cloned_to_quarantine_path`, `cloned_at`, `static_review_status`, `reviewer`, `gate_decision`.

2. **Static review plan (checklist filled)** (`review/static-review-checklist.md`) -- The 22-item checklist from Phase 6C of `phase-6-source-lock-quarantine.md` (sections 6C.1 through 6C.5), filled per project. Each check item must have a result and evidence reference.

3. **Quarantine path record** (`review/quarantine-path-record.json`) -- Documents the exact quarantine path used, creation timestamp, permission verification result, and the quarantine policy version referenced.

4. **Clone command audit log** -- Records the exact `git clone` and `git checkout` commands executed, their stdout/stderr, exit codes, and the full resolved commit SHA. Saved to `review/clone-audit-log.txt`.

5. **Post-clone git status** -- Output of `git status`, `git log -1 --oneline`, and `git remote -v` captured after clone and pinned checkout. Verifies the working tree is at the expected commit. Saved to `review/post-clone-git-status.txt`.

6. **SourceLockReport draft** (`review/source-lock-report.md`) -- A structured human-readable report summarizing: the clone operation, commit lock, static review checklist results, any flagged findings, and the preliminary gate recommendation. This is a DRAFT pending human reviewer sign-off.

---

## 7. Handoff Signature Block

```
Handoff prepared: 2026-05-27
Runtime v2 Phase 0-5/6A/6B: COMPLETE
Phase 6C: BLOCKED pending source URLs and clone approval

Phase 6B Deliverables:
  - Source lock plans: 2 (Taste-Skill, Understand Anything)
  - Plan files: skills-inbox/source-lock-plans/Taste-Skill.plan.json
               skills-inbox/source-lock-plans/Understand-Anything.plan.json
  - Allowlist: skills-inbox/allowlist.draft.json (v0.1.1-reviewer-decisions-applied)
  - Deferred projects: 3 (ECC, AnySearch Skill, addyosmani-agent-skills-zh)
  - Rejected projects: 3 (AnySearch MCP Server, Anthropic Cybersecurity Skills, UI-TARS Desktop)
  - Reference-only: 1 (Andrej Karpathy Skills)

Next human action required:
  1. Supply source URLs for Taste-Skill and Understand Anything
  2. Verify URLs against allowlist.draft.json entries
  3. Review and approve Phase 6B source lock plans
  4. Issue Phase 6C clone authorization (per project)
  5. Prepare quarantine directories

Receiving agent (Phase 6C) action upon unblock:
  - Read this handoff document in full
  - Read all "Must Read First" files
  - Confirm all 5 Phase 6C Preconditions are met
  - Then proceed with clone and static review per project authorization

Handoff agent signature: K2 Handoff Agent, Batch D6, 2026-05-27
```

---

## 8. References

- `AGENTS.md` -- Runtime bootstrap and Phase 0-5 boundary
- `docs/agent-runtime/phase-6-source-lock-quarantine.md` -- Full Phase 6 design
- `docs/agent-runtime/phase-6a-approval-pack.md` -- Phase 6A human approval workflow
- `docs/agent-runtime/phase-6a-approval-matrix.md` -- Phase 6A reviewer decisions
- `docs/agent-runtime/phase-6b-source-lock-plan.md` -- Phase 6B planning summary
- `skills-inbox/allowlist.draft.json` -- Clone allowlist draft
- `skills-inbox/source-lock-plans/INDEX.md` -- Source lock plan registry
- `skills-inbox/source-lock-plans/Taste-Skill.plan.json` -- Taste-Skill source lock plan
- `skills-inbox/source-lock-plans/Understand-Anything.plan.json` -- Understand Anything source lock plan
- `skills-inbox/external/candidate-index.md` -- Full 9-project candidate registry
- `schemas/agent-runtime/source-lock-record.schema.json` -- SourceLockRecord JSON Schema
- `docs/agent-runtime/integration-contracts.md` -- Contract 6 (SkillIntakeRecord), Contract 7 (ToolRiskRecord)
