# Tool Policy -- RD2100 Agent Runtime v2

> Batch B1R, 2026-05-27
> Phase-split policy: Phase 0-5 bootstrap is strict read-mostly.
> Phase 6+ policies are defined as future reference only.

---

## Bootstrap Phase 0-5 Policy (ACTIVE)

This section governs the current phase. All other sections are future reference.

### Permitted: Read-Only Tools

| Tool | Constraint |
|------|------------|
| `Read` | Cannot read `.env`, `*.key`, `*.pem`, tokens, credentials, SSH keys |
| `Glob` | File pattern matching only |
| `Grep` | Content search, regex patterns |

### Permitted: Code Intelligence (MCP)

| Tool | Constraint |
|------|------------|
| `codegraph_search` | Symbol search |
| `codegraph_context` | Symbol context with callers/callees |
| `codegraph_callers` | Inbound call analysis |
| `codegraph_callees` | Outbound call analysis |
| `codegraph_impact` | Change impact analysis |
| `codegraph_node` | Single symbol source/signature |
| `codegraph_explore` | Multi-symbol area survey |
| `codegraph_files` | Directory listing |
| `codegraph_status` | Index health check |


| Tool | Constraint |
|------|------------|

**FORBIDDEN in Phase 0-5**: , , , , , 

### Permitted: Task Management

| Tool | Constraint |
|------|------------|
| `TaskCreate` | Create new tasks |
| `TaskUpdate` | Update task status |
| `TaskList` | List current tasks |
| `TaskGet` | Get task details |

### Permitted: Agent Spawning

| Tool | Constraint |
|------|------------|
| `Agent` | Subagent spawning (foreground only for Phase 0-5) |
| `SendMessage` | Inter-agent communication |

### Permitted: Communication

| Tool | Constraint |
|------|------------|
| `AskUserQuestion` | Only when genuinely blocked after investigation |

### Permitted: Bash (Read-Only + Approved Docs-Only Writes)

| Command Pattern | Allowed? | Constraint |
|-----------------|:---:|------------|
| `test -d`, `test -f` | YES | Path existence checks |
| `ls`, `wc`, `head` | YES | Directory listing, file stats |
| `git status`, `git diff`, `git log` | YES | Read-only git |
| `git rev-parse`, `git branch`, `git remote -v` | YES | Read-only git |
| `mkdir -p` under approved scope | YES | Only for approved new doc directories |
| `echo` to new files under approved scope | YES | Only for approved Batch write tasks |
| `git status --short` (verification) | YES | Pre/post verification |

### FORBIDDEN: Phase 0-5

| Category | Examples | Reason |
|----------|----------|--------|
| **Package managers** | `npm install`, `npm ci`, `pip install`, `pip install -e .`, `yarn add` | No dependency changes |
| **Build tools** | `npm run build`, `npx tsc`, `python -m compileall` | No compilation (unless reviewer-approved validation) |
| **Test runners** | `pytest`, `npm test`, `jest` | No test execution (unless reviewer-approved validation command) |
| **MCP config mutation** | Any modification to MCP server settings | Configuration freeze |
| **Hook registration** | `git config core.hooksPath`, husky, lint-staged | No behavioral side effects |
| **External scripts** | `curl \| sh`, `Invoke-WebRequest \| Invoke-Expression` | Supply chain risk |
| **UI automation** | UI-TARS, computer-use MCP tools (`mcp__computer-use__*`) | Not in bootstrap scope |
| **Dangerous git** | `git reset --hard`, `git clean -f`, `git push --force`, `git commit`, `git stash` | Data loss risk, dirty baseline protection |
| **External skill execution** | Running any skill code from `skills-inbox/external/` | Untrusted code |
| **Remote execution** | `ssh`, `scp`, remote PowerShell | Not in bootstrap scope |

### Reviewer-Approved Validation Commands

The following commands are pre-approved for verification during Batch execution.
They do NOT constitute a general allowance for test/build commands.

| Command | Approved For | Batch |
|---------|-------------|-------|
| `git status --short` | Verifying no unexpected file changes | All batches |
| `test -f <path>` | Verifying approved files exist | All batches |
| `test -d <path>` | Verifying directory existence | All batches |

Adding new validation commands requires reviewer approval.

---

## Future: Phase 6+ Tool Policy (REFERENCE ONLY)

This section describes planned policy for later phases. It is NOT active in Phase 0-5.

### Phase 6: Source Lock & Quarantine
- Package managers allowed in quarantine workspaces only (git worktrees)
- External skill repos may be cloned into quarantine (NOT installed, NOT executed)
- Static analysis tools permitted (read-only AST scan)

### Phase 7+: Full Capability
- Package installation within project scope
- Test execution (pytest, npm test)
- Build verification (tsc, compile)
- Approved skills may be installed via `skill-installer`
- MCP configuration may be modified with reviewer approval

### Project Implementation Tasks
- Full build/test/install policies are defined separately
- This bootstrap policy only covers the agent runtime bootstrap phases
