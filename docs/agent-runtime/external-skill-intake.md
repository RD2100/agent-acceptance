# External Skill Intake Policy -- RD2100 Agent Runtime v2

> Batch B1R, 2026-05-27
> Phase 0-5: reference and classify only. No install, no clone, no execution.

## Phase 0-5 Intake Pipeline

```
Discovery -> Record -> Classify -> Risk Review -> Defer
   |           |          |            |            |
   v           v          v            v            v
 skills-    SkillIntake  risk       ToolRisk     disposition:
 inbox/     Record       level      Record       reference_only
                                                  / candidate
                                                  / defer
                                                  / reject
```

## Dispositions (Phase 0-5 Only)

| Disposition | Meaning | Action |
|-------------|---------|--------|
| `reference_only` | Skill is documented for awareness. No evaluation performed. | Record name, source, purpose. Stop. |
| `candidate` | Skill looks useful and safe. Deserves deeper review in Phase 6. | Full SkillIntakeRecord. Defer evaluation. |
| `defer` | Skill may be useful but requires Phase 6 Source Lock & Quarantine. | Record rationale. Queue for Phase 6. |
| `reject` | Skill is unsafe, incompatible, or permanently out of scope. | Record rejection reason. Do not re-evaluate unless new evidence. |

## What Phase 0-5 Does NOT Allow

| Forbidden Action | Why | When Allowed |
|------------------|-----|--------------|
| `skill-installer install` | Requires Phase 6 Source Lock & Quarantine | Phase 6+ |
| Clone external skill repo | Supply chain risk | Phase 6+ (quarantine-only) |
| Run external skill code | Untrusted execution | Phase 6+ (sandbox-only) |
| Enable/activate external skill | Runtime modification | Phase 7+ (after full review) |
| Modify MCP config for skill | Configuration mutation | Phase 7+ (after full review) |
| Register hooks for skill | Behavioral side effects | Phase 7+ (after full review) |
| Write skill to installed skills dir | File system pollution | Never in Phase 0-5 |

## Stage 1: Discovery

Skills become known to the runtime through:

| Source | Action |
|--------|--------|
| User mentions a skill name | Create `reference_only` SkillIntakeRecord |
| System prompt lists a skill | Classify as `candidate` or `defer` |
| User explicitly requests installation | Create SkillIntakeRecord with `defer` + rationale |
| External skill files placed in `skills-inbox/external/` | Record, classify, do NOT execute |

## Stage 2: Record

Create a `SkillIntakeRecord` (see `integration-contracts.md`, Contract 6):

```json
{
  "record_id": "sr-XXX",
  "skill_name": "<name>",
  "source": "<where from>",
  "evaluated_at": "<ISO8601>",
  "disposition": "reference_only|candidate|defer|reject",
  "rationale": "<why>"
}
```

## Stage 3: Classify

Assign risk level:

| Risk | Criteria | Example |
|------|----------|---------|
| `low` | Read-only, no external calls, no state mutation | `caveman`, `codebase-search` |
| `medium` | Modifies project files, no external network | `claude-refactor`, `claude-md-docs` |
| `high` | Modifies git history, installs packages, network calls | `claude-git-helper`, `skill-installer` |
| `critical` | Can modify system config, MCP, hooks, credentials | MCP-modifying skills, credential-handling skills |

## Stage 4: Risk Review

Create a `ToolRiskRecord` (see `integration-contracts.md`, Contract 7) for each skill classified as `candidate` or higher.

Gate check (Phase 0-5 subset):
- P0: Does the skill description mention install, clone, or remote execution? If yes -> `defer` or `reject`.
- P1: Does the skill require tools forbidden in Phase 0-5? If yes -> `defer`.

## Stage 5: Defer

All skills not classified as `reference_only` or `reject` are deferred to Phase 6.

Phase 6 Source Lock & Quarantine will:
1. Clone the skill repo into an isolated quarantine directory (NOT into installed skills)
2. Run static analysis (read-only AST scan, no execution)
3. Produce a quarantine report
4. Still NOT install, enable, or register the skill

Phase 7+ (after full human-reviewed gate) may install approved skills.

## Inbox Management

