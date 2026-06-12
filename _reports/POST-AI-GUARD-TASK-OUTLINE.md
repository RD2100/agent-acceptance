# 后续任务大纲 (Post AI-GUARD-FILES-MODE-AND-LARGE-FILE-SCAN-A1)

> 生成时间: 2026-06-12
> 基线 commits: 1d820d3c (P1 --files mode + streaming scan) + b797f19 (test portability follow-up)
> 用途: 提交 Codex 审核后续任务优先级与分解合理性
> 版本: v2 (已修正编码、基线、任务分解、执行顺序)

---

## 零、已完成的近期工作

| Commit | Task | 内容 |
|--------|------|------|
| 1d820d3c | AI-GUARD-FILES-MODE-AND-LARGE-FILE-SCAN-A1 | P1: ai_guard.py --files mode + streaming scan |
| b797f19 | (follow-up) | 12 处 rm -rf 替换为 shutil.rmtree, 53 tests 重跑通过 |

测试可移植性补丁 (rm -rf -> shutil.rmtree) 已在 b797f19 中完成并 commit。53 target tests 在 Windows 环境可复现。

---

## 一、项目现状摘要

- 测试套件: 1268 passed / 2 failed (pre-existing router registry status)
- TaskSpec 总数: 42 个 (.ai/tasks/)
- 证据目录: 38 个 (_evidence/), 34 个 ECS-A2 证据包 ZIP
- 未跟踪文件: 约 200 个 (工作区根目录)
- Live Dispatch: 未授权, 需人类显式授权
- 核心功能完成度: 约 95%, 收尾清理: 约 40%

---

## 二、建议执行顺序 (已根据 Codex 审核反馈调整)

```
阶段 1 (只读清点):  WORKSPACE-CLOSURE-INVENTORY-A1
阶段 2 (治理收尾):  HOOK-FAILURE-SEMANTICS-FINALIZE-A1
阶段 3 (分批清理):  按 inventory 结果分批处理, 每批独立 TaskSpec
阶段 4 (质量加固):  Codex P2/P3 + 结构性缺陷
阶段 5 (授权决策):  人类主导, live dispatch / 项目绑定
```

---

## 三、阶段 1: WORKSPACE-CLOSURE-INVENTORY-A1 (只读, 不修改)

来源: closeout-report, current-task.yaml next_recommended, deferred-files-register

目标: 对工作区根目录约 200 个 untracked 文件生成分类清单。不删除, 不移动, 不归档。

输出格式 (每个文件一行):
```
文件路径 | 分类 | 建议动作 | 风险等级 | 是否有对应 evidence ZIP | 备注
```

分类维度:

1. CDP 临时脚本 (约 35 个): _ask_*.py, _capture_*.py, _submit_*.py, _build_*.py 等
2. 会话证据目录 (约 20 个): _evidence/ 下未被 ZIP 归档的子目录
3. 证据包 ZIP 迭代 (约 15 个): 同一 task 的多轮 ZIP, 需标记最终版本
4. NEG-009 mock fixture 重复 (17 个): _projects/*/NEG-009-secrets-read.json
5. Windows 意外文件: nul (NUL 设备重定向产物)
6. 报告与文档: _reports/PROMPT_*.md 等
7. scripts/_evidence/ 子目录: 脚本运行产物

每条建议动作仅限以下四种之一:
- KEEP: 保留在工作区 (说明理由)
- COMMIT: 应纳入 git 版本控制 (建议归属 TaskSpec)
- ARCHIVE: 移入 _archive/ 或 _evidence/ 归档
- DISCARD: 可安全删除 (说明为何无价值)

验收标准: 输出一份 inventory.yaml 或 inventory.md, 覆盖全部 untracked 文件, 经人工确认后进入阶段 3。

---

## 四、阶段 2: HOOK-FAILURE-SEMANTICS-FINALIZE-A1

来源: closeout-report limitations, EXECUTION_REPORT deferred

目标: 将 hook 失败语义从 "代码实现 + 测试覆盖" 推进到 "文档化 + 审查确认"。

子任务:

1. 检查 docs/agent-runtime/hook-failure-semantics.md 与 v2.4.0 五阶段管线一致性
2. 补充超时行为 (30s ai-guard), advisory vs blocking 决策树
3. 补充 latest.json schema 与 hook 输出不一致时的 fallback 说明
4. 合并 TaskSpec: .ai/tasks/evidence-capture-hook-failure-semantics-a1.yaml (当前 in_progress)
5. 提交审查 (GPT 或 Codex), 获取 accepted verdict

验收标准: 文档完整, 审查 accepted, TaskSpec 状态转 completed。

---

## 五、阶段 3: 按 Inventory 分批清理 (阶段 1 完成后启动)

本阶段必须在阶段 1 (只读清点) 产出 inventory 并经人工确认后才能启动。每个批次需要独立 TaskSpec。

预计批次 (根据当前预估, 阶段 1 后调整):

| 批次 | 预期范围 | 前置条件 |
|------|----------|----------|
| 3a | CDP 临时脚本 triage (保留/归档/删除) | inventory 分类完成 |
| 3b | 证据目录归档 (有 ZIP 的删除原始目录) | inventory 确认 ZIP 覆盖 |
| 3c | ZIP 迭代清理 (只保留最终版本) | inventory 标记最终版本 |
| 3d | NEG-009 fixture 去重 + deny_paths 策略调整 | 需评估 fixture 用途 |
| 3e | nul 文件删除 + scripts/_evidence/ 清理 | 低风险, 可先做 |

风险说明: 涉及删除/归档操作, 每个批次 commit 前必须通过治理 hook 四道门禁。

---

## 六、阶段 4: 质量加固与技术债

### 6a. Codex Review P2/P3 跟进

| 项目 | 优先级 | 描述 |
|------|--------|------|
| PowerShell 空格路径 | P2 | hook 中 $stagedFiles 含空格时参数展开错误, 需 hook-level 修复 + 测试 |
| py_compile CI 集成 | P3 | 在 CI 或 pre-push hook 中加 py_compile 检查 |
| build_evidence_pack.py 拆分 | P2 | 72KB 单体脚本, 按功能拆分为 builder + validators + ZIP 工具 |
| 测试脆弱性 | P3 | 部分测试依赖硬编码路径或特定环境 |

### 6b. 结构性缺陷收尾

| 缺陷 | 描述 | 当前状态 |
|------|------|----------|
| SD-05 | Agent 在 GPT 回复不完整时执行 | 部分修复, capture + validate 脚本已部署 |
| SD-06 | accepted 不产生 next_task_authorization | 部分修复, 模板 + schema 已更新 |

---

## 七、阶段 5: 授权门控 (人类主导)

| 项目 | 状态 | 阻塞原因 |
|------|------|----------|
| Live Dispatch | 未授权 | 需人类显式授权; 建议先做 fresh dry-run |
| tripmark | tab_unresolved | 无法 dispatch 直到 tab 修复 |
| 7 pending projects | 未绑定 | 需逐个绑定验证后才可 dispatch |
| PAPER-C1 | accepted, binding 未提交 | GPT 已接受但 binding commit 未完成 |
| CODEGRAPH-FORK-POOL | review_unverified | 批量审查中未验证 |

---

## 八、in_progress 状态卡住的任务 (需决策)

以下 8 个 TaskSpec 标记 in_progress 但实际未完成。建议作为阶段 1 的伴随动作逐个决策:

| Task ID | Priority | 建议操作 |
|---------|----------|----------|
| HANDOFF-PIPELINE-REFACTOR-A1 | P0 | 评估: 是否已被 CDP 方案替代? 若是则关闭 |
| EVIDENCE-CAPTURE-HOOK-FAILURE-SEMANTICS-A1 | P0 | 合并到阶段 2 (T2) |
| CONTEXT-COMPRESSION-A1 | P1 | ai_guard --files 已修 (1d820d3c), 可重新尝试 commit |
| EVIDENCE-CAPTURE-HOOK-FAILURE-RUNTIME-VALIDATION-A1 | P1 | 检查是否已被 test_hook_failure_semantics.py 覆盖 |
| R18-FOLLOWUP-CLEANUP-A1 | P1 | 检查具体遗留项 |
| R18-WORKSPACE-CLEANUP-A1 | P1 | 可能被阶段 3 覆盖 |
| EVIDENCE-CAPTURE-HOOK-FAILURE-RUNTIME-VALIDATION-CLEANUP-A1 | P2 | 依赖上面第 4 项 |
| R18-EVIDENCE-MAINTENANCE-A1 | P2 | 可能被阶段 3 部分覆盖 |

---

## 九、ready 状态任务 (已规划未启动, 需评估)

| Task ID | Priority | 评估建议 |
|---------|----------|----------|
| m4-m1-s1-status-semantics-unification | P0 | 评估: 状态语义统一是否影响当前运行 |
| t-governance-convergence-20260601 | P0 | 评估: 治理收敛是否仍有未完成项 |
| m4-m0-readiness-snapshot | P1 | 评估: M4 里程碑入口快照 |
| t-chain-evidence-hardening-20260601 | -- | 可能已被 ECS-A2 覆盖 |
| t-dirty-boundary-closure-20260601 | -- | 评估是否仍需 |
| t-review-* (4 个审查任务) | -- | 对应上述任务的审查环节 |
| REVIEW-TEMPLATE-V2 | -- | 模板已 push 但从未提交 GPT 审查, 补审工作量小 |

---

## 十、不在本大纲范围内

- 新功能开发 (如 Paper 实际工作流扩展到真实论文)
- 跨仓库同步 (devframe-control-plane, dev-frame-opencode)
- Live dispatch 的实际执行 (需人类授权后另行规划)
- 新项目绑定 (7 个 pending projects 的具体绑定工作)
