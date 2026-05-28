# Lessons Learned — RD2100 Agent Runtime

> Running log of operational discoveries. Each entry feeds back into rules, profiles, or protocol.
> Format: Date | Context | Problem → Root Cause → Solution → Derived Rule/Change

---

## LL-001: (status: active) opencode Desktop Conflict

- **Date**: 2026-05-28
- **Context**: SADP dispatch testing, all opencode run commands timing out
- **Problem**: v4-pro dispatches consistently 30s timeout with no output
- **Root Cause**: opencode desktop app holding process lock, CLI dispatch blocked
- **Solution**: Close desktop app before CLI dispatch
- **Derived**: Added to `dispatch-model-profiles.md` Failure Pattern Library
- **Changed Files**: `dispatch-model-profiles.md`

## LL-002: (status: active) v4-pro PS1 File Read Timeout

- **Date**: 2026-05-28
- **Context**: Governance audit — read hooks/*.ps1 via opencode
- **Problem**: Any .ps1 file >100 lines causes 30s timeout on v4-pro
- **Root Cause**: DeepSeek v4-pro tool-call timeout shorter than file read duration for large files
- **Solution**: Route PS1/code file audits to deepseek-chat or Codex direct
- **Derived**: Model selection rule in dispatch-model-profiles.md
- **Changed Files**: `dispatch-model-profiles.md`, SADP §4.6

## LL-003: (status: active) v4-pro Multi-File Cap = 2

- **Date**: 2026-05-28
- **Context**: Governance audit — batch audit of 8 files
- **Problem**: 3+ .md files in single prompt → 30s timeout
- **Root Cause**: Agent serially reads files; cumulative tool-call time exceeds v4-pro limit
- **Solution**: Cap v4-pro at 2 files/dispatch; use deepseek-chat for 3-5 files; Codex direct for 6+
- **Derived**: Quick Reference table in dispatch-model-profiles.md
- **Changed Files**: `dispatch-model-profiles.md`

## LL-004: (status: active) --add-dir Not Supported by opencode run

- **Date**: 2026-05-28
- **Context**: Attempted to give agent explicit directory access
- **Problem**: `opencode run --add-dir D:\agent-acceptance` → exit 1, shows help
- **Root Cause**: `--add-dir` is not a valid option for `opencode run` subcommand
- **Solution**: Use absolute paths in prompt; agent has filesystem access via build agent permissions
- **Derived**: Documented in build agent limitations
- **Changed Files**: `dispatch-model-profiles.md`

## LL-005: (status: active) agent create Hangs on v4-pro

- **Date**: 2026-05-28
- **Context**: Attempted to create dedicated SADP executor agent
- **Problem**: `opencode agent create` → "Generating agent configuration..." loops forever
- **Root Cause**: Agent creation calls model to generate config; v4-pro tool timeout prevents completion
- **Solution**: Use existing `build` agent; no custom agent needed for current dispatch patterns
- **Derived**: Skip agent creation in Phase 0-5; revisit when model supports it
- **Changed Files**: `dispatch-model-profiles.md`

## LL-006: (status: active) SADP Dispatch = Real but Constrained

- **Date**: 2026-05-28
- **Context**: End-to-end SADP validation
- **Finding**: opencode dispatch IS real multi-agent (unique sessionID, cost >0, tokens >0)
- **Finding**: But practical limits (2 files/v4-pro, 5 files/chat) mean plan agent must decide: dispatch or self-execute
- **Finding**: Trust Record (sessionID + timestamp + tokens + cost) prevents plan agent from faking dispatches
- **Derived**: SADP dispatch decision tree needed
- **Changed Files**: `sub-agent-dispatch-protocol.md` §2.1, §4.6

---

## How to Add a Lesson

1. Assign next LL-XXX number
2. Fill all fields: Date, Context, Problem, Root Cause, Solution, Derived, Changed Files
3. If a rule should be created/modified, reference it in Derived
4. If model behavior changes, update `dispatch-model-profiles.md`
5. If protocol changes, update `sub-agent-dispatch-protocol.md`

---

> **Count**: 6 lessons | **Period**: 2026-05-28 (single session)

## LL-007: (status: active) Prompt-Induced Redundant Construction

- **Date**: 2026-05-28
- **Pattern Name**: Prompt-Induced Redundant Construction
- **Context**: User proposed "建立通用型框架去调用资源". Agent agreed and began designing new Resource Activation Framework.
- **Problem**: capability-inventory (28 entries) + SADP dispatch protocol already covered resource invocation. New framework was redundant.
- **Root Cause**: 
  1. Compliance bias — agent treated user proposal as task goal, not hypothesis to verify
  2. Action reward bias — "build new" felt more productive than "existing is sufficient"
  3. No mandatory pre-check — inventory was available but not forced as decision gate
  4. No veto mechanism — plan agent created task, execute agent would have blindly executed
- **Solution**:
  1. core-008: Resource Sufficiency — Prove Gap Before Any Action (P0, universal)
  2. Gate 0: Reuse-before-Build Check — mandatory before any construction TaskSpec
  3. Execute agent veto right — can reject redundant TaskSpecs
  4. CLAUDE.md: Reuse-before-Build summary rule
- **Derived Pattern**: `Prompt-Induced Redundant Construction` — when user instruction implies "build X", agent defaults to compliance. Trigger words: "建立/新建/设计/重构/通用化/抽象化/框架"
- **Prevention**: Gate 0 must run before TaskSpec creation. Trigger words → auto-trigger Gate 0.
- **Changed Files**: `rules/core.md` (+core-008), `sub-agent-dispatch-protocol.md` (§0), `CLAUDE.md`, `lessons-learned.md` (LL-007)


---

## Knowledge Metabolism

Three-tier classification for all knowledge entries:

| Tier | Name | Behavior | Constraint |
|------|------|----------|------------|
| 3 | **Incident** | Specific event. Does not constrain execution directly. | 3 incidents → can promote to pattern |
| 2 | **Pattern** | Recurring failure type. Triggers retrieval but not blocking. | 3 validations → can promote to principle |
| 1 | **Principle** | Stable rule. P0/P1 enforcement. Review-gated modification. | 3+ false positives → downgrade to pattern |

**Lifecycle Rules:**
1. 3 similar incidents → reviewer may promote to 1 pattern
2. Pattern validated 3+ times with no false positives → reviewer may promote to principle
3. Principle causing 3+ false positives → must downgrade to pattern
4. Pattern not triggered in 90 days → archive
5. Archived items do not enter daily decision context (kept for historical reference only)

**Lesson Status Legend:**
- `active` — currently constraining decisions
- `watch` — monitoring, not yet blocking
- `deprecated` — superseded by newer lesson or rule
- `archived` — historical only, not in decision path
