# Single-Project Queue Specification

Field reference for authoring `.queue.json` and batch task files.

## Queue File (`.queue.json`)

Top-level structure:

```json
{
  "queue_id": "my-project-quality",
  "owner": "code-agent",
  "mode": "safe-batch",
  "description": "What this queue checks and why",
  "items": [ ... ]
}
```

### Top-level Fields

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `queue_id` | Yes | string | Unique ID. Convention: `<project>-<purpose>-queue` |
| `owner` | Yes | string | Who runs this. Use `code-agent` for agent-executed queues |
| `mode` | Yes | string | Currently always `"safe-batch"` |
| `description` | Yes | string | Human-readable purpose. Shown in reports |
| `items` | Yes | array | Queue items (tasks to execute). Min 1 |

### Item Fields

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `id` | Yes | string | Unique within queue. Convention: `q-<purpose>` |
| `title` | Yes | string | Human-readable title. Shown in reports |
| `tier` | Yes | int | `0` = auto, `1` = review, `2` = escalate |
| `task_file` | Yes | string | Path to batch task JSON. Relative to repo root |
| `runner` | Yes | string | Path to runner script. Must be in allowlist |
| `status` | Yes | string | Initial status. Use `"pending"` |
| `allowed_files` | No | array | Glob patterns for allowed write targets. **Currently advisory** — reported but not enforced as sandbox |
| `forbidden_files` | No | array | Glob patterns that must not be modified. **Scanned by queue runner** — writing these triggers escalation |
| `expected_artifacts` | No | array | Files that must exist after execution. Missing → failed |
| `escalate_on` | No | array | Triggers: `"failed"`, `"missing_artifact"`, `"timeout"`, `"forbidden_command"` |

## Batch Task File (`.json`)

Top-level structure:

```json
{
  "batch_id": "batch-my-checks",
  "mode": "dry-run",
  "description": "What this batch checks",
  "tasks": [ ... ]
}
```

### Top-level Fields

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `batch_id` | Yes | string | Unique ID. Convention: `batch-<purpose>` |
| `mode` | Yes | string | `"dry-run"` (default). `"apply"` requires user ACK |
| `description` | Yes | string | Human-readable. Shown in batch reports |
| `tasks` | Yes | array | Task definitions. Min 1 |

### Task Fields

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `id` | Yes | string | Unique within batch. Convention: `<check-name>` |
| `title` | Yes | string | Human-readable. Shown in reports |
| `tier` | Yes | int | `0` = auto, `1` = review, `2` = escalate |
| `command` | Yes | string | Shell command to execute |
| `expected_exit_codes` | Yes | array[int] | Acceptable exit codes. Usually `[0]` |
| `required_artifacts` | No | array[string] | Files that must exist post-execution |
| `timeout_seconds` | Yes | int | Max execution time. Hard limit enforced by runner |

## Hard Constraints (enforced by runner)

These are checked automatically by `Run-Batch.ps1` / `Run-WorkQueue.ps1`:

1. **Forbidden command patterns**: The runner scans every `command` for destructive patterns (`rm -rf`, `del /f`, `git push`, `DROP TABLE`, etc.). If found, the task is escalated.
2. **Runner allowlist**: Only allowlisted runners can execute. Adding a runner requires updating `Test-WorkQueue.ps1` and `Run-WorkQueue.ps1`.
3. **Timeout**: Every task has a hard timeout. Exceeding it marks the task as failed.
4. **Artifact check**: If `expected_artifacts` is non-empty, the runner verifies each artifact exists after execution.
5. **Tier 2 escalation**: Any tier=2 item is automatically escalated — the agent must NOT execute it without user ACK.

## Soft Constraints (advisory / report-only)

These are checked and reported but do not block execution:

1. **`allowed_files`**: Reported as informational. The runner does not enforce a sandbox.
2. **`forbidden_files`**: Scanned against actual file writes during execution. If a forbidden file is written, the task escalates.

## Example: Minimal Project Queue

```json
{
  "queue_id": "myproject-quality",
  "owner": "code-agent",
  "mode": "safe-batch",
  "description": "My project's Tier 0 quality checks",
  "items": [
    {
      "id": "q-my-checks",
      "title": "Run project quality batch",
      "tier": 0,
      "task_file": "scripts/my-batch.json",
      "runner": "D:\\agent-acceptance\\scripts\\Run-Batch.ps1",
      "status": "pending",
      "escalate_on": ["failed", "timeout"]
    }
  ]
}
```

## Example: Minimal Batch Task File

```json
{
  "batch_id": "batch-my-checks",
  "mode": "dry-run",
  "description": "My project's quality checks",
  "tasks": [
    {
      "id": "lint",
      "title": "Run linter",
      "tier": 0,
      "command": "npm run lint",
      "expected_exit_codes": [0],
      "timeout_seconds": 60
    },
    {
      "id": "typecheck",
      "title": "Type-check source",
      "tier": 0,
      "command": "npx tsc --noEmit",
      "expected_exit_codes": [0],
      "timeout_seconds": 60
    },
    {
      "id": "test",
      "title": "Run unit tests",
      "tier": 0,
      "command": "npm test",
      "expected_exit_codes": [0],
      "timeout_seconds": 120
    }
  ]
}
```
