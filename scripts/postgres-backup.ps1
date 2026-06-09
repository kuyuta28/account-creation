$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

# Resolve compose files (same logic as docker-up.ps1)
$ComposeFiles = @("-f", "docker-compose.yml")
if ($env:COMPOSE_PROFILES -and (Test-Path "docker-compose.$($env:COMPOSE_PROFILES).yml")) {
    $ComposeFiles += "-f", "docker-compose.$($env:COMPOSE_PROFILES).yml"
}
if (Test-Path "docker-compose.observability.yml") { $ComposeFiles += "-f", "docker-compose.observability.yml" }

# Postgres container name comes from docker-compose.yml: ccs-postgres (we override
# to the project-prefixed name produced by docker compose v2).
$PGContainer = if ($env:PG_CONTAINER) { $env:PG_CONTAINER } else { "account-creation-postgres-1" }
$DbName = if ($env:DB_NAME) { $env:DB_NAME } else { "account_creator" }
$DbUser = if ($env:DB_USER) { $env:DB_USER } else { "ccs" }
$OutDir = if ($env:BACKUP_DIR) { $env:BACKUP_DIR } else { (Join-Path $Root "backups\postgres") }

if (-not (Test-Path $OutDir)) {
    New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
}

$Stamp = (Get-Date -Format "yyyyMMdd-HHmmss")
$File = Join-Path $OutDir "pgdump-$DbName-$Stamp.dump"

# Pre-flight: container must be up
$running = docker ps --filter "name=$PGContainer" --filter "status=running" --format '{{.Names}}'
if (-not $running) {
    throw "Postgres container '$PGContainer' is not running. Start the stack first."
}

# Pre-flight: db must be reachable
docker exec $PGContainer pg_isready -U $DbUser -d $DbName | Out-Null
if ($LASTEXITCODE -ne 0) { throw "pg_isready failed (exit $LASTEXITCODE)" }

Write-Host "[backup] target: $File"
Write-Host "[backup] format: custom (compressed)"

# pg_dump custom format (-Fc) is the only format that supports selective restore with pg_restore.
# It is also compressed, so backup files stay small.
docker exec $PGContainer pg_dump -U $DbUser -d $DbName --format=custom --no-owner --clean --if-exists --file=/tmp/backup.dump
if ($LASTEXITCODE -ne 0) { throw "pg_dump inside container failed ($LASTEXITCODE)" }

docker cp "$PGContainer`:/tmp/backup.dump" $File
if ($LASTEXITCODE -ne 0) { throw "docker cp failed ($LASTEXITCODE)" }

docker exec $PGContainer rm -f /tmp/backup.dump | Out-Null

# Verify the dump is a valid pg_dump archive.
# `pg_restore -l` lists the table of contents; exit 0 = valid, exit 1 = warnings only.
Write-Host "[backup] verifying archive..."
# Use `cmd /c` so the `<` redirect is parsed by cmd, not PowerShell.
$verify = cmd /c "docker exec -i $PGContainer pg_restore -l < `"$File`" 2>&1"
$verify | Out-Null
if ($LASTEXITCODE -ne 1 -and $LASTEXITCODE -ne 0) {
    throw "Backup archive verification FAILED (pg_restore -l exit $LASTEXITCODE)"
}

$Size = (Get-Item $File).Length
Write-Host "[backup] OK: $File ($([math]::Round($Size/1MB,2)) MB)"

# Retention: keep last 14 daily, 8 weekly. Default 7d, override with BACKUP_RETAIN_DAYS.
$RetainDays = if ($env:BACKUP_RETAIN_DAYS) { [int]$env:BACKUP_RETAIN_DAYS } else { 14 }
Get-ChildItem -Path $OutDir -Filter "pgdump-*.dump" -ErrorAction SilentlyContinue |
    Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-$RetainDays) } |
    ForEach-Object {
        Write-Host "[backup] removing old: $($_.Name) (age > $RetainDays days)"
        Remove-Item $_.FullName -Force
    }

Write-Host "[backup] done."
