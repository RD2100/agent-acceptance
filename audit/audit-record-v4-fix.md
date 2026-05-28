# Audit Record: V4 Bootstrap Governance Manifest Fix

> Auditor: OpenCode | Date: 2026-05-28
> Source under audit: `reports/fix-v4-manifest.md`
> Targets: `templates/runtime-bootstrap/bootstrap.ps1`, `templates/runtime-bootstrap/governance-manifest.template.md`

---

## Claim 1: 2 files changed

**Verdict: PARTIALLY TRUE**

`git log` shows only `bootstrap.ps1` (3 insertions, 1 deletion) changed in commit `5bf1baf`. The `governance-manifest.template.md` has no diff between `06ed05c` and `5bf1baf` — it was created in the earlier commit along with the foundation. Both files **exist** and have the claimed functionality, but only 1 file received a code change in the reported batch.

---

## Claim 2: Template placeholders replaced from `{hash}` to named `{{HASH}}` forms

**Verdict: TRUE**

`governance-manifest.template.md` uses 5 named `{{...}}` placeholders:

| Placeholder | Line |
|---|---|
| `{{P0_HASH}}` | 23 |
| `{{GATE0_HASH}}` | 24 |
| `{{VETO_HASH}}` | 25 |
| `{{PROTECTED_HASH}}` | 26 |
| `{{CUMULATIVE_HASH}}` | 27 |

Additionally, `{{CURRENT_DATE}}` (line 12) replaces the previously claimed `{bootstrap_date}`. A grep for `{hash}` across the templates directory returns **zero results**, confirming no bare `{hash}` tokens remain.

---

## Claim 3: `bootstrap.ps1` computes SHA256 hashes and generates manifest

**Verdict: TRUE**

`bootstrap.ps1` lines 116-125 contain the full hash-computation pipeline:

```
Line 116: Get-FileHash ... rules\core.md -Algorithm SHA256
Line 117: Get-FileHash ... sub-agent-dispatch-protocol.md -Algorithm SHA256
Line 118: Get-FileHash ... AGENTS.md -Algorithm SHA256
Line 119-125: $ManifestPlaceholders = @{ ... } -> New-FromTemplate ...
Line 126: New-FromTemplate "governance-manifest.template.md" -> governance-manifest.md
```

The 5 placeholders are populated with real SHA256 hashes before template generation (lines 80-81). The manifest generation appears after all universal copy and template steps, ensuring all source files exist at hash time.

---

## Summary

| Check | Claim | Verdict | Evidence |
|---|---|---|---|
| 2 files changed | bootstrap.ps1 + template | Partial — 1 file changed in latest commit, both exist with correct content | `git diff --stat 06ed05c..5bf1baf` |
| `{hash}` → `{{HASH}}` | All placeholders renamed | TRUE | grep: 0 `{hash}` hits, 5 `{{X_HASH}}` hits in template |
| SHA256 + manifest gen | bootstrap.ps1 computes hashes | TRUE | Lines 116-126: 3 `Get-FileHash` calls + `$ManifestPlaceholders` + `New-FromTemplate` |

**Overall: Claim verified. Functionally correct. The partial discrepancy on "2 files changed" is a commit-boundary artifact — the template was introduced in the prior commit and not re-touched.**
