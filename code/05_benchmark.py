"""Bước 5 - Thực nghiệm hiệu năng lưu trữ và xử lý.

Đo trên chính dữ liệu của đồ án (không dùng số liệu tham khảo bên ngoài):
  (a) Định dạng lưu trữ: CSV, CSV nén gzip, Parquet Snappy, Parquet ZSTD
      cho cùng một lát cắt dữ liệu HVFHV (kích thước tệp, thời gian ghi, đọc).
  (b) Bộ máy xử lý: DuckDB, Pandas, PyArrow cho cùng một truy vấn tổng hợp
      (doanh thu và số chuyến theo vùng đón) trên một tháng dữ liệu đầy đủ.
  (c) Cắt tỉa cột (column pruning) và đẩy điều kiện lọc xuống (predicate
      pushdown) trong DuckDB.
Mỗi phép đo chạy trong tiến trình con riêng để đo bộ nhớ đỉnh (max RSS).

Chạy:  python code/05_benchmark.py [part]   với part ∈ {format, engine, pruning}
"""
import json
import subprocess
import sys
import textwrap

import pandas as pd

from config import ROOT, TAB, LOG, raw_file

BENCH = ROOT / "data" / "_bench"
BENCH.mkdir(exist_ok=True)
MONTH = "2024-03"
SRC = raw_file("hvfhv", MONTH).as_posix()
SLICE_ROWS = 2_000_000
REPEAT = 3


def child(code):
    """Chạy đoạn mã trong tiến trình con; trả về dict kết quả và max RSS (MB)."""
    wrapper = textwrap.dedent(f"""
import json, resource, time
t0 = time.perf_counter()
{textwrap.dedent(code)}
el = time.perf_counter() - t0
rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
print(json.dumps(dict(seconds=el, max_rss_mb=rss, **(extra if 'extra' in dir() else {{}}))))
""")
    out = subprocess.run([sys.executable, "-c", wrapper], capture_output=True, text=True, cwd=str(ROOT / "code"))
    if out.returncode != 0:
        raise RuntimeError(out.stderr[-2000:])
    return json.loads(out.stdout.strip().splitlines()[-1])


def part_format():
    base = (BENCH / "slice").as_posix()
    rows = []
    prep = f"""
import duckdb
con = duckdb.connect(); con.execute("SET threads=2")
con.execute("CREATE TABLE t AS SELECT * FROM '{SRC}' LIMIT {SLICE_ROWS}")
"""
    writes = {
        "CSV": f"COPY t TO '{base}.csv' (HEADER)",
        "CSV.gz": f"COPY t TO '{base}.csv.gz' (HEADER, COMPRESSION gzip)",
        "Parquet Snappy": f"COPY t TO '{base}_snappy.parquet' (FORMAT PARQUET, COMPRESSION SNAPPY)",
        "Parquet ZSTD": f"COPY t TO '{base}_zstd.parquet' (FORMAT PARQUET, COMPRESSION ZSTD)",
    }
    files = {"CSV": f"{base}.csv", "CSV.gz": f"{base}.csv.gz",
             "Parquet Snappy": f"{base}_snappy.parquet", "Parquet ZSTD": f"{base}_zstd.parquet"}
    for fmt, sql in writes.items():
        r = child(prep + f"""
t1 = time.perf_counter(); con.execute("{sql}"); w = time.perf_counter() - t1
import os; extra = dict(write_s=w, size_mb=os.path.getsize('{files[fmt]}')/2**20)
""")
        reader = (f"read_csv('{files[fmt]}', header=true)" if fmt.startswith("CSV") else f"'{files[fmt]}'")
        reads = []
        for _ in range(REPEAT):
            rr = child(f"""
import duckdb
con = duckdb.connect(); con.execute("SET threads=2")
res = con.execute("SELECT PULocationID, count(*), sum(base_passenger_fare) FROM {reader} GROUP BY 1").fetchall()
extra = dict(groups=len(res))
""")
            reads.append(rr["seconds"])
        rows.append(dict(format=fmt, rows=SLICE_ROWS, size_mb=r["size_mb"], write_s=r["write_s"],
                         agg_query_s_median=sorted(reads)[1], agg_query_s_min=min(reads),
                         agg_query_s_max=max(reads)))
        print(rows[-1], flush=True)
    df = pd.DataFrame(rows)
    df["size_ratio_vs_csv"] = df.size_mb / df.loc[df.format == "CSV", "size_mb"].iloc[0]
    df.to_csv(TAB / "t09_bench_format.csv", index=False)


