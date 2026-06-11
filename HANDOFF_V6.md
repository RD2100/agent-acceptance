# HANDOFF V6 — DevFrame Agent Acceptance + Control Plane

> 生成时间: 2026-06-07T10:05:00+08:00
> 交接原因: GPT 对话 47 replies，本会话 40+ assistant messages，上下文膨胀接近阈值
> 上游对话: https://chatgpt.com/c/6a23dd8c-4550-83a8-bdee-76ca5a982edb (47 assistant replies)
> 交接至: new-conversation (待创建)

---

## 1. 项目定位

DevFrame 是一个三层工作流治理体系，用 evidence-first + GPT 审查 + 自动化流水线管理 AI 辅助的软件工程任务。

| 层 | 仓库 | 职责 |
|------|------|------|
| 规范验收层 | agent-acceptance (D:\agent-acceptance) | 合约、schema、validator、GPT review 模板、pre-commit/pre-push gate |
| 编排控制层 | devframe-control-plane (D:\devframe-control-plane) | pipeline runner、state machine、submission adapter、CDP bridge、CLI |
| 执行层 | dev-frame-opencode (D:\dev-frame-opencode) | 具体代码修改和测试运行 |

核心价值：把多阶段 Agent/GPT 工作流变成可冷启动、可迁移、可审核、可交接的 evidence-first 框架。

---

## 2. 架构

每个非平凡任务的闭环路径：
1. authorization（构建授权证据包 ZIP → CDP 提交 GPT → 等待审查）
2. execution（GPT accepted 后执行代码变更）
3. evidence（收集 TEST_OUTPUT、SAFETY_ATTESTATION、CLOSURE_REPORT）
4. closure（构建闭合证据包 ZIP → CDP 提交 GPT → GPT accepted → closed）
5. chain（持久化到 DECISION_LEDGER，更新 PROJECT_HISTORY.md）

关键规则：
- commit + push ≠ done。正确终点是 GPT accepted + ledger entry
- pre-push gate step 2.6 强制检查 GPT 审查状态
- 跳过 GPT 审查的任务不得声称 closed

---

## 3. 已完成阶段

### 全部 GROUP backfill (2026-06-07)

| 任务 | 内容 | 状态 |
|------|------|------|
| GROUP-01 | contracts + policies + tests (6 schema + 12 policy + 12 test files) | accepted |
| GROUP-02 | scripts/validate_paper_task.py + test_paper_task_validator.py | accepted |
| GROUP-03 | frozen memory compiler output | accepted |
| GROUP-04 | capability inventory + routing cleanup | accepted |
| GROUP-05 | chain-evidence hardening R3 (ai_guard + go_evidence + schema) | accepted |
| GROUP-06 | workflow closure validator for control-plane | accepted |
| WorkQueue | specialized batches + Run-WorkQueue propagation | accepted |
| REPO-CODE-VERIFICATION-R3 | remote origin/master clean verification | accepted |
| CONTEXT-COMPRESSION-A1 | privacy-safe context compression layer | **accepted R6, binding in progress** |

### 论文任务 (已闭合)
- PAPER-C1: real paper safety protocol (accepted)
- PAPER-C2: synthetic-only authorization/redaction gate (closed)

### 测试状态
- Full test suite: 232 PASS, 21 warnings
- agent-acceptance: 232 tests (170 baseline + 51 new + 11 others)
- devframe-control-plane: 65 PASS

---

## 4. 当前状态

```yaml
current_state:
  task_in_progress: CONTEXT-COMPRESSION-A1-BINDING
  task_status:
    implementation: COMPLETE
    gpt_review: accepted (R6)
    binding: PENDING (PROJECT_HISTORY + LEDGER updated but NOT committed)
    commit: BLOCKED (pre-commit gate ai_guard.py scans entire working tree)
  blocker_detail: >
    ai_guard.py TaskSpec scope scan checks git diff HEAD (entire working tree,
    not just staged files). 7 dirty-worktree files flagged that are NOT staged:
    HANDOFF_REPLY_V4.txt, archive/draft-hooks/*.ps1 (3), runs/*/POST_REVIEW_ROUTE.json (2),
    hooks/sealed-files-manifest.json. All 107 staged files are clean and covered
    by TaskSpec write_set. GPT adjudication requested but not yet responded.
  resolution_needed: >
    Either GPT authorizes --no-verify, or ai_guard.py is fixed to scan staged-only,
    or dirty files are temporarily stashed.
```

