"""Bước 6 - Phân tích khám phá (EDA) trên các bảng Gold.

Sinh các bảng mô tả và hình ảnh phục vụ Chương 3-4 của báo cáo:
quy mô dữ liệu, chất lượng dữ liệu, bản đồ nhóm vùng, chuỗi thời gian số
chuyến theo nhóm, doanh thu phí CBD, cấu trúc theo giờ, tốc độ, thời gian chờ,
giá cước và thị phần hãng.

Chạy:  python code/06_eda.py
"""
import json
import time

import matplotlib.dates as mdates
import numpy as np
import pandas as pd
from matplotlib.collections import PolyCollection
from matplotlib.patches import Patch

from config import GOLD, LOG, TAB, POLICY_DATE
from viz import C, GROUP_COLOR, GROUP_LABEL, SEQ, fig, plt, policy_line, save

t0 = time.time()
P = pd.Timestamp(POLICY_DATE)
dim = pd.read_parquet(GOLD / "dim_zone.parquet")
zpu = pd.read_parquet(GOLD / "zone_day_pu.parquet")
zpu["d"] = pd.to_datetime(zpu["d"])
zpu = zpu.merge(dim[["LocationID", "grp", "Borough", "Zone"]], left_on="zone", right_on="LocationID", how="left")
ghd = pd.read_parquet(GOLD / "grp_hour_day.parquet")
ghd["d"] = pd.to_datetime(ghd["d"])
cgd = pd.read_parquet(GOLD / "company_grp_day.parquet")
cgd["d"] = pd.to_datetime(cgd["d"])
q = pd.read_csv(TAB / "t06_quality_by_month.csv")
man = pd.read_csv(TAB / "t01_bronze_manifest.csv")
out = {}

# ---------------- H1. Quy mô dữ liệu theo tháng ----------------
f, ax = fig(6.6, 3.2)
m = man.pivot(index="month", columns="service", values="n_rows") / 1e6
x = np.arange(len(m))
ax.bar(x - 0.2, m["hvfhv"], width=0.38, color=C["s1"], label="HVFHV (Uber, Lyft)")
ax.bar(x + 0.2, m["yellow"], width=0.38, color=C["s2"], label="Taxi vàng")
ax.set_xticks(x[::2], [s[2:] for s in m.index[::2]], rotation=0)
ax.set_ylabel("Triệu chuyến / tháng")
ax.set_title("Số bản ghi thô theo tháng và theo dịch vụ, 2024–2025")
ax.legend(loc="upper left", ncol=2)
save(f, "f01_rows_by_month")

# ---------------- H2. Tỷ lệ loại bỏ theo quy tắc ----------------
rules = ["q_bad_zone", "q_bad_miles", "q_bad_time", "q_bad_fare", "q_bad_speed", "q_bad_pay", "q_out_of_month"]
lab = {"q_bad_zone": "Vùng không xác định (264/265)", "q_bad_miles": "Quãng đường ≤0 hoặc >100 dặm",
       "q_bad_time": "Thời gian <1 phút hoặc >4 giờ", "q_bad_fare": "Giá cước ≤0 hoặc >1000 USD",
       "q_bad_speed": "Tốc độ >80 mph", "q_bad_pay": "Thu nhập tài xế âm/thiếu",
       "q_out_of_month": "Thời điểm ngoài tháng tệp"}
qs = q.groupby("service")[rules + ["n_raw"]].sum()
rate = qs[rules].div(qs["n_raw"], axis=0) * 100
rate.T.rename(index=lab).to_csv(TAB / "t13_reject_rate_by_rule.csv")
f, ax = fig(6.6, 3.4)
y = np.arange(len(rules))
ax.barh(y + 0.2, rate.loc["hvfhv", rules], height=0.38, color=C["s1"], label="HVFHV")
ax.barh(y - 0.2, rate.loc["yellow", rules], height=0.38, color=C["s2"], label="Taxi vàng")
ax.set_yticks(y, [lab[r] for r in rules])
ax.invert_yaxis()
ax.set_xlabel("% số bản ghi thô (một bản ghi có thể vi phạm nhiều quy tắc)")
ax.set_title("Tỷ lệ bản ghi vi phạm từng quy tắc chất lượng")
ax.legend(loc="lower right")
save(f, "f02_reject_by_rule")

