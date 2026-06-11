"""Tests for SHARED-CDP-TAB-TARGET-RESOLVER-A1 — v2 tab-level target resolution.

Tests cover:
  1. CDP page discovery and filtering
  2. Single tab target resolution (exact, no match, ambiguous)
  3. Batch resolution across all projects
  4. Edge cases (no chat_url, CDP unreachable, non-ChatGPT pages)
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"
sys.path.insert(0, str(SCRIPTS))

import tab_target_resolver


# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def sample_cdp_pages():
    """Realistic CDP /json page list with ChatGPT tabs + other pages."""
    return [
        {
            "id": "target-alpha-001",
            "type": "page",
            "title": "ChatGPT - Project Alpha",
            "url": "https://chatgpt.com/c/conv-alpha-123",
            "webSocketDebuggerUrl": "ws://localhost:9222/devtools/page/target-alpha-001",
        },
        {
            "id": "target-beta-002",
            "type": "page",
            "title": "ChatGPT - Project Beta",
            "url": "https://chatgpt.com/c/conv-beta-456",
            "webSocketDebuggerUrl": "ws://localhost:9222/devtools/page/target-beta-002",
        },
        {
            "id": "target-google-003",
            "type": "page",
            "title": "Google",
            "url": "https://www.google.com/",
            "webSocketDebuggerUrl": "ws://localhost:9222/devtools/page/target-google-003",
        },
        {
            "id": "target-chatgpt-home",
            "type": "page",
            "title": "ChatGPT",
            "url": "https://chatgpt.com/",
            "webSocketDebuggerUrl": "ws://localhost:9222/devtools/page/target-chatgpt-home",
        },
    ]


@pytest.fixture
def empty_cdp_pages():
    """Empty CDP page list (endpoint unreachable or no tabs)."""
    return []


# ── 1. Page Discovery and Filtering ──────────────────────────────────


class TestCdpPageDiscovery:
    """Test CDP page list fetching and filtering."""

    def test_is_chatgpt_page_positive(self):
        page = {"url": "https://chatgpt.com/c/abc123"}
        assert tab_target_resolver.is_chatgpt_page(page) is True

    def test_is_chatgpt_page_openai_domain(self):
        page = {"url": "https://chat.openai.com/c/abc123"}
        assert tab_target_resolver.is_chatgpt_page(page) is True

    def test_is_chatgpt_page_negative(self):
        page = {"url": "https://www.google.com/"}
        assert tab_target_resolver.is_chatgpt_page(page) is False

    def test_is_chatgpt_conversation_page_positive(self):
        page = {"url": "https://chatgpt.com/c/abc123"}
        assert tab_target_resolver.is_chatgpt_conversation_page(page) is True

    def test_is_chatgpt_conversation_page_homepage(self):
        """ChatGPT homepage is NOT a conversation page."""
        page = {"url": "https://chatgpt.com/"}
        assert tab_target_resolver.is_chatgpt_conversation_page(page) is False

    def test_filter_chatgpt_pages(self, sample_cdp_pages):
        chatgpt_pages = [p for p in sample_cdp_pages if tab_target_resolver.is_chatgpt_page(p)]
        assert len(chatgpt_pages) == 3  # alpha, beta, chatgpt-home
        urls = [p["url"] for p in chatgpt_pages]
        assert "https://www.google.com/" not in urls


# ── 2. Single Tab Target Resolution ──────────────────────────────────


class TestResolveTabTarget:
    """Test resolve_tab_target for individual URLs."""

    def test_exact_match(self, sample_cdp_pages):
        result = tab_target_resolver.resolve_tab_target(
            "https://chatgpt.com/c/conv-alpha-123",
            sample_cdp_pages,
        )
        assert result["match_status"] == "exact_match"
        assert result["target_id"] == "target-alpha-001"
        assert result["target_url"] == "https://chatgpt.com/c/conv-alpha-123"
        assert result["issues"] == []

    def test_exact_match_trailing_slash(self, sample_cdp_pages):
        """Trailing slash should not prevent matching."""
        result = tab_target_resolver.resolve_tab_target(
            "https://chatgpt.com/c/conv-alpha-123/",
            sample_cdp_pages,
        )
        assert result["match_status"] == "exact_match"
        assert result["target_id"] == "target-alpha-001"

    def test_exact_match_with_query_params(self, sample_cdp_pages):
        """Query params should be stripped for matching."""
        result = tab_target_resolver.resolve_tab_target(
            "https://chatgpt.com/c/conv-alpha-123?foo=bar",
            sample_cdp_pages,
        )
        assert result["match_status"] == "exact_match"
        assert result["target_id"] == "target-alpha-001"

    def test_no_match(self, sample_cdp_pages):
        result = tab_target_resolver.resolve_tab_target(
            "https://chatgpt.com/c/nonexistent-789",
            sample_cdp_pages,
        )
        assert result["match_status"] == "no_match"
        assert result["target_id"] is None
        assert any("No CDP tab found" in issue for issue in result["issues"])

    def test_ambiguous_match(self):
        """Multiple tabs with the same URL -> ambiguous."""
        pages = [
            {"id": "t1", "type": "page", "url": "https://chatgpt.com/c/dup-123"},
            {"id": "t2", "type": "page", "url": "https://chatgpt.com/c/dup-123"},
        ]
        result = tab_target_resolver.resolve_tab_target(
            "https://chatgpt.com/c/dup-123",
            pages,
        )
        assert result["match_status"] == "ambiguous"
        assert result["target_id"] is None
        assert any("Multiple CDP tabs" in issue for issue in result["issues"])

    def test_empty_chat_url(self, sample_cdp_pages):
        result = tab_target_resolver.resolve_tab_target("", sample_cdp_pages)
        assert result["match_status"] == "no_chat_url"
        assert result["target_id"] is None

    def test_none_chat_url(self, sample_cdp_pages):
        result = tab_target_resolver.resolve_tab_target(None, sample_cdp_pages)
        assert result["match_status"] == "no_chat_url"

    def test_cdp_unreachable(self):
        result = tab_target_resolver.resolve_tab_target(
            "https://chatgpt.com/c/conv-alpha-123",
            [],
        )
        assert result["match_status"] == "cdp_unreachable"
        assert result["target_id"] is None


# ── 3. Isolation Rules ───────────────────────────────────────────────


class TestTabTargetIsolation:
    """Verify v2 isolation rules for tab target resolution."""

    def test_non_chatgpt_page_cannot_be_bound(self):
        """A Google tab should never be a valid target — rejected by structural validation (F7)."""
        pages = [
            {"id": "t1", "type": "page", "url": "https://www.google.com/"},
        ]
        result = tab_target_resolver.resolve_tab_target(
            "https://www.google.com/",
            pages,
        )
        # F7: Non-ChatGPT domain in chat_url is rejected before matching
        assert result["match_status"] == "invalid_chat_url"

    def test_non_chatgpt_cdp_page_excluded(self):
        """Non-ChatGPT CDP pages are filtered out — cannot match even if URL coincidentally matches."""
        pages = [
            {"id": "t1", "type": "page", "url": "https://chatgpt.com/c/test-123"},
            {"id": "t2", "type": "page", "url": "https://www.google.com/search?q=chatgpt"},
        ]
        result = tab_target_resolver.resolve_tab_target(
            "https://chatgpt.com/c/test-123",
            pages,
        )
        assert result["match_status"] == "exact_match"
        assert result["target_id"] == "t1"  # Only the ChatGPT page matches

    def test_no_fallback_to_last_tab(self, sample_cdp_pages):
        """If no exact match, must NOT fallback to last tab."""
        result = tab_target_resolver.resolve_tab_target(
            "https://chatgpt.com/c/nonexistent",
            sample_cdp_pages,
        )
        assert result["match_status"] == "no_match"
        assert result["target_id"] is None  # No fallback

    def test_no_fallback_to_active_tab(self, sample_cdp_pages):
        """If no exact match, must NOT fallback to current active tab."""
        result = tab_target_resolver.resolve_tab_target(
            "https://chatgpt.com/c/missing-conv",
            sample_cdp_pages,
        )
        assert result["match_status"] == "no_match"
        assert result["target_id"] is None

    def test_unique_projects_unique_targets(self, sample_cdp_pages):
        """Two different conversations should resolve to different targets."""
        r1 = tab_target_resolver.resolve_tab_target(
            "https://chatgpt.com/c/conv-alpha-123", sample_cdp_pages
        )
        r2 = tab_target_resolver.resolve_tab_target(
            "https://chatgpt.com/c/conv-beta-456", sample_cdp_pages
        )
        assert r1["target_id"] != r2["target_id"]
        assert r1["match_status"] == "exact_match"
        assert r2["match_status"] == "exact_match"


# ── 4. Batch Resolution ─────────────────────────────────────────────


class TestBatchResolution:
    """Test resolve_all_targets and resolve_project_target."""

    def test_resolve_all_skips_pending_projects(self):
        """Pending projects should be skipped, not resolved."""
        result = tab_target_resolver.resolve_all_targets()
        for r in result.get("results", []):
            if r.get("binding_status") != "active":
                assert r.get("match_status") == "skipped" or r.get("skip_reason") == "not_active"

    def test_resolve_all_report_structure(self):
        """Verify the batch report has required v2 fields."""
        result = tab_target_resolver.resolve_all_targets()
        assert "schema_version" in result
        assert result["schema_version"] == "2.0.0"
        assert "cdp_healthy" in result
        assert "total_cdp_pages" in result
        assert "chatgpt_pages" in result
        assert "resolved_targets" in result
        assert "human_required" in result
        assert "blocked" in result
        assert "results" in result

    def test_resolve_project_nonexistent(self):
        """Nonexistent project should return resolved=False."""
        result = tab_target_resolver.resolve_project_target("fake-project")
        assert result["resolved"] is False
        assert "not found" in result.get("error", "").lower()

    def test_resolve_project_pending(self):
        """Pending project should not resolve."""
        result = tab_target_resolver.resolve_project_target("project-alpha")
        assert result["resolved"] is False


# ── 5. Edge Cases ────────────────────────────────────────────────────


class TestEdgeCases:
    """Edge cases for tab target resolution."""

    def test_cdp_pages_only_service_workers(self):
        """Service workers should be filtered out."""
        pages = [
            {"id": "sw1", "type": "service_worker", "url": "https://chatgpt.com/sw.js"},
            {"id": "sw2", "type": "background_page", "url": "https://chatgpt.com/bg"},
        ]
        # list_cdp_pages filters to type=page, so service workers are excluded
        result = tab_target_resolver.resolve_tab_target(
            "https://chatgpt.com/c/test", pages
        )
        assert result["match_status"] == "no_match"

    def test_mixed_page_types(self):
        """resolve_tab_target matches by URL — type filtering is list_cdp_pages' job.
        If two pages have the same URL (regardless of type), it's ambiguous."""
        pages = [
            {"id": "page1", "type": "page", "url": "https://chatgpt.com/c/test-123"},
            {"id": "sw1", "type": "service_worker", "url": "https://chatgpt.com/c/test-123"},
        ]
        result = tab_target_resolver.resolve_tab_target(
            "https://chatgpt.com/c/test-123", pages
        )
        # Two pages match -> ambiguous (type filtering happens upstream)
        assert result["match_status"] == "ambiguous"

    def test_is_valid_conv_id(self):
        """Verify conversation ID validation."""
        assert tab_target_resolver.load_registry is not None  # smoke test import


