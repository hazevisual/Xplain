param(
    [Parameter(Mandatory = $true)]
    [string]$Url,
    [int]$TimeoutSec = 20,
    [int]$IntervalMs = 250
)

$deadline = (Get-Date).AddSeconds($TimeoutSec)

do {
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 1 -ErrorAction Stop
        if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
            Write-Output "UP"
            exit 0
        }
    } catch {
        # Keep polling until timeout.
    }
    Start-Sleep -Milliseconds $IntervalMs
} while ((Get-Date) -lt $deadline)

Write-Output "DOWN"
exit 1
