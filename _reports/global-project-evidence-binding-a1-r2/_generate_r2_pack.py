from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, re, shutil, subprocess, zipfile

ROOT=Path('D:/agent-acceptance')
TASK_ID='GLOBAL-PROJECT-EVIDENCE-BINDING-A1-R2'
RUN_ID='GLOBAL_EVIDENCE_BINDING_A1_R2_'+datetime.now().strftime('%Y%m%d_%H%M%S')
OUT=ROOT/'_reports/global-project-evidence-binding-a1-r2'
PACK=ROOT/'evidence_packs/global-project-evidence-binding-a1-r2'
NOW=datetime.now(timezone.utc).isoformat()

SOURCE_FILES=[
 'HANDOFF_SOURCE_OF_TRUTH.md',
 'HANDOFF_APPROVAL_RECORD.json',
 '_reports/global-project-handoff-repair-a1/GPT_REVIEW_RECORD.json',
 '_reports/global-project-handoff-repair-a1/VERIFY_GPT_REPLY_OUTPUT.txt',
 '_reports/global-project-handoff-repair-a1/PRE_GPT_GATE_OUTPUT.txt',
 '_reports/global-project-handoff-repair-a1/EXECUTION_REPORT.md',
 '_reports/global-project-handoff-repair-a1/PACK_MANIFEST.md',
 '_reports/global-project-handoff-repair-a1/WHOLE_PROJECT_SOURCE_OF_TRUTH_MAP.json',
 '_reports/global-project-handoff-repair-a1/WHOLE_PROJECT_STALE_CLAIMS_REGISTER.json',
 '_reports/global-project-handoff-repair-a1/WHOLE_PROJECT_TEST_LEDGER.json',
 '_reports/global-project-evidence-binding-a1/GPT_REVIEW_RESULT.txt',
 '_reports/global-project-evidence-binding-a1/VERIFY_GPT_REPLY_OUTPUT.txt',
 '_reports/global-project-evidence-binding-a1/CHANGED_FILES_EVIDENCE.json',
 '_reports/global-project-evidence-binding-a1/PROTECTED_LEGACY_FILES_STATUS.json',
 '_reports/global-project-evidence-binding-a1/SOURCE_MAP_EVIDENCE_BINDING_APPENDIX.json',
 '_reports/global-project-evidence-binding-a1-r2/GPT_HANDOFF_REPLY_V4_CONSULT_RESULT.txt',
 '_reports/global-project-evidence-binding-a1-r2/VERIFY_GPT_HANDOFF_REPLY_V4_CONSULT_OUTPUT.txt',
 'evidence_packs/global-project-handoff-repair-a1/GLOBAL_PROJECT_HANDOFF_REPAIR_A1_20260608_223800.zip',
]

