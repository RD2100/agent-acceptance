"""Test boot context builder."""
import sys
import os
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import build_boot_context as bcb


class TestBootContextBuilder:
    """Test BOOT_CONTEXT.md generation."""

    def test_build_generates_file(self):
        """build_boot_context should generate a file."""
        with tempfile.TemporaryDirectory() as tmp:
            output = os.path.join(tmp, "BOOT_CONTEXT.md")
            result = bcb.build_boot_context(output_path=output)
            assert os.path.exists(output)
            assert result["total_characters"] > 0

    def test_boot_context_within_char_limit(self):
        """BOOT_CONTEXT.md should be 3000-6000 characters."""
        with tempfile.TemporaryDirectory() as tmp:
            output = os.path.join(tmp, "BOOT_CONTEXT.md")
            result = bcb.build_boot_context(output_path=output)
            assert 3000 <= result["total_characters"] <= 6000, \
                f"Char count {result['total_characters']} not in 3000-6000 range"
            assert result["within_limit"] is True

    def test_boot_context_has_required_sections(self):
        """BOOT_CONTEXT.md must contain all 8 required sections."""
        with tempfile.TemporaryDirectory() as tmp:
            output = os.path.join(tmp, "BOOT_CONTEXT.md")
            bcb.build_boot_context(output_path=output)
            content = Path(output).read_text(encoding="utf-8")

        required_titles = [
            "项目身份",
            "三层架构",
            "当前阶段",
            "最近 Accepted",
            "开放风险",
            "下一步推荐",
            "绝对安全边界",
            "冷启动读取顺序",
        ]
        for title in required_titles:
            assert title in content, f"Missing section: {title}"

    def test_boot_context_has_hash(self):
        """BOOT_CONTEXT.md should have a SHA256 hash."""
        with tempfile.TemporaryDirectory() as tmp:
            output = os.path.join(tmp, "BOOT_CONTEXT.md")
            result = bcb.build_boot_context(output_path=output)
            assert len(result["hash"]) == 64
            assert result["hash"].isalnum() or all(c in "0123456789abcdef" for c in result["hash"])

    def test_boot_context_not_copy_full_project_history(self):
        """BOOT_CONTEXT.md must NOT be a copy of full PROJECT_HISTORY.md."""
        with tempfile.TemporaryDirectory() as tmp:
            output = os.path.join(tmp, "BOOT_CONTEXT.md")
            bcb.build_boot_context(output_path=output)
            bc = Path(output).read_text(encoding="utf-8")

        ph = Path(__file__).parent.parent / "PROJECT_HISTORY.md"
        ph_text = ph.read_text(encoding="utf-8") if ph.exists() else ""

        # BOOT_CONTEXT should be dramatically shorter than PROJECT_HISTORY
        assert len(bc) < len(ph_text) * 0.5, \
            f"BOOT_CONTEXT ({len(bc)} chars) should be < 50% of PROJECT_HISTORY ({len(ph_text)} chars)"

    def test_boot_context_does_not_contain_full_binding_blocks(self):
        """BOOT_CONTEXT should not paste entire binding YAML blocks."""
        with tempfile.TemporaryDirectory() as tmp:
            output = os.path.join(tmp, "BOOT_CONTEXT.md")
            bcb.build_boot_context(output_path=output)
            bc = Path(output).read_text(encoding="utf-8")

        # Should not contain large verbatim binding blocks
        assert "evidence_pack_sha256" not in bc or bc.count("evidence_pack_sha256") <= 5, \
            "BOOT_CONTEXT contains too many evidence_pack_sha256 references"


class TestBootContextSchema:
    """Test boot context output matches schema requirements."""

    def test_generated_at_is_iso_format(self):
        """generated_at should be ISO 8601."""
        with tempfile.TemporaryDirectory() as tmp:
            output = os.path.join(tmp, "BOOT_CONTEXT.md")
            result = bcb.build_boot_context(output_path=output)
            assert "T" in result["generated_at"]
            assert "+" in result["generated_at"] or "Z" in result["generated_at"]

    def test_boot_context_markdown_structure(self):
        """Generated file should be valid markdown with h1 title."""
        with tempfile.TemporaryDirectory() as tmp:
            output = os.path.join(tmp, "BOOT_CONTEXT.md")
            bcb.build_boot_context(output_path=output)
            bc = Path(output).read_text(encoding="utf-8")

        assert bc.startswith("# BOOT_CONTEXT.md")
        assert "## 1." in bc
        assert "## 8." in bc
