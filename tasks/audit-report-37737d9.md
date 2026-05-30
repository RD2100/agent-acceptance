# Fix Audit Report — Draft JSON Schema Repair

> Generated: 2026-05-30 | Agent: Codex (primary)
> Commit: 37737d9 | Repo: D:\agent-acceptance

## Change Summary

**Problem**: commit f8687d3 introduced two draft JSON schemas with broken JSON:
- `//` line comments (not valid JSON)
- `$comment` key inserted in the WRONG position (inside `"properties": {` creating malformed structure)
- UTF-8 BOM causing Python `json.load` failures

**Fix**: Rebuilt both files from backup `.backup\simplify-20260530-100839\`:
- Removed all `//` comments
- Placed single `$comment` at top-level (valid JSON Schema 2020-12)
- No BOM (clean UTF-8)

## Files Changed

| File | + | - |
|------|---|---|
| `schemas/draft/boundary-envelope.schema.draft.json` | 66 | 115 |
| `schemas/draft/frame-manifest.schema.draft.json` | 66 | 155 |

## Verification

| Check | Result |
|-------|--------|
| `python json.load` | PASS (both files) |
| UTF-8 BOM | CLEAN (no BOM) |
| `sadp-audit.ps1` | PASS |
| `$comment` position | Top-level only |

## Reviewer Index

- **Changed files**: 2 (`schemas/draft/*.json`)
- **Critical paths**: `json.load()` parse, `sadp-audit.ps1` secret scan
- **Backup source**: `.backup\simplify-20260530-100839\`
- **Known gaps**: No TaskSpec for draft files (expected — drafts are not active)
- **Suggested review focus**: Verify JSON structural integrity, confirm no secrets, confirm BOM-free

## Request

Please perform:
1. Regression: `python -c "import json; json.load(open('schemas/draft/boundary-envelope.schema.draft.json')); json.load(open('schemas/draft/frame-manifest.schema.draft.json'))"`
2. Secret scan: `powershell.exe -ExecutionPolicy Bypass -File scripts/sadp-audit.ps1`
3. Diff review: `git diff HEAD~1`
4. Confirm backup integrity