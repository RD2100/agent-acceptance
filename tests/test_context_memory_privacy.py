"""Test privacy guard fail-closed behavior."""
import sys
import tempfile
import os
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from validate_context_memory import check_privacy, validate_file


class TestPrivacyGuardFailClosed:
    """Privacy guard must fail closed on forbidden content."""

    def test_raw_paper_text_in_memory_entry_must_fail(self):
        """Memory entry containing raw_paper_text marker as content must fail."""
        text = "This memory entry contains raw_paper_text from the thesis chapter 1."
        result = check_privacy(text, "memory/tasks/test-paper.md")
        assert not result["pass"], f"Should fail but passed: {result}"

    def test_private_user_text_in_memory_entry_must_fail(self):
        """Memory entry containing private_user_text marker as content must fail."""
        text = "User data: private_user_text was found in the submission."
        result = check_privacy(text, "memory/tasks/test-private.md")
        assert not result["pass"], f"Should fail but passed: {result}"

    def test_raw_transcript_in_memory_entry_must_fail(self):
        """Memory entry containing raw_transcript marker as content must fail."""
        text = "Here is the raw_transcript from the conversation."
        result = check_privacy(text, "memory/tasks/test-transcript.md")
        assert not result["pass"], f"Should fail but passed: {result}"

    def test_secret_token_in_memory_must_fail(self):
        """Memory entry containing secret=value must fail."""
        text = "api_key=sk-1234567890abcdef secret=mysecret"
        result = check_privacy(text, "memory/tasks/test-secret.md")
        assert not result["pass"], f"Should fail but passed: {result}"

    def test_api_key_value_in_memory_must_fail(self):
        """Memory entry containing api_key: <value> must fail."""
        text = "OpenAI config: api_key: sk-proj-1234567890abcdefghij"
        result = check_privacy(text, "memory/tasks/test-apikey.md")
        assert not result["pass"], f"Should fail but passed: {result}"

    def test_doctor_paper_full_text_marker_must_fail(self):
        """Memory entry containing 博士论文正文 as content must fail."""
        text = "以下是博士论文正文的第三章内容摘要..."
        result = check_privacy(text, "memory/tasks/test-doctor.md")
        assert not result["pass"], f"Should fail but passed: {result}"


class TestPrivacyGuardPass:
    """Privacy guard must pass on legitimate task metadata."""

    def test_task_metadata_only_should_pass(self):
        """Memory entry with only task_id, review_run_id, verdict, hash should pass."""
        text = """task_id: GROUP-01
review_run_id: group-01-contract-backfill-v1
overall_judgment: accepted
evidence_pack_sha256: 390654644cd913c461f6dc970684d461021d61b06e5ac9cd773343b6c8630465
implementation_commit: fc2b217
"""
        result = check_privacy(text, "memory/tasks/GROUP-01.md")
        assert result["pass"], f"Should pass but failed: {result['issues']}"

    def test_safety_boundary_documentation_should_pass(self):
        """Safety boundary documentation listing forbidden terms should pass."""
        text = """# 绝对安全边界（永久禁止）
以下内容严格禁止：
- secret
- token
- api_key
- cookie
- session
- 博士论文正文
"""
        result = check_privacy(text, "memory/knowledge/safety.md")
        assert result["pass"], f"Should pass but failed: {result['issues']}"

    def test_boot_context_should_pass(self):
        """BOOT_CONTEXT.md content should pass privacy check."""
        text = """# BOOT_CONTEXT.md
## 安全边界
绝对禁止：cookies/session/browser profile 读取、secret 写入、token 泄露。
"""
        result = check_privacy(text, "BOOT_CONTEXT.md")
        assert result["pass"], f"Should pass but failed: {result['issues']}"

    def test_sha256_hashes_should_not_trigger_secret_check(self):
        """SHA256 hashes (64 hex chars) are evidence hashes, not secrets."""
        text = """evidence_pack_sha256: 390654644cd913c461f6dc970684d461021d61b06e5ac9cd773343b6c8630465"""
        result = check_privacy(text, "memory/tasks/test-hash.md")
        assert result["pass"], f"Should pass but failed: {result['issues']}"


