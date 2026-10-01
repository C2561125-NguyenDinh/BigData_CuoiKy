"""Bước 20 - Suy luận bền vững cho các kết quả chính.

Bổ sung cho bước 07 và 19 bốn nhóm kiểm tra mà phân tích ban đầu chưa có:

(A) Sai số chuẩn và kiểm định bội trên panel chính (vùng × tuần, HVFHV, TWFE):
    - sai số phân cụm hai chiều (vùng và tuần);
    - sai số Conley (HAC không gian, nhân Bartlett, ngưỡng 2/5/10 km) cộng tương quan theo thời gian trong vùng;
    - wild cluster bootstrap theo vùng (trọng số Webb 6 điểm, giả thuyết H0 được áp đặt khi tính p);
    - hiệu chỉnh kiểm định bội cho họ 8 chỉ tiêu chính: Holm, Benjamini–Hochberg và Romano–Wolf
      (stepdown trên bootstrap chung)                                                      -> t92, t92b
(B) Độ nhạy của tác động sau điều chỉnh xu hướng với cách chọn năm gốc và dạng xu hướng trên panel
    vùng × tháng 2022–2025 (cùng mẫu với bước 19), sai số bằng wild cluster bootstrap         -> t93, f59
(C) Độ nhạy Rambachan–Roth (RM và SD) với khoảng tin cậy bootstrap cho tập nhận dạng: max_pre|Δβ|
    được ước lượng lại trong mỗi lần bootstrap thay vì coi là hằng số; điểm gãy trên lưới mịn   -> t94, t94b, f60
(D) DML: độ nhạy theo ngưỡng cắt xu hướng, quy tắc cắt của Crump và cộng sự (2009),
    ước lượng trọng số chồng lấn (ATO) và sai số phân cụm theo vùng đón                      -> t95

Chạy:  python code/20_inference_robustness.py
"""
import json
import time
import warnings

import numpy as np
import pandas as pd
from scipy import stats

from causal import demean_fe, fe_ols
from config import GOLD, LOG, SEED, TAB
from panels import MIN_DAILY, SUMS, add_ratios, dim, zone_week
from viz import C, fig, plt, save

warnings.filterwarnings("ignore")
t0 = time.time()
rng = np.random.default_rng(SEED)
B = 9999
WEBB = np.array([-np.sqrt(1.5), -1.0, -np.sqrt(0.5), np.sqrt(0.5), 1.0, np.sqrt(1.5)])

dmz = dim().set_index("LocationID")
XY = np.c_[dmz.cx_ft, dmz.cy_ft] * 0.0003048          # toạ độ State Plane (ft) -> km


def boot_weights(G, B, rng):
    return rng.choice(WEBB, size=(B, G))


# ============================================================================ (A)
FAMILY = {"ln_n": "log số chuyến", "mph": "Tốc độ (dặm/giờ)", "wait": "Thời gian chờ (phút)",
          "fare_pm": "Giá cước cơ sở/dặm (USD)", "pay_pm": "Thu nhập tài xế/dặm (USD)",
          "rider_pt": "Chi phí hành khách/chuyến (USD)", "pay_share": "Thu nhập tài xế/giá cước (%)",
          "shared_pct": "Tỷ lệ yêu cầu đi chung (%)"}
zw = zone_week("hvfhv")
zones = np.sort(zw.zone.unique())
zidx = {z: i for i, z in enumerate(zones)}
G = len(zones)
V_ALL = boot_weights(G, B, rng)                          # cùng trọng số cho mọi chỉ tiêu (để tính Romano–Wolf)
dist = np.sqrt(((XY[[dmz.index.get_loc(z) for z in zones]][:, None, :] -
                 XY[[dmz.index.get_loc(z) for z in zones]][None, :, :]) ** 2).sum(-1))
