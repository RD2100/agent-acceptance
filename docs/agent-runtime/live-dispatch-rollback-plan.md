# Live Dispatch Rollback Plan

**Task:** LIVE-DISPATCH-READINESS-REVIEW-A1
**Date:** 2026-06-12
**Scope:** Rollback procedures for live dispatch events

---

## Rollback Triggers

A rollback should be initiated when any of the following occur:

1. **Dispatch misdirection:** Packet sent to wrong conversation/tab
2. **GPT response anomaly:** Unexpected, incoherent, or missing GPT response
3. **Hook pipeline failure:** Blocking stage fails during dispatch-related commit
4. **Evidence capture failure:** Evidence pack cannot be built or manifest is invalid
5. **CDP connection loss:** Chrome DevTools Protocol connection drops during dispatch
6. **Human operator judgment:** Operator determines rollback is necessary

## Rollback Levels

### Level 1: Dispatch Abort (no packet sent)

**Trigger:** Pre-send validation failure, dry-run mismatch, operator cancel before send.

**Procedure:**
1. Set dispatch status to `aborted` in any tracking state
2. Do not send the packet
3. Log the abort reason
4. No code changes to revert

**Impact:** Zero. The dispatch packet was constructed but never transmitted.

### Level 2: Post-Send Rollback (packet sent, no commit)

**Trigger:** GPT response received but anomalous, evidence capture failed, operator judgment.

**Procedure:**
1. Do not commit any dispatch-related changes
2. Preserve the GPT response as evidence (save to `_evidence/` directory)
3. Build evidence pack if possible (even partial evidence is valuable)
4. Document the rollback reason in the evidence pack
5. Set dispatch status to `rolled_back`

**Impact:** Minimal. A GPT response was received but not acted upon. The conversation state may show the dispatched message; this is acceptable as evidence.

### Level 3: Post-Commit Rollback (packet sent, commit made)

**Trigger:** Hook pipeline failure on dispatch commit, evidence pack invalid after commit, operator judgment.

**Procedure:**
1. **Do not push.** The commit exists locally only.
2. Create a new commit that reverts the dispatch-related changes:
   ```
   git revert <dispatch-commit-sha>
   ```
3. Preserve the original commit and revert commit as evidence
4. Build evidence pack including both commits
5. Document the rollback chain in the evidence manifest

**Impact:** Low. The dispatch commit exists in local history but is reverted. No remote impact if push was not executed.

### Level 4: Post-Push Rollback (packet sent, commit pushed)

**Trigger:** Critical issue discovered after push. **This level should be avoided by ensuring push is the last step and requires separate human authorization.**

**Procedure:**
1. Create a revert commit:
   ```
   git revert <dispatch-commit-sha>
   git push origin master
   ```
2. Build a comprehensive evidence pack documenting the full dispatch-rollback cycle
3. Submit for GPT review with explicit notation that this was a rollback
4. Conduct a post-mortem review

**Impact:** Medium. The dispatch and rollback are both visible in remote history. This is acceptable for governance transparency but indicates a process failure.

## Registry Rollback

If a project binding causes dispatch issues:

1. **Disable the binding:** Set `binding_status` to `disabled` in `CONVERSATION_BINDING.json`
2. **Remove from registry:** If the project should not be dispatchable, set `binding_status` to `suspended` in `PROJECT_REGISTRY.json`
3. **Rebind:** If the conversation was wrong, rebind to a new conversation with a distinct conversation_id

## CDP Rollback

If Chrome/CDP issues occur:

1. **Disconnect:** Stop using the CDP endpoint (do not close Chrome)
2. **Restart Chrome CDP:** Use `restart_chrome_cdp.ps1` if Chrome is unresponsive
3. **Verify targets:** After restart, run `tab_target_resolver.py` to confirm target resolution
4. **Fresh dry-run:** Execute `dry_run_dispatch_10.py` to validate the dispatch pipeline before retrying

## Evidence Rollback

Evidence packs are **additive** -- they are never modified after creation. If an evidence pack was built incorrectly:

1. **Do not delete the original pack**
2. Build a new pack with a corrected manifest
3. Reference the original pack in the new pack's manifest as `supersedes`
4. Both packs remain in the evidence directory for audit trail

## Escalation Path

| Situation | Escalate To |
|---|---|
| Dispatch sent to wrong conversation | Human operator immediately |
| GPT response contains unexpected instructions | Human operator before any action |
| CDP connection hijack suspected | Human operator + close Chrome |
| Multiple dispatches sent accidentally | Human operator + halt all automation |
| Evidence tampering suspected | Human operator + preserve all files |

## Post-Rollback Actions

After any rollback:

1. **Document:** Create an evidence pack for the rollback event itself
2. **Review:** Submit the rollback evidence for GPT review
3. **Learn:** Add findings to `docs/agent-runtime/lessons-learned.md`
4. **Update:** If the rollback revealed a new failure mode, update the readiness review
5. **Re-authorize:** Live dispatch requires fresh human authorization after any rollback

---

**This plan is a living document. It should be reviewed and updated after every dispatch event (successful or rolled back).**
