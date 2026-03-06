param(
    [switch]$SkipWebBuild
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot

function Invoke-Step {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Title,
        [Parameter(Mandatory = $true)]
        [scriptblock]$Action
    )

    Write-Host ""
    Write-Host "==> $Title"
    & $Action
}

function Invoke-External {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,
        [string[]]$Arguments = @()
    )

    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        $renderedArgs = ($Arguments -join " ")
        throw "Command failed ($LASTEXITCODE): $FilePath $renderedArgs"
    }
}

function Invoke-JsonRequest {
    param(
        [Parameter(Mandatory = $true)]
        [ValidateSet("GET", "POST", "PUT", "DELETE")]
        [string]$Method,
        [Parameter(Mandatory = $true)]
        [string]$Uri,
        [object]$Body
    )

    $args = @{
        Method = $Method
        Uri = $Uri
        UseBasicParsing = $true
        TimeoutSec = 20
        ErrorAction = "Stop"
    }

    if ($null -ne $Body) {
        $args["ContentType"] = "application/json"
        $args["Body"] = ($Body | ConvertTo-Json -Depth 10)
    }

    $statusCode = 0
    $rawBody = $null

    try {
        $response = Invoke-WebRequest @args
        $statusCode = [int]$response.StatusCode
        $rawBody = $response.Content
    } catch {
        if (-not $_.Exception.Response) {
            throw
        }
        $statusCode = [int]$_.Exception.Response.StatusCode
        if ($_.ErrorDetails -and $_.ErrorDetails.Message) {
            $rawBody = $_.ErrorDetails.Message
        } else {
            $stream = $_.Exception.Response.GetResponseStream()
            $reader = New-Object System.IO.StreamReader($stream)
            $rawBody = $reader.ReadToEnd()
            $reader.Close()
        }
    }

    $payload = $null
    if ($rawBody) {
        try {
            $payload = $rawBody | ConvertFrom-Json
        } catch {
            $payload = $null
        }
    }

    return @{
        StatusCode = $statusCode
        Body = $payload
        Raw = $rawBody
    }
}

