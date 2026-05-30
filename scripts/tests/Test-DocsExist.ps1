<#
.SYNOPSIS
Verify that core governance documents exist. Used by batch-smoke.json.
Exit: 0=PASS (4+ docs exist), 2=FAILED (<4 docs exist)
#>
$files = @(
    'AGENTS.md',
    'rules/core.md',
    'rules/security.md',
    'docs/agent-runtime/operating-model.md',
    'docs/agent-runtime/capability-inventory.md'
)
$ok = 0
foreach ($f in $files) {
    if (Test-Path $f) { $ok++ }
}
Write-Host "$ok/$($files.Count) docs exist"
if ($ok -ge 4) { exit 0 } else { exit 2 }
