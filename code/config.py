"""Cấu hình chung cho toàn bộ pipeline đồ án.

Mọi đường dẫn đều tính tương đối so với thư mục gốc của đồ án
(thư mục cha của thư mục code/), vì vậy có thể chép nguyên thư mục
CongestionPricing_CaseStudy sang máy khác và chạy lại.
"""
from pathlib import Path
import datetime as dt

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
BRONZE = ROOT / "data" / "bronze"
SILVER = ROOT / "data" / "silver"
GOLD = ROOT / "data" / "gold"
OUT = ROOT / "outputs"
FIG = OUT / "figures"
TAB = OUT / "tables"
LOG = OUT / "logs"
for p in (BRONZE, SILVER, GOLD, FIG, TAB, LOG):
    p.mkdir(parents=True, exist_ok=True)

# Giai đoạn nghiên cứu: 24 tháng, 12 tháng trước và 12 tháng sau chính sách
MONTHS = [f"{y}-{m:02d}" for y in (2024, 2025) for m in range(1, 13)]
# Giai đoạn trước chính sách mở rộng (bước 03 ext, 04 ext, 19): chỉ dùng cho các phân tích dài hạn,
# không làm thay đổi các bảng Gold chính của giai đoạn 2024–2025.
MONTHS_EXT = [f"{y}-{m:02d}" for y in (2022, 2023) for m in range(1, 13)]


def is_ext(ym: str) -> bool:
    return ym[:4] in ("2022", "2023")
SERVICES = ("hvfhv", "yellow")

# Ngày bắt đầu thu phí vùng giảm ùn tắc (Congestion Relief Zone toll)
POLICY_DATE = dt.date(2025, 1, 5)
POLICY_TS = "2025-01-05 00:00:00"

# Mã giấy phép của các hãng gọi xe (High Volume For-Hire Services)
HVFHS_COMPANY = {"HV0002": "Juno", "HV0003": "Uber", "HV0004": "Via", "HV0005": "Lyft"}

# Ngưỡng làm sạch dữ liệu (áp dụng ở lớp Silver)
CLEAN = dict(
    min_miles=0.0,          # quãng đường phải > 0
    max_miles=100.0,        # loại chuyến > 100 dặm
    min_time_s=60,          # loại chuyến < 1 phút
    max_time_s=4 * 3600,    # loại chuyến > 4 giờ
    max_speed_mph=80.0,     # loại chuyến có tốc độ trung bình > 80 mph
    min_fare=0.0,           # giá cước phải > 0
    max_fare=1000.0,        # loại giá cước > 1000 USD
    max_wait_min=120.0,     # thời gian chờ hợp lệ 0..120 phút
)

# Ngưỡng phân loại vùng theo tỷ lệ chuyến nội vùng bị thu phí CBD
CRZ_FULL_SHARE = 0.90       # >= 90%: vùng nằm trọn trong vùng thu phí
CRZ_PARTIAL_SHARE = 0.10    # 10%..90%: vùng nằm vắt qua ranh giới
AIRPORT_ZONES = (1, 132, 138)   # EWR, JFK, LaGuardia

DUCKDB_SETTINGS = {"memory_limit": "1800MB", "threads": 2,
                   "preserve_insertion_order": False}
SEED = 20250105


def duck():
    """Tạo kết nối DuckDB với cấu hình giới hạn bộ nhớ (chạy được trên máy RAM thấp)."""
    import duckdb
    con = duckdb.connect()
    for k, v in DUCKDB_SETTINGS.items():
        con.execute(f"SET {k}='{v}'" if isinstance(v, str) else f"SET {k}={v}")
    import os
    # Thư mục tràn đĩa của DuckDB; có thể trỏ ra ổ cục bộ bằng DUCKDB_TMP nếu thư mục dự án không cho xóa tệp.
    tmp = Path(os.environ.get("DUCKDB_TMP", ROOT / "data" / "_duckdb_tmp"))
    tmp.mkdir(exist_ok=True)
    con.execute(f"SET temp_directory='{tmp.as_posix()}'")
    return con


def raw_file(service: str, ym: str) -> Path:
    name = "fhvhv" if service == "hvfhv" else "yellow"
    return RAW / f"{name}_tripdata_{ym}.parquet"


def silver_file(service: str, ym: str) -> Path:
    y, m = ym.split("-")
    p = SILVER / f"service={service}" / f"year={y}" / f"month={m}"
    p.mkdir(parents=True, exist_ok=True)
    return p / "part-0.parquet"


def gold_part(table: str, service: str, ym: str) -> Path:
    p = GOLD / ("_parts_ext" if is_ext(ym) else "_parts") / table
    p.mkdir(parents=True, exist_ok=True)
    return p / f"{service}_{ym}.parquet"
