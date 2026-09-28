"""Bước 11 - Bảng chi tiết cho phụ lục: theo vùng, theo tháng, theo luồng.

Mọi con số trong phụ lục được tính trực tiếp từ các bảng Gold.
Chạy:  python code/11_appendix_tables.py
"""
import json
import time

import numpy as np
import pandas as pd

from config import GOLD, LOG, TAB
from panels import P

t0 = time.time()
dim = pd.read_parquet(GOLD / "dim_zone.parquet")
z = pd.read_parquet(GOLD / "zone_day_pu.parquet")
z["d"] = pd.to_datetime(z.d)
zd = pd.read_parquet(GOLD / "zone_day_do.parquet")
zd["d"] = pd.to_datetime(zd.d)

# Cùng cửa sổ lịch cho hai năm: 05/01–31/12
z = z[((z.d >= "2024-01-05") & (z.d <= "2024-12-31")) | (z.d >= P)]
zd = zd[((zd.d >= "2024-01-05") & (zd.d <= "2024-12-31")) | (zd.d >= P)]
z["yr"] = z.d.dt.year
zd["yr"] = zd.d.dt.year
S = ["n", "fare", "pay", "miles", "time_s", "tips", "cbd", "rider_cost", "wait_sum", "wait_n", "n_cbd"]
a = z.groupby(["service", "zone", "yr"])[S + ["n_to_crz"]].sum()
days = z.groupby("yr").d.nunique()
b = zd.groupby(["service", "zone", "yr"])[["n", "n_from_crz"]].sum().rename(columns={"n": "n_do"})
m = a.join(b, how="outer").reset_index()
m["days"] = m.yr.map(days)
m["pu_per_day"] = m.n / m.days
m["do_per_day"] = m.n_do / m.days
m["fare_pt"] = m.fare / m.n
m["pay_pt"] = m.pay / m.n
m["mph"] = m.miles / (m.time_s / 3600)
m["wait"] = m.wait_sum / m.wait_n.replace(0, np.nan)
m["cbd_pt"] = m.cbd / m.n
m["share_to_crz"] = 100 * m.n_to_crz / m.n
w = m.pivot_table(index=["service", "zone"], columns="yr",
                  values=["pu_per_day", "do_per_day", "fare_pt", "pay_pt", "mph", "wait", "cbd_pt", "share_to_crz"])
w.columns = [f"{a}_{b}" for a, b in w.columns]
w = w.reset_index().merge(dim[["LocationID", "Zone", "Borough", "grp", "dist_to_crz_km"]],
                          left_on="zone", right_on="LocationID", how="left")
w["pu_yoy_pct"] = 100 * (w.pu_per_day_2025 / w.pu_per_day_2024 - 1)
w["do_yoy_pct"] = 100 * (w.do_per_day_2025 / w.do_per_day_2024 - 1)
w = w.sort_values(["service", "Borough", "zone"])
w.to_csv(TAB / "a01_zone_detail.csv", index=False)

# Theo tháng × nhóm
z2 = pd.read_parquet(GOLD / "zone_day_pu.parquet")
z2["d"] = pd.to_datetime(z2.d)
z2 = z2.merge(dim[["LocationID", "grp"]], left_on="zone", right_on="LocationID")
z2["ym"] = z2.d.dt.to_period("M").astype(str)
mg = z2.groupby(["service", "ym", "grp"])[S].sum().reset_index()
mg["days"] = mg.ym.map(z2.groupby("ym").d.nunique())
mg["trips_per_day"] = mg.n / mg.days
mg["fare_pt"] = mg.fare / mg.n
mg["pay_pt"] = mg.pay / mg.n
mg["mph"] = mg.miles / (mg.time_s / 3600)
mg["wait"] = mg.wait_sum / mg.wait_n.replace(0, np.nan)
mg["cbd_pt"] = mg.cbd / mg.n
mg["share_cbd"] = 100 * mg.n_cbd / mg.n
mg.to_csv(TAB / "a02_month_group_detail.csv", index=False)

# Luồng nhóm × giờ × năm
g = pd.read_parquet(GOLD / "grp_hour_day.parquet")
g["d"] = pd.to_datetime(g.d)
g = g[((g.d >= "2024-01-05") & (g.d <= "2024-12-31")) | (g.d >= P)]
g["yr"] = g.d.dt.year
fg = g.groupby(["service", "pu_grp", "do_grp", "hr", "yr"])[["n", "miles", "time_s", "fare", "pay"]].sum()
fg["mph"] = fg.miles / (fg.time_s / 3600)
fg["fare_pt"] = fg.fare / fg.n
fg = fg.reset_index()
fg["per_day"] = fg.n / fg.yr.map(days)
fg.to_csv(TAB / "a03_flow_hour_detail.csv", index=False)

(LOG / "11_appendix.json").write_text(json.dumps(dict(seconds=round(time.time() - t0, 1), zones=int(w.zone.nunique()))))
print("done", round(time.time() - t0, 1))
