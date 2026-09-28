"""Bước 14 - Phân tích bổ sung.

(a) Tác động riêng cho từng vùng CRZ: TWFE với tương tác D × vùng; quan hệ giữa tác
    động và đặc trưng vùng (lưu lượng, khoảng cách tới ranh giới bên trong CRZ, tỷ trọng
    chuyến nội vùng).
(b) Lan tỏa theo dải khoảng cách, tách riêng theo quận.
(c) Sai khác kép mô tả của tốc độ theo giờ × loại ngày: (CRZ→CRZ) so với (quận ngoài→quận ngoài).
(d) Chuyến sân bay: số chuyến/ngày của các luồng sân bay, cùng kỳ 2025/2024.
(e) Thành phần quãng đường: tỷ trọng chuyến ngắn trong mẫu chuyến, CRZ so với nơi khác.

Chạy:  python code/14_extra_analysis.py
"""
import json
import time

import numpy as np
import pandas as pd
from matplotlib.collections import PolyCollection
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from shapely.geometry import Polygon
from shapely.ops import unary_union

from causal import fe_ols
from config import GOLD, LOG, TAB
from panels import P, zone_week
from viz import C, fig, plt, save

t0 = time.time()
meta = {}
dim = pd.read_parquet(GOLD / "dim_zone.parquet")

# ---------------- (a) Tác động theo từng vùng CRZ ----------------
zw = zone_week("hvfhv", extra=("n_to_crz",))
crz_zones = sorted(zw[zw.treat == 1].zone.unique())
names = []
for z in crz_zones:
    nm = f"D_{z}"
    zw[nm] = ((zw.zone == z) & (zw.post == 1)).astype(float)
    names.append(nm)
rows = []
for y in ("ln_n", "mph", "wait"):
    res, info, _ = fe_ols(zw, y, names, ["zone", "wk"], "zone")
    for (_, r), z in zip(res.iterrows(), crz_zones):
        rows.append(dict(zone=z, outcome=y, coef=r.coef, se=r.se, p=r.p, ci_low=r.ci_low, ci_high=r.ci_high))
ze = pd.DataFrame(rows)
pre = zw[zw.post == 0].groupby("zone").agg(n=("n", "sum"), n_to_crz=("n_to_crz", "sum"), miles=("miles", "sum"),
                                           time_s=("time_s", "sum"), fare=("fare", "sum"))
pre["pre_per_day"] = pre.n / ((P - pd.Timestamp("2024-01-07")).days)
pre["share_to_crz"] = 100 * pre.n_to_crz / pre.n
pre["mph_pre"] = pre.miles / (pre.time_s / 3600)
pre["fare_pt_pre"] = pre.fare / pre.n

# Khoảng cách từ tâm vùng CRZ tới ranh giới ngoài của CRZ (độ "sâu" bên trong vùng)
poly = pd.read_parquet(GOLD / "zone_polygons.parquet")
geoms = {}
for (lid, part), g in poly.groupby(["LocationID", "part"]):
    if len(g) >= 3:
        pg = Polygon(np.c_[g.x.values, g.y.values]).buffer(0)
        geoms[lid] = unary_union([geoms[lid], pg]) if lid in geoms else pg
crz_all = unary_union([geoms[z] for z in dim[dim.grp == "CRZ"].LocationID if z in geoms])
depth = {}
for z in crz_zones:
    if z in geoms:
        depth[z] = geoms[z].centroid.distance(crz_all.exterior if crz_all.geom_type == "Polygon"
                                              else unary_union([p.exterior for p in crz_all.geoms])) * 0.0003048
zi = ze.pivot(index="zone", columns="outcome", values="coef").add_prefix("b_")
zs = ze.pivot(index="zone", columns="outcome", values="se").add_prefix("se_")
zt = zi.join(zs).join(pre[["pre_per_day", "share_to_crz", "mph_pre", "fare_pt_pre"]])
zt["depth_km"] = zt.index.map(depth)
zt = zt.join(dim.set_index("LocationID")[["Zone"]])
zt["pct_ln_n"] = 100 * (np.exp(zt.b_ln_n) - 1)
zt.reset_index().to_csv(TAB / "t54_zone_specific_effects.csv", index=False)

# Hồi quy tác động theo vùng lên đặc trưng vùng (trọng số nghịch đảo phương sai)
import statsmodels.api as sm
Xd = pd.DataFrame({"log_pre_per_day": np.log(zt.pre_per_day), "share_to_crz": zt.share_to_crz,
                   "depth_km": zt.depth_km, "fare_pt_pre": zt.fare_pt_pre}).dropna()
