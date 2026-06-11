"""
BINDCHROME-REGISTRY-CLEANUP-VALIDATION-A1
验证脚本：validate_project_registry_bindings.py

8 条规则：
1. project_id 唯一
2. active 项目必须有 chat_url 或 binding_path
3. pending_binding 项目允许无 chat_url
4. active 项目的 binding 文件必须存在
5. binding.project_id == registry.project_id
6. binding.project_root == registry.project_root
7. 不允许 active + chat_url:null
8. 不允许重复指向同一 conversation
"""
import json
import sys
from pathlib import Path

REGISTRY = Path(r"D:\agent-acceptance\.agent\PROJECT_REGISTRY.json")

def load_registry():
    return json.loads(REGISTRY.read_text(encoding="utf-8"))

def load_binding(project_id, project_root):
    """Try to find CONVERSATION_BINDING.json for a project."""
    # Check in project_root/.agent/
    binding_path = Path(project_root) / ".agent" / "CONVERSATION_BINDING.json"
    if binding_path.exists():
        return json.loads(binding_path.read_text(encoding="utf-8")), str(binding_path)
    # Check in _projects/{project_id}/.agent/
    alt_path = Path(r"D:\agent-acceptance\_projects") / project_id / ".agent" / "CONVERSATION_BINDING.json"
    if alt_path.exists():
        return json.loads(alt_path.read_text(encoding="utf-8")), str(alt_path)
    return None, None

