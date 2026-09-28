"""Bước 3 - Lớp Silver và các phân vùng Gold theo tháng (xử lý tăng dần).

Mỗi lần chạy xử lý một cặp (dịch vụ, tháng):
  1. Đọc tệp Bronze, chuẩn hóa lược đồ chung cho HVFHV và Yellow Taxi.
  2. Gắn cờ chất lượng cho từng chuyến và đếm số chuyến vi phạm từng quy tắc.
  3. Ghi các chuyến hợp lệ ra Silver (Parquet ZSTD, phân vùng
     service=/year=/month=).
  4. Từ Silver, tính các bảng tổng hợp Gold của tháng đó.
Thiết kế theo tháng giúp pipeline chạy lại được từng phần (idempotent)
và chạy được trên máy chỉ có khoảng 3 GB RAM.

Chạy:  python code/03_silver_gold_month.py hvfhv 2024-01 0   (khúc 0 của tháng)
       python code/03_silver_gold_month.py all              (chạy hết mọi phân vùng còn thiếu)
       python code/03_silver_gold_month.py ext              (giai đoạn mở rộng 2022–2023)
"""
import json
import os
import sys
import time

from config import (CLEAN, GOLD, LOG, MONTHS, MONTHS_EXT, SERVICES, SEED, duck,
                    gold_part, is_ext, raw_file, silver_file)


def month_bounds(ym):
    y, m = map(int, ym.split("-"))
    ny, nm = (y + 1, 1) if m == 12 else (y, m + 1)
    return f"{y}-{m:02d}-01", f"{ny}-{nm:02d}-01"


def std_select(svc, f, ym):
    """Chuẩn hóa về lược đồ chung. Cột không có ở một nguồn được gán NULL/0."""
    has_cbd = ym >= "2025-01"
    # 0.0::DOUBLE (không phải hằng số DECIMAL) để mọi phân vùng có cùng kiểu cột phí (xem mục 5.2 của báo cáo)
    cbd = "coalesce(cbd_congestion_fee,0)" if has_cbd else "0.0::DOUBLE"
    if svc == "hvfhv":
        return f"""
        SELECT 'hvfhv' AS service, hvfhs_license_num AS company_code,
               request_datetime AS request_ts, pickup_datetime AS pickup_ts,
               dropoff_datetime AS dropoff_ts, PULocationID::INTEGER AS pu, DOLocationID::INTEGER AS dl,
               trip_miles AS miles, trip_time::DOUBLE AS time_s,
               base_passenger_fare AS fare, coalesce(tolls,0) AS tolls,
               coalesce(bcf,0) AS bcf, coalesce(sales_tax,0) AS tax,
               coalesce(congestion_surcharge,0) AS cong_sur,
               coalesce(airport_fee,0) AS airport_fee, {cbd} AS cbd_fee,
               coalesce(tips,0) AS tips, driver_pay,
               (shared_request_flag = 'Y')::INT AS shared_req,
               (shared_match_flag = 'Y')::INT AS shared_match,
               (wav_request_flag = 'Y')::INT AS wav_req,
               NULL::DOUBLE AS total_amount, NULL::INT AS payment_type
        FROM read_parquet('{f}')"""
    return f"""
        SELECT 'yellow' AS service, 'YELLOW' AS company_code,
               NULL::TIMESTAMP AS request_ts, tpep_pickup_datetime AS pickup_ts,
               tpep_dropoff_datetime AS dropoff_ts, PULocationID::INTEGER AS pu, DOLocationID::INTEGER AS dl,
               trip_distance AS miles,
               date_diff('second', tpep_pickup_datetime, tpep_dropoff_datetime)::DOUBLE AS time_s,
               fare_amount AS fare, coalesce(tolls_amount,0) AS tolls, 0.0 AS bcf,
               coalesce(mta_tax,0) AS tax, coalesce(congestion_surcharge,0) AS cong_sur,
               coalesce(Airport_fee,0) AS airport_fee, {cbd} AS cbd_fee,
               coalesce(tip_amount,0) AS tips, NULL::DOUBLE AS driver_pay,
               0 AS shared_req, 0 AS shared_match, 0 AS wav_req,
               total_amount, payment_type::INT AS payment_type
        FROM read_parquet('{f}')"""


