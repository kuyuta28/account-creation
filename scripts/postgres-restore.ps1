$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

$PGContainer = if ($env:PG_CONTAINER) { $env:PG_CONTAINER } else { "postgres" }
$DbName = if ($env:DB_NAME) { $env:DB_NAME } else { "account_creator" }
$DbUser = if ($env:DB_USER) { $env:DB_USER } else { "ccs" }

if ($args.Count -lt 1) {
    Write-Host "Usage: pwsh scripts/postgres-restore.ps1 <path-to-dump> [--yes]"
    Write-Host "  --yes  skip the destructive 'are you sure' prompt"
    exit 1
}
$DumpFile = $args[0]
$Force = ($args -contains "--yes")

if (-not (Test-Path $DumpFile)) { throw "Dump file not found: $DumpFile" }
$Size = (Get-Item $DumpFile).Length
Write-Host "[restore] dump: $DumpFile ($([math]::Round($Size/1MB,2)) MB)"

$running = docker ps --filter "name=$PGContainer" --filter "status=running" --format '{{.Names}}'
if (-not $running) { throw "Postgres container '$PGContainer' is not running." }

docker exec $PGContainer pg_isready -U $DbUser -d $DbName | Out-Null
if ($LASTEXITCODE -ne 0) { throw "pg_isready failed" }

# Confirm with the operator unless --yes
if (-not $Force) {
    Write-Host ""
    Write-Host "*** This will OVERWRITE the current database '$DbName' in $PGContainer." -ForegroundColor Yellow
    Write-Host "*** Stop the dependent services first (registrar/mail/aa/tts) so they don't reconnect mid-restore." -ForegroundColor Yellow
    $resp = Read-Host "Type 'restore' to continue"
    if ($resp -ne "restore") { Write-Host "Aborted."; exit 0 }
}

# Copy dump into container
$TmpPath = "/tmp/restore-$([guid]::NewGuid().ToString('N')).dump"
Write-Host "[restore] copying dump into container..."
Get-Content $DumpFile -Raw -Encoding Byte | docker exec -i $PGContainer sh -c "cat > $TmpPath"
if ($LASTEXITCODE -ne 0) { throw "docker cp into container failed" }

# Drop and recreate. We can't drop the db while connected, so use a maintenance db.
Write-Host "[restore] dropping + recreating database '$DbName'..."
docker exec $PGContainer psql -U $DbUser -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='$DbName' AND pid <> pg_backend_pid();" | Out-Null
docker exec $PGContainer dropdb -U $DbUser --if-exists $DbName
if ($LASTEXITCODE -ne 0) { throw "dropdb failed" }
docker exec $PGContainer createdb -U $DbUser -O $DbUser $DbName
if ($LASTEXITCODE -ne 0) { throw "createdb failed" }

Write-Host "[restore] running pg_restore (this can take minutes on large dumps)..."
docker exec $PGContainer pg_restore -U $DbUser -d $DbName --no-owner --clean --if-exists $TmpPath 2>&1 | Out-Null
# pg_restore exits 0 only when perfectly clean; warnings are common. Treat 0 and 1 as OK.
if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne 1) {
    docker exec $PGContainer rm -f $TmpPath | Out-Null
    throw "pg_restore failed (exit $LASTEXITCODE)"
}

docker exec $PGContainer rm -f $TmpPath | Out-Null

# Post-restore sanity check: count accounts
$count = docker exec $PGContainer psql -U $DbUser -d $DbName -tAc "SELECT count(*) FROM accounts"
Write-Host "[restore] OK. accounts row count after restore: $count"
Write-Host "[restore] You can now restart dependent services:"
Write-Host "          pwsh scripts/docker-up.ps1"
