"""Bước 18 - Kiểm định các giả thuyết suy ra từ mô hình lý thuyết (mục 2.11 của báo cáo).

Kiểm định giả thuyết:
  H1b  Liều – đáp ứng theo tỷ trọng phí trong giá: DiD trên panel OD × tháng, tách cặp chạm CRZ
       theo ngũ phân vị của τ/p (τ = 1,50 USD; p = chi phí hành khách mỗi chuyến năm 2024).
       Độ co giãn ngụ ý ε_q = −β_q / ln(1 + τ/p_q).                                          -> t83
  H2b  Độ lồi của đường tốc độ – lưu lượng: mức tăng tốc độ theo giờ × loại ngày (t57) hồi quy
       theo lưu lượng CRZ→CRZ năm 2024 của cùng giờ.                                        -> t84
  H3   Lan tỏa tỷ lệ với mức phơi nhiễm: trên các vùng không thuộc CRZ, tác động sau chính sách
       tương tác với tỷ trọng chuyến đi vào CRZ năm 2024 (liều liên tục).                    -> t85
  H4   Thu nhập tài xế mỗi dặm giảm cơ học khi tốc độ tăng: thu nhập = a·dặm + b·phút, nên
       thu nhập/dặm = a + b/tốc độ. Ước lượng b từ biến thiên trong năm 2024 rồi dự báo
       thay đổi do tốc độ tăng, so với hệ số DiD.                                              -> t86
Phân tích độ nhạy Rambachan–Roth được làm ở bước 19, trên giai đoạn trước chính sách mở rộng 2022–2024,
vì với một năm trước chính sách, các hệ số trước bị mùa vụ chi phối.
Chạy:  python code/18_theory_sensitivity.py
"""
import json
import time

import numpy as np
import pandas as pd

from causal import event_study, fe_ols
from config import GOLD, LOG, TAB
from panels import P, add_ratios, od_month, zone_week, SUMS
from viz import C, fig, save

t0 = time.time()
FEE = 1.5
meta = {}

# ================================================================== H1b
od = od_month("hvfhv")
pre = od[od.post == 0].groupby("pair")[["rider_cost", "n", "miles"]].sum()
pre["p0"] = pre.rider_cost / pre.n
pre["miles0"] = pre.miles / pre.n
od = od.merge(pre[["p0", "miles0"]], left_on="pair", right_index=True)
tp = od[od.touch == 1].drop_duplicates("pair")[["pair", "p0"]]
tp["share"] = FEE / tp.p0
tp["q"] = pd.qcut(tp.share, 5, labels=False) + 1
od = od.merge(tp[["pair", "q"]], on="pair", how="left")
rows = []
for q in range(1, 6):
    sub = od[(od.touch == 0) | (od.q == q)]
    res, info, _ = fe_ols(sub, "ln_n", ["D"], ["pair", "ym"], "pu")
    r = res.iloc[0]
    s = tp[tp.q == q]
    p_mean = float(np.average(s.p0))
    miles = float(od[od.q == q].drop_duplicates("pair").miles0.mean())
    share = FEE / p_mean
    rows.append(dict(quintile=q, pairs=len(s), p0_mean=p_mean, fee_share=share, miles_mean=miles,
                     coef=r.coef, se=r.se, p=r.p, ci_low=r.ci_low, ci_high=r.ci_high,
                     implied_elasticity=-r.coef / np.log(1 + share), n_obs=info["n_obs"]))
h1 = pd.DataFrame(rows)
h1.to_csv(TAB / "t83_dose_response_fee_share.csv", index=False)
# kiểm định xu hướng: hồi quy có trọng số β_q theo ln(1+τ/p)
x = np.log(1 + h1.fee_share)
w = 1 / h1.se ** 2
X = np.c_[np.ones(5), x]
beta = np.linalg.solve(X.T @ (X * w.values[:, None]), X.T @ (w * h1.coef))
cov = np.linalg.inv(X.T @ (X * w.values[:, None]))
meta["h1b"] = dict(slope=float(beta[1]), slope_se=float(np.sqrt(cov[1, 1])), intercept=float(beta[0]))
print(h1, meta["h1b"], flush=True)

