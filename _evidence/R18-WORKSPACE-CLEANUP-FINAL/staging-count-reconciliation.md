# Staging Count Reconciliation

## Commits in Scope
| Commit | Description |
|--------|-------------|
| 104ac8b1 | Registry reconciliation, session artifacts, NUL removal (44 files) |
| f06ce965 | Closure evidence: deferred register, raw audit, remaining scripts (8 files) |
| 6022c187 | Updated evidence with raw audit files (8 files) |

## Count Discrepancy Explanation

| Source | Count | Explanation |
|--------|-------|-------------|
| git show --name-status | varies | R100/R059 rename entries counted per pair |
| git diff --stat | varies | Counts both sides of renames as separate entries |
| git diff --name-only | varies | Unique resolved paths |
| safety-report (per commit) | varies per commit | Based on --cached --name-only at staging time |

## Combined Files Across All 3 Commits
Total unique files committed: 67

## Post-Commit Workspace State
- Untracked (NEG-009 deferred): 17
- Untracked (secret-scan denied): 3
- Untracked (other): 3
- Total untracked: 23
- All untracked files are accounted for in deferred-files-register.yaml
