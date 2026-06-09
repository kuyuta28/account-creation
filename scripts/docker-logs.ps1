$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

$ComposeFiles = @("-f", "docker-compose.yml")
if ($env:COMPOSE_PROFILES -and (Test-Path "docker-compose.$($env:COMPOSE_PROFILES).yml")) {
    $ComposeFiles += "-f", "docker-compose.$($env:COMPOSE_PROFILES).yml"
}
if (Test-Path "docker-compose.observability.yml") { $ComposeFiles += "-f", "docker-compose.observability.yml" }

$Tail = if ($args.Count -gt 0) { $args[0] } else { "100" }
$Service = if ($args.Count -gt 1) { $args[1] } else { "" }

docker compose @ComposeFiles logs --tail=$Tail --follow $Service