mr = []
for y in ("b_ln_n", "b_mph"):
    yy = zt.loc[Xd.index, y]
    w = 1 / zt.loc[Xd.index, y.replace("b_", "se_")] ** 2
    m = sm.WLS(yy, sm.add_constant(Xd), weights=w).fit(cov_type="HC1")
    for k in m.params.index:
        mr.append(dict(outcome=y, term=k, coef=m.params[k], se=m.bse[k], p=m.pvalues[k], r2=m.rsquared, n=int(m.nobs)))
pd.DataFrame(mr).to_csv(TAB / "t55_zone_effect_meta_regression.csv", index=False)

# Bản đồ tác động theo vùng CRZ
cmap = LinearSegmentedColormap.from_list("div", [C["div_neg"], C["div_mid"], C["div_pos"]])
vals = zt.pct_ln_n.to_dict()
lim = float(np.nanmax(np.abs(zt.pct_ln_n)))
norm = TwoSlopeNorm(vmin=-lim, vcenter=0, vmax=lim)
mh = dim[dim.Borough == "Manhattan"].LocationID.tolist()
f, ax = fig(4.8, 6.4)
verts, cols = [], []
for (lid, part), g in poly[poly.LocationID.isin(mh)].groupby(["LocationID", "part"]):
    verts.append(np.c_[g.x.values, g.y.values])
    cols.append(cmap(norm(vals[lid])) if lid in vals else "#e4e3df")
ax.add_collection(PolyCollection(verts, facecolors=cols, edgecolors="#ffffff", linewidths=0.4))
ax.autoscale_view()
ax.set_aspect("equal")
ax.axis("off")
ax.set_ylim(ax.get_ylim()[0], ax.get_ylim()[0] + 0.55 * (ax.get_ylim()[1] - ax.get_ylim()[0]))
sm_ = plt.cm.ScalarMappable(norm=norm, cmap=cmap)
cb = f.colorbar(sm_, ax=ax, shrink=0.6, pad=0.01)
cb.set_label("% thay đổi số chuyến đón (DiD theo vùng)")
ax.set_title("Tác động DiD riêng của từng vùng CRZ")
save(f, "f38_zone_effects_map")

f, axs = fig(6.8, 3.0, ncols=2)
axs[0].scatter(np.log10(zt.pre_per_day), zt.pct_ln_n, s=22, color=C["s1"])
axs[0].axhline(0, color=C["text2"], lw=0.8)
axs[0].set_xlabel("log10 chuyến đón/ngày năm 2024")
axs[0].set_ylabel("% thay đổi số chuyến (DiD vùng)")
axs[0].set_title("Theo quy mô vùng", fontsize=9.5)
axs[1].scatter(zt.depth_km, zt.pct_ln_n, s=22, color=C["s1"])
axs[1].axhline(0, color=C["text2"], lw=0.8)
axs[1].set_xlabel("Khoảng cách từ tâm vùng tới ranh giới CRZ (km)")
axs[1].set_title("Theo độ sâu trong CRZ", fontsize=9.5)
f.suptitle("Tác động theo vùng CRZ và đặc trưng vùng", x=0.02, ha="left", fontsize=10.5, fontweight="bold")
f.tight_layout()
save(f, "f39_zone_effects_scatter")
meta["zone_effects"] = dict(n=int(len(zt)), n_negative=int((zt.b_ln_n < 0).sum()),
                            n_sig_negative=int(((zt.b_ln_n + 1.96 * zt.se_ln_n) < 0).sum()),
                            n_mph_positive=int((zt.b_mph > 0).sum()))

# ---------------- (b) Lan tỏa theo quận ----------------
pu = zone_week("hvfhv", groups=("CRZ", "CRZ_PARTIAL", "MN_NORTH", "OUTER"))
pu = pu[pu.grp != "CRZ"].copy()
pu["near"] = (pu.dist_to_crz_km <= 5).astype(int)
rows = []
for b in ["Manhattan", "Brooklyn", "Queens", "Bronx"]:
    pu[f"D_{b}"] = ((pu.Borough == b) & (pu.near == 1) & (pu.post == 1)).astype(float)
res, info, _ = fe_ols(pu, "ln_n", [f"D_{b}" for b in ["Manhattan", "Brooklyn", "Queens", "Bronx"]], ["zone", "wk"], "zone")
for (_, r), b in zip(res.iterrows(), ["Manhattan", "Brooklyn", "Queens", "Bronx"]):
    rows.append(dict(borough=b, coef=r.coef, se=r.se, p=r.p, ci_low=r.ci_low, ci_high=r.ci_high,
                     n_near=int(pu[(pu.Borough == b) & (pu.near == 1)].zone.nunique())))
pd.DataFrame(rows).to_csv(TAB / "t56_spillover_by_borough.csv", index=False)

