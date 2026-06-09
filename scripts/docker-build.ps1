$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

$ComposeFiles = @("-f", "docker-compose.yml")
if ($env:COMPOSE_PROFILES -and (Test-Path "docker-compose.$($env:COMPOSE_PROFILES).yml")) {
    $ComposeFiles += "-f", "docker-compose.$($env:COMPOSE_PROFILES).yml"
}
if (Test-Path "docker-compose.observability.yml") { $ComposeFiles += "-f", "docker-compose.observability.yml" }

$Target = if ($args.Count -gt 0) { $args[0] } else { "" }
$NoCache = if ($env:NO_CACHE -eq "1") { "--no-cache" } else { "" }

Write-Host "[build] docker compose build $Target $NoCache"
docker compose @ComposeFiles build $NoCache $Target
if ($LASTEXITCODE -ne 0) { throw "build failed ($LASTEXITCODE)" }
Write-Host "[build] OK"
