# WORKSPACE-CLOSURE-INVENTORY-A1

Total untracked entries: 204
Generated: 2026-06-12
Baseline: b797f19

## Summary by Category

| Category | Count |
|----------|-------|
| AI_STATE | 2 |
| CDP_TEMP_SCRIPT | 56 |
| EVIDENCE_DIR_NO_ZIP | 9 |
| EVIDENCE_DIR_WITH_ZIP | 13 |
| EVIDENCE_LOOSE_HTML | 1 |
| EVIDENCE_LOOSE_JSON | 2 |
| EVIDENCE_LOOSE_PNG | 6 |
| EVIDENCE_LOOSE_TXT | 18 |
| EVIDENCE_SUBDIR_FILE | 46 |
| EVIDENCE_ZIP | 25 |
| GOVERNANCE_MARKER | 1 |
| NEG009_FIXTURE | 17 |
| REPORT_CURRENT | 2 |
| REPORT_PROMPT | 2 |
| REVIEW_PROMPT | 1 |
| SCRIPT_ARTIFACT | 1 |
| UNKNOWN | 1 |
| WINDOWS_ARTIFACT | 1 |
| **TOTAL** | **204** |

## Summary by Suggested Action

| Action | Count | Description |
|--------|-------|-------------|
| COMMIT | 106 | Should be added to git |
| ARCHIVE | 77 | Move to archive dir or trash |
| KEEP | 20 | Retain in workspace as-is |
| DISCARD | 1 | Safe to delete |

## Full Inventory

### AI_STATE (2 items)

| Path | Action | Risk | Has ZIP | Notes |
|------|--------|------|---------|-------|
| .ai/conversation/current.json | KEEP | LOW | - | AI conversation state (auto-managed) |
| .ai/tasks/workspace-closure-inventory-a1.yaml | KEEP | LOW | - | AI conversation state (auto-managed) |

### CDP_TEMP_SCRIPT (56 items)

| Path | Action | Risk | Has ZIP | Notes |
|------|--------|------|---------|-------|
| _ask_a4_task.py | ARCHIVE | LOW | - | One-off session CDP script |
| _ask_ecs_a2_r1.py | ARCHIVE | LOW | - | One-off session CDP script |
| _ask_ecs_a2_r2.py | ARCHIVE | LOW | - | One-off session CDP script |
| _ask_next_after_a4.py | ARCHIVE | LOW | - | One-off session CDP script |
| _ask_next_direction.py | ARCHIVE | LOW | - | One-off session CDP script |
| _ask_next_task.py | ARCHIVE | LOW | - | One-off session CDP script |
| _build_closeout_packs.py | ARCHIVE | LOW | - | One-off session CDP script |
| _build_evidence_maintenance.py | ARCHIVE | LOW | - | One-off session CDP script |
| _build_uaws_evidence.py | ARCHIVE | LOW | - | One-off session CDP script |
| _capture_a2_r3_verdict.py | ARCHIVE | LOW | - | One-off session CDP script |
| _capture_a3_r1_v2.py | ARCHIVE | LOW | - | One-off session CDP script |
| _capture_a3_r1_verdict.py | ARCHIVE | LOW | - | One-off session CDP script |
| _capture_cleanup_a1.py | ARCHIVE | LOW | - | One-off session CDP script |
| _capture_health_gate_a1.py | ARCHIVE | LOW | - | One-off session CDP script |
| _capture_health_gate_a1_v2.py | ARCHIVE | LOW | - | One-off session CDP script |
| _capture_health_gate_a1_v3.py | ARCHIVE | LOW | - | One-off session CDP script |
| _capture_hfs.py | ARCHIVE | LOW | - | One-off session CDP script |
| _capture_hrv.py | ARCHIVE | LOW | - | One-off session CDP script |
| _capture_hrv_full.py | ARCHIVE | LOW | - | One-off session CDP script |
| _capture_hrv_v3.py | ARCHIVE | LOW | - | One-off session CDP script |
| _capture_hrv_v3b.py | ARCHIVE | LOW | - | One-off session CDP script |
| _capture_hrv_v3c.py | ARCHIVE | LOW | - | One-off session CDP script |
| _capture_hrv_v4.py | ARCHIVE | LOW | - | One-off session CDP script |
| _capture_r2_verdict.py | ARCHIVE | LOW | - | One-off session CDP script |
| _capture_r3_final.py | ARCHIVE | LOW | - | One-off session CDP script |
| _capture_r3_verdict.py | ARCHIVE | LOW | - | One-off session CDP script |
| _check_browser.py | ARCHIVE | LOW | - | One-off session CDP script |
| _check_browser2.py | ARCHIVE | LOW | - | One-off session CDP script |
| _debug_gpt.py | ARCHIVE | LOW | - | One-off session CDP script |
| _submit_cleanup_a1.py | ARCHIVE | LOW | - | One-off session CDP script |
| _submit_closeout_review.py | ARCHIVE | LOW | - | One-off session CDP script |
| _submit_ecs.py | ARCHIVE | LOW | - | One-off session CDP script |
| _submit_ecs_a2.py | ARCHIVE | LOW | - | One-off session CDP script |
| _submit_fix_independent_review.py | ARCHIVE | LOW | - | One-off session CDP script |
| _submit_fix_r2.py | ARCHIVE | LOW | - | One-off session CDP script |
| _submit_health_gate_a1.py | ARCHIVE | LOW | - | One-off session CDP script |
| _submit_health_gate_a1_r2.py | ARCHIVE | LOW | - | One-off session CDP script |
| _submit_health_gate_a1_r3.py | ARCHIVE | LOW | - | One-off session CDP script |
| _submit_health_gate_a2_r3.py | ARCHIVE | LOW | - | One-off session CDP script |
| _submit_health_gate_a3.py | ARCHIVE | LOW | - | One-off session CDP script |
| _submit_health_gate_a3_v2.py | ARCHIVE | LOW | - | One-off session CDP script |
| _submit_health_gate_a3_v3.py | ARCHIVE | LOW | - | One-off session CDP script |
| _submit_health_gate_proposal.py | ARCHIVE | LOW | - | One-off session CDP script |
| _submit_health_gate_r2.py | ARCHIVE | LOW | - | One-off session CDP script |
| _submit_health_gate_r3.py | ARCHIVE | LOW | - | One-off session CDP script |
| _submit_hfs.py | ARCHIVE | LOW | - | One-off session CDP script |
| _submit_hfs2.py | ARCHIVE | LOW | - | One-off session CDP script |
| _submit_hrv.py | ARCHIVE | LOW | - | One-off session CDP script |
| _submit_hrv_v2.py | ARCHIVE | LOW | - | One-off session CDP script |
| _submit_hrv_v3.py | ARCHIVE | LOW | - | One-off session CDP script |
| _submit_hrv_v4.py | ARCHIVE | LOW | - | One-off session CDP script |
| _submit_hrv_v4_final.py | ARCHIVE | LOW | - | One-off session CDP script |
| _submit_hrv_v5.py | ARCHIVE | LOW | - | One-off session CDP script |
| _submit_maintenance.py | ARCHIVE | LOW | - | One-off session CDP script |
| _submit_readiness_review_r1.py | ARCHIVE | LOW | - | One-off session CDP script |
| _submit_uaws.py | ARCHIVE | LOW | - | One-off session CDP script |

