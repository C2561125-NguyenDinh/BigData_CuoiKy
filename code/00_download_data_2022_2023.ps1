# Tai du lieu bo sung 2022-2023 (HVFHV + taxi vang) cho giai doan truoc chinh sach dai hon
# Chay:  powershell -ExecutionPolicy Bypass -File code\00_download_data_2022_2023.ps1
# Khoang 48 tep, ~12 GB. Bo qua tep da tai du; tu thu lai va tai tiep khi mat mang.
$dst = Join-Path (Split-Path $PSScriptRoot -Parent) "data\raw"
New-Item -ItemType Directory -Force -Path $dst | Out-Null
$base = "https://d37ci6vzurychx.cloudfront.net/trip-data"
$urls = @()
foreach ($y in 2022, 2023) { foreach ($m in 1..12) {
  $ym = "{0}-{1:D2}" -f $y, $m
  $urls += "$base/fhvhv_tripdata_$ym.parquet"
  $urls += "$base/yellow_tripdata_$ym.parquet"
}}
$i = 0
foreach ($u in $urls) {
  $i++
  $f = Join-Path $dst (Split-Path $u -Leaf)
  if ((Test-Path $f) -and (Get-Item $f).Length -gt 1MB) { continue }
  Write-Host ("[{0}/{1}] Tai {2}" -f $i, $urls.Count, $u)
  curl.exe -L --fail --retry 5 --retry-delay 5 -C - -o $f $u
  if ($LASTEXITCODE -ne 0) { Write-Host "  LOI: $u" -ForegroundColor Red }
}
$n = (Get-ChildItem $dst -Filter "*_tripdata_202[23]-*.parquet").Count
Write-Host "Xong. So tep 2022-2023 da co: $n / 48"
