"""Dựng các bảng dữ liệu bảng (panel) dùng cho phân tích nhân quả.

Tuần được định nghĩa từ Chủ nhật đến thứ Bảy, để tuần 0 bắt đầu đúng ngày
05/01/2025 (Chủ nhật), ngày đầu tiên thu phí. Nhờ vậy không có tuần nào
bị trộn lẫn ngày trước và sau chính sách.
"""
import numpy as np
import pandas as pd

from config import GOLD, POLICY_DATE

P = pd.Timestamp(POLICY_DATE)
W0 = pd.Timestamp("2024-01-07")      # Chủ nhật đầu tiên của năm 2024
W_END = pd.Timestamp("2025-12-27")   # thứ Bảy cuối cùng có đủ tuần trong dữ liệu
MIN_DAILY = {"hvfhv": 100, "yellow": 20}


def dim():
    return pd.read_parquet(GOLD / "dim_zone.parquet")


def add_ratios(g):
    g["ln_n"] = np.log(g["n"])
    g["fare_pm"] = g.fare / g.miles
    g["pay_pm"] = g.pay / g.miles
    g["fare_pt"] = g.fare / g.n
    g["pay_pt"] = g.pay / g.n
    g["mph"] = g.miles / (g.time_s / 3600)
    g["min_pt"] = g.time_s / g.n / 60
    g["miles_pt"] = g.miles / g.n
    g["wait"] = g.wait_sum / g.wait_n.replace(0, np.nan)
    g["rider_pt"] = g.rider_cost / g.n
    g["cbd_pt"] = g.cbd / g.n
    g["tips_pt"] = g.tips / g.n
    g["pay_share"] = 100 * g.pay / g.fare
    g["cbd_share"] = 100 * g.n_cbd / g.n
    g["shared_pct"] = 100 * g.shared_req / g.n
    return g


SUMS = ["n", "fare", "pay", "miles", "time_s", "tips", "cbd", "rider_cost", "cong_sur",
        "tolls", "wait_sum", "wait_n", "shared_req", "n_cbd"]


