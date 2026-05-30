<#
.SYNOPSIS
Secret check: invokes ai_guard.py and parses its output.
Does NOT re-implement secret scanning rules. Exit code mapping:
  ai_guard 0 → PASS, 1 → BLOCKED, 2 → INFRA_ERROR, other → INFRA_ERROR
#>
param(
    [string]$Mode = "staged",
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
)

Import-Module (Join-Path $PSScriptRoot "shared\GovernanceShared.psm1") -Force
Import-Module (Join-Path $PSScriptRoot "..\lib\Process.psm1") -Force

$aiGuardPath = Join-Path $ProjectRoot "tools\ai_guard.py"
if (-not (Test-Path $aiGuardPath)) {
    return New-CheckResult -CheckName "Secrets" -Status "INFRA_ERROR" `
        -Details @("ai_guard.py not found at $aiGuardPath") `
        -Suggestion "Ensure tools/ai_guard.py exists."
}

$tmpDir = Join-Path $env:TEMP "test-secrets-$([Guid]::NewGuid().ToString('N').Substring(0,8))"
New-Item -ItemType Directory -Force -Path $tmpDir | Out-Null

$result = Invoke-CheckedNative `
    -FilePath "python" `
    -ArgumentList @($aiGuardPath, $Mode) `
    -WorkingDirectory $ProjectRoot `
    -TimeoutSeconds 60

switch ($result.ExitCode) {
    0 {
        return New-CheckResult -CheckName "Secrets" -Status "PASS" -Details @("ai_guard.py: no secrets found")
    }
    1 {
        return New-CheckResult -CheckName "Secrets" -Status "BLOCKED" `
            -Details @("ai_guard.py: secret pattern(s) detected") `
            -Suggestion "Remove or rotate secrets before committing."
    }
    default {
        return New-CheckResult -CheckName "Secrets" -Status "INFRA_ERROR" `
            -Details @("ai_guard.py returned exit $($result.ExitCode) or timed out") `
            -Suggestion "Check ai_guard.py configuration and .ai/policy.yaml."
    }
}