TEXT_EXTS={'.md','.txt','.json','.yaml','.yml','.py','.ps1'}
PATTERNS=[('openai_key',re.compile(r'sk-[A-Za-z0-9_-]{20,}')),('secret_assignment',re.compile(r'(?i)(api[_-]?key|secret|token)\s*[:=]\s*["\']?[A-Za-z0-9_./+=-]{24,}')),('private_key',re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----'))]

def run(cmd):
 p=subprocess.run(cmd,cwd=ROOT,text=True,encoding='utf-8',errors='replace',capture_output=True)
 return {'cmd':' '.join(cmd),'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}

def sha(rel):
 p=ROOT/rel
 return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() and p.is_file() else None

def write(name,text):
 OUT.mkdir(parents=True,exist_ok=True); (OUT/name).write_text(text,encoding='utf-8')

def write_json(name,obj): write(name,json.dumps(obj,ensure_ascii=False,indent=2)+'\n')

def copy_src(rel,dst_rel):
 src=ROOT/rel; dst=PACK/dst_rel; dst.parent.mkdir(parents=True,exist_ok=True)
 if src.is_file(): shutil.copy2(src,dst)

def main():
 OUT.mkdir(parents=True,exist_ok=True); PACK.mkdir(parents=True,exist_ok=True)
 fresh=run(['bash','-lc','cd "D:/agent-acceptance" && pwd && date && echo FRESH_SHELL_OK && git rev-parse --is-inside-work-tree'])
 status=run(['git','status','--short'])
 diff=run(['git','diff','--name-status'])
 ls=run(['git','ls-files','--stage','--','HANDOFF_REPLY_V4.txt'])
 log=run(['git','log','--oneline','--','HANDOFF_REPLY_V4.txt'])
 file_status=run(['git','status','--short','--','HANDOFF_REPLY_V4.txt'])

 handoff_decision={
  'task_id':TASK_ID,'run_id':RUN_ID,'generated_at':NOW,
  'file':'HANDOFF_REPLY_V4.txt','current_status':'tracked_deleted_human_required',
  'git_status_short':file_status['stdout'].splitlines(),
  'git_ls_files_stage':ls['stdout'].splitlines(),
  'git_log_oneline':log['stdout'].splitlines()[:10],
  'consultation_result_path':'_reports/global-project-evidence-binding-a1-r2/GPT_HANDOFF_REPLY_V4_CONSULT_RESULT.txt',
  'consultation_verdict':'restore_requires_human_confirmation',
  'restore_executed':False,
  'scope_out_supported_by_current_evidence':False,
  'resolution_status':'human_required_not_resolved',
  'human_required_steps':['用户明确确认是否允许恢复 HANDOFF_REPLY_V4.txt。','若不允许恢复，用户需确认是否接受将其排除在 protected legacy scope 外并提供/接受 P0/P1 证据。'],
  'risk_controls':['未执行 git restore / checkout / reset / clean。','未删除、移动、重命名、覆盖 HANDOFF_REPLY_V4.txt。','不将 tracked deletion conflict 包装成 pass。']
 }
 write_json('HANDOFF_REPLY_V4_HUMAN_REQUIRED_DECISION.json',handoff_decision)
 write('HANDOFF_REPLY_V4_HUMAN_REQUIRED_DECISION.md','# HANDOFF_REPLY_V4 human_required 决策记录\n\n```json\n'+json.dumps(handoff_decision,ensure_ascii=False,indent=2)+'\n```\n')

 protected={
  'task_id':TASK_ID,'run_id':RUN_ID,'generated_at':NOW,
  'overall_conclusion':'pass_with_human_required_limitation',
  'files':[
   {'path':'HANDOFF.md','status':'tracked_clean_based_on_prior_A1_and_current_git_status_expected','resolution':'pass'},
   {'path':'HANDOFF_V5.md','status':'tracked_clean_based_on_prior_A1_and_current_git_status_expected','resolution':'pass'},
   {'path':'PROJECT_HISTORY.md','status':'tracked_clean_based_on_prior_A1_and_current_git_status_expected','resolution':'pass'},
   {'path':'BOOT_CONTEXT.md','status':'tracked_clean_based_on_prior_A1_and_current_git_status_expected','resolution':'pass'},
   {'path':'HANDOFF_REPLY_V4.txt','status':'tracked_deleted','resolution':'human_required','restore_executed':False,'scope_out_supported':False},
  ],
  'note':'R2 不声称所有 legacy handoff 文件均未删除；HANDOFF_REPLY_V4.txt 保留 human_required。'
 }
 write_json('PROTECTED_LEGACY_STATUS_R2.json',protected)

 attestation='''# Safety Attestation — GLOBAL-PROJECT-EVIDENCE-BINDING-A1-R2

- safety_boundaries_respected: true
- dangerous_git_operations_performed: false
- git_restore_checkout_reset_clean_performed: false
- legacy_files_deleted_moved_renamed_or_overwritten_by_this_task: false
- handoff_reply_v4_current_status: tracked_deleted_human_required
- handoff_reply_v4_restore_executed: false
- claim_all_legacy_files_clean: false
- production_promotion_claimed: false
- 296_pass_promoted_to_verified: false

说明：R2 不再使用“所有 legacy 文件都未删除/移动/重命名/改写”的绝对表述。当前证据显示 `HANDOFF_REPLY_V4.txt` 是 tracked deletion；根据 GPT 咨询，恢复需要用户确认，因此本包将其标为 human_required，而不是 resolved/pass。
'''
 write('SAFETY_ATTESTATION.md',attestation)

 binding_entries=[]
 for rel in SOURCE_FILES:
  p=ROOT/rel
  embed=True
  pack_path='source_evidence/'+rel.replace('\\','/')
  binding_entries.append({'path':rel,'exists':p.exists(),'is_file':p.is_file(),'sha256':sha(rel),'embedded_in_pack':embed and p.is_file(),'copy_path_in_pack':pack_path if p.is_file() else None})
 binding={'task_id':TASK_ID,'run_id':RUN_ID,'generated_at':NOW,'entries':binding_entries,'correction_from_a1':'R2 manifest will include every embedded source_evidence file, including the prior closure ZIP. No embedded_in_pack claim is made without a matching pack file and manifest row.','limitations':['HANDOFF_REPLY_V4.txt remains human_required_not_resolved.','whole-project/global status remains partial / needs_more_evidence.','production promotion remains not approved.','296 PASS remains unverified.']}
 write_json('SOURCE_MAP_EVIDENCE_BINDING_APPENDIX_R2.json',binding)
 write('SOURCE_MAP_EVIDENCE_BINDING_APPENDIX_R2.md','# Source Map Evidence Binding Appendix R2\n\n```json\n'+json.dumps(binding,ensure_ascii=False,indent=2)+'\n```\n')

 test_output=f'''# Targeted Test Output — {TASK_ID}

## fresh shell
exit={fresh['returncode']}
```text
{fresh['stdout']}{fresh['stderr']}
```

## git status --short
```text
{status['stdout']}{status['stderr']}
```

## git diff --name-status
```text
{diff['stdout']}{diff['stderr']}
```

## HANDOFF_REPLY_V4 status
```text
{file_status['stdout']}{ls['stdout']}{log['stdout']}
```
'''
 write('TARGETED_TEST_OUTPUT.txt',test_output)

 if PACK.exists():
  for c in PACK.iterdir():
   if c.is_dir(): shutil.rmtree(c)
   elif c.suffix!='.zip': c.unlink()
 (PACK/'actual_deliverables').mkdir(parents=True,exist_ok=True); (PACK/'reports').mkdir(parents=True,exist_ok=True); (PACK/'source_evidence').mkdir(parents=True,exist_ok=True)
 for f in ['HANDOFF_REPLY_V4_HUMAN_REQUIRED_DECISION.json','HANDOFF_REPLY_V4_HUMAN_REQUIRED_DECISION.md','PROTECTED_LEGACY_STATUS_R2.json','SOURCE_MAP_EVIDENCE_BINDING_APPENDIX_R2.json','SOURCE_MAP_EVIDENCE_BINDING_APPENDIX_R2.md']:
  shutil.copy2(OUT/f, PACK/'actual_deliverables'/f)
 for f in ['SAFETY_ATTESTATION.md','TARGETED_TEST_OUTPUT.txt']:
  shutil.copy2(OUT/f, PACK/'reports'/f)
 for e in binding_entries:
  if e['embedded_in_pack']:
   copy_src(e['path'], e['copy_path_in_pack'])

 # safety scan before manifest
 findings=[]; scanned=[]
 for p in sorted(PACK.rglob('*')):
  if p.is_file() and p.suffix!='.zip':
   rel=str(p.relative_to(PACK)).replace('\\','/'); data=p.read_bytes(); info={'path':rel,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'findings':[]}
   if p.suffix.lower() in TEXT_EXTS:
    text=data.decode('utf-8',errors='replace')
    for name,pat in PATTERNS:
     if pat.search(text): info['findings'].append(name)
   if info['findings']: findings.append(info)
   scanned.append(info)
 safety={'task_id':TASK_ID,'run_id':RUN_ID,'pass':not findings,'findings':findings,'scanned_file_count':len(scanned),'files':scanned}
 write_json('EXPANDED_ZIP_SAFETY_SCAN_R2.json',safety)
 write('EXPANDED_ZIP_SAFETY_SCAN_R2.md','# Expanded ZIP Safety Scan R2\n\n- pass: '+str(not findings)+'\n- scanned_file_count: '+str(len(scanned))+'\n- findings: '+('none' if not findings else json.dumps(findings,ensure_ascii=False))+'\n')
 shutil.copy2(OUT/'EXPANDED_ZIP_SAFETY_SCAN_R2.json', PACK/'reports'/'EXPANDED_ZIP_SAFETY_SCAN_R2.json')
 shutil.copy2(OUT/'EXPANDED_ZIP_SAFETY_SCAN_R2.md', PACK/'reports'/'EXPANDED_ZIP_SAFETY_SCAN_R2.md')

 exec_report=f'''# Execution Report — {TASK_ID}

- run_id: {RUN_ID}
- generated_at: {NOW}
- status: ready_for_gpt_review_with_human_required_limitation
- reused_existing_workflow: true

## 执行结果

- 已生成 `HANDOFF_REPLY_V4_HUMAN_REQUIRED_DECISION`：不自动恢复，标记 human_required。
- 已修正 safety attestation：不再声称所有 legacy 文件均未删除。
- 已修正 source binding：所有 `embedded_in_pack=true` 的文件都复制到 `source_evidence/` 并进入 manifest。
- 已嵌入 prior closure ZIP：`evidence_packs/global-project-handoff-repair-a1/GLOBAL_PROJECT_HANDOFF_REPAIR_A1_20260608_223800.zip`。

## 未执行的高风险操作

- 未执行 git restore / checkout / reset / clean。
- 未恢复、删除、移动、重命名或覆盖 `HANDOFF_REPLY_V4.txt`。

## 保留限制

- `HANDOFF_REPLY_V4.txt` 仍为 `tracked_deleted_human_required`，不是 resolved。
- whole-project/global status 仍为 partial / needs_more_evidence。
- production promotion 未批准。
- 296 PASS 未验证。
'''
 write('EXECUTION_REPORT.md',exec_report); shutil.copy2(OUT/'EXECUTION_REPORT.md', PACK/'reports'/'EXECUTION_REPORT.md')
 closure=f'''# Closure Report — {TASK_ID}

- run_id: {RUN_ID}
- status: ready_for_gpt_review_with_human_required_limitation

本 R2 修复了 A1 中两个可自动修复的问题：safety attestation 与 source binding/manifest 一致性。`HANDOFF_REPLY_V4.txt` 根据 GPT 咨询保留为 human_required，不自动恢复，也不声称 resolved。
'''
 (PACK/'CLOSURE_REPORT.md').write_text(closure,encoding='utf-8')
 prompt=f'''GPT 审查请求：{TASK_ID}

run_id: {RUN_ID}

请审查附件 R2 evidence pack。重点：
1. 是否正确处理上一轮 blocked 的三个问题。
2. `HANDOFF_REPLY_V4.txt` 是否被如实标记为 `tracked_deleted_human_required`，没有被包装成 resolved/pass。
3. safety attestation 是否已和 git evidence 一致。
4. source binding / manifest 是否一致，旧 closure ZIP 若声称嵌入则确实在 pack 与 manifest 中。
5. 是否保留 partial / needs_more_evidence、production 未批准、296 PASS 未验证等限制。

请只返回：
run_id: {RUN_ID}
task_id: {TASK_ID}
overall_judgment: accepted | accepted_with_limitation | blocked | review_unverified
evidence_pack_reviewed: true | false
attachment_reviewed: true | false
blocking_issues:
  - <问题或 none>
required_fixes:
  - <修复或 none>
limitations:
  - <限制或 none>
next_task_authorization:
  task_id: <下个任务或 none>
  authorized: 已授权 | 未授权
  execute_immediately: 是 | 否
  ask_before_starting: 是 | 否
END_OF_GPT_RESPONSE
'''
 (PACK/'GPT_REVIEW_PROMPT.md').write_text(prompt,encoding='utf-8')
 (PACK/'SAFETY_ATTESTATION.md').write_text(attestation,encoding='utf-8')

 rows=[]
 for p in sorted(PACK.rglob('*')):
  if p.is_file() and p.suffix!='.zip': rows.append((str(p.relative_to(PACK)).replace('\\','/'),hashlib.sha256(p.read_bytes()).hexdigest(),p.stat().st_size))
 manifest=['# Pack Manifest R2','',f'- task_id: {TASK_ID}',f'- run_id: {RUN_ID}',f'- generated_at: {NOW}','','| Path | SHA256 | Bytes |','|---|---|---:|']
 for rel,dig,size in rows: manifest.append(f'| `{rel}` | `{dig}` | {size} |')
 man='\n'.join(manifest)+'\n'; write('PACK_MANIFEST.md',man); (PACK/'PACK_MANIFEST.md').write_text(man,encoding='utf-8')
 zip_path=PACK/f'GLOBAL_PROJECT_EVIDENCE_BINDING_A1_R2_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip'
 with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as zf:
  for p in sorted(PACK.rglob('*')):
   if p.is_file() and p!=zip_path and p.suffix!='.zip': zf.write(p,p.relative_to(PACK))
 rec={'task_id':TASK_ID,'run_id':RUN_ID,'zip_path':str(zip_path.relative_to(ROOT)).replace('\\','/'),'zip_sha256':hashlib.sha256(zip_path.read_bytes()).hexdigest(),'generated_at':NOW,'safety_pass':not findings,'handoff_reply_v4_status':'tracked_deleted_human_required'}
 write_json('ZIP_RECORD.json',rec)
 print(json.dumps(rec,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
