# GROUP-05 R3 Delta Note

This R3 pack supersedes the prior accepted GROUP-05 pack.

Reason for R3:
- The stricter rule `rerun_verified_at must be on or after reviewed_at` incorrectly blocked an existing completed run.
- The actual workflow semantics are: rerun happens first, reviewer may inspect it later.
- Therefore GROUP-05 now requires only that `rerun_verified_at` be on or after `created_at`, and that `rerun_summary` / `rerun_verified_at` stay paired.

Confirmed in this pack:
- targeted tests still pass
- full tests still pass
- `python tools/ai_guard.py evidence runs/t-chain-evidence-hardening-20260601` now passes
- malformed chain fail-closed coverage remains present
