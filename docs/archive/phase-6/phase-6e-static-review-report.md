# Phase 6E Static Security Review Report

> Date: 2026-05-27
> Scope: Taste-Skill only
> Mode: static review only; no install, no execute, no import

## Executive Assessment

`human_required`

Taste-Skill is source-locked in quarantine at commit `3c7017d636c3a4aad378433ea6d0cfa6c921da4a`. Static review found no package manifest, no dependency lockfile, no postinstall hook, no MCP configuration file, and no hook registration code. The repository is primarily a collection of `SKILL.md` prompt/instruction files plus media assets and research notes.

The source is not safe for direct runtime installation because it contains install instructions, multiple strong agent behavior directives, optional external-service/MCP references, external image URLs, and prompt content that could conflict with RD2100 Runtime v2 frontend/routing rules. It is suitable only for constrained reviewer-supervised sandbox dry-run consideration.

## Source Summary

| Source | Commit | Quarantine Path | Review Result |
|---|---|---|---|
| Taste-Skill | `3c7017d636c3a4aad378433ea6d0cfa6c921da4a` | `skills-inbox/quarantine/sources/Taste-Skill__3c7017d/` | `human_required` |
| Understand Anything | N/A | N/A | `blocked_network_unavailable` |

## Static Checks

| Check | Result | Notes |
|---|---|---|
| LICENSE present | yes | MIT license present. |
| README present | yes | Includes `npx skills add` install instructions; not authorized for this runtime. |
| Package manifest present | no | No `package.json`, `pyproject.toml`, `requirements.txt`, `setup.py`, or lockfile found. |
| Install scripts | yes, documentation only | `README.md` and `CHANGELOG.md` include `npx skills add` commands. These are not executed. |
| Executable script | present | `skill.sh` is a local registry lookup script; not executed. |
| Postinstall/prepare script | no | No package manifest found. |
| MCP config file | no | Research/skill docs mention MCP conceptually; no local MCP config was found. |
| Hook registration code | no | No `.git/hooks` registration code found in static scan. |
| Secrets/token handling | no direct credential handling found | Search hits were documentation/general text, not credential access code. |
| Network indicators | present in docs/assets | README badges, `picsum.photos`, Google Stitch links, C2PA metadata in images; no code execution observed. |
| Binary/media files | present | `.png` and `.webp` media assets present; mark as media/binary review note. |
| Prompt injection risk | medium/high | Multiple SKILL.md files contain strong behavior directives that could override local style/runtime policies if copied wholesale. |
| Runtime loadable | no | Quarantine only. Not copied to runtime path. |

## Key Findings

| Severity | Finding | Evidence | Required Control |
|---|---|---|---|
| HIGH | Direct install must remain forbidden | README includes `npx skills add` install commands. | Do not run install commands; keep `install_allowed=false`. |
| HIGH | Prompt/rule conflict risk | Multiple `SKILL.md` files contain strong UI/code-generation directives. | Do not copy wholesale into AGENTS.md/rules; only compare/select under reviewer gate. |
| MEDIUM | Optional MCP/external-service references | `stitch-skill` and research docs mention MCP/external services. | MCP remains disabled; no config mutation. |
| MEDIUM | External URL use in design guidance | Several skills reference `picsum.photos` or external image/service URLs. | Any future sandbox dry-run must declare network/media policy first. |
| LOW | Media/binary assets present | `.png` and `.webp` files found. | Treat as non-executable media; do not load into runtime automatically. |

## Forbidden Action Check

| Check | Result |
|---|---|
| Installed package or skill? | no |
| Executed `skill.sh`? | no |
| Ran tests/build/examples? | no |
| Imported external code? | no |
| Enabled MCP? | no |
| Registered hook? | no |
| Copied source into runtime docs/rules? | no |
| Wrote memory? | no |
| Read secrets? | no |

## Recommendation

- Taste-Skill: `candidate_for_sandbox_dry_run`
- Understand Anything: `blocked_until_network_available`
- Allow direct install/runtime enablement: no
- Allow Phase 6F promotion decision: yes

