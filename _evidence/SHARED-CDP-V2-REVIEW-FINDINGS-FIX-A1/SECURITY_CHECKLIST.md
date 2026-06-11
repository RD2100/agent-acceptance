# Security Checklist: AWSP v2 Shared CDP Architecture Fix

**Review scope**: 4 files in `D:\agent-acceptance\scripts\`
- `multi_project_router.py`
- `dry_run_dispatch_10.py`
- `gate0_preflight_10.py`
- `tab_target_resolver.py`

**Reviewed**: 2026-06-10
**Architecture**: Shared CDP v2 — single Chrome instance, conversation-based isolation, tab-level target resolution

---

## Module 1: CDP Endpoint Security

### 1.1 Localhost Restriction

- [x] **PASS** — `validate_cdp_endpoint()` in `tab_target_resolver.py` (L56-65) rejects any hostname not in `("localhost", "127.0.0.1", "::1")`. Returns `(False, "cdp_endpoint_must_be_localhost")` for remote hosts. This prevents accidental connection to remote Chrome instances that could expose CDP to the network.

- [x] **PASS** — `validate_cdp_endpoint()` in `multi_project_router.py` (L45-60) implements identical localhost hostname check. Both functions enforce the same allowlist independently.

- [x] **PASS** — `_check_cdp()` in `multi_project_router.py` (L63-72) calls `validate_cdp_endpoint()` BEFORE making any HTTP request to the endpoint. No outbound HTTP connection occurs if validation fails.

- [x] **PASS** — `check_cdp_health()` in `gate0_preflight_10.py` (L76-87) calls `_canonical_validate_cdp_endpoint()` (imported from `tab_target_resolver.py`) before `urllib.request.urlopen()`. Preflight never probes unvalidated endpoints.

- [x] **PASS** — `list_cdp_pages()` in `tab_target_resolver.py` (L90-107) calls `validate_cdp_endpoint()` before fetching `/json`. Returns empty list on validation failure — no network call to untrusted hosts.

### 1.2 Scheme Validation

- [x] **PASS** — `tab_target_resolver.py` L63: `parsed.scheme not in ("http", "https")` rejects `ftp://`, `ws://`, `file://`, and other non-HTTP schemes. Returns `(False, "cdp_endpoint_must_use_http")`.

- [x] **PASS** — `multi_project_router.py` L54: identical scheme check. Both validators allow only `http` and `https`.

### 1.3 Port Validation

- [x] **PASS** — `tab_target_resolver.py` L67-68: `parsed.port is None` check ensures a port is explicitly specified. Default ports (80/443) without explicit notation are rejected. Returns `(False, "cdp_endpoint_missing_port")`.

- [x] **PASS** — `multi_project_router.py` L58-59: identical explicit-port requirement.

- [ ] **FAIL** — **No port range restriction.** Both `validate_cdp_endpoint()` implementations accept any valid port (1-65535). A configuration pointing to `http://localhost:80` or `http://localhost:22` would pass validation and trigger an HTTP probe to an unrelated local service. **Recommendation**: Restrict to a known CDP port range (e.g., 9222-9230) or at minimum reject well-known ports below 1024.

### 1.4 Timeout Enforcement

- [x] **PASS** — `_check_cdp()` in `multi_project_router.py` L69: `timeout=3` on `urllib.request.urlopen()`. Prevents hanging on unresponsive endpoints.

- [x] **PASS** — `check_cdp_health()` in `gate0_preflight_10.py` L82-84: `timeout=3` on CDP health check.

- [x] **PASS** — `list_cdp_pages()` in `tab_target_resolver.py` L102: `timeout=5` on CDP `/json` fetch.

### 1.5 Duplicate Validation Logic (Drift Risk)

- [ ] **FAIL** — `multi_project_router.py` defines its own `validate_cdp_endpoint()` (L45-60) that is a copy of the one in `tab_target_resolver.py` (L51-69). The router does NOT import the canonical version from `tab_target_resolver`, unlike `gate0_preflight_10.py` which imports `_canonical_validate_cdp_endpoint`. While currently identical, future edits to one without the other would create a validation divergence — a maintenance-level security risk. **Recommendation**: `multi_project_router.py` should import the canonical validator from `tab_target_resolver.py`.

---

## Module 2: Data Leakage Prevention

### 2.1 webSocketDebuggerUrl Redaction

