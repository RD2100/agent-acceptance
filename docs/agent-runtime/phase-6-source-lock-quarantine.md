# Phase 6: Source Lock & Quarantine -- RD2100 Agent Runtime v2

> Batch D6, 2026-05-27
> Design phase. No implementation, no execution, no clone.
> Phase 6 is a REVIEW-ONLY phase. It does NOT install, run, or enable any skill.

## Overview

Phase 6 receives skills deferred from Phase 0-5 (disposition: `candidate` or `defer`) and performs the first deep-review step: locking the source at a specific commit, cloning into an isolated quarantine directory, and running static analysis. No code is ever executed during Phase 6.

### Phase 0-5 Handoff

The entry point to Phase 6 is a `SkillIntakeRecord` (Contract 6 from `integration-contracts.md`) with:
- `disposition`: `candidate` or `defer`
- `risk_level`: `medium`, `high`, or `critical`
- `declared_tools`: known tool list from Phase 0-5 classification
- `rationale`: why the skill was deferred

Phase 6 takes that record and produces a `SourceLockRecord` plus a quarantine artifact set.

---

## Phase 6A: Allowlist Verification

**Purpose**: Before any clone operation, verify the source URL against the clone allowlist.

### Step 6A.1: Extract source URL

From the `SkillIntakeRecord.source` field, extract the canonical source URL (GitHub repo, registered skill hub, or user-provided path).

### Step 6A.2: Check allowlist

Compare against `skills-inbox/allowlist.json` (or `allowlist.example.json` as template).

Allowed source URL patterns must match by:
- Full domain match (e.g., `github.com/anthropics/claude-code`)
- Or wildcard domain match (e.g., `github.com/anthropics/*`)
- Or explicit entry with reviewer approval

If the source is NOT on the allowlist:
- Set `SourceLockRecord.gate_decision` to `rejected_allowlist`
- Record reason in `static_review_status`
- End Phase 6 for this skill. Do NOT clone.

### Step 6A.3: Record allowlist decision

Log which allowlist entry matched (or rejection reason) into the SourceLockRecord.

---

## Phase 6B: Source Lock (Clone at Pinned Commit)

**Purpose**: Pin the skill source at a specific commit for deterministic review.

### Step 6B.1: Determine target commit

- If `SkillIntakeRecord` specifies a branch: resolve to its HEAD commit SHA.
- If user specifies a tag: resolve to its commit SHA.
- If user specifies a commit SHA directly: use it.
- Default: `main` or `master` branch HEAD.

### Step 6B.2: Create SourceLockRecord

See `schemas/agent-runtime/source-lock-record.schema.json` for full field definitions.

```json
{
  "record_id": "slr-001",
  "skill_name": "example-skill",
  "source_url": "https://github.com/example/skill-repo",
  "locked_commit_sha": "abc123def456",
  "cloned_to_quarantine_path": "D:\\agent-acceptance\\skills-inbox\\quarantine\\example-skill\\",
  "cloned_at": "2026-05-27T12:00:00Z",
  "static_review_status": "pending",
  "reviewer": "pending",
  "gate_decision": "pending"
}
```

### Step 6B.3: Clone into quarantine (FUTURE: this is design, not execution)

When Phase 6 is implemented:
- `git clone --no-checkout <source_url> skills-inbox/quarantine/<skill-name>/`
- `git checkout <locked_commit_sha>`
- Read-only after clone. No writes to the quarantine working tree.

### Step 6B.4: Verify clone integrity

- Verify the checked-out commit matches `locked_commit_sha`
- Verify no `.git` submodules reference external URLs not on the allowlist
- Verify no LFS objects pull from external sources that bypass the allowlist

---

## Phase 6C: Static Review Checklist

**Purpose**: Read-only analysis of the quarantined source. No execution of any kind.

### 6C.1: Structural Review

| Check | Method | Pass Condition |
|-------|--------|----------------|
| C1.1: File count | `ls -R` or Glob pattern | Reasonable file count (<500 files unless justified) |
| C1.2: Binary files | File header magic bytes scan | No executables (.exe, .dll, .so, .dylib) in source tree |
| C1.3: Obfuscated content | Entropy scan | No base64 blobs >1KB, no minified JS >10KB |
| C1.4: Hidden files | Check for `.` prefixed files beyond `.git` | No suspicious hidden files |
| C1.5: Symlinks | Check for symlinks pointing outside quarantine | No symlink escapes |

### 6C.2: Tool Declaration Review

