#!/usr/bin/env pwsh
# sidix-learn.ps1 — Capture knowledge cepat ke corpus SIDIX
#
# Usage:
#   .\tools\sidix-learn.ps1 "topik singkat"
#   .\tools\sidix-learn.ps1 "nginx reverse proxy" "Nginx adalah web server..."
#
# Output: brain/public/research_notes/[N]_[slug].md

param(
    [Parameter(Mandatory=$true)]
    [string]$Topik,

    [Parameter(Mandatory=$false)]
    [string]$IsiAwal = ""
)

# Cari nomor berikutnya
$notesDir = "brain\public\research_notes"
$files = Get-ChildItem $notesDir -Filter "*.md" | Sort-Object Name
$lastNum = 0
if ($files) {
    $lastFile = $files[-1].Name
    if ($lastFile -match "^(\d+)_") {
        $lastNum = [int]$Matches[1]
    }
}
$nextNum = $lastNum + 1

# Buat slug dari topik
$slug = $Topik.ToLower() -replace '[^a-z0-9\s]', '' -replace '\s+', '_'
$fileName = "${nextNum}_${slug}.md"
$filePath = "$notesDir\$fileName"

# Tanggal hari ini
$today = Get-Date -Format "yyyy-MM-dd"

# Template isi
$template = @"
# $Topik

> Dibuat: $today via sidix-learn
> Topik: $Topik

$IsiAwal

---

## Apa

[Jelaskan konsep/teknologi/metode ini]

## Mengapa

[Kenapa ini penting? Masalah apa yang dipecahkan?]

## Bagaimana

[Langkah-langkah, cara kerja, implementasi]

## Contoh Nyata

[Contoh konkret dari pengalaman proyek SIDIX]

## Keterbatasan

[Apa yang tidak bisa dilakukan, trade-off, kapan tidak digunakan]

## Referensi

-
"@

# Tulis file
$template | Out-File -FilePath $filePath -Encoding utf8

Write-Host "✅ Research note dibuat: $filePath" -ForegroundColor Green
Write-Host "📝 Edit file, lalu jalankan:" -ForegroundColor Yellow
Write-Host "   git add $filePath && git commit -m 'doc: research note $nextNum — $Topik'" -ForegroundColor Cyan
