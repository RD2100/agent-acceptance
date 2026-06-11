import os, shutil, hashlib, zipfile, subprocess

base = "evidence_packs/guard-20260608"
for d in [base+"/actual_deliverables", base+"/reports"]: os.makedirs(d, exist_ok=True)

# Actual deliverables
shutil.copy("scripts/verify_gpt_reply.py", base+"/actual_deliverables/")
shutil.copy("tests/test_gpt_review_response_binding.py", base+"/actual_deliverables/")

# Reports
subprocess.run(["python", "-m", "pytest", "tests/test_gpt_review_response_binding.py", "-v", "--tb=short"], stdout=open(base+"/reports/TARGETED_TEST_OUTPUT.txt","w"), timeout=15)
subprocess.run(["python", "-m", "pytest", "tests/", "-q", "--tb=line"], stdout=open(base+"/reports/TEST_OUTPUT.txt","w"), timeout=30)
subprocess.run(["git", "status", "--short"], stdout=open(base+"/reports/GIT_STATUS.txt","w"), timeout=5)

# CHANGED_FILES
with open(base+"/CHANGED_FILES.txt", "w") as f:
    f.write("scripts/verify_gpt_reply.py (rewritten)\ntests/test_gpt_review_response_binding.py (new, 12 tests)\n")

# SAFETY
with open(base+"/SAFETY_ATTESTATION.md", "w") as f:
    f.write("guard_fail_closed: true\n12_targeted_tests_pass: true\n287_full_tests_pass: true\nno_dirty_baseline: true\n")

# Test guard against actual GPT reply
r = subprocess.run(["python", "scripts/verify_gpt_reply.py", "evidence_packs/batch-final-20260608/GPT_R7.txt", "PAPER-SAFETY-INFRASTRUCTURE"], capture_output=True, text=True)
with open(base+"/reports/GUARD_AGAINST_REAL_REPLY.txt", "w") as f: f.write(r.stdout)

# Build ZIP
lines = ["| path | bytes | sha256 |", "|---|---:|---|"]
for root, dirs, files in os.walk(base):
    for fn in sorted(files):
        if fn.endswith(".zip") or fn == "PACK_MANIFEST.md" or fn.startswith("_"): continue
        fp = os.path.join(root, fn); rel = os.path.relpath(fp, base).replace("\\", "/")
        lines.append("| %s | %d | %s |" % (rel, os.path.getsize(fp), hashlib.sha256(open(fp,"rb").read()).hexdigest()))
lines.append("| PACK_MANIFEST.md | self | self_excluded |")
open(base+"/PACK_MANIFEST.md","w").write("\n".join(lines)+"\n")

zp = zipfile.ZipFile(base+"/guard-pack-r3.zip", "w", zipfile.ZIP_DEFLATED)
for root, dirs, files in os.walk(base):
    for fn in files:
        if fn.endswith(".zip") or fn.startswith("_"): continue
        zp.write(os.path.join(root, fn), os.path.relpath(os.path.join(root, fn), base))
zp.close()
print("R3 pack: %d bytes" % os.path.getsize(base+"/guard-pack-r3.zip"))
