"""Bước 0b - Tải dữ liệu thô 2022–2023 (HVFHV và taxi vàng) cho giai đoạn trước chính sách mở rộng.

Bản Python đa nền tảng của 00_download_data_2022_2023.ps1 (Windows, macOS, Linux).
Tệp: fhvhv_tripdata_YYYY-MM.parquet và yellow_tripdata_YYYY-MM.parquet cho 01/2022–12/2023,
khoảng 48 tệp, 12 GB. Bỏ qua tệp đã tải đủ; tệp tải dở (.part) được tải lại từ đầu.

Chạy:  python code/00_download_data_2022_2023.py
"""
import time
import urllib.request

from config import MONTHS_EXT, RAW

BASE = "https://d37ci6vzurychx.cloudfront.net/trip-data"
RAW.mkdir(parents=True, exist_ok=True)
urls = [f"{BASE}/{svc}_tripdata_{ym}.parquet" for ym in MONTHS_EXT for svc in ("fhvhv", "yellow")]
for i, u in enumerate(urls, 1):
    dst = RAW / u.rsplit("/", 1)[-1]
    if dst.exists() and dst.stat().st_size > 1_000_000:
        continue
    print(f"[{i}/{len(urls)}] Tải {u}", flush=True)
    tmp = dst.with_suffix(dst.suffix + ".part")
    for attempt in range(5):
        try:
            urllib.request.urlretrieve(u, tmp)
            tmp.replace(dst)
            break
        except Exception as e:  # mạng chập chờn: thử lại sau 5 giây
            print("  lỗi:", e, "- thử lại", flush=True)
            time.sleep(5)
n = len(list(RAW.glob("*_tripdata_202[23]-*.parquet")))
print(f"Xong. Số tệp 2022–2023 đã có: {n} / 48")