def validate():
    reg = load_registry()
    projects = reg["projects"]
    results = []
    passed = 0
    failed = 0

    print("=" * 60)
    print("BINDCHROME REGISTRY BINDING VALIDATION")
    print(f"Registry: {REGISTRY}")
    print(f"Total projects: {reg['total_projects']}")
    print(f"Actual entries: {len(projects)}")
    print("=" * 60)

    # Rule 1: project_id unique
    ids = list(projects.keys())
    dup_ids = [x for x in ids if ids.count(x) > 1]
    r1 = len(dup_ids) == 0
    results.append(("Rule 1: project_id unique", r1, f"IDs: {ids}, Duplicates: {dup_ids}"))

    # Rule 7: no active + chat_url:null
    r7_issues = []
    for pid, pdata in projects.items():
        if pdata["binding_status"] == "active":
            binding, bpath = load_binding(pid, pdata["project_root"])
            if binding:
                for b in binding.get("bindings", []):
                    if b.get("chat_url") is None:
                        r7_issues.append(f"{pid}: active but chat_url is null")
            else:
                r7_issues.append(f"{pid}: active but no binding file found")
    r7 = len(r7_issues) == 0
    results.append(("Rule 7: no active + chat_url:null", r7, 
                     "PASS" if r7 else f"Issues: {r7_issues}"))

    # Rule 2: active projects must have chat_url or binding_path
    r2_issues = []
    for pid, pdata in projects.items():
        if pdata["binding_status"] == "active":
            binding, bpath = load_binding(pid, pdata["project_root"])
            if not binding and not bpath:
                r2_issues.append(f"{pid}: no binding file")
            elif binding:
                has_url = any(b.get("chat_url") for b in binding.get("bindings", []))
                if not has_url:
                    r2_issues.append(f"{pid}: binding exists but no chat_url")
    r2 = len(r2_issues) == 0
    results.append(("Rule 2: active has chat_url", r2,
                     "PASS" if r2 else f"Issues: {r2_issues}"))

    # Rule 3: pending_binding projects may lack chat_url (informational)
    pending = {pid: pdata for pid, pdata in projects.items() 
               if pdata["binding_status"] == "pending_binding"}
    r3 = True  # Always pass - pending is allowed to lack binding
    results.append(("Rule 3: pending_binding allowed no chat_url", r3,
                     f"Pending projects: {list(pending.keys())}"))

    # Rule 4: active projects must have binding file on disk
    r4_issues = []
    for pid, pdata in projects.items():
        if pdata["binding_status"] == "active":
            binding, bpath = load_binding(pid, pdata["project_root"])
            if not bpath:
                r4_issues.append(f"{pid}: binding file not found")
            else:
                pass  # File exists
    r4 = len(r4_issues) == 0
    results.append(("Rule 4: active binding file exists", r4,
                     "PASS" if r4 else f"Issues: {r4_issues}"))

    # Rule 5: binding.project_id == registry.project_id
    r5_issues = []
    for pid, pdata in projects.items():
        binding, bpath = load_binding(pid, pdata["project_root"])
        if binding:
            if binding.get("project_id") != pid:
                r5_issues.append(f"{pid}: binding says '{binding.get('project_id')}' but registry says '{pid}'")
    r5 = len(r5_issues) == 0
    results.append(("Rule 5: binding.project_id matches", r5,
                     "PASS" if r5 else f"Issues: {r5_issues}"))

    # Rule 6: binding.project_root == registry.project_root
    r6_issues = []
    for pid, pdata in projects.items():
        binding, bpath = load_binding(pid, pdata["project_root"])
        if binding:
            b_root = binding.get("project_root", "").replace("/", "\\")
            r_root = pdata["project_root"].replace("/", "\\")
            if b_root != r_root:
                r6_issues.append(f"{pid}: binding root='{b_root}' vs registry root='{r_root}'")
    r6 = len(r6_issues) == 0
    results.append(("Rule 6: binding.project_root matches", r6,
                     "PASS" if r6 else f"Issues: {r6_issues}"))

    # Rule 8: no duplicate conversation_id
    conv_ids = []
    for pid, pdata in projects.items():
        binding, bpath = load_binding(pid, pdata["project_root"])
        if binding:
            for b in binding.get("bindings", []):
                cid = b.get("conversation_id")
                if cid and not cid.startswith("pending-"):
                    conv_ids.append((pid, cid))
    dup_convs = {}
    for pid, cid in conv_ids:
        if cid in dup_convs:
            dup_convs[cid].append(pid)
        else:
            dup_convs[cid] = [pid]
    real_dups = {cid: pids for cid, pids in dup_convs.items() if len(pids) > 1}
    r8 = len(real_dups) == 0
    results.append(("Rule 8: no duplicate conversation_id", r8,
                     "PASS" if r8 else f"Duplicates: {real_dups}"))

    # Print results
    print()
    for rule, ok, detail in results:
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {rule}")
        print(f"         {detail}")
        print()
        if ok:
            passed += 1
        else:
            failed += 1

    # Route resolution dry-run
    print("-" * 60)
    print("ROUTE RESOLUTION DRY-RUN")
    print("-" * 60)
    for pid, pdata in projects.items():
        binding, bpath = load_binding(pid, pdata["project_root"])
        status = pdata["binding_status"]
        if status == "active" and binding:
            url = binding["bindings"][0].get("chat_url", "N/A")
            conv = binding["bindings"][0].get("conversation_id", "N/A")
            print(f"  {pid}: Registry -> Binding({bpath}) -> chat_url={url} -> ROUTABLE")
        elif status == "pending_binding":
            print(f"  {pid}: Registry -> pending_binding -> NO AUTO-SUBMIT -> SAFE")
        else:
            print(f"  {pid}: Registry -> NO BINDING -> NOT ROUTABLE (issue!)")

    # Removed projects check
    print()
    print("-" * 60)
    print("REMOVED PROJECTS VERIFICATION")
    print("-" * 60)
    removed = ["project-gamma", "project-delta", "project-epsilon", 
               "project-zeta", "project-eta", "project-theta", "project-iota",
               "dev-frame-writing"]
    for rpid in removed:
        in_registry = rpid in projects
        dir_exists = Path(r"D:\agent-acceptance\_projects") / rpid.replace("dev-frame-", "") 
        # Check physical dir
        if rpid == "dev-frame-writing":
            phys = Path(r"D:\agent-acceptance\_projects\dev-frame-writing")
        else:
            phys = Path(r"D:\agent-acceptance\_projects") / rpid
        phys_exists = phys.exists()
        print(f"  {rpid}: in_registry={in_registry}, dir_exists={phys_exists}")

    # Summary
    print()
    print("=" * 60)
    total = passed + failed
    print(f"RESULT: {passed}/{total} rules passed, {failed} failed")
    if failed == 0:
        print("STATUS: ALL CHECKS PASSED")
    else:
        print("STATUS: SOME CHECKS FAILED")
    print("=" * 60)

    return failed == 0

if __name__ == "__main__":
    ok = validate()
    sys.exit(0 if ok else 1)