# ---------------- H3. Bản đồ nhóm vùng ----------------
poly = pd.read_parquet(GOLD / "zone_polygons.parquet")
grp_of = dim.set_index("LocationID")["grp"].to_dict()


def draw_map(ax, values=None, cmap=None, norm=None, cats=None):
    verts, cols = [], []
    for (lid, part), g in poly.groupby(["LocationID", "part"]):
        verts.append(np.c_[g.x.values, g.y.values])
        if cats is not None:
            cols.append(cats.get(lid, "#ffffff"))
        else:
            v = values.get(lid, np.nan)
            cols.append("#f0efec" if pd.isna(v) else cmap(norm(v)))
    pc = PolyCollection(verts, facecolors=cols, edgecolors="#ffffff", linewidths=0.35)
    ax.add_collection(pc)
    ax.autoscale_view()
    ax.set_aspect("equal")
    ax.axis("off")


f, ax = fig(6.2, 6.2)
draw_map(ax, cats={k: GROUP_COLOR[v] for k, v in grp_of.items()})
hand = [Patch(facecolor=GROUP_COLOR[g], label=f"{GROUP_LABEL[g]} ({(dim.grp == g).sum()} vùng)")
        for g in ["CRZ", "CRZ_PARTIAL", "MN_NORTH", "OUTER", "AIRPORT"]]
ax.legend(handles=hand, loc="upper left", fontsize=8.5)
ax.set_title("Phân nhóm 263 vùng taxi theo mức độ chịu phí CBD (xác định từ dữ liệu quý I/2025)")
save(f, "f03_zone_group_map")

f, ax = fig(4.6, 6.2)
mh = dim[dim.Borough == "Manhattan"].LocationID.tolist()
poly_m = poly[poly.LocationID.isin(mh)]
poly_bak = poly
poly = poly_m
draw_map(ax, cats={k: GROUP_COLOR[v] for k, v in grp_of.items()})
for _, r in dim[dim.Borough == "Manhattan"].iterrows():
    if r.grp in ("CRZ_PARTIAL",):
        ax.annotate(str(r.LocationID), (r.cx_ft, r.cy_ft), fontsize=6.5, ha="center", color=C["text"])
ax.set_title("Manhattan: vùng CRZ và các vùng vắt qua ranh giới")
ax.legend(handles=hand[:3], loc="upper left", fontsize=8)
save(f, "f04_manhattan_map")
poly = poly_bak

# ---------------- H4. Chuỗi số chuyến theo ngày ----------------
hv = zpu[zpu.service == "hvfhv"]
daily = hv.groupby(["d", "grp"])["n"].sum().unstack()
daily.to_csv(TAB / "t14_daily_trips_by_group_hvfhv.csv")
f, ax = fig(6.8, 3.4)
for g in ["CRZ", "MN_NORTH", "OUTER"]:
    s = daily[g].rolling(7, center=True).mean() / 1e3
    ax.plot(s.index, s.values, color=GROUP_COLOR[g] if g != "OUTER" else C["s2"], label=GROUP_LABEL[g])
policy_line(ax, P)
ax.set_ylabel("Nghìn chuyến / ngày (TB trượt 7 ngày)")
ax.set_title("Số chuyến HVFHV theo nhóm vùng đón khách")
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=3)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%y"))
save(f, "f05_daily_trips_by_group")

# Chỉ số hóa so với cùng kỳ: tỷ lệ 2025/2024 theo tuần ISO
hv_w = hv.assign(y=hv.d.dt.isocalendar().year, w=hv.d.dt.isocalendar().week)
wk = hv_w.groupby(["y", "w", "grp"])["n"].sum().unstack().reset_index()
wk = wk[(wk.w >= 2) & (wk.w <= 51)]
yoy = wk.pivot(index="w", columns="y")
ratio = pd.DataFrame({g: 100 * (yoy[(g, 2025)] / yoy[(g, 2024)] - 1) for g in ["CRZ", "MN_NORTH", "OUTER", "AIRPORT"]})
ratio.to_csv(TAB / "t15_weekly_yoy_pct_by_group_hvfhv.csv")
f, ax = fig(6.8, 3.4)
for g, col in (("CRZ", C["s1"]), ("MN_NORTH", C["s3"]), ("OUTER", C["s2"])):
    ax.plot(ratio.index, ratio[g], color=col, label=GROUP_LABEL[g], marker="o", ms=3)
