# External Candidate Index -- RD2100 Agent Runtime v2

> Batch J, 2026-05-27 | J-External-Intake-Agent
> This index records classification decisions only. No repositories have been cloned, accessed, or executed.
> All entries are `reference_only`, `candidate`, `defer`, or `reject`.

## Candidate Registry

| # | skill_name | disposition | risk_level | description | forbidden_actions | next_step |
|---|-----------|-------------|------------|-------------|-------------------|-----------|
| 1 | ECC | defer | high | External code capability | -- | Phase 6: quarantine clone, static AST scan, sandbox plan review (static only); no execution in Phase 6. |
| 2 | Taste-Skill | candidate | medium | Skill evaluation framework | -- | Phase 6: full SkillIntakeRecord, deep review for quality pipeline integration. |
| 3 | AnySearch Skill | defer | high | Web search integration | -- | Phase 6: quarantine with network isolation, review outbound call patterns. |
| 4 | AnySearch MCP Server | reject | critical | MCP server for search | MCP config modification, MCP server registration, runtime configuration mutation, install into MCP settings | Permanently rejected. MCP config mutation is out of scope. |
| 5 | Understand Anything | candidate | medium | Code understanding tool | -- | Phase 6: evaluate codebase search integration, verify no destructive capabilities. |
| 6 | Anthropic Cybersecurity Skills | reject | critical | Security testing skills | Security tool execution, exploit code execution, penetration testing via agent, network scanning, credential testing | Permanently rejected. Security tool execution is out of scope. |
| 7 | Andrej Karpathy Skills | reference_only | medium | AI/ML workflow skills | -- | Remains reference_only indefinitely unless domain priority changes. |
| 8 | UI-TARS Desktop | reject | critical | Desktop automation | Computer-use tool activation, screen capture/control, keyboard/mouse emulation, GUI automation, desktop process interaction | Permanently rejected. Desktop automation is out of scope. |
| 9 | addyosmani-agent-skills-zh | defer | high | Agent skills collection (Chinese) | -- | Phase 6: quarantine clone, categorize individual skills, classify each sub-skill independently. |

## Disposition Summary

| disposition | count | projects |
|-------------|-------|----------|
| reference_only | 1 | Andrej Karpathy Skills (#7) |
| candidate | 2 | Taste-Skill (#2), Understand Anything (#5) |
| defer | 3 | ECC (#1), AnySearch Skill (#3), addyosmani-agent-skills-zh (#9) |
| reject | 3 | AnySearch MCP Server (#4), Anthropic Cybersecurity Skills (#6), UI-TARS Desktop (#8) |

## Risk Distribution

| risk_level | count | projects |
|------------|-------|----------|
| medium | 3 | Taste-Skill, Understand Anything, Andrej Karpathy Skills |
| high | 3 | ECC, AnySearch Skill, addyosmani-agent-skills-zh |
| critical | 3 | AnySearch MCP Server, Anthropic Cybersecurity Skills, UI-TARS Desktop |

## Verification Notes

- All 9 projects have been classified with metadata only.
- No `install`, `approved`, or `absorb` dispositions appear anywhere.
- All MCP-modifying, cybersecurity, and desktop-automation items are classified as `critical` + `reject`.
- No network access was performed during classification.
- No repositories were cloned, read, or executed.

## References

- `docs/agent-runtime/external-skill-intake.md` -- Full intake policy and Candidate Registry section
- `skills-inbox/external/README.md` -- Inbox workspace documentation
