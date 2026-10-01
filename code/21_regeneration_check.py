"""Bước 21 - Kiểm chứng khả năng tái tạo lớp Gold khi Silver không được lưu bền (giai đoạn 2022–2023).

Với HVFHV từ 08/2022 và mọi tháng taxi vàng 2022–2023, bước 03 không ghi Silver xuống đĩa vì giới hạn tài
nguyên. Để kiểm toán được các phân vùng này mà không cần Silver, bước này chạy lại bước 03 cho một số phân vùng
từ Bronze vào một thư mục tạm, rồi so sánh từng bảng Gold mới với bảng Gold đang dùng: số dòng và tổng của mọi
cột số (sai lệch tương đối tối đa). Nếu trùng khớp, Silver của các phân vùng đó có thể được dựng lại bất kỳ lúc
nào từ Bronze (đã có dấu băm SHA-256) và mã nguồn, nên việc không lưu Silver không làm mất khả năng kiểm toán.

Chạy:  python code/21_regeneration_check.py yellow 2022-01 0
       python code/21_regeneration_check.py report         (gộp kết quả thành bảng t96)
"""
import importlib.util
import json
import os
import sys
import time
from pathlib import Path

import pandas as pd

from config import GOLD, LOG, TAB, duck

VERIFY = Path(os.environ.get("VERIFY_DIR", GOLD.parent / "_verify"))
VLOG = LOG / "regeneration"
TABLES = ["zone_day_pu", "zone_day_do", "grp_hour_day", "company_grp_day", "zone_hour_month", "od_month", "trip_sample"]


def fingerprint(con, path):
    df = con.execute(f"SELECT * FROM read_parquet('{Path(path).as_posix()}') LIMIT 0").df()
    num = [c for c, t in df.dtypes.items() if pd.api.types.is_numeric_dtype(t)]
    exprs = ["count(*) AS _rows"] + [f'sum(CAST("{c}" AS DOUBLE)) AS "{c}"' for c in num]
    return con.execute(f"SELECT {', '.join(exprs)} FROM read_parquet('{Path(path).as_posix()}')").df().iloc[0]


def check(svc, ym, k):
    spec = importlib.util.spec_from_file_location("step03", Path(__file__).parent / "03_silver_gold_month.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    out = VERIFY / f"{svc}_{ym}_c{k}"

    def gp(table, service, ymk):
        p = out / table
        p.mkdir(parents=True, exist_ok=True)
        return p / f"{service}_{ymk}.parquet"
    m.gold_part = gp
    m.LOG = out / "log"
    m.silver_file = lambda s, y: out / "silver" / "part-0.parquet"
    (out / "silver").mkdir(parents=True, exist_ok=True)
    (out / "log").mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    m.run(svc, ym, k)
    sec = time.time() - t0
    con = duck()
    rows = []
    for t in TABLES:
        orig = GOLD / "_parts_ext" / t / f"{svc}_{ym}_c{k}.parquet"
        new = out / t / f"{svc}_{ym}_c{k}.parquet"
        if not orig.exists() or not new.exists():
            continue
        a, b = fingerprint(con, orig), fingerprint(con, new)
        rel = ((a - b).abs() / a.abs().clip(lower=1e-9)).max()
        rows.append(dict(service=svc, month=ym, chunk=k, table=t, rows_orig=int(a["_rows"]), rows_new=int(b["_rows"]),
                         n_numeric_cols=len(a) - 1, max_rel_diff=float(rel)))
    VLOG.mkdir(parents=True, exist_ok=True)
    rec = dict(service=svc, month=ym, chunk=k, seconds=round(sec, 1), tables=rows)
    (VLOG / f"{svc}_{ym}_c{k}.json").write_text(json.dumps(rec, indent=2))
    print(json.dumps(rec)[:800], flush=True)


def report():
    recs = [json.loads(p.read_text()) for p in sorted(VLOG.glob("*.json"))]
    df = pd.DataFrame([r for rec in recs for r in rec["tables"]])
    df.to_csv(TAB / "t96_regeneration_check.csv", index=False)
    print(df)


if __name__ == "__main__":
    if sys.argv[1] == "report":
        report()
    else:
        check(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 0)
