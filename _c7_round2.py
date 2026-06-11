import sys, os, json
os.chdir("D:/agent-acceptance")
sys.path.insert(0, "scripts")
from paper_c7_iteration_ledger import start_round, add_issue, close_round, load

# Round 1: close with GPT verdict
r = close_round("M3", 1, "blocked", "GPT: 3 P1 issues found")
print(f"Round 1 closed: {r.get('ok')}")

# Record GPT's P1 issues
for issue_id, desc in [
    ("M3-P1-01", "Section function misalignment: claims 实然之境 but text is normative/prescriptive"),
    ("M3-P1-02", "Unified mechanism gap: mentions 内在统一性 without specifying mechanism"),
    ("M3-P1-03", "Citation credibility: 1057 chars, 0 citations, policy-language only")
]:
    result = add_issue("M3", 1, {"issue_id": issue_id, "severity": "P1", "description": desc, "source": "GPT", "status": "open"})
    print(f"  Issue {issue_id}: {result.get('ok', result.get('duplicate', 'error'))}")

# Start round 2
r2 = start_round("M3", 2)
print(f"Round 2: allowed={r2['allowed']}")

# Check ledger
ledger = load("M3")
print(f"\nLedger status: {ledger['status']}")
print(f"Rounds: {len(ledger['rounds'])}")
for rd in ledger["rounds"]:
    issues = rd.get("issues", [])
    print(f"  Round {rd['round']}: {rd['status']}, {len(issues)} issues")
