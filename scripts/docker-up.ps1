$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

$ComposeFiles = @("-f", "docker-compose.yml")
if ($env:COMPOSE_PROFILES) { $ComposeFiles += "-f", "docker-compose.$($env:COMPOSE_PROFILES).yml" }
if (Test-Path "docker-compose.observability.yml") { $ComposeFiles += "-f", "docker-compose.observability.yml" }

function Invoke-Dc {
    param([Parameter(ValueFromRemainingArguments=$true)][string[]]$Args)
    Write-Host "> docker compose $($Args -join ' ')"
    docker compose @ComposeFiles @Args
    if ($LASTEXITCODE -ne 0) { throw "docker compose $($Args -join ' ') failed ($LASTEXITCODE)" }
}

Write-Host "[up] starting services..."
Invoke-Dc up -d --remove-orphans

Write-Host "[up] waiting for healthchecks..."
$Services = docker compose @ComposeFiles config --services
foreach ($svc in $Services) {
    Write-Host "  - $svc"
    $ok = $false
    for ($i=0; $i -lt 60; $i++) {
        $hc = docker compose @ComposeFiles ps --format json 2>$null | ConvertFrom-Json
        $row = $hc | Where-Object { $_.Service -eq $svc } | Select-Object -First 1
        if ($row -and $row.Health -eq "healthy") { $ok = $true; break }
        if ($row -and -not $row.Health) { $ok = $true; break }  # no healthcheck defined
        Start-Sleep -Seconds 2
    }
    if (-not $ok) { Write-Warning "  ! $svc did not become healthy in 120s" }
}

Write-Host "[up] status:"
Invoke-Dc ps