try {
    Invoke-Step -Title "Start/ensure stack" -Action {
        Invoke-External -FilePath "docker" -Arguments @("compose", "up", "-d")
    }

    Invoke-Step -Title "Wait for API and Web readiness" -Action {
        Invoke-External -FilePath "powershell" -Arguments @(
            "-ExecutionPolicy", "Bypass",
            "-File", "scripts/wait-url.ps1",
            "-Url", "http://localhost:8000/health",
            "-TimeoutSec", "60",
            "-IntervalMs", "500"
        )
        Invoke-External -FilePath "powershell" -Arguments @(
            "-ExecutionPolicy", "Bypass",
            "-File", "scripts/wait-url.ps1",
            "-Url", "http://localhost:3000",
            "-TimeoutSec", "60",
            "-IntervalMs", "500"
        )
    }

    Invoke-Step -Title "Apply migrations and run API tests" -Action {
        Invoke-External -FilePath "docker" -Arguments @("compose", "exec", "api", "sh", "-lc", "alembic upgrade head && alembic current")
        Invoke-External -FilePath "docker" -Arguments @("compose", "exec", "api", "sh", "-lc", "pytest tests -q")
    }

    Invoke-Step -Title "Run frontend lint/build checks" -Action {
        Invoke-External -FilePath "cmd" -Arguments @("/c", "npm run lint:web")
        if (-not $SkipWebBuild) {
            Invoke-External -FilePath "cmd" -Arguments @("/c", "npm run build --workspace @xplain/web")
        }
    }

    Invoke-Step -Title "Run API integration smoke scenario" -Action {
        $apiBase = "http://localhost:8000/api/v1/processes"

        $created = Invoke-JsonRequest -Method POST -Uri $apiBase -Body @{
            title = "Regression Scenario"
            description = "Collect input. Validate context. Produce visual explanation."
        }
        if ($created.StatusCode -ne 201) {
            throw "Create process failed with status $($created.StatusCode)"
        }

        $processId = $created.Body.id
        if (-not $processId) {
            throw "Create process returned empty id"
        }

        $generated = Invoke-JsonRequest -Method POST -Uri "$apiBase/$processId/generate-graph" -Body @{ text = $null }
        if ($generated.StatusCode -ne 200) {
            throw "Generate graph failed with status $($generated.StatusCode)"
        }
        if ($generated.Body.graph.nodes.Count -lt 1 -or $generated.Body.graph.edges.Count -lt 1) {
            throw "Generated graph has no nodes/edges"
        }

        $narrative = Invoke-JsonRequest -Method POST -Uri "$apiBase/$processId/generate-narrative" -Body $null
        if ($narrative.StatusCode -ne 200) {
            throw "Generate narrative failed with status $($narrative.StatusCode)"
        }
        if (-not $narrative.Body.summary) {
            throw "Generated narrative has empty summary"
        }
        if ($narrative.Body.steps.Count -lt 1) {
            throw "Generated narrative has no steps"
        }
        if (-not $narrative.Body.generatedBy) {
            throw "Generated narrative has no generatedBy marker"
        }

        $nodeId = $generated.Body.graph.nodes[0].id
        $edgeId = $generated.Body.graph.edges[0].id

        $revisions = Invoke-JsonRequest -Method GET -Uri "$apiBase/$processId/revisions" -Body $null
        if ($revisions.StatusCode -ne 200 -or $revisions.Body.Count -lt 2) {
            throw "Revision history is incomplete"
        }

        $commentProcess = Invoke-JsonRequest -Method POST -Uri "$apiBase/$processId/comments" -Body @{
            targetType = "process"
            message = "Regression process comment"
            author = "qa"
        }
        if ($commentProcess.StatusCode -ne 200) {
            throw "Process comment failed with status $($commentProcess.StatusCode)"
        }

        $commentNode = Invoke-JsonRequest -Method POST -Uri "$apiBase/$processId/comments" -Body @{
            targetType = "node"
            targetId = $nodeId
            message = "Regression node comment"
            author = "qa"
        }
        if ($commentNode.StatusCode -ne 200) {
            throw "Node comment failed with status $($commentNode.StatusCode)"
        }

        $commentEdge = Invoke-JsonRequest -Method POST -Uri "$apiBase/$processId/comments" -Body @{
            targetType = "edge"
            targetId = $edgeId
            message = "Regression edge comment"
            author = "qa"
        }
        if ($commentEdge.StatusCode -ne 200) {
            throw "Edge comment failed with status $($commentEdge.StatusCode)"
        }

        $comments = Invoke-JsonRequest -Method GET -Uri "$apiBase/$processId/comments" -Body $null
        if ($comments.StatusCode -ne 200 -or $comments.Body.Count -lt 3) {
            throw "Comments list is incomplete"
        }

        $statusInReview = Invoke-JsonRequest -Method POST -Uri "$apiBase/$processId/status" -Body @{
            targetStatus = "in_review"
        }
        if ($statusInReview.StatusCode -ne 200 -or $statusInReview.Body.status -ne "in_review") {
            throw "Transition to in_review failed"
        }

        $lockedGeneration = Invoke-JsonRequest -Method POST -Uri "$apiBase/$processId/generate-graph" -Body @{ text = "retry" }
        if ($lockedGeneration.StatusCode -ne 409 -or $lockedGeneration.Body.error.code -ne "process_locked") {
            throw "Expected process_locked 409, got $($lockedGeneration.StatusCode) with code $($lockedGeneration.Body.error.code)"
        }

        $summary = [ordered]@{
            processId = $processId
            graphVersion = [int]$generated.Body.version
            narrativeSteps = [int]$narrative.Body.steps.Count
            narrativeRefs = [int]$narrative.Body.references.Count
            revisions = [int]$revisions.Body.Count
            comments = [int]$comments.Body.Count
            status = [string]$statusInReview.Body.status
            lockedGenerationCheck = "passed"
        }

        ($summary | ConvertTo-Json -Depth 5) | Out-Host
    }

    Write-Host ""
    Write-Host "Regression suite PASSED."
    exit 0
}
catch {
    Write-Host ""
    Write-Host "Regression suite FAILED."
    Write-Host $_
    exit 1
}
finally {
    Pop-Location
}