ax.axhline(0, color=C["text2"], lw=0.8)
ax.set_xlabel("Tuần ISO (2025 so với cùng tuần 2024)")
ax.set_ylabel("% thay đổi số chuyến so với cùng kỳ")
ax.set_title("Tăng trưởng cùng kỳ số chuyến HVFHV theo tuần, 2025 so với 2024")
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=3)
save(f, "f06_weekly_yoy_by_group")

# ---------------- H5. Doanh thu phí CBD ----------------
allz = zpu.assign(ym=zpu.d.dt.to_period("M").astype(str))
rev = allz[allz.d >= P].groupby(["ym", "service"]).agg(cbd=("cbd", "sum"), n=("n", "sum"), n_cbd=("n_cbd", "sum")).reset_index()
rev["share_charged"] = 100 * rev.n_cbd / rev.n
rev["avg_fee_charged"] = rev.cbd / rev.n_cbd
rev.to_csv(TAB / "t16_cbd_revenue_by_month.csv", index=False)
out["cbd_total_2025_hvfhv_musd"] = float(rev[rev.service == "hvfhv"].cbd.sum() / 1e6)
out["cbd_total_2025_yellow_musd"] = float(rev[rev.service == "yellow"].cbd.sum() / 1e6)
rp = rev.pivot(index="ym", columns="service", values="cbd") / 1e6
f, ax = fig(6.6, 3.2)
x = np.arange(len(rp))
ax.bar(x - 0.2, rp["hvfhv"], width=0.38, color=C["s1"], label="HVFHV (1,50 USD/chuyến)")
ax.bar(x + 0.2, rp["yellow"], width=0.38, color=C["s2"], label="Taxi vàng (0,75 USD/chuyến)")
ax.set_xticks(x, [s[5:] + "/25" for s in rp.index])
ax.set_ylabel("Triệu USD")
ax.set_title("Tổng phí CBD ghi nhận trong dữ liệu chuyến đi theo tháng, 2025")
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=2)
save(f, "f07_cbd_revenue")

# ---------------- H6. Cấu trúc luồng giữa các nhóm ----------------
hvg = ghd[ghd.service == "hvfhv"].copy()
hvg["post"] = hvg.d >= P
hvg["yr"] = hvg.d.dt.year
flow = hvg.groupby(["yr", "pu_grp", "do_grp"])["n"].sum().unstack("do_grp").fillna(0)
flow.to_csv(TAB / "t17_flow_matrix_by_year_hvfhv.csv")
share = hvg.groupby(["yr", "pu_grp", "do_grp"])["n"].sum()
share = (share / share.groupby("yr").transform("sum") * 100).unstack("yr")
share["change_pp"] = share[2025] - share[2024]
share.reset_index().to_csv(TAB / "t18_flow_share_change_hvfhv.csv", index=False)

# ---------------- H7. Hồ sơ theo giờ ----------------
crz_touch = hvg[(hvg.pu_grp == "CRZ") | (hvg.do_grp == "CRZ")]
hp = crz_touch.groupby(["yr", "hr"])["n"].sum().unstack("yr")
ndays = hvg.groupby("yr").d.nunique()
hp = hp / ndays
hp.to_csv(TAB / "t19_hour_profile_crz_touch.csv")
f, ax = fig(6.6, 3.2)
ax.plot(hp.index, hp[2024] / 1e3, color=C["s2"], label="2024", marker="o", ms=3)
ax.plot(hp.index, hp[2025] / 1e3, color=C["s1"], label="2025", marker="o", ms=3)
ax.set_xticks(range(0, 24, 2))
ax.set_xlabel("Giờ đón khách")
ax.set_ylabel("Nghìn chuyến / ngày")
ax.set_title("Chuyến HVFHV có điểm đầu hoặc cuối trong CRZ, trung bình theo giờ")
ax.legend()
save(f, "f08_hour_profile_crz")

