# GPT Review Prompt — 仓库代码核验

## 任务
审查 agent-acceptance GitHub 远程仓库的当前提交历史，核验：
1. 是否只提交了已 GPT-accepted 的 GROUP selected files
2. 是否夹带了 dirty baseline (未授权文件、缓存、临时数据等)

## 背景
agent-acceptance 仓库采用 evidence-first 工作流。本地 worktree 包含大量未追踪文件（dirty state），但只有经过 GPT accepted 的 GROUP selected files 才应被 commit + push 到 GitHub。

已 accepted 的两个 GROUP：
- **GROUP-01**: contracts + policies + tests (flow runner contract backfill)
- **GROUP-02**: scripts/validate_paper_task.py + tests/test_paper_task_validator.py (PAPER-A3 validator residual)

## 核验方法
完整的证据报告位于附件 `REPO_CODE_VERIFICATION_REPORT.md`，包含：
1. git status --short (本地工作区全景)
2. git log --oneline -n 20 (提交历史)
3. git show --stat (逐提交文件清单)
4. git diff (提交范围变更)
5. git ls-files (敏感模式扫描：__pycache__, *.pyc, .tmpconfig, .tmpdata)
6. PROJECT_HISTORY.md binding 记录
7. WORKFLOW_AUDIT_LEDGER.yaml binding 记录
8. PACK_MANIFEST.md + SHA256

## 审查要点
- [ ] 远程仓库的 commit 文件清单是否与 GROUP-01/GROUP-02 selected files 一致
- [ ] 是否存在 `__pycache__/`, `*.pyc`, `.tmpconfig/`, `.tmpdata/` 被追踪
- [ ] `whole_dirty_worktree_accepted: false` 是否正确声明
- [ ] binding 记录与 implementation commits 是否对账一致
- [ ] SHA256 校验链是否完整

## 判定标准
- 全部 ✅ → accepted
- 发现未授权文件 → blocked，需回滚和重新提交
- 发现缓存/临时文件被追踪 → blocked，需清理后重新提交