def chunk_filter(ym, k, n):
    """Chia một tháng thành n khúc theo ngày đón khách để mỗi lần xử lý vừa bộ nhớ.
    Khúc cuối nhận thêm các dòng có thời điểm ngoài tháng/NULL để chúng vẫn được gắn cờ."""
    lo, hi = month_bounds(ym)
    if n == 1:
        return "TRUE"
    y, m = map(int, ym.split("-"))
    step = {4: 8, 6: 5}.get(n, 28 // n)   # 4 khúc: ngày 1, 9, 17, 25; 6 khúc: ngày 1, 6, 11, 16, 21, 26
    cuts = [f"{y}-{m:02d}-{1 + step * i:02d}" for i in range(n)] + [hi]
    a, b = cuts[k], cuts[k + 1]
    if k < n - 1:
        return f"pickup_ts >= TIMESTAMP '{a}' AND pickup_ts < TIMESTAMP '{b}'"
    return f"(pickup_ts IS NULL OR pickup_ts >= TIMESTAMP '{a}' OR pickup_ts < TIMESTAMP '{lo}')"


N_CHUNKS = {"hvfhv": 4, "yellow": 1}


def n_chunks_for(svc, ym):
    """Số khúc mỗi tháng. Từ HVFHV 08/2022 của giai đoạn mở rộng dùng 6 khúc để mỗi khúc chắc chắn
    xong trong giới hạn thời gian của môi trường chạy (máy đồng thời đang tải dữ liệu)."""
    if svc == "hvfhv" and is_ext(ym) and ym >= "2022-08":
        return 6
    return N_CHUNKS[svc]


def run(svc, ym, k=0):
    t0 = time.time()
    n_chunks = n_chunks_for(svc, ym)
    tag = f"{svc}_{ym}_c{k}"
    con = duck()
    lo, hi = month_bounds(ym)
    f = raw_file(svc, ym).as_posix()
    dim = (GOLD / "dim_zone.parquet").as_posix()
    c = CLEAN
    con.execute(f"CREATE TEMP TABLE z AS SELECT LocationID, grp FROM '{dim}'")
    con.execute(f"CREATE TEMP VIEW std AS SELECT * FROM ({std_select(svc, f, ym)}) "
                f"WHERE {chunk_filter(ym, k, n_chunks)}")
    # Cờ chất lượng: mỗi quy tắc một cột 0/1
    con.execute(f"""
    CREATE TEMP VIEW flagged AS
    SELECT *,
      (pickup_ts < TIMESTAMP '{lo}' OR pickup_ts >= TIMESTAMP '{hi}' OR pickup_ts IS NULL)::INT AS q_out_of_month,
      (pu IS NULL OR dl IS NULL OR pu NOT BETWEEN 1 AND 263 OR dl NOT BETWEEN 1 AND 263)::INT AS q_bad_zone,
      (miles IS NULL OR miles <= {c['min_miles']} OR miles > {c['max_miles']})::INT AS q_bad_miles,
      (time_s IS NULL OR time_s < {c['min_time_s']} OR time_s > {c['max_time_s']})::INT AS q_bad_time,
      (fare IS NULL OR fare <= {c['min_fare']} OR fare > {c['max_fare']})::INT AS q_bad_fare,
      (CASE WHEN time_s > 0 AND miles / (time_s/3600.0) > {c['max_speed_mph']} THEN 1 ELSE 0 END) AS q_bad_speed,
      (CASE WHEN service='hvfhv' AND (driver_pay IS NULL OR driver_pay < 0) THEN 1 ELSE 0 END) AS q_bad_pay
    FROM std""")
    q = con.execute("""
    SELECT count(*) n_raw, sum(q_out_of_month) q_out_of_month, sum(q_bad_zone) q_bad_zone,
           sum(q_bad_miles) q_bad_miles, sum(q_bad_time) q_bad_time, sum(q_bad_fare) q_bad_fare,
           sum(q_bad_speed) q_bad_speed, sum(q_bad_pay) q_bad_pay,
           sum(CASE WHEN q_out_of_month+q_bad_zone+q_bad_miles+q_bad_time+q_bad_fare+q_bad_speed+q_bad_pay>0
               THEN 1 ELSE 0 END) n_rejected
    FROM flagged""").df().iloc[0].to_dict()
    q = {k: int(v) for k, v in q.items()}
    t_quality = time.time() - t0

    # Giai đoạn mở rộng từ HVFHV 08/2022: không ghi lớp Silver xuống đĩa (Bronze vẫn giữ nguyên nên dựng lại
    # được bất cứ lúc nào); bảng chuyến đã làm sạch chỉ nằm trong bộ nhớ DuckDB để tính các phân vùng Gold.
    persist = not (is_ext(ym) and (svc == "yellow" or ym >= "2022-08"))
    silver_sql = f"""
      SELECT f.service, f.company_code, f.request_ts, f.pickup_ts, f.dropoff_ts, f.pu, f.dl,
             f.miles, f.time_s, f.fare, f.tolls, f.bcf, f.tax, f.cong_sur, f.airport_fee, f.cbd_fee,
             f.tips, f.driver_pay, f.shared_req, f.shared_match, f.wav_req, f.total_amount, f.payment_type,
             CAST(f.pickup_ts AS DATE) AS d, hour(f.pickup_ts)::TINYINT AS hr,
             isodow(f.pickup_ts)::TINYINT AS dow,
             CASE WHEN f.request_ts IS NOT NULL
                   AND date_diff('second', f.request_ts, f.pickup_ts) BETWEEN 0 AND {c['max_wait_min']*60}
                  THEN date_diff('second', f.request_ts, f.pickup_ts)/60.0 END AS wait_min,
             f.miles / (f.time_s/3600.0) AS mph,
             zp.grp AS pu_grp, zd.grp AS do_grp,
             (zp.grp='CRZ' OR zd.grp='CRZ')::INT AS touch_crz,
             f.fare + f.tolls + f.bcf + f.tax + f.cong_sur + f.airport_fee + f.cbd_fee AS rider_cost
      FROM flagged f
      LEFT JOIN z zp ON f.pu = zp.LocationID
      LEFT JOIN z zd ON f.dl = zd.LocationID
      WHERE q_out_of_month+q_bad_zone+q_bad_miles+q_bad_time+q_bad_fare+q_bad_speed+q_bad_pay = 0
"""
    if persist:
        sf = silver_file(svc, ym).with_name(f"part-{k}.parquet").as_posix()
        con.execute(f"COPY ({silver_sql}) TO '{sf}' (FORMAT PARQUET, COMPRESSION ZSTD, ROW_GROUP_SIZE 1000000)")
        t_silver = time.time() - t0
        con.execute(f"CREATE TEMP VIEW s AS SELECT * FROM read_parquet('{sf}')")
    else:
        sf = None
        con.execute(f"CREATE TEMP TABLE s AS {silver_sql}")
        t_silver = time.time() - t0
    sums = """count(*) AS n, sum(fare) AS fare, sum(driver_pay) AS pay, sum(miles) AS miles,
              sum(time_s) AS time_s, sum(tips) AS tips, sum(cbd_fee) AS cbd, sum(rider_cost) AS rider_cost,
              sum(cong_sur) AS cong_sur, sum(tolls) AS tolls, sum(wait_min) AS wait_sum,
              count(wait_min) AS wait_n, sum(shared_req) AS shared_req, sum((cbd_fee>0)::INT) AS n_cbd"""
    gold = {
        "zone_day_pu": f"""SELECT service, d, pu AS zone, {sums},
                  sum((do_grp='CRZ')::INT) AS n_to_crz,
                  sum((company_code='HV0003')::INT) AS n_uber, sum((company_code='HV0005')::INT) AS n_lyft
                  FROM s GROUP BY ALL""",
        "zone_day_do": f"""SELECT service, d, dl AS zone, {sums},
                  sum((pu_grp='CRZ')::INT) AS n_from_crz FROM s GROUP BY ALL""",
        "grp_hour_day": f"""SELECT service, d, hr, pu_grp, do_grp, {sums} FROM s GROUP BY ALL""",
        "company_grp_day": f"""SELECT service, company_code, d, pu_grp, do_grp, {sums} FROM s GROUP BY ALL""",
        "zone_hour_month": f"""SELECT service, '{ym}' AS ym, pu AS zone, hr, {sums} FROM s GROUP BY ALL""",
        "od_month": f"""SELECT service, '{ym}' AS ym, pu, dl, {sums} FROM s GROUP BY ALL""",
        "trip_sample": f"""SELECT * FROM s USING SAMPLE {0.25 if svc == 'hvfhv' else 1.0}% (bernoulli, {SEED})""",
    }
    for name, sql in gold.items():
        gp = gold_part(name, svc, ym + "_c" + str(k)).as_posix()
        con.execute(f"COPY ({sql}) TO '{gp}' (FORMAT PARQUET, COMPRESSION ZSTD)")
    t_gold = time.time() - t0
    n_silver = con.execute("SELECT count(*) FROM s").fetchone()[0]
    rec = dict(service=svc, month=ym, chunk=k, **q, n_silver=int(n_silver),
               sec_quality=round(t_quality, 1), sec_silver=round(t_silver - t_quality, 1),
               sec_gold=round(t_gold - t_silver, 1), sec_total=round(t_gold, 1),
               silver_mb=round(os.path.getsize(sf) / 2**20, 1) if sf else 0.0, silver_persisted=bool(sf))
    plog = LOG / ("partitions_ext" if is_ext(ym) else "partitions")
    plog.mkdir(exist_ok=True)
    (plog / f"{tag}.json").write_text(json.dumps(rec, indent=2))
    print(json.dumps(rec), flush=True)


if __name__ == "__main__":
    if sys.argv[1] in ("all", "ext"):
        months = MONTHS_EXT if sys.argv[1] == "ext" else MONTHS
        plog = LOG / ("partitions_ext" if sys.argv[1] == "ext" else "partitions")
        # Tùy chọn: giới hạn thời gian mỗi lần gọi (giây), dùng khi môi trường giới hạn thời gian lệnh
        budget = float(sys.argv[2]) if len(sys.argv) > 2 else float("inf")
        start = time.time()
        for s in SERVICES:
            for m in months:
                rf = raw_file(s, m)
                # Bỏ qua tệp chưa tải hoặc đang được tải (sửa đổi trong 2 phút gần nhất)
                if not rf.exists() or time.time() - rf.stat().st_mtime < 120:
                    continue
                for k in range(n_chunks_for(s, m)):
                    if not (plog / f"{s}_{m}_c{k}.json").exists():
                        est = (80 if n_chunks_for(s, m) == 4 else 45) if s == "hvfhv" else 30
                        if time.time() - start + est > budget:
                            sys.exit(0)
                        run(s, m, k)
    else:
        run(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 0)
