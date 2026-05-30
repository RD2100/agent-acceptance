# GovernanceShared.psm1 — Pure function parsers shared by Test-Governance and Test-GovernanceDrift.
# NO orchestrator logic, NO I/O side effects, NO CI exit code logic.
# Only stateless parsers and resolvers.

function Get-ProjectRoot {
    <#
    .SYNOPSIS
    Return the project root directory (parent of scripts/).
    #>
    return (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
}

function Resolve-ExpectedFiles {
    <#
    .SYNOPSIS
    Expand expected-files.txt glob patterns via Get-ChildItem -Recurse.
    Returns array of resolved file paths relative to ProjectRoot.
    #>
    param(
        [Parameter(Mandatory)]
        [string]$ExpectedFilesPath,
        [Parameter(Mandatory)]
        [string]$ProjectRoot
    )
    if (-not (Test-Path $ExpectedFilesPath)) { return @() }

    $results = @()
    $lines = Get-Content $ExpectedFilesPath | Where-Object { $_ -notmatch '^\s*(#|$)' }
    foreach ($line in $lines) {
        $pattern = $line.Trim()
        # Convert glob pattern to Get-ChildItem arguments
        $dir = Split-Path $pattern -Parent
        $name = Split-Path $pattern -Leaf
        $fullDir = Join-Path $ProjectRoot $dir
        if (Test-Path $fullDir) {
            $matches = Get-ChildItem -Path $fullDir -Filter $name -Recurse -File -ErrorAction SilentlyContinue
            foreach ($m in $matches) {
                $relPath = $m.FullName.Substring($ProjectRoot.Length + 1) -replace '\\', '/'
                $results += $relPath
            }
        }
    }
    # Apply manifest-ignore.txt filtering
    $ignorePath = Join-Path $ProjectRoot "governance\manifest-ignore.txt"
    if (Test-Path $ignorePath) {
        $ignorePatterns = Get-Content $ignorePath | Where-Object { $_ -notmatch '^\s*(#|$)' } | ForEach-Object { $_.Trim() }
        $results = $results | Where-Object {
            $keep = $true
            foreach ($ip in $ignorePatterns) {
                $wc = $ip -replace '\*\*/', '*' -replace '/', '/'
                if ($_ -like $wc) { $keep = $false; break }
            }
            $keep
        }
    }

    return $results | Sort-Object -Unique
}

function Parse-RuleIds {
    <#
    .SYNOPSIS
    Extract rule IDs and priorities from a rules/*.md file.
    Returns hashtable: { id, priority, file }.
    #>
    param([Parameter(Mandatory)]$FilePath)
    if (-not (Test-Path $FilePath)) { return @() }

    $results = @()
    $content = Get-Content $FilePath -Raw
    $lines = $content -split "`n"

    for ($i = 0; $i -lt $lines.Count; $i++) {
        # Match "## RULE core-001: ..." or "### core-001: ..." style headers
        if ($lines[$i] -match '(core|sec|review|git|code|research|fe|front)-(\d{3})') {
            $ruleId = "$($Matches[1])-$($Matches[2])"
            $priority = 'unknown'
            # Look forward or backward for Priority line
            for ($j = [math]::Max(0, $i - 3); $j -lt [math]::Min($i + 8, $lines.Count); $j++) {
                if ($lines[$j] -match 'Priority[:\*\s]+P(\d)') {
                    $priority = "P$($Matches[1])"
                    break
                }
            }
            $results += @{ id = $ruleId; priority = $priority; file = (Split-Path $FilePath -Leaf) }
        }
    }
    return $results
}

function Parse-CapabilityEntries {
    <#
    .SYNOPSIS
    Extract CAP-xxx IDs and status from capability-inventory.md.
    #>
    param([Parameter(Mandatory)]$FilePath)
    if (-not (Test-Path $FilePath)) { return @() }

    $results = @()
    $content = Get-Content $FilePath -Raw
    $lines = $content -split "`n"

    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match 'CAP-(\d{3})') {
            $capId = "CAP-$($Matches[1])"
            $status = 'unknown'
            for ($j = $i; $j -lt [math]::Min($i + 10, $lines.Count); $j++) {
                if ($lines[$j] -match 'verified_status[:\s]*(verified|broken|stale|degraded|unknown)') {
                    $status = $Matches[1]
                    break
                }
            }
            $results += @{ id = $capId; status = $status }
        }
    }
    return $results
}

function New-CheckResult {
    <#
    .SYNOPSIS
    Standard check result object consumed by Test-Governance orchestrator.
    #>
    param(
        [string]$CheckName,
        [string]$Status,   # PASS | BLOCKED | INFRA_ERROR | WARN
        [string[]]$Details = @(),
        [string]$Suggestion = ''
    )
    return @{
        CheckName = $CheckName
        Status = $Status
        Details = $Details
        Suggestion = $Suggestion
    }
}

Export-ModuleMember -Function Get-ProjectRoot, Resolve-ExpectedFiles, Parse-RuleIds, Parse-CapabilityEntries, New-CheckResult
