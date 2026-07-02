$ErrorActionPreference = "Continue"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

$ComposeFiles = @("-f", "docker-compose.yml")
if ($env:COMPOSE_PROFILES -and (Test-Path "docker-compose.$($env:COMPOSE_PROFILES).yml")) {
    $ComposeFiles += "-f", "docker-compose.$($env:COMPOSE_PROFILES).yml"
}

Write-Host "=== compose ps ==="
& docker compose @ComposeFiles ps

Write-Host ""
Write-Host "=== docker ps (all) ==="
docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

Write-Host ""
Write-Host "=== healthchecks ==="
foreach ($svc in (& docker compose @ComposeFiles config --services)) {
    $hc = docker inspect --format '{{.Name}} health={{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "$svc" 2>$null
    if ($hc) { Write-Host "  $hc" } else { Write-Host "  $svc  (not running)" }
}

Write-Host ""
Write-Host "=== disk ==="
docker system df

Write-Host ""
Write-Host "=== volume: postgres_data ==="
docker volume inspect account-creation_postgres_data --format '{{.Mountpoint}}  {{.Size}}' 2>$null