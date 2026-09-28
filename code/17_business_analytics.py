"""Bước 17 - Phân tích phục vụ quyết định kinh doanh và chiến lược dữ liệu.

Các phần:
  company    Tác động theo hãng (Uber, Lyft) và thị phần trong CRZ.                   -> t77
  forecast   Dự báo nhu cầu: so sánh mô hình dự báo số chuyến CRZ theo ngày trên giai đoạn
             giữ lại trước chính sách; dùng mô hình tốt nhất làm phản thực tế sau chính sách
             (cách tiếp cận kiểu CausalImpact).                                      -> t78, t79, f53
  power      Độ lớn tác động nhỏ nhất phát hiện được (MDE) theo độ dài giai đoạn sau
             chính sách: quy mô dữ liệu cần cho một "thử nghiệm A/B" chính sách.        -> t80, f54
  pricing    Độ nhạy của giá theo nhu cầu trong ngày (dấu hiệu định giá động) trước/sau. -> t81
  tco        Hạch toán tài nguyên của pipeline: dung lượng từng lớp, thời gian tính toán,
             tỷ lệ nén, tài nguyên cho mỗi triệu dòng.                                -> t82
Chạy:  python code/17_business_analytics.py <phần>
"""
import json
import sys
import time

import numpy as np
import pandas as pd

from causal import fe_ols
from config import GOLD, LOG, SEED, TAB
from panels import P, zone_week

BLOG = LOG / "business"
BLOG.mkdir(parents=True, exist_ok=True)


def wlog(name, rec):
    (BLOG / f"{name}.json").write_text(json.dumps(rec, indent=2, ensure_ascii=False, default=str))
    print(json.dumps(rec, ensure_ascii=False, default=str)[:900], flush=True)


# ------------------------------------------------------------------ company
def part_company():
    zw = zone_week("hvfhv", extra=("n_uber", "n_lyft"))
    zw["tw"] = zw.treat.astype(str) + "_" + zw.woy.astype(str)
    zw["ln_uber"] = np.log(zw.n_uber.clip(lower=1))
    zw["ln_lyft"] = np.log(zw.n_lyft.clip(lower=1))
    zw["uber_share"] = 100 * zw.n_uber / (zw.n_uber + zw.n_lyft)
    rows = []
    for y, lab in (("ln_uber", "log số chuyến Uber"), ("ln_lyft", "log số chuyến Lyft"),
                   ("uber_share", "Thị phần Uber trong HVFHV (%)")):
        for sname, fes in (("TWFE", ["zone", "wk"]), ("DDD mùa vụ", ["zone", "wk", "tw"])):
            res, info, _ = fe_ols(zw, y, ["D"], fes, "zone")
            r = res.iloc[0]
            pre = zw.loc[(zw.treat == 1) & (zw.post == 0), y].mean()
            rows.append(dict(outcome=y, outcome_label=lab, spec=sname, coef=r.coef, se=r.se, p=r.p,
                             ci_low=r.ci_low, ci_high=r.ci_high,
                             pct=100 * (np.exp(r.coef) - 1) if y.startswith("ln_") else np.nan,
                             treated_pre_mean=pre, n_obs=info["n_obs"], n_clusters=info["n_clusters"]))
    t = pd.DataFrame(rows)
    t.to_csv(TAB / "t77_company_did.csv", index=False)
    # Kiểm định chênh lệch Uber – Lyft: hồi quy xếp chồng, cụm theo vùng
    st = pd.concat([zw.assign(y=zw.ln_uber, firm=1), zw.assign(y=zw.ln_lyft, firm=0)])
    st["zf"] = st.zone.astype(str) + "_" + st.firm.astype(str)
    st["wf"] = st.wk.astype(str) + "_" + st.firm.astype(str)
    st["D_uber"] = st.D * st.firm
    res, info, _ = fe_ols(st, "y", ["D", "D_uber"], ["zf", "wf"], "zone")
    diff = res[res.term == "D_uber"].iloc[0].to_dict()
    pd.DataFrame([diff]).to_csv(TAB / "t77b_company_diff.csv", index=False)
    wlog("company", dict(rows=rows, diff=diff))


# ------------------------------------------------------------------ forecast
def daily_groups():
    z = pd.read_parquet(GOLD / "grp_hour_day.parquet")
    z = z[z.service == "hvfhv"]
    d = z.groupby(["d", "pu_grp"]).n.sum().unstack()
    d.index = pd.to_datetime(d.index)
    return d.sort_index()


