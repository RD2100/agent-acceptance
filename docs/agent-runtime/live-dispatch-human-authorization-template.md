# Live Dispatch Human Authorization Template

**This document must be completed by a human operator before any live dispatch is executed.**

---

## Authorization Record

| Field | Value |
|---|---|
| Authorization ID | _(auto-generated on approval)_ |
| Date | _(YYYY-MM-DD)_ |
| Authorizer | _(human operator name/ID)_ |
| Task ID | _(TaskSpec task_id)_ |
| Dispatch scope | _(single project / multi-project)_ |

## Pre-Authorization Checklist

The following must all be confirmed before authorization is granted:

### Mandatory (all must be PASS)

- [ ] **Binding conflict resolved:** dev-frame-writing and dev-frame-opencode have distinct conversation_ids
- [ ] **Registry capacity compliant:** total_projects <= max_registered_projects
- [ ] **Fresh dry-run passed:** dry_run_dispatch_10.py executed within 1 hour, target project classified as `dispatchable`
- [ ] **Hook pipeline passing:** latest.json shows overall_result = PASS, all blocking stages exit_code 0
- [ ] **Evidence capture ready:** build_evidence_pack.py operational, evidence-manifest.schema.json aligned

### Target Project Confirmation

- [ ] **Target project:** _(project_id)_
- [ ] **Target conversation:** _(conversation_id, first 8 chars)_
- [ ] **Target chat URL:** _(full ChatGPT URL)_
- [ ] **Tab target resolved:** target_id confirmed via CDP `/json` page list
- [ ] **Chrome instance running:** localhost:9222 responsive

### Safety Constraints

- [ ] **Single dispatch only:** This authorization covers ONE dispatch event to ONE project
- [ ] **No batch dispatch:** Multi-project dispatch requires separate authorization
- [ ] **Evidence mandatory:** Evidence pack must be built for this dispatch
- [ ] **GPT review required:** Dispatch result must be submitted for GPT review
- [ ] **Rollback plan reviewed:** Operator has read `docs/agent-runtime/live-dispatch-rollback-plan.md`

## Authorization Decision

- [ ] **AUTHORIZED** -- All checks passed, live dispatch may proceed
- [ ] **DENIED** -- Authorization refused (reason below)
- [ ] **DEFERRED** -- Not yet ready (conditions below)

### If Denied or Deferred

**Reason:**

___________________________________________________________________________

___________________________________________________________________________

**Conditions for re-evaluation:**

___________________________________________________________________________

## Post-Dispatch Confirmation

_(To be completed after dispatch executes)_

| Field | Value |
|---|---|
| Dispatch executed at | _(ISO-8601 timestamp)_ |
| Packet sent | _(yes/no)_ |
| GPT response received | _(yes/no)_ |
| Evidence pack built | _(yes/no)_ |
| Evidence pack manifest valid | _(yes/no)_ |
| GPT review submitted | _(yes/no)_ |
| GPT review verdict | _(accepted / needs_revision / blocked)_ |
| Rollback needed | _(yes/no)_ |

## Signatures

| Role | Name | Date | Signature |
|---|---|---|---|
| Authorizer | | | |
| Operator | | | |
| Reviewer | | | |

---

**Important:** This template is a governance artifact. Live dispatch without human authorization violates the `human_gated_for_external_runtime_execution` policy defined in `CONVERSATION_BINDING.json` and constitutes a governance violation.
