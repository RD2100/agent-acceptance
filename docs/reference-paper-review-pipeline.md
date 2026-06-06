# Reference Paper Review Pipeline — 端到端快乐路径设计

> 版本: 1.0.0-draft
> 目标: 让 paper_iteration 从 init 到 closure evidence 的完整框架路径可用且比绕过更简单
> 设计先行，实现在 REF-PAPER-1 中完成

## 1. 目标

提供一条完整、可运行、可复用的 paper review pipeline，使智能体的最简单路径是：

```bash
devframe run pipelines/reference_paper_review.yaml --dry-run
```

而不是：

```bash
python submit_to_gpt.py
```

## 2. Pipeline 阶段

```
Stage 1: initialize_project
  devframe init paper_iteration <target>
  → 生成 PAPER_PROFILE.yaml, PAPER_STATE.yaml, PAPER_LEDGER.md 等

Stage 2: load_pipeline
  runner 加载 pipelines/reference_paper_review.yaml
  → 验证 schema，解析 stage 序列

Stage 3: run_synthetic_paper_task
  executor 执行审查/核验/改写（dry-run only）
  → 生成 synthetic review report, citation check, revision diff

Stage 4: collect_actual_deliverables
  框架自动扫描产出目录
  → 收集所有实际生成的文件路径 + SHA256

Stage 5: build_evidence_pack
  review_pack_builder 构建标准 evidence pack
  → 生成 PACK_MANIFEST.md（含 SHA256）
  → 验证 manifest 与 ZIP 双向一致
  → 拒绝 summary-only pack

Stage 6: run_pre_submission_gate
  验证：pipeline provenance、bypass check、evidence 完整性
  → 验证 pipeline_run_id 存在
  → 扫描 ad-hoc 脚本
  → 验证 submission 路径合法
  → 检查 manifest 一致

Stage 7: submission_adapter_dry_run
  submission_adapter 以 dry-run 模式执行
  → 输出 SUBMISSION_RESULT（mode=dry_run）
  → 证明 submission 经由 adapter，不是手写

Stage 8: parse_review_result
  解析 GPT 或模拟回复
  → 解析 overall_judgment, blocking_reasons 等
  → 写入 CAPTURED_REPLY

Stage 9: state_machine_transition
  state_machine 验证阶段转换合法性
  → 检查 blocked items
  → 检查 authorization→execution→closure 顺序

Stage 10: generate_flow_outcome
  框架生成 FLOW_OUTCOME.json
  → transport_status, business_decision, dispatch_status
  → 非 agent 手写

Stage 11: closure
  收集所有 evidence 到 closure pack
  → 归档 evidence_packs/<run_id>/
```

## 3. 谁生成什么

| 文件 | 由谁生成 | 方式 |
|------|---------|------|
| PAPER_PROFILE.yaml | devframe init | 模板初始化 |
| PAPER_STATE.yaml | runner | 阶段转换 |
| review_report | executor | 合成文本 |
| PACK_MANIFEST.md | pack_builder | 自动扫描 + SHA256 |
| PRE_SUBMISSION_CHECK.yaml | pre-submission gate | 自动检查 |
| FLOW_OUTCOME.json | runner | 框架生成 |
| SUBMISSION_RESULT.json | submission_adapter | adapter 输出 |
| CLOSURE_REPORT.yaml | runner | 框架生成（非 agent 手写） |

## 4. 禁止

- agent 手写 FLOW_OUTCOME.json
- agent 手写 PACK_MANIFEST.md（必须由 builder 生成）
- agent 直接调 Playwright 提交
- agent 手写 evidence pack ZIP
- 绕过任一 stage 直接 closure

## 5. 验收标准

- `devframe run pipelines/reference_paper_review.yaml --dry-run` 成功执行 11 个 stage
- 所有产出文件由框架生成，无 agent 手写
- FLOW_OUTCOME 可追溯到 pipeline_run_id
- 不出现临时 Playwright 脚本
- 不出现手写 submit_to_gpt.py
- pre-submission gate 通过
- 所有 tests 通过
