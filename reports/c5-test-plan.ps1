
# Batch C5: Bootstrap Acceptance Tests
# Run: powershell -ExecutionPolicy Bypass -File D:\agent-acceptance\reports\c5-test-plan.ps1

$results = @()
$ErrorActionPreference = "Continue"

# === TEST-01: Fresh Project (11 checks) ===
$d = "$env:TEMP\c5-test-01"; ri -Recurse -Force $d -EA SilentlyContinue *>$null; ni -ItemType Dir -Force -Path $d *>$null; Set-Location $d
powershell -EP Bypass -File D:\agent-acceptance\templates\runtime-bootstrap\bootstrap.ps1 -ProjectName happy-path -ProjectRoot $d -Force *>$null
$c = @((Test-Path "$d\AGENTS.md"),(Test-Path "$d\rules\core.md"),(Test-Path "$d\schemas"),(Test-Path "$d\docs\agent-runtime\capability-inventory.md"),(Test-Path "$d\docs\agent-runtime\tool-policy.md"),(Test-Path "$d\docs\agent-runtime\reviewer-playbook.md"),(Test-Path "$d\docs\agent-runtime\negative-test-fixtures"),((gci "$d\rules\*.md").Count -eq 8),((gci -Recurse "$d\schemas\*.json").Count -ge 18),((sls -Path "$d\docs\agent-runtime\capability-inventory.md" -Pattern "^## \d+\.").Count -eq 10),(-not (sls -Path "$d\AGENTS.md" -Pattern "\{\{" -SimpleMatch -Quiet)))
$p = ($c | ? { $_ }).Count; $t = $c.Count; $r = if($p -eq $t){"PASS"}else{"FAIL"}
Write-Output "TEST-01: $r - $p/$t checks"; $results += "TEST-01: $r"
ri -Recurse -Force $d -EA SilentlyContinue *>$null

# === TEST-02: Dry-Run ===
$d = "$env:TEMP\c5-test-02"; ri -Recurse -Force $d -EA SilentlyContinue *>$null; ni -ItemType Dir -Force -Path $d *>$null
powershell -EP Bypass -File D:\agent-acceptance\templates\runtime-bootstrap\bootstrap.ps1 -ProjectName dry-run -ProjectRoot $d -DryRun *>$null
$fe = Test-Path "$d\AGENTS.md"; $re = Test-Path "$d\rules"
$r = if(-not $fe -and -not $re){"PASS"}else{"FAIL"}
Write-Output "TEST-02: $r"; $results += "TEST-02: $r"
ri -Recurse -Force $d -EA SilentlyContinue *>$null

# === TEST-03: Force Overwrite ===
$d = "$env:TEMP\c5-test-03"; ri -Recurse -Force $d -EA SilentlyContinue *>$null; ni -ItemType Dir -Force -Path $d *>$null
powershell -EP Bypass -File D:\agent-acceptance\templates\runtime-bootstrap\bootstrap.ps1 -ProjectName first -ProjectRoot $d -Force *>$null
"MODIFIED" | Set-Content "$d\AGENTS.md"
powershell -EP Bypass -File D:\agent-acceptance\templates\runtime-bootstrap\bootstrap.ps1 -ProjectName overwritten -ProjectRoot $d -Force *>$null
$sn = (Get-Content "$d\AGENTS.md" -Raw | sls "# AGENTS.md -- (.+)" | % { $_.Matches.Groups[1].Value })
$r = if($sn -eq "overwritten"){"PASS"}else{"FAIL"}
Write-Output "TEST-03: $r - name=$sn"; $results += "TEST-03: $r"
ri -Recurse -Force $d -EA SilentlyContinue *>$null

# === TEST-04: Skip Without Force ===
$d = \"$env:TEMP\c5-test-04\"; ri -Recurse -Force $d -EA SilentlyContinue *>$null; ni -ItemType Dir -Force -Path $d *>$null
powershell -EP Bypass -File D:\agent-acceptance\templates\runtime-bootstrap\bootstrap.ps1 -ProjectName first -ProjectRoot $d -Force *>$null
$f1 = Get-Content \"$d\AGENTS.md\" -Raw
$out = powershell -EP Bypass -File D:\agent-acceptance\templates\runtime-bootstrap\bootstrap.ps1 -ProjectName second -ProjectRoot $d 2>&1
$f2 = Get-Content \"$d\AGENTS.md\" -Raw; $sk = $out | sls SKIP
$r = if($f1 -eq $f2 -and $sk){\"PASS\"}else{\"FAIL\"}
Write-Output \"TEST-04: $r\"; $results += \"TEST-04: $r\"
ri -Recurse -Force $d -EA SilentlyContinue *>$null

# === TEST-05: Auto-Detect Dir Name ===
$d = \"$env:TEMP\c5-test-05-my-cool-app\"; ri -Recurse -Force $d -EA SilentlyContinue *>$null; ni -ItemType Dir -Force -Path $d *>$null; Set-Location $d
git init 2>$null *>$null
powershell -EP Bypass -File D:\agent-acceptance\templates\runtime-bootstrap\bootstrap.ps1 -ProjectRoot $d -Force *>$null
$det = (Get-Content \"$d\AGENTS.md\" -Raw | sls \"# AGENTS.md -- (.+)\" | % { $_.Matches.Groups[1].Value })
$r = if($det -eq \"c5-test-05-my-cool-app\"){\"PASS\"}else{\"FAIL\"}
Write-Output \"TEST-05: $r - detected=$det\"; $results += \"TEST-05: $r\"
ri -Recurse -Force $d -EA SilentlyContinue *>$null

# === TEST-06: Auto-Detect Git Remote ===
$d = \"$env:TEMP\c5-test-06\"; ri -Recurse -Force $d -EA SilentlyContinue *>$null; ni -ItemType Dir -Force -Path $d *>$null; Set-Location $d
git init 2>$null *>$null; git remote add origin https://github.com/example/git-detected-project.git 2>$null *>$null
powershell -EP Bypass -File D:\agent-acceptance\templates\runtime-bootstrap\bootstrap.ps1 -ProjectRoot $d -Force *>$null
$det = (Get-Content \"$d\AGENTS.md\" -Raw | sls \"# AGENTS.md -- (.+)\" | % { $_.Matches.Groups[1].Value })
$r = if($det -eq \"git-detected-project\"){\"PASS\"}else{\"FAIL\"}
Write-Output \"TEST-06: $r - detected=$det\"; $results += \"TEST-06: $r\"
ri -Recurse -Force $d -EA SilentlyContinue *>$null