"""Bước 10 - Hiệu ứng lan tỏa, kiểm định giả dược và độ vững.

(a) Lan tỏa không gian: các vùng ngoài CRZ nằm sát ranh giới có thay đổi
    khác các vùng xa hay không (cả điểm đón và điểm trả), theo dải khoảng cách.
(b) Giả dược theo thời gian: chỉ dùng dữ liệu 2024, giả định chính sách bắt
    đầu 07/07/2024.
(c) Suy diễn hoán vị: gán ngẫu nhiên 38 vùng đối chứng làm "vùng xử lý", lặp 500 lần.
(d) Bảng độ vững cho log số chuyến đón với nhiều lựa chọn mẫu và đặc tả.

Chạy:  python code/10_spillover_robustness.py
"""
import json
import sys
import time

import numpy as np
import pandas as pd

from causal import fe_ols
from config import LOG, SEED, TAB
from panels import P, zone_day, zone_week
from viz import C, fig, plt, save

t0 = time.time()
rng = np.random.default_rng(SEED)
meta = {}
PART = sys.argv[1] if len(sys.argv) > 1 else "all"


def want(p):
    return PART in (p, "all")


if want("spill"):
    # ---------------- (a) Lan tỏa ----------------
    groups = ("CRZ", "CRZ_PARTIAL", "MN_NORTH", "OUTER")
    pu = zone_week("hvfhv", "zone_day_pu", groups=groups)
    do = zone_week("hvfhv", "zone_day_do", groups=groups, extra=("n_from_crz",))
    do["n_nocrz"] = do.n - do.n_from_crz
    do["ln_nocrz"] = np.log(do.n_nocrz.clip(lower=1))
    do["ln_from_crz"] = np.log(do.n_from_crz.clip(lower=1))


    def band(r):
        if r.grp == "CRZ":
            return "CRZ"
        if r.grp == "CRZ_PARTIAL":
            return "Vắt ranh giới"
        d = r.dist_to_crz_km
        if d <= 1.0:
            return "0–1 km"
        if d <= 2.5:
            return "1–2,5 km"
        if d <= 5:
            return "2,5–5 km"
        if d <= 10:
            return "5–10 km"
        return ">10 km"


    sp_rows = []
    for nm, pan, ys in (("điểm đón", pu, ["ln_n"]), ("điểm trả", do, ["ln_n", "ln_nocrz", "ln_from_crz"])):
        pan = pan.copy()
        pan["band"] = pan.apply(band, axis=1)
        bands = ["CRZ", "Vắt ranh giới", "0–1 km", "1–2,5 km", "2,5–5 km", "5–10 km"]
        for b in bands:
            pan[f"D_{b}"] = ((pan.band == b) & (pan.post == 1)).astype(float)
        for y in ys:
            res, info, _ = fe_ols(pan, y, [f"D_{b}" for b in bands], ["zone", "wk"], "zone")
            for (_, r), b in zip(res.iterrows(), bands):
                sp_rows.append(dict(side=nm, outcome=y, band=b, coef=r.coef, se=r.se, p=r.p, ci_low=r.ci_low,
                                    ci_high=r.ci_high, n_zones=int(pan[pan.band == b].zone.nunique()),
                                    ref="> 10 km", n_obs=info["n_obs"]))
    sp = pd.DataFrame(sp_rows)
    sp.to_csv(TAB / "t48_spillover_bands.csv", index=False)
    f, axs = fig(6.8, 3.2, ncols=2, sharey=True)
    for ax, (side, y, ttl) in zip(axs, (("điểm đón", "ln_n", "Số chuyến đón"),
                                        ("điểm trả", "ln_nocrz", "Số chuyến trả (khách từ ngoài CRZ)"))):
        e = sp[(sp.side == side) & (sp.outcome == y)]
        xx = np.arange(len(e))
        cols = [C["s1"] if b == "CRZ" else (C["s2"] if b == "Vắt ranh giới" else C["s3"]) for b in e.band]
        ax.bar(xx, 100 * e.coef, color=cols, width=0.65)
        ax.errorbar(xx, 100 * e.coef, yerr=[100 * (e.coef - e.ci_low), 100 * (e.ci_high - e.coef)], fmt="none",
                    ecolor=C["text2"], elinewidth=1)
        ax.set_xticks(xx, e.band, rotation=35, ha="right")
        ax.axhline(0, color=C["text2"], lw=0.8)
        ax.set_title(ttl, fontsize=9.5)
    axs[0].set_ylabel("log điểm ×100 (so với vùng > 10 km)")
    f.suptitle("Tác động theo dải khoảng cách tới ranh giới CRZ (HVFHV)", x=0.02, ha="left", fontsize=10.5,
               fontweight="bold")
    f.tight_layout()
    save(f, "f32_spillover_bands")


