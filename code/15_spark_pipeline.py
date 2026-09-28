"""Bước 15 - Xử lý phân tán bằng Apache Spark (PySpark) trên cùng lớp Silver.

Mục đích: đối chứng bộ máy nhúng một nút (DuckDB) với bộ máy phân tán trong bộ nhớ
(Spark) trên chính dữ liệu của đồ án, và minh họa các cơ chế của Spark mà học phần đề cập:
đồ thị thực thi (DAG) và phả hệ (lineage), bộ tối ưu Catalyst, cắt tỉa phân vùng,
xáo trộn (shuffle), lưu đệm trong bộ nhớ, trao đổi dữ liệu qua Apache Arrow và
xử lý luồng có cấu trúc (Structured Streaming).

Các phần (mỗi phần ghi nhật ký JSON riêng vào outputs/logs/spark/):
  repro [giây]      Tái lập bảng Gold zone_day_pu bằng Spark cho cả 48 tháng-dịch vụ
                    (tăng dần, bỏ qua tháng đã làm, dừng khi hết ngân sách thời gian).
  validate          So khớp từng ô giữa bản Spark và bản DuckDB của zone_day_pu.
  engine <e>        Cùng một truy vấn trên một tháng HVFHV; e ∈ {duckdb, spark_df, spark_sql}.
  shuffle <p> [noaqe]  Spark với spark.sql.shuffle.partitions = p (tùy chọn tắt AQE).
  scale <e> <k>     Truy vấn trên k tháng HVFHV đầu tiên của năm 2025 với bộ máy e.
  cache             Ba truy vấn lặp lại trước và sau khi lưu đệm DataFrame.
  prune             Cắt tỉa phân vùng kiểu Hive trên toàn bộ lớp Silver; lưu kế hoạch vật lý.
  arrow             Chuyển kết quả Spark sang pandas có và không có Apache Arrow.
  stream_prep       Tách hai tuần quanh ngày 05/01/2025 thành các tệp theo ngày.
  stream            Structured Streaming: mỗi tệp một lô vi mô, cửa sổ 1 giờ theo nhóm vùng.
  report            Tổng hợp nhật ký thành bảng t60–t67 và hình f42–f46.

Chạy:  python code/15_spark_pipeline.py <phần> [tham số]
Yêu cầu: Java 11+, pyspark 3.5.
"""
import json
import os
import resource
import shutil
import sys
import time

from config import GOLD, LOG, MONTHS, ROOT, SERVICES, SILVER, TAB, duck

os.environ.setdefault("SPARK_LOCAL_HOSTNAME", "localhost")
os.environ.setdefault("SPARK_LOCAL_IP", "127.0.0.1")
os.environ.setdefault("PYSPARK_PYTHON", sys.executable)

SLOG = LOG / "spark"
SLOG.mkdir(parents=True, exist_ok=True)
# Thư mục làm việc của Spark (bảng tái lập, tệp tạm, luồng, checkpoint). Spark cần quyền
# xóa tệp trong thư mục này (thư mục _temporary khi ghi, checkpoint khi xử lý luồng), nên có
# thể trỏ sang ổ đĩa cục bộ bằng biến môi trường SPARK_WORK.
from pathlib import Path  # noqa: E402
WORK = Path(os.environ.get("SPARK_WORK", ROOT / "data" / "_spark"))
SPARK_GOLD = WORK / "gold" / "zone_day_pu"
SPARK_TMP = WORK / "tmp"
STREAM = WORK / "stream"
BENCH_MONTH = "2025-03"
DRIVER_MEM = "1200m"
REPEAT = 3

SUMS_SQL = """count(*) AS n, sum(fare) AS fare, sum(driver_pay) AS pay, sum(miles) AS miles,
  sum(time_s) AS time_s, sum(tips) AS tips, sum(CAST(cbd_fee AS DOUBLE)) AS cbd,
  sum(rider_cost) AS rider_cost, sum(cong_sur) AS cong_sur, sum(tolls) AS tolls,
  sum(wait_min) AS wait_sum, count(wait_min) AS wait_n, sum(shared_req) AS shared_req,
  sum(CAST(cbd_fee > 0 AS INT)) AS n_cbd,
  sum(CAST(do_grp = 'CRZ' AS INT)) AS n_to_crz,
  sum(CAST(company_code = 'HV0003' AS INT)) AS n_uber,
  sum(CAST(company_code = 'HV0005' AS INT)) AS n_lyft"""