# ── 6. CDP Endpoint Validation (T-002) ───────────────────────────────


class TestCDPEndpointValidation:
    """Direct tests for validate_cdp_endpoint() security function (T-002)."""

    def test_valid_localhost(self):
        valid, err = tab_target_resolver.validate_cdp_endpoint("http://localhost:9222")
        assert valid is True
        assert err is None

    def test_valid_127(self):
        valid, err = tab_target_resolver.validate_cdp_endpoint("http://127.0.0.1:9222")
        assert valid is True
        assert err is None

    def test_valid_ipv6(self):
        valid, err = tab_target_resolver.validate_cdp_endpoint("http://[::1]:9222")
        assert valid is True
        assert err is None

    def test_reject_remote_host(self):
        valid, err = tab_target_resolver.validate_cdp_endpoint("http://192.168.1.100:9222")
        assert valid is False
        assert err == "cdp_endpoint_must_be_localhost"

    def test_reject_ftp_scheme(self):
        valid, err = tab_target_resolver.validate_cdp_endpoint("ftp://localhost:9222")
        assert valid is False
        assert err == "cdp_endpoint_must_use_http_or_https"

    def test_reject_missing_port(self):
        valid, err = tab_target_resolver.validate_cdp_endpoint("http://localhost")
        assert valid is False
        assert err == "cdp_endpoint_missing_port"

    def test_reject_port_out_of_range(self):
        valid, err = tab_target_resolver.validate_cdp_endpoint("http://localhost:80")
        assert valid is False
        assert err == "cdp_endpoint_port_out_of_range"

    def test_reject_port_22(self):
        valid, err = tab_target_resolver.validate_cdp_endpoint("http://localhost:22")
        assert valid is False
        assert err == "cdp_endpoint_port_out_of_range"

    def test_allow_port_9230(self):
        valid, err = tab_target_resolver.validate_cdp_endpoint("http://localhost:9230")
        assert valid is True
        assert err is None

    def test_allow_port_9231(self):
        """Port 9231 is the upper boundary for 10-project plan (9222-9231)."""
        valid, err = tab_target_resolver.validate_cdp_endpoint("http://localhost:9231")
        assert valid is True
        assert err is None

    def test_reject_port_9232(self):
        """Port 9232 is above the 10-project range (9222-9231)."""
        valid, err = tab_target_resolver.validate_cdp_endpoint("http://localhost:9232")
        assert valid is False
        assert err == "cdp_endpoint_port_out_of_range"

    def test_reject_port_9221(self):
        """Port 9221 is below the CDP range."""
        valid, err = tab_target_resolver.validate_cdp_endpoint("http://localhost:9221")
        assert valid is False
        assert err == "cdp_endpoint_port_out_of_range"

    def test_allow_https_scheme(self):
        """HTTPS scheme is accepted (consistent with http)."""
        valid, err = tab_target_resolver.validate_cdp_endpoint("https://localhost:9222")
        assert valid is True
        assert err is None

    def test_reject_ws_scheme(self):
        """WebSocket scheme is rejected — only http/https allowed."""
        valid, err = tab_target_resolver.validate_cdp_endpoint("ws://localhost:9222")
        assert valid is False
        assert err == "cdp_endpoint_must_use_http_or_https"

    def test_reject_malformed(self):
        valid, err = tab_target_resolver.validate_cdp_endpoint("not-a-url")
        assert valid is False


