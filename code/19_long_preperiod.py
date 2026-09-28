"""Bước 19 - Giai đoạn trước chính sách mở rộng (2022–2025): nghiên cứu sự kiện khử mùa vụ,
giả dược theo năm, điều chỉnh xu hướng và phân tích độ nhạy Rambachan–Roth.

Đầu vào: data/gold/long/zone_day_pu.parquet (bước 03 ext + 04 ext), panel vùng × tháng 01/2022–12/2025.
Nhóm vùng và ngưỡng lưu lượng giống panel chính (CRZ, Manhattan phía bắc, quận ngoài; ≥ 100 chuyến/ngày
năm 2024), cân bằng đủ 48 tháng.

Đặc tả (cho mỗi biến kết quả y):
  y_zm = α_z + γ_m + μ_{T(z), tháng-trong-năm(m)} + Σ_{m ≥ 2023-01} β_m · T_z · 1[tháng = m] + ε_zm
Năm 2022 là năm gốc: hiệu ứng cố định nhóm × tháng-trong-năm hấp thụ mùa vụ riêng của CRZ, nên β_m đo
chênh lệch CRZ – đối chứng của tháng m so với cùng tháng năm 2022.

Các đại lượng:
  (1) Hệ số β_m cho 36 tháng (2023–2025)                                                    -> t89, f57
  (2) Giả dược theo năm: TB(β_2024) − TB(β_2023) (chính sách giả 01/2024) và tác động thật
      TB(β_2025) − TB(β_2024); kiểm định Wald đồng thời các β của 2023–2024 bằng nhau          -> t90
  (3) Tác động sau điều chỉnh xu hướng tuyến tính ước lượng từ 24 tháng 2023–2024             -> t90
  (4) Độ nhạy Rambachan–Roth (phiên bản đơn giản hóa, bảo thủ) trên β đã khử mùa vụ:
      RM: |δ_t − δ_{t−1}| ≤ M̄ · max_pre |Δβ|;  SD: ngoại suy xu hướng tuyến tính + sai phân bậc hai ≤ M.
      Với RM, tác động được chuẩn hóa so với tháng cuối trước chính sách (12/2024).           -> t91, t91b, f58
Chạy:  python code/19_long_preperiod.py
"""
import json
import time

import numpy as np
import pandas as pd
from scipy import stats

from causal import fe_ols
from config import GOLD, LOG, TAB
from panels import MIN_DAILY, SUMS, add_ratios, dim
from viz import C, fig, save

t0 = time.time()
z = pd.read_parquet(GOLD / "long" / "zone_day_pu.parquet")
z = z[z.service == "hvfhv"].copy()
z["d"] = pd.to_datetime(z.d)
z = z[(z.d >= "2022-01-01") & (z.d <= "2025-12-31")]
z["ym"] = z.d.dt.to_period("M")
dm = dim()[["LocationID", "grp"]]
z = z.merge(dm, left_on="zone", right_on="LocationID")
z = z[z.grp.isin(["CRZ", "MN_NORTH", "OUTER"])]
g = z.groupby(["zone", "grp", "ym"])[SUMS].sum().reset_index()
pre24 = z[(z.d >= "2024-01-07") & (z.d < "2025-01-05")].groupby("zone").n.sum() / 364
keep = pre24[pre24 >= MIN_DAILY["hvfhv"]].index
cnt = g.groupby("zone").ym.nunique()
keep = [k for k in keep if cnt.get(k, 0) == 48]
g = g[g.zone.isin(keep)].copy()
g = add_ratios(g)
g["rider_ex_pt"] = (g.rider_cost - g.cbd) / g.n
g["treat"] = (g.grp == "CRZ").astype(int)
g["year"] = g.ym.dt.year
g["moy"] = g.ym.dt.month
g["ymc"] = g.ym.astype(str)
g["tm"] = g.treat.astype(str) + "_" + g.moy.astype(str)
months = sorted(g.ym.unique())
ev = [m for m in months if m.year >= 2023]
names = []
for m in ev:
    nm = f"e_{m}"
    g[nm] = ((g.ym == m) & (g.treat == 1)).astype(float)
    names.append(nm)
meta = dict(zones=int(g.zone.nunique()), treated=int(g[g.treat == 1].zone.nunique()), obs=int(len(g)))

OUT = {"ln_n": "log số chuyến", "mph": "Tốc độ (dặm/giờ)", "wait": "Thời gian chờ (phút)",
       "fare_pm": "Giá cước cơ sở/dặm (USD)", "pay_pm": "Thu nhập tài xế/dặm (USD)",
       "rider_ex_pt": "Chi phí hành khách/chuyến trừ phí CBD (USD)", "pay_share": "Thu nhập tài xế/giá cước (%)",
       "shared_pct": "Tỷ lệ yêu cầu đi chung (%)"}