### EVIDENCE_DIR_NO_ZIP (9 items)

| Path | Action | Risk | Has ZIP | Notes |
|------|--------|------|---------|-------|
| _evidence/EVIDENCE-CAPTURE-HOOK-FAILURE-RUNTIME-VALIDATIO... | COMMIT | MEDIUM | - | Evidence dir without ZIP; should be committed or ZIP built |
| _evidence/EVIDENCE-CAPTURE-HOOK-FAILURE-RUNTIME-VALIDATIO... | COMMIT | MEDIUM | - | Evidence dir without ZIP; should be committed or ZIP built |
| _evidence/EVIDENCE-CAPTURE-HOOK-FAILURE-RUNTIME-VALIDATIO... | COMMIT | MEDIUM | - | Evidence dir without ZIP; should be committed or ZIP built |
| _evidence/EVIDENCE-CAPTURE-HOOK-FAILURE-RUNTIME-VALIDATIO... | COMMIT | MEDIUM | - | Evidence dir without ZIP; should be committed or ZIP built |
| _evidence/EVIDENCE-CAPTURE-HOOK-FAILURE-RUNTIME-VALIDATIO... | COMMIT | MEDIUM | - | Evidence dir without ZIP; should be committed or ZIP built |
| _evidence/EVIDENCE-CAPTURE-HOOK-FAILURE-RUNTIME-VALIDATIO... | COMMIT | MEDIUM | - | Evidence dir without ZIP; should be committed or ZIP built |
| _evidence/EVIDENCE-CAPTURE-HOOK-FAILURE-SEMANTICS-A1/ | COMMIT | MEDIUM | - | Evidence dir without ZIP; should be committed or ZIP built |
| _evidence/hook-output/ | COMMIT | MEDIUM | - | Evidence dir without ZIP; should be committed or ZIP built |
| _evidence/runtime-negative-path-evidence/ | COMMIT | MEDIUM | - | Evidence dir without ZIP; should be committed or ZIP built |

### EVIDENCE_DIR_WITH_ZIP (13 items)

| Path | Action | Risk | Has ZIP | Notes |
|------|--------|------|---------|-------|
| _evidence/CONVERSATION-HEALTH-GATE-A1-R2/ | ARCHIVE | LOW | EVIDENCE_PACK_CONVERSATION_HEALTH_GATE_A1_R2.zip | Evidence dir has corresponding ZIP; raw dir can be archived |
| _evidence/CONVERSATION-HEALTH-GATE-A1-R3/ | ARCHIVE | LOW | EVIDENCE_PACK_CONVERSATION_HEALTH_GATE_A1_R3.zip | Evidence dir has corresponding ZIP; raw dir can be archived |
| _evidence/CONVERSATION-HEALTH-GATE-A1-R4/ | ARCHIVE | LOW | EVIDENCE_PACK_CONVERSATION_HEALTH_GATE_A1_R4.zip | Evidence dir has corresponding ZIP; raw dir can be archived |
| _evidence/CONVERSATION-HEALTH-GATE-A1/ | ARCHIVE | LOW | EVIDENCE_PACK_CONVERSATION_HEALTH_GATE_A1.zip | Evidence dir has corresponding ZIP; raw dir can be archived |
| _evidence/CONVERSATION-HEALTH-GATE-A2-R2/ | ARCHIVE | LOW | EVIDENCE_PACK_CONVERSATION_HEALTH_GATE_A2_R2.zip | Evidence dir has corresponding ZIP; raw dir can be archived |
| _evidence/CONVERSATION-HEALTH-GATE-A2-R3/ | ARCHIVE | LOW | EVIDENCE_PACK_CONVERSATION_HEALTH_GATE_A2_R3.zip | Evidence dir has corresponding ZIP; raw dir can be archived |
| _evidence/CONVERSATION-HEALTH-GATE-A2/ | ARCHIVE | LOW | EVIDENCE_PACK_CONVERSATION_HEALTH_GATE_A2.zip | Evidence dir has corresponding ZIP; raw dir can be archived |
| _evidence/CONVERSATION-HEALTH-GATE-A3-R2/ | ARCHIVE | LOW | EVIDENCE_PACK_CONVERSATION_HEALTH_GATE_A3_R2.zip | Evidence dir has corresponding ZIP; raw dir can be archived |
| _evidence/CONVERSATION-HEALTH-GATE-A3/ | ARCHIVE | LOW | EVIDENCE_PACK_CONVERSATION_HEALTH_GATE_A3.zip | Evidence dir has corresponding ZIP; raw dir can be archived |
| _evidence/CONVERSATION-HEALTH-GATE-A4/ | ARCHIVE | LOW | EVIDENCE_PACK_CONVERSATION_HEALTH_GATE_A4.zip | Evidence dir has corresponding ZIP; raw dir can be archived |
| _evidence/EVIDENCE-CAPTURE-STANDARD-A1/ | ARCHIVE | LOW | EVIDENCE_PACK_EVIDENCE_CAPTURE_STANDARD_A1.zip | Evidence dir has corresponding ZIP; raw dir can be archived |
| _evidence/R18-EVIDENCE-MAINTENANCE-FINAL/ | ARCHIVE | LOW | EVIDENCE_PACK_R18_EVIDENCE_MAINTENANCE_FINAL.zip | Evidence dir has corresponding ZIP; raw dir can be archived |
| _evidence/UNIVERSAL-AGENT-WORKFLOW-STANDARD-A1/ | ARCHIVE | LOW | EVIDENCE_PACK_UNIVERSAL_AGENT_WORKFLOW_STANDARD_A1.zip | Evidence dir has corresponding ZIP; raw dir can be archived |