if want("placebo"):
    # ---------------- (b) Giả dược theo thời gian ----------------
    zw = zone_week("hvfhv")
    fake = pd.Timestamp("2024-07-07")
    z24 = zw[zw.wk < P].copy()
    z24["D_fake"] = ((z24.wk >= fake) & (z24.treat == 1)).astype(float)
    pl_rows = []
    z24["trend_T"] = z24.treat * z24.k / 52.0
    zw["trend_T"] = zw.treat * zw.k / 52.0
    for y in ("ln_n", "fare_pm", "pay_pm", "fare_pt", "pay_pt", "rider_pt", "mph", "wait", "miles_pt"):
        res, info, _ = fe_ols(z24, y, ["D_fake"], ["zone", "wk"], "zone")
        rest, _, _ = fe_ols(z24, y, ["D_fake", "trend_T"], ["zone", "wk"], "zone")
        real, _, _ = fe_ols(zw, y, ["D"], ["zone", "wk"], "zone")
        realt, _, _ = fe_ols(zw, y, ["D", "trend_T"], ["zone", "wk"], "zone")
        pl_rows.append(dict(outcome=y, placebo_coef=res.coef[0], placebo_se=res.se[0], placebo_p=res.p[0],
                            placebo_trend_coef=rest.coef[0], placebo_trend_se=rest.se[0], placebo_trend_p=rest.p[0],
                            real_coef=real.coef[0], real_se=real.se[0], real_p=real.p[0],
                            real_trend_coef=realt.coef[0], real_trend_se=realt.se[0], real_trend_p=realt.p[0]))
    pd.DataFrame(pl_rows).to_csv(TAB / "t49_placebo_time.csv", index=False)

    # Giả dược theo thời gian cho panel cặp OD × tháng (07/2024) và đặc tả có xu hướng riêng
    from panels import od_month
    od = od_month("hvfhv")
    od["trend_T"] = od.touch * od.k / 12.0
    o24 = od[od.post == 0].copy()
    o24["D_fake"] = ((o24.ym >= "2024-07") & (o24.touch == 1)).astype(float)
    op = []
    for y in ("ln_n", "fare_pt", "pay_pt", "rider_pt", "fare_pm", "pay_pm", "mph"):
        a = fe_ols(o24, y, ["D_fake"], ["pair", "ym"], "pu")[0].iloc[0]
        b = fe_ols(o24, y, ["D_fake", "trend_T"], ["pair", "ym"], "pu")[0].iloc[0]
        c = fe_ols(od, y, ["D"], ["pair", "ym"], "pu")[0].iloc[0]
        d = fe_ols(od, y, ["D", "trend_T"], ["pair", "ym"], "pu")[0].iloc[0]
        op.append(dict(outcome=y, placebo_coef=a.coef, placebo_se=a.se, placebo_p=a.p,
                       placebo_trend_coef=b.coef, placebo_trend_se=b.se, placebo_trend_p=b.p,
                       real_coef=c.coef, real_se=c.se, real_p=c.p,
                       real_trend_coef=d.coef, real_trend_se=d.se, real_trend_p=d.p))
    pd.DataFrame(op).to_csv(TAB / "t49b_placebo_time_od.csv", index=False)


if want("perm"):
    zw = zone_week("hvfhv")
    # ---------------- (c) Hoán vị ----------------
    ctrl = zw[zw.treat == 0].zone.unique()
    n_t = zw[zw.treat == 1].zone.nunique()
    real = fe_ols(zw, "ln_n", ["D"], ["zone", "wk"], "zone")[0].coef[0]
    cz = zw[zw.treat == 0].copy()
    perm = []
    for i in range(500):
        fake_t = set(rng.choice(ctrl, size=n_t, replace=False))
        cz["Dp"] = (cz.zone.isin(fake_t) & (cz.post == 1)).astype(float)
        perm.append(fe_ols(cz, "ln_n", ["Dp"], ["zone", "wk"], "zone")[0].coef[0])
    perm = np.array(perm)
    meta["permutation"] = dict(real=float(real), n_perm=len(perm), p_two_sided=float((1 + np.sum(np.abs(perm) >= abs(real))) / (1 + len(perm))),
                               perm_mean=float(perm.mean()), perm_sd=float(perm.std()),
                               perm_p2_5=float(np.percentile(perm, 2.5)), perm_p97_5=float(np.percentile(perm, 97.5)))
    pd.DataFrame(dict(perm_coef=perm)).to_csv(TAB / "t50_permutation.csv", index=False)
    f, ax = fig(6.2, 3.0)
    ax.hist(100 * perm, bins=40, color=C["neutral"], edgecolor="white")
    ax.axvline(100 * real, color=C["s1"], lw=2)
    ax.annotate(f"Ước lượng thật: {100 * real:.1f}", (100 * real, ax.get_ylim()[1] * 0.9), xytext=(5, 0),
                textcoords="offset points")
    ax.set_xlabel("Hệ số DiD log số chuyến ×100 khi gán xử lý ngẫu nhiên")
    ax.set_ylabel("Số lần lặp")
    ax.set_title("Phân phối hoán vị (500 lần) so với ước lượng thật")
    save(f, "f33_permutation")