coef_rows, sum_rows, rm_rows, sd_rows = [], [], [], []
yrs = np.array([m.year for m in ev])
kidx = np.arange(len(ev))                       # 0 = 2023-01
for y, lab in OUT.items():
    d = g.dropna(subset=[y])
    res, info, V = fe_ols(d, y, names, ["zone", "ymc", "tm"], "zone")
    b = res.coef.to_numpy()
    se = res.se.to_numpy()
    for m, bb, ss in zip(ev, b, se):
        coef_rows.append(dict(outcome=y, label=lab, ym=str(m), coef=bb, se=ss))
    G = info["n_clusters"]
    crit = stats.t.ppf(0.975, G - 1)

    def lin(a):
        return float(a @ b), float(np.sqrt(a @ V @ a))
    a23 = (yrs == 2023) / (yrs == 2023).sum()
    a24 = (yrs == 2024) / (yrs == 2024).sum()
    a25 = (yrs == 2025) / (yrs == 2025).sum()
    plc, plc_se = lin(a24 - a23)
    eff, eff_se = lin(a25 - a24)
    acc, acc_se = lin((a25 - a24) - (a24 - a23))   # thay đổi năm 2025 trừ thay đổi năm 2024 (giả định xu hướng năm không đổi)
    # Wald: 24 hệ số 2023–2024 bằng nhau (không có biến động có hệ thống trước chính sách)
    pre = np.where(yrs <= 2024)[0]
    Lw = np.zeros((len(pre) - 1, len(b)))
    for i in range(len(pre) - 1):
        Lw[i, pre[i]] = 1
        Lw[i, pre[-1]] = -1
    wv = Lw @ b
    Wst = float(wv @ np.linalg.pinv(Lw @ V @ Lw.T) @ wv)
    wp = float(stats.chi2.sf(Wst, len(pre) - 1))
    # Điều chỉnh xu hướng tuyến tính ước lượng từ 2023–2024
    Xp = np.c_[np.ones(len(pre)), kidx[pre]]
    H = np.linalg.pinv(Xp.T @ Xp) @ Xp.T                    # 2 × n_pre
    S = np.zeros((len(pre), len(b)))
    S[np.arange(len(pre)), pre] = 1
    CL = H @ S                                               # 2 × K
    post = np.where(yrs == 2025)[0]
    trend_post = np.c_[np.ones(len(post)), kidx[post]] @ CL
    trend_24 = np.c_[np.ones((yrs == 2024).sum()), kidx[yrs == 2024]] @ CL
    a_tr = (a25 - a24) - (trend_post.mean(0) - trend_24.mean(0))
    eff_tr, eff_tr_se = lin(a_tr)
    slope, slope_se = float((CL @ b)[1]), float(np.sqrt((CL @ V @ CL.T)[1, 1]))
    # Rambachan–Roth: đo so với TB 2024; δ tại tháng cuối trước chính sách (12/2024)
    bp = b[pre]
    dmax = float(np.max(np.abs(np.diff(bp))))
    kpost = np.arange(1, len(post) + 1)                      # số bước kể từ 12/2024
    # Theo Rambachan–Roth, tham số được chuẩn hóa so với tháng cuối trước chính sách (12/2024): θ = TB(β_2025) − β_2024-12.
    # Dưới RM, độ chệch của θ bị chặn bởi M̄ · max|Δβ_pre| · TB(k), k = số tháng kể từ 12/2024.
    a_last = np.zeros(len(b))
    a_last[pre[-1]] = 1
    eff_rr, eff_rr_se = lin(a25 - a_last)
    w_rm = float(kpost.mean())
    for M in (0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0):
        B = M * dmax * w_rm
        rm_rows.append(dict(outcome=y, label=lab, M=M, effect=eff_rr, se=eff_rr_se, bound=B,
                            ci_low=eff_rr - B - crit * eff_rr_se, ci_high=eff_rr + B + crit * eff_rr_se))
    brk_rm = max((abs(eff_rr) - crit * eff_rr_se) / (dmax * w_rm), 0.0)
    w_sd = float(np.mean(kpost * (kpost + 1) / 2))
    for M in (0, 0.0025, 0.005, 0.01, 0.02, 0.05):
        B = M * w_sd
        sd_rows.append(dict(outcome=y, label=lab, M=M, effect_trend_adj=eff_tr, se=eff_tr_se, bound=B,
                            ci_low=eff_tr - B - crit * eff_tr_se, ci_high=eff_tr + B + crit * eff_tr_se))
    brk_sd = max((abs(eff_tr) - crit * eff_tr_se) / w_sd, 0.0)
    sum_rows.append(dict(outcome=y, label=lab, placebo_2024_vs_2023=plc, placebo_se=plc_se,
                         placebo_p=float(2 * stats.t.sf(abs(plc / plc_se), G - 1)),
                         effect_2025_vs_2024=eff, effect_se=eff_se, effect_p=float(2 * stats.t.sf(abs(eff / eff_se), G - 1)),
                         pre_wald=Wst, pre_wald_df=len(pre) - 1, pre_wald_p=wp, pre_slope_per_month=slope, pre_slope_se=slope_se,
                         effect_trend_adj=eff_tr, effect_trend_adj_se=eff_tr_se,
                         effect_trend_adj_p=float(2 * stats.t.sf(abs(eff_tr / eff_tr_se), G - 1)),
                         accel=acc, accel_se=acc_se, accel_p=float(2 * stats.t.sf(abs(acc / acc_se), G - 1)),
                         effect_vs_last_pre=eff_rr, effect_vs_last_pre_se=eff_rr_se,
                         max_pre_delta=dmax, breakdown_RM=brk_rm, breakdown_SD=brk_sd,
                         pre_mean_2024=float(d[(d.treat == 1) & (d.year == 2024)][y].mean()),
                         n_obs=info["n_obs"], n_clusters=G))
    print(sum_rows[-1], flush=True)