### EVIDENCE_LOOSE_HTML (1 items)

| Path | Action | Risk | Has ZIP | Notes |
|------|--------|------|---------|-------|
| _evidence/a3_r1_page_after_send.html | ARCHIVE | LOW | - | Debug HTML capture |

### EVIDENCE_LOOSE_JSON (2 items)

| Path | Action | Risk | Has ZIP | Notes |
|------|--------|------|---------|-------|
| _evidence/GPT_CAPTURE_RECONCILIATION.json | COMMIT | LOW | - | Loose JSON artifact |
| _evidence/GPT_REVIEW_SUBMISSION_STATUS.json | COMMIT | LOW | - | Loose JSON artifact |

### EVIDENCE_LOOSE_PNG (6 items)

| Path | Action | Risk | Has ZIP | Notes |
|------|--------|------|---------|-------|
| _evidence/GPT_REVIEW_UPLOAD_CONFIRMATION.png | ARCHIVE | LOW | - | Debug screenshot |
| _evidence/gpt_page_debug.png | ARCHIVE | LOW | - | Debug screenshot |
| _evidence/gpt_v3_nav_debug.png | ARCHIVE | LOW | - | Debug screenshot |
| _evidence/gpt_v3_nav_debug_after_nav.png | ARCHIVE | LOW | - | Debug screenshot |
| _evidence/gpt_v3_nav_debug_final.png | ARCHIVE | LOW | - | Debug screenshot |
| _evidence/gpt_v3_verdict_debug.png | ARCHIVE | LOW | - | Debug screenshot |

### EVIDENCE_LOOSE_TXT (18 items)

| Path | Action | Risk | Has ZIP | Notes |
|------|--------|------|---------|-------|
| _evidence/GPT_REVIEW_CHAT_URL.txt | COMMIT | LOW | - | Loose verdict/output text file |
| _evidence/GPT_REVIEW_RESULT.txt | COMMIT | LOW | - | Loose verdict/output text file |
| _evidence/cleanup_a1_verdict.txt | COMMIT | LOW | - | Loose verdict/output text file |
| _evidence/conversation_health_gate_a1_r2_verdict.txt | COMMIT | LOW | - | Loose verdict/output text file |
| _evidence/conversation_health_gate_a1_r3_verdict.txt | COMMIT | LOW | - | Loose verdict/output text file |
| _evidence/conversation_health_gate_a1_r4_verdict.txt | COMMIT | LOW | - | Loose verdict/output text file |
| _evidence/conversation_health_gate_a1_verdict.txt | COMMIT | LOW | - | Loose verdict/output text file |
| _evidence/conversation_health_gate_a2_r2_verdict.txt | COMMIT | LOW | - | Loose verdict/output text file |
| _evidence/conversation_health_gate_a2_r3_verdict.txt | COMMIT | LOW | - | Loose verdict/output text file |
| _evidence/conversation_health_gate_a3_verdict.txt | COMMIT | LOW | - | Loose verdict/output text file |
| _evidence/hfs_verdict.txt | COMMIT | LOW | - | Loose verdict/output text file |
| _evidence/hrv_v3_verdict.txt | COMMIT | LOW | - | Loose verdict/output text file |
| _evidence/hrv_v4_verdict.txt | COMMIT | LOW | - | Loose verdict/output text file |
| _evidence/hrv_verdict.txt | COMMIT | LOW | - | Loose verdict/output text file |
| _evidence/hrv_verdict_full.txt | COMMIT | LOW | - | Loose verdict/output text file |
| _evidence/next_direction_discussion.txt | COMMIT | LOW | - | Loose verdict/output text file |
| _evidence/next_task_reply_a4.txt | COMMIT | LOW | - | Loose verdict/output text file |
| _evidence/next_task_reply_after_a4.txt | COMMIT | LOW | - | Loose verdict/output text file |

### EVIDENCE_SUBDIR_FILE (46 items)