| Check | Method | Pass Condition |
|-------|--------|----------------|
| C2.1: Declared tools match Phase 6+ policy | Read skill definition YAML/JSON | No tools in the `deferred` or `forbidden` categories from Phase 0-5 |
| C2.2: MCP registration intent | Grep for `mcp__`, `settings.json`, `MCP` | No MCP config mutation code |
| C2.3: Hook registration intent | Grep for `husky`, `lint-staged`, `git config core.hooksPath` | No hook registration code |
| C2.4: UI automation intent | Grep for `UI-TARS`, `computer-use`, `mouse_move`, `keyboard` | No UI/desktop automation code |
| C2.5: Shell execution | Grep for `exec(`, `execSync(`, `spawn(`, `subprocess`, `os.system` | Flagged for deeper review if found |

### 6C.3: Network & External Access Review

| Check | Method | Pass Condition |
|-------|--------|----------------|
| C3.1: Outbound HTTP | Grep for `fetch(`, `axios`, `requests.get`, `http.Client` | Flagged for deeper review if found |
| C3.2: External API keys | Grep for API key patterns, `process.env` | No hardcoded secrets |
| C3.3: File system writes | Grep for `writeFile`, `fs.write`, `open(..., 'w')` | Flagged for deeper review if found outside approved scope |
| C3.4: Package installation | Grep for `npm install`, `pip install`, `gem install` | CRITICAL: block if found in skill code (install scripts are separate concern) |

### 6C.4: Skill Manifest Integrity

| Check | Method | Pass Condition |
|-------|--------|----------------|
| C4.1: Has valid manifest | Check for `skill.md` or `SKILL.md` or manifest file | Must exist and be parseable |
| C4.2: Purpose matches declared | Compare manifest description with Phase 0-5 classification | No contradiction |
| C4.3: Version declared | Check for version string in manifest | Must be present |
| C4.4: Dependency list | Parse declared dependencies | All dependencies on allowlist or standard library |

### 6C.5: Security Hotspots

| Check | Method | Pass Condition |
|-------|--------|----------------|
| C5.1: Shell injection patterns | Grep for template-based shell commands without sanitization | No unsanitized command construction |
| C5.2: Path traversal | Grep for `../`, `path.join(userInput`, `os.path.join` with variables | No path traversal risk |
| C5.3: Eval patterns | Grep for `eval(`, `exec(`, `Function(` | CRITICAL: block |
| C5.4: Credential files | Grep for `.env`, `.pem`, `.key` references | Flagged for deeper review |

---

## Phase 6D: Quarantine Directory Policy

**Purpose**: Define where quarantined repos live, their permissions, and lifecycle.

### Directory Structure

```
skills-inbox/quarantine/
  README.md              <- Quarantine policy (this doc subset)
  <skill-name-1>/         <- One directory per quarantined skill
    .source-lock.json     <- Copy of SourceLockRecord
    repo/                 <- Git worktree (read-only)
    review/               <- Static review outputs
      static-review.md    <- Phase 6C checklist results
      tool-manifest.json  <- Extracted tool declarations
      risk-report.md      <- Overall risk assessment
    metadata/
      skill-intake.json   <- Copy of original SkillIntakeRecord
  <skill-name-2>/
    ...
```

### Permissions

| Subject | Permission | Rationale |
|---------|------------|-----------|
| Quarantine root (`skills-inbox/quarantine/`) | Agent can read, cannot write outside `review/` | Review outputs only |
| `repo/` directory | Read-only after clone | No source modification during review |
| `review/` directory | Agent can write review artifacts | Static analysis outputs |
| `metadata/` directory | Agent can write metadata copies | Record keeping |
| `.git/` inside `repo/` | Read-only | No git operations in quarantine |
| Files outside quarantine | No writes from quarantine context | Strict isolation |

### Lifecycle

```
[Clone] -> [Static Review] -> [Decision] -> [Archive | Promote | Delete]
  |             |                  |
  v             v                  v
 6B.3          6C               6F
```

**Clone** (Phase 6B): `git clone` into `repo/`, immediately lock read-only.

**Static Review** (Phase 6C): Run all checklist items, produce review artifacts in `review/`.

**Decision** (Phase 6F):
- **Archive**: Source is safe but not needed now. Keep read-only in quarantine, mark `archived`.
- **Promote**: Source passes all gates. Ready for Phase 7 installation pipeline. Mark `approved_for_install`.
- **Delete**: Source fails critical gates or is malicious. Remove from quarantine. Record rejection reason permanently.

---

## Phase 6E: Scope Boundary Enforcement

**Purpose**: Explicitly state what Phase 6 STILL forbids.

Phase 6 is a review-only phase. The following remain FORBIDDEN:

