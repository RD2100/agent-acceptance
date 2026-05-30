# Workflow Skill Deployment — 2026-05-30

> Deployed: `~/.codex/skills/agent-acceptance/` + `~/.agents/skills/agent-acceptance/`

## Structure

```
agent-acceptance/
  SKILL.md              — Trigger: @go, SADP formal workflow
  agents/openai.yaml    — UI metadata
  references/
    sadp-protocol.md    — Full SADP: Gate 0 → Execute → Audit
    p0-rules.md         — P0 hard stops
    security-rules.md   — Secret safety rules
  scripts/
    sadp-audit.ps1      — Pre-commit secret scanner
```

## Trigger

- `@go` command
- User asks for formal workflow / SADP / audit trail

## Coverage

| Environment | Path |
|-------------|------|
| Codex | `~/.codex/skills/agent-acceptance/` |
| Claude Code | `~/.agents/skills/agent-acceptance/` |