rowsA, tstar_u, tobs = [], {}, {}
for y, lab in FAMILY.items():
    d = zw.dropna(subset=[y]).reset_index(drop=True)
    Z, _ = demean_fe(d, [y, "D"], ["zone", "wk"])
    yt, xt = Z[:, 0], Z[:, 1]
    g = d.zone.map(zidx).to_numpy()
    w = pd.factorize(d.wk)[0]
    n, Wn = len(d), w.max() + 1
    k_fe = d.zone.nunique() + d.wk.nunique() - 1
    sxx = float(xt @ xt)
    b = float(xt @ yt) / sxx
    e = yt - b * xt
    adj = G / (G - 1) * (n - 1) / max(n - 1 - k_fe, 1)

    def cl_var(codes, ncl, score):
        s = np.bincount(codes, weights=score, minlength=ncl)
        return float(s @ s) / sxx ** 2

    sc = xt * e
    v_z = cl_var(g, G, sc)
    v_w = cl_var(w, Wn, sc)
    v_zw = float(sc @ sc) / sxx ** 2
    se_cr1 = np.sqrt(adj * v_z)
    se_2w = np.sqrt(adj * max(v_z + v_w - v_zw, v_z))
    # Conley: tương quan theo thời gian trong vùng (cụm vùng) + tương quan không gian giữa các vùng trong cùng tuần
    S = np.zeros((Wn, G))
    np.add.at(S, (w, g), sc)
    conley = {}
    for cut in (2, 5, 10):
        K = np.clip(1 - dist / cut, 0, None)
        np.fill_diagonal(K, 0)
        spatial = float(np.einsum("tg,gh,th->", S, K, S))
        conley[cut] = np.sqrt(adj * (v_z * sxx ** 2 + spatial) / sxx ** 2)
    # Wild cluster bootstrap
    A_r = np.bincount(g, weights=xt * yt, minlength=G)    # điểm số dưới H0 (β = 0): phần dư = y đã khử FE
    Q = np.bincount(g, weights=xt * xt, minlength=G)
    bs_r = V_ALL @ A_r / sxx
    sc_r = V_ALL * A_r[None, :] - bs_r[:, None] * Q[None, :]
    se_r = np.sqrt(adj * (sc_r ** 2).sum(1)) / sxx
    t_obs = b / se_cr1
    p_wcr = float(np.mean(np.abs(bs_r / se_r) >= abs(t_obs)))
    A_u = np.bincount(g, weights=xt * e, minlength=G)
    db = V_ALL @ A_u / sxx
    sc_u = V_ALL * A_u[None, :] - db[:, None] * Q[None, :]
    se_u = np.sqrt(adj * (sc_u ** 2).sum(1)) / sxx
    tu = db / se_u
    q_lo, q_hi = np.quantile(tu, [0.025, 0.975])
    tstar_u[y], tobs[y] = tu, t_obs
    p_cr1 = float(2 * stats.t.sf(abs(t_obs), G - 1))
    rowsA.append(dict(outcome=y, label=lab, coef=b, se_cr1=se_cr1, p_cr1=p_cr1, se_twoway=se_2w,
                      p_twoway=float(2 * stats.t.sf(abs(b / se_2w), min(G, Wn) - 1)),
                      se_conley2=conley[2], se_conley5=conley[5], se_conley10=conley[10],
                      p_conley10=float(2 * stats.norm.sf(abs(b / conley[10]))),
                      p_wild=max(p_wcr, 1 / (B + 1)), wild_ci_low=b - q_hi * se_cr1, wild_ci_high=b - q_lo * se_cr1,
                      n_obs=n, n_clusters=G, n_weeks=int(Wn)))
A = pd.DataFrame(rowsA)
# Kiểm định bội trên họ 8 chỉ tiêu
m = len(A)
for col, out in (("p_cr1", "holm_cr1"), ("p_wild", "holm_wild")):
    o = np.argsort(A[col].to_numpy())
    adjp = np.maximum.accumulate([(m - i) * A[col].to_numpy()[j] for i, j in enumerate(o)])
    A.loc[A.index[o], out] = np.minimum(adjp, 1)
