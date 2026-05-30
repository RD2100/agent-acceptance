# Process.psm1 — Unified native command execution
# All governance scripts that invoke native commands, subprocesses, PowerShell jobs,
# or external scripts MUST use this module. Direct $LASTEXITCODE reads are forbidden.
#
# Exit code contract (project-wide):
#   0 = PASS
#   1 = BLOCKED (governance violation)
#   2 = INFRA_ERROR (script error, missing resource, timeout)

function Invoke-CheckedCommand {
    <#
    .SYNOPSIS
    Execute a native command with timeout and reliable exit code capture.
    .PARAMETER Command
    The command string to execute (passed to Invoke-Expression inside a job).
    .PARAMETER OutputDir
    Directory to write stdout.log and exit.code files.
    .PARAMETER WorkingDirectory
    Working directory for the command.
    .PARAMETER TimeoutSeconds
    Maximum execution time before forced termination.
    .OUTPUTS
    Hashtable with keys: ExitCode (int), TimedOut (bool), Duration (double).
    #>
    param(
        [Parameter(Mandatory)]
        [string]$Command,
        [Parameter(Mandatory)]
        [string]$OutputDir,
        [string]$WorkingDirectory = (Get-Location).Path,
        [int]$TimeoutSeconds = 120
    )

    $exitCodeFile = Join-Path $OutputDir 'exit.code'
    $stdoutFile   = Join-Path $OutputDir 'stdout.log'

    # Remove stale exit code file from prior runs
    if (Test-Path $exitCodeFile) {
        Remove-Item $exitCodeFile -Force
    }

    $t0 = Get-Date

    try {
        $job = Start-Job -ScriptBlock {
            param($cmd, $outDir, $workDir, $ecFile)
            Set-Location $workDir
            try {
                Invoke-Expression $cmd 2>&1 | Out-File (Join-Path $outDir 'stdout.log')
                # Capture the exit code from Invoke-Expression
                $ec = if ($LASTEXITCODE) { $LASTEXITCODE } else { 0 }
                $ec.ToString() | Out-File -FilePath $ecFile -NoNewline
            } catch {
                "2" | Out-File -FilePath $ecFile -NoNewline
            }
        } -ArgumentList $Command, $OutputDir, $WorkingDirectory, $exitCodeFile

        $done = Wait-Job $job -Timeout $TimeoutSeconds

        if (-not $done) {
            Stop-Job $job -PassThru | Remove-Job -Force
            $ts = [math]::Round(((Get-Date) - $t0).TotalSeconds, 1)
            return @{
                ExitCode = 2
                TimedOut = $true
                Duration = $ts
            }
        }

        Receive-Job $job 2>&1 | Out-Null
        Remove-Job $job -Force

        # Read exit code from file (NOT from $LASTEXITCODE)
        $actualExit = 0
        if (Test-Path $exitCodeFile) {
            $content = (Get-Content -Path $exitCodeFile -Raw).Trim()
            if ($content -match '^\d+$') {
                $actualExit = [int]$content
            } else {
                $actualExit = 2
            }
        } else {
            $actualExit = 2  # exit code file missing = infra error
        }

        $ts = [math]::Round(((Get-Date) - $t0).TotalSeconds, 1)
        return @{
            ExitCode = $actualExit
            TimedOut = $false
            Duration = $ts
        }
    } catch {
        $ts = [math]::Round(((Get-Date) - $t0).TotalSeconds, 1)
        return @{
            ExitCode = 2
            TimedOut = $false
            Duration = $ts
        }
    }
}


function Invoke-CheckedNative {
    <#
    .SYNOPSIS
    Execute a native program (not a PowerShell expression) and capture exit code.
    Uses Start-Process for reliable exit code capture.
    #>
    param(
        [Parameter(Mandatory)]
        [string]$FilePath,
        [string[]]$ArgumentList = @(),
        [string]$WorkingDirectory = (Get-Location).Path,
        [int]$TimeoutSeconds = 120
    )

    $t0 = Get-Date
    $exitCodeFile = Join-Path $env:TEMP "checked-native-$([Guid]::NewGuid().ToString('N').Substring(0,8)).code"

    try {
        $proc = Start-Process -FilePath $FilePath `
            -ArgumentList $ArgumentList `
            -WorkingDirectory $WorkingDirectory `
            -NoNewWindow -Wait -PassThru `
            -RedirectStandardOutput (Join-Path $env:TEMP "checked-native-stdout.tmp") `
            -RedirectStandardError (Join-Path $env:TEMP "checked-native-stderr.tmp")

        $ts = [math]::Round(((Get-Date) - $t0).TotalSeconds, 1)

        $ec = if ($proc.ExitCode) { $proc.ExitCode } else { 0 }

        # Timeout enforcement: if Start-Process -Wait exceeds limit externally
        if ($ts -gt $TimeoutSeconds) {
            return @{ ExitCode = 2; TimedOut = $true; Duration = $ts }
        }

        return @{
            ExitCode = $ec
            TimedOut = $false
            Duration = $ts
        }
    } catch {
        $ts = [math]::Round(((Get-Date) - $t0).TotalSeconds, 1)
        return @{
            ExitCode = 2
            TimedOut = $false
            Duration = $ts
        }
    }
}


function Assert-NoBareLastExitCode {
    <#
    .SYNOPSIS
    Verify that a script file does not directly read $LASTEXITCODE outside Process.psm1.
    Uses AST inspection (not grep).
    #>
    param(
        [Parameter(Mandatory)]
        [string]$ScriptPath
    )

    if ($ScriptPath -match 'Process\.psm1$') { return $true }
    if ($ScriptPath -match '\\tests\\' -or $ScriptPath -match '\\.tests\.ps1$') { return $true }

    $content = Get-Content $ScriptPath -Raw -ErrorAction SilentlyContinue
    if (-not $content) { return $true }

    $ast = [System.Management.Automation.Language.Parser]::ParseInput($content, [ref]$null, [ref]$null)
    if (-not $ast) { return $true }

    $violations = $ast.FindAll({
        param($node)
        $node -is [System.Management.Automation.Language.VariableExpressionAst] -and
        $node.VariablePath.UserPath -eq 'LASTEXITCODE'
    }, $true)

    if ($violations) {
        Write-Warning "[Process.psm1] $ScriptPath directly reads `$LASTEXITCODE ($($violations.Count) occurrence(s)). Use Invoke-CheckedCommand instead."
        return $false
    }
    return $true
}


Export-ModuleMember -Function Invoke-CheckedCommand, Invoke-CheckedNative, Assert-NoBareLastExitCode