QUERY = f"SELECT service, d, pu AS zone, {SUMS_SQL} FROM s GROUP BY service, d, pu"
METRICS = ["n", "fare", "pay", "miles", "time_s", "tips", "cbd", "rider_cost", "cong_sur", "tolls",
           "wait_sum", "wait_n", "shared_req", "n_cbd", "n_to_crz", "n_uber", "n_lyft"]


def month_dir(svc, ym):
    y, m = ym.split("-")
    return SILVER / f"service={svc}" / f"year={y}" / f"month={m}"


def months_2025(k):
    return [m for m in MONTHS if m.startswith("2025")][:k]


def spark_session(shuffle=8, extra=None):
    from pyspark.sql import SparkSession
    SPARK_TMP.mkdir(parents=True, exist_ok=True)
    b = (SparkSession.builder.master("local[2]").appName("crz-lakehouse")
         .config("spark.driver.memory", DRIVER_MEM)
         .config("spark.ui.enabled", "false")
         .config("spark.ui.showConsoleProgress", "false")
         .config("spark.sql.shuffle.partitions", str(shuffle))
         .config("spark.sql.session.timeZone", "UTC")
         .config("spark.local.dir", SPARK_TMP.as_posix())
         .config("spark.sql.adaptive.enabled", "true")
         .config("spark.driver.extraJavaOptions", "-Dlog4j2.level=ERROR"))
    for k, v in (extra or {}).items():
        b = b.config(k, v)
    s = b.getOrCreate()
    s.sparkContext.setLogLevel("ERROR")
    return s


def jvm_peak_mb(spark):
    """Bộ nhớ đỉnh (VmHWM) của tiến trình JVM chạy Spark driver/executor (chế độ local)."""
    try:
        pid = spark.sparkContext._gateway.proc.pid
        for line in open(f"/proc/{pid}/status"):
            if line.startswith("VmHWM"):
                return int(line.split()[1]) / 1024
    except Exception:
        return None


def py_peak_mb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


def write_log(name, rec):
    (SLOG / f"{name}.json").write_text(json.dumps(rec, indent=2, ensure_ascii=False, default=str))
    print(json.dumps(rec, ensure_ascii=False, default=str)[:600], flush=True)


def load_months(spark, svc, months, cols=None):
    paths = [month_dir(svc, m).as_posix() for m in months]
    df = spark.read.option("basePath", SILVER.as_posix()).parquet(*paths)
    if cols:
        df = df.select(*cols)
    return df


# ------------------------------------------------------------------ repro
def part_repro(budget):
    t_start = time.time()
    todo = [(s, m) for s in SERVICES for m in MONTHS
            if not (SLOG / "repro" / f"{s}_{m}.json").exists()]
    if not todo:
        print("repro: đã xong toàn bộ")
        return
    (SLOG / "repro").mkdir(exist_ok=True)
    t0 = time.time()
    spark = spark_session()
    t_boot = time.time() - t0
    for svc, ym in todo:
        if time.time() - t_start > budget:
            break
        t1 = time.time()
        df = load_months(spark, svc, [ym])
        df.createOrReplaceTempView("s")
        out = spark.sql(QUERY)
        dst = SPARK_GOLD / f"service={svc}" / f"ym={ym}"
        out.coalesce(1).write.mode("overwrite").parquet(dst.as_posix())
        el = time.time() - t1
        n_in = sum(json.loads(p.read_text())["n_silver"]
                   for p in (LOG / "partitions").glob(f"{svc}_{ym}_c*.json"))
        rec = dict(service=svc, month=ym, seconds=round(el, 2), n_silver=n_in,
                   rows_per_sec=round(n_in / el), boot_s=round(t_boot, 2),
                   jvm_peak_mb=jvm_peak_mb(spark))
        (SLOG / "repro" / f"{svc}_{ym}.json").write_text(json.dumps(rec, indent=2))
        print(json.dumps(rec), flush=True)
    spark.stop()
    left = sum(1 for s in SERVICES for m in MONTHS if not (SLOG / "repro" / f"{s}_{m}.json").exists())
    print("repro: còn lại", left)


