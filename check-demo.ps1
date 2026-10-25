param([string]$BaseUrl = 'http://localhost:8000')
$ErrorActionPreference = 'Stop'
# Read-only gate: never starts/stops services, seeds data, or records video.
$metadataPath = Join-Path $PSScriptRoot 'RepairFlow\backend\data\demo-prep\roof-scaffold-fixture-case.json'
$metadata = Get-Content -LiteralPath $metadataPath -Raw | ConvertFrom-Json
$caseId = $metadata.case_id
function Assert-Demo($condition, [string]$message) {
    if (-not $condition) { throw $message }
}
$null = Invoke-RestMethod "$BaseUrl/healthz" -TimeoutSec 10
$ready = Invoke-RestMethod "$BaseUrl/api/v1/readiness" -TimeoutSec 10
Assert-Demo ($ready.database -eq 'ok' -and $ready.coordinator_provider -eq 'fixture') 'Expected a healthy offline fixture backend.'
$detail = Invoke-RestMethod "$BaseUrl/api/v1/cases/$caseId" -TimeoutSec 10
$snapshot = $detail.snapshot
Assert-Demo ($snapshot.case.status -eq 'RESOLVED') 'Demo case is not resolved.'
Assert-Demo (@($snapshot.work_orders).Count -eq 3) 'Expected three demo work orders.'
Assert-Demo (@($snapshot.work_orders | Where-Object status -ne 'COMPLETED').Count -eq 0) 'A work order is incomplete.'
Assert-Demo (@($snapshot.dependencies).Count -eq 2) 'Expected two dependencies.'
Assert-Demo (@($snapshot.dependencies | Where-Object status -ne 'SATISFIED').Count -eq 0) 'A dependency remains unsatisfied.'
$runs = Invoke-RestMethod "$BaseUrl/api/v1/cases/$caseId/runs?limit=50" -TimeoutSec 10
Assert-Demo (@($runs.items).Count -eq 11) 'Expected eleven demo decision rounds.'
Assert-Demo (@($runs.items | Where-Object action_state -ne 'SUCCEEDED').Count -eq 0) 'A demo action has not succeeded.'
foreach ($section in @('', '/summary', '/timeline', '/agent', '/work', '/property', '/files', '/costs', '/messages')) {
    $url = "$BaseUrl/maintenance/tickets/$caseId$section"
    $page = Invoke-WebRequest $url -UseBasicParsing -TimeoutSec 10
    Assert-Demo ($page.StatusCode -eq 200 -and $page.Content -match '<html') "Page shell unavailable: $url"
}
Write-Output "PASS: fixture backend, resolved case #$($snapshot.case.case_number), 3 completed work orders, 2 satisfied dependencies, 11 succeeded actions, 9 page shells."
Write-Output "Demo URL: $BaseUrl/maintenance/tickets/$caseId"
Write-Output 'Browser rehearsal is still required: HTTP page shells alone do not prove rendered UI. Do not record until all planned content is visibly loaded.'
