"""Bước 1 - Lớp Bronze: lập danh mục (catalog) cho dữ liệu thô.

Dữ liệu thô là các tệp Parquet gốc của NYC TLC, giữ nguyên, không sửa
(nguyên tắc bất biến của lớp Bronze). Bước này đọc metadata của từng tệp
(không đọc toàn bộ dữ liệu) để ghi lại: kích thước, số dòng, số row group,
lược đồ cột, dấu vân tay lược đồ và khoảng thời gian thực tế trong tệp.
Kết quả dùng để phát hiện lệch lược đồ (schema drift) giữa các tháng.

Chạy:  python code/01_bronze_catalog.py        (giai đoạn chính 2024–2025)
       python code/01_bronze_catalog.py ext    (giai đoạn mở rộng 2022–2023, ghi t01x–t03x)
"""
import sys
import hashlib
import json
import time

import pandas as pd
import pyarrow.parquet as pq

from config import MONTHS, MONTHS_EXT, SERVICES, raw_file, BRONZE, TAB, LOG, duck

EXT = len(sys.argv) > 1 and sys.argv[1] == "ext"
if EXT:
    MONTHS = MONTHS_EXT
SFX = "x" if EXT else ""

t0 = time.time()
con = duck()
rows = []
schemas = {}
for svc in SERVICES:
    ts_col = "pickup_datetime" if svc == "hvfhv" else "tpep_pickup_datetime"
    for ym in MONTHS:
        f = raw_file(svc, ym)
        meta = pq.ParquetFile(f).metadata
        sch = pq.read_schema(f)
        cols = [(n, str(t)) for n, t in zip(sch.names, sch.types)]
        fp = hashlib.md5(json.dumps(cols).encode()).hexdigest()[:10]
        schemas.setdefault(svc, {})[ym] = cols
        mn, mx = con.execute(f"SELECT min({ts_col}), max({ts_col}) FROM '{f.as_posix()}'").fetchone()
        comp = meta.row_group(0).column(0).compression if meta.num_row_groups else ""
        rows.append(dict(service=svc, month=ym, file=f.name,
                         size_mb=round(f.stat().st_size / 2**20, 1),
                         n_rows=meta.num_rows, n_row_groups=meta.num_row_groups,
                         n_columns=meta.num_columns, compression=comp,
                         schema_fingerprint=fp, min_pickup=str(mn), max_pickup=str(mx),
                         created_by=meta.created_by))
        print(svc, ym, meta.num_rows, flush=True)

man = pd.DataFrame(rows)
man.to_csv(TAB / f"t01{SFX}_bronze_manifest{'_ext' if EXT else ''}.csv", index=False)
man.to_parquet(BRONZE / f"bronze_manifest{'_ext' if EXT else ''}.parquet", index=False)

# Phát hiện lệch lược đồ: so cột của từng tháng với tháng đầu tiên
drift = []
for svc, d in schemas.items():
    base = dict(d[MONTHS[0]])
    for ym, cols in d.items():
        cur = dict(cols)
        added = sorted(set(cur) - set(base))
        removed = sorted(set(base) - set(cur))
        changed = sorted(c for c in set(cur) & set(base) if cur[c] != base[c])
        if added or removed or changed:
            drift.append(dict(service=svc, month=ym, added=";".join(added),
                              removed=";".join(removed), type_changed=";".join(changed)))
pd.DataFrame(drift).to_csv(TAB / f"t02{SFX}_schema_drift{'_ext' if EXT else ''}.csv", index=False)

summary = man.groupby("service").agg(files=("file", "count"), total_rows=("n_rows", "sum"),
                                     total_size_mb=("size_mb", "sum")).reset_index()
summary.to_csv(TAB / f"t03{SFX}_bronze_summary{'_ext' if EXT else ''}.csv", index=False)
(LOG / f"01_bronze_catalog{'_ext' if EXT else ''}.json").write_text(json.dumps(
    dict(seconds=round(time.time() - t0, 1), files=len(man),
         total_rows=int(man.n_rows.sum()), total_mb=float(man.size_mb.sum())), indent=2))
print(summary)
print("drift rows:", len(drift), "time", round(time.time() - t0, 1))