| Path | Action | Risk | Has ZIP | Notes |
|------|--------|------|---------|-------|
| _evidence/EVIDENCE-CAPTURE-STANDARD-A2/ai-guard-scope-che... | COMMIT | LOW | - | File inside evidence subdir |
| _evidence/EVIDENCE-CAPTURE-STANDARD-A2/chain-evidence.json | COMMIT | LOW | - | File inside evidence subdir |
| _evidence/EVIDENCE-CAPTURE-STANDARD-A2/conversation-health/ | COMMIT | LOW | - | File inside evidence dir EVIDENCE-CAPTURE-STANDARD-A2 |
| _evidence/EVIDENCE-CAPTURE-STANDARD-A2/deferred-files-reg... | COMMIT | LOW | - | File inside evidence subdir |
| _evidence/EVIDENCE-CAPTURE-STANDARD-A2/diff-stat-13a7f4b.txt | COMMIT | LOW | - | File inside evidence subdir |
| _evidence/EVIDENCE-CAPTURE-STANDARD-A2/diff-stat-148c550.txt | COMMIT | LOW | - | File inside evidence subdir |
| _evidence/EVIDENCE-CAPTURE-STANDARD-A2/diff-stat-442ad78.txt | COMMIT | LOW | - | File inside evidence subdir |
| _evidence/EVIDENCE-CAPTURE-STANDARD-A2/diff-stat-b474d4b.txt | COMMIT | LOW | - | File inside evidence subdir |
| _evidence/EVIDENCE-CAPTURE-STANDARD-A2/diff-stat-c96de98.txt | COMMIT | LOW | - | File inside evidence subdir |
| _evidence/EVIDENCE-CAPTURE-STANDARD-A2/diff-stat-ceb9ed0.txt | COMMIT | LOW | - | File inside evidence subdir |
| _evidence/EVIDENCE-CAPTURE-STANDARD-A2/diff-stat-combined... | COMMIT | LOW | - | File inside evidence subdir |
| _evidence/EVIDENCE-CAPTURE-STANDARD-A2/diff.patch | COMMIT | LOW | - | File inside evidence subdir |
| _evidence/EVIDENCE-CAPTURE-STANDARD-A2/evidence-manifest.... | COMMIT | LOW | - | File inside evidence subdir |
| _evidence/EVIDENCE-CAPTURE-STANDARD-A2/extra/ | COMMIT | LOW | - | File inside evidence dir EVIDENCE-CAPTURE-STANDARD-A2 |
| _evidence/EVIDENCE-CAPTURE-STANDARD-A2/final-report.md | COMMIT | LOW | - | File inside evidence subdir |
| _evidence/EVIDENCE-CAPTURE-STANDARD-A2/git-log.txt | COMMIT | LOW | - | File inside evidence subdir |
| _evidence/EVIDENCE-CAPTURE-STANDARD-A2/git-show-13a7f4b.txt | COMMIT | LOW | - | File inside evidence subdir |
| _evidence/EVIDENCE-CAPTURE-STANDARD-A2/git-show-148c550.txt | COMMIT | LOW | - | File inside evidence subdir |
| _evidence/EVIDENCE-CAPTURE-STANDARD-A2/git-show-442ad78.txt | COMMIT | LOW | - | File inside evidence subdir |
| _evidence/EVIDENCE-CAPTURE-STANDARD-A2/git-show-b474d4b.txt | COMMIT | LOW | - | File inside evidence subdir |
| _evidence/EVIDENCE-CAPTURE-STANDARD-A2/git-show-c96de98.txt | COMMIT | LOW | - | File inside evidence subdir |
| _evidence/EVIDENCE-CAPTURE-STANDARD-A2/git-show-ceb9ed0.txt | COMMIT | LOW | - | File inside evidence subdir |
| _evidence/EVIDENCE-CAPTURE-STANDARD-A2/git-status-after.txt | COMMIT | LOW | - | File inside evidence subdir |
| _evidence/EVIDENCE-CAPTURE-STANDARD-A2/gpt_review_prompt_... | COMMIT | LOW | - | File inside evidence subdir |
| _evidence/EVIDENCE-CAPTURE-STANDARD-A2/gpt_verdict_a2.txt | COMMIT | LOW | - | File inside evidence subdir |
| _evidence/EVIDENCE-CAPTURE-STANDARD-A2/gpt_verdict_a2_r2.txt | COMMIT | LOW | - | File inside evidence subdir |
| _evidence/EVIDENCE-CAPTURE-STANDARD-A2/gpt_verdict_a2_r3.txt | COMMIT | LOW | - | File inside evidence subdir |
| _evidence/EVIDENCE-CAPTURE-STANDARD-A2/gpt_verdict_a2_r4.txt | COMMIT | LOW | - | File inside evidence subdir |
| _evidence/EVIDENCE-CAPTURE-STANDARD-A2/gpt_verdict_a2_r5.txt | COMMIT | LOW | - | File inside evidence subdir |
| _evidence/EVIDENCE-CAPTURE-STANDARD-A2/pre-gpt-gate-evide... | COMMIT | LOW | - | File inside evidence dir EVIDENCE-CAPTURE-STANDARD-A2 |
| _evidence/EVIDENCE-CAPTURE-STANDARD-A2/r2_submission.txt | COMMIT | LOW | - | File inside evidence subdir |
| _evidence/EVIDENCE-CAPTURE-STANDARD-A2/r3_submission.txt | COMMIT | LOW | - | File inside evidence subdir |
| _evidence/EVIDENCE-CAPTURE-STANDARD-A2/r4_submission.txt | COMMIT | LOW | - | File inside evidence subdir |
| _evidence/EVIDENCE-CAPTURE-STANDARD-A2/r5_submission.txt | COMMIT | LOW | - | File inside evidence subdir |
| _evidence/EVIDENCE-CAPTURE-STANDARD-A2/review.md | COMMIT | LOW | - | File inside evidence subdir |
| _evidence/EVIDENCE-CAPTURE-STANDARD-A2/review.yaml | COMMIT | LOW | - | File inside evidence subdir |
| _evidence/EVIDENCE-CAPTURE-STANDARD-A2/runtime-evidence-i... | COMMIT | LOW | - | File inside evidence subdir |
| _evidence/EVIDENCE-CAPTURE-STANDARD-A2/sadp-audit-raw.txt | COMMIT | LOW | - | File inside evidence subdir |
| _evidence/EVIDENCE-CAPTURE-STANDARD-A2/safety-report.json | COMMIT | LOW | - | File inside evidence subdir |
| _evidence/EVIDENCE-CAPTURE-STANDARD-A2/secret-scan-output... | COMMIT | LOW | - | File inside evidence subdir |
| _evidence/EVIDENCE-CAPTURE-STANDARD-A2/test-output.txt | COMMIT | LOW | - | File inside evidence subdir |
| _evidence/R18-FOLLOWUP-FINAL/secret-scan-output.txt | COMMIT | LOW | - | File inside evidence subdir |
| _evidence/R18-WORKSPACE-CLEANUP-FINAL/secret-scan-output.txt | COMMIT | LOW | - | File inside evidence subdir |
| _evidence/R18-WORKSPACE-CLOSURE-SLIM/secret-scan-output.txt | COMMIT | LOW | - | File inside evidence subdir |
| _evidence/R18-WORKSPACE-CLOSURE/secret-scan-output.txt | COMMIT | LOW | - | File inside evidence subdir |
| _evidence/R18-catchup-commits/secret-scan-output.txt | COMMIT | LOW | - | File inside evidence subdir |