| Forbidden Action | Phase 0-5 Status | Phase 6 Status | When Allowed |
|------------------|:---:|:---:|--------------|
| `skill-installer install` | FORBIDDEN | FORBIDDEN | Phase 7+ |
| Enable/activate external skill | FORBIDDEN | FORBIDDEN | Phase 7+ |
| Register MCP servers | FORBIDDEN | FORBIDDEN | Phase 7+ |
| Modify MCP config (`settings.json`) | FORBIDDEN | FORBIDDEN | Phase 7+ |
| Register git hooks | FORBIDDEN | FORBIDDEN | Phase 7+ |
| Run external skill code | FORBIDDEN | FORBIDDEN | Phase 7+ (sandbox only) |
| Execute code from quarantine | N/A (no quarantine) | FORBIDDEN | NEVER (quarantine is read-only) |
| UI-TARS / real desktop automation | FORBIDDEN | FORBIDDEN | Reviewer-approved exceptions only |
| `mcp__computer-use__*` tools | FORBIDDEN | FORBIDDEN | Reviewer-approved exceptions only |
| Write to installed skills dir | FORBIDDEN | FORBIDDEN | Phase 7+ (approved skills only) |
| Package installation outside quarantine | FORBIDDEN | FORBIDDEN | Phase 7+ (project scope) |
| `bb_solidify_knowledge` / `bb_share_knowledge` | FORBIDDEN | FORBIDDEN | Phase 7+ |

### What Phase 6 Does Allow (New vs Phase 0-5)

| Allowed Action | Constraint |
|----------------|------------|
| Clone repos into quarantine | Allowlist-verified sources only |
| Read-only static analysis | AST scan, Grep, Read -- no execution |
| Write review artifacts to `review/` | Inside quarantine directory only |
| `git clone --no-checkout` | Allowlist-verified URLs only |
| `git checkout <sha>` | Pinned commit only, inside quarantine |
| Create SourceLockRecord | Per the schema contract |

---

## Phase 6F: Phase 7 Gate

**Purpose**: Define what must pass before a quarantined skill can move to Phase 7 (Installation Pipeline).

### Gate Checklist

A skill is eligible for Phase 7 promotion ONLY if ALL of the following pass:

| Gate | Condition | Check |
|------|-----------|-------|
| G1: Allowlist | Source URL on approved allowlist | Phase 6A output |
| G2: Source Lock | Commit SHA locked and verified | Phase 6B output |
| G3: Static Review | All 6C checklist items passed or flagged with acceptable rationale | Phase 6C output |
| G4: No Criticals | No C3.4 (package install), C5.3 (eval), or C5.4 (credentials) failures | Phase 6C hotspots |
| G5: No Forbidden Tools | No deferred/forbidden tool usage declared | Phase 6C tool review |
| G6: Manifest Valid | Skill manifest exists and is internally consistent | Phase 6C manifest check |
| G7: Reviewer Approval | Human reviewer has set `gate_decision` to `approved_for_install` | Explicit human action |
| G8: Quarantine Integrity | Quarantine has not been modified since clone | Checksum verification |

### Gate Decision States

| Decision | Meaning | Next Action |
|----------|---------|-------------|
| `approved_for_install` | All gates passed. Ready for Phase 7. | Move to Phase 7 pipeline |
| `rejected_permanent` | Failed critical gates. Unsafe. | Delete from quarantine. Record permanently. |
| `rejected_needs_fix` | Non-critical issues found. | Archive. Re-evaluate after source update. |
| `rejected_allowlist` | Source not on allowlist. | Do not clone. Record. |
| `pending` | Review in progress or not started. | Continue Phase 6 workflow. |
| `archived` | Safe but not needed now. | Keep read-only. May revisit later. |

---

## Data Flow: Phase 0-5 to Phase 6 to Phase 7

```
Phase 0-5                        Phase 6                          Phase 7
---------                        -------                          -------

SkillIntakeRecord ---------> SourceLockRecord ---------> InstallRecord
  .record_id                    .record_id                      (future contract)
  .skill_name                   .skill_name
  .source     ----------------> .source_url
  .disposition (defer/candidate) .locked_commit_sha
  .risk_level -----------------> .static_review_status
  .declared_tools               .reviewer
  .rationale                    .gate_decision

                                quarantine/
                                  repo/        (read-only clone)
                                  review/      (static analysis output)
                                  metadata/
                                    skill-intake.json
```

---

## References

- `external-skill-intake.md` -- Phase 0-5 intake pipeline and SkillIntakeRecord handoff
- `tool-policy.md` -- Phase 0-5 restrictions, Phase 6+ reference policy
- `skill-trigger-matrix.md` -- Deferred/forbidden skill classifications
- `integration-contracts.md` -- Contract 6 (SkillIntakeRecord), Contract 7 (ToolRiskRecord)
- `schemas/agent-runtime/source-lock-record.schema.json` -- SourceLockRecord JSON Schema
- `skills-inbox/quarantine/README.md` -- Quarantine directory policy
- `skills-inbox/allowlist.json` -- Clone allowlist (example in `allowlist.example.json`)

---

> **Remember**: Phase 6 is a DESIGN document. No skills have been cloned into quarantine.
> The quarantine directory and allowlist are empty templates. Implementation awaits Batch D7+.
