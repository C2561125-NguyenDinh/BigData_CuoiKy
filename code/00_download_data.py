"""Bước 0 - Tải dữ liệu thô từ NYC TLC về data/raw (bỏ qua tệp đã có).

Nguồn: https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page
Tệp: fhvhv_tripdata_YYYY-MM.parquet và yellow_tripdata_YYYY-MM.parquet
     cho 01/2024–12/2025, cùng taxi_zone_lookup.csv và taxi_zones.zip.
Tổng dung lượng khoảng 12,6 GB.

Chạy:  python code/00_download_data.py
"""
import urllib.request

from config import MONTHS, RAW

BASE = "https://d37ci6vzurychx.cloudfront.net"
urls = [f"{BASE}/misc/taxi_zone_lookup.csv", f"{BASE}/misc/taxi_zones.zip"]
for ym in MONTHS:
    urls += [f"{BASE}/trip-data/fhvhv_tripdata_{ym}.parquet", f"{BASE}/trip-data/yellow_tripdata_{ym}.parquet"]

RAW.mkdir(parents=True, exist_ok=True)
for u in urls:
    dst = RAW / u.rsplit("/", 1)[-1]
    if dst.exists() and dst.stat().st_size > 0:
        continue
    print("Tải", u, flush=True)
    tmp = dst.with_suffix(dst.suffix + ".part")
    urllib.request.urlretrieve(u, tmp)
    tmp.rename(dst)
print("Đủ", len(list(RAW.glob('*.parquet'))), "tệp parquet")