- [x] **PASS** — `resolve_tab_target()` in `tab_target_resolver.py` (L196-203) explicitly redacts the full WebSocket debugger URL on exact match:
  ```python
  "webSocketDebuggerUrl": "[REDACTED]" if ws_url else None,
  "has_webSocketDebuggerUrl": ws_url is not None,
  ```
  Only a boolean presence flag is exposed. The full `ws://...` URL (which grants full browser control) is never stored in any return value, report, or packet.

- [x] **PASS** — `resolve_all_targets()` in `tab_target_resolver.py` (L276-288) uses `**tab_result` spread from `resolve_tab_target()`, inheriting the redacted value. No raw `webSocketDebuggerUrl` leaks into the batch report.

- [x] **PASS** — `resolve_project_target()` in `tab_target_resolver.py` (L356-368) also uses `**tab_result` spread, inheriting redaction.

### 2.2 Sensitive Data in Reports

- [ ] **FAIL** — `dry_run_dispatch_10.py` L233: dispatch report entries include raw `conversation_id` in the top-level result dict:
  ```python
  "conversation_id": target.get("conversation_id"),
  ```
  The report is written to `_reports/multi-project-batch-init-a1/DRY_RUN_DISPATCH_10.json` (L300). If report files are shared or committed, conversation IDs could enable cross-project impersonation. **Recommendation**: Redact or hash conversation IDs in reports (e.g., `conv_id[:8] + "..."`).

- [ ] **FAIL** — `gate0_preflight_10.py` L191: preflight report includes raw `conv_id` per project:
  ```python
  "conv_id": primary_conv_id,
  ```
  Same exposure risk as above. Written to `_reports/.../GATE0_PREFLIGHT_10.json` (L409-411).

- [x] **PASS** — `cdp_endpoint` in reports is always `http://localhost:<port>`. Since localhost is already enforced, this does not leak network-reachable addresses. The port number alone is low-sensitivity.

### 2.3 Sensitive Data in Dispatch Packets

- [ ] **FAIL** — `build_dispatch_packet()` in `multi_project_router.py` L289 includes `message_text` in the dispatch packet:
  ```python
  "message_text": message_text,
  ```
  While the packet is only built (not sent) in dry-run mode, the full task message is persisted in the packet payload. If packets are logged or stored, task instructions could leak. **Recommendation**: Store only `message_length` (already included at L291) and a hash, not the full text.

- [x] **PASS** — `build_dispatch_packet()` L236: non-dispatchable packets have `"packet": None` in the dry-run report (L236 of `dry_run_dispatch_10.py`). Failed packet payloads are not persisted.

### 2.4 CDP Tab ID Leakage in Error Paths

- [ ] **FAIL** — `resolve_tab_target()` in `tab_target_resolver.py` L183-189: on ambiguous match, raw CDP page target IDs are exposed in the issues list:
  ```python
  f"Multiple CDP tabs match {chat_url}: {target_ids}",
  ```
  While these are internal IDs (not WebSocket URLs), they could assist an attacker in targeting specific browser tabs. **Risk**: Low — IDs are UUIDs with no inherent exploitability, but best practice is to redact.

---

## Module 3: Fail-Closed Enforcement

### 3.1 Dispatch Gates (build_dispatch_packet)

- [x] **PASS** — `build_dispatch_packet()` in `multi_project_router.py` L221-228: blocks dispatch when `tab_match_status != "exact_match"`. Returns `dispatchable: False` with `blocked_reason: "tab_match_status_not_exact"`. No fallback to approximate or last-known tab.

- [x] **PASS** — `multi_project_router.py` L230-236: blocks dispatch when `target_id` is falsy (None or empty). Returns `blocked_reason: "missing_target_id"`.

- [x] **PASS** — `multi_project_router.py` L238-245: blocks dispatch when `target_url` is falsy. Returns `blocked_reason: "missing_target_url"`. Triple-gate enforcement: exact match + target_id + target_url must all be present.

- [x] **PASS** — `multi_project_router.py` L213-214: blocks dispatch when `target["resolved"]` is False. Returns error from the resolution failure. Unresolved targets cannot produce dispatchable packets.

### 3.2 Classification Gates (dry_run_dispatch_10)

