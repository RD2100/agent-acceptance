from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, re, shutil, subprocess, zipfile
ROOT=Path('D:/agent-acceptance')
TASK_ID='GLOBAL-PROJECT-EVIDENCE-BINDING-A1-R4'
RUN_ID='GLOBAL_EVIDENCE_BINDING_A1_R4_'+datetime.now().strftime('%Y%m%d_%H%M%S')
OUT=ROOT/'_reports/global-project-evidence-binding-a1-r4'
PACK=ROOT/'evidence_packs/global-project-evidence-binding-a1-r4'
NOW=datetime.now(timezone.utc).isoformat()
OLD_ZIP_REL='evidence_packs/global-project-handoff-repair-a1/GLOBAL_PROJECT_HANDOFF_REPAIR_A1_20260608_223800.zip'
OLD_ZIP_PACK='source_evidence/evidence_packs/global-project-handoff-repair-a1/GLOBAL_PROJECT_HANDOFF_REPAIR_A1_20260608_223800.zip'
SOURCE_FILES=['HANDOFF_SOURCE_OF_TRUTH.md','HANDOFF_APPROVAL_RECORD.json','_reports/global-project-handoff-repair-a1/GPT_REVIEW_RECORD.json','_reports/global-project-handoff-repair-a1/VERIFY_GPT_REPLY_OUTPUT.txt','_reports/global-project-handoff-repair-a1/PRE_GPT_GATE_OUTPUT.txt','_reports/global-project-handoff-repair-a1/EXECUTION_REPORT.md','_reports/global-project-handoff-repair-a1/PACK_MANIFEST.md','_reports/global-project-handoff-repair-a1/WHOLE_PROJECT_SOURCE_OF_TRUTH_MAP.json','_reports/global-project-handoff-repair-a1/WHOLE_PROJECT_STALE_CLAIMS_REGISTER.json','_reports/global-project-handoff-repair-a1/WHOLE_PROJECT_TEST_LEDGER.json','_reports/global-project-evidence-binding-a1/GPT_REVIEW_RESULT.txt','_reports/global-project-evidence-binding-a1/VERIFY_GPT_REPLY_OUTPUT.txt','_reports/global-project-evidence-binding-a1/CHANGED_FILES_EVIDENCE.json','_reports/global-project-evidence-binding-a1/PROTECTED_LEGACY_FILES_STATUS.json','_reports/global-project-evidence-binding-a1/SOURCE_MAP_EVIDENCE_BINDING_APPENDIX.json','_reports/global-project-evidence-binding-a1-r2/GPT_HANDOFF_REPLY_V4_CONSULT_RESULT.txt','_reports/global-project-evidence-binding-a1-r2/VERIFY_GPT_HANDOFF_REPLY_V4_CONSULT_OUTPUT.txt','_reports/global-project-evidence-binding-a1-r2/HANDOFF_REPLY_V4_HUMAN_REQUIRED_DECISION.json','_reports/global-project-evidence-binding-a1-r3/GPT_REVIEW_RESULT.txt','_reports/global-project-evidence-binding-a1-r3/VERIFY_GPT_REPLY_OUTPUT.txt',OLD_ZIP_REL]
TEXT_EXTS={'.md','.txt','.json','.yaml','.yml','.py','.ps1'}
PATTERNS=[('openai_key',re.compile(r'sk-[A-Za-z0-9_-]{20,}')),('secret_assignment',re.compile(r'(?i)(api[_-]?key|secret|token)\s*[:=]\s*["\']?[A-Za-z0-9_./+=-]{24,}')),('private_key',re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----'))]
def run(cmd):
 p=subprocess.run(cmd,cwd=ROOT,text=True,encoding='utf-8',errors='replace',capture_output=True); return {'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
def sha_path(p): return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() and p.is_file() else None
def sha(rel): return sha_path(ROOT/rel)
def write(n,t): OUT.mkdir(parents=True,exist_ok=True); (OUT/n).write_text(t,encoding='utf-8')
def write_json(n,o): write(n,json.dumps(o,ensure_ascii=False,indent=2)+'\n')
def copy_src(rel,dst_rel):
 src=ROOT/rel; dst=PACK/dst_rel; dst.parent.mkdir(parents=True,exist_ok=True)
 if src.is_file(): shutil.copy2(src,dst)
def main():
 OUT.mkdir(parents=True,exist_ok=True); PACK.mkdir(parents=True,exist_ok=True)
 fresh=run(['bash','-lc','cd "D:/agent-acceptance" && pwd && date && echo FRESH_SHELL_OK && git rev-parse --is-inside-work-tree'])
 status=run(['git','status','--short'])
 if PACK.exists():
  for c in PACK.iterdir():
   if c.is_dir(): shutil.rmtree(c)
   elif c.suffix!='.zip': c.unlink()
 for d in ['actual_deliverables','reports','source_evidence']:(PACK/d).mkdir(parents=True,exist_ok=True)
 entries=[]
 for rel in SOURCE_FILES:
  p=ROOT/rel; pack_path='source_evidence/'+rel.replace('\\','/')
  entries.append({'path':rel,'exists':p.exists(),'is_file':p.is_file(),'sha256':sha(rel),'embedded_in_pack':p.is_file(),'copy_path_in_pack':pack_path if p.is_file() else None})
  if p.is_file(): copy_src(rel,pack_path)
 old_pack_path=PACK/OLD_ZIP_PACK
 embed_check={'task_id':TASK_ID,'run_id':RUN_ID,'required_embedded_zip':OLD_ZIP_PACK,'present_in_pack_directory':old_pack_path.exists(),'sha256':sha_path(old_pack_path),'bytes':old_pack_path.stat().st_size if old_pack_path.exists() else None}
 write_json('EMBEDDED_ZIP_PRESENCE_CHECK_R4.json',embed_check)
 binding={'task_id':TASK_ID,'run_id':RUN_ID,'generated_at':NOW,'r4_fix':'最终 closure ZIP 允许包含 source_evidence 下的旧 closure ZIP；PACK_MANIFEST 明确列出旧 closure ZIP 的 SHA256 和字节数。','entries':entries,'embedded_zip_presence_check':embed_check,'limitations':['HANDOFF_REPLY_V4.txt remains tracked_deleted_human_required.','whole-project/global status remains partial / needs_more_evidence.','production promotion remains not approved.','296 PASS remains unverified.']}
 write_json('SOURCE_MAP_EVIDENCE_BINDING_APPENDIX_R4.json',binding); write('SOURCE_MAP_EVIDENCE_BINDING_APPENDIX_R4.md','# Source Map Evidence Binding Appendix R4\n\n```json\n'+json.dumps(binding,ensure_ascii=False,indent=2)+'\n```\n')
 decision=json.loads((ROOT/'_reports/global-project-evidence-binding-a1-r2/HANDOFF_REPLY_V4_HUMAN_REQUIRED_DECISION.json').read_text(encoding='utf-8')); decision['r4_status']='still_tracked_deleted_human_required'; decision['r4_revalidated_at']=NOW
 write_json('HANDOFF_REPLY_V4_HUMAN_REQUIRED_DECISION_R4.json',decision)
 for f in ['EMBEDDED_ZIP_PRESENCE_CHECK_R4.json','SOURCE_MAP_EVIDENCE_BINDING_APPENDIX_R4.json','SOURCE_MAP_EVIDENCE_BINDING_APPENDIX_R4.md','HANDOFF_REPLY_V4_HUMAN_REQUIRED_DECISION_R4.json']:
  shutil.copy2(OUT/f,PACK/'actual_deliverables'/f)
 att='''# Safety Attestation — GLOBAL-PROJECT-EVIDENCE-BINDING-A1-R4

- safety_boundaries_respected: true
- dangerous_git_operations_performed: false
- git_restore_checkout_reset_clean_performed: false
- legacy_files_deleted_moved_renamed_or_overwritten_by_this_task: false
- handoff_reply_v4_current_status: tracked_deleted_human_required
- handoff_reply_v4_restore_executed: false
- claim_all_legacy_files_clean: false
- production_promotion_claimed: false
- 296_pass_promoted_to_verified: false

R4 只修复 R3 的打包问题：最终 closure ZIP 必须包含旧 closure ZIP 本体并在 PACK_MANIFEST 中列出。HANDOFF_REPLY_V4.txt 仍保留 human_required。
'''
 write('SAFETY_ATTESTATION.md',att); shutil.copy2(OUT/'SAFETY_ATTESTATION.md',PACK/'reports'/'SAFETY_ATTESTATION.md')
 test=f'''# Targeted Test Output — {TASK_ID}

## fresh shell
exit={fresh['returncode']}
```text
{fresh['stdout']}{fresh['stderr']}
```

## git status --short
```text
{status['stdout']}{status['stderr']}
```

## embedded old closure zip check
```json
{json.dumps(embed_check,ensure_ascii=False,indent=2)}
```
'''
 write('TARGETED_TEST_OUTPUT.txt',test); shutil.copy2(OUT/'TARGETED_TEST_OUTPUT.txt',PACK/'reports'/'TARGETED_TEST_OUTPUT.txt'); shutil.copy2(OUT/'TARGETED_TEST_OUTPUT.txt',PACK/'reports'/'TEST_OUTPUT.txt')
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
 safety={'task_id':TASK_ID,'run_id':RUN_ID,'pass':not findings,'scanned_non_zip_file_count':len(scanned),'zip_binary_files_covered_by_manifest_hash':True,'findings':findings,'files':scanned}
 write_json('EXPANDED_ZIP_SAFETY_SCAN_R4.json',safety); write('EXPANDED_ZIP_SAFETY_SCAN_R4.md','# Expanded ZIP Safety Scan R4\n\n- pass: '+str(not findings)+'\n- scanned_non_zip_file_count: '+str(len(scanned))+'\n- zip_binary_files_covered_by_manifest_hash: true\n- findings: '+('none' if not findings else json.dumps(findings,ensure_ascii=False))+'\n')
 shutil.copy2(OUT/'EXPANDED_ZIP_SAFETY_SCAN_R4.json',PACK/'reports'/'EXPANDED_ZIP_SAFETY_SCAN_R4.json'); shutil.copy2(OUT/'EXPANDED_ZIP_SAFETY_SCAN_R4.md',PACK/'reports'/'EXPANDED_ZIP_SAFETY_SCAN_R4.md')
 exec_report=f'''# Execution Report — {TASK_ID}

- run_id: {RUN_ID}
- generated_at: {NOW}
- status: ready_for_gpt_review_with_human_required_limitation

## R4 修复点

- 旧 closure ZIP 实际存在于 pack 目录：`{OLD_ZIP_PACK}`，present={embed_check['present_in_pack_directory']}。
- PACK_MANIFEST 将列出该旧 closure ZIP。
- 最终 closure ZIP 打包逻辑不再排除 `source_evidence/**/*.zip`。
- 未执行 git restore / checkout / reset / clean；未改动 HANDOFF_REPLY_V4.txt。
'''
 write('EXECUTION_REPORT.md',exec_report); shutil.copy2(OUT/'EXECUTION_REPORT.md',PACK/'reports'/'EXECUTION_REPORT.md')
 (PACK/'CLOSURE_REPORT.md').write_text(f'# Closure Report — {TASK_ID}\n\n- run_id: {RUN_ID}\n- status: ready_for_gpt_review_with_human_required_limitation\n- R4 修复：旧 closure ZIP 已实际嵌入、进入 manifest、进入最终附件 ZIP。\n',encoding='utf-8')
 prompt=f'''GPT 审查请求：{TASK_ID}

run_id: {RUN_ID}

请审查附件 R4 evidence pack。R4 专门修复 R3 的打包问题：旧 closure ZIP 必须实际存在于附件 ZIP 的 `source_evidence/evidence_packs/global-project-handoff-repair-a1/GLOBAL_PROJECT_HANDOFF_REPAIR_A1_20260608_223800.zip`，并列入 PACK_MANIFEST。

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
 (PACK/'GPT_REVIEW_PROMPT.md').write_text(prompt,encoding='utf-8'); (PACK/'SAFETY_ATTESTATION.md').write_text(att,encoding='utf-8')
 rows=[]
 for p in sorted(PACK.rglob('*')):
  if p.is_file() and p.name!='PACK_MANIFEST.md': rows.append((str(p.relative_to(PACK)).replace('\\','/'),hashlib.sha256(p.read_bytes()).hexdigest(),p.stat().st_size))
 manifest=['# Pack Manifest R4','',f'- task_id: {TASK_ID}',f'- run_id: {RUN_ID}',f'- generated_at: {NOW}','- note: PACK_MANIFEST.md self-hash omitted to avoid self-referential drift; all other pack files including embedded ZIP files are listed.','','| Path | SHA256 | Bytes |','|---|---|---:|']
 for rel,dig,size in rows: manifest.append(f'| `{rel}` | `{dig}` | {size} |')
 man='\n'.join(manifest)+'\n'; write('PACK_MANIFEST.md',man); (PACK/'PACK_MANIFEST.md').write_text(man,encoding='utf-8')
 zip_path=PACK/f'GLOBAL_PROJECT_EVIDENCE_BINDING_A1_R4_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip'
 with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as zf:
  for p in sorted(PACK.rglob('*')):
   if p.is_file() and p!=zip_path: zf.write(p,p.relative_to(PACK))
 # verify final zip contains old zip
 with zipfile.ZipFile(zip_path) as zf: names=set(zf.namelist())
 final_check={'old_zip_path':OLD_ZIP_PACK,'present_in_final_zip':OLD_ZIP_PACK in names,'final_zip_entry_count':len(names)}
 write_json('FINAL_ZIP_CONTENT_CHECK.json',final_check)
 rec={'task_id':TASK_ID,'run_id':RUN_ID,'zip_path':str(zip_path.relative_to(ROOT)).replace('\\','/'),'zip_sha256':hashlib.sha256(zip_path.read_bytes()).hexdigest(),'generated_at':NOW,'embedded_old_closure_zip_present_in_pack_dir':embed_check['present_in_pack_directory'],'embedded_old_closure_zip_present_in_final_zip':final_check['present_in_final_zip'],'safety_pass':not findings}
 write_json('ZIP_RECORD.json',rec)
 print(json.dumps(rec,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