# ------------------------------------------------------------------ validate
def part_validate():
    con = duck()
    sp = (SPARK_GOLD / "**" / "*.parquet").as_posix()
    con.execute(f"CREATE VIEW sp AS SELECT * FROM read_parquet('{sp}', hive_partitioning=true)")
    con.execute(f"CREATE VIEW dk AS SELECT * FROM '{(GOLD / 'zone_day_pu.parquet').as_posix()}'")
    rows = []
    cnt = con.execute("""SELECT (SELECT count(*) FROM sp), (SELECT count(*) FROM dk),
        (SELECT count(*) FROM sp FULL JOIN dk USING (service, d, zone) WHERE sp.n IS NULL OR dk.n IS NULL)
    """).fetchone()
    for m in METRICS:
        r = con.execute(f"""SELECT sp.service,
              count(*) AS cells,
              sum(CASE WHEN (sp.{m} IS NULL) <> (dk.{m} IS NULL) THEN 1 ELSE 0 END) AS null_mismatch,
              max(abs(sp.{m}::DOUBLE - dk.{m}::DOUBLE)) AS max_abs_diff,
              max(abs(sp.{m}::DOUBLE - dk.{m}::DOUBLE) / nullif(abs(dk.{m}::DOUBLE), 0)) AS max_rel_diff,
              sum(sp.{m}::DOUBLE) AS total_spark, sum(dk.{m}::DOUBLE) AS total_duckdb
            FROM sp JOIN dk USING (service, d, zone) GROUP BY 1 ORDER BY 1""").df()
        r.insert(1, "metric", m)
        rows.append(r)
    import pandas as pd
    t = pd.concat(rows, ignore_index=True)
    t["exact_match"] = (t.max_abs_diff.fillna(0) == 0) & (t.null_mismatch == 0)
    t.to_csv(TAB / "t61_spark_validation.csv", index=False)
    write_log("validate", dict(rows_spark=cnt[0], rows_duckdb=cnt[1], unmatched_keys=cnt[2],
                               metrics=len(METRICS), all_within_1e9=bool((t.max_rel_diff.fillna(0) < 1e-9).all()),
                               exact_cells_share=float(t.exact_match.mean())))


# ------------------------------------------------------------------ engine
def run_duckdb(months):
    con = duck()
    paths = ", ".join(f"'{(month_dir('hvfhv', m) / '*.parquet').as_posix()}'" for m in months)
    con.execute(f"CREATE VIEW s AS SELECT * FROM read_parquet([{paths}])")
    times = []
    for _ in range(REPEAT):
        t = time.perf_counter()
        res = con.execute(QUERY).fetchall()
        times.append(time.perf_counter() - t)
    return times, len(res), None


def run_spark(months, api="df", shuffle=8, extra=None):
    from pyspark.sql import functions as F
    t0 = time.perf_counter()
    spark = spark_session(shuffle, extra)
    boot = time.perf_counter() - t0
    df = load_months(spark, "hvfhv", months)
    df.createOrReplaceTempView("s")
    times = []
    for _ in range(REPEAT):
        t = time.perf_counter()
        if api == "sql":
            res = spark.sql(QUERY).collect()
        else:
            res = (df.groupBy("service", "d", F.col("pu").alias("zone"))
                   .agg(F.count(F.lit(1)).alias("n"), F.sum("fare").alias("fare"),
                        F.sum("driver_pay").alias("pay"), F.sum("miles").alias("miles"),
                        F.sum("time_s").alias("time_s"), F.sum("tips").alias("tips"),
                        F.sum(F.col("cbd_fee").cast("double")).alias("cbd"),
                        F.sum("rider_cost").alias("rider_cost"), F.sum("cong_sur").alias("cong_sur"),
                        F.sum("tolls").alias("tolls"), F.sum("wait_min").alias("wait_sum"),
                        F.count("wait_min").alias("wait_n"), F.sum("shared_req").alias("shared_req"),
                        F.sum((F.col("cbd_fee") > 0).cast("int")).alias("n_cbd"),
                        F.sum((F.col("do_grp") == "CRZ").cast("int")).alias("n_to_crz"),
                        F.sum((F.col("company_code") == "HV0003").cast("int")).alias("n_uber"),
                        F.sum((F.col("company_code") == "HV0005").cast("int")).alias("n_lyft"))
                   .collect())
        times.append(time.perf_counter() - t)
    peak = jvm_peak_mb(spark)
    spark.stop()
    return times, len(res), dict(boot_s=boot, jvm_peak_mb=peak)


