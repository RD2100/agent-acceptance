# Evidence Generation Hygiene Standard

| Field    | Value                                      |
| -------- | ------------------------------------------ |
| Task     | UNIVERSAL-AGENT-WORKFLOW-STANDARD-A1       |
| Document | Evidence Generation Hygiene Standard       |
| Version  | 1.0.0                                      |
| Date     | 2026-06-11                                 |
| Status   | Active                                     |

---

## Purpose

Prevent recursive artifact pollution -- the chicken-and-egg problem where evidence generation creates new files that themselves need evidence.

When an agent generates an evidence pack to prove workspace closure, the generation process itself can introduce new untracked files (builder scripts, temporary outputs, session artifacts). If these files are not properly managed, they create a cascading pollution effect: the evidence requires more evidence, which creates more files, which requires more evidence. This standard defines rules to break that cycle.

---

## Core Rules

### 1. Use Pre-Existing Builder Tools

Evidence builder scripts SHOULD be pre-existing tracked tools when possible.

- If the project already has `_build_*.py` patterns or similar evidence generation utilities, reuse them.
- Do NOT create new builder scripts for every evidence pack unless the existing tools are genuinely insufficient.
- When evaluating whether to create a new builder, the threshold is: "The existing builder cannot produce the required output format" -- not "I prefer a different approach."

**Rationale:** Reusing tracked builders eliminates the builder-script-as-untracked-file problem entirely. A tracked, committed builder is a stable tool, not a session artifact.

### 2. Temporary Scripts Outside Repo

Temporary generation scripts SHOULD run outside the repository.

- Preferred location: workspace temp directory or system temp directory.
- If they must run inside the repo (e.g., due to path dependencies), they MUST be handled via one of the lifecycle options in Rule 3.
- Never assume a temporary script "doesn't count" as an untracked file. If `git status` can see it, it counts.

### 3. Builder Script Lifecycle

When a builder script is created inside the repo, it MUST follow one of these lifecycle paths:

| Option | Action | When to Use |
| ------ | ------ | ----------- |
| **A: Commit** | Commit the builder in the same commit as the evidence it generates | When the builder is reusable and adds value to the project |
| **B: Remove** | Delete the builder after generating evidence | When the builder is truly one-off and has no future use |
| **C: Register** | Register in `deferred-files-register.yaml` as `session_artifact_pending` | When the builder may be needed again in the current session |

**NEVER** leave a builder script untracked and unregistered. This is the most common form of recursive artifact pollution.

### 4. No New Untracked Without Registration

Generating an evidence pack MUST NOT create new untracked files without registering them.

- The evidence builder itself counts as a file that needs accounting.
- Any output files (logs, summaries, intermediate data) count as files that need accounting.
- Even temporary files in `.gitignore`-excluded directories should be mentioned in the register if they are relevant to the closure claim.

### 5. Generate After Last Commit

Final evidence MUST be generated AFTER the last commit, not before.

- The evidence must reflect the true post-commit state of the workspace.
- Generating evidence before the final commit causes numbers to disagree with post-commit reality.
- If additional commits are needed after evidence generation, the evidence MUST be regenerated.

**Sequence:**

```
1. Make all code changes
2. Stage and commit all changes
3. Run git status --porcelain (post-commit baseline)
4. Generate evidence pack (reflects post-commit state)
5. Submit evidence to GPT
```

**Never:**

```
1. Make all code changes
2. Generate evidence pack         <-- WRONG: pre-commit state
3. Stage and commit all changes   <-- commit changes the workspace state
4. Submit evidence to GPT         <-- evidence no longer matches reality
```

### 6. Single-Pass Generation

All evidence files MUST be generated in a single script pass.

- This ensures internal consistency: all files in the evidence pack report identical numbers.
- Never manually create evidence files that could disagree with each other.
- If the evidence pack includes a workspace status report, a deferred-files register, and a test summary, all three must be generated from the same `git status` snapshot.

**Consistency requirement:** If the workspace status report says "20 untracked files," the deferred-files register must list exactly 20 entries, and the test summary must reference the same 20-file state. Disagreement between evidence files is a critical defect.

### 7. Deny-List Awareness

Files on the git deny_list require special handling during evidence generation.

