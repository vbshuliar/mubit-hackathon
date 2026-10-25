param(
    [ValidateSet('fixi', 'lab')]
    [string]$App = 'fixi'
)

$ErrorActionPreference = 'Stop'
$exitCode = 0
$backendPath = Join-Path $PSScriptRoot 'RepairFlow\backend'

if ($App -eq 'fixi') {
    $frontendIndex = Join-Path $PSScriptRoot 'RepairFlow\frontend-fixi\dist\index.html'
    if (-not (Test-Path -LiteralPath $frontendIndex)) {
        throw 'Build the frontend first: cd RepairFlow\frontend-fixi; npm ci; npm run build'
    }
    Push-Location -LiteralPath $backendPath
    try {
        Write-Host 'FIXI: http://localhost:8000/maintenance (Ctrl+C to stop)'
        & uv run --frozen uvicorn app.main:app --host 127.0.0.1 --port 8000
        $exitCode = $LASTEXITCODE
    } finally {
        Pop-Location
    }
} else {
    Push-Location -LiteralPath $PSScriptRoot
    try {
        Write-Host 'Learning lab: http://localhost:3000 (Ctrl+C to stop)'
        & node --env-file-if-exists=.env server.mjs
        $exitCode = $LASTEXITCODE
    } finally {
        Pop-Location
    }
}

exit $exitCode
