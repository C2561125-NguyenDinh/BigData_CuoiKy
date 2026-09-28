"""Bước 4 - Hợp nhất các phân vùng Gold theo tháng thành bảng Gold cuối.

Các bảng tổng hợp ở bước 3 được ghi theo từng khúc (chunk) của từng tháng.
Vì mọi chỉ tiêu đều là tổng (count, sum), việc hợp nhất chỉ là cộng dồn,
không làm mất thông tin. Bước này cũng tổng hợp nhật ký chất lượng dữ liệu.

Chạy:  python code/04_gold_consolidate.py        (bảng Gold chính 2024–2025)
       python code/04_gold_consolidate.py ext    (bảng Gold dài 2022–2025 trong data/gold/long/, không đụng bảng chính)
"""
import sys
import json
import time

import pandas as pd

from config import GOLD, LOG, TAB, duck

t0 = time.time()
con = duck()
EXT = len(sys.argv) > 1 and sys.argv[1] == "ext"
parts = GOLD / "_parts"
OUTDIR = GOLD / "long" if EXT else GOLD
OUTDIR.mkdir(exist_ok=True)
SFX = "x" if EXT else ""
SUM_COLS = ("n, fare, pay, miles, time_s, tips, cbd, rider_cost, cong_sur, tolls, "
            "wait_sum, wait_n, shared_req, n_cbd")


def sums(extra=""):
    cols = [c.strip() for c in (SUM_COLS + ("," + extra if extra else "")).split(",")]
    return ", ".join(f"sum({c})::DOUBLE AS {c}" for c in cols)


specs = {
    "zone_day_pu": ("service, d, zone", sums("n_to_crz, n_uber, n_lyft")),
    "zone_day_do": ("service, d, zone", sums("n_from_crz")),
    "grp_hour_day": ("service, d, hr, pu_grp, do_grp", sums()),
    "company_grp_day": ("service, company_code, d, pu_grp, do_grp", sums()),
    "zone_hour_month": ("service, ym, zone, hr", sums()),
    "od_month": ("service, ym, pu, dl", sums()),
}
info = {}
# Tùy chọn: chỉ hợp nhất một số bảng (python 04_gold_consolidate.py ext od_month,trip_sample,quality)
ONLY = set(sys.argv[2].split(",")) if len(sys.argv) > 2 else None
for name, (keys, agg) in specs.items():
    if ONLY and name not in ONLY:
        continue
    src = (parts / name / "*_c*.parquet").as_posix()
    if EXT:
        src = [src, (GOLD / "_parts_ext" / name / "*_c*.parquet").as_posix()]
    dst = (OUTDIR / f"{name}.parquet").as_posix()
    # union_by_name=true: hợp nhất lược đồ theo tên cột và nâng kiểu lên kiểu rộng nhất.
    # Không có tùy chọn này DuckDB lấy lược đồ của tệp đầu tiên (HVFHV 01/2024, cột cbd kiểu
    # DECIMAL(38,1)) và ép các tệp sau về kiểu đó, làm tròn tổng phí 0,75 USD của taxi vàng.
    # Lỗi này được phát hiện khi đối chứng chéo với bản tái lập bằng Spark (bước 15).
    srcx = f"'{src}'" if isinstance(src, str) else "[" + ", ".join(f"'{x}'" for x in src) + "]"
    con.execute(f"COPY (SELECT {keys}, {agg} FROM read_parquet({srcx}, union_by_name=true) GROUP BY ALL ORDER BY ALL) "
                f"TO '{dst}' (FORMAT PARQUET, COMPRESSION ZSTD)")
    info[name] = con.execute(f"SELECT count(*) FROM '{dst}'").fetchone()[0]
    print(name, info[name], flush=True)

if ONLY and "trip_sample" not in ONLY:
    src = None
else:
    src = (parts / "trip_sample" / "*_c*.parquet").as_posix()
if EXT and src:
    src = (GOLD / "_parts_ext" / "trip_sample" / "*_c*.parquet").as_posix()
if src:
    con.execute(f"COPY (SELECT * FROM read_parquet('{src}', union_by_name=true)) TO '{(OUTDIR / 'trip_sample.parquet').as_posix()}' "
                "(FORMAT PARQUET, COMPRESSION ZSTD)")
    info["trip_sample"] = con.execute(f"SELECT count(*) FROM '{(OUTDIR / 'trip_sample.parquet').as_posix()}'").fetchone()[0]

# Nhật ký chất lượng dữ liệu theo tháng
recs = [json.loads(p.read_text()) for p in sorted((LOG / ("partitions_ext" if EXT else "partitions")).glob("*_c*.json"))]
q = pd.DataFrame(recs)
qm = q.groupby(["service", "month"]).agg(
    n_raw=("n_raw", "sum"), q_out_of_month=("q_out_of_month", "sum"), q_bad_zone=("q_bad_zone", "sum"),
    q_bad_miles=("q_bad_miles", "sum"), q_bad_time=("q_bad_time", "sum"), q_bad_fare=("q_bad_fare", "sum"),
    q_bad_speed=("q_bad_speed", "sum"), q_bad_pay=("q_bad_pay", "sum"), n_rejected=("n_rejected", "sum"),
    n_silver=("n_silver", "sum"), silver_mb=("silver_mb", "sum"), sec_quality=("sec_quality", "sum"),
    sec_silver=("sec_silver", "sum"), sec_gold=("sec_gold", "sum"), sec_total=("sec_total", "sum"),
    chunks=("chunk", "count")).reset_index()
qm["reject_pct"] = 100 * qm.n_rejected / qm.n_raw
qm.to_csv(TAB / f"t06{SFX}_quality_by_month.csv", index=False)
qs = qm.groupby("service").sum(numeric_only=True).reset_index()
qs["reject_pct"] = 100 * qs.n_rejected / qs.n_raw
qs.to_csv(TAB / f"t07{SFX}_quality_summary.csv", index=False)
q.to_csv(TAB / f"t08{SFX}_partition_runtime.csv", index=False)
(LOG / f"04_gold_consolidate{'_ext' if EXT else ''}.json").write_text(json.dumps(dict(
    seconds=round(time.time() - t0, 1), rows=info), indent=2, default=int))
print(qs.T)
print("time", round(time.time() - t0, 1))
