$ErrorActionPreference = "Continue"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

$ComposeFiles = @("-f", "docker-compose.yml")
if ($env:COMPOSE_PROFILES -and (Test-Path "docker-compose.$($env:COMPOSE_PROFILES).yml")) {
    $ComposeFiles += "-f", "docker-compose.$($env:COMPOSE_PROFILES).yml"
}

Write-Host "> docker compose $($ComposeFiles -join ' ') down"
& docker compose @ComposeFiles down 2>&1 | Out-Null

if ($env:PRUNE_VOLUMES -eq "1") {
    Write-Host "[down] removing postgres_data volume"
    docker volume rm account-creation_postgres_data 2>$null
}