o = np.argsort(A.p_wild.to_numpy())[::-1]
bh = np.minimum.accumulate([A.p_wild.to_numpy()[j] * m / (m - i) for i, j in enumerate(o)])
A.loc[A.index[o], "bh_wild"] = np.minimum(bh, 1)
# Romano–Wolf stepdown (bootstrap-t chung, không áp đặt H0 – thống kê đã được định tâm)
T = np.abs(np.c_[[tstar_u[y] for y in A.outcome]]).T     # B × m
to = np.abs(A.outcome.map(tobs).to_numpy())
order = np.argsort(-to)
rw = np.zeros(m)
for i, j in enumerate(order):
    rest = order[i:]
    rw[j] = np.mean(T[:, rest].max(1) >= to[j])
rw[order] = np.maximum.accumulate(rw[order])
A["romano_wolf"] = np.maximum(rw, 1 / (B + 1))
A.to_csv(TAB / "t92_inference_main.csv", index=False)
print(A[["outcome", "coef", "se_cr1", "se_twoway", "se_conley10", "p_wild", "holm_wild", "romano_wolf"]], flush=True)

# Kiểm định bội cho toàn bộ bảng t30 (mọi chỉ tiêu × đặc tả, HVFHV và taxi vàng)
t30 = pd.read_csv(TAB / "t30_did_main.csv")
pv = t30.p.to_numpy()
mm = len(pv)
o = np.argsort(pv)
holm = np.minimum(np.maximum.accumulate([(mm - i) * pv[j] for i, j in enumerate(o)]), 1)
t30.loc[t30.index[o], "p_holm"] = holm
o2 = o[::-1]
bh = np.minimum(np.minimum.accumulate([pv[j] * mm / (mm - i) for i, j in enumerate(o2)]), 1)
t30.loc[t30.index[o2], "q_bh"] = bh
t30[["service", "outcome", "outcome_label", "spec", "coef", "p", "p_holm", "q_bh"]].to_csv(TAB / "t92b_multiple_testing_t30.csv", index=False)

# ============================================================================ (B)
z = pd.read_parquet(GOLD / "long" / "zone_day_pu.parquet")
z = z[z.service == "hvfhv"].copy()
z["d"] = pd.to_datetime(z.d)
z = z[(z.d >= "2022-01-01") & (z.d <= "2025-12-31")]
z["ym"] = z.d.dt.to_period("M")
z = z.merge(dim()[["LocationID", "grp"]], left_on="zone", right_on="LocationID")
z = z[z.grp.isin(["CRZ", "MN_NORTH", "OUTER"])]
gl = z.groupby(["zone", "grp", "ym"])[SUMS].sum().reset_index()
pre24 = z[(z.d >= "2024-01-07") & (z.d < "2025-01-05")].groupby("zone").n.sum() / 364
keep = pre24[pre24 >= MIN_DAILY["hvfhv"]].index
cnt = gl.groupby("zone").ym.nunique()
keep = [k for k in keep if cnt.get(k, 0) == 48]
gl = add_ratios(gl[gl.zone.isin(keep)].copy())
gl["treat"] = (gl.grp == "CRZ").astype(int)
gl["year"], gl["moy"] = gl.ym.dt.year, gl.ym.dt.month
gl["ymc"] = gl.ym.astype(str)
gl["tm"] = gl.treat.astype(str) + "_" + gl.moy.astype(str)
LONG_OUT = {"ln_n": "log số chuyến", "mph": "Tốc độ (dặm/giờ)", "wait": "Thời gian chờ (phút)",
            "fare_pm": "Giá cước cơ sở/dặm (USD)", "pay_pm": "Thu nhập tài xế/dặm (USD)",
            "shared_pct": "Tỷ lệ yêu cầu đi chung (%)"}
