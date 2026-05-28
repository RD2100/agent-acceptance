# Runtime Bootstrap -- Instantiation Guide

## Step 1: Run Bootstrap

```powershell
cd D:\your-project
powershell -ExecutionPolicy Bypass -File D:\agent-acceptance\templates\runtime-bootstrap\bootstrap.ps1
```

Auto-detects project name from directory or git remote. Override: `.\bootstrap.ps1 -ProjectName "my-app" -ProjectRoot "D:\my-app" -Platform Both`

## Step 2: Verify

```powershell
cat AGENTS.md | Select-String "{{"   # Must return nothing
dir rules\                           # 8 files
dir schemas\                         # 18 files
cat docs\agent-runtime\capability-inventory.md | Select-String "^## \d+\."  # >= 10
```

## Step 3: Register Project Resources

1. Open `docs/agent-runtime/capability-inventory.md`
2. Add entries #11+ for project-specific resources
3. Set `Status: proposed`, submit to reviewer, change to `Status: approved` after sign-off

## Step 4: Configure Platform Assets

Claude Code: Copy hook drafts from agent-acceptance/hooks/ (4 audit-only drafts). Create project-specific sealed-files-manifest.json.
Codex: Enable plugins as needed. Run `codex plugin list` and compare against capability inventory.

## Step 5: Submit for Reviewer

```markdown
# Bootstrap Report -- PROJECT_NAME
- Bootstrap v1.0
- Assets: 8 rules, 18 schemas, AGENTS.md, 10 capabilities, tool policy, 5 reviewer docs, 30 fixtures
- Pending: register project capabilities (#11+), configure platform assets, reviewer sign-off
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `{{PROJECT_NAME}}` in AGENTS.md | Re-run with -Force |
| Rules not copied | Ensure running from project root |
| File exists errors | Use -Force |