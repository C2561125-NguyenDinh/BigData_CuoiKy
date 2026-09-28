"""Bước 7 - Ước lượng tác động trung bình: DiD, DDD mùa vụ và nghiên cứu sự kiện.

Thiết kế chính: panel vùng đón × tuần (Chủ nhật–thứ Bảy), 01/2024–12/2025.
  Nhóm xử lý  : vùng nằm trọn trong CRZ.
  Nhóm đối chứng: vùng Manhattan phía bắc và các quận ngoài (loại sân bay,
                  vùng vắt ranh giới, vùng không xác định, vùng quá nhỏ).
Đặc tả:
  (1) TWFE : y_zt = a_z + g_t + b*D_zt + e
  (2) DDD mùa vụ: thêm hiệu ứng cố định (nhóm xử lý × tuần-trong-năm),
      tức là so sánh chênh lệch xử lý–đối chứng của cùng tuần giữa 2025 và 2024.
  (3) TWFE có trọng số theo số chuyến bình quân năm 2024.
Sai số chuẩn phân cụm theo vùng.

Chạy:  python code/07_did_main.py
"""
import json
import time

import matplotlib.dates as mdates
import numpy as np
import pandas as pd

from causal import event_study, fe_ols, pretrend_wald, pretrend_wald_centered
from config import LOG, TAB
from panels import P, od_month, zone_day, zone_hour_month, zone_week
from viz import C, fig, plt, policy_line, save

t0 = time.time()
OUTCOMES_HV = {
    "ln_n": "log số chuyến đón",
    "fare_pm": "Giá cước cơ sở / dặm (USD)",
    "pay_pm": "Thu nhập tài xế / dặm (USD)",
    "fare_pt": "Giá cước cơ sở / chuyến (USD)",
    "pay_pt": "Thu nhập tài xế / chuyến (USD)",
    "rider_pt": "Tổng chi phí hành khách / chuyến (USD)",
    "cbd_pt": "Phí CBD / chuyến (USD)",
    "tips_pt": "Tiền tip / chuyến (USD)",
    "pay_share": "Thu nhập tài xế / giá cước (%)",
    "mph": "Tốc độ trung bình (dặm/giờ)",
    "miles_pt": "Quãng đường / chuyến (dặm)",
    "wait": "Thời gian chờ đón (phút)",
    "shared_pct": "Tỷ lệ chuyến có yêu cầu đi chung (%)",
}
OUTCOMES_YE = {k: v for k, v in OUTCOMES_HV.items() if k in ("ln_n", "fare_pm", "fare_pt", "rider_pt", "cbd_pt", "tips_pt", "mph", "miles_pt")}
OUTCOMES_YE["rider_pt"] = "Tổng tiền thanh toán trừ tip / chuyến (USD)"

rows = []
meta = {}


def run_specs(panel, outcomes, service, label):
    for y, ylab in outcomes.items():
        if panel[y].notna().sum() == 0:
            continue
        specs = {
            "TWFE": dict(fes=["zone", "wk"], w=None, x=["D"]),
            "DDD mùa vụ": dict(fes=["zone", "wk", "tw"], w=None, x=["D"]),
            "TWFE có trọng số": dict(fes=["zone", "wk"], w="w_pre", x=["D"]),
            # Cho phép nhóm xử lý có xu hướng tuyến tính riêng (năm), tác động là độ dịch mức sau 05/01/2025
            "TWFE + xu hướng nhóm": dict(fes=["zone", "wk"], w=None, x=["D", "trend_T"]),
            # Lưu ý: không kết hợp DDD với xu hướng nhóm vì khi đã có FE nhóm×tuần-trong-năm,
            # biến xu hướng tuyến tính và D gần như đa cộng tuyến hoàn toàn (không định danh được).
        }
        for sname, sp in specs.items():
            res, info, _ = fe_ols(panel, y, sp["x"], sp["fes"], "zone", sp["w"])
            r = res.iloc[0].to_dict()
            pre_mean = panel.loc[(panel.treat == 1) & (panel.post == 0), y].mean()
            rows.append(dict(service=service, sample=label, outcome=y, outcome_label=ylab, spec=sname,
                             coef=r["coef"], se=r["se"], p=r["p"], ci_low=r["ci_low"], ci_high=r["ci_high"],
                             pct_effect=(100 * (np.exp(r["coef"]) - 1)) if y == "ln_n" else 100 * r["coef"] / pre_mean,
                             treated_pre_mean=pre_mean, n_obs=info["n_obs"], n_clusters=info["n_clusters"],
                             within_r2=info["within_r2"]))