SPECS = {
    "S1": dict(label="Gốc 2022, xu hướng tuyến tính 2023–2024 (bước 19)", base=2022, drop_moy=(), trend=(2023, 2024), deg=1),
    "S2": dict(label="Gốc 2022, bỏ tháng 1–2 mọi năm (Omicron)", base=2022, drop_moy=(1, 2), trend=(2023, 2024), deg=1),
    "S3": dict(label="Gốc 2023 (bỏ 2022), xu hướng tuyến tính 2024", base=2023, drop_moy=(), trend=(2024, 2024), deg=1),
    "S4": dict(label="Gốc 2022, xu hướng bậc hai 2023–2024", base=2022, drop_moy=(), trend=(2023, 2024), deg=2),
    "S5": dict(label="Gốc 2022, xu hướng tuyến tính chỉ từ 2024", base=2022, drop_moy=(), trend=(2024, 2024), deg=1),
    "S6": dict(label="Gốc 2022, không điều chỉnh xu hướng (2025 − 2024)", base=2022, drop_moy=(), trend=None, deg=0),
}


def long_fit(spec, y):
    d = gl[(gl.year >= spec["base"]) & (~gl.moy.isin(spec["drop_moy"]))].dropna(subset=[y]).copy()
    ev = sorted(m for m in d.ym.unique() if m.year > spec["base"])
    names = []
    for mth in ev:
        nm = f"e_{mth}"
        d[nm] = ((d.ym == mth) & (d.treat == 1)).astype(float)
        names.append(nm)
    d = d.reset_index(drop=True)
    Zm, _ = demean_fe(d, [y] + names, ["zone", "ymc", "tm"])
    yt, X = Zm[:, 0], Zm[:, 1:]
    XtX_inv = np.linalg.pinv(X.T @ X)
    b = XtX_inv @ X.T @ yt
    e = yt - X @ b
    gi = pd.factorize(d.zone)[0]
    Gl = gi.max() + 1
    Cg = np.zeros((Gl, X.shape[1]))
    np.add.at(Cg, gi, X * e[:, None])
    n, k = X.shape
    k_fe = d.zone.nunique() + d.ymc.nunique() + d.tm.nunique() - 2
    adj = Gl / (Gl - 1) * (n - 1) / max(n - k - k_fe, 1)
    V = adj * XtX_inv @ Cg.T @ Cg @ XtX_inv
    Db = boot_weights(Gl, 1999, np.random.default_rng(SEED + 7)) @ Cg @ XtX_inv   # 1999 × K, b* − b̂
    return np.array(ev), b, V, Db, Gl


def trend_weights(ev, spec):
    """Vector a sao cho a·β = tác động 2025 so với 2024 sau khi trừ xu hướng ngoại suy."""
    yrs = np.array([mth.year for mth in ev])
    kk = np.array([(mth.year - 2023) * 12 + mth.month - 1 for mth in ev], dtype=float)
    a25 = (yrs == 2025) / (yrs == 2025).sum()
    a24 = (yrs == 2024) / (yrs == 2024).sum()
    a = a25 - a24
    if spec["trend"] is None:
        return a
    lo, hi = spec["trend"]
    pre = np.where((yrs >= lo) & (yrs <= hi))[0]
    Xp = np.vander(kk[pre], spec["deg"] + 1, increasing=True)
    H = np.linalg.pinv(Xp.T @ Xp) @ Xp.T
    S = np.zeros((len(pre), len(ev)))
    S[np.arange(len(pre)), pre] = 1
    CL = H @ S
    tp = np.vander(kk[yrs == 2025], spec["deg"] + 1, increasing=True) @ CL
    t4 = np.vander(kk[yrs == 2024], spec["deg"] + 1, increasing=True) @ CL
    return a - (tp.mean(0) - t4.mean(0))


rowsB, store = [], {}
for sk, spec in SPECS.items():
    for y, lab in LONG_OUT.items():
        ev, b, V, Db, Gl = long_fit(spec, y)
        a = trend_weights(ev, spec)
        est = float(a @ b)
        se = float(np.sqrt(a @ V @ a))
        bs = Db @ a
        lo_, hi_ = np.quantile(bs, [0.025, 0.975])
        rowsB.append(dict(spec=sk, spec_label=spec["label"], outcome=y, label=lab, effect=est, se_cr1=se,
                          p_cr1=float(2 * stats.t.sf(abs(est / se), Gl - 1)), se_wild=float(bs.std(ddof=1)),
                          ci_low_wild=est - hi_, ci_high_wild=est - lo_, n_event=len(ev), n_clusters=Gl))
        if sk in ("S1", "S2") and y in ("ln_n", "mph", "wait"):
            store[(sk, y)] = (ev, b, V, Db)
    print(sk, "done", round(time.time() - t0), flush=True)