if want("robust"):
    zw = zone_week("hvfhv")
    # ---------------- (d) Bảng độ vững ----------------
    rob = []


    def add(name, pan, y="ln_n", fes=("zone", "wk"), w=None, D="D", cl="zone"):
        res, info, _ = fe_ols(pan, y, [D], list(fes), cl, w)
        r = res.iloc[0]
        rob.append(dict(spec=name, coef=r.coef, se=r.se, p=r.p, ci_low=r.ci_low, ci_high=r.ci_high,
                        pct=100 * (np.exp(r.coef) - 1) if y.startswith("ln") else np.nan,
                        n_obs=info["n_obs"], n_zones=int(pan.zone.nunique()),
                        n_treated=int(pan[pan.treat == 1].zone.nunique()), outcome=y))


    add("Cơ sở: CRZ vs MN bắc + quận ngoài, vùng ≥100 chuyến/ngày", zw)
    add("Đối chứng chỉ Manhattan phía bắc", zw[(zw.treat == 1) | (zw.grp == "MN_NORTH")])
    add("Đối chứng chỉ các quận ngoài", zw[(zw.treat == 1) | (zw.grp == "OUTER")])
    add("Đối chứng chỉ Brooklyn và Queens", zw[(zw.treat == 1) | (zw.Borough.isin(["Brooklyn", "Queens"]))])
    add("Ngưỡng vùng ≥50 chuyến/ngày", zone_week("hvfhv", min_daily=50))
    add("Ngưỡng vùng ≥300 chuyến/ngày", zone_week("hvfhv", min_daily=300))
    zp = zone_week("hvfhv", groups=("CRZ", "CRZ_PARTIAL", "MN_NORTH", "OUTER"))
    zp["treat"] = zp.grp.isin(["CRZ", "CRZ_PARTIAL"]).astype(int)
    zp["D"] = zp.treat * zp.post
    add("Gộp vùng vắt ranh giới vào nhóm xử lý", zp)
    add("Bỏ tuần lễ cuối năm (20/12–05/01)", zw[~(((zw.wk.dt.month == 12) & (zw.wk.dt.day >= 20)) | ((zw.wk.dt.month == 1) & (zw.wk.dt.day <= 5)))])
    add("Bỏ 4 tuần đầu sau chính sách", zw[(zw.k < 0) | (zw.k >= 4)])
    add("Chỉ 01–06/2025 là giai đoạn sau", zw[zw.wk < "2025-07-01"])
    add("Chỉ 07–12/2025 là giai đoạn sau", zw[(zw.wk < P) | (zw.wk >= "2025-07-01")])
    add("Có trọng số theo lưu lượng 2024", zw, w="w_pre")
    zt = zw.copy()
    zt["trend_T"] = zt.treat * zt.k / 52.0
    res_t, info_t, _ = fe_ols(zt, "ln_n", ["D", "trend_T"], ["zone", "wk"], "zone")
    r = res_t.iloc[0]
    rob.append(dict(spec="Thêm xu hướng tuyến tính riêng của nhóm xử lý", coef=r.coef, se=r.se, p=r.p,
                    ci_low=r.ci_low, ci_high=r.ci_high, pct=100 * (np.exp(r.coef) - 1), n_obs=info_t["n_obs"],
                    n_zones=int(zt.zone.nunique()), n_treated=int(zt[zt.treat == 1].zone.nunique()), outcome="ln_n"))
    zw2 = zw.copy()
    zw2["tw"] = zw2.treat.astype(str) + "_" + zw2.woy.astype(str)
    add("DDD: thêm FE nhóm × tuần-trong-năm", zw2, fes=("zone", "wk", "tw"))
    zw3 = zw.copy()
    zw3["bw"] = zw3.Borough + "_" + zw3.wk.astype(str)
    add("FE quận × tuần (so sánh trong cùng quận)", zw3[zw3.Borough == "Manhattan"], fes=("zone", "bw"))
    add("Phân cụm theo quận thay vì vùng (5 cụm, chỉ tham khảo)", zw, cl="Borough")
    zd = zone_day("hvfhv")
    add("Panel vùng × ngày", zd.rename(columns={"d": "wk"}))
    rb = pd.DataFrame(rob)
    rb.to_csv(TAB / "t51_robustness_ln_n.csv", index=False)
    print(rb[["spec", "coef", "se", "p", "pct"]].to_string(), flush=True)

    f, ax = fig(6.8, 4.6)
    yy = np.arange(len(rb))[::-1]
    ax.errorbar(100 * rb.coef, yy, xerr=[100 * (rb.coef - rb.ci_low), 100 * (rb.ci_high - rb.coef)], fmt="o",
                color=C["s1"], ecolor=C["s1"], ms=4, elinewidth=1)
    ax.axvline(0, color=C["text2"], lw=0.8)
    ax.axvline(100 * rb.coef.iloc[0], color=C["s1"], lw=0.8, ls=":")
    ax.set_yticks(yy, rb.spec, fontsize=7.5)
    ax.set_xlabel("Hệ số DiD log số chuyến đón ×100 (KTC 95%)")
    ax.set_title("Độ vững của ước lượng chính qua các đặc tả")
    save(f, "f34_robustness_forest")


(LOG / f"10_spillover_robustness_{PART}.json").write_text(json.dumps(dict(seconds=round(time.time() - t0, 1), **meta), indent=2, default=float))
print(meta, "time", round(time.time() - t0, 1))