```
skills-inbox/external/<skill-name>/
  SkillIntakeRecord.json     <- Stage 2 output
  evaluation/
    classification.md         <- Stage 3 output
  review/
    risk-review.md            <- Stage 4 output
```

No sandbox/ directory in Phase 0-5 (no execution = no sandbox needed).

## Candidate Registry (Phase 0-5 Classification)

> Batch J, 2026-05-27 | J-External-Intake-Agent
> 9 external GitHub candidate projects classified as reference-only metadata entries.
> No repositories have been cloned, accessed, or executed.

| # | skill_name | risk_level | disposition | rationale |
|---|-----------|------------|-------------|-----------|
| 1 | ECC | high | defer | Enables external code execution capability; unacceptable risk without Phase 6 Source Lock, Quarantine, and sandbox review. |
| 2 | Taste-Skill | medium | candidate | Skill evaluation framework useful for internal quality review pipeline; no network or system-level access concerns. |
| 3 | AnySearch Skill | high | defer | Integrates web search with network access; requires Quarantine network isolation and sandbox inspection before any activation. |
| 4 | AnySearch MCP Server | critical | reject | Modifies MCP configuration at runtime, which is permanently out of scope. MCP config mutation is a Phase 0-5 forbidden action with no path to approval. |
| 5 | Understand Anything | medium | candidate | Code understanding tool with no destructive capabilities; merits deeper review in Phase 6 for codebase search integration. |
| 6 | Anthropic Cybersecurity Skills | critical | reject | Executes security testing tools including potential exploit code; permanently out of scope for agent runtime regardless of Phase. |
| 7 | Andrej Karpathy Skills | medium | reference_only | AI/ML workflow skills documented for awareness; evaluated as reference-only due to domain specificity without urgent integration need. |
| 8 | UI-TARS Desktop | critical | reject | Desktop automation with computer-use and screen control; permanently out of scope -- equivalent to granting an agent unrestricted GUI access. |
| 9 | addyosmani-agent-skills-zh | high | defer | Agent skills collection (Chinese); broad scope with unknown tool surface requires Quarantine review before classification can be finalized. |

### Forbidden Actions Per Critical Item

These items are permanently rejected. The following actions are forbidden even in Phase 6+:

| skill_name | forbidden_actions |
|-----------|-------------------|
| AnySearch MCP Server | MCP config modification, MCP server registration, runtime configuration mutation, install into MCP settings |
| Anthropic Cybersecurity Skills | Security tool execution, exploit code execution, penetration testing via agent, network scanning, credential testing |
| UI-TARS Desktop | Computer-use tool activation, screen capture/control, keyboard/mouse emulation, GUI automation, desktop process interaction |

### Next Steps (Phase 6+ for Non-Rejected Items)

| skill_name | next_step |
|-----------|----------|
| ECC | Phase 6 Source Lock: quarantine clone, static AST scan, sandbox plan review (static only); no execution in Phase 6. |
| Taste-Skill | Phase 6: full SkillIntakeRecord, deep review for internal quality pipeline integration. |
| AnySearch Skill | Phase 6: quarantine with network isolation, review all outbound call patterns before any activation. |
| Understand Anything | Phase 6: evaluate codebase search integration fit, verify no destructive capabilities exist in tool surface. |
| Andrej Karpathy Skills | Remains reference_only indefinitely unless domain priority changes; no Phase 6 action planned. |
| addyosmani-agent-skills-zh | Phase 6: quarantine clone, categorize individual skills within collection, classify each sub-skill independently. |

## Current Inbox Status

- `skills-inbox/external/`: Contains candidate-index.md (Batch J classification metadata)
- Total classified (Batch J): 9
- Deferred to Phase 6: 3 (ECC, AnySearch Skill, addyosmani-agent-skills-zh)
- Rejected: 3 (AnySearch MCP Server, Anthropic Cybersecurity Skills, UI-TARS Desktop)
- Reference only: 1 (Andrej Karpathy Skills)
- Candidate: 2 (Taste-Skill, Understand Anything)

## References

- `integration-contracts.md` -- Contract 6 (SkillIntakeRecord), Contract 7 (ToolRiskRecord)
- `tool-policy.md` -- Phase 0-5 tool restrictions
- `skill-trigger-matrix.md` -- Trigger recommendations (not auto-triggers)