Bt = pd.DataFrame(rowsB)
Bt.to_csv(TAB / "t93_trend_spec_sensitivity.csv", index=False)

f, axs = fig(w=11.5, h=3.6, ncols=3)
for ax, y in zip(axs, ("ln_n", "mph", "wait")):
    s = Bt[Bt.outcome == y].reset_index(drop=True)
    yy = np.arange(len(s))[::-1]
    sc_ = 100 if y == "ln_n" else 1
    ax.errorbar(s.effect * sc_, yy, xerr=[(s.effect - s.ci_low_wild) * sc_, (s.ci_high_wild - s.effect) * sc_],
                fmt="o", color=C["s1"], ecolor=C["s1"], capsize=3, ms=4)
    ax.axvline(0, color="0.4", lw=0.8)
    ax.set_yticks(yy)
    ax.set_yticklabels(s.spec)
    ax.set_title(LONG_OUT[y] + (" ×100" if y == "ln_n" else ""), fontsize=9.5)
f.tight_layout()
save(f, "f59_trend_spec_sensitivity")

# ============================================================================ (C)
# Độ nhạy Rambachan–Roth với suy luận bootstrap cho cả hai đầu của tập nhận dạng.
# Tham số: θ = TB(β_2025) − β_2024-12 (RM) hoặc tác động sau điều chỉnh xu hướng tuyến tính (SD).
# RM(M̄): |δ_t − δ_{t−1}| ≤ M̄ · max_pre |Δβ|  ⇒  |độ chệch của θ| ≤ M̄ · max_pre|Δβ| · TB(k), k = số tháng kể từ 12/2024.
# SD(M): độ cong của độ chệch so với xu hướng tuyến tính ≤ M mỗi tháng² ⇒ |độ chệch| ≤ M · TB(k(k+1)/2).
# Khác bước 19 ở chỗ max_pre|Δβ| cũng được ước lượng lại trong mỗi lần bootstrap (không coi là hằng số),
# và khoảng tin cậy lấy phân vị 2,5% của cận dưới và 97,5% của cận trên trên cùng các lần bootstrap
# (khoảng tin cậy cho tập nhận dạng theo kiểu Imbens–Manski, bảo thủ).
def rr_parts(ev, b, Db, sk):
    yrs = np.array([mth.year for mth in ev])
    pre, post = np.where(yrs <= 2024)[0], np.where(yrs == 2025)[0]
    kpost = np.arange(1, len(post) + 1)
    a_rm = np.zeros(len(ev))
    a_rm[post] = 1 / len(post)
    a_rm[pre[-1]] -= 1
    a_sd = trend_weights(ev, SPECS[sk])
    bstar = b[None, :] + Db
    return dict(th_rm=float(a_rm @ b), th_rm_b=bstar @ a_rm, th_sd=float(a_sd @ b), th_sd_b=bstar @ a_sd,
                dmax=float(np.abs(np.diff(b[pre])).max()), dmax_b=np.abs(np.diff(bstar[:, pre], axis=1)).max(1),
                w_rm=float(kpost.mean()), w_sd=float(np.mean(kpost * (kpost + 1) / 2)))