# ---------------- H8. Tốc độ trong CRZ theo giờ ----------------
intra = hvg[(hvg.pu_grp == "CRZ") & (hvg.do_grp == "CRZ")]
sp = intra.groupby(["yr", "hr"])[["miles", "time_s"]].sum()
sp["mph"] = sp.miles / (sp.time_s / 3600)
spd = sp["mph"].unstack("yr")
spd.to_csv(TAB / "t20_speed_intra_crz_by_hour.csv")
f, ax = fig(6.6, 3.2)
ax.plot(spd.index, spd[2024], color=C["s2"], label="2024", marker="o", ms=3)
ax.plot(spd.index, spd[2025], color=C["s1"], label="2025", marker="o", ms=3)
ax.set_xticks(range(0, 24, 2))
ax.set_xlabel("Giờ đón khách")
ax.set_ylabel("Tốc độ trung bình (dặm/giờ)")
ax.set_title("Tốc độ trung bình của chuyến HVFHV nội vùng CRZ theo giờ")
ax.legend()
save(f, "f09_speed_intra_crz_hour")

# Tốc độ theo tháng cho 3 loại luồng
def mph_series(df):
    g = df.groupby(df.d.dt.to_period("M"))[["miles", "time_s"]].sum()
    return g.miles / (g.time_s / 3600)


sp_m = pd.DataFrame({
    "CRZ→CRZ": mph_series(hvg[(hvg.pu_grp == "CRZ") & (hvg.do_grp == "CRZ")]),
    "MN bắc→MN bắc": mph_series(hvg[(hvg.pu_grp == "MN_NORTH") & (hvg.do_grp == "MN_NORTH")]),
    "Quận ngoài→Quận ngoài": mph_series(hvg[(hvg.pu_grp == "OUTER") & (hvg.do_grp == "OUTER")]),
})
sp_m.index = sp_m.index.astype(str)
sp_m.to_csv(TAB / "t21_speed_by_month_flow.csv")
f, ax = fig(6.8, 3.3)
for (k, col) in zip(sp_m.columns, (C["s1"], C["s3"], C["s2"])):
    ax.plot(pd.to_datetime(sp_m.index), sp_m[k], color=col, label=k, marker="o", ms=3)
policy_line(ax, P)
ax.set_ylabel("Dặm/giờ")
ax.set_title("Tốc độ trung bình theo tháng của ba loại luồng chuyến HVFHV")
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=3)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%y"))
save(f, "f10_speed_by_month")

# ---------------- H9. Giá cước, thu nhập tài xế theo tháng ----------------
def per_trip(df):
    g = df.groupby(df.d.dt.to_period("M"))[["n", "fare", "pay", "miles", "rider_cost", "tips", "wait_sum", "wait_n", "cbd"]].sum()
    return pd.DataFrame({"fare_per_trip": g.fare / g.n, "pay_per_trip": g.pay / g.n,
                         "fare_per_mile": g.fare / g.miles, "pay_per_mile": g.pay / g.miles,
                         "rider_cost_per_trip": g.rider_cost / g.n, "tips_per_trip": g.tips / g.n,
                         "pay_share_of_fare": 100 * g.pay / g.fare, "wait_min": g.wait_sum / g.wait_n,
                         "cbd_per_trip": g.cbd / g.n})


touch = hvg[(hvg.pu_grp == "CRZ") | (hvg.do_grp == "CRZ")]
notouch = hvg[(hvg.pu_grp != "CRZ") & (hvg.do_grp != "CRZ") & (hvg.pu_grp.isin(["MN_NORTH", "OUTER"])) & (hvg.do_grp.isin(["MN_NORTH", "OUTER"]))]
pt = pd.concat({"touch_crz": per_trip(touch), "no_touch": per_trip(notouch)}, axis=1)
pt.index = pt.index.astype(str)
pt.to_csv(TAB / "t22_price_pay_by_month.csv")
for var, ttl, yl, nm in (("fare_per_mile", "Giá cước cơ sở trên mỗi dặm", "USD/dặm", "f11_fare_per_mile"),
                         ("pay_per_mile", "Thu nhập tài xế trên mỗi dặm", "USD/dặm", "f12_pay_per_mile"),
                         ("wait_min", "Thời gian chờ từ lúc gọi xe đến lúc đón", "Phút", "f13_wait_time"),
                         ("pay_share_of_fare", "Thu nhập tài xế so với giá cước cơ sở", "%", "f14_pay_share")):
    f, ax = fig(6.6, 3.1)
    xx = pd.to_datetime(pt.index)
    ax.plot(xx, pt[("touch_crz", var)], color=C["s1"], label="Chuyến chạm CRZ", marker="o", ms=3)
    ax.plot(xx, pt[("no_touch", var)], color=C["s2"], label="Chuyến không chạm CRZ", marker="o", ms=3)
    policy_line(ax, P)
    ax.set_ylabel(yl)
    ax.set_title(ttl + " (HVFHV, theo tháng)")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=2)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%y"))
    save(f, nm)

