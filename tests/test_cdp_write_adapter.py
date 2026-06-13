"""Tests for CDP Write Adapter and Dispatch Runner.

Tests the low-level adapter (cdp_write_adapter.py) and the
orchestration runner (cdp_dispatch_runner.py).

Integration tests require a live Chrome with --remote-debugging-port=9222
and at least one ChatGPT tab.  Unit tests use mocks.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

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


# ── Prompt formatting ────────────────────────────────────────────────


class TestFormatTaskSpecPrompt:

    def test_basic_formatting(self):
        assignment = {
            "worker_role": "Architecture-Reviewer",
            "target": "Confirm dispatch boundaries.",
            "allowed_modify_range": ["_reports/review/"],
            "forbidden_modify_range": ["scripts/", "tests/"],
            "quality_standard": "P0/P1 zero.",
            "completion_standard": "Report includes verdict.",
            "blocking_conditions": ["Finds P0 issue"],
            "task_spec": {
                "task_id": "ma-arch-a1",
                "title": "Review architecture",
                "description": "Check module boundaries.",
                "priority": "P2",
                "assumptions": ["Gate 0 may be HUMAN_REQUIRED."],
            },
        }
        prompt = runner.format_taskspec_prompt(assignment)
        assert "# Task: Review architecture" in prompt
        assert "Architecture-Reviewer" in prompt
        assert "ma-arch-a1" in prompt
        assert "Confirm dispatch boundaries." in prompt
        assert "_reports/review/" in prompt
        assert "scripts/" in prompt
        assert "P0/P1 zero" in prompt
        assert "Finds P0 issue" in prompt
        assert "Gate 0 may be HUMAN_REQUIRED" in prompt

    def test_prompt_length_reasonable(self):
        assignment = {
            "worker_role": "Verifier",
            "target": "Run tests.",
            "allowed_modify_range": ["_reports/verifier/"],
            "forbidden_modify_range": ["scripts/"],
            "quality_standard": "P0 zero.",
            "completion_standard": "Report complete.",
            "blocking_conditions": [],
            "required_verification_commands": ["pytest tests/ -q"],
            "task_spec": {
                "task_id": "ma-verifier",
                "title": "Run verification",
                "description": "Run all tests.",
                "priority": "P2",
                "assumptions": [],
            },
        }
        prompt = runner.format_taskspec_prompt(assignment)
        assert len(prompt) < 4000, f"Prompt too long: {len(prompt)} chars"
        assert "pytest tests/ -q" in prompt

    def test_safe_wrapper_handles_errors(self):
        # Pass invalid data that would crash the formatter
        result = runner.format_taskspec_prompt_safe({"worker_role": "Test"})
        assert "Test" in result  # Should not raise


# ── Worker-to-target mapping ─────────────────────────────────────────


class TestMapWorkersToTargets:

    def _make_assignment(self, role: str, status: str = "ready") -> dict:
        return {
            "worker_role": role,
            "parallel_safe": True,
            "task_spec": {"task_id": f"ma-{role.lower()}", "status": status},
        }

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
            adapter.CDPPage("T1", "https://chatgpt.com/c/aaa-111", "aaa-111", "Tab1", "ws://1"),
            adapter.CDPPage("T2", "https://chatgpt.com/c/bbb-222", "bbb-222", "Tab2", "ws://2"),
        ]

    def test_maps_by_conversation_id(self):
        assignments = [self._make_assignment("Architecture-Reviewer")]
        binding = self._make_binding()
        targets = self._make_targets()
        mappings = runner.map_workers_to_targets(assignments, binding, targets)
        assert len(mappings) == 1
        assert mappings[0][1].target_id == "T1"  # reviewer → first target

    def test_maps_verifier_to_executor(self):
        assignments = [self._make_assignment("Verifier")]
        binding = self._make_binding()
        targets = self._make_targets()
        mappings = runner.map_workers_to_targets(assignments, binding, targets)
        assert len(mappings) == 1
        assert mappings[0][1].target_id == "T2"  # verifier → second target

    def test_handles_no_targets(self):
        assignments = [self._make_assignment("Architecture-Reviewer")]
        binding = self._make_binding()
        mappings = runner.map_workers_to_targets(assignments, binding, [])
        assert len(mappings) == 0


# ── Plan loading helpers ─────────────────────────────────────────────


class TestPlanHelpers:

    def test_get_parallel_assignments(self):
        plan = {
            "assignments": [
                {"worker_role": "A", "parallel_safe": True, "task_spec": {"status": "ready"}},
                {"worker_role": "B", "parallel_safe": True, "task_spec": {"status": "ready"}},
                {"worker_role": "C", "parallel_safe": False, "task_spec": {"status": "ready"}},
                {"worker_role": "D", "parallel_safe": True, "task_spec": {"status": "completed"}},
            ]
        }
        result = runner.get_parallel_assignments(plan)
        assert len(result) == 2
        roles = [a["worker_role"] for a in result]
        assert "A" in roles
        assert "B" in roles

    def test_get_serial_assignments(self):
        plan = {
            "assignments": [
                {"worker_role": "A", "parallel_safe": True, "task_spec": {"status": "ready"}},
                {"worker_role": "C", "parallel_safe": False, "task_spec": {"status": "ready"}},
                {"worker_role": "D", "parallel_safe": False, "task_spec": {"status": "completed"}},
            ]
        }
        result = runner.get_serial_assignments(plan)
        assert len(result) == 1
        assert result[0]["worker_role"] == "C"


# ── Integration test: CDP connectivity ────────────────────────────────


class TestCDPIntegration:
    """Integration tests that require a live Chrome instance.

    These are skipped if CDP is not available.
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
        # Should have at least one ChatGPT page in the test environment
        assert isinstance(pages, list)
        assert len(pages) >= 1, "Expected at least 1 ChatGPT page"

    def test_pages_have_conversation_ids(self):
        pages = adapter._find_chatgpt_pages()
        chat_pages = [p for p in pages if p.conversation_id]
        assert len(chat_pages) >= 1, "Expected at least 1 page with conversation_id"

    def test_dispatch_runner_status(self):
        """Verify the runner can report status."""
        plan = runner.load_dispatch_plan()
        assert plan.get("status") == "READY"

    def test_dispatch_runner_dry_run_mapping(self):
        """Verify dry-run produces correct mappings."""
        plan = runner.load_dispatch_plan()
        binding = runner.load_binding()
        targets = runner.discover_targets()
        assignments = runner.get_parallel_assignments(plan)
        mappings = runner.map_workers_to_targets(assignments, binding, targets)
        assert len(mappings) >= 1
        # Every mapping should have a valid target
        for assignment, target in mappings:
            assert target.ws_url.startswith("ws://")
            assert target.conversation_id is not None
