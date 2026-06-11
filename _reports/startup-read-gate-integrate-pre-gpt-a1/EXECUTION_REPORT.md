## STARTUP-READ-GATE-INTEGRATE-PRE-GPT-A1 — Execution Report

| Field | Value |
|-------|-------|
| **task_id** | STARTUP-READ-GATE-INTEGRATE-PRE-GPT-A1 |
| **run_id** | STARTUP_READ_GATE_INTEGRATE_PRE_GPT_A1_20260609T122600_RD |
| **status** | complete |
| **generated_at** | 2026-06-09T20:26:00+08:00 |
| **author** | Agent (QoderWork) |
| **parent_task** | STARTUP-READ-GATE-STRICT-HASH-TASKID-A1 (GPT-authorized) |

### Scope

Integrate `startup_read_gate.py` into `pre_gpt_review_gate.py` per hardening plan §5.7.3:
> pre_gpt_review_gate.py 增加检查项：验证启动证明存在且完整

### Implementation Summary

**Modified: `scripts/pre_gpt_review_gate.py`** (~130 lines, from ~53 lines)

Added:
- `startup_proof_path`, `required_reads_path`, `strict` parameters to `gate()` function
- `--startup-proof-path`, `--required-reads`, `--strict` CLI flags (argparse)
- Dynamic import of `startup_read_gate.gate()` when proof path provided
- Task ID extraction from PACK_MANIFEST.md for cross-reference
- Startup gate errors prefixed with `startup_read_gate:` for traceability
- Startup gate warnings forwarded to main gate warnings
- `startup_read_gate` and `startup_coverage_ratio` in extra_checks

**Modified: `tests/test_pre_gpt_review_gate.py`** (20 tests, from 15)

Added `TestStartupReadGateIntegration` class (5 tests):
- `test_no_proof_path_skips_startup_check` — backward compatible
- `test_valid_proof_passes_startup_gate` — integration pass path
- `test_invalid_proof_blocks_gate` — integration block path
- `test_strict_mode_promotes_warnings` — strict mode integration
- `test_startup_coverage_ratio_reported` — extra_checks propagation

### Test Results

```
tests/test_pre_gpt_review_gate.py: 20 passed (15 existing + 5 new)
tests/test_startup_read_gate.py: 19 passed (unchanged)
Full suite: 371 passed (366 + 5 new)
```

### Coverage Matrix

| Capability | Status | Verified By |
|---|---|---|
| No proof → skip startup check | Implemented | test_no_proof_path_skips_startup_check |
| Valid proof → gate passes | Implemented | test_valid_proof_passes_startup_gate |
| Invalid proof → gate blocks | Implemented | test_invalid_proof_blocks_gate |
| Strict mode → warnings become errors | Implemented | test_strict_mode_promotes_warnings |
| Coverage ratio propagated | Implemented | test_startup_coverage_ratio_reported |
| Backward compat (no startup args) | Preserved | All 15 existing tests still pass |
| CLI argparse interface | Implemented | Manual + integration tests |

### Known Limitations

1. Startup read gate is opt-in via `--startup-proof-path` — not yet enforced for all submissions
2. Task ID extraction from PACK_MANIFEST.md uses simple line parsing — may miss complex formats
3. State machine runtime integration still pending (startup_read_gate as transition guard)
4. startup_timestamp freshness check not yet implemented
5. `NEXT_AGENT_REQUIRED_READS.json` must exist at repo root or be explicitly provided