- [x] **PASS** — `_classify_packet()` in `dry_run_dispatch_10.py` L67-115 implements a 7-level priority classification with strict fail-closed ordering:
  1. `non_dispatchable_pending` — registry says pending manual binding (L91)
  2. `non_dispatchable_collision` — isolation collision detected (L95)
  3. `blocked_ambiguous_tab` — tab match is ambiguous (L103-104)
  4. `human_required_tab_unresolved` — tab not found (L105)
  5. `human_required_missing_target_id` — target_id absent (L107-108)
  6. `human_required` — other failure (L111)
  7. `dispatchable` — all checks pass (L115)

  A packet is only `dispatchable` when classification equals `"dispatchable"` (L190). No bypass path exists.

- [x] **PASS** — `dry_run_dispatch_10.py` L235-236: non-dispatchable results set `"packet": None`, preventing accidental inclusion of partial packet data in the report.

### 3.3 Gate0 Preflight Gates

- [x] **PASS** — `run_preflight()` in `gate0_preflight_10.py` L281-292 implements a strict verdict model:
  - `BLOCKED` when `active_count == 0` (no active projects)
  - `PARTIAL_PASS` when any critical issue exists (`blocked_count > 0 or collision_count > 0`) or unresolved issues (`tab_unresolved_count > 0 or stale_count > 0`)
  - `PASS` only when all active projects have unique conversations AND resolved tabs

- [x] **PASS** — `_evaluate_project_v2()` in `gate0_preflight_10.py` L104-198: when CDP is unhealthy, active projects are classified as `"stale"` (L143-145), never `"active"`. No tab resolution is attempted against a dead endpoint.

- [x] **PASS** — `gate0_preflight_10.py` L152-156: conversation collision is checked BEFORE tab resolution. A colliding project is classified as `"conversation_collision"` and never reaches the tab resolution step, preventing dispatch of colliding targets.

### 3.4 No Bypass Paths

- [x] **PASS** — All three enforcement layers are stacked: `tab_target_resolver` (resolution) -> `multi_project_router` (packet building) -> `dry_run_dispatch_10` (classification). No layer can be skipped because each depends on the output of the previous. The classification in `dry_run_dispatch_10.py` re-checks tab status independently (L99-100) rather than trusting the packet's `dispatchable` flag alone.

- [x] **PASS** — `tab_target_resolver.py` L171-191: no fallback to "last tab" or "current active tab". Zero matches returns `no_match`; multiple matches returns `ambiguous`. Both block dispatch. This is explicitly documented as a v2 rule (L16-17 in module docstring).

---

## Module 4: Input Validation

### 4.1 CDP Endpoint Parsing

- [x] **PASS** — Both `validate_cdp_endpoint()` implementations (`tab_target_resolver.py` L51-69, `multi_project_router.py` L45-60) wrap `urlparse()` in a try/except (L59-62 / L50-53). Malformed URLs that crash the parser return `(False, "cdp_endpoint_parse_failed")` without raising an exception.

- [x] **PASS** — The hostname check uses `parsed.hostname` (lowercase-normalized by `urlparse`), so `LOCALHOST`, `LocalHost`, and mixed-case variants are all correctly matched. IPv6 `::1` is also included.

### 4.2 URL Normalization

- [x] **PASS** — `resolve_tab_target()` in `tab_target_resolver.py` L159 normalizes the bound `chat_url`:
  ```python
  normalized_chat = chat_url.rstrip("/").split("?")[0]
  ```
  Strips trailing slashes and query parameters for consistent matching.

- [x] **PASS** — `tab_target_resolver.py` L165: applies the same normalization to each CDP page URL:
  ```python
  normalized_page = page_url.rstrip("/").split("?")[0]
  ```
  Both sides use identical normalization, preventing asymmetric matching failures.

- [ ] **FAIL** — **No URL fragment handling.** The normalization `rstrip("/").split("?")[0]` does not strip URL fragments (`#section`). If a `chat_url` in the binding file contains a fragment (e.g., `https://chatgpt.com/c/abc#msg123`) but the CDP page URL does not, the match would fail with `no_match`. While unlikely in practice, this is a normalization gap. **Recommendation**: Add `.split("#")[0]` before `.split("?")[0]`.

- [ ] **FAIL** — **No structural validation of `chat_url` format.** The `chat_url` from the binding file is used directly in string comparison without verifying it matches the expected ChatGPT conversation URL pattern (`https://chatgpt.com/c/<uuid>`). A binding file with `chat_url: "https://evil.com/phishing"` would pass through to matching. While `is_chatgpt_page()` filters CDP pages in batch mode (`resolve_all_targets()` L228), the `resolve_tab_target()` function itself accepts any URL, and `resolve_project_target()` also calls it with ChatGPT-filtered pages. The risk is limited because a non-ChatGPT URL would simply not match any CDP page, but the function does not enforce the expected URL structure. **Recommendation**: Add a format check (e.g., regex for `chatgpt.com/c/` or `chat.openai.com/c/`) at the binding-loading stage.

