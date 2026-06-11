import sys, os
os.chdir("D:/agent-acceptance")
sys.path.insert(0, "scripts")
from paper_c7_iteration_ledger import close_round, module_status

close_round("M3", 3, "pass_with_limitation", "GPT accepted: all P1 issues resolved")
s = module_status("M3")
print(f"M3: {s['status']}")

for mid in ["M1","M2","M3","M4","M5","M6"]:
    st = module_status(mid)
    print(f"  {mid}: {st['status']}")