class TestPrivacyGuardRealFiles:
    """Verify all generated memory outputs pass privacy guard."""

    def test_all_generated_outputs_pass(self):
        """All generated BOOT_CONTEXT, memory/* files must pass."""
        repo = Path(__file__).parent.parent
        files = list(repo.glob("BOOT_CONTEXT.md"))
        files += list(repo.glob("memory/index.md"))
        files += list(repo.glob("memory/tasks/*.md"))
        files += list(repo.glob("memory/knowledge/*.md"))

        assert len(files) > 0, "No generated files found"

        failed = []
        for fp in files:
            result = validate_file(fp)
            if not result["pass"]:
                failed.append((str(fp), result["issues"]))

        assert len(failed) == 0, f"Privacy violations in generated files: {failed}"


class TestPrivacyGuardSafetyDocWithContent:
    """Safety doc with embedded actual content MUST fail."""

    def test_safety_header_with_raw_paper_text_content_must_fail(self):
        """Safety doc header + raw_paper_text: actual content on separate line must fail."""
        text = """# 安全边界
以下是禁止内容列表：
raw_paper_text: 第三章关于机器学习的论述主要围绕深度学习展开...
"""
        result = check_privacy(text, "memory/tasks/test-leak.md")
        assert not result["pass"], f"Should FAIL: safety doc with actual paper content. Got: {result}"

    def test_safety_doc_with_private_user_text_must_fail(self):
        """Safety doc with private_user_text: actual content must fail."""
        text = """# 隐私规则
不得包含以下内容。
但下面是实际用户数据：
private_user_text: 用户张三在2024年3月提交了论文初稿...
"""
        result = check_privacy(text, "memory/tasks/test-leak2.md")
        assert not result["pass"], f"Should FAIL: safety doc with actual private text. Got: {result}"

    def test_safety_doc_with_raw_transcript_must_fail(self):
        """Safety doc with raw_transcript: actual content must fail."""
        text = """# 注意事项
禁止上传 raw_transcript。
raw_transcript: User: 我的论文是关于... GPT: 我理解你的论文主题是...
"""
        result = check_privacy(text, "memory/tasks/test-leak3.md")
        assert not result["pass"], f"Should FAIL: safety doc with actual transcript. Got: {result}"

    def test_safety_doc_with_doctor_paper_content_must_fail(self):
        """Safety doc that mentions 博士论文正文 as forbidden, but then has actual content."""
        text = """# 安全规则
禁止博士论文正文内容。
博士论文正文: 本研究探讨了人工智能在医疗诊断中的应用...
"""
        result = check_privacy(text, "memory/tasks/test-leak4.md")
        assert not result["pass"], f"Should FAIL: safety doc with actual paper content. Got: {result}"

    def test_safety_bullet_list_only_must_pass(self):
        """Pure safety documentation bullet list (no actual content) must pass."""
        text = """# 绝对安全边界
以下内容严格禁止出现在任何输出中：
- raw_paper_text
- private_user_text
- raw_transcript
- 博士论文正文
- secret
- api_key
"""
        result = check_privacy(text, "memory/tasks/test-ok.md")
        assert result["pass"], f"Should PASS: pure safety doc. Got: {result['issues']}"