### EVIDENCE_ZIP (25 items)

| Path | Action | Risk | Has ZIP | Notes |
|------|--------|------|---------|-------|
| _evidence/EVIDENCE_PACK_CONVERSATION_HEALTH_GATE_A1.zip | COMMIT | LOW | EVIDENCE_PACK_CONVERSATION_HEALTH_GATE_A1.zip | Evidence pack ZIP - should be committed |
| _evidence/EVIDENCE_PACK_CONVERSATION_HEALTH_GATE_A1_R2.zip | COMMIT | LOW | EVIDENCE_PACK_CONVERSATION_HEALTH_GATE_A1_R2.zip | Evidence pack ZIP - should be committed |
| _evidence/EVIDENCE_PACK_CONVERSATION_HEALTH_GATE_A1_R3.zip | COMMIT | LOW | EVIDENCE_PACK_CONVERSATION_HEALTH_GATE_A1_R3.zip | Evidence pack ZIP - should be committed |
| _evidence/EVIDENCE_PACK_CONVERSATION_HEALTH_GATE_A1_R4.zip | COMMIT | LOW | EVIDENCE_PACK_CONVERSATION_HEALTH_GATE_A1_R4.zip | Evidence pack ZIP - should be committed |
| _evidence/EVIDENCE_PACK_CONVERSATION_HEALTH_GATE_A2.zip | COMMIT | LOW | EVIDENCE_PACK_CONVERSATION_HEALTH_GATE_A2.zip | Evidence pack ZIP - should be committed |
| _evidence/EVIDENCE_PACK_CONVERSATION_HEALTH_GATE_A2_R2.zip | COMMIT | LOW | EVIDENCE_PACK_CONVERSATION_HEALTH_GATE_A2_R2.zip | Evidence pack ZIP - should be committed |
| _evidence/EVIDENCE_PACK_CONVERSATION_HEALTH_GATE_A2_R3.zip | COMMIT | LOW | EVIDENCE_PACK_CONVERSATION_HEALTH_GATE_A2_R3.zip | Evidence pack ZIP - should be committed |
| _evidence/EVIDENCE_PACK_CONVERSATION_HEALTH_GATE_A3.zip | COMMIT | LOW | EVIDENCE_PACK_CONVERSATION_HEALTH_GATE_A3.zip | Evidence pack ZIP - should be committed |
| _evidence/EVIDENCE_PACK_CONVERSATION_HEALTH_GATE_A3_R2.zip | COMMIT | LOW | EVIDENCE_PACK_CONVERSATION_HEALTH_GATE_A3_R2.zip | Evidence pack ZIP - should be committed |
| _evidence/EVIDENCE_PACK_CONVERSATION_HEALTH_GATE_A4.zip | COMMIT | LOW | EVIDENCE_PACK_CONVERSATION_HEALTH_GATE_A4.zip | Evidence pack ZIP - should be committed |
| _evidence/EVIDENCE_PACK_ECS_A2_R2.zip | COMMIT | LOW | EVIDENCE_PACK_ECS_A2_R2.zip | Evidence pack ZIP - should be committed |
| _evidence/EVIDENCE_PACK_ECS_A2_R3.zip | COMMIT | LOW | EVIDENCE_PACK_ECS_A2_R3.zip | Evidence pack ZIP - should be committed |
| _evidence/EVIDENCE_PACK_ECS_A2_R4.zip | COMMIT | LOW | EVIDENCE_PACK_ECS_A2_R4.zip | Evidence pack ZIP - should be committed |
| _evidence/EVIDENCE_PACK_ECS_A2_R5.zip | COMMIT | LOW | EVIDENCE_PACK_ECS_A2_R5.zip | Evidence pack ZIP - should be committed |
| _evidence/EVIDENCE_PACK_EVIDENCE_CAPTURE_STANDARD_A1.zip | COMMIT | LOW | EVIDENCE_PACK_EVIDENCE_CAPTURE_STANDARD_A1.zip | Evidence pack ZIP - should be committed |
| _evidence/EVIDENCE_PACK_EVIDENCE_CAPTURE_STANDARD_A2.zip | COMMIT | LOW | EVIDENCE_PACK_EVIDENCE_CAPTURE_STANDARD_A2.zip | Evidence pack ZIP - should be committed |
| _evidence/EVIDENCE_PACK_HOOK_FAILURE_RUNTIME_VALIDATION_A... | COMMIT | LOW | EVIDENCE_PACK_HOOK_FAILURE_RUNTIME_VALIDATION_A1.zip | Evidence pack ZIP - should be committed |
| _evidence/EVIDENCE_PACK_HOOK_FAILURE_RUNTIME_VALIDATION_C... | COMMIT | LOW | EVIDENCE_PACK_HOOK_FAILURE_RUNTIME_VALIDATION_CLEANUP_A1.zip | Evidence pack ZIP - should be committed |
| _evidence/EVIDENCE_PACK_HOOK_FAILURE_RUNTIME_VALIDATION_V... | COMMIT | LOW | EVIDENCE_PACK_HOOK_FAILURE_RUNTIME_VALIDATION_V2.zip | Evidence pack ZIP - should be committed |
| _evidence/EVIDENCE_PACK_HOOK_FAILURE_RUNTIME_VALIDATION_V... | COMMIT | LOW | EVIDENCE_PACK_HOOK_FAILURE_RUNTIME_VALIDATION_V3.zip | Evidence pack ZIP - should be committed |
| _evidence/EVIDENCE_PACK_HOOK_FAILURE_RUNTIME_VALIDATION_V... | COMMIT | LOW | EVIDENCE_PACK_HOOK_FAILURE_RUNTIME_VALIDATION_V4.zip | Evidence pack ZIP - should be committed |
| _evidence/EVIDENCE_PACK_HOOK_FAILURE_RUNTIME_VALIDATION_V... | COMMIT | LOW | EVIDENCE_PACK_HOOK_FAILURE_RUNTIME_VALIDATION_V5.zip | Evidence pack ZIP - should be committed |
| _evidence/EVIDENCE_PACK_HOOK_FAILURE_SEMANTICS_A1.zip | COMMIT | LOW | EVIDENCE_PACK_HOOK_FAILURE_SEMANTICS_A1.zip | Evidence pack ZIP - should be committed |
| _evidence/EVIDENCE_PACK_R18_EVIDENCE_MAINTENANCE_FINAL.zip | COMMIT | LOW | EVIDENCE_PACK_R18_EVIDENCE_MAINTENANCE_FINAL.zip | Evidence pack ZIP - should be committed |
| _evidence/EVIDENCE_PACK_UNIVERSAL_AGENT_WORKFLOW_STANDARD... | COMMIT | LOW | EVIDENCE_PACK_UNIVERSAL_AGENT_WORKFLOW_STANDARD_A1.zip | Evidence pack ZIP - should be committed |