# ---------- (A) HVFHV: panel vùng × tuần ----------
zw = zone_week("hvfhv", extra=("n_to_crz",))
zw["tw"] = zw.treat.astype(str) + "_" + zw.woy.astype(str)
zw["trend_T"] = zw.treat * zw.k / 52.0
zw["ln_to_crz"] = np.log1p(zw.n_to_crz)
meta["hv_zone_week"] = dict(zones=int(zw.zone.nunique()), treated=int(zw[zw.treat == 1].zone.nunique()),
                            control=int(zw[zw.treat == 0].zone.nunique()), weeks=int(zw.wk.nunique()),
                            obs=int(len(zw)), trips=float(zw.n.sum()))
run_specs(zw, OUTCOMES_HV, "hvfhv", "vùng×tuần")

# ---------- (B) Taxi vàng ----------
# Taxi vàng: số chuyến taxi vàng ở các quận ngoài tăng hơn gấp đôi năm 2025 (xem bảng
# t27b theo VendorID), không liên quan đến CRZ, nên nhóm đối chứng chính chỉ gồm Manhattan phía bắc.
# Đặc tả gồm cả quận ngoài được báo cáo riêng như một phép thử độ nhạy.
yw_all = zone_week("yellow")
yw_all["tw"] = yw_all.treat.astype(str) + "_" + yw_all.woy.astype(str)
yw_all["trend_T"] = yw_all.treat * yw_all.k / 52.0
run_specs(yw_all, {"ln_n": "log số chuyến đón"}, "yellow", "vùng×tuần, đối chứng gồm quận ngoài")
yw = zone_week("yellow", groups=("CRZ", "MN_NORTH"))
yw["tw"] = yw.treat.astype(str) + "_" + yw.woy.astype(str)
yw["trend_T"] = yw.treat * yw.k / 52.0
meta["ye_zone_week"] = dict(zones=int(yw.zone.nunique()), treated=int(yw[yw.treat == 1].zone.nunique()),
                            control=int(yw[yw.treat == 0].zone.nunique()), weeks=int(yw.wk.nunique()),
                            obs=int(len(yw)), trips=float(yw.n.sum()))
run_specs(yw, OUTCOMES_YE, "yellow", "vùng×tuần")

main = pd.DataFrame(rows)
main.to_csv(TAB / "t30_did_main.csv", index=False)
print(main[main.spec == "TWFE"][["service", "outcome", "coef", "se", "p", "pct_effect"]].to_string(), flush=True)

# ---------- (C) Nghiên cứu sự kiện theo tuần: log số chuyến ----------
ev_all = []
for svc, pan in (("hvfhv", zw), ("yellow", yw)):
    res, info, V = event_study(pan, "ln_n", "treat", "k", ["zone", "wk"], "zone", ref=-1, lo=-52, hi=51)
    res["service"], res["spec"] = svc, "TWFE"
    pt = pretrend_wald_centered(res, V)
    res["pretrend_wald"], res["pretrend_p"] = pt["wald"], pt["p"]
    res["post_mean_c"] = res.loc[res.k >= 0, "coef_c"].mean()
    ev_all.append(res)
    # DDD: chỉ đưa biến giả cho các tuần sau chính sách; tuần 2024 cùng vị trí
    # trong năm đóng vai trò mốc so sánh thông qua hiệu ứng cố định nhóm×tuần-trong-năm
    pp = pan.copy()
    ks = sorted(k for k in pp.k.unique() if k >= 0)
    names = []
    for k in ks:
        nm = f"post_{k}"
        pp[nm] = ((pp.k == k) & (pp.treat == 1)).astype(float)
        names.append(nm)
    r2, info2, _ = fe_ols(pp, "ln_n", names, ["zone", "wk", "tw"], "zone")
    r2["k"], r2["service"], r2["spec"] = ks, svc, "DDD mùa vụ"
    r2["pretrend_wald"], r2["pretrend_p"] = np.nan, np.nan
    ev_all.append(r2)
