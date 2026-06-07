# Dirty Worktree Split

> 主题: dirty_worktree_split
> 关联任务: GROUP-01, GROUP-02, GROUP-03, GROUP-04, GROUP-05, GROUP-06
> 最后更新: 2026-06-07
> 阅读时机: 任何涉及 git commit/push 操作前

## 核心原则

本地 worktree 包含大量未追踪/修改文件（dirty state）。只有经过 GPT accepted 的 GROUP selected files 才能被 commit + push。

## 禁止 Whole-Dirty-Tree Commit

每个 GROUP binding 必须声明：
- `whole_dirty_worktree_accepted: false`
- `scope_limit: "only GROUP-XX selected files"`

## 已知 Dirty Baseline

本地始终存在的 dirty 文件（不得提交）：
- HANDOFF_REPLY_V4.txt 的删除
- archive/draft-hooks/*.ps1 的修改
- runs/*/POST_REVIEW_ROUTE.json 的修改
- .tmpconfig/ .tmpdata/ __pycache__/
- root scratch GPT 文件（GPT_REVIEW_RESULT.md 等）

## 操作流程

1. 每次提交前 git status --short 确认 scope
2. 只 git add selected files，不使用 git add -A
3. git diff --cached 确认暂存区无 dirty baseline
4. 禁止 --no-verify 跳过 gate