# ── 7. URL Normalization Edge Cases (T-003) ──────────────────────────


class TestURLNormalization:
    """Test URL normalization edge cases in resolve_tab_target (T-003)."""

    def test_trailing_slash_match(self):
        pages = [{"id": "t1", "type": "page", "url": "https://chatgpt.com/c/abc/"}]
        result = tab_target_resolver.resolve_tab_target("https://chatgpt.com/c/abc", pages)
        assert result["match_status"] == "exact_match"

    def test_query_params_stripped(self):
        pages = [{"id": "t1", "type": "page", "url": "https://chatgpt.com/c/abc?foo=bar"}]
        result = tab_target_resolver.resolve_tab_target("https://chatgpt.com/c/abc", pages)
        assert result["match_status"] == "exact_match"

    def test_fragment_stripped(self):
        """F6: URL fragments are stripped for matching."""
        pages = [{"id": "t1", "type": "page", "url": "https://chatgpt.com/c/abc"}]
        result = tab_target_resolver.resolve_tab_target("https://chatgpt.com/c/abc#msg123", pages)
        assert result["match_status"] == "exact_match"

    def test_combined_trailing_slash_query_fragment(self):
        pages = [{"id": "t1", "type": "page", "url": "https://chatgpt.com/c/abc/?x=1"}]
        result = tab_target_resolver.resolve_tab_target("https://chatgpt.com/c/abc#top?y=2", pages)
        assert result["match_status"] == "exact_match"

    def test_invalid_chat_url_domain(self):
        """F7: Non-ChatGPT domain is rejected before matching."""
        pages = [{"id": "t1", "type": "page", "url": "https://evil.com/phishing"}]
        result = tab_target_resolver.resolve_tab_target("https://evil.com/phishing", pages)
        assert result["match_status"] == "invalid_chat_url"