# ================================================================== H2b
sp = pd.read_csv(TAB / "t57_speed_did_hour_daytype.csv")
g = pd.read_parquet(GOLD / "grp_hour_day.parquet")
g = g[(g.service == "hvfhv") & (g.pu_grp == "CRZ") & (g.do_grp == "CRZ")].copy()
g["d"] = pd.to_datetime(g.d)
g = g[g.d < P]
g["daytype"] = np.where(g.d.dt.dayofweek >= 5, "Cuối tuần", "Ngày thường")
vol = g.groupby(["daytype", "hr"]).agg(n=("n", "sum"), days=("d", "nunique")).reset_index()
vol["trips_per_hour"] = vol.n / vol.days
vol["mph_2024"] = (g.groupby(["daytype", "hr"]).miles.sum() / (g.groupby(["daytype", "hr"]).time_s.sum() / 3600)).values
h2 = sp.merge(vol[["daytype", "hr", "trips_per_hour", "mph_2024"]], on=["daytype", "hr"])
h2["v_rel"] = h2.trips_per_hour / h2.trips_per_hour.max()
h2.to_csv(TAB / "t84_speed_gain_vs_flow.csv", index=False)
import statsmodels.api as sm
m1 = sm.OLS(h2.did_vs_outer, sm.add_constant(h2[["v_rel"]])).fit(cov_type="HC1")
m2 = sm.OLS(h2.did_vs_outer, sm.add_constant(pd.DataFrame({"v_rel": h2.v_rel, "v_rel2": h2.v_rel ** 2}))).fit(cov_type="HC1")
m3 = sm.OLS(h2.did_vs_outer, sm.add_constant(pd.DataFrame({"v_rel": h2.v_rel,
            "weekend": (h2.daytype == "Cuối tuần").astype(int)}))).fit(cov_type="HC1")
h2m = pd.DataFrame([
    dict(model="Tuyến tính theo lưu lượng", term="v_rel", coef=m1.params["v_rel"], se=m1.bse["v_rel"], p=m1.pvalues["v_rel"], r2=m1.rsquared, n=int(m1.nobs)),
    dict(model="Bậc hai theo lưu lượng", term="v_rel", coef=m2.params["v_rel"], se=m2.bse["v_rel"], p=m2.pvalues["v_rel"], r2=m2.rsquared, n=int(m2.nobs)),
    dict(model="Bậc hai theo lưu lượng", term="v_rel2", coef=m2.params["v_rel2"], se=m2.bse["v_rel2"], p=m2.pvalues["v_rel2"], r2=m2.rsquared, n=int(m2.nobs)),
    dict(model="Tuyến tính + cuối tuần", term="v_rel", coef=m3.params["v_rel"], se=m3.bse["v_rel"], p=m3.pvalues["v_rel"], r2=m3.rsquared, n=int(m3.nobs)),
    dict(model="Tuyến tính + cuối tuần", term="weekend", coef=m3.params["weekend"], se=m3.bse["weekend"], p=m3.pvalues["weekend"], r2=m3.rsquared, n=int(m3.nobs)),
])
h2m["spearman_rho"] = h2[["did_vs_outer", "v_rel"]].corr(method="spearman").iloc[0, 1]
h2m.to_csv(TAB / "t84b_speed_gain_vs_flow_models.csv", index=False)
print(h2m, flush=True)

# ================================================================== H3
zw = zone_week("hvfhv", groups=("MN_NORTH", "OUTER", "CRZ_PARTIAL"), extra=("n_to_crz",))
ex = zw[zw.post == 0].groupby("zone")[["n_to_crz", "n"]].sum()
ex["exposure"] = ex.n_to_crz / ex.n
zw = zw.merge(ex[["exposure"]], left_on="zone", right_index=True)
zw["post_x_exp"] = zw.post * zw.exposure
rows = []
for lab, sub in (("Mọi vùng ngoài CRZ", zw), ("Bỏ vùng vắt ranh giới", zw[zw.grp != "CRZ_PARTIAL"]),
                 ("Chỉ quận ngoài", zw[zw.grp == "OUTER"])):
    for y in ("ln_n", "mph"):
        res, info, _ = fe_ols(sub, y, ["post_x_exp"], ["zone", "wk"], "zone")
        r = res.iloc[0]
        rows.append(dict(sample=lab, outcome=y, coef=r.coef, se=r.se, p=r.p, ci_low=r.ci_low, ci_high=r.ci_high,
                         n_zones=info["n_clusters"], n_obs=info["n_obs"],
                         exp_p10=float(sub.drop_duplicates("zone").exposure.quantile(.1)),
                         exp_p90=float(sub.drop_duplicates("zone").exposure.quantile(.9))))
