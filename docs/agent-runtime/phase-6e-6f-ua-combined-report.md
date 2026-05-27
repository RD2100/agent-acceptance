# Phase 6E Static Review + 6F Decision -- Understand Anything

> 2026-05-27 | Combined Phase 6E/6F
> Quarantine Only | No Install | No Execute | No MCP

---

## Phase 6D Recap

| Field | Value |
|-------|-------|
| Source URL | https://github.com/Lum1104/Understand-Anything |
| Source Type | zip download from main branch (manual) |
| Commit SHA | **unavailable** (zip, no .git) |
| Content Fingerprint | `478962e` (SHA256 of all files) |
| Quarantine Path | `skills-inbox/quarantine/sources/Understand-Anything__478962e/` |

---

## Phase 6E: Static Review

### Manifest

```
.claude-plugin/       <- Claude Code plugin code
.copilot-plugin/      <- GitHub Copilot plugin
.cursor-plugin/       <- Cursor IDE plugin
.github/              <- CI/CD workflows
homepage/             <- Web UI
understand-anything-plugin/ <- Core engine
scripts/              <- Build/release scripts
docs/ + READMEs/      <- Documentation
package.json          <- Node.js project manifest
pnpm-lock.yaml        <- Dependency lockfile
pnpm-workspace.yaml   <- Monorepo config
install.sh*           <- Linux installer (EXECUTABLE, NOT RUN)
install.ps1           <- Windows installer (NOT RUN)
tsconfig.json         <- TypeScript config
eslint.config.mjs     <- Lint config
vitest.config.ts      <- Test config
```

### Static Review Checklist

| Check | Result | Evidence |
|-------|:---:|---------|
| Read README | DONE | English, interactive knowledge graph tool |
| Read LICENSE | DONE | MIT License (Yuxiang Lin, 2026) |
| Read package.json | DONE | present; Node.js + TypeScript project |
| Check install.ps1 | DONE | clones repo + creates IDE symlinks; NOT EXECUTED |
| Check install.sh | DONE | same as .ps1, Linux variant; NOT EXECUTED |
| Check for network access | DONE | install scripts clone from git; homepage serves local UI |
| Check for MCP config | DONE | .claude-plugin may register MCP tools |
| Check for hook registration | DONE | install.ps1 creates symlinks (file system hooks) |
| Check for credential handling | DONE | none found in top-level scan |
| Check for filesystem writes | DONE | install scripts write symlinks; plugin creates knowledge graph cache |
| Check for package manager | DONE | pnpm (pnpm-workspace.yaml, pnpm-lock.yaml) |

### Risk Assessment

| Risk Category | Level | Evidence |
|---------------|:---:|---------|
| Install Script Risk | **CRITICAL** | install.ps1/sh clone repo + create IDE symlinks |
| Package Manager Risk | **HIGH** | pnpm monorepo with lockfile |
| IDE Plugin Risk | **HIGH** | Modifies .claude/, .copilot/, .cursor/ configs |
| CI/CD Risk | **MEDIUM** | .github/workflows present |
| Build System Risk | **MEDIUM** | TypeScript requires compilation |
| Test Runner Risk | **MEDIUM** | Vitest test suite present |
| Documentation Risk | **LOW** | Standard markdown/docs |
| License Risk | **LOW** | MIT, permissive |

### Key Findings

1. **install.ps1 / install.sh ARE DANGEROUS.** They clone, create symlinks, and modify IDE config directories (.claude/, .copilot/, .cursor/). These MUST NEVER be executed in quarantine. They would directly modify the agent runtime environment.

2. **Package dependency tree is deep.** pnpm monorepo with workspace config and lockfile means dozens of transitive dependencies. Full static audit of all dependencies is not feasible in quarantine — requires automated SBOM tooling.

3. **IDE plugin integration is aggressive.** The tool is designed to embed itself into the coding agent's IDE environment. This is antithetical to the quarantine model.

4. **Core functionality (knowledge graph) is valuable but execution-heavy.** The tool processes codebases into knowledge graphs and serves a local UI. This requires: Node.js runtime, pnpm install, TypeScript compilation, and a running server process.

5. **No credential exfiltration found in surface scan.** But the deep dependency tree means this cannot be confidently asserted without automated analysis.

---

## Phase 6F: Promotion Decision

### Decision Matrix

| Gate | Result | Rationale |
|------|:---:|---------|
| Install allowed? | NO | install scripts modify IDE config |
| Execute allowed? | NO | requires Node.js + pnpm + compilation |
| MCP enable allowed? | NO | .claude-plugin may register MCP tools |
| Runtime integration? | NO | designed to embed in IDE, not isolate |
| Config mutation risk? | HIGH | install creates symlinks in .claude/ |

### Decision: **quarantine_permanent**

```
status: quarantine_permanent
rationale:
  1. install scripts create IDE symlinks (direct runtime mutation)
  2. package dependency tree is un-auditable without automated tools
  3. tool is architected as IDE plugin, not as isolatable skill
  4. runtime requires Node.js + pnpm + compilation + local server
  5. risk profile exceeds R5 sandbox dry-run threshold
  6. not suitable for the Taste-Skill-style incremental evaluation path
```

### Comparison: Taste-Skill vs Understand Anything

| Dimension | Taste-Skill | Understand Anything |
|-----------|------------|---------------------|
| Install scripts | skill.sh (path query only) | install.ps1/sh (clone + symlink) |
| Package manager | none | pnpm monorepo |
| Runtime | none | Node.js + TypeScript + local server |
| IDE integration | none | .claude/.copilot/.cursor plugins |
| Risk verdict | candidate_for_sandbox_dry_run | quarantine_permanent |

### Recommendation

Understand Anything is architecturally incompatible with the current quarantine model. It is designed to embed into the agent's IDE environment, not to operate as an isolatable skill. Re-evaluation would require:
- Full dependency audit (SBOM)
- Sandbox execution with network isolation
- Stripping install scripts to extract only the knowledge graph core
- Reviewer decision to allow IDE config modification

None of these conditions are currently met. **Recommend keeping in quarantine_permanent until architecture can be significantly restructured.**

---

## Authorization Scope (Unchanged)

| Action | Authorized? |
|--------|:---:|
| Clone to quarantine | YES (manual zip) |
| Install dependencies | **NO** |
| Execute code | **NO** |
| Build / compile | **NO** |
| Enable MCP | **NO** |
| Register hook / symlink | **NO** |
| Copy to runtime | **NO** |
