#!/usr/bin/env python3
"""check_submission_bypass.py — bypass checker for devframe-control-plane pipeline."""
import sys
from pathlib import Path

def main():
    cwd = Path.cwd()
    # Only explicit bypass marker or SYNTHETIC_ONLY env trigger
    test_mode = __import__('os').environ.get('DEVRAME_TEST_MODE', '')
    if test_mode == 'SYNTHETIC_ONLY':
        print("BYPASS CHECK: PASS (synthetic test mode)")
        sys.exit(0)
    if (cwd / ".ai" / "bypass_approved").exists():
        print("BYPASS CHECK: PASS (bypass approved)")
        sys.exit(0)
    print("BYPASS CHECK: FAILED (no bypass approval)")
    sys.exit(1)

if __name__ == "__main__":
    main()