# ---------------- H10. Thị phần hãng ----------------
cg = cgd[cgd.service == "hvfhv"].copy()
cg["ym"] = cg.d.dt.to_period("M").astype(str)
cs = cg.groupby(["ym", "company_code"])["n"].sum().unstack().fillna(0)
cs = cs.div(cs.sum(axis=1), axis=0) * 100
cs.to_csv(TAB / "t23_company_share_by_month.csv")
cz = cg[(cg.pu_grp == "CRZ") | (cg.do_grp == "CRZ")].groupby(["ym", "company_code"])["n"].sum().unstack().fillna(0)
cz = cz.div(cz.sum(axis=1), axis=0) * 100
cz.to_csv(TAB / "t24_company_share_crz_by_month.csv")
f, ax = fig(6.6, 3.1)
xx = pd.to_datetime(cs.index)
ax.plot(xx, cs["HV0003"], color=C["s1"], label="Uber, toàn thành phố", marker="o", ms=3)
ax.plot(xx, cz["HV0003"], color=C["s3"], label="Uber, chuyến chạm CRZ", marker="o", ms=3)
policy_line(ax, P)
ax.set_ylabel("% số chuyến HVFHV")
ax.set_title("Thị phần Uber theo tháng (phần còn lại chủ yếu là Lyft)")
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=2)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%y"))
save(f, "f15_company_share")

# ---------------- H11. Bản đồ thay đổi cùng kỳ theo vùng ----------------
zy = hv.assign(yr=hv.d.dt.year).query("d.dt.dayofyear >= 5")
zz = zy.groupby(["zone", "yr"])["n"].sum().unstack()
zz = zz[(zz[2024] >= 5000)]
zz["yoy_pct"] = 100 * (zz[2025] / zz[2024] - 1)
zz = zz.join(dim.set_index("LocationID")[["Zone", "Borough", "grp"]])
zz.reset_index().to_csv(TAB / "t25_zone_yoy_pickups.csv", index=False)
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
cmap = LinearSegmentedColormap.from_list("div", [C["div_neg"], C["div_mid"], C["div_pos"]])
lim = float(np.nanpercentile(np.abs(zz.yoy_pct), 95))
norm = TwoSlopeNorm(vmin=-lim, vcenter=0, vmax=lim)
f, ax = fig(6.2, 6.4)
draw_map(ax, values=zz["yoy_pct"].to_dict(), cmap=cmap, norm=norm)
sm = plt.cm.ScalarMappable(norm=norm, cmap=cmap)
cb = f.colorbar(sm, ax=ax, shrink=0.55, pad=0.01)
cb.set_label("% thay đổi số chuyến đón 2025 so với 2024")
ax.set_title("Thay đổi cùng kỳ số chuyến HVFHV theo vùng đón (từ 05/01)")
save(f, "f16_zone_yoy_map")

# ---------------- Bảng mô tả tổng hợp theo nhóm và năm ----------------
desc = hv.assign(yr=hv.d.dt.year).groupby(["grp", "yr"]).agg(
    trips=("n", "sum"), fare=("fare", "sum"), pay=("pay", "sum"), miles=("miles", "sum"),
    time_s=("time_s", "sum"), cbd=("cbd", "sum"), rider_cost=("rider_cost", "sum"),
    wait_sum=("wait_sum", "sum"), wait_n=("wait_n", "sum"), tips=("tips", "sum"))
desc["trips_per_day"] = desc.trips / desc.index.get_level_values("yr").map({2024: 366, 2025: 365})
desc["fare_per_trip"] = desc.fare / desc.trips
desc["pay_per_trip"] = desc.pay / desc.trips
desc["miles_per_trip"] = desc.miles / desc.trips
desc["min_per_trip"] = desc.time_s / desc.trips / 60
desc["mph"] = desc.miles / (desc.time_s / 3600)
desc["wait_min"] = desc.wait_sum / desc.wait_n
desc["cbd_per_trip"] = desc.cbd / desc.trips
desc["tips_per_trip"] = desc.tips / desc.trips
desc.reset_index().to_csv(TAB / "t26_desc_by_group_year_hvfhv.csv", index=False)