def n_rows(months, svc="hvfhv"):
    return sum(json.loads(p.read_text())["n_silver"] for m in months
               for p in (LOG / "partitions").glob(f"{svc}_{m}_c*.json"))


def part_engine(engine, months=None, tag=None, shuffle=8, aqe=True):
    months = months or [BENCH_MONTH]
    if engine == "duckdb":
        times, groups, extra = run_duckdb(months)
    else:
        times, groups, extra = run_spark(months, "sql" if engine == "spark_sql" else "df", shuffle,
                                         None if aqe else {"spark.sql.adaptive.enabled": "false"})
    rec = dict(engine=engine, months=months, n_rows=n_rows(months), groups=groups, shuffle=shuffle, aqe=aqe,
               times=[round(x, 3) for x in times], first_s=round(times[0], 3),
               median_s=round(sorted(times)[len(times) // 2], 3),
               py_peak_mb=round(py_peak_mb(), 1), **(extra or {}))
    write_log(tag or f"engine_{engine}", rec)


# ------------------------------------------------------------------ cache
def part_cache():
    from pyspark import StorageLevel
    from pyspark.sql import functions as F
    spark = spark_session()
    df = load_months(spark, "hvfhv", [BENCH_MONTH],
                     ["d", "hr", "pu", "dl", "pu_grp", "do_grp", "fare", "miles", "time_s", "wait_min"])
    qs = {
        "q1_vùng×ngày": lambda x: x.groupBy("pu", "d").agg(F.count(F.lit(1)), F.sum("fare")).count(),
        "q2_nhóm×giờ": lambda x: x.groupBy("pu_grp", "hr").agg(F.avg("wait_min"), F.sum("miles")).count(),
        "q3_OD": lambda x: x.groupBy("pu", "dl").agg(F.sum("time_s")).count(),
    }
    out = []
    for phase in ("không lưu đệm", "lưu đệm"):
        x = df
        mat = None
        if phase == "lưu đệm":
            x = df.persist(StorageLevel.MEMORY_AND_DISK)
            t = time.perf_counter()
            x.count()
            mat = time.perf_counter() - t
        for qn, q in qs.items():
            for rep in range(2):
                t = time.perf_counter()
                q(x)
                out.append(dict(phase=phase, query=qn, rep=rep + 1, seconds=round(time.perf_counter() - t, 3)))
        if mat is not None:
            out.append(dict(phase=phase, query="vật chất hóa bộ đệm", rep=1, seconds=round(mat, 3)))
    # Dung lượng bộ đệm theo trình quản lý lưu trữ của Spark
    st = spark.sparkContext._jsc.sc().getRDDStorageInfo()
    mem = sum(i.memSize() for i in st) / 2**20
    disk = sum(i.diskSize() for i in st) / 2**20
    lineage = df.groupBy("pu", "d").agg(F.count(F.lit(1))).rdd.toDebugString().decode()
    (SLOG / "lineage_q1.txt").write_text(lineage)
    write_log("cache", dict(month=BENCH_MONTH, n_rows=n_rows([BENCH_MONTH]), runs=out,
                            cache_mem_mb=round(mem, 1), cache_disk_mb=round(disk, 1),
                            jvm_peak_mb=jvm_peak_mb(spark)))
    spark.stop()


# ------------------------------------------------------------------ prune
def scan_metrics(df):
    """Đọc số liệu của toán tử quét tệp (FileSourceScanExec) trong kế hoạch vật lý đã thực thi."""
    def walk(n):
        name = n.getClass().getSimpleName()
        if name.endswith("QueryStageExec"):
            return walk(n.plan())
        if name == "AdaptiveSparkPlanExec":
            return walk(n.executedPlan())
        if "FileSourceScanExec" in name:
            return [n]
        out, ch = [], n.children()
        for i in range(ch.size()):
            out += walk(ch.apply(i))
        return out
    res = {}
    for node in walk(df._jdf.queryExecution().executedPlan()):
        m = node.metrics()
        for k in ("numFiles", "numPartitions", "filesSize", "numOutputRows"):
            o = m.get(k)
            if o.isDefined():
                res[k] = res.get(k, 0) + int(o.get().value())
    return res


def part_prune():
    from pyspark.sql import functions as F
    spark = spark_session()
    cols = ["service", "year", "month", "pu", "d", "fare"]
    base = spark.read.parquet((SILVER).as_posix()).select(*cols)
    runs = []
    cases = {
        "toàn bộ Silver (không lọc)": base,
        "service='hvfhv'": base.where(F.col("service") == "hvfhv"),
        "service='hvfhv' AND year=2025": base.where((F.col("service") == "hvfhv") & (F.col("year") == 2025)),
        "service='hvfhv' AND year=2025 AND month=3": base.where(
            (F.col("service") == "hvfhv") & (F.col("year") == 2025) & (F.col("month") == 3)),
        "lọc theo cột d (không phải khóa phân vùng)": base.where(
            (F.col("d") >= "2025-03-01") & (F.col("d") < "2025-04-01")),
    }
    for name, q in cases.items():
        agg = q.groupBy("pu").agg(F.count(F.lit(1)).alias("n"), F.sum("fare").alias("fare"))
        t = time.perf_counter()
        rows = agg.collect()
        el = time.perf_counter() - t
        sm = scan_metrics(agg)
        runs.append(dict(case=name, files=sm.get("numFiles"), partitions=sm.get("numPartitions"),
                         scanned_mb=round(sm.get("filesSize", 0) / 2**20, 1),
                         rows_scanned=sm.get("numOutputRows"), rows=int(sum(x["n"] for x in rows)),
                         seconds=round(el, 3)))
        if "month=3" in name:
            (SLOG / "plan_pruned.txt").write_text(agg._jdf.queryExecution().explainString(
                spark._jvm.org.apache.spark.sql.execution.ExplainMode.fromString("formatted")))
            (SLOG / "plan_logical.txt").write_text(agg._jdf.queryExecution().toString())
        print(runs[-1], flush=True)
    write_log("prune", dict(runs=runs, jvm_peak_mb=jvm_peak_mb(spark)))
    spark.stop()


# ------------------------------------------------------------------ arrow
def part_arrow():
    from pyspark.sql import functions as F
    out = []
    for arrow in ("false", "true"):
        spark = spark_session(extra={"spark.sql.execution.arrow.pyspark.enabled": arrow})
        df = load_months(spark, "hvfhv", [BENCH_MONTH], ["pu", "dl", "d", "hr", "fare", "miles", "time_s", "mph"])
        sub = df.where(F.col("d") < "2025-03-04").cache()
        n = sub.count()
        for rep in range(REPEAT):
            t = time.perf_counter()
            pdf = sub.toPandas()
            out.append(dict(arrow=arrow == "true", rep=rep + 1, rows=n, cols=pdf.shape[1],
                            seconds=round(time.perf_counter() - t, 3)))
            del pdf
        spark.stop()
    write_log("arrow", dict(runs=out))


# ------------------------------------------------------------------ stream
def part_stream_prep():
    inp = STREAM / "in_all"
    if inp.exists():
        shutil.rmtree(inp)
    inp.mkdir(parents=True)
    con = duck()
    paths = ", ".join(f"'{(month_dir('hvfhv', m) / '*.parquet').as_posix()}'" for m in ("2024-12", "2025-01"))
    days = con.execute(f"""SELECT DISTINCT d FROM read_parquet([{paths}])
                          WHERE d BETWEEN '2024-12-29' AND '2025-01-11' ORDER BY d""").fetchall()
    for (d,) in days:
        con.execute(f"""COPY (SELECT pickup_ts, company_code, pu, dl, pu_grp, do_grp,
                              CAST(cbd_fee AS DOUBLE) AS cbd_fee, fare, miles, time_s
                              FROM read_parquet([{paths}]) WHERE d = DATE '{d}' ORDER BY pickup_ts)
                        TO '{(inp / f"trips_{d}.parquet").as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)""")
    print("stream_prep:", len(days), "tệp")


def part_stream():
    from pyspark.sql import functions as F
    src = STREAM / "in_all"
    land = STREAM / "landing"
    ck = STREAM / "checkpoint"
    sink = STREAM / "sink"
    for p in (land, ck, sink):
        if p.exists():
            shutil.rmtree(p)
    land.mkdir(parents=True)
    # Mô phỏng nguồn phát sinh: chép toàn bộ tệp ngày vào thư mục hạ cánh;
    # maxFilesPerTrigger=1 buộc Spark xử lý mỗi tệp (một ngày) là một lô vi mô.
    for f in sorted(src.glob("*.parquet")):
        shutil.copy(f, land / f.name)
    spark = spark_session(shuffle=4)
    schema = spark.read.parquet(next(land.glob("*.parquet")).as_posix()).schema
    stream = (spark.readStream.schema(schema).option("maxFilesPerTrigger", 1)
              .parquet(land.as_posix()))
    # Parquet do DuckDB ghi có kiểu TIMESTAMP không múi giờ (timestamp_ntz); cơ chế watermark
    # của Spark yêu cầu kiểu timestamp, nên ép kiểu (phiên đặt múi giờ UTC nên không lệch giờ).
    agg = (stream.withColumn("pickup_ts", F.col("pickup_ts").cast("timestamp"))
           .withWatermark("pickup_ts", "2 hours")
           .withColumn("vao_crz", ((F.col("pu_grp") == "CRZ") | (F.col("do_grp") == "CRZ")).cast("int"))
           .groupBy(F.window("pickup_ts", "1 hour"), "company_code")
           .agg(F.count(F.lit(1)).alias("n"), F.sum("vao_crz").alias("n_crz"),
                F.sum((F.col("cbd_fee") > 0).cast("int")).alias("n_cbd"),
                F.sum("cbd_fee").alias("cbd"), F.sum("miles").alias("miles"),
                F.sum("time_s").alias("time_s")))
    t0 = time.perf_counter()
    q = (agg.writeStream.outputMode("append").format("parquet")
         .option("path", sink.as_posix()).option("checkpointLocation", ck.as_posix())
         .trigger(availableNow=True).start())
    q.awaitTermination()
    wall = time.perf_counter() - t0
    prog = [json.loads(p.json) for p in q.recentProgress] if hasattr(q.recentProgress[0], "json") \
        else q.recentProgress
    batches = [dict(batch=p["batchId"], rows=p["numInputRows"],
                    trigger_ms=p["durationMs"].get("triggerExecution"),
                    add_batch_ms=p["durationMs"].get("addBatch"),
                    rows_per_s=p.get("processedRowsPerSecond"),
                    watermark=p.get("eventTime", {}).get("watermark"),
                    state_rows=(p.get("stateOperators") or [{}])[0].get("numRowsTotal"),
                    state_mem_mb=round((p.get("stateOperators") or [{}])[0].get("memoryUsedBytes", 0) / 2**20, 2))
               for p in prog]
    res = spark.read.parquet(sink.as_posix()).toPandas()
    res["hour"] = res["window"].apply(lambda w: w["start"])
    res.drop(columns="window").to_parquet(STREAM / "stream_hourly.parquet")
    write_log("stream", dict(files=len(list(land.glob("*.parquet"))), wall_s=round(wall, 2),
                             batches=batches, output_rows=len(res), jvm_peak_mb=jvm_peak_mb(spark)))
    spark.stop()


# ------------------------------------------------------------------ report
def part_report():
    import pandas as pd
    import matplotlib.dates as mdates
    from viz import C, fig, save, policy_line

    # t60: tái lập zone_day_pu bằng Spark
    rp = pd.DataFrame([json.loads(p.read_text()) for p in sorted((SLOG / "repro").glob("*.json"))])
    rp.to_csv(TAB / "t60_spark_repro_partitions.csv", index=False)
    tot = rp.groupby("service").agg(months=("month", "count"), n_silver=("n_silver", "sum"),
                                    seconds=("seconds", "sum"), sec_median=("seconds", "median"),
                                    jvm_peak_mb=("jvm_peak_mb", "max"))
    tot["rows_per_sec"] = tot.n_silver / tot.seconds
    # Thời gian DuckDB cho riêng bước Gold (cùng dữ liệu) từ nhật ký bước 03
    parts = pd.DataFrame([json.loads(p.read_text()) for p in (LOG / "partitions").glob("*.json")])
    tot = tot.join(parts.groupby("service").sec_gold.sum().rename("duckdb_gold_all7_s"))
    tot.to_csv(TAB / "t60b_spark_repro_totals.csv")

    # t62: bộ máy
    eng = []
    for e in ("duckdb", "spark_df", "spark_sql"):
        p = SLOG / f"engine_{e}.json"
        if p.exists():
            eng.append(json.loads(p.read_text()))
    eng = pd.DataFrame(eng)
    eng["rows_per_s_median"] = eng.n_rows / eng.median_s
    eng.drop(columns=["months"]).to_csv(TAB / "t62_spark_engine.csv", index=False)

    # t63: shuffle
    sh = pd.DataFrame([json.loads(p.read_text()) for p in sorted(SLOG.glob("shuffle_*.json"))])
    sh["aqe"] = sh.get("aqe", True)
    sh["aqe"] = sh.aqe.fillna(True).astype(bool)
    sh = sh.sort_values(["aqe", "shuffle"])
    sh[["aqe", "shuffle", "first_s", "median_s", "times", "jvm_peak_mb"]].to_csv(TAB / "t63_spark_shuffle.csv", index=False)

    # t64: mở rộng theo khối lượng
    sc = pd.DataFrame([json.loads(p.read_text()) for p in sorted(SLOG.glob("scale_*.json"))])
    sc["k_months"] = sc.months.apply(len)
    sc["rows_per_s"] = sc.n_rows / sc.median_s
    sc = sc.sort_values(["engine", "k_months"])
    sc[["engine", "k_months", "n_rows", "first_s", "median_s", "rows_per_s", "jvm_peak_mb", "py_peak_mb"]] \
        .to_csv(TAB / "t64_spark_scale.csv", index=False)

    # t65: lưu đệm
    ca = json.loads((SLOG / "cache.json").read_text())
    cr = pd.DataFrame(ca["runs"])
    cr.to_csv(TAB / "t65_spark_cache.csv", index=False)

    # t66: cắt tỉa phân vùng + Arrow
    pr = pd.DataFrame(json.loads((SLOG / "prune.json").read_text())["runs"])
    pr.to_csv(TAB / "t66_spark_pruning.csv", index=False)
    ar = pd.DataFrame(json.loads((SLOG / "arrow.json").read_text())["runs"])
    ar.groupby("arrow").agg(rows=("rows", "first"), cols=("cols", "first"),
                            median_s=("seconds", "median"), min_s=("seconds", "min"),
                            max_s=("seconds", "max")).to_csv(TAB / "t66b_spark_arrow.csv")

    # t67: luồng
    st = json.loads((SLOG / "stream.json").read_text())
    sb = pd.DataFrame(st["batches"])
    sb = sb[sb.rows > 0]
    sb.to_csv(TAB / "t67_stream_batches.csv", index=False)

    # ---- hình
    # f42: so sánh bộ máy + mở rộng
    f, axes = fig(6.8, 3.0, ncols=2)
    ax = axes[0]
    lab = {"duckdb": "DuckDB", "spark_df": "Spark DataFrame", "spark_sql": "Spark SQL"}
    x = range(len(eng))
    ax.bar([i - 0.2 for i in x], eng.first_s, 0.4, color=C["neutral"], label="Lần 1")
    ax.bar([i + 0.2 for i in x], eng.median_s, 0.4, color=C["s1"], label="Trung vị 3 lần")
    ax.set_xticks(list(x), [lab[e] for e in eng.engine])
    ax.set_ylabel("Giây")
    ax.set_title("Cùng truy vấn, một tháng HVFHV")
    ax.legend()
    ax = axes[1]
    for e, col in (("duckdb", C["s2"]), ("spark_df", C["s1"])):
        d = sc[sc.engine == e]
        ax.plot(d.n_rows / 1e6, d.median_s, marker="o", color=col, label=lab[e])
    ax.set_xlabel("Triệu dòng Silver")
    ax.set_ylabel("Giây (trung vị)")
    ax.set_title("Mở rộng theo khối lượng dữ liệu")
    ax.legend()
    f.tight_layout()
    save(f, "f42_spark_engine_scale")

    # f43: shuffle partitions
    f, ax = fig(6.0, 2.8)
    for flag, col, lb in ((True, C["s1"], "Bật AQE"), (False, C["s2"], "Tắt AQE")):
        d = sh[sh.aqe == flag]
        ax.plot(d.shuffle.astype(str), d.median_s, marker="o", color=col, label=lb)
    ax.legend()
    ax.set_xlabel("spark.sql.shuffle.partitions")
    ax.set_ylabel("Giây (trung vị)")
    ax.set_title("Số phân vùng xáo trộn và thời gian truy vấn")
    save(f, "f43_spark_shuffle")

    # f44: cache
    f, ax = fig(6.4, 2.9)
    g = cr[cr["query"] != "vật chất hóa bộ đệm"].groupby(["query", "phase"]).seconds.median().unstack()
    xs = range(len(g))
    ax.bar([i - 0.2 for i in xs], g["không lưu đệm"], 0.4, color=C["neutral"], label="Đọc lại từ Parquet")
    ax.bar([i + 0.2 for i in xs], g["lưu đệm"], 0.4, color=C["s1"], label="Từ bộ đệm trong bộ nhớ")
    ax.set_xticks(list(xs), [q.split("_", 1)[1] for q in g.index])
    ax.set_ylabel("Giây (trung vị 2 lần)")
    ax.set_title("Hiệu quả lưu đệm DataFrame")
    ax.legend()
    save(f, "f44_spark_cache")

    # f45: streaming – kết quả cửa sổ giờ
    h = pd.read_parquet(STREAM / "stream_hourly.parquet")
    h = h.groupby("hour")[["n", "n_crz", "n_cbd", "cbd"]].sum().reset_index().sort_values("hour")
    h.to_csv(TAB / "t67b_stream_hourly.csv", index=False)
    f, axes = fig(6.8, 4.2, nrows=2, sharex=True)
    axes[0].plot(h.hour, h.n / 1e3, color=C["neutral_dark"], lw=1.2, label="Mọi chuyến")
    axes[0].plot(h.hour, h.n_crz / 1e3, color=C["s1"], lw=1.2, label="Chuyến chạm CRZ")
    axes[0].set_ylabel("Nghìn chuyến/giờ")
    axes[0].legend(loc="upper left", ncol=2)
    axes[0].set_title("Kết quả cửa sổ 1 giờ do Structured Streaming phát ra")
    axes[1].plot(h.hour, h.n_cbd / h.n * 100, color=C["s2"], lw=1.2)
    axes[1].set_ylabel("% chuyến có phí CBD")
    import datetime as dt
    for a in axes:
        policy_line(a, dt.datetime(2025, 1, 5), "") if a is axes[1] else a.axvline(
            dt.datetime(2025, 1, 5), color=C["text2"], lw=1, ls="--")
    axes[1].xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
    f.tight_layout()
    save(f, "f45_stream_hourly")

    # f46: độ trễ lô vi mô
    f, ax = fig(6.4, 2.8)
    ax.bar(sb.batch.astype(str), sb.trigger_ms / 1000, color=C["s1"])
    ax2 = ax.twinx()
    ax2.plot(sb.batch.astype(str), sb.rows / 1e3, color=C["s2"], marker="o", lw=1.2)
    ax2.set_ylabel("Nghìn dòng/lô", color=C["s2"])
    ax2.grid(False)
    ax.set_xlabel("Lô vi mô (mỗi lô = một ngày dữ liệu)")
    ax.set_ylabel("Giây xử lý/lô")
    ax.set_title("Thời gian xử lý từng lô vi mô")
    save(f, "f46_stream_batches")
    print(tot, eng, sh, sc, pr, sep="\n")


if __name__ == "__main__":
    part = sys.argv[1]
    a = sys.argv[2:]
    if part == "repro":
        part_repro(float(a[0]) if a else 1e9)
    elif part == "validate":
        part_validate()
    elif part == "engine":
        part_engine(a[0])
    elif part == "shuffle":
        aqe = not (len(a) > 1 and a[1] == "noaqe")
        part_engine("spark_df", tag=f"shuffle_{int(a[0]):03d}" + ("" if aqe else "_noaqe"),
                    shuffle=int(a[0]), aqe=aqe)
    elif part == "scale":
        k = int(a[1])
        part_engine(a[0], months=months_2025(k), tag=f"scale_{a[0]}_{k:02d}")
    elif part == "cache":
        part_cache()
    elif part == "prune":
        part_prune()
    elif part == "arrow":
        part_arrow()
    elif part == "stream_prep":
        part_stream_prep()
    elif part == "stream":
        part_stream()
    elif part == "report":
        part_report()
    else:
        raise SystemExit(__doc__)