class TestPrivacyGuardPayloadInSafetyContext:
    """Forbidden marker with payload in safety context MUST fail."""

    def test_safety_bullet_with_raw_paper_payload_must_fail(self):
        """# 安全边界\n- raw_paper_text: ACTUAL PAPER CONTENT → FAIL"""
        text = """# 安全边界
- raw_paper_text: ACTUAL PAPER CONTENT 泄漏在此
"""
        result = check_privacy(text, "test.md")
        assert not result["pass"], f"Should FAIL: bullet with raw_paper_text payload"

    def test_safety_header_with_raw_paper_payload_must_fail(self):
        """# raw_paper_text: ACTUAL PAPER CONTENT → FAIL"""
        text = "# raw_paper_text: ACTUAL PAPER CONTENT 泄漏在此\n"
        result = check_privacy(text, "test.md")
        assert not result["pass"], f"Should FAIL: header with raw_paper_text payload"

    def test_safety_bullet_with_private_user_text_payload_must_fail(self):
        """# 隐私规则\n- private_user_text: ACTUAL USER DATA → FAIL"""
        text = """# 隐私规则
- private_user_text: ACTUAL USER DATA 用户张三的数据
"""
        result = check_privacy(text, "test.md")
        assert not result["pass"], f"Should FAIL: bullet with private_user_text payload"

    def test_safety_bullet_with_raw_transcript_payload_must_fail(self):
        """# 注意事项\n- raw_transcript: User: ... GPT: ... → FAIL"""
        text = """# 注意事项
- raw_transcript: User: 我的论文是关于... GPT: 我理解你的论文主题是...
"""
        result = check_privacy(text, "test.md")
        assert not result["pass"], f"Should FAIL: bullet with raw_transcript payload"

    def test_pure_safety_bullet_list_still_passes(self):
        """Pure forbidden-term bullet list (no payload) → PASS"""
        text = """# 绝对安全边界（永久禁止）
以下内容严格禁止：
- raw_paper_text
- private_user_text
- raw_transcript
- 博士论文正文
- secret
- api_key
"""
        result = check_privacy(text, "test.md")
        assert result["pass"], f"Should PASS: pure safety bullet list. Got: {result['issues']}"

    def test_bullet_with_doctor_paper_payload_must_fail(self):
        """Bullet: 博士论文正文: ACTUAL CONTENT → FAIL"""
        text = """# 禁止事项
- 博士论文正文: 本研究探讨了人工智能在医疗诊断中的应用
"""
        result = check_privacy(text, "test.md")
        assert not result["pass"], f"Should FAIL: bullet with 博士论文正文 payload"

    def test_safety_bullet_with_api_key_payload_must_fail(self):
        """Safety bullet with api_key: sk-xxx → FAIL"""
        text = """# 安全边界
- api_key: sk-abcdef1234567890
"""
        result = check_privacy(text, "test.md")
        assert not result["pass"], f"Should FAIL: safety bullet with api_key payload"

    def test_safety_bullet_with_token_payload_must_fail(self):
        """Safety bullet with token: abcdefghijklmnop → FAIL"""
        text = """# 安全边界
- token: abcdefghijklmnop
"""
        result = check_privacy(text, "test.md")
        assert not result["pass"], f"Should FAIL: safety bullet with token payload"

    def test_safety_bullet_with_secret_payload_must_fail(self):
        """Safety bullet with secret: actual-secret → FAIL"""
        text = """# 安全边界
- secret: actual-secret-value
"""
        result = check_privacy(text, "test.md")
        assert not result["pass"], f"Should FAIL: safety bullet with secret payload"

    def test_safety_bullet_with_cookie_payload_must_fail(self):
        """Safety bullet with cookie: actual-cookie → FAIL"""
        text = """# 安全边界
- cookie: actual-cookie-value
"""
        result = check_privacy(text, "test.md")
        assert not result["pass"], f"Should FAIL: safety bullet with cookie payload"

    def test_safety_bullet_with_session_payload_must_fail(self):
        """Safety bullet with session: abcdefghijklmnop → FAIL"""
        text = """# 安全边界
- session: abcdefghijklmnop
"""
        result = check_privacy(text, "test.md")
        assert not result["pass"], f"Should FAIL: safety bullet with session payload"


class TestPrivacyGuardEdgeCases:
    """Edge case tests."""

    def test_empty_file_should_pass(self):
        """Empty content should pass."""
        result = check_privacy("", "memory/tasks/empty.md")
        assert result["pass"]

    def test_chinese_only_task_metadata_should_pass(self):
        """Chinese task metadata without forbidden content should pass."""
        text = """任务ID: GROUP-01
状态: accepted
范围: only selected files
"""
        result = check_privacy(text, "memory/tasks/chinese-task.md")
        assert result["pass"], f"Should pass but failed: {result['issues']}"

    def test_long_base64_not_hex_should_fail(self):
        """A long non-hex base64 string (looks like encoded secret) should fail."""
        text = "encoded_data: dGhpcyBpc250IHJlYWxseSBhIHNlY3JldCBidXQgaXQgbG9va3MgbGlrZSBvbmU="
        result = check_privacy(text, "memory/tasks/test-base64.md")
        # This is a long non-hex string, should trigger base64 check
        assert not result["pass"], f"Should fail on long non-hex base64: {result}"