ev = pd.concat(ev_all)
ev.to_csv(TAB / "t31_event_study_weekly_ln_n.csv", index=False)

for svc, nm, ttl in (("hvfhv", "f19_event_study_hvfhv", "HVFHV"), ("yellow", "f20_event_study_yellow", "Taxi vàng")):
    f, ax = fig(6.8, 3.4)
    e = ev[(ev.service == svc) & (ev.spec == "TWFE")].sort_values("k")
    x = P + pd.to_timedelta(e.k * 7, unit="D")
    ax.fill_between(x, 100 * e.ci_low_c, 100 * e.ci_high_c, color=C["s1"], alpha=0.18, lw=0)
    ax.plot(x, 100 * e.coef_c, color=C["s1"], lw=1.6, label="Hệ số tuần (×100, log điểm), KTC 95%")
    ax.axhline(0, color=C["text2"], lw=0.8)
    policy_line(ax, P)
    ax.set_ylabel("Chênh lệch CRZ – đối chứng (log điểm ×100)")
    ax.set_title(f"Nghiên cứu sự kiện theo tuần, log số chuyến đón – {ttl} (mốc: TB 52 tuần trước)")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%y"))
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=2)
    save(f, nm)

# DDD mùa vụ: chỉ các tuần sau chính sách có nghĩa
f, ax = fig(6.8, 3.2)
for svc, col, lab in (("hvfhv", C["s1"], "HVFHV"), ("yellow", C["s2"], "Taxi vàng")):
    e = ev[(ev.service == svc) & (ev.spec == "DDD mùa vụ") & (ev.k >= 0)].sort_values("k")
    ax.plot(e.k, 100 * e.coef, color=col, lw=1.6, label=lab)
    ax.fill_between(e.k, 100 * e.ci_low, 100 * e.ci_high, color=col, alpha=0.15, lw=0)
ax.axhline(0, color=C["text2"], lw=0.8)
ax.set_xlabel("Tuần kể từ 05/01/2025")
ax.set_ylabel("log điểm ×100")
ax.set_title("Tác động theo tuần sau khi khử mùa vụ nhóm (DDD), log số chuyến đón")
ax.legend(loc="lower right")
save(f, "f21_event_ddd_weekly")

# ---------- (D) Nghiên cứu sự kiện theo tháng cho các biến giá, thu nhập, tốc độ, thời gian chờ ----------
zw["km"] = ((zw.wk.dt.year - 2025) * 12 + zw.wk.dt.month - 1).astype(int)
mo_rows = []
for y in ("fare_pm", "pay_pm", "rider_pt", "mph", "wait", "miles_pt"):
    res, info, V = event_study(zw, y, "treat", "km", ["zone", "wk"], "zone", ref=-1)
    res["outcome"] = y
    pt = pretrend_wald_centered(res, V)
    res["pretrend_p"] = pt["p"]
    # Kiểm tra gián đoạn: chênh lệch giữa TB 3 tháng đầu sau và TB 3 tháng cuối trước chính sách
    # Giá trị đã chuẩn hóa của kỳ mốc (k = -1, hệ số gốc bằng 0)
    n_pre = int((res.k < 0).sum()) + 1
    c_ref = -res.loc[res.k < 0, "coef"].sum() / n_pre
    pre3 = list(res.loc[res.k.isin([-3, -2]), "coef_c"]) + [c_ref]
    res["jump_3v3"] = res.loc[res.k.isin([0, 1, 2]), "coef_c"].mean() - np.mean(pre3)
    mo_rows.append(res)
