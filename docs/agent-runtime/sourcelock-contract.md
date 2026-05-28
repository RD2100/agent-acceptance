# SourceLock Contract v1.0

> Phase 6 | 2026-05-28
> Governs: external skill intake, quarantine, and activation

## 1. SourceLock Record

Every external skill that enters quarantine must have a SourceLock record:

\\\yaml
sourcelock_record:
  record_id: sl-XXX
  skill_name:
  source_url:
  source_hash:          # SHA256 of cloned repo at intake
  clone_date:
  quarantine_path:      # quarantine/clones/<skill-name>/
  risk_level: low | medium | high | critical
  scan_results:
    ast_scan: pass | warn | fail
    dependency_audit: pass | warn | fail
    secret_scan: pass | warn | fail
  disposition: pending | approved | rejected
  reviewer:
  review_date:
\\\

## 2. Quarantine Pipeline

\\\
External Skill URL
    |
    v
SourceLock Record created (skills-inbox/source-lock-requests/)
    |
    v
quarantine clone (quarantine/clones/<name>/)
    |
    v
Static scans (quarantine/scans/<name>/)
    |-- AST scan: tree-sitter parse all source files
    |-- Dependency audit: check imports/requires for known-risk patterns
    |-- Secret scan: grep for credential/token/key patterns
    |
    v
Quarantine Report (quarantine/reports/<name>.md)
    |
    v
Human review gate
    |
    v
Approved -> skills-inbox/external/<name>/ (classification)
Rejected -> quarantine/clones/<name>/ deleted
\\\

## 3. Forbidden in Quarantine

| Action | Status |
|--------|:------:|
| Execute code from quarantine | FORBIDDEN |
| Network access during scan | FORBIDDEN |
| Write to installed skills/ directory | FORBIDDEN |
| Modify MCP config | FORBIDDEN |
| Auto-approve high/critical risk skills | FORBIDDEN |

## 4. Quarantine Commands

\\\powershell
# Clone into quarantine (no network during scan phase)
git clone <url> quarantine/clones/<skill-name> --depth 1

# Static AST scan (read-only)
# Run tree-sitter or equivalent parser, output to quarantine/scans/

# Dependency audit
rg -n "require\(|import |from " quarantine/clones/<skill-name>/ > quarantine/scans/<skill-name>-deps.txt

# Secret scan
rg -n "(api_key|token|password|secret|credential|private.key)" quarantine/clones/<skill-name>/ > quarantine/scans/<skill-name>-secrets.txt
\\\

## 5. Active SourceLock Records

| ID | Skill | Status | Queued |
|----|-------|:------:|:------:|
| sl-001 | Taste-Skill | pending | skills-inbox/taste-skill/ |
| sl-002 | Understand-Anything | pending | skills-inbox/quarantine/sources/ |
| sl-003 | ECC | pending | request only |
| sl-004 | AnySearch-Skill | pending | request only |
| sl-005 | addyosmani-agent-skills-zh | pending | request only |