def features(d):
    from pandas.tseries.holiday import USFederalHolidayCalendar
    hol = USFederalHolidayCalendar().holidays(d.index.min(), d.index.max())
    X = pd.DataFrame(index=d.index)
    X["ln_mn"] = np.log(d["MN_NORTH"])
    X["ln_out"] = np.log(d["OUTER"])
    for k in range(6):
        X[f"dow{k}"] = (d.index.dayofweek == k).astype(int)
    X["holiday"] = d.index.isin(hol).astype(int)
    X["hol_adj"] = (d.index.isin(hol + pd.Timedelta(days=1)) | d.index.isin(hol - pd.Timedelta(days=1))).astype(int)
    doy = d.index.dayofyear
    X["xmas"] = ((d.index.month == 12) & (d.index.day >= 20)) | ((d.index.month == 1) & (d.index.day <= 3))
    X["xmas"] = X.xmas.astype(int)
    X["trend"] = (d.index - d.index.min()).days / 365.0
    X["sin1"], X["cos1"] = np.sin(2 * np.pi * doy / 365.25), np.cos(2 * np.pi * doy / 365.25)
    return X


def part_forecast():
    import lightgbm as lgb
    from sklearn.linear_model import RidgeCV
    from viz import C, fig, save, policy_line
    d = daily_groups()
    y = np.log(d["CRZ"])
    X = features(d)
    tr_end, ho_end = pd.Timestamp("2024-10-31"), P - pd.Timedelta(days=1)
    tr, ho = X.index <= tr_end, (X.index > tr_end) & (X.index <= ho_end)
    cal = [c for c in X.columns if c not in ("ln_mn", "ln_out", "trend")]
    variants = {
        "Ridge: chỉ lịch + xu hướng": ("ridge", cal + ["trend"]),
        "Ridge: lịch + MN phía bắc + quận ngoài + xu hướng": ("ridge", cal + ["ln_mn", "ln_out", "trend"]),
        "Ridge: lịch + MN phía bắc + quận ngoài": ("ridge", cal + ["ln_mn", "ln_out"]),
        "Ridge: lịch + quận ngoài": ("ridge", cal + ["ln_out"]),
        "LightGBM: lịch + MN phía bắc + quận ngoài": ("lgb", cal + ["ln_mn", "ln_out"]),
    }

    def fit(kind, cols, mask):
        if kind == "ridge":
            return RidgeCV(alphas=np.logspace(-3, 3, 13)).fit(X[mask][cols], y[mask])
        return lgb.LGBMRegressor(n_estimators=400, learning_rate=0.03, num_leaves=15, min_child_samples=10,
                                 random_state=SEED, verbose=-1).fit(X[mask][cols], y[mask])

    pre = X.index < P
    acc, fits = [], {}
    naive = y.shift(7)
    e = np.exp(y[ho]) - np.exp(naive[ho])
    acc.append(dict(model="Naive theo tuần (t−7)", holdout_days=int(ho.sum()),
                    mape_pct=100 * np.mean(np.abs(e) / np.exp(y[ho])), rmse=float(np.sqrt(np.mean(e ** 2))),
                    bias_pct=100 * np.mean(e / np.exp(y[ho])), post_effect_pct=np.nan))
    for k, (kind, cols) in variants.items():
        p = pd.Series(fit(kind, cols, tr).predict(X[cols]), index=X.index)
        e = np.exp(y[ho]) - np.exp(p[ho])
        mfull = fit(kind, cols, pre)
        cf = pd.Series(mfull.predict(X[cols]), index=X.index)
        post_eff = 100 * (np.exp(np.mean((y - cf)[~pre])) - 1)
        fits[k] = (mfull, cols, cf)
        acc.append(dict(model=k, holdout_days=int(ho.sum()), mape_pct=100 * np.mean(np.abs(e) / np.exp(y[ho])),
                        rmse=float(np.sqrt(np.mean(e ** 2))), bias_pct=100 * np.mean(e / np.exp(y[ho])),
                        post_effect_pct=post_eff))
    acc = pd.DataFrame(acc).sort_values("mape_pct")
    acc.to_csv(TAB / "t78_forecast_accuracy.csv", index=False)
    # Quy tắc chọn định trước: mô hình có MAPE giữ lại thấp nhất (trừ naive, không dự báo xa được)
    best = acc[acc.model.isin(list(variants))].iloc[0].model
    m, cols_ctrl, cf = fits[best]
    resid = (y - cf)[pre]
    out = pd.DataFrame(dict(actual=np.exp(y), counterfactual=np.exp(cf)))
    out["effect_pct"] = 100 * (out.actual / out.counterfactual - 1)
    out["month"] = out.index.to_period("M").astype(str)
    # Khoảng tin cậy bằng bootstrap khối (khối 7 ngày) trên phần dư trước chính sách
    rng = np.random.default_rng(SEED)
    r = resid.values
    B = 500
    mon = []
    post = out[out.index >= P]
    for mth, g in post.groupby("month"):
        L = len(g)
        sims = []
        for _ in range(B):
            starts = rng.integers(0, len(r) - 7, size=int(np.ceil(L / 7)))
            e = np.concatenate([r[s:s + 7] for s in starts])[:L]
            sims.append(np.mean(e))
        gap = np.mean(np.log(g.actual.values) - np.log(g.counterfactual.values))
        lo, hi = np.percentile(gap - np.array(sims), [2.5, 97.5])
        mon.append(dict(month=mth, days=L, effect_pct=100 * (np.exp(gap) - 1),
                        ci_low=100 * (np.exp(lo) - 1), ci_high=100 * (np.exp(hi) - 1)))
    mon = pd.DataFrame(mon)
    mon["model"] = best
    all_post = 100 * (np.exp(np.mean(np.log(post.actual) - np.log(post.counterfactual))) - 1)
    mon.to_csv(TAB / "t79_forecast_counterfactual_monthly.csv", index=False)
    out.reset_index(names="d").to_csv(TAB / "t79b_forecast_daily.csv", index=False)
    coef = pd.Series(getattr(m, "coef_", np.full(len(cols_ctrl), np.nan)), index=cols_ctrl)
    f, axes = fig(6.8, 4.4, nrows=2, sharex=True)
    wk = out.resample("W-SAT").mean(numeric_only=True)
    axes[0].plot(wk.index, wk.actual / 1e3, color=C["s1"], label="Thực tế")
    axes[0].plot(wk.index, wk.counterfactual / 1e3, color=C["s2"], ls="--", label="Dự báo phản thực tế")
    axes[0].set_ylabel("Nghìn chuyến/ngày")
    axes[0].legend(loc="lower left")
    axes[0].set_title("Dự báo nhu cầu làm phản thực tế cho số chuyến đón trong CRZ")
    policy_line(axes[0], P)
    axes[1].bar(pd.to_datetime(mon.month) + pd.Timedelta(days=14), mon.effect_pct, width=20, color=C["s1"])
    axes[1].errorbar(pd.to_datetime(mon.month) + pd.Timedelta(days=14), mon.effect_pct,
                     yerr=[mon.effect_pct - mon.ci_low, mon.ci_high - mon.effect_pct], fmt="none", color=C["text2"], lw=0.8)
    axes[1].axhline(0, color=C["text2"], lw=0.7)
    axes[1].set_ylabel("Thực tế so với dự báo (%)")
    f.tight_layout()
    save(f, "f53_forecast_counterfactual")
    wlog("forecast", dict(best=best, accuracy=acc.to_dict("records"), post_effect_pct=all_post,
                          coef=coef.to_dict(), resid_sd=float(resid.std())))


