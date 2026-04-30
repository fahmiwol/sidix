param(
  [string]$Path = "."
)

$ErrorActionPreference = "Stop"

Write-Host "Scanning for high-risk patterns in tracked files..." -ForegroundColor Cyan

$patterns = @(
  "sk-[A-Za-z0-9]{20,}",                 # generic key-like tokens
  "BEGIN( RSA)? PRIVATE KEY",            # private keys
  "AKIA[0-9A-Z]{16}",                    # AWS access key id
  "xox[baprs]-[A-Za-z0-9-]+",            # Slack tokens
  "D:\\\\MIGHAN Model",                  # local path (example)
  "C:\\\\Users\\\\",                     # local path
  "password\\s*=",
  "api[_-]?key",
  "secret\\b",
  "token\\b"
)

$files = git ls-files
if (-not $files) {
  Write-Host "No tracked files found." -ForegroundColor Yellow
  exit 0
}

$hadHits = $false
foreach ($pat in $patterns) {
  $hits = $files | Select-String -Pattern $pat -CaseSensitive:$false -List
  if ($hits) {
    $hadHits = $true
    Write-Host ""
    Write-Host "Pattern: $pat" -ForegroundColor Yellow
    $hits | ForEach-Object { Write-Host (" - " + $_.Path) }
  }
}

if ($hadHits) {
  Write-Host ""
  Write-Host "Scan finished: potential hits found. Review before commit." -ForegroundColor Red
  exit 2
}

Write-Host ""
Write-Host "Scan finished: no hits." -ForegroundColor Green

