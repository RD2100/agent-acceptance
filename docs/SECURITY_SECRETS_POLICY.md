# WriteLab / RD2100 Agent Runtime — Secrets Security Policy

> Version 1.0 | 2026-05-29
> Triggered by: DeepSeek API Key leak incident (agent-acceptance + writelab)
> Enforces: core-002 (No Secret Exposure)

---

## 1. File Classification

| File Type | Allowed Content | Action |
|-----------|----------------|--------|
| `.env` / `.env.local` | Real local keys | MUST be in .gitignore |
| `.env.example` / `env.example` | Placeholders ONLY | Git-tracked, mandatory secret scan |
| `README` / docs | Placeholders ONLY | Mandatory secret scan |
| CI yaml | Secret NAME only | Forbidden: plaintext values |
| Tests / fixtures | Fake keys (`sk-test-`, `sk-fake-`) | Forbidden: real provider keys |
| Packaging (`packaging/`, `dist/`) | No keys embedded | Pre-package scan required |
| Release artifacts | No keys | Pre-release scan required |
| Agent debug output (`tasks/*result*.txt`) | Must not be committed | .gitignore enforced |

---

## 2. Placeholder Format

All `.example`, `.template`, `.sample` files MUST use strongly invalid placeholders:

```env
# CORRECT:
DEEPSEEK_API_KEY=__REPLACE_WITH_YOUR_OWN_DEEPSEEK_API_KEY__
OPENAI_API_KEY=__REPLACE_WITH_YOUR_OWN_OPENAI_API_KEY__

# WRONG:
DEEPSEEK_API_KEY=sk-your-key-here
DEEPSEEK_API_KEY=
```

The placeholder must:
- Be obviously invalid as a real key
- Not match any real key pattern (length, prefix, character class)
- Contain the word `REPLACE` or `YOUR_OWN`

---

## 3. Key Lifecycle

| Phase | Requirement |
|-------|-------------|
| **Creation** | Named with project+environment |
| **Storage** | User profile directory or OS credential store, NEVER repo root |
| **Usage** | Loaded from env var or secure store at runtime, not hardcoded |
| **Rotation** | Rotated on leak, on team member departure, or every 90 days |
| **Revocation** | Immediate on suspected leak — before history cleanup |
| **Audit** | Provider console logs checked for anomalous usage after any leak |

---

## 4. Agent Hard Rules (External-Enforced)

1. Never write real API keys into repository files.
2. Never write real API keys into .env.example, config.example, README, tests, CI files, packaging files, or release artifacts.
3. Treat every file containing "example", "sample", "template", "packaging", "workflow", "docker", or "README" as secret-sensitive.
4. Before git add or git commit, secret scanning runs on staged diff.
5. If a suspected secret is found, STOP immediately. Report it.
6. If a secret has already been committed, REVOKE/ROTATE before cleanup.
7. Default answer to "should I scan?" is YES. Scanning is mandatory.

---

## 5. CI / Pre-Commit Gates

| Gate | Where | Action on Hit |
|------|-------|---------------|
| `sadp-audit.ps1` (enhanced) | pre-commit | Block commit if secret in staged diff |
| GitHub push protection | remote | Block push if secret detected |
| CI `sadp-audit` | PR / push | Fail check if secret in repo |
| Pre-release scan | release workflow | Block if artifact contains secret |

---

## 6. Leak Response SOP

| Time | Action |
|------|--------|
| 0-5 min | Stop agent, freeze CI/CD |
| 5-15 min | Revoke/rotate compromised key in provider console |
| 15-30 min | Check provider logs for anomalous usage |
| 30-60 min | git filter-repo clean history |
| 60+ min | Force push, notify collaborators, check forks |
| Complete | Re-scan: current tree, all branches, tags, releases, CI logs |
| Post-mortem | Write incident report, update this policy, add new detection rules |

---

## 7. Scan Commands (Reference)

```powershell
# Staged diff scan
git diff --cached | Select-String -Pattern "sk-[a-zA-Z0-9]{10,}"

# Full repo scan
gitleaks detect --source . --verbose

# History deep scan
trufflehog git file://. --only-verified

# CI: scan changed files only
gitleaks detect --source . --log-level=error --no-git
```