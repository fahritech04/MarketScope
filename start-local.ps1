param(
  [switch]$ReinstallDeps,
  [switch]$SkipSchema
)

$ErrorActionPreference = "Stop"

function Write-Step([string]$message) {
  Write-Host "==> $message" -ForegroundColor Cyan
}

function Read-DotEnv([string]$envPath) {
  $map = @{}
  if (-not (Test-Path $envPath)) {
    return $map
  }
  foreach ($line in Get-Content -LiteralPath $envPath) {
    $trimmed = $line.Trim()
    if (-not $trimmed -or $trimmed.StartsWith("#")) {
      continue
    }
    $idx = $trimmed.IndexOf("=")
    if ($idx -lt 1) {
      continue
    }
    $key = $trimmed.Substring(0, $idx).Trim()
    $value = $trimmed.Substring($idx + 1).Trim()
    $map[$key] = $value
  }
  return $map
}

function Wait-HttpReady([string]$url, [int]$timeoutSec) {
  $deadline = (Get-Date).AddSeconds($timeoutSec)
  while ((Get-Date) -lt $deadline) {
    try {
      Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 5 | Out-Null
      return $true
    }
    catch {
      Start-Sleep -Seconds 2
    }
  }
  return $false
}

$rootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$apiDir = Join-Path $rootDir "apps\api"
$webDir = Join-Path $rootDir "apps\web"
$envPath = Join-Path $rootDir ".env"

if (-not (Test-Path $envPath)) {
  throw "File .env belum ada di root project: $envPath"
}

$envMap = Read-DotEnv -envPath $envPath

Write-Step "Menyiapkan backend Python"
$venvPython = Join-Path $apiDir ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
  py -3.12 -m venv (Join-Path $apiDir ".venv")
}

if ($ReinstallDeps -or -not (Test-Path (Join-Path $apiDir ".venv\Lib\site-packages\fastapi"))) {
  & $venvPython -m pip install -r (Join-Path $apiDir "requirements.txt")
}

if (-not (Test-Path "$env:LOCALAPPDATA\ms-playwright\chromium-*")) {
  & $venvPython -m playwright install chromium
}

Write-Step "Menyiapkan frontend Node.js"
if ($ReinstallDeps -or -not (Test-Path (Join-Path $webDir "node_modules"))) {
  & npm.cmd --prefix $webDir install
}

$apiBase = if ($envMap.ContainsKey("NEXT_PUBLIC_API_URL") -and $envMap["NEXT_PUBLIC_API_URL"]) {
  $envMap["NEXT_PUBLIC_API_URL"]
} else {
  "http://127.0.0.1:8000/api/v1"
}

$webEnvLocal = Join-Path $webDir ".env.local"
Set-Content -LiteralPath $webEnvLocal -Value "NEXT_PUBLIC_API_URL=$apiBase" -Encoding UTF8

if (-not $SkipSchema) {
  if ($envMap.ContainsKey("SUPABASE_DB_URL") -and $envMap["SUPABASE_DB_URL"]) {
    Write-Step "Apply schema ke Supabase PostgreSQL"
    $schemaPath = Join-Path $rootDir "database\schema.sql"
    $schemaPy = @"
import os
from pathlib import Path
import psycopg

conninfo = os.environ["SUPABASE_DB_URL"]
schema = Path(r"$schemaPath").read_text(encoding="utf-8")
with psycopg.connect(conninfo, autocommit=True) as conn:
    with conn.cursor() as cur:
        cur.execute(schema)
print("SCHEMA_APPLIED=1")
"@
    $tmpPy = Join-Path $rootDir ".tmp_apply_schema.py"
    Set-Content -LiteralPath $tmpPy -Value $schemaPy -Encoding UTF8
    try {
      $env:SUPABASE_DB_URL = $envMap["SUPABASE_DB_URL"]
      & $venvPython $tmpPy
    }
    finally {
      Remove-Item -LiteralPath $tmpPy -Force -ErrorAction SilentlyContinue
      Remove-Item Env:\SUPABASE_DB_URL -ErrorAction SilentlyContinue
    }
  } else {
    Write-Warning "SUPABASE_DB_URL belum di-set di .env, apply schema dilewati."
  }
}

Write-Step "Menjalankan backend + frontend (background)"
$backendOut = Join-Path $rootDir "backend.log"
$backendErr = Join-Path $rootDir "backend.err.log"
$frontendOut = Join-Path $rootDir "frontend.log"
$frontendErr = Join-Path $rootDir "frontend.err.log"

# Stop process lama di port 8000/3000 jika ada.
foreach ($port in @(8000, 3000)) {
  $connections = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
  foreach ($conn in $connections) {
    try {
      Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
    } catch {}
  }
}
Start-Sleep -Seconds 1

$backendProc = Start-Process `
  -FilePath $venvPython `
  -ArgumentList @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000") `
  -WorkingDirectory $apiDir `
  -WindowStyle Hidden `
  -RedirectStandardOutput $backendOut `
  -RedirectStandardError $backendErr `
  -PassThru

$frontendProc = Start-Process `
  -FilePath "npm.cmd" `
  -ArgumentList @("run", "dev", "--", "--hostname", "127.0.0.1", "--port", "3000") `
  -WorkingDirectory $webDir `
  -WindowStyle Hidden `
  -RedirectStandardOutput $frontendOut `
  -RedirectStandardError $frontendErr `
  -PassThru

$backendReady = Wait-HttpReady -url "http://127.0.0.1:8000/health" -timeoutSec 60
$frontendReady = Wait-HttpReady -url "http://127.0.0.1:3000" -timeoutSec 90

Write-Host ""
Write-Host "Backend PID  : $($backendProc.Id)"
Write-Host "Frontend PID : $($frontendProc.Id)"
Write-Host "Backend URL  : http://127.0.0.1:8000/health (ready=$backendReady)"
Write-Host "Frontend URL : http://127.0.0.1:3000 (ready=$frontendReady)"
Write-Host ""
Write-Host "Log backend  : $backendOut"
Write-Host "Log frontend : $frontendOut"
