param(
    [string]$CommandLabel = "",
    [string]$Since,
    [string]$TaskId = "",
    [string]$OutputPath = ""
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot

function Invoke-Git {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Args
    )

    $result = & git @Args
    if ($LASTEXITCODE -ne 0) {
        throw "Git command failed: git $($Args -join ' ')"
    }

    if ($null -eq $result) {
        return @()
    }

    return @($result)
}

try {
    if ([string]::IsNullOrWhiteSpace($CommandLabel)) {
        $CommandLabel = ([char]0x041E) + ([char]0x0442) + ([char]0x0447) + ([char]0x0435) + ([char]0x0442)
    }

    if ([string]::IsNullOrWhiteSpace($OutputPath)) {
        $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
        $OutputPath = "docs/reports/SESSION-$stamp.md"
    }

    if ([string]::IsNullOrWhiteSpace($Since)) {
        $reportsDir = Join-Path $repoRoot "docs/reports"
        $latestReport = $null
        if (Test-Path $reportsDir) {
            $latestReport = Get-ChildItem -Path $reportsDir -Filter "SESSION-*.md" -File |
                Sort-Object LastWriteTimeUtc -Descending |
                Select-Object -First 1
        }

        if ($null -ne $latestReport) {
            $Since = $latestReport.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
        } else {
            $Since = (Get-Date).Date.ToString("yyyy-MM-dd HH:mm:ss")
        }
    }

    $branch = ((Invoke-Git -Args @("rev-parse", "--abbrev-ref", "HEAD")) | Select-Object -First 1).ToString().Trim()
    $headHash = ((Invoke-Git -Args @("rev-parse", "--short", "HEAD")) | Select-Object -First 1).ToString().Trim()
    $headSubject = ((Invoke-Git -Args @("show", "-s", "--format=%s", "HEAD")) | Select-Object -First 1).ToString().Trim()
    $statusLines = Invoke-Git -Args @("status", "--short")
    $isClean = $statusLines.Count -eq 0

    $commitLines = @(& git log --since="$Since" --date=iso --pretty=format:"- %h %ad %s")
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to collect git commits since '$Since'"
    }
    if ($commitLines.Count -eq 0) {
        $commitLines = @("- no commits in selected window")
    }

    $changedFilesRaw = @(& git log --since="$Since" --name-only --pretty=format:)
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to collect changed files since '$Since'"
    }
    $changedFiles = @(
        $changedFilesRaw |
            Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
            Sort-Object -Unique |
            ForEach-Object { "- $_" }
    )
    if ($changedFiles.Count -eq 0) {
        $changedFiles = @("- no files changed in selected window")
    }

    $workingTreeSection = @()
    if ($isClean) {
        $workingTreeSection = @("- clean")
    } else {
        $workingTreeSection = @($statusLines | ForEach-Object { "- $_" })
    }

    $utcNow = (Get-Date).ToUniversalTime().ToString("o")
    $localNow = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")

    $taskLine = if ([string]::IsNullOrWhiteSpace($TaskId)) { "n/a" } else { $TaskId }

    $report = @()
    $report += "## Session Report"
    $report += ""
    $report += "- Command: $CommandLabel"
    $report += "- Generated at (local): $localNow"
    $report += "- Generated at (UTC): $utcNow"
    $report += "- Branch: $branch"
    $report += "- HEAD: $headHash ($headSubject)"
    $report += "- Task ID: $taskLine"
    $report += "- Window start: $Since"
    $report += ""
    $report += "### Summary"
    $report += "- Fill in a short human summary for this session."
    $report += ""
    $report += "### Completed"
    $report += "- Fill in completed outcomes."
    $report += ""
    $report += "### In Progress"
    $report += "- Fill in remaining work."
    $report += ""
    $report += "### Risks / Blockers"
    $report += "- none"
    $report += ""
    $report += "### Validation"
    $report += '- Fill in checks run (`tests`, `build`, `smoke`).'
    $report += ""
    $report += "### Commits In Window"
    $report += $commitLines
    $report += ""
    $report += "### Files Changed In Window"
    $report += $changedFiles
    $report += ""
    $report += "### Working Tree Snapshot"
    $report += $workingTreeSection
    $report += ""
    $report += "### Next Actions"
    $report += "- Fill in next concrete actions."
    $report += ""

    $fullOutputPath = Join-Path $repoRoot $OutputPath
    $outputDir = Split-Path -Parent $fullOutputPath
    New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
    Set-Content -Path $fullOutputPath -Value $report -Encoding utf8

    Write-Output "REPORT_PATH=$OutputPath"
    exit 0
}
catch {
    Write-Error $_
    exit 1
}
finally {
    Pop-Location
}
