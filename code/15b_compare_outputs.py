"""Bước 15b - So sánh các bảng kết quả hiện tại với một bản chụp trước đó.

Dùng sau khi sửa lỗi ở một bước thượng nguồn (ví dụ bước 04) và chạy lại các bước phân tích,
để biết chính xác tệp kết quả nào thay đổi và thay đổi bao nhiêu (phân tích tác động theo phả hệ).

Chạy:  python code/15b_compare_outputs.py <thư_mục_bản_chụp>
Ghi:   outputs/tables/t61c_rerun_changes.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from config import TAB

snap = Path(sys.argv[1])
rows = []
for f in sorted(TAB.glob("*.csv")):
    old = snap / f.name
    if not old.exists() or f.name.startswith("t61"):
        continue
    a, b = pd.read_csv(f), pd.read_csv(old)
    if a.shape != b.shape:
        rows.append(dict(file=f.name, changed=True, cols="(khác kích thước)", max_abs=np.nan, max_rel=np.nan))
        continue
    num = a.select_dtypes("number").columns
    d = (a[num] - b[num]).abs()
    rel = d / b[num].abs().replace(0, np.nan)
    ch = [c for c in num if (d[c] > 1e-9).any()]
    txt = (a.drop(columns=num).fillna("") != b.drop(columns=num).fillna("")).any()
    ch += [c for c in txt.index if txt[c]]
    rows.append(dict(file=f.name, changed=bool(ch), cols=";".join(ch),
                     max_abs=float(d.max().max()) if len(num) else 0.0,
                     max_rel=float(rel.max().max()) if len(num) else 0.0))
t = pd.DataFrame(rows)
t.to_csv(TAB / "t61c_rerun_changes.csv", index=False)
print(t[t.changed].to_string())
print("so sánh", len(t), "tệp; thay đổi", int(t.changed.sum()))
