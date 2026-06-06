# PAPER-C1 Real-Paper Pilot Safety Protocol

> Status: draft_for_review
> Scope: protocol_only
> Primary repo: agent-acceptance
> Safety mode: no real paper execution

## 1. Purpose

PAPER-C1 defines the safety gate that must exist before any future real-paper pilot can be considered. This task does not process real papers, does not inspect user private text, and does not enable a runtime path for real-paper execution.

The only allowed materials for PAPER-C1 are:

- synthetic placeholders
- redacted protocol examples
- contract text
- validation tests
- closure evidence

## 2. Non-Negotiable Boundaries

The real-paper pilot remains blocked unless a later accepted task explicitly changes the authorization state.

Current state:

```yaml
real_paper_execution_allowed: false
real_paper_full_text_allowed: false
user_private_text_allowed: false
memory_write_with_paper_content_allowed: false
external_upload_allowed: false
live_cdp_allowed: false
```

Fail closed when any of these are observed:

- full paper text is submitted or requested
- user private text is present
- authorization is missing, ambiguous, stale, or not task-scoped
- redaction report is missing
- privacy attestation is missing
- evidence pack contains paper content instead of redacted metadata
- memory write contains paper content, paper excerpts, citation original text, user identity, or unpublished argument
- external upload is attempted
- live CDP/browser capture is requested for paper content
- historical evidence is deleted, moved, renamed, overwritten, or regenerated without trace

## 3. Authorization Policy

Future real-paper pilot authorization must be explicit, current, and scoped to a single task.

Required authorization fields:

```yaml
authorization_id: string
authorized_by: human_user
authorized_at_utc: string
task_id: string
allowed_input_classification: user_authorized_excerpt
allowed_operations:
  - classify
  - redact
  - summarize_metadata
expires_at_utc: string
revocation_supported: true
```

Authorization does not permit:

- ingesting full paper text
- storing paper content
- adding paper text to fixtures
- writing paper content to memory
- uploading paper text externally
- using live CDP for paper content

## 4. Redaction Policy

Before any review, the input must be reduced to redacted metadata or a task-scoped excerpt. The redaction report must state what was removed and what remains.

Allowed evidence after redaction:

- task id
- task type
- data classification
- input version hash
- output version hash when applicable
- redaction actions
- privacy attestation
- workflow logs that contain no paper content
- reviewer verdict and blocking issue ids

Forbidden evidence:

- full paper text
- unredacted excerpt
- author identity
- school, advisor, student id, email, submission id, or journal tracking id
- citation original text copied from the paper
- unpublished claims or argument text
- raw chat transcript containing paper content

## 5. Input Classification Rules

| Classification | Current handling |
| --- | --- |
| synthetic | allowed for tests and fixtures |
| redacted | allowed for evidence after privacy validation |
| user_authorized_excerpt | blocked unless explicit task-scoped authorization exists |
| real_paper_full_text | blocked in PAPER-C1 |

Any classifier uncertainty must resolve to blocked.

## 6. Evidence-Pack Rules

Every future pilot evidence pack must include:

- `PAPER_TASK_INPUT.yaml`
- `PAPER_TASK_OUTPUT.yaml`
- `PRIVACY_ATTESTATION.yaml`
- `REDACTION_REPORT.yaml`
- `PACK_MANIFEST.md`
- validation output from the paper task validator
- negative fail-closed proof for at least one privacy violation

The evidence pack must not contain real paper content. Hashes and file lists must be internally consistent.

## 7. Memory Policy

Memory writes are allowed only for redacted workflow lessons. A memory candidate must be rejected if it includes paper content, paper excerpts, citation original text, identity data, unpublished argument, or task-specific private details.

Allowed memory example:

```yaml
memory_policy: redacted_workflow_lesson_only
lesson: "A missing REDACTION_REPORT.yaml caused the paper validator to fail closed."
contains_paper_content: false
```

Forbidden memory example:

```yaml
memory_policy: paper_content
blocked_reason: memory_write_contains_paper_content
content: SYNTHETIC_PLACEHOLDER_ONLY_DO_NOT_REPLACE_WITH_REAL_TEXT
```

## 8. Exit Criteria

PAPER-C1 can be accepted only when:

- the protocol is present and says real-paper execution is still disabled
- the safety contract is machine-readable
- negative privacy fixtures use synthetic placeholders only
- tests verify the safety contract and fixtures
- an evidence pack is created without real paper content
- GPT review accepts the evidence pack