### GOVERNANCE_MARKER (1 items)

| Path | Action | Risk | Has ZIP | Notes |
|------|--------|------|---------|-------|
| READY_FOR_HUMAN_AUTHORIZATION_WITH_LIMITATIONS | COMMIT | LOW | - | Governance authorization marker file |

### NEG009_FIXTURE (17 items)

| Path | Action | Risk | Has ZIP | Notes |
|------|--------|------|---------|-------|
| _projects/dev-frame-writing/docs/agent-runtime/negative-t... | KEEP | MEDIUM | - | Negative test fixture on deny_paths (contains 'secret' in name) |
| _projects/dev-frame-writing/docs/agent-runtime/negative-t... | KEEP | MEDIUM | - | Negative test fixture on deny_paths (contains 'secret' in name) |
| _projects/project-alpha/docs/agent-runtime/negative-test-... | KEEP | MEDIUM | - | Negative test fixture on deny_paths (contains 'secret' in name) |
| _projects/project-delta/docs/agent-runtime/negative-test-... | KEEP | MEDIUM | - | Negative test fixture on deny_paths (contains 'secret' in name) |
| _projects/project-delta/docs/agent-runtime/negative-test-... | KEEP | MEDIUM | - | Negative test fixture on deny_paths (contains 'secret' in name) |
| _projects/project-epsilon/docs/agent-runtime/negative-tes... | KEEP | MEDIUM | - | Negative test fixture on deny_paths (contains 'secret' in name) |
| _projects/project-epsilon/docs/agent-runtime/negative-tes... | KEEP | MEDIUM | - | Negative test fixture on deny_paths (contains 'secret' in name) |
| _projects/project-eta/docs/agent-runtime/negative-test-fi... | KEEP | MEDIUM | - | Negative test fixture on deny_paths (contains 'secret' in name) |
| _projects/project-eta/docs/agent-runtime/negative-test-fi... | KEEP | MEDIUM | - | Negative test fixture on deny_paths (contains 'secret' in name) |
| _projects/project-gamma/docs/agent-runtime/negative-test-... | KEEP | MEDIUM | - | Negative test fixture on deny_paths (contains 'secret' in name) |
| _projects/project-gamma/docs/agent-runtime/negative-test-... | KEEP | MEDIUM | - | Negative test fixture on deny_paths (contains 'secret' in name) |
| _projects/project-iota/docs/agent-runtime/negative-test-f... | KEEP | MEDIUM | - | Negative test fixture on deny_paths (contains 'secret' in name) |
| _projects/project-iota/docs/agent-runtime/negative-test-f... | KEEP | MEDIUM | - | Negative test fixture on deny_paths (contains 'secret' in name) |
| _projects/project-theta/docs/agent-runtime/negative-test-... | KEEP | MEDIUM | - | Negative test fixture on deny_paths (contains 'secret' in name) |
| _projects/project-theta/docs/agent-runtime/negative-test-... | KEEP | MEDIUM | - | Negative test fixture on deny_paths (contains 'secret' in name) |
| _projects/project-zeta/docs/agent-runtime/negative-test-f... | KEEP | MEDIUM | - | Negative test fixture on deny_paths (contains 'secret' in name) |
| _projects/project-zeta/docs/agent-runtime/negative-test-f... | KEEP | MEDIUM | - | Negative test fixture on deny_paths (contains 'secret' in name) |

### REPORT_CURRENT (2 items)

| Path | Action | Risk | Has ZIP | Notes |
|------|--------|------|---------|-------|
| _reports/POST-AI-GUARD-TASK-OUTLINE.ascii.md | COMMIT | LOW | - | Current task outline document |
| _reports/POST-AI-GUARD-TASK-OUTLINE.md | COMMIT | LOW | - | Current task outline document |

