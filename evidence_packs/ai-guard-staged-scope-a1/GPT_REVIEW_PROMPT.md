# GPT Review Prompt — AI-GUARD-STAGED-SCOPE-A1 R3

## What was done
ai_guard.py `task` mode now scans ONLY staged files. `audit` mode scans full tree.

## Verify in ZIP
1. actual_deliverables/tools/ai_guard.py: task mode = git_staged_files(), audit mode = git_changed_files()
2. actual_deliverables/test_ai_guard_staged_scope.py: 7 real git fixture tests
3. reports/TARGETED_TEST_OUTPUT.txt: 7 passed
4. reports/FULL_TEST_OUTPUT.txt: 239 passed
5. reports/AI_GUARD_TASK_MODE_OUTPUT.txt: 0 errors on CONTEXT-COMPRESSION-A1

## Changes
- task mode: staged ONLY for ALL checks (scope, deny, secret, restricted)
- audit mode: full working-tree scan (separate mode)
- --root flag for testability
- Guard NOT disabled, NOT weakened

## Tests (7, all with real git repos)
- unstaged secret does not block clean staged commit
- staged forbidden marker fails closed
- task mode ignores unstaged secrets
- audit mode catches working-tree modified secrets
- 3 structural fail-closed checks

Return: overall_judgment: accepted|blocked
END_OF_GPT_RESPONSE
