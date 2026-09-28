# Tải dữ liệu thô NYC TLC trên Windows PowerShell (bỏ qua tệp đã có)
# Chạy từ bất kỳ đâu:  powershell -ExecutionPolicy Bypass -File code\00_download_data.ps1
$dst = Join-Path (Split-Path $PSScriptRoot -Parent) "data\raw"
New-Item -ItemType Directory -Force -Path $dst | Out-Null
$base = "https://d37ci6vzurychx.cloudfront.net"
$urls = @("$base/misc/taxi_zone_lookup.csv", "$base/misc/taxi_zones.zip")
foreach ($y in 2024, 2025) { foreach ($m in 1..12) {
  $ym = "{0}-{1:D2}" -f $y, $m
  $urls += "$base/trip-data/fhvhv_tripdata_$ym.parquet"
  $urls += "$base/trip-data/yellow_tripdata_$ym.parquet"
}}
foreach ($u in $urls) {
  $f = Join-Path $dst (Split-Path $u -Leaf)
  if (-not (Test-Path $f)) { Write-Host "Tai $u"; curl.exe -L --fail -o $f $u }
}
