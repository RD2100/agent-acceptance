# Staging Count Reconciliation

## Discrepancy Explanation

| Source | Count | Explanation |
|--------|-------|-------------|
| `git diff --stat` | 238 | Counts both sides of renames as separate entries |
| `git show --name-status` | varies | R100/R059 entries counted once per rename pair |
| `git diff --cached --name-only` (pre-commit) | 229 | Unique resolved paths at staging time |
| `safety-report.json files_staged` | 229 | Matches --name-only count |

## Root Cause

The commit includes a large rename operation: `_projects/project-beta/` -> `_projects/dev-frame-writing/`.
Git interprets this as R100 (100% similarity rename) for most files.

- `git diff --stat` counts each rename as 2 changes (delete source + add destination)
- `git diff --name-only` resolves to the final path only (1 per rename)
- `safety-report.json` was generated from `--name-only` output, giving 229 unique paths

## Verification

The `diff.patch` in this evidence pack was generated with `git diff bc974d2f~1..bc974d2f`
and covers ALL changes including `hooks/sealed-files-manifest.json`.
Total diff headers in diff.patch: 238