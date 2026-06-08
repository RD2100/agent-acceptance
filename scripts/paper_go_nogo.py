#!/usr/bin/env python3
"""paper_go_nogo.py — Final human GO/NOGO gate for paper pilot. Fail-closed by default.
Checks result semantics, not just file existence."""
import json, sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def _read_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def check():
    """GO requires: auth gate pass + preflight semantic check + pilot result semantics + dry-run packet result semantics."""
    checks = {}

    # 1. Auth gate — must be authorized with bounded scope
    import paper_auth_gate
    checks["auth"] = paper_auth_gate.check()

    # 2. Preflight — validate structured result
    preflight_json = REPO / "_reports" / "paper_pilot_preflight_output.json"
    if preflight_json.exists():
        preflight_data = _read_json(preflight_json)
        checks["preflight"] = preflight_data is not None and preflight_data.get("status") == "PASS"
    else:
        checks["preflight"] = False

    # 3. Pilot runner — check result semantics
    pilot_json = REPO / "evidence_packs" / "paper-c3-dry-run" / "PILOT_RESULT.json"
    pilot_data = _read_json(pilot_json)
    pilot_ok = pilot_data is not None and pilot_data.get("pilot") == "PASS"
    checks["pilot_runner"] = pilot_ok

    # 4. Dry run packet — enforce result semantics
    dr_json = REPO / "evidence_packs" / "paper-c3-dry-run" / "PILOT_RESULT.json"
    dr_data = _read_json(dr_json) if dr_json.exists() else None
    checks["dry_run_packet"] = dr_ok = (dr_data is not None and not dr_data.get("all_gates_passed", True))

    all_ok = checks["auth"]["authorized"] and all(v for v in checks.values() if isinstance(v, bool))
    return {"go": all_ok, "checks": checks, "timestamp": datetime.now(timezone.utc).isoformat()}


def main():
    r = check()
    print(json.dumps(r, indent=2, ensure_ascii=False))
    print(f"\n{'GO' if r['go'] else 'NOGO'}: real-paper pilot is {'AUTHORIZED' if r['go'] else 'BLOCKED'}")
    sys.exit(0 if r["go"] else 1)


if __name__ == "__main__":
    main()