### REPORT_PROMPT (2 items)

| Path | Action | Risk | Has ZIP | Notes |
|------|--------|------|---------|-------|
| _reports/PROMPT_AGENT_FLOW_FRAMEWORK.md | COMMIT | LOW | - | Agent prompt document |
| _reports/PROMPT_AGENT_PAPER_DEVELOPMENT.md | COMMIT | LOW | - | Agent prompt document |

### REVIEW_PROMPT (1 items)

| Path | Action | Risk | Has ZIP | Notes |
|------|--------|------|---------|-------|
| _codex_review_prompt.md | COMMIT | LOW | - | Codex code review prompt template |

### SCRIPT_ARTIFACT (1 items)

| Path | Action | Risk | Has ZIP | Notes |
|------|--------|------|---------|-------|
| scripts/_evidence/ | ARCHIVE | LOW | - | Script run artifacts directory |

### UNKNOWN (1 items)

| Path | Action | Risk | Has ZIP | Notes |
|------|--------|------|---------|-------|
| _gen_inventory.py | KEEP | MEDIUM | - | Unclassified - needs manual review |

### WINDOWS_ARTIFACT (1 items)

| Path | Action | Risk | Has ZIP | Notes |
|------|--------|------|---------|-------|
| nul | DISCARD | LOW | - | Windows NUL device redirect artifact (accidental) |

## Evidence ZIP Coverage

| Evidence Directory | ZIP File | Status |
|-------------------|----------|--------|
| CONVERSATION-HEALTH-GATE-A1 | EVIDENCE_PACK_CONVERSATION_HEALTH_GATE_A1.zip | COVERED |
| CONVERSATION-HEALTH-GATE-A1-R2 | EVIDENCE_PACK_CONVERSATION_HEALTH_GATE_A1_R2.zip | COVERED |
| CONVERSATION-HEALTH-GATE-A1-R3 | EVIDENCE_PACK_CONVERSATION_HEALTH_GATE_A1_R3.zip | COVERED |
| CONVERSATION-HEALTH-GATE-A1-R4 | EVIDENCE_PACK_CONVERSATION_HEALTH_GATE_A1_R4.zip | COVERED |
| CONVERSATION-HEALTH-GATE-A2 | EVIDENCE_PACK_CONVERSATION_HEALTH_GATE_A2.zip | COVERED |
| CONVERSATION-HEALTH-GATE-A2-R2 | EVIDENCE_PACK_CONVERSATION_HEALTH_GATE_A2_R2.zip | COVERED |
| CONVERSATION-HEALTH-GATE-A2-R3 | EVIDENCE_PACK_CONVERSATION_HEALTH_GATE_A2_R3.zip | COVERED |
| CONVERSATION-HEALTH-GATE-A3 | EVIDENCE_PACK_CONVERSATION_HEALTH_GATE_A3.zip | COVERED |
| CONVERSATION-HEALTH-GATE-A3-R2 | EVIDENCE_PACK_CONVERSATION_HEALTH_GATE_A3_R2.zip | COVERED |
| CONVERSATION-HEALTH-GATE-A4 | EVIDENCE_PACK_CONVERSATION_HEALTH_GATE_A4.zip | COVERED |
| EVIDENCE-CAPTURE-HOOK-FAILURE-RUNTIME-VALIDATION-A1 | - | NO_ZIP |
| EVIDENCE-CAPTURE-HOOK-FAILURE-RUNTIME-VALIDATION-A1-V2 | - | NO_ZIP |
| EVIDENCE-CAPTURE-HOOK-FAILURE-RUNTIME-VALIDATION-A1-V3 | - | NO_ZIP |
| EVIDENCE-CAPTURE-HOOK-FAILURE-RUNTIME-VALIDATION-A1-V4 | - | NO_ZIP |
| EVIDENCE-CAPTURE-HOOK-FAILURE-RUNTIME-VALIDATION-A1-V5 | - | NO_ZIP |
| EVIDENCE-CAPTURE-HOOK-FAILURE-RUNTIME-VALIDATION-CLEANUP-A1 | - | NO_ZIP |
| EVIDENCE-CAPTURE-HOOK-FAILURE-SEMANTICS-A1 | - | NO_ZIP |
| EVIDENCE-CAPTURE-STANDARD-A1 | EVIDENCE_PACK_EVIDENCE_CAPTURE_STANDARD_A1.zip | COVERED |
| EVIDENCE-CAPTURE-STANDARD-A2 | EVIDENCE_PACK_EVIDENCE_CAPTURE_STANDARD_A2.zip | COVERED |
| LIVE-DISPATCH-READINESS-FIX-A1 | - | NO_ZIP |
| LIVE-DISPATCH-READINESS-REVIEW-A1 | - | NO_ZIP |
| LIVE-DISPATCH-READINESS-SADP-ECS-CLOSEOUT-A1 | - | NO_ZIP |
| R18-EVIDENCE-MAINTENANCE-FINAL | EVIDENCE_PACK_R18_EVIDENCE_MAINTENANCE_FINAL.zip | COVERED |
| R18-FOLLOWUP-FINAL | EVIDENCE_PACK_R18_FOLLOWUP_FINAL.zip | COVERED |
| R18-WORKSPACE-CLEANUP | EVIDENCE_PACK_R18_WORKSPACE_CLEANUP.zip | COVERED |
| R18-WORKSPACE-CLEANUP-FINAL | EVIDENCE_PACK_R18_WORKSPACE_CLEANUP_FINAL.zip | COVERED |
| R18-WORKSPACE-CLOSURE | EVIDENCE_PACK_R18_WORKSPACE_CLOSURE.zip | COVERED |
| R18-WORKSPACE-CLOSURE-SLIM | EVIDENCE_PACK_R18_WORKSPACE_CLOSURE_SLIM.zip | COVERED |
| R18-catchup-commits | - | NO_ZIP |
| R18-followup-cleanup | - | NO_ZIP |
| SHARED-CDP-GPT-REVIEW-DRY-RUN-2-A1 | - | NO_ZIP |
| SHARED-CDP-V2-REVIEW-FINDINGS-FIX-A1 | - | NO_ZIP |
| UNIVERSAL-AGENT-WORKFLOW-STANDARD-A1 | EVIDENCE_PACK_UNIVERSAL_AGENT_WORKFLOW_STANDARD_A1.zip | COVERED |
| conversation-health | EVIDENCE_PACK_CONVERSATION_HEALTH_GATE_A1.zip | COVERED |
| conversation-health-evidence | - | NO_ZIP |
| hook-output | - | NO_ZIP |
| pre-gpt-gate-evidence | - | NO_ZIP |
| runtime-negative-path-evidence | - | NO_ZIP |

