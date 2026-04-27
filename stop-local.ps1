$ErrorActionPreference = "SilentlyContinue"

foreach ($port in @(8000, 3000)) {
  $connections = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
  foreach ($conn in $connections) {
    Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
  }
}

Write-Host "Service lokal dihentikan (port 8000 dan 3000)."