# ------------------------------------------------------------------ power
def part_power():
    from viz import C, fig, save
    zw = zone_week("hvfhv")
    rows = []
    for L in (4, 8, 13, 26, 39, 52):
        sub = zw[(zw.k < L)]
        for y, lab in (("ln_n", "log số chuyến"), ("mph", "Tốc độ (dặm/giờ)"), ("wait", "Thời gian chờ (phút)")):
            res, info, _ = fe_ols(sub, y, ["D"], ["zone", "wk"], "zone")
            r = res.iloc[0]
            rows.append(dict(post_weeks=L, outcome=y, outcome_label=lab, coef=r.coef, se=r.se, p=r.p,
                             mde80=2.8 * r.se, n_obs=info["n_obs"]))
    t = pd.DataFrame(rows)
    t["mde80_pct"] = np.where(t.outcome == "ln_n", 100 * (np.exp(t.mde80) - 1), np.nan)
    t.to_csv(TAB / "t80_power_mde.csv", index=False)
    f, axes = fig(6.8, 2.9, ncols=3)
    for ax, (y, lab) in zip(axes, (("ln_n", "log số chuyến"), ("mph", "Tốc độ (dặm/giờ)"), ("wait", "Chờ (phút)"))):
        d = t[t.outcome == y]
        ax.plot(d.post_weeks, d.coef.abs(), marker="o", color=C["s1"], label="|Ước lượng|")
        ax.plot(d.post_weeks, d.mde80, marker="s", color=C["s2"], label="MDE (80%, α=5%)")
        ax.set_title(lab, fontsize=9)
        ax.set_xlabel("Số tuần sau chính sách")
    axes[0].legend(fontsize=7)
    f.tight_layout()
    save(f, "f54_power_mde")
    wlog("power", dict(rows=rows))


