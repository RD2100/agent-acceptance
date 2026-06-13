"""Tests for CDP Write Adapter and Review Dispatcher.

Tests the low-level adapter (cdp_write_adapter.py) and the
review dispatch runner (cdp_dispatch_runner.py).

Integration tests require a live Chrome with --remote-debugging-port=9222
and at least one ChatGPT tab.  Unit tests use mocks.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"


# ── Import adapter modules ────────────────────────────────────────────


def _import_adapter():
    """Import cdp_write_adapter module."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "cdp_write_adapter", SCRIPTS / "cdp_write_adapter.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["cdp_write_adapter"] = mod
    spec.loader.exec_module(mod)
    return mod


def _import_runner():
    """Import cdp_dispatch_runner module."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "cdp_dispatch_runner", SCRIPTS / "cdp_dispatch_runner.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["cdp_dispatch_runner"] = mod
    spec.loader.exec_module(mod)
    return mod


adapter = _import_adapter()
runner = _import_runner()


# ── CDPPage data class ───────────────────────────────────────────────


class TestCDPPage:

    def test_from_cdp_json_extracts_conversation_id(self):
        data = {
            "id": "ABC123",
            "url": "https://chatgpt.com/c/deadbeef-1234-5678-abcd-000000000000",
            "title": "Test conversation",
            "webSocketDebuggerUrl": "ws://localhost:9222/devtools/page/ABC123",
        }
        page = adapter.CDPPage.from_cdp_json(data)
        assert page.target_id == "ABC123"
        assert page.conversation_id == "deadbeef-1234-5678-abcd-000000000000"
        assert page.title == "Test conversation"

    def test_from_cdp_json_no_conversation_id(self):
        data = {
            "id": "XYZ",
            "url": "https://chatgpt.com/",
            "title": "ChatGPT Home",
            "webSocketDebuggerUrl": "ws://localhost:9222/devtools/page/XYZ",
        }
        page = adapter.CDPPage.from_cdp_json(data)
        assert page.conversation_id is None

    def test_from_cdp_json_strips_query_and_hash(self):
        data = {
            "id": "Q1",
            "url": "https://chatgpt.com/c/11111111-2222-3333-4444-555555555555?model=gpt4#section",
            "title": "Test",
            "webSocketDebuggerUrl": "ws://localhost:9222/devtools/page/Q1",
        }
        page = adapter.CDPPage.from_cdp_json(data)
        assert page.conversation_id == "11111111-2222-3333-4444-555555555555"


# ── InjectionResult / DispatchResult ─────────────────────────────────


class TestResultClasses:

    def test_injection_result_success(self):
        r = adapter.InjectionResult(success=True, method="execCommand", text_length=42)
        assert r.success
        assert r.method == "execCommand"
        assert r.text_length == 42

    def test_injection_result_failure(self):
        r = adapter.InjectionResult(success=False, method="none", text_length=0, error="not found")
        assert not r.success
        assert r.error == "not found"

    def test_dispatch_result_has_captured_at(self):
        r = adapter.DispatchResult(
            injection=adapter.InjectionResult(True, "execCommand", 10),
            sent=True,
            response_text="Hello",
            response_time_seconds=5.2,
        )
        assert r.captured_at  # auto-filled
        assert r.response_time_seconds == 5.2


# ── Review prompt formatting ─────────────────────────────────────────


class TestFormatReviewPrompt:

    def _make_report(self, **overrides) -> dict:
        base = {
            "role": "Architecture-Reviewer",
            "file": "ARCHITECTURE_REVIEW.md",
            "path": "_reports/multi-agent-architecture-review-a1/ARCHITECTURE_REVIEW.md",
            "review_type": "architecture",
            "content": "## Verdict: PARTIAL\n\nFindings:\n- P0-001: blocking conditions empty\n- P1-001: forbidden ranges\n\n## Changed Files\n- schema.json\n- dispatch_plan.py",
            "content_length": 150,
            "verdict": "CONDITIONAL",
        }
        base.update(overrides)
        return base

    def test_prompt_contains_review_instructions(self):
        report = self._make_report()
        prompt = runner.format_review_prompt(report)
        assert "Independent Review Request" in prompt
        assert "Architecture-Reviewer" in prompt
        assert "CONDITIONAL" in prompt
        assert "Verdict agreement" in prompt
        assert "Evidence sufficiency" in prompt
        assert "Gap identification" in prompt
        assert "Risk flags" in prompt

    def test_prompt_includes_report_content(self):
        report = self._make_report()
        prompt = runner.format_review_prompt(report)
        assert "P0-001: blocking conditions empty" in prompt
        assert "P1-001: forbidden ranges" in prompt

    def test_prompt_truncates_long_reports(self):
        long_content = "x" * 10000
        report = self._make_report(content=long_content, content_length=10000)
        prompt = runner.format_review_prompt(report)
        assert "truncated" in prompt
        assert len(prompt) < 8000

    def test_prompt_asks_for_approve_or_reject(self):
        report = self._make_report()
        prompt = runner.format_review_prompt(report)
        assert "APPROVE" in prompt
        assert "REJECT" in prompt

    def test_safe_wrapper_handles_errors(self):
        result = runner.format_review_prompt_safe({"role": "Test", "file": "test.md"})
        assert "Test" in result


# ── Report discovery ─────────────────────────────────────────────────


class TestDiscoverReports:

    def test_discovers_existing_reports(self):
        """The three worker reports from the dispatch should be found."""
        reports = runner.discover_reports()
        assert len(reports) >= 1, "Expected at least 1 report to exist"
        roles = [r["role"] for r in reports]
        # At least some of the known reports should be present
        assert any(r in roles for r in ["Architecture-Reviewer", "Verifier", "Quality-Reviewer"])

    def test_report_has_required_fields(self):
        reports = runner.discover_reports()
        if not reports:
            pytest.skip("No reports present")
        r = reports[0]
        assert "role" in r
        assert "file" in r
        assert "path" in r
        assert "content" in r
        assert "content_length" in r
        assert "verdict" in r
        assert r["content_length"] > 0


# ── Report-to-reviewer mapping ───────────────────────────────────────


class TestMapReportsToReviewers:

    def _make_binding(self) -> dict:
        return {
            "bindings": [
                {
                    "agent_id": "agent-local-001",
                    "role": "reviewer",
                    "binding_status": "active",
                    "conversation_id": "aaa-111",
                },
                {
                    "agent_id": "agent-pilot-beta",
                    "role": "executor",
                    "binding_status": "active",
                    "conversation_id": "bbb-222",
                },
            ]
        }

    def _make_targets(self) -> list:
        return [
            adapter.CDPPage("T1", "https://chatgpt.com/c/aaa-111", "aaa-111", "Review Tab", "ws://1"),
            adapter.CDPPage("T2", "https://chatgpt.com/c/bbb-222", "bbb-222", "Exec Tab", "ws://2"),
        ]

    def test_all_reports_go_to_reviewer(self):
        reports = [
            {"role": "Architecture-Reviewer", "file": "arch.md"},
            {"role": "Verifier", "file": "verify.md"},
            {"role": "Quality-Reviewer", "file": "quality.md"},
        ]
        binding = self._make_binding()
        targets = self._make_targets()
        mappings = runner.map_reports_to_reviewers(reports, binding, targets)
        assert len(mappings) == 3
        # All should map to reviewer target (T1)
        for _, target in mappings:
            assert target.target_id == "T1"

    def test_handles_no_targets(self):
        reports = [{"role": "Test", "file": "test.md"}]
        binding = self._make_binding()
        mappings = runner.map_reports_to_reviewers(reports, binding, [])
        assert len(mappings) == 0


# ── Integration tests: CDP connectivity ──────────────────────────────


class TestCDPIntegration:
    """Integration tests that require a live Chrome instance.

    Skipped if CDP is not available.
    """

    @pytest.fixture(autouse=True)
    def check_cdp(self):
        """Skip if CDP is not available."""
        try:
            import urllib.request
            with urllib.request.urlopen("http://localhost:9222/json", timeout=3) as resp:
                if resp.status != 200:
                    pytest.skip("CDP not available")
        except Exception:
            pytest.skip("CDP not available")

    def test_list_chatgpt_pages(self):
        pages = adapter._find_chatgpt_pages()
        assert isinstance(pages, list)
        assert len(pages) >= 1, "Expected at least 1 ChatGPT page"

    def test_pages_have_conversation_ids(self):
        pages = adapter._find_chatgpt_pages()
        chat_pages = [p for p in pages if p.conversation_id]
        assert len(chat_pages) >= 1, "Expected at least 1 page with conversation_id"

    def test_runner_discovers_reports_and_targets(self):
        """End-to-end: runner can discover reports and CDP targets."""
        reports = runner.discover_reports()
        targets = runner.discover_targets()
        assert len(reports) >= 1, "Expected at least 1 report"
        assert len(targets) >= 1, "Expected at least 1 CDP target"

    def test_runner_can_map_reports(self):
        """Reports can be mapped to available targets."""
        reports = runner.discover_reports()
        binding = runner.load_binding()
        targets = runner.discover_targets()
        mappings = runner.map_reports_to_reviewers(reports, binding, targets)
        assert len(mappings) >= 1
        for report, target in mappings:
            assert target.ws_url.startswith("ws://")
            assert report["content_length"] > 0
