$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

# Resolve compose files (same logic as docker-down.ps1)
$ComposeFiles = @("-f", "docker-compose.yml")
if ($env:COMPOSE_PROFILES -and (Test-Path "docker-compose.$($env:COMPOSE_PROFILES).yml")) {
    $ComposeFiles += "-f", "docker-compose.$($env:COMPOSE_PROFILES).yml"
}
if (Test-Path "docker-compose.observability.yml") { $ComposeFiles += "-f", "docker-compose.observability.yml" }
$MigrationsFile = "docker-compose.migrations.yml"
$HasMigrations = Test-Path $MigrationsFile

function Invoke-Dc {
    param([Parameter(ValueFromRemainingArguments=$true)][string[]]$Args)
    Write-Host "> docker compose $($ComposeFiles -join ' ') $($Args -join ' ')"
    docker compose @ComposeFiles @Args
    if ($LASTEXITCODE -ne 0) { throw "docker compose $($Args -join ' ') failed ($LASTEXITCODE)" }
}

# 1. Bring up Postgres + dependencies first so migrations can run.
Write-Host "[up] phase 1: starting dependencies (postgres + traefik)..."
Invoke-Dc up -d --remove-orphans postgres traefik

if ($HasMigrations) {
    # 2. Run migrations (one-shot Flyway container).
    Write-Host "[up] phase 2: running migrations..."
    $AllFiles = $ComposeFiles + @("-f", $MigrationsFile)
    $flywayArgs = @("run", "--rm", "flyway")
    Write-Host "> docker compose $($AllFiles -join ' ') $($flywayArgs -join ' ')"
    docker compose @AllFiles @flywayArgs
    if ($LASTEXITCODE -ne 0) {
        throw "migrations failed (exit $LASTEXITCODE). Stack left half-up; run \`docker compose down\` and inspect."
    }
} else {
    Write-Host "[up] phase 2: skipping migrations (no $MigrationsFile)"
}

# 3. Bring up the rest.
Write-Host "[up] phase 3: starting app services..."
Invoke-Dc up -d --remove-orphans

# 4. Wait for healthchecks.
Write-Host "[up] phase 4: waiting for healthchecks..."
$Services = docker compose @ComposeFiles config --services
foreach ($svc in $Services) {
    Write-Host "  - $svc"
    $ok = $false
    for ($i=0; $i -lt 60; $i++) {
        $hc = docker compose @ComposeFiles ps --format json 2>$null | ConvertFrom-Json
        $row = $hc | Where-Object { $_.Service -eq $svc } | Select-Object -First 1
        if ($row -and $row.Health -eq "healthy") { $ok = $true; break }
        if ($row -and -not $row.Health) { $ok = $true; break }
        Start-Sleep -Seconds 2
    }
    if (-not $ok) { Write-Warning "  ! $svc did not become healthy in 120s" }
}

Write-Host "[up] status:"
Invoke-Dc ps