evm = pd.concat(mo_rows)
evm.to_csv(TAB / "t32_event_study_monthly_hvfhv.csv", index=False)
f, axs = plt.subplots(3, 2, figsize=(6.8, 7.2), sharex=True)
for ax, y in zip(axs.ravel(), ("fare_pm", "pay_pm", "rider_pt", "mph", "wait", "miles_pt")):
    e = evm[evm.outcome == y].sort_values("k")
    ax.errorbar(e.k, e.coef_c, yerr=[e.coef_c - e.ci_low_c, e.ci_high_c - e.coef_c], fmt="o", ms=3.5,
                color=C["s1"], ecolor=C["s1"], elinewidth=1, capsize=0)
    ax.axhline(0, color=C["text2"], lw=0.8)
    ax.axvline(-0.5, color=C["text2"], lw=0.8, ls="--")
    ax.set_title(OUTCOMES_HV[y], fontsize=9)
for ax in axs[-1]:
    ax.set_xlabel("Tháng so với 01/2025")
f.suptitle("Nghiên cứu sự kiện theo tháng (HVFHV, vùng×tuần, mốc: TB 12 tháng 2024)", x=0.02, ha="left",
           fontsize=10.5, fontweight="bold")
f.tight_layout()
save(f, "f22_event_monthly_grid")

# ---------- (E) Không đồng nhất theo khung giờ ----------
hm = zone_hour_month("hvfhv")
hrows = []
for hb, g in hm.groupby("hbin"):
    for y in ("ln_n", "mph", "wait", "fare_pm"):
        res, info, _ = fe_ols(g, y, ["D"], ["zone", "ym"], "zone")
        r = res.iloc[0]
        hrows.append(dict(hbin=hb, outcome=y, coef=r.coef, se=r.se, p=r.p, ci_low=r.ci_low, ci_high=r.ci_high,
                          n_obs=info["n_obs"], pre_mean=g.loc[(g.treat == 1) & (g.post == 0), y].mean()))
hh = pd.DataFrame(hrows)
hh.to_csv(TAB / "t33_heterogeneity_hour.csv", index=False)
f, axs = fig(6.8, 3.0, ncols=2)
for ax, y, ttl in ((axs[0], "ln_n", "log số chuyến đón (×100)"), (axs[1], "mph", "Tốc độ (dặm/giờ)")):
    e = hh[hh.outcome == y].sort_values("hbin")
    sc = 100 if y == "ln_n" else 1
    xx = np.arange(len(e))
    ax.bar(xx, sc * e.coef, color=C["s1"], width=0.6)
    ax.errorbar(xx, sc * e.coef, yerr=[sc * (e.coef - e.ci_low), sc * (e.ci_high - e.coef)], fmt="none",
                ecolor=C["text2"], elinewidth=1)
    ax.set_xticks(xx, e.hbin)
    ax.axhline(0, color=C["text2"], lw=0.8)
    ax.set_title(ttl, fontsize=9.5)
    ax.set_xlabel("Khung giờ đón")
f.suptitle("Tác động DiD theo khung giờ (HVFHV, vùng×khung giờ×tháng)", x=0.02, ha="left",
           fontsize=10.5, fontweight="bold")
f.tight_layout()
save(f, "f23_heterogeneity_hour")

# ---------- (F) Ngày thường và cuối tuần ----------
zd = zone_day("hvfhv")
zd["D_we"] = zd.D * zd.weekend
wres = []
for y in ("ln_n", "mph", "wait", "fare_pm"):
    res, info, _ = fe_ols(zd, y, ["D", "D_we"], ["zone", "d"], "zone")
    res["outcome"] = y
    res["n_obs"] = info["n_obs"]
    wres.append(res)
pd.concat(wres).to_csv(TAB / "t34_heterogeneity_weekend.csv", index=False)
meta["hv_zone_day"] = dict(zones=int(zd.zone.nunique()), obs=int(len(zd)))

