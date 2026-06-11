# Workspace Closure Standard

| Field    | Value                                  |
| -------- | -------------------------------------- |
| Task     | UNIVERSAL-AGENT-WORKFLOW-STANDARD-A1   |
| Document | Workspace Closure Standard             |
| Version  | 1.0.0                                  |
| Date     | 2026-06-11                             |
| Status   | Active                                 |

---

## Purpose

Define acceptable workspace states at task completion. Prevent false "clean workspace" claims that erode trust between executor agents and reviewers.

Every closure claim must be verifiable by running `git status --porcelain` and comparing the output against the stated closure state. This standard eliminates ambiguity by defining exactly which states are acceptable, which are not, and what evidence is required to support each claim.

---

## Closure States

### 1. Clean Workspace (ideal, rare)

```yaml
clean:
  modified_tracked: 0
  untracked: 0
  description: "No outstanding changes of any kind"
```

A clean workspace means zero modified tracked files and zero untracked files. This state is ideal but rare in practice. Do not claim this state unless `git status --porcelain` returns completely empty output.

### 2. Registered Closure (acceptable)

```yaml
registered_closure:
  modified_tracked: 0
  untracked: "all listed in deferred-files-register.yaml"
  description: "All outstanding files are formally documented"
  requirements:
    - "Every untracked file appears exactly once in the register"
    - "Register categorizes each file (deferred, denied, pending)"
    - "Register total matches git status count exactly"
```

Registered closure is the practical standard for most task completions. It acknowledges that some files remain in the workspace but requires that every one of them is formally accounted for in the deferred-files register. The arithmetic must be exact: if `git status --porcelain` shows N untracked entries, the register must list exactly N entries.

### 3. Not Closed (unacceptable for completion claims)

```yaml
not_closed:
  conditions:
    - "Any modified_tracked files > 0"
    - "Any unregistered untracked files"
    - "Register count does not match git status count"
```

A workspace is not closed if any of the above conditions hold. Claiming completion while the workspace is in this state constitutes a closure violation.

---

## Mandatory Distinctions

The standard MUST distinguish the following terms. Using them interchangeably or loosely is a violation.

| Term | Definition | When to Use |
| ---- | ---------- | ----------- |
| **fully clean workspace** | Zero untracked files exist. `git status --porcelain` shows no `??` entries. | Only when literally true. Do not claim unless verified. |
| **registered closure** | All untracked files are documented in `deferred-files-register.yaml` with exact count match. | Standard acceptable completion state. |
| **dirty workspace** | Unregistered changes exist. Some files are untracked and not in the register. | Unacceptable. Must be resolved before claiming completion. |
| **permanently deferred deny_path fixtures** | Files that can NEVER be committed (e.g., secret-scan outputs, credential files). Always registered, never removed. | For files on the git deny_list that must persist in the workspace. |

### Precision Requirements

- Never say "workspace is clean" when you mean "workspace is in registered closure."
- Never say "all files accounted for" unless the register count exactly matches `git status` output.
- Never claim "0 untracked" while `git status --porcelain` shows `??` entries.

---

## Closure Checklist

Before claiming task completion, verify every item:

- [ ] `git status --porcelain` shows 0 modified tracked files
- [ ] All untracked files are listed in `deferred-files-register.yaml`
- [ ] Register total matches actual untracked count from `git status --porcelain`
- [ ] Tests pass (or test count is explicitly justified for docs-only tasks)
- [ ] Evidence pack built and submitted to GPT
- [ ] GPT verdict is ACCEPTED or ACCEPTED_WITH_LIMITATION

Each checklist item must be supported by evidence. A checkbox without supporting output is not valid.

---

## Anti-Patterns (Forbidden)

The following behaviors are explicitly forbidden and constitute closure violations:

1. **False clean claim** -- Claiming "clean workspace" when untracked files exist.
2. **False zero count** -- Claiming "0 untracked" while `git status` shows untracked entries.
3. **Register undercount** -- Registering fewer files than `git status` shows.
4. **Arithmetic mismatch** -- Stating "all accounted for" while the numbers do not add up.
5. **External modification blindness** -- Claiming closure while `PROJECT_REGISTRY.json` or other governance files have been externally modified and the changes are not reflected in tests or register.
6. **Builder script amnesia** -- Creating a builder script during evidence generation and then forgetting to register or remove the script itself.
7. **Premature closure** -- Declaring closure before the final commit has been made.

---

## Failure Mode Examples

These examples are drawn from actual review cycles to illustrate common closure failures.

### R18 Closure SLIM

Claimed 19 deferred files but `git status` showed 20. The missing entry was the third secret-scan output file. The register was off by one, invalidating the "all accounted for" claim.

### R18 Workspace Cleanup

Register showed 17 + 2 = 19 files, but the actual count was 17 + 3 = 20. The arithmetic in the register itself was internally inconsistent, and the discrepancy was not caught before closure was claimed.

### R18 External Registry Modification

`PROJECT_REGISTRY.json` was externally modified (reduced from 11 to 3 projects), which caused test failures. The closure claim did not account for this external change, and the test suite caught the inconsistency.

### R18 Unregistered Builder Script

A builder script (`_build_workspace_cleanup_final.py`) was created during the evidence generation process. The script itself was an untracked file that was neither committed, removed, nor registered in the deferred-files register. This created a recursive pollution problem: the evidence generation process created an artifact that itself needed evidence.

---

## Verification Protocol

To verify a closure claim, the reviewer (or GPT) must:

1. Run `git status --porcelain` independently.
2. Count modified tracked files (lines starting with `M`, `A`, `D`, `R`).
3. Count untracked files (lines starting with `??`).
4. Open `deferred-files-register.yaml` and count registered entries.
5. Compare: register count must equal untracked count exactly.
6. Confirm: modified tracked count must be 0.
7. If both conditions hold, the closure state is **Registered Closure**.
8. If untracked count is also 0, the closure state is **Clean Workspace**.
9. If either condition fails, the closure state is **Not Closed** and the completion claim is rejected.

---

## Related Documents

- [Evidence Generation Hygiene Standard](evidence-generation-hygiene.md)
- [Universal Agent Workflow Standard](universal-agent-workflow-standard.md)
- [Verification Gates](verification-gates.md)
