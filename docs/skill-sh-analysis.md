# skill.sh 安全性分析 — Taste-Skill

> 分析目标: `skills-inbox/taste-skill/skill.sh`
> 分析日期: 2026-05-28
> 方法: 静态源码阅读（未执行）
> 治理合规: 读取源码是允许的；Do Not 清单禁止的是执行 skill.sh，读取不在禁止之列

## 源码内容

```bash
#!/usr/bin/env bash

# Local skill registry
declare -A SKILLS=(
  [taste-skill]="skills/taste-skill/SKILL.md"
  [taste-skill-v1]="skills/taste-skill-v1/SKILL.md"
  [gpt-taste]="skills/gpt-tasteskill/SKILL.md"
  [image-to-code-skill]="skills/image-to-code-skill/SKILL.md"
  [imagegen-frontend-web]="skills/imagegen-frontend-web/SKILL.md"
  [imagegen-frontend-mobile]="skills/imagegen-frontend-mobile/SKILL.md"
  [brandkit]="skills/brandkit/SKILL.md"
  [redesign-skill]="skills/redesign-skill/SKILL.md"
  [soft-skill]="skills/soft-skill/SKILL.md"
  [output-skill]="skills/output-skill/SKILL.md"
  [minimalist-skill]="skills/minimalist-skill/SKILL.md"
  [brutalist-skill]="skills/brutalist-skill/SKILL.md"
  [stitch-skill]="skills/stitch-skill/SKILL.md"
)

if [[ $# -eq 0 ]]; then
  echo "Usage: source ./skill.sh <skill-name>"
  echo "Available skills: ${!SKILLS[@]}"
else
  echo "${SKILLS[$1]}"
fi
```

## 行为分析

| 检查项 | 结果 | 说明 |
|--------|------|------|
| 网络请求 | 无 | 无 curl/wget/fetch |
| 文件写入 | 无 | 仅 echo 到 stdout |
| 进程启动 | 无 | 无 exec/eval/system/source |
| 权限提升 | 无 | 无 sudo/su |
| 环境变量修改 | 无 | 无 export/set |
| 加密/混淆 | 无 | 纯文本 bash |
| 外部命令调用 | 仅 `echo` | bash built-in |
| 文件系统遍历 | 无 | 无 find/ls/read |
| MCP/Agent 交互 | 无 | 纯 CLI echo |

## 结论

**风险等级: 极低 (negligible)**

skill.sh 是一个纯静态的查找表（bash 关联数组），将 skill 名称映射到对应的 SKILL.md 文件路径。它:
1. 不执行任何安装操作
2. 不下载任何外部资源
3. 不修改文件系统
4. 不调用网络
5. 不启动子进程
6. 只做一件事: `echo` 输出路径字符串

它确实如描述所言：只是一个 shell 包装器，不会实际安装任何东西。

## 与 Do Not 条款的对照

| Do Not 条款 | 是否触发 |
|-------------|---------|
| Do not execute skill.sh | ✅ 未触发（仅读取，未执行） |
| Do not install Taste-Skill | ✅ 未触发 |
| Do not execute any quarantined source | ✅ 未触发 |

**注意**: 尽管 skill.sh 本身无害，治理文档明确禁止执行它。本分析仅基于静态阅读。