# ---------- (G) Panel cặp OD × tháng ----------
od = od_month("hvfhv")
meta["hv_od_month"] = dict(pairs=int(od.pair.nunique()), obs=int(len(od)),
                           by_type=od.groupby("ftype").pair.nunique().to_dict(), trips=float(od.n.sum()))
orow = []
for ft in ("Tất cả chuyến chạm CRZ", "CRZ→CRZ", "CRZ→ngoài", "ngoài→CRZ"):
    sub = od if ft.startswith("Tất cả") else od[(od.ftype == ft) | (od.touch == 0)]
    for y in ("ln_n", "fare_pm", "pay_pm", "rider_pt", "cbd_pt", "mph", "pay_share", "tips_pt", "fare_pt", "pay_pt", "shared_pct"):
        res, info, _ = fe_ols(sub, y, ["D"], ["pair", "ym"], "pu")
        r = res.iloc[0]
        pre_mean = sub.loc[(sub.touch == 1) & (sub.post == 0), y].mean()
        orow.append(dict(flow=ft, outcome=y, outcome_label=OUTCOMES_HV.get(y, y), coef=r.coef, se=r.se, p=r.p,
                         ci_low=r.ci_low, ci_high=r.ci_high, pre_mean=pre_mean,
                         pct=(100 * (np.exp(r.coef) - 1)) if y == "ln_n" else 100 * r.coef / pre_mean,
                         n_obs=info["n_obs"], n_clusters=info["n_clusters"]))
odr = pd.DataFrame(orow)
odr.to_csv(TAB / "t35_did_od_pairs.csv", index=False)
print(odr[odr.outcome.isin(["ln_n", "rider_pt", "cbd_pt", "fare_pt", "pay_pt"])].to_string(), flush=True)

# Tỷ lệ chuyển giá (pass-through) của phí CBD sang tổng chi phí hành khách
pt_rows = []
for ft in ("Tất cả chuyến chạm CRZ", "CRZ→CRZ", "CRZ→ngoài", "ngoài→CRZ"):
    a = odr[(odr.flow == ft) & (odr.outcome == "rider_pt")].iloc[0]
    b = odr[(odr.flow == ft) & (odr.outcome == "cbd_pt")].iloc[0]
    c = odr[(odr.flow == ft) & (odr.outcome == "fare_pt")].iloc[0]
    d = odr[(odr.flow == ft) & (odr.outcome == "pay_pt")].iloc[0]
    pt_rows.append(dict(flow=ft, d_rider_cost=a.coef, d_cbd=b.coef, d_base_fare=c.coef, d_driver_pay=d.coef,
                        pass_through_ratio=a.coef / b.coef if b.coef else np.nan))
pd.DataFrame(pt_rows).to_csv(TAB / "t36_pass_through.csv", index=False)

# Nghiên cứu sự kiện theo tháng cho panel OD: log số chuyến
res, info, V = event_study(od, "ln_n", "touch", "k", ["pair", "ym"], "pu", ref=-1)
res["pretrend_p"] = pretrend_wald_centered(res, V)["p"]
res.to_csv(TAB / "t37_event_od_ln_n.csv", index=False)
f, ax = fig(6.6, 3.1)
ax.errorbar(res.k, 100 * res.coef_c, yerr=[100 * (res.coef_c - res.ci_low_c), 100 * (res.ci_high_c - res.coef_c)],
            fmt="o", ms=4, color=C["s1"], elinewidth=1)
ax.axhline(0, color=C["text2"], lw=0.8)
ax.axvline(-0.5, color=C["text2"], lw=0.8, ls="--")
ax.set_xlabel("Tháng so với 01/2025")
ax.set_ylabel("log điểm ×100")
ax.set_title("Nghiên cứu sự kiện theo tháng, cặp OD chạm CRZ so với không chạm (mốc: TB 2024)")
save(f, "f24_event_od")

(LOG / "07_did_main.json").write_text(json.dumps(dict(seconds=round(time.time() - t0, 1), **meta), indent=2, default=float))
print(json.dumps(meta, indent=1, default=float), "time", round(time.time() - t0, 1))
