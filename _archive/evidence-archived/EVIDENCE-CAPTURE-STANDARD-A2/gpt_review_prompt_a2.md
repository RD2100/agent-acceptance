GPT REVIEW REQUEST: EVIDENCE-CAPTURE-STANDARD-A2

commit: b474d4b
base: 2d5f902
SHA-256: 7c824ddd0e0e240222c504fb110359564fb208330bc5f35a3ee438643f51442d
file_count: 42
test_result: 1260 passed, 0 failed (1204 regression + 56 new)

ECS-A2 交付摘要：

1. docs/agent-runtime/evidence-capture-standard.md — 规范化的 Evidence Capture Standard
   - Tier 0/1/2 分层必备文件（解决 7/9/10/11 不一致）
   - verdict_eligibility 三类信号分类（硬阻断/降级/记录）
   - runtime evidence 双轨制（.txt + index.json）
   - stale evidence确定性规则
   - "Relationship to SADP 0.R.2 Review YAML" 节

2. docs/agent-runtime/evidence-pack-review-rules.md — 整合的 review 评估规则

3. schemas/agent-runtime/evidence-manifest.schema.json — manifest schema

4. schemas/agent-runtime/runtime-evidence-index.schema.json — runtime index schema

5. scripts/build_evidence_pack.py — 12项改造：
   - 生成 evidence-manifest.json
   - 顶层 verdict_eligibility + evidence_completeness
   - review_yaml_profile: ecs-v1
   - --head 参数
   - test_mode: full_regression/targeted_tests
   - consistency_check.all_files_agree 改为 computed
   - validate_evidence_pack_contract() 可测试入口
   - runtime-evidence-index.json 生成

6. tests/test_evidence_capture_standard.py — 56 个新测试

GPT R1+R2 复核记录在 evidence pack 内：
- _evidence/EVIDENCE-CAPTURE-STANDARD-A2/gpt_review_r1.txt
- _evidence/EVIDENCE-CAPTURE-STANDARD-A2/gpt_review_r2.txt

请审查附件中的 evidence pack ZIP 并给出裁决。

Return format:
verdict: accepted | accepted_with_limitation | needs_revision | rejected
limitations:
  - <list or none>
next_task:
  task_id: <next task or none>
  authorized: yes | no

END_OF_GPT_RESPONSE
