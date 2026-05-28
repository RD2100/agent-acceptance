# skills-inbox 完整清单

> 生成时间: 2026-05-28
> CodeGraph 索引状态: 243 files indexed, 2193 nodes, 4539 edges, 8.42 MB
> 语言分布: TypeScript(178), TSX(36), JavaScript(16), YAML(7), Python(6)

## 目录结构概览

```
skills-inbox/
├── allowlist.draft.json           (1 file)
├── allowlist.example.json         (1 file)
├── external/                      (2 files)
│   ├── candidate-index.md
│   └── README.md
├── quarantine/                    (404 files)
│   ├── README.md
│   └── sources/
│       └── Understand-Anything__478962e/  (403 files)
├── source-lock-plans/             (3 files)
│   ├── INDEX.md
│   ├── Taste-Skill.plan.json
│   └── Understand-Anything.plan.json
├── source-lock-requests/          (8 files)
│   ├── INDEX.md
│   ├── README.md
│   ├── example-source-lock-request.json
│   ├── phase-6c-url-approval.json
│   ├── Taste-Skill.request.json
│   ├── Understand-Anything.request.json
│   ├── ECC.request.json
│   ├── AnySearch-Skill.request.json
│   └── addyosmani-agent-skills-zh.request.json
└── taste-skill/                   (41 files)
    ├── skill.sh
    ├── README.md
    ├── CHANGELOG.md
    ├── LICENSE
    ├── SOURCELOCK.json
    ├── REVIEW-NOTES.md
    ├── .github/
    ├── assets/
    ├── examples/
    ├── research/
    └── skills/                    (13 个 sub-skill)
```

## 统计汇总

| 区域 | 文件数 | 说明 |
|------|--------|------|
| 根目录 | 2 | allowlist.draft.json, allowlist.example.json |
| external/ | 2 | 候选索引 + README |
| quarantine/ | 404 | Understand-Anything 完整克隆 (403) + README (1) |
| source-lock-plans/ | 3 | INDEX + 2 个计划 JSON |
| source-lock-requests/ | 8 | INDEX + 6 个请求 JSON + README |
| taste-skill/ | 41 | 非隔离区的 Taste-Skill（含13个sub-skill） |
| **合计** | **462** | |

## Taste-Skill 的 13 个 Sub-Skill

| # | Sub-Skill | SKILL.md | 分类 (local-skill-intake.md) |
|---|-----------|----------|------------------------------|
| 1 | taste-skill | skills/taste-skill/SKILL.md | reference_only (Design/Media) |
| 2 | taste-skill-v1 | skills/taste-skill-v1/SKILL.md | reference_only (Design/Media) |
| 3 | gpt-tasteskill | skills/gpt-tasteskill/SKILL.md | reference_only (Design/Media) |
| 4 | image-to-code-skill | skills/image-to-code-skill/SKILL.md | reference_only (Design/Media) |
| 5 | imagegen-frontend-web | skills/imagegen-frontend-web/SKILL.md | reference_only (Design/Media) |
| 6 | imagegen-frontend-mobile | skills/imagegen-frontend-mobile/SKILL.md | reference_only (Design/Media) |
| 7 | brandkit | skills/brandkit/SKILL.md | reference_only (Design/Media) |
| 8 | redesign-skill | skills/redesign-skill/SKILL.md | reference_only (Design/Media) |
| 9 | soft-skill | skills/soft-skill/SKILL.md | reference_only (Design/Media) |
| 10 | output-skill | skills/output-skill/SKILL.md | reference_only (Design/Media) |
| 11 | minimalist-skill | skills/minimalist-skill/SKILL.md | reference_only (Design/Media) |
| 12 | brutalist-skill | skills/brutalist-skill/SKILL.md | reference_only (Design/Media) |
| 13 | stitch-skill | skills/stitch-skill/SKILL.md | reference_only (Design/Media) |

**分类依据**: 全部 13 个 sub-skill 属于 Design/Media/Doc 类型（前端设计/图像生成/品牌工具/风格主题），按 local-skill-intake.md §3 分类为 `reference_only`。

## Quarantine（隔离区）分类

| Skill | commit | 状态 | 文件数 | 分类 |
|-------|--------|------|--------|------|
| Understand-Anything__478962e | 478962e | quarantine_permanent | 403 | reject (critical: Node/pnpm monorepo, IDE plugins, install scripts) |

**注**: 目录 `skills-inbox/quarantine/sources/Taste-Skill__3c7017d/` 在治理文档中被引用但实际不存在。Taste-Skill 的代码位于 `skills-inbox/taste-skill/`（非隔离区），仅计划 JSON 在隔离相关目录中。

## External Candidate Index 分类

| # | Project | disposition | risk | 
|---|---------|-------------|------|
| 1 | ECC | defer | high |
| 2 | Taste-Skill | candidate | medium |
| 3 | AnySearch Skill | defer | high |
| 4 | AnySearch MCP Server | reject | critical |
| 5 | Understand Anything | quarantine_permanent | critical |
| 6 | Anthropic Cybersecurity Skills | reject | critical |
| 7 | Andrej Karpathy Skills | reference_only | medium |
| 8 | UI-TARS Desktop | reject | critical |
| 9 | addyosmani-agent-skills-zh | defer | high |

## CodeGraph 索引状态

| 指标 | 值 |
|------|-----|
| 文件索引 | 243 |
| 总节点 | 2193 |
| 总边 | 4539 |
| 数据库大小 | 8.42 MB |
| 后端 | node:sqlite (WAL + FTS5) |
| 语言 | TypeScript(178), TSX(36), JavaScript(16), YAML(7), Python(6) |
| 主要节点类型 | import(720), function(413), method(315), constant(267), file(236) |

**按 R4 策略**: 当前索引非空，trusted_for_current_run 可由 agent 判断。但节点数 (2193) 远大于 accept 项目自身代码量，大部分来自 Understand Anything 隔离源码。