### 4.3 Conversation ID Validation

- [x] **PASS** — `is_valid_conv_id()` in `gate0_preflight_10.py` L90-98 implements three validation rules:
  1. Rejects `None` values (L93)
  2. Rejects placeholder IDs starting with `"pending-"` (L94-95)
  3. Rejects empty or whitespace-only strings (L96-97)

  This prevents pending/placeholder bindings from being treated as active.

- [x] **PASS** — `gate0_preflight_10.py` L132: `any_valid_conv = any(is_valid_conv_id(c) for c in conv_ids)` — at least one valid conversation ID is required before classifying a project as active. Projects with only pending IDs are classified as `"stale"`.

### 4.4 Page Type Filtering

- [ ] **FAIL** — `is_chatgpt_page()` in `tab_target_resolver.py` L110-113 uses substring containment:
  ```python
  return "chatgpt.com" in url or "chat.openai.com" in url
  ```
  A URL like `https://evil-chatgpt.com/phishing` or `https://notchatgpt.com.evil.net/page` would pass this check. While this only affects CDP page filtering (not dispatch security), it could cause non-ChatGPT tabs to be included in the matching pool. **Recommendation**: Use `urlparse()` to check the hostname against an allowlist of known ChatGPT domains.

- [x] **PASS** — `is_chatgpt_conversation_page()` in `tab_target_resolver.py` L116-122 is more specific, requiring `chatgpt.com/c/` or `chat.openai.com/c/` in the URL. However, this function is defined but **never called** in any of the 4 files. The batch resolver uses `is_chatgpt_page()` (the broader check) at L228. **Recommendation**: Use `is_chatgpt_conversation_page()` instead of `is_chatgpt_page()` for page filtering in `resolve_all_targets()`.

---

## Module 5: Isolation Integrity

### 5.1 Conversation-Based Isolation

- [x] **PASS** — `verify_isolation()` in `multi_project_router.py` L299-333: iterates all resolved targets, tracks `conversation_id` in a dict, and flags any ID shared by two or more projects as a collision:
  ```python
  if conv in conv_ids:
      issues.append(f"Conversation collision: {pid} and {conv_ids[conv]} share {conv}")
  ```
  Returns `isolated: False` when any collision exists.

- [x] **PASS** — `_find_collision_projects()` in `dry_run_dispatch_10.py` L120-145: independently detects conversation collisions using a list-accumulation approach (`conv_ids.setdefault(conv, []).append(pid)`), then collects all projects involved in any collision. This is used to classify colliding projects as `non_dispatchable_collision` (L95-96).

- [x] **PASS** — `run_preflight()` in `gate0_preflight_10.py` L235-256: builds a `conv_id_map` across all active projects in a first pass, identifies duplicates (`conv_id_duplicates`), and passes them to `_evaluate_project_v2()` where colliding projects are classified as `"conversation_collision"` (L152-156). The two-pass design ensures all collisions are detected before any per-project verdict is rendered.

### 5.2 No Cross-Project Leakage

- [x] **PASS** — Each project's dispatch target is resolved independently via its own `CONVERSATION_BINDING.json` (loaded per-project in `load_binding()`). The shared CDP endpoint is read from the global registry, but per-project routing data (conversation_id, chat_url, agent_id) comes from each project's isolated binding file. No project can influence another's dispatch target.

- [x] **PASS** — `resolve_target()` in `multi_project_router.py` L93-176: takes a `project_id` and looks up only that project's data from the registry and its binding file. There is no cross-project data mixing in the resolution path.

- [x] **PASS** — `resolve_all_targets()` in `tab_target_resolver.py` L236: iterates projects sequentially, loading each project's binding independently. No shared mutable state between project evaluations.

### 5.3 Chat URL Collision Detection (Defense-in-Depth)

- [x] **PASS** — `gate0_preflight_10.py` L236, L252, L256: in addition to conversation_id collisions, the preflight also detects `chat_url_duplicates` — cases where two active projects share the same `chat_url`. This is a defense-in-depth measure: even if conversation IDs differ, sharing the same URL means both projects would resolve to the same CDP tab, which would be a routing ambiguity. Projects with duplicate chat_urls are classified as `"blocked"` (L157-160).