# ---------------- (c) Tốc độ theo giờ × loại ngày ----------------
g = pd.read_parquet(GOLD / "grp_hour_day.parquet")
g = g[g.service == "hvfhv"].copy()
g["d"] = pd.to_datetime(g.d)
g = g[((g.d >= "2024-01-05") & (g.d <= "2024-12-31")) | (g.d >= P)]
g["yr"] = g.d.dt.year
g["daytype"] = np.where(g.d.dt.dayofweek >= 5, "Cuối tuần", "Ngày thường")
g["flow"] = g.pu_grp + "→" + g.do_grp
sel = g[g.flow.isin(["CRZ→CRZ", "OUTER→OUTER", "MN_NORTH→MN_NORTH"])]
a = sel.groupby(["flow", "daytype", "hr", "yr"])[["miles", "time_s", "n"]].sum()
a["mph"] = a.miles / (a.time_s / 3600)
m = a["mph"].unstack("yr")
m["d"] = m[2025] - m[2024]
dd = m["d"].unstack("flow")
dd["did_vs_outer"] = dd["CRZ→CRZ"] - dd["OUTER→OUTER"]
dd["did_vs_mn"] = dd["CRZ→CRZ"] - dd["MN_NORTH→MN_NORTH"]
dd.reset_index().to_csv(TAB / "t57_speed_did_hour_daytype.csv", index=False)
f, axs = fig(6.8, 2.8, nrows=1)
hm = dd["did_vs_outer"].unstack("hr").loc[["Ngày thường", "Cuối tuần"]]
lim = float(np.nanmax(np.abs(hm.values)))
im = axs.imshow(hm.values, aspect="auto", cmap=cmap, norm=TwoSlopeNorm(vmin=-lim, vcenter=0, vmax=lim))
axs.set_yticks([0, 1], hm.index)
axs.set_xticks(range(0, 24, 2), [str(h) for h in range(0, 24, 2)])
axs.set_xlabel("Giờ đón")
axs.grid(False)
cb = f.colorbar(im, ax=axs, pad=0.01)
cb.set_label("dặm/giờ")
axs.set_title("Chênh lệch thay đổi tốc độ cùng kỳ: CRZ→CRZ trừ quận ngoài→quận ngoài")
save(f, "f40_speed_did_heatmap")

# ---------------- (d) Chuyến sân bay ----------------
air = g[(g.pu_grp == "AIRPORT") | (g.do_grp == "AIRPORT")]
ag = air.groupby(["pu_grp", "do_grp", "yr"])["n"].sum().unstack("yr")
days = g.groupby("yr").d.nunique()
ag = ag.div(days, axis=1)
ag["chg_pct"] = 100 * (ag[2025] / ag[2024] - 1)
ag.reset_index().to_csv(TAB / "t58_airport_flows.csv", index=False)

# ---------------- (e) Thành phần quãng đường ----------------
s = pd.read_parquet(GOLD / "trip_sample.parquet", columns=["service", "d", "miles", "pu_grp", "do_grp", "touch_crz"])
s = s[s.service == "hvfhv"].copy()
s["d"] = pd.to_datetime(s.d)
s = s[((s.d >= "2024-01-05") & (s.d <= "2024-12-31")) | (s.d >= P)]
s["yr"] = s.d.dt.year
bins = [0, 1, 2, 3, 5, 10, 1000]
labs = ["<1", "1–2", "2–3", "3–5", "5–10", ">10"]
s["mb"] = pd.cut(s.miles, bins, labels=labs, right=False)
comp = s.groupby(["touch_crz", "yr", "mb"], observed=True).size().unstack("mb")
comp = comp.div(comp.sum(axis=1), axis=0) * 100
comp.reset_index().to_csv(TAB / "t59_distance_composition.csv", index=False)
f, axs = fig(6.8, 3.0, ncols=2, sharey=True)
for ax, tc, ttl in ((axs[0], 1, "Chuyến chạm CRZ"), (axs[1], 0, "Chuyến không chạm CRZ")):
    xx = np.arange(len(labs))
    ax.bar(xx - 0.2, comp.loc[(tc, 2024)], width=0.38, color=C["s2"], label="2024")
    ax.bar(xx + 0.2, comp.loc[(tc, 2025)], width=0.38, color=C["s1"], label="2025")
    ax.set_xticks(xx, labs)
    ax.set_xlabel("Quãng đường (dặm)")
    ax.set_title(ttl, fontsize=9.5)
axs[0].set_ylabel("% số chuyến")
axs[0].legend()
f.suptitle("Phân bố quãng đường chuyến HVFHV (mẫu 0,25%), 05/01–31/12", x=0.02, ha="left", fontsize=10.5,
           fontweight="bold")
f.tight_layout()
save(f, "f41_distance_composition")

(LOG / "14_extra.json").write_text(json.dumps(dict(seconds=round(time.time() - t0, 1), **meta), indent=2))
print(meta, round(time.time() - t0, 1))