# ------------------------------------------------------------------ pricing
def part_pricing():
    h = pd.read_parquet(GOLD / "zone_hour_month.parquet")
    h = h[h.service == "hvfhv"].copy()
    dm = pd.read_parquet(GOLD / "dim_zone.parquet")[["LocationID", "grp"]]
    h = h.merge(dm, left_on="zone", right_on="LocationID")
    rows = []
    for grp in ("CRZ", "MN_NORTH", "OUTER"):
        g = h[(h.grp == grp) & (h.n >= 200)].copy()
        g["ln_fpm"] = np.log(g.fare / g.miles)
        g["ln_n"] = np.log(g.n)
        g["ln_mph"] = np.log(g.miles / (g.time_s / 3600))
        g["zm"] = g.zone.astype(str) + "_" + g.ym
        for per, gg in (("2024", g[g.ym < "2025-01"]), ("2025", g[g.ym >= "2025-01"])):
            res, info, _ = fe_ols(gg, "ln_fpm", ["ln_n", "ln_mph"], ["zm"], "zone")
            for _, r in res.iterrows():
                rows.append(dict(group=grp, period=per, term=r.term, coef=r.coef, se=r.se, p=r.p,
                                 n_obs=info["n_obs"], n_clusters=info["n_clusters"], within_r2=info["within_r2"]))
    t = pd.DataFrame(rows)
    t.to_csv(TAB / "t81_price_demand_elasticity.csv", index=False)
    wlog("pricing", dict(rows=rows))


# ------------------------------------------------------------------ tco
def part_tco():
    man = pd.read_csv(TAB / "t01_bronze_manifest.csv")
    q = pd.read_csv(TAB / "t06_quality_by_month.csv")
    cat = pd.read_csv(TAB / "t68_data_catalog.csv")
    steps = {}
    for f in list(LOG.glob("*.json")):
        try:
            d = json.loads(f.read_text())
            if isinstance(d, dict) and "seconds" in d:
                steps[f.stem] = float(d["seconds"])
        except Exception:
            pass
    spark = pd.read_csv(TAB / "t60b_spark_repro_totals.csv")
    rows = []
    n_raw = int(man.n_rows.sum())
    for layer in ("Bronze", "Silver", "Gold"):
        c = cat[cat.layer == layer]
        rows.append(dict(item=f"Dung lượng lớp {layer}", value=c.size_mb.sum() / 1024, unit="GB",
                         note=f"{int(c.rows.sum()):,} dòng; {int(c.files.sum())} tệp"))
    rows.append(dict(item="Thời gian lớp Silver + Gold (bước 03)", value=q.sec_total.sum() / 60, unit="phút",
                     note="2 luồng, giới hạn bộ nhớ DuckDB 1,8 GB"))
    rows.append(dict(item="Thời gian hợp nhất Gold (bước 04)", value=steps.get("04_gold_consolidate", np.nan) / 60,
                     unit="phút", note=""))
    ana = {k: v for k, v in steps.items() if k[:2] in ("06", "07", "08", "09", "10", "11", "14")}
    rows.append(dict(item="Thời gian các bước phân tích 06–11, 14", value=sum(ana.values()) / 60, unit="phút",
                     note=f"{len(ana)} nhật ký"))
    rows.append(dict(item="Tài nguyên xử lý Silver+Gold trên mỗi triệu dòng Bronze",
                     value=q.sec_total.sum() * 2 / (n_raw / 1e6), unit="lõi·giây", note="= thời gian × 2 lõi / triệu dòng"))
    rows.append(dict(item="Tái lập zone_day_pu bằng Spark trên mỗi triệu dòng Silver",
                     value=spark.seconds.sum() * 2 / (spark.n_silver.sum() / 1e6), unit="lõi·giây", note="local[2]"))
    rows.append(dict(item="Tỷ lệ Gold / Bronze theo dung lượng",
                     value=100 * cat[cat.layer == "Gold"].size_mb.sum() / cat[cat.layer == "Bronze"].size_mb.sum(),
                     unit="%", note="mức cô đặc thông tin cho phân tích"))
    t = pd.DataFrame(rows)
    t.to_csv(TAB / "t82_resource_accounting.csv", index=False)
    wlog("tco", dict(rows=rows))


if __name__ == "__main__":
    fn = {"company": part_company, "forecast": part_forecast, "power": part_power, "pricing": part_pricing,
          "tco": part_tco}
    fn[sys.argv[1]]()