---

## 5. 安全边界

永久禁止：
- guard removal
- evidence cleanup/deletion/movement/renaming
- cookies/session/browser profile 读取
- 真实用户数据提交
- CURRENT_STATE/CURRENT_ROUTE 非授权修改
- DECISION_LEDGER 非授权写入
- whole-dirty-tree commit
- 论文正文 / raw transcript / private text 写入 memory
- 跳过 GPT 审查声称 closed

Fail-Closed：
- review_unverified → stop
- REVIEW_RUN_ID mismatch → stop
- CDP unavailable → stop
- timeout → stop
- 测试失败 → 不得继续

---

## 6. 关键教训

1. PROJECT_HISTORY.md 是唯一蓝本，永不删除，每次任务闭合后追加
2. HANDOFF.md 是快照，跨对话使用，不要单独维护
3. 不要用脚本切片编辑包含中文的文件（字节偏移会漂移）
4. 上传给 GPT 的文件必须是 git 干净版本
5. 闭合证据迭代有递减回报——2 轮后仍 blocked 用 accept_with_evidence_limitation
6. CDP 通信需要 Chrome --remote-debugging-port=9222 --user-data-dir=.chrome-cdp-profile
7. 每次 CDP 提交必须保存 GPT_REPLY.txt + SHA256
8. evidence pack 必须是 actual deliverables + raw git evidence，不是 summary-only
9. privacy guard 不能用 file-level exemption，必须 per-line 判断
10. pre-commit gate 的 ai_guard.py 会扫描整个 working tree（含未暂存的 dirty files）

---

## 7. 下一步计划

### 立即（新 Agent 接手第一件事）

```yaml
immediate:
  task: CONTEXT-COMPRESSION-A1-BINDING
  goal: "提交所有 selected files + binding records，完成闭合"
  steps:
    - "解决 pre-commit gate ai_guard.py 扫描 dirty worktree 的问题"
    - "选项 A: 等待 GPT adjudication 回复（可能授权 --no-verify）"
    - "选项 B: 临时 stash dirty files，commit selected，再 restore"
    - "选项 C: 先 fix ai_guard.py 只扫描 staged 文件"
    - "git commit selected files with message 'feat: implement CONTEXT-COMPRESSION-A1...'"
    - "更新 PROJECT_HISTORY.md 的 implementation_commit 和 pushed_to_github"
  staged_files: 107 (all CONTEXT-COMPRESSION-A1 selected files, verified clean)
  evidence_pack: evidence_packs/context-compression-a1/closure-pack-r6.zip
  gpt_verdict: accepted
```

### 后续（GPT 推荐）

```yaml
next_candidates:
  - "GPT-REVIEW-QUEUE-A1: GPT 审查队列管理"
  - "TDD-GOVERNANCE-A1: TDD 治理集成"
  - "ai_guard.py 修复: 只扫描 staged files"
  - "不做: PAPER-C3 / 真实论文处理 / dirty worktree cleanup"
```

---

## 8. GPT 响应格式

每次提交 evidence pack 给 GPT 时，要求 GPT 返回结构化 YAML：

```yaml
overall_judgment: accepted | blocked
reviewer_type: gpt
task_id: <TASK_ID>
evidence_pack_reviewed: true
blocking_issues: []
required_fixes: []
next_task_authorization:
  authorized: yes | no
  execute_immediately: yes | no
  ask_before_starting: yes | no
  recommended_task_id: <NEXT_TASK>
```

结束标记: END_OF_GPT_RESPONSE

---

## 9. 交接协议

新 Agent 接手时：
1. 读取本 HANDOFF_V6.md（本文档）
2. 读取 BOOT_CONTEXT.md（冷启动短入口，~3K chars）
3. 读取 memory/index.md（记忆索引）
4. 按需读取 PROJECT_HISTORY.md（仅当需要完整历史）
5. 验证 handoff_understood=yes
6. 开始执行 CONTEXT-COMPRESSION-A1-BINDING

CDP 连接信息：
- Chrome: --remote-debugging-port=9222 --user-data-dir=D:\dev-frame-opencode\.chrome-cdp-profile
- GPT 对话: https://chatgpt.com/c/6a23dd8c-4550-83a8-bdee-76ca5a982edb
- 连接方式: pw.chromium.connect_over_cdp('http://localhost:9222')

END_OF_HANDOFF