- NEVER include `secret-scan-output.txt` or other deny-listed files in git staging. The deny_list will block the commit.
- **Exception:** Files explicitly covered by `allow_paths` in `.ai/policy.yaml` may be staged (see DR-20260612-ALLOW-PATHS for authorized scope).
- Use `git reset HEAD -- <path>` to unstage deny-listed files before committing (unless covered by allow_paths).
- Include deny-listed files only in the ZIP evidence pack, not in git.
- The deferred-files register MUST categorize deny-listed files as `permanently_deferred_deny_path`.

---

## Anti-Patterns

The following behaviors are explicitly forbidden:

1. **Premature evidence** -- Creating the evidence pack before the final commit. Numbers will mismatch post-commit reality.
2. **Builder amnesia** -- Creating a builder script, generating evidence, then forgetting to register or remove the builder itself.
3. **Unregistered output** -- Running a builder that outputs files to the evidence directory without registering those output files.
4. **Manual evidence editing** -- Manually editing evidence files after generation. This breaks internal consistency between files in the pack.
5. **Deny-list staging** -- Including deny_list files in git staging, which blocks the commit and creates a stuck workspace state.
6. **Multi-pass inconsistency** -- Generating evidence files in multiple passes, where each pass sees a different workspace state.
7. **Evidence-before-cleanup** -- Generating evidence before workspace cleanup is complete, then performing cleanup that changes the workspace state.

---

## Failure Mode Examples

These examples are drawn from actual review cycles to illustrate common evidence generation failures.

### R18 Premature Evidence Generation

Evidence pack was generated before the final commit. The `git-status-after` file in the evidence pack showed the pre-commit state (with staged files), while the actual post-commit state was different. The register counts disagreed with the post-commit `git status` output, causing the GPT reviewer to reject the closure claim.

### R18 Unregistered Builder Script

The builder script `_build_workspace_cleanup_final.py` was created inside the repo to generate the evidence pack. After generation, the script itself remained as an untracked file. It was neither committed, removed, nor registered in the deferred-files register. This created a recursive problem: the evidence generation process created an artifact that itself needed to be accounted for in the evidence.

### R18 Accumulating Session Artifacts

Multiple rounds of evidence generation created accumulating session artifacts. Each round produced a new builder script and a new set of output files. By the third round, there were three builder scripts and three sets of outputs, all untracked. The deferred-files register only accounted for the most recent round, leaving the earlier artifacts unregistered.

### R18 Deny-List Staging Block

`secret-scan-output.txt` was included in `git add .` staging. The commit was blocked by the deny_list pre-commit hook. The file had to be manually unstaged with `git reset HEAD -- secret-scan-output.txt` before the commit could proceed. This caused a delay and introduced confusion about whether the file should be in the evidence pack or in git (answer: evidence pack only, never in git).

---

## Evidence Generation Checklist

Before submitting an evidence pack, verify:

- [ ] Evidence was generated AFTER the last commit
- [ ] All evidence files were generated in a single script pass
- [ ] Builder script is either committed, removed, or registered
- [ ] No deny-listed files are in git staging
- [ ] All output files from the builder are accounted for in the register
- [ ] Numbers are internally consistent across all evidence files
- [ ] No evidence files were manually edited after generation

---

## Builder Script Decision Tree

```
Need to generate evidence?
  |
  +-- Does a tracked builder already exist?
  |     |
  |     +-- YES --> Reuse it (Rule 1)
  |     |
  |     +-- NO --> Create builder OUTSIDE repo (Rule 2)
  |           |
  |           +-- Must run inside repo?
  |                 |
  |                 +-- NO --> Run from temp directory
  |                 |
  |                 +-- YES --> Choose lifecycle (Rule 3):
  |                       |
  |                       +-- A: Commit it (reusable)
  |                       +-- B: Remove it (one-off)
  |                       +-- C: Register it (session-pending)
  |
  +-- Generate evidence AFTER last commit (Rule 5)
  |
  +-- Single-pass generation (Rule 6)
  |
  +-- Verify no deny-list files in staging (Rule 7)
  |
  +-- Submit to GPT
```

---

## Related Documents

- [Workspace Closure Standard](workspace-closure-standard.md)
- [Universal Agent Workflow Standard](universal-agent-workflow-standard.md)
- [Verification Gates](verification-gates.md)
