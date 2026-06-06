"""Test paper workflow memory privacy rules."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def test_paper_rules_doc_exists():
    p = Path("docs/paper-workflow-memory-rules.md")
    assert p.exists()
    text = p.read_text(encoding="utf-8")
    assert "真实论文全文" in text
    assert "绝对禁止进入记忆" in text
    assert "允许进入记忆" in text


def test_paper_rules_prohibit_full_text():
    text = Path("docs/paper-workflow-memory-rules.md").read_text(encoding="utf-8")
    prohibited = ["真实论文全文", "论文片段", "用户身份", "博士论文草稿", "未发表稿件"]
    for phrase in prohibited:
        assert phrase in text, f"Missing prohibited category: {phrase}"


def test_paper_rules_allow_redacted():
    text = Path("docs/paper-workflow-memory-rules.md").read_text(encoding="utf-8")
    allowed = ["审稿维度得分", "工作流教训", "模板使用经验", "失败模式"]
    for phrase in allowed:
        assert phrase in text, f"Missing allowed category: {phrase}"


def test_memory_compiler_exists():
    p = Path("scripts/memory_compiler.py")
    assert p.exists()
    text = p.read_text(encoding="utf-8")
    assert "lessons" in text.lower()


def run_all_tests():
    tests = [
        ("paper rules doc exists", test_paper_rules_doc_exists),
        ("paper rules prohibit full text", test_paper_rules_prohibit_full_text),
        ("paper rules allow redacted", test_paper_rules_allow_redacted),
        ("memory compiler exists", test_memory_compiler_exists),
    ]
    passed = failed = 0
    print("=" * 60)
    print("Paper Memory Rules — Tests")
    print("=" * 60)
    for name, fn in tests:
        try:
            fn()
            print(f"  [PASS] {name}")
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {name}: {e}")
            failed += 1
    print(f"\n  Results: {passed}/{passed+failed} passed")
    return failed == 0


if __name__ == "__main__":
    sys.exit(0 if run_all_tests() else 1)