def zone_week(service="hvfhv", table="zone_day_pu", groups=("CRZ", "MN_NORTH", "OUTER"),
              min_daily=None, extra=()):
    """Panel vùng × tuần, cân bằng, chỉ giữ vùng đủ lớn trong năm 2024."""
    z = pd.read_parquet(GOLD / f"{table}.parquet")
    z = z[z.service == service].copy()
    z["d"] = pd.to_datetime(z["d"])
    z = z[(z.d >= W0) & (z.d <= W_END)]
    z["wk"] = z.d - pd.to_timedelta((z.d.dt.dayofweek + 1) % 7, unit="D")
    cols = SUMS + list(extra)
    g = z.groupby(["zone", "wk"])[cols].sum().reset_index()
    dm = dim()[["LocationID", "grp", "Borough", "Zone", "dist_to_crz_km", "ring", "area_km2"]]
    g = g.merge(dm, left_on="zone", right_on="LocationID", how="left")
    g = g[g.grp.isin(groups)]
    md = MIN_DAILY[service] if min_daily is None else min_daily
    pre = g[g.wk < P].groupby("zone")["n"].sum() / ((P - W0).days)
    keep = pre[pre >= md].index
    nweeks = g.wk.nunique()
    full = g.groupby("zone").wk.nunique()
    keep = [k for k in keep if full.get(k, 0) == nweeks]
    g = g[g.zone.isin(keep)].copy()
    g["treat"] = (g.grp == "CRZ").astype(int)
    g["post"] = (g.wk >= P).astype(int)
    g["D"] = g.treat * g.post
    g["k"] = ((g.wk - P).dt.days // 7).astype(int)
    g["woy"] = ((g.wk - pd.Timestamp("2024-01-07")).dt.days // 7) % 52
    g["w_pre"] = g.zone.map(pre)
    g["month"] = g.wk.dt.to_period("M").astype(str)
    return add_ratios(g)


def zone_day(service="hvfhv", groups=("CRZ", "MN_NORTH", "OUTER"), min_daily=None):
    z = pd.read_parquet(GOLD / "zone_day_pu.parquet")
    z = z[z.service == service].copy()
    z["d"] = pd.to_datetime(z["d"])
    dm = dim()[["LocationID", "grp"]]
    z = z.merge(dm, left_on="zone", right_on="LocationID")
    z = z[z.grp.isin(groups)]
    md = MIN_DAILY[service] if min_daily is None else min_daily
    pre = z[z.d < P].groupby("zone")["n"].sum() / 366
    z = z[z.zone.isin(pre[pre >= md].index)].copy()
    # cân bằng: điền 0 không cần vì vùng lớn luôn có chuyến; bỏ ngày thiếu
    z["treat"] = (z.grp == "CRZ").astype(int)
    z["post"] = (z.d >= P).astype(int)
    z["D"] = z.treat * z.post
    z["weekend"] = (z.d.dt.dayofweek >= 5).astype(int)
    return add_ratios(z)


def od_month(service="hvfhv", min_monthly=300):
    """Panel cặp vùng (điểm đón, điểm trả) × tháng, cân bằng 24 tháng."""
    o = pd.read_parquet(GOLD / "od_month.parquet")
    o = o[o.service == service].copy()
    dm = dim().set_index("LocationID")["grp"]
    o["pu_grp"] = o.pu.map(dm)
    o["do_grp"] = o.dl.map(dm)
    ok = ["CRZ", "MN_NORTH", "OUTER"]
    o = o[o.pu_grp.isin(ok) & o.do_grp.isin(ok)]
    o["pair"] = o.pu.astype(str) + "_" + o.dl.astype(str)
    pre = o[o.ym < "2025-01"].groupby("pair")["n"].mean()
    cnt = o.groupby("pair").ym.nunique()
    keep = pre[(pre >= min_monthly)].index.intersection(cnt[cnt == 24].index)
    o = o[o.pair.isin(keep)].copy()
    o["touch"] = ((o.pu_grp == "CRZ") | (o.do_grp == "CRZ")).astype(int)
    o["ftype"] = np.select([(o.pu_grp == "CRZ") & (o.do_grp == "CRZ"), o.pu_grp == "CRZ", o.do_grp == "CRZ"],
                           ["CRZ→CRZ", "CRZ→ngoài", "ngoài→CRZ"], "không chạm CRZ")
    o["post"] = (o.ym >= "2025-01").astype(int)
    o["D"] = o.touch * o.post
    o["w_pre"] = o.pair.map(pre)
    o["k"] = o.ym.map({m: i - 12 for i, m in enumerate(sorted(o.ym.unique()))})
    return add_ratios(o)


def zone_hour_month(service="hvfhv", groups=("CRZ", "MN_NORTH", "OUTER"), min_daily=None):
    h = pd.read_parquet(GOLD / "zone_hour_month.parquet")
    h = h[h.service == service].copy()
    dm = dim()[["LocationID", "grp"]]
    h = h.merge(dm, left_on="zone", right_on="LocationID")
    h = h[h.grp.isin(groups)]
    md = MIN_DAILY[service] if min_daily is None else min_daily
    pre = h[h.ym < "2025-01"].groupby("zone")["n"].sum() / 366
    h = h[h.zone.isin(pre[pre >= md].index)].copy()
    bins = [(0, 5, "00–05"), (6, 9, "06–09"), (10, 15, "10–15"), (16, 19, "16–19"), (20, 23, "20–23")]
    h["hbin"] = pd.cut(h.hr, [-1] + [b[1] for b in bins], labels=[b[2] for b in bins]).astype(str)
    g = h.groupby(["zone", "grp", "ym", "hbin"])[SUMS].sum().reset_index()
    g["treat"] = (g.grp == "CRZ").astype(int)
    g["post"] = (g.ym >= "2025-01").astype(int)
    g["D"] = g.treat * g.post
    return add_ratios(g)
