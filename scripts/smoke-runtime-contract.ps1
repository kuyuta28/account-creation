$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$Compose = Join-Path $Root "docker-compose.yml"

function Invoke-Checked {
    param([string] $Command)
    Write-Host "> $Command"
    cmd /c $Command
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code ${LASTEXITCODE}: $Command"
    }
}

function Wait-HttpOk {
    param(
        [string] $Url,
        [hashtable] $Headers = @{},
        [int] $TimeoutSeconds = 90
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    $lastError = $null
    while ((Get-Date) -lt $deadline) {
        try {
            $response = Invoke-WebRequest -UseBasicParsing $Url -Headers $Headers -TimeoutSec 5
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 300) {
                return $response
            }
            $lastError = "HTTP $($response.StatusCode)"
        } catch {
            $lastError = $_.Exception.Message
        }
        Start-Sleep -Seconds 2
    }

    throw "Timed out waiting for $Url. Last error: $lastError"
}

function Assert-ImageFileNotEmpty {
    param(
        [string] $Image,
        [string] $Path
    )

    $size = docker run --rm $Image python -c "import pathlib; print(pathlib.Path('$Path').stat().st_size)"
    if ($LASTEXITCODE -ne 0) {
        throw "Cannot inspect $Image`:$Path"
    }
    if ([int] $size -le 0) {
        throw "$Image`:$Path is empty"
    }
}

function Assert-ContainerPythonExpression {
    param(
        [string] $Container,
        [string] $Expression
    )

    docker exec $Container python -c $Expression
    if ($LASTEXITCODE -ne 0) {
        throw "Python contract failed in $Container`: $Expression"
    }
}

Set-Location $Root

Invoke-Checked "docker compose -f `"$Compose`" build --no-cache registrar aa-proxy mail-service tts-proxy"

Assert-ImageFileNotEmpty "account-creation-registrar" "/app/src/api/server.py"
Assert-ImageFileNotEmpty "account-creation-registrar" "/app/src/api/routers/accounts.py"
Assert-ImageFileNotEmpty "account-creation-registrar" "/app/src/config/settings.py"
Assert-ImageFileNotEmpty "account-creation-aa-proxy" "/app/src/aa_proxy/server.py"

Invoke-Checked "docker compose -f `"$Compose`" up -d --force-recreate postgres registrar aa-proxy mail-service tts-proxy"

Assert-ContainerPythonExpression "registrar" "import uvicorn; assert hasattr(uvicorn, 'run'); import src.api.server as s; assert hasattr(s, 'app')"
Assert-ContainerPythonExpression "aa-proxy" "import uvicorn; assert hasattr(uvicorn, 'run'); import src.aa_proxy.server as s; assert hasattr(s, 'app')"

$health = Wait-HttpOk "http://localhost:8709/api/v1/health"
$healthJson = $health.Content | ConvertFrom-Json
if (-not $healthJson.success -or $healthJson.data.status -ne "ok") {
    throw "Registrar health contract failed: $($health.Content)"
}

$origin = "http://127.0.0.1:1421"
$accounts = Wait-HttpOk "http://localhost:8709/api/v1/accounts?page=1&limit=100" @{ Origin = $origin }
$cors = $accounts.Headers["Access-Control-Allow-Origin"]
if ($cors -ne $origin) {
    throw "CORS contract failed. Expected $origin, got $cors"
}

$accountsJson = $accounts.Content | ConvertFrom-Json
if (-not $accountsJson.success -or $null -eq $accountsJson.data.accounts) {
    throw "Accounts response envelope contract failed: $($accounts.Content)"
}

Write-Host "Runtime contract smoke passed. Accounts returned: $($accountsJson.data.accounts.Count)"