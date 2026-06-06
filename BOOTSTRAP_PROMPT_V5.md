# Bootstrap Prompt — 配合 HANDOFF V5 使用

> 本提示词与 `HANDOFF_V5.md` 配套使用，复制到新对话第一条消息。

---

请阅读附件 HANDOFF_V5.md（项目交接文档，约 13KB，路径：`D:/agent-acceptance/HANDOFF_V5.md`，含 END_OF_HANDOFF 标记）。

## 确认理解

用以下**中文 YAML 格式**回复（字段名和字段值全部用中文）：

```yaml
审查运行ID: handoff-verify-v5-{时间戳}
交接理解判决: 已理解 | 未理解
项目身份已理解: 是 | 否
三层架构已理解: 是 | 否
已完成阶段已理解: 是 | 否
当前未闭合任务已理解: 是 | 否
安全边界已理解: 是 | 否
下一步任务已理解: 是 | 否
可以继续执行: 是 | 否
说明: 用中文说明对项目整体和当前未闭合任务的理解，至少 5 句话
```

---

## 必须遵守的执行规则

以下规则**不可跳过、不可降级、不可 soft-fail**：

### 任务闭环规则

1. **closed 的唯一路径**: plan → execute → self-verify → build evidence pack → submit GPT → GPT accepted → ledger closed → push allowed
2. **不许把 ready_for_review 当 closed** — 没有 GPT accepted，不得写 final_status: closed
3. **不许跳过 GPT 审查** — commit + push ≠ done。任何修改合约/模板/validator/governance docs 的治理任务必须有 GPT closure review
4. **summary-only evidence pack 必须在本地 fail** — validator 已部署，pack validate 已接入

### GPT 审查规则

5. **GPT 回复必须完整** — 等待 END_OF_GPT_RESPONSE 标记后才读取。不足 2000 bytes 或缺少标记 = 不得执行
6. **GPT accepted 必须包含 next_task_authorization** — 否则 accepted 无效
7. **GPT blocked 必须包含 required_fixes 和 resubmission_requirements**
8. **审查回复末尾必须包含 END_OF_GPT_RESPONSE**
9. **对话超过 60 条 assistant message → 强制 handoff**

### Evidence Pack 规则

10. **每次提交 GPT 必须构建 evidence pack**, 清单见 HANDOFF_V5.md 第 12 节
11. **PACK_MANIFEST.md 与 ZIP 双向一致**, 所有 SHA256 可复核
12. **WORKFLOW_CLOSURE_VALIDATION.yaml 和 PACK_VALIDATE_OUTPUT.txt 必须是 fresh pass**, 绝不使用 stale 旧数据
13. **证据包构建正确顺序**: 全部文件 → 加临时 manifest → 打包 → validator → fresh validation → 替换 stale → 重建 manifest

### 安全边界

14. 不得删除/移动/重命名/清理 evidence 或 runs
15. 不得伪造 GPT accepted 或 FLOW_OUTCOME
16. 不得移除或弱化 guard
17. 不得默认开启 live CDP
18. 不得处理真实论文全文或用户私密数据
19. 不得手写 Playwright 绕过 submission_adapter
20. 每次提交前运行 bypass checker + workflow closure validator

---

## 当前待闭合任务（按优先级）

| # | 任务 | 优先级 | 说明 |
|---|------|--------|------|
| 1 | REVIEW-TEMPLATE-V2 closure | P0 | commit `bc841e9d` 已 push 但从未提交 GPT。需构建 evidence pack 提交 6a23dd8c |
| 2 | MEMORY-A3 closure | P0 | lint 已部署，状态已改为 pass。需提交 GPT 确认闭合 |
| 3 | WORKFLOW_AUDIT_LEDGER SD-01/02/03 状态变更 | P0 | SD 已标记 fixed，但这次状态变更未经 GPT 审查确认 |
| 4 | GPT-REVIEW-GATE-A1 | P1 | 将 GPT 审查升级为硬门禁。GPT 已给出完整方案(见 docs/GPT_STRUCTURAL_FIX.txt) |

---

## 关键教训（必须内化）

1. **不要把 ready_for_review 当 closed** — 历史上至少 3 个任务犯过此错误
2. **不要提交 summary-only pack** — 历史上至少 4 次第一次提交缺实际产物
3. **GPT 审查不可跳过** — 这是贯穿全 session 的结构性缺陷，需 GPT-REVIEW-GATE-A1 修复
4. **Stale VALIDATION 是反复出现陷阱** — CONTROL-PLANE-A1 4+ 轮 blocked 根因
5. **不要等 GPT 回复未完成就执行** — 174 bytes 截断案例。capture_gpt_reply.py 已修复

---

## 相关文件路径

| 文件 | 路径 |
|------|------|
| HANDOFF | `D:/agent-acceptance/HANDOFF_V5.md` |
| 工作流审计台账 | `D:/agent-acceptance/docs/WORKFLOW_AUDIT_LEDGER.yaml` |
| GPT 结构化修复方案 | `D:/agent-acceptance/docs/GPT_STRUCTURAL_FIX.txt` |
| 审查模板 | `D:/agent-acceptance/templates/GPT_REVIEW_PROMPT_TEMPLATE.md` |
| 闭合报告模板 | `D:/agent-acceptance/templates/CLOSURE_REPORT_TEMPLATE.md` |
| Validator | `D:/agent-acceptance/scripts/validate_workflow_closure.py` |
| GPT 回复完整性检查 | `D:/agent-acceptance/scripts/validate_gpt_reply_completeness.py` |
| GPT 回复捕获 | `D:/agent-acceptance/scripts/capture_gpt_reply.py` |
| Bypass 检测 | `D:/agent-acceptance/scripts/check_submission_bypass.py` |
| Memory 编译器 | `D:/agent-acceptance/scripts/memory_compiler.py` |
| Memory Lint | `D:/agent-acceptance/scripts/memory_lint.py` |
| Handoff 检测 | `D:/agent-acceptance/scripts/check_handoff_needed.py` |
| Handoff 验证 | `D:/agent-acceptance/scripts/validate_handoff.py` |
| Stage Executor | `D:/devframe-control-plane/control_plane/stage_executor.py` |
| Pre-push Gate | `D:/agent-acceptance/hooks/pre-push.governance.ps1` |
| 当前对话 | `https://chatgpt.com/c/6a23dd8c-4550-83a8-bdee-76ca5a982edb` (13 msgs) |

---

## 验收条件

`交接理解判决: 已理解` 且 `可以继续执行: 是` → 直接执行优先级任务，不得再次确认。
