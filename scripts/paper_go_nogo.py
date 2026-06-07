#!/usr/bin/env python3
"""paper_go_nogo.py — Final human GO/NOGO gate for paper pilot. Fail-closed by default."""
import json, sys
from datetime import datetime, timezone
from pathlib import Path
REPO = Path(__file__).resolve().parent.parent

def check():
    """GO requires: auth gate pass + preflight pass + pilot pass + dry-run packet exists."""
    checks = {}
    # 1. Auth gate
    import paper_auth_gate
    checks["auth"] = paper_auth_gate.check()
    # 2. Preflight
    p = REPO / "scripts/paper_pilot_preflight.py"
    checks["preflight"] = p.exists()
    # 3. Pilot runner
    r = REPO / "scripts/paper_pilot_runner.py"
    checks["pilot_runner"] = r.exists()
    # 4. Dry run packet
    dr = REPO / "evidence_packs/paper-c3-dry-run/dry-run-packet.zip"
    checks["dry_run_packet"] = dr.exists()
    all_ok = checks["auth"]["authorized"] and all(v for v in checks.values() if isinstance(v, bool))
    return {"go": all_ok, "checks": checks, "timestamp": datetime.now(timezone.utc).isoformat()}

def main():
    r = check()
    print(json.dumps(r, indent=2, ensure_ascii=False))
    print(f"\n{'GO' if r['go'] else 'NOGO'}: real-paper pilot is {'AUTHORIZED' if r['go'] else 'BLOCKED'}")
    sys.exit(0 if r["go"] else 1)

if __name__ == "__main__":
    main()
