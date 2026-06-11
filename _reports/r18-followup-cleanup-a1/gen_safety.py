"""Safety report generator for R18-FOLLOWUP."""
import subprocess, yaml, fnmatch, json, os

os.chdir("D:/agent-acceptance")

r = subprocess.run(['git', 'diff', '--cached', '--name-only'], capture_output=True, encoding='utf-8')
staged = [l.strip() for l in r.stdout.replace("\r", "").split("\n") if l.strip()]

with open('.ai/current-task.yaml', encoding='utf-8') as f:
    task = yaml.safe_load(f)
write_set = task.get('write_set') or []

def matches(path, patterns):
    for p in patterns:
        if fnmatch.fnmatch(path, p) or fnmatch.fnmatch(path.replace("\\", "/"), p):
            return True
    return False

scope_v = [f for f in staged if not matches(f, write_set)]
deny_patterns = ['**/NEG-009-secrets-read.json', '**/.env', '**/credentials.json']
deny_v = [f for f in staged if matches(f, deny_patterns)]

report = {
    'report_id': 'R18-FOLLOWUP-safety',
    'date': '2026-06-11',
    'task_id': task.get('task_id'),
    'files_staged': len(staged),
    'write_set_patterns': len(write_set),
    'scope_violations': len(scope_v),
    'deny_path_violations': len(deny_v),
    'scope_violation_files': scope_v,
    'deny_violation_files': deny_v,
    'overall_verdict': 'PASS' if not scope_v and not deny_v else 'FAIL'
}

with open('_reports/r18-followup-cleanup-a1/safety-report.json', 'w', encoding='utf-8') as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

print(f"Staged: {len(staged)} files")
print(f"Scope violations: {len(scope_v)}")
print(f"Deny violations: {len(deny_v)}")
print(f"Verdict: {report['overall_verdict']}")
for v in scope_v[:10]:
    print(f"  SCOPE: {v}")