rowsC, brk = [], []
for (sk, y), (ev, b, V, Db) in store.items():
    r = rr_parts(ev, b, Db, sk)
    se_sd = float(r["th_sd_b"].std(ddof=1))
    for M in (0, 0.25, 0.5, 1.0, 1.5, 2.0):
        bd_, bdb = M * r["dmax"] * r["w_rm"], M * r["dmax_b"] * r["w_rm"]
        rowsC.append(dict(spec=sk, outcome=y, restriction="RM", M=M, M_rel_se=np.nan, theta=r["th_rm"],
                          set_low=r["th_rm"] - bd_, set_high=r["th_rm"] + bd_,
                          ci_low=float(np.quantile(r["th_rm_b"] - bdb, 0.025)),
                          ci_high=float(np.quantile(r["th_rm_b"] + bdb, 0.975)), max_pre_delta=r["dmax"]))
    for Mr in (0, 0.05, 0.1, 0.25, 0.5, 1.0):
        M = Mr * se_sd / r["w_sd"]                    # M được chọn sao cho độ chệch tối đa = Mr × sai số chuẩn
        rowsC.append(dict(spec=sk, outcome=y, restriction="SD", M=M, M_rel_se=Mr, theta=r["th_sd"],
                          set_low=r["th_sd"] - M * r["w_sd"], set_high=r["th_sd"] + M * r["w_sd"],
                          ci_low=float(np.quantile(r["th_sd_b"] - M * r["w_sd"], 0.025)),
                          ci_high=float(np.quantile(r["th_sd_b"] + M * r["w_sd"], 0.975)), max_pre_delta=r["dmax"]))
    bd = np.nan
    for M in np.arange(0, 3.0001, 0.005):
        lo = np.quantile(r["th_rm_b"] - M * r["dmax_b"] * r["w_rm"], 0.025)
        hi = np.quantile(r["th_rm_b"] + M * r["dmax_b"] * r["w_rm"], 0.975)
        if lo <= 0 <= hi:
            bd = M
            break
    bsd = np.nan
    lo0, hi0 = np.quantile(r["th_sd_b"], [0.025, 0.975])
    if not (lo0 <= 0 <= hi0):
        bsd = (min(abs(lo0), abs(hi0))) / r["w_sd"]   # M (đơn vị kết quả/tháng²) làm khoảng tin cậy SD chạm 0
    else:
        bsd = 0.0
    brk.append(dict(spec=sk, outcome=y, theta_rm=r["th_rm"], max_pre_delta=r["dmax"], breakdown_RM=bd,
                    theta_sd=r["th_sd"], se_sd=se_sd, breakdown_SD=bsd, breakdown_SD_rel_se=bsd * r["w_sd"] / se_sd))
Ct = pd.DataFrame(rowsC)
Ct["covers_zero"] = (Ct.ci_low <= 0) & (Ct.ci_high >= 0)
Ct.to_csv(TAB / "t94_rr_bootstrap.csv", index=False)
pd.DataFrame(brk).to_csv(TAB / "t94b_rr_breakdown.csv", index=False)
print(pd.DataFrame(brk), flush=True)

f, axs = fig(w=11.5, h=3.4, ncols=3)
for ax, y in zip(axs, ("ln_n", "mph", "wait")):
    sc_ = 100 if y == "ln_n" else 1
    for sk, col, off, lab_ in (("S1", C["s1"], -0.03, "S1: gốc 2022"), ("S2", C["s2"], 0.03, "S2: bỏ tháng 1–2")):
        s = Ct[(Ct.outcome == y) & (Ct.spec == sk) & (Ct.restriction == "RM")]
        ax.vlines(s.M + off, s.ci_low * sc_, s.ci_high * sc_, color=col, lw=2.2, label=lab_)
    ax.axhline(0, color="0.4", lw=0.8)
    ax.set_xlabel("M̄ (độ lớn tương đối)")
    ax.set_title(LONG_OUT[y] + (" ×100" if y == "ln_n" else ""), fontsize=9.5)
axs[0].legend(fontsize=7.5)
f.tight_layout()
save(f, "f60_rr_bootstrap")

# ============================================================================ (D)
import lightgbm as lgb  # noqa: E402
from sklearn.model_selection import KFold  # noqa: E402