- [x] **PASS** — `gate0_preflight_10.py` L255-256: duplicate detection uses `set(v)` to deduplicate project IDs before counting, preventing a single project with multiple active agents pointing to the same URL from triggering a false positive.

### 5.4 Shared CDP / Shared Profile Tolerance

- [x] **PASS** — The v2 architecture explicitly expects shared CDP endpoints and shared browser profiles across projects. `gate0_preflight_10.py` L19-21 (docstring): "Shared CDP endpoint is EXPECTED (not a collision), Shared browser profile is EXPECTED (not a collision)". The `_evaluate_project_v2()` function (L104-198) does NOT check for profile or port uniqueness, correctly avoiding false collision reports.

- [x] **PASS** — `_find_collision_projects()` in `dry_run_dispatch_10.py` L124-125 (docstring): "In v2 shared-CDP architecture, ONLY conversation_id collisions matter. Shared CDP endpoints and shared profiles are EXPECTED." The function only tracks `conversation_id`, not CDP endpoint or profile path.

### 5.5 Default Endpoint Hardening

- [ ] **FAIL** — Both `multi_project_router.py` L117 and `gate0_preflight_10.py` L211 use a hardcoded fallback:
  ```python
  cdp_endpoint = registry.get("shared_cdp_endpoint", "http://localhost:9222")
  ```
  If the registry is missing or corrupted, the system falls back to `http://localhost:9222`. While localhost-only validation prevents remote exploitation, the hardcoded fallback could silently connect to an unintended local Chrome instance. **Recommendation**: Fail explicitly when `shared_cdp_endpoint` is missing from the registry, rather than falling back to a default.

---

## Summary

| Module | PASS | FAIL | Total |
|--------|------|------|-------|
| 1. CDP Endpoint Security | 10 | 2 | 12 |
| 2. Data Leakage Prevention | 4 | 4 | 8 |
| 3. Fail-Closed Enforcement | 10 | 0 | 10 |
| 4. Input Validation | 5 | 3 | 8 |
| 5. Isolation Integrity | 9 | 1 | 10 |
| **Total** | **38** | **10** | **48** |

**Overall pass rate**: 38/48 (79%)

### Critical Findings (FAIL items)

| # | Module | Severity | Finding | File(s) |
|---|--------|----------|---------|---------|
| F1 | 1.3 | Low | No CDP port range restriction — any port accepted | `tab_target_resolver.py`, `multi_project_router.py` |
| F2 | 1.5 | Low | Duplicate `validate_cdp_endpoint()` — drift risk | `multi_project_router.py` |
| F3 | 2.2 | Medium | Raw `conversation_id` exposed in dry-run and preflight reports | `dry_run_dispatch_10.py`, `gate0_preflight_10.py` |
| F4 | 2.3 | Medium | Full `message_text` persisted in dispatch packet | `multi_project_router.py` |
| F5 | 2.4 | Low | Raw CDP target IDs exposed in ambiguous-match error messages | `tab_target_resolver.py` |
| F6 | 4.2 | Low | URL normalization does not strip fragments (`#`) | `tab_target_resolver.py` |
| F7 | 4.2 | Low | No structural validation of `chat_url` format | `tab_target_resolver.py` |
| F8 | 4.4 | Medium | `is_chatgpt_page()` uses substring match — spoofable by `evil-chatgpt.com` | `tab_target_resolver.py` |
| F9 | 4.4 | Low | `is_chatgpt_conversation_page()` defined but never called | `tab_target_resolver.py` |
| F10 | 5.5 | Low | Hardcoded fallback CDP endpoint instead of explicit failure | `multi_project_router.py`, `gate0_preflight_10.py` |

### Strongest Security Properties

1. **Fail-closed dispatch**: Triple-gate enforcement (exact_match + target_id + target_url) with no fallback paths. This is the strongest property in the architecture.
2. **WebSocket URL redaction**: `webSocketDebuggerUrl` (the most dangerous CDP credential) is consistently redacted to `[REDACTED]` in all code paths.
3. **Conversation isolation**: Three independent collision detection mechanisms across three files, all converging on the same result.
4. **Localhost-only CDP**: All HTTP probes are gated by localhost validation, preventing network-facing CDP exposure.
