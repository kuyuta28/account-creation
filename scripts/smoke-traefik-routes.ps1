param(
    [string]$BaseUrl = "http://localhost"
)

$routes = @(
    @{ Name = "registrar"; Url = "$BaseUrl/api/v1/health" },
    @{ Name = "mail-service"; Url = "$BaseUrl/mail/api/health" },
    @{ Name = "tts-proxy"; Url = "$BaseUrl/tts/api/health" },
    @{ Name = "aa-proxy"; Url = "$BaseUrl/aa/api/health" }
)

foreach ($route in $routes) {
    $response = Invoke-WebRequest -Uri $route.Url -UseBasicParsing -TimeoutSec 10
    if ($response.StatusCode -lt 200 -or $response.StatusCode -ge 300) {
        throw "$($route.Name) returned HTTP $($response.StatusCode) at $($route.Url)"
    }
    Write-Host "$($route.Name) OK $($response.StatusCode) $($route.Url)"
}