## MEDIUM/HIGH Risk Items

- **_evidence/EVIDENCE-CAPTURE-HOOK-FAILURE-RUNTIME-VALIDATION-A1-V2/**: Evidence dir without ZIP; should be committed or ZIP built
- **_evidence/EVIDENCE-CAPTURE-HOOK-FAILURE-RUNTIME-VALIDATION-A1-V3/**: Evidence dir without ZIP; should be committed or ZIP built
- **_evidence/EVIDENCE-CAPTURE-HOOK-FAILURE-RUNTIME-VALIDATION-A1-V4/**: Evidence dir without ZIP; should be committed or ZIP built
- **_evidence/EVIDENCE-CAPTURE-HOOK-FAILURE-RUNTIME-VALIDATION-A1-V5/**: Evidence dir without ZIP; should be committed or ZIP built
- **_evidence/EVIDENCE-CAPTURE-HOOK-FAILURE-RUNTIME-VALIDATION-A1/**: Evidence dir without ZIP; should be committed or ZIP built
- **_evidence/EVIDENCE-CAPTURE-HOOK-FAILURE-RUNTIME-VALIDATION-CLEANUP-A1/**: Evidence dir without ZIP; should be committed or ZIP built
- **_evidence/EVIDENCE-CAPTURE-HOOK-FAILURE-SEMANTICS-A1/**: Evidence dir without ZIP; should be committed or ZIP built
- **_evidence/hook-output/**: Evidence dir without ZIP; should be committed or ZIP built
- **_evidence/runtime-negative-path-evidence/**: Evidence dir without ZIP; should be committed or ZIP built
- **_gen_inventory.py**: Unclassified - needs manual review
- **_projects/dev-frame-writing/docs/agent-runtime/negative-test-fixtures/NEG-009-secrets-read.json**: Negative test fixture on deny_paths (contains 'secret' in name)
- **_projects/dev-frame-writing/docs/agent-runtime/negative-test-fixtures/negative-test-fixtures/NEG-009-secrets-read.json**: Negative test fixture on deny_paths (contains 'secret' in name)
- **_projects/project-alpha/docs/agent-runtime/negative-test-fixtures/NEG-009-secrets-read.json**: Negative test fixture on deny_paths (contains 'secret' in name)
- **_projects/project-delta/docs/agent-runtime/negative-test-fixtures/NEG-009-secrets-read.json**: Negative test fixture on deny_paths (contains 'secret' in name)
- **_projects/project-delta/docs/agent-runtime/negative-test-fixtures/negative-test-fixtures/NEG-009-secrets-read.json**: Negative test fixture on deny_paths (contains 'secret' in name)
- **_projects/project-epsilon/docs/agent-runtime/negative-test-fixtures/NEG-009-secrets-read.json**: Negative test fixture on deny_paths (contains 'secret' in name)
- **_projects/project-epsilon/docs/agent-runtime/negative-test-fixtures/negative-test-fixtures/NEG-009-secrets-read.json**: Negative test fixture on deny_paths (contains 'secret' in name)
- **_projects/project-eta/docs/agent-runtime/negative-test-fixtures/NEG-009-secrets-read.json**: Negative test fixture on deny_paths (contains 'secret' in name)
- **_projects/project-eta/docs/agent-runtime/negative-test-fixtures/negative-test-fixtures/NEG-009-secrets-read.json**: Negative test fixture on deny_paths (contains 'secret' in name)
- **_projects/project-gamma/docs/agent-runtime/negative-test-fixtures/NEG-009-secrets-read.json**: Negative test fixture on deny_paths (contains 'secret' in name)
- **_projects/project-gamma/docs/agent-runtime/negative-test-fixtures/negative-test-fixtures/NEG-009-secrets-read.json**: Negative test fixture on deny_paths (contains 'secret' in name)
- **_projects/project-iota/docs/agent-runtime/negative-test-fixtures/NEG-009-secrets-read.json**: Negative test fixture on deny_paths (contains 'secret' in name)
- **_projects/project-iota/docs/agent-runtime/negative-test-fixtures/negative-test-fixtures/NEG-009-secrets-read.json**: Negative test fixture on deny_paths (contains 'secret' in name)
- **_projects/project-theta/docs/agent-runtime/negative-test-fixtures/NEG-009-secrets-read.json**: Negative test fixture on deny_paths (contains 'secret' in name)
- **_projects/project-theta/docs/agent-runtime/negative-test-fixtures/negative-test-fixtures/NEG-009-secrets-read.json**: Negative test fixture on deny_paths (contains 'secret' in name)
- **_projects/project-zeta/docs/agent-runtime/negative-test-fixtures/NEG-009-secrets-read.json**: Negative test fixture on deny_paths (contains 'secret' in name)
- **_projects/project-zeta/docs/agent-runtime/negative-test-fixtures/negative-test-fixtures/NEG-009-secrets-read.json**: Negative test fixture on deny_paths (contains 'secret' in name)
