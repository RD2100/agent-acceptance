# AA-1 Policy Summary

## TERMINAL_STATE_POLICY.md

6 valid terminal states: accepted_done, human_required, blocked_unresolvable, technical_failure, max_rounds_reached, high_risk_required.

Critical rule: terminal=false → agent MUST continue. TaskSpec generation ≠ terminal.

## DISPATCHER_POLICY.md

Decision matrix mapping business_decision to dispatch_status:
- accepted → dispatched (or taskspec_generated if allow_next_stage=false)
- human_required → stopped
- blocked → stopped
- unknown → stopped (fail-closed)

Anti-patterns: Markdown-only output, ready_to_dispatch without dispatch, transport success assumed as acceptance.

## AUTONOMOUS_PROGRESS_POLICY.md

Allowed autonomous: stage advancement, TaskSpec generation, non-destructive execution, tests, evidence pack generation, GPT review submission, status file writing.

Always human-required: deletion, movement, renaming, worktree cleanup, evidence overwrite, sensitive config, baseline fabrication, human attestation fabrication, scope expansion.

## HUMAN_REQUIRED_TAXONOMY.md

8 categories: missing_baseline, destructive_action, sensitive_config, evidence_overwrite, scope_expansion, ambiguous_authority, external_secret, manual_attestation_required.

Precedence: external_secret > destructive_action > evidence_overwrite > scope_expansion > sensitive_config > ambiguous_authority > missing_baseline > manual_attestation_required.

## STAGE_GATE_POLICY.md

5 gate results: accepted, blocked, human_required, partial, unknown.

Priority chain: GPT Review → Agent-Acceptance Gate → Dispatch. Gate overrides GPT if schema/policy violation detected.

## EVIDENCE_PACK_CONTRACT.md

Minimum requirements: manifest, GPT review prompt with structured fields, evidence index (with missing evidence listed), machine-readable state.

Missing evidence must be explicit, not silently omitted.
