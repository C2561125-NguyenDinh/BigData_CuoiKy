"""Chạy toàn bộ pipeline của đồ án theo đúng thứ tự, trên Windows, macOS hoặc Linux.

Dùng (từ thư mục gốc của kho):
  python code/run_all.py                 # toàn bộ: tải dữ liệu, Bronze → Silver → Gold, mọi phân tích, báo cáo
  python code/run_all.py --from-gold     # chỉ dùng lớp Gold có sẵn trong data/gold (kèm theo kho GitHub):
                                         # chạy lại phân tích 06–11, 14, 16 (phần dùng Gold), 17–20 và dựng báo cáo, không cần tải dữ liệu
  python code/run_all.py --no-spark      # bỏ bước 15 (cần Java 11+)
  python code/run_all.py --no-ext        # bỏ phần dữ liệu 2022–2023 (bước 01/03/04 ext)
  python code/run_all.py --no-report     # không dựng báo cáo (bước 13 cần LibreOffice và pdftotext)

Biến môi trường SPARK_WORK và DUCKDB_TMP trỏ tới thư mục làm việc có quyền xóa tệp; mặc định nằm trong data/.
Bản run_all.sh tương đương cho bash vẫn được giữ.
"""
import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CODE = ROOT / "code"
ap = argparse.ArgumentParser()
ap.add_argument("--from-gold", action="store_true")
ap.add_argument("--no-spark", action="store_true")
ap.add_argument("--no-ext", action="store_true")
ap.add_argument("--no-report", action="store_true")
a = ap.parse_args()

os.environ.setdefault("SPARK_WORK", str(ROOT / "data" / "_spark"))
os.environ.setdefault("DUCKDB_TMP", str(ROOT / "data" / "_duck_tmp"))

S = []          # (nhóm, lệnh)
if not a.from_gold:
    S += [("dl", ["00_download_data.py"]), ("dl-ext", ["00_download_data_2022_2023.py"]),
          ("etl", ["01_bronze_catalog.py"]), ("etl", ["02_zone_dimension.py"]),
          ("etl", ["03_silver_gold_month.py", "all"]), ("etl", ["04_gold_consolidate.py"]),
          ("etl", ["05_benchmark.py", "format"]), ("etl", ["05_benchmark.py", "engine"]),
          ("etl", ["05_benchmark.py", "pruning"])]
S += [("ana", ["06_eda.py"]), ("ana", ["07_did_main.py"]), ("ana", ["08_synthetic_control.py"]),
      ("ana", ["09_dml_heterogeneity.py"]), ("ana", ["10_spillover_robustness.py", "all"]),
      ("ana", ["11_appendix_tables.py"]), ("ana", ["14_extra_analysis.py"])]
if not a.from_gold:
    S += [("ana", ["12_pipeline_figures.py"])]
if not a.from_gold and not a.no_spark:
    sp = [["repro"], ["validate"]] + [["engine", e] for e in ("duckdb", "spark_df", "spark_sql")]
    for p in (1, 2, 4, 8, 16, 32, 64, 200, 1000):
        sp += [["shuffle", str(p)], ["shuffle", str(p), "noaqe"]]
    for k in (1, 2, 3, 4, 6):
        sp += [["scale", "duckdb", str(k)], ["scale", "spark_df", str(k)]]
    sp += [["cache"], ["prune"], ["arrow"], ["stream_prep"], ["stream"], ["report"]]
    S += [("spark", ["15_spark_pipeline.py"] + x) for x in sp] + [("spark", ["15b_compare_outputs.py"])]
if not a.from_gold:
    S += [("gov", ["16_governance_risk.py", p]) for p in
          ("catalog", "lineage", "integrity", "reconcile", "anomaly", "tripanom", "privacy", "dp", "dr")]
else:
    S += [("gov", ["16_governance_risk.py", p]) for p in ("anomaly", "tripanom", "dp")]
S += [("biz", ["17_business_analytics.py", p]) for p in ("company", "forecast", "power", "pricing", "tco")]
S += [("ana", ["18_theory_sensitivity.py"])]
if not a.from_gold and not a.no_ext:
    S += [("ext", ["01_bronze_catalog.py", "ext"]), ("ext", ["03_silver_gold_month.py", "ext"]),
          ("ext", ["04_gold_consolidate.py", "ext"])]
S += [("ana", ["19_long_preperiod.py"]), ("ana", ["20_inference_robustness.py"])]
if not a.from_gold and not a.no_ext:
    S += [("ext", ["21_regeneration_check.py"] + x.split()) for x in ("yellow 2022-01 0", "yellow 2023-07 0", "hvfhv 2022-10 0")]
    S += [("ext", ["21_regeneration_check.py", "report"])]
if not a.no_report:
    S += [("rep", ["13_build_report.py"])]

t0 = time.time()
for i, (grp, cmd) in enumerate(S, 1):
    print(f"\n=== [{i}/{len(S)}] {' '.join(cmd)}", flush=True)
    r = subprocess.run([sys.executable, str(CODE / cmd[0])] + cmd[1:], cwd=ROOT)
    if r.returncode != 0:
        sys.exit(f"Lỗi ở bước: {' '.join(cmd)} (mã {r.returncode})")
print(f"\nXong {len(S)} bước trong {(time.time() - t0) / 60:.1f} phút.")
