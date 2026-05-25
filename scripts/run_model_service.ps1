param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("land", "house", "rental")]
    [string]$Model,

    [int]$Port = 0,

    [string]$HostAddress = "127.0.0.1",

    [string]$Python = ""
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$defaultPython = Join-Path $repoRoot "backend\.venv\Scripts\python.exe"

if (-not $Python) {
    if (Test-Path $defaultPython) {
        $Python = $defaultPython
    } else {
        $Python = "python"
    }
}

$defaultPorts = @{
    land = 8011
    house = 8012
    rental = 8013
}

if ($Port -le 0) {
    $Port = $defaultPorts[$Model]
}

$module = "ml.$($Model)_service.app:app"

Write-Host "Starting Reva $Model model service"
Write-Host "URL: http://$HostAddress`:$Port"
Write-Host "Health: http://$HostAddress`:$Port/health"
Write-Host "Predict: http://$HostAddress`:$Port/predict"

& $Python -B -m uvicorn $module --host $HostAddress --port $Port --reload