df = pd.read_parquet(GOLD / "dml_od_dataset.parquet")
XC = ["ln_n_2024", "miles_pt", "min_pt", "tips_pt", "uber_share", "night_share", "same_zone"]
X = df[XC].to_numpy()
Dd = df.D.to_numpy()
e_hat = df.e_hat.to_numpy()
kf = KFold(5, shuffle=True, random_state=SEED)
params = dict(n_estimators=400, learning_rate=0.03, num_leaves=15, min_child_samples=40, subsample=0.8,
              subsample_freq=1, colsample_bytree=0.8, reg_lambda=1.0, random_state=SEED, verbose=-1, n_jobs=2)
# Ngưỡng tối ưu của Crump, Hotz, Imbens và Mitnik (2009): giữ e ∈ [α, 1−α] với α thoả điều kiện
h = 1 / (e_hat * (1 - e_hat))
alpha_c = 0.0
for g_ in np.sort(h)[::-1]:
    if g_ <= 2 * h[h <= g_].mean():
        alpha_c = 0.5 - np.sqrt(0.25 - 1 / g_)
        break
rowsD = []
pu = pd.factorize(df.pu)[0]
for yname in ("dlog_n", "d_mph", "d_pay_pm"):
    Y = df[yname].to_numpy()
    mu1, mu0 = np.zeros(len(df)), np.zeros(len(df))
    for tr, te in kf.split(X):
        t1, t0_ = tr[Dd[tr] == 1], tr[Dd[tr] == 0]
        mu1[te] = lgb.LGBMRegressor(**params).fit(X[t1], Y[t1]).predict(X[te])
        mu0[te] = lgb.LGBMRegressor(**params).fit(X[t0_], Y[t0_]).predict(X[te])
    for name, a_ in (("0,01", 0.01), ("0,025", 0.025), ("0,05 (chính)", 0.05), ("0,10", 0.10),
                     (f"Crump ({alpha_c:.3f})".replace(".", ","), alpha_c)):
        kp = (e_hat >= a_) & (e_hat <= 1 - a_)
        ec = np.clip(e_hat, a_, 1 - a_)
        phi = mu1 - mu0 + Dd * (Y - mu1) / ec - (1 - Dd) * (Y - mu0) / (1 - ec)
        est = phi[kp].mean()
        se_iid = phi[kp].std(ddof=1) / np.sqrt(kp.sum())
        s = np.bincount(pu[kp], weights=phi[kp] - est)
        se_cl = np.sqrt((s @ s)) / kp.sum()
        rowsD.append(dict(outcome=yname, estimator="AIPW cắt xu hướng", trim=name, n_used=int(kp.sum()),
                          n_treated=int(Dd[kp].sum()), estimate=est, se_iid=se_iid, se_cluster_pu=se_cl))
    # ATO (trọng số chồng lấn, Li, Morgan và Zaslavsky 2018), dạng tăng cường
    hw = e_hat * (1 - e_hat)
    num = hw * (mu1 - mu0) + Dd * (1 - e_hat) * (Y - mu1) - (1 - Dd) * e_hat * (Y - mu0)
    est = num.sum() / hw.sum()
    psi = (num - est * hw) / hw.mean()
    s = np.bincount(pu, weights=psi)
    rowsD.append(dict(outcome=yname, estimator="ATO (trọng số chồng lấn)", trim="không cắt", n_used=len(df),
                      n_treated=int(Dd.sum()), estimate=est, se_iid=psi.std(ddof=1) / np.sqrt(len(df)),
                      se_cluster_pu=np.sqrt(s @ s) / len(df)))
Dt = pd.DataFrame(rowsD)
Dt.to_csv(TAB / "t95_dml_trimming.csv", index=False)
print(Dt, flush=True)

(LOG / "20_inference_robustness.json").write_text(json.dumps(dict(
    seconds=round(time.time() - t0, 1), bootstrap_draws=B, weights="Webb 6 điểm", clusters_main=G,
    crump_alpha=alpha_c, long_zones=int(gl.zone.nunique())), indent=2, default=float))
print("xong", round(time.time() - t0, 1))
