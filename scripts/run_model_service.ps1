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
$healthUrl = "http://$HostAddress`:$Port/health"
$predictUrl = "http://$HostAddress`:$Port/predict"

try {
    $health = Invoke-RestMethod -Uri $healthUrl -TimeoutSec 2 -ErrorAction Stop
    $runningModel = ""
    if ($health.PSObject.Properties.Name -contains "model_type") {
        $runningModel = [string]$health.model_type
    }
    if (-not $runningModel -or $runningModel -eq $Model) {
        Write-Host "Reva $Model model service is already running"
        Write-Host "URL: http://$HostAddress`:$Port"
        Write-Host "Health: $healthUrl"
        Write-Host "Predict: $predictUrl"
        return
    }
} catch {
    # No healthy model service is responding on this port; continue to port check.
}

$portIsOpen = $false
$client = [System.Net.Sockets.TcpClient]::new()
try {
    $connect = $client.BeginConnect($HostAddress, $Port, $null, $null)
    if ($connect.AsyncWaitHandle.WaitOne(500)) {
        $client.EndConnect($connect)
        $portIsOpen = $true
    }
} catch {
    $portIsOpen = $false
} finally {
    $client.Close()
}

if ($portIsOpen) {
    throw "Port $Port on $HostAddress is already in use by another process. Stop that process or run with -Port <another-port>."
}

Write-Host "Starting Reva $Model model service"
Write-Host "URL: http://$HostAddress`:$Port"
Write-Host "Health: $healthUrl"
Write-Host "Predict: $predictUrl"

& $Python -B -m uvicorn $module --host $HostAddress --port $Port --reload