yl = zpu[zpu.service == "yellow"]
descy = yl.assign(yr=yl.d.dt.year).groupby(["grp", "yr"]).agg(trips=("n", "sum"), fare=("fare", "sum"),
                                                              miles=("miles", "sum"), time_s=("time_s", "sum"),
                                                              cbd=("cbd", "sum"), tips=("tips", "sum"))
descy["fare_per_trip"] = descy.fare / descy.trips
descy["mph"] = descy.miles / (descy.time_s / 3600)
descy["cbd_per_trip"] = descy.cbd / descy.trips
descy.reset_index().to_csv(TAB / "t27_desc_by_group_year_yellow.csv", index=False)

# Taxi vàng và HVFHV: số chuyến đón trong CRZ theo tuần (chỉ số)
both = zpu[zpu.grp == "CRZ"].groupby(["service", pd.Grouper(key="d", freq="W-SUN")])["n"].sum().unstack("service")
base = both[(both.index >= "2024-01-08") & (both.index < "2024-12-30")].mean()
idx = both / base * 100
idx.to_csv(TAB / "t28_weekly_index_crz_by_service.csv")
f, ax = fig(6.8, 3.2)
ax.plot(idx.index, idx["hvfhv"], color=C["s1"], label="HVFHV")
ax.plot(idx.index, idx["yellow"], color=C["s2"], label="Taxi vàng")
policy_line(ax, P)
ax.set_ylabel("Chỉ số (TB tuần năm 2024 = 100)")
ax.set_title("Số chuyến đón trong CRZ theo tuần, HVFHV và taxi vàng")
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=2)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%y"))
save(f, "f17_weekly_index_crz_services")

# Phân phối giá cước/chuyến từ mẫu chuyến (0,25% HVFHV)
smp = pd.read_parquet(GOLD / "trip_sample.parquet", columns=["service", "d", "fare", "rider_cost", "miles", "touch_crz", "cbd_fee", "mph"])
smp = smp[smp.service == "hvfhv"]
smp["yr"] = pd.to_datetime(smp.d).dt.year
smp["fpm"] = smp.fare / smp.miles
qq = smp.groupby(["touch_crz", "yr"])["rider_cost"].quantile([0.1, 0.25, 0.5, 0.75, 0.9]).unstack()
qq.to_csv(TAB / "t29_rider_cost_quantiles_sample.csv")
f, axs = fig(6.8, 3.2, ncols=2, sharey=True)
bins = np.linspace(0, 80, 81)
for ax, tc, ttl in ((axs[0], 1, "Chuyến chạm CRZ"), (axs[1], 0, "Chuyến không chạm CRZ")):
    for yr, col in ((2024, C["s2"]), (2025, C["s1"])):
        v = smp[(smp.touch_crz == tc) & (smp.yr == yr)].rider_cost
        ax.hist(v.clip(upper=80), bins=bins, density=True, histtype="step", color=col, lw=1.6, label=str(yr))
    ax.set_title(ttl)
    ax.set_xlabel("Tổng chi phí hành khách/chuyến (USD, chưa gồm tip)")
axs[0].set_ylabel("Mật độ")
axs[0].legend()
save(f, "f18_rider_cost_hist")
out["n_sample_hvfhv"] = int(len(smp))

# Taxi vàng: số chuyến theo nhà cung cấp (VendorID) × năm × nhóm vùng đón, đọc trực tiếp từ Bronze
from config import RAW, duck
con = duck()
con.execute(f"CREATE TEMP TABLE z AS SELECT LocationID, grp FROM '{(GOLD / 'dim_zone.parquet').as_posix()}'")
vend = con.execute(f"""
    SELECT year(tpep_pickup_datetime) AS yr, VendorID AS vendor, coalesce(z.grp, 'UNKNOWN') AS pu_grp, count(*) AS n
    FROM read_parquet('{(RAW / 'yellow_tripdata_202*.parquet').as_posix()}') y
    LEFT JOIN z ON y.PULocationID = z.LocationID
    WHERE year(tpep_pickup_datetime) IN (2024, 2025)
    GROUP BY ALL ORDER BY ALL""").df()
vend.to_csv(TAB / "t27b_yellow_vendor_by_year_group.csv", index=False)

(LOG / "06_eda.json").write_text(json.dumps(dict(seconds=round(time.time() - t0, 1), **out), indent=2))
print(out, "time", round(time.time() - t0, 1))