co = pd.DataFrame(coef_rows)
co.to_csv(TAB / "t89_long_event_study.csv", index=False)
sm_ = pd.DataFrame(sum_rows)
sm_.to_csv(TAB / "t90_long_placebo_trend.csv", index=False)
pd.DataFrame(rm_rows).to_csv(TAB / "t91_rr_relative_magnitudes.csv", index=False)
pd.DataFrame(sd_rows).to_csv(TAB / "t91b_rr_smoothness.csv", index=False)

# Chuỗi mô tả: số chuyến/ngày theo tháng của CRZ và đối chứng, chỉ số 2022 = 100
desc = g.groupby(["ym", "treat"]).n.sum().unstack()
desc.columns = ["control", "crz"]
days = pd.Series({m: m.days_in_month for m in desc.index})
desc = desc.div(days, axis=0)
desc = desc / desc[desc.index.year == 2022].mean() * 100
desc.index = desc.index.astype(str)
desc.to_csv(TAB / "t89b_long_index.csv")

# Hình f57: hệ số theo tháng của 4 biến
f, axes = fig(6.8, 5.2, nrows=2, ncols=2, sharex=True)
for ax, y in zip(axes.flat, ["ln_n", "mph", "fare_pm", "pay_pm"]):
    d = co[co.outcome == y]
    x = pd.PeriodIndex(d.ym, freq="M").to_timestamp()
    ax.fill_between(x, d.coef - 1.96 * d.se, d.coef + 1.96 * d.se, color=C["s1"], alpha=0.2, lw=0)
    ax.plot(x, d.coef, color=C["s1"], lw=1.2)
    ax.axhline(0, color=C["text2"], lw=0.7)
    ax.axvline(pd.Timestamp("2025-01-01"), color=C["text2"], lw=0.8, ls="--")
    ax.axvline(pd.Timestamp("2024-01-01"), color=C["s2"], lw=0.8, ls=":")
    ax.set_title(OUT[y], fontsize=8.5)
    ax.tick_params(labelsize=7)
f.tight_layout()
save(f, "f57_long_event_study")

f, axes = fig(6.8, 4.6, nrows=2, ncols=4)
rm = pd.DataFrame(rm_rows)
for ax, (y, lab) in zip(axes.flat, OUT.items()):
    d = rm[rm.outcome == y]
    ax.fill_between(d.M, d.ci_low, d.ci_high, color=C["s1"], alpha=0.25, lw=0)
    ax.plot(d.M, d.effect, color=C["s1"], lw=1.2)
    ax.axhline(0, color=C["text2"], lw=0.8)
    ax.set_title(lab, fontsize=7)
    ax.tick_params(labelsize=6.5)
for ax in axes[1]:
    ax.set_xlabel("M̄", fontsize=8)
f.tight_layout()
save(f, "f58_rr_long")

meta["seconds"] = round(time.time() - t0, 1)
(LOG / "19_long_preperiod.json").write_text(json.dumps(meta, indent=2))
print(meta)