h3 = pd.DataFrame(rows)
h3.to_csv(TAB / "t85_spillover_dose_response.csv", index=False)
# Đường liều – đáp ứng theo nhóm phơi nhiễm
zx = zw.drop_duplicates("zone")[["zone", "exposure"]].copy()
zx["bin"] = pd.qcut(zx.exposure, 5, labels=False) + 1
zw = zw.merge(zx[["zone", "bin"]], on="zone")
names = []
for b in range(2, 6):
    zw[f"pb{b}"] = ((zw.bin == b) & (zw.post == 1)).astype(float)
    names.append(f"pb{b}")
res, info, _ = fe_ols(zw, "ln_n", names, ["zone", "wk"], "zone")
res["bin"] = [2, 3, 4, 5]
res["exposure_mean"] = [zx[zx.bin == b].exposure.mean() for b in range(2, 6)]
res.to_csv(TAB / "t85b_spillover_by_exposure_bin.csv", index=False)
h3b = res.copy()
meta["h3_bin1_exposure"] = float(zx[zx.bin == 1].exposure.mean())
print(h3, res, flush=True)

# ================================================================== H4
zc = zone_week("hvfhv")
z24 = zc[(zc.post == 0)].copy()
z24["inv_mph"] = 1 / z24.mph
z24["min_pm"] = (z24.time_s / 60) / z24.miles
res_b, info_b, _ = fe_ols(z24, "pay_pm", ["min_pm"], ["zone", "wk"], "zone")
b = float(res_b.coef.iloc[0])
did_mph = pd.read_csv(TAB / "t30_did_main.csv")
d0 = did_mph[(did_mph.service == "hvfhv") & (did_mph["sample"] == "vùng×tuần") & (did_mph.spec == "TWFE")].set_index("outcome")
m0 = float(d0.loc["mph", "treated_pre_mean"])
dm = float(d0.loc["mph", "coef"])
pred = b * 60 * (1 / (m0 + dm) - 1 / m0)
h4 = pd.DataFrame([dict(b_pay_per_minute=b, b_se=float(res_b.se.iloc[0]), mph_pre=m0, d_mph=dm,
                        predicted_d_pay_pm=pred, did_d_pay_pm=float(d0.loc["pay_pm", "coef"]),
                        did_d_pay_pm_se=float(d0.loc["pay_pm", "se"]), pay_pm_pre=float(d0.loc["pay_pm", "treated_pre_mean"]),
                        within_r2=info_b["within_r2"], n_obs=info_b["n_obs"])])
h4.to_csv(TAB / "t86_driver_pay_mechanical.csv", index=False)
print(h4.T, flush=True)

# ================================================================== hình
f, axes = fig(7.4, 3.1, ncols=3)
ax = axes[0]
ax.errorbar(100 * h1.fee_share, 100 * (np.exp(h1.coef) - 1), yerr=196 * h1.se, fmt="o", color=C["s1"], capsize=3)
ax.set_xlabel("Phí / chi phí chuyến 2024 (%)", fontsize=8)
ax.set_ylabel("Tác động lên số chuyến (%)", fontsize=8)
ax.set_title("H1b: theo tỷ trọng phí", fontsize=8.5)
ax = axes[1]
for dt, col in (("Ngày thường", C["s1"]), ("Cuối tuần", C["s2"])):
    d = h2[h2.daytype == dt]
    ax.scatter(d.v_rel, d.did_vs_outer, s=14, color=col, label=dt)
ax.set_xlabel("Lưu lượng CRZ→CRZ 2024 (tương đối)", fontsize=8)
ax.set_ylabel("Tăng tốc độ (dặm/giờ)", fontsize=8)
ax.set_title("H2b: theo lưu lượng", fontsize=8.5)
ax.legend(fontsize=7)
ax = axes[2]
eb = h3b  # kết quả theo nhóm phơi nhiễm
ax.errorbar(100 * np.r_[meta["h3_bin1_exposure"], eb.exposure_mean], 100 * (np.exp(np.r_[0, eb.coef]) - 1),
            yerr=np.r_[0, 196 * eb.se], fmt="o-", color=C["s3"], capsize=3)
ax.set_xlabel("Tỷ trọng chuyến vào CRZ 2024 (%)", fontsize=8)
ax.set_ylabel("So với nhóm thấp nhất (%)", fontsize=8)
ax.set_title("H3: theo phơi nhiễm", fontsize=8.5)
for a_ in axes:
    a_.tick_params(labelsize=7)
f.tight_layout()
save(f, "f56_theory_tests")

meta["seconds"] = round(time.time() - t0, 1)
(LOG / "18_theory_sensitivity.json").write_text(json.dumps(meta, indent=2))
print(meta)