QUERY_DESC = "Số chuyến, tổng giá cước, tổng thu nhập tài xế theo vùng đón (1 tháng HVFHV đầy đủ)"


def part_engine():
    codes = {
        "DuckDB (SQL)": f"""
import duckdb
con = duckdb.connect(); con.execute("SET threads=2")
res = con.execute("SELECT PULocationID, count(*), sum(base_passenger_fare), sum(driver_pay) FROM '{SRC}' GROUP BY 1").df()
extra = dict(groups=len(res))
""",
        "Pandas (read_parquet 3 cột + groupby)": f"""
import pandas as pd
df = pd.read_parquet('{SRC}', columns=['PULocationID','base_passenger_fare','driver_pay'])
res = df.groupby('PULocationID').agg(n=('base_passenger_fare','size'), fare=('base_passenger_fare','sum'), pay=('driver_pay','sum'))
extra = dict(groups=len(res))
""",
        "PyArrow (dataset + group_by)": f"""
import pyarrow.parquet as pq
t = pq.read_table('{SRC}', columns=['PULocationID','base_passenger_fare','driver_pay'])
res = t.group_by('PULocationID').aggregate([('base_passenger_fare','count'),('base_passenger_fare','sum'),('driver_pay','sum')])
extra = dict(groups=res.num_rows)
""",
    }
    rows = []
    for eng, code in codes.items():
        rs = [child(code) for _ in range(REPEAT)]
        secs = sorted(r["seconds"] for r in rs)
        rows.append(dict(engine=eng, query=QUERY_DESC, month=MONTH, seconds_median=secs[1],
                         seconds_min=secs[0], seconds_max=secs[-1],
                         max_rss_mb=max(r["max_rss_mb"] for r in rs), groups=rs[0]["groups"]))
        print(rows[-1], flush=True)
    pd.DataFrame(rows).to_csv(TAB / "t10_bench_engine.csv", index=False)


def part_pruning():
    tests = {
        "Đọc 2 cột, không lọc": f"SELECT count(*), sum(base_passenger_fare), sum(trip_miles) FROM '{SRC}'",
        "Đọc toàn bộ 24 cột (max từng cột)": f"SELECT max(COLUMNS(*)) FROM '{SRC}'",
        "2 cột + lọc 1 ngày (pushdown theo min/max row group)": f"SELECT count(*), sum(base_passenger_fare) FROM '{SRC}' WHERE pickup_datetime >= TIMESTAMP '{MONTH}-15' AND pickup_datetime < TIMESTAMP '{MONTH}-16'",
        "2 cột + lọc theo vùng (không sắp xếp theo vùng)": f"SELECT count(*), sum(base_passenger_fare) FROM '{SRC}' WHERE PULocationID = 161",
    }
    rows = []
    for name, sql in tests.items():
        rs = []
        for _ in range(REPEAT):
            rs.append(child(f"""
import duckdb
con = duckdb.connect(); con.execute("SET threads=2"); con.execute("PRAGMA enable_profiling='no_output'")
res = con.execute(\"\"\"{sql}\"\"\").fetchall()
extra = dict(result=str(res[0][0]))
"""))
        secs = sorted(r["seconds"] for r in rs)
        rows.append(dict(test=name, seconds_median=secs[1], seconds_min=secs[0], seconds_max=secs[-1],
                         max_rss_mb=max(r["max_rss_mb"] for r in rs), first_value=rs[0]["result"]))
        print(rows[-1], flush=True)
    import pyarrow.parquet as pq
    md = pq.ParquetFile(SRC).metadata
    rg = []
    for i in range(md.num_row_groups):
        st = md.row_group(i).column(5).statistics
        rg.append(dict(row_group=i, rows=md.row_group(i).num_rows,
                       min_pickup=str(st.min) if st else None, max_pickup=str(st.max) if st else None))
    pd.DataFrame(rg).to_csv(TAB / "t12_rowgroup_stats.csv", index=False)
    pd.DataFrame(rows).to_csv(TAB / "t11_bench_pruning.csv", index=False)


if __name__ == "__main__":
    part = sys.argv[1] if len(sys.argv) > 1 else "all"
    for p, fn in (("format", part_format), ("engine", part_engine), ("pruning", part_pruning)):
        if part in (p, "all"):
            fn()
    (LOG / f"05_benchmark_{part}.json").write_text(json.dumps(dict(done=part)))
