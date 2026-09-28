"""Bước 8 - Kiểm soát tổng hợp (Synthetic Control) cho tổng số chuyến đón trong CRZ.

Chuỗi xử lý: tổng số chuyến HVFHV đón trong 38 vùng CRZ theo tuần, chuẩn hóa
bằng trung bình năm 2024 (chỉ số = 1). Nguồn đối chứng (donor pool): các vùng
đối chứng của panel chính, chuẩn hóa tương tự.
Trọng số w >= 0, tổng bằng 1, được chọn để khớp 52 tuần năm 2024.
Hai biến thể: SCM chuẩn (Abadie và cộng sự) và SCM khử trung bình
(cho phép chênh lệch mức cố định, Ferman & Pinto).
Suy diễn: kiểm định giả dược theo không gian (lần lượt coi từng vùng đối
chứng là "vùng xử lý"), so sánh tỷ số RMSPE sau/trước.

Chạy:  python code/08_synthetic_control.py
"""
import json
import time

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from config import LOG, TAB
from panels import P, zone_week
from viz import C, fig, plt, policy_line, save

t0 = time.time()
zw = zone_week("hvfhv")
W = zw.pivot_table(index="wk", columns="zone", values="n", aggfunc="sum")
treated_z = sorted(zw[zw.treat == 1].zone.unique())
donors = sorted(zw[zw.treat == 0].zone.unique())
pre = W.index < P
yT = W[treated_z].sum(axis=1)
yT = yT / yT[pre].mean()
Y0 = W[donors] / W[donors][pre].mean()


def fit_w(y, X, demean=False):
    yp, Xp = y[pre].to_numpy(), X[pre].to_numpy()
    if demean:
        yp = yp - yp.mean()
        Xp = Xp - Xp.mean(axis=0)
    J = Xp.shape[1]
    obj = lambda w: np.sum((yp - Xp @ w) ** 2)
    jac = lambda w: -2 * Xp.T @ (yp - Xp @ w)
    cons = ({"type": "eq", "fun": lambda w: w.sum() - 1, "jac": lambda w: np.ones(J)},)
    r = minimize(obj, np.full(J, 1 / J), jac=jac, bounds=[(0, 1)] * J, constraints=cons,
                 method="SLSQP", options=dict(maxiter=500, ftol=1e-12))
    w = np.clip(r.x, 0, None)
    w = w / w.sum()
    synth = X.to_numpy() @ w
    if demean:
        synth = synth + (y[pre].mean() - (X[pre].to_numpy() @ w).mean())
    return w, pd.Series(synth, index=y.index)


out = {}
res = {}
for demean in (False, True):
    w, s = fit_w(yT, Y0, demean)
    gap = yT - s
    rm_pre = float(np.sqrt(np.mean(gap[pre] ** 2)))
    rm_post = float(np.sqrt(np.mean(gap[~pre] ** 2)))
    key = "demeaned" if demean else "standard"
    res[key] = (w, s, gap)
    out[key] = dict(rmspe_pre=rm_pre, rmspe_post=rm_post, ratio=rm_post / rm_pre,
                    avg_gap_post=float(gap[~pre].mean()),
                    avg_pct_effect_post=float(100 * (yT[~pre] / s[~pre] - 1).mean()),
                    n_donors_positive=int((w > 1e-3).sum()))
    wt = pd.DataFrame(dict(zone=donors, weight=w)).sort_values("weight", ascending=False)
    wt = wt.merge(zw[["zone", "Zone", "Borough", "grp"]].drop_duplicates(), on="zone")
    wt.to_csv(TAB / f"t38_scm_weights_{key}.csv", index=False)

pd.DataFrame({"week": W.index, "treated_index": yT.values, "synth_standard": res["standard"][1].values,
              "synth_demeaned": res["demeaned"][1].values}).to_csv(TAB / "t39_scm_series.csv", index=False)

f, axs = plt.subplots(2, 1, figsize=(6.8, 5.4), sharex=True)
axs[0].plot(yT.index, yT, color=C["s1"], label="CRZ thực tế")
axs[0].plot(yT.index, res["standard"][1], color=C["s2"], label="CRZ tổng hợp (SCM chuẩn)")
policy_line(axs[0], P)
axs[0].set_ylabel("Chỉ số (TB 2024 = 1)")
axs[0].set_title("Kiểm soát tổng hợp: số chuyến HVFHV đón trong CRZ theo tuần")
axs[0].legend(loc="lower left", fontsize=8)
axs[1].plot(yT.index, 100 * res["standard"][2], color=C["s2"], label="SCM chuẩn")
axs[1].axhline(0, color=C["text2"], lw=0.8)
policy_line(axs[1], P, "")
axs[1].set_ylabel("Khoảng cách ×100")
axs[1].set_title("Khoảng cách giữa CRZ thực tế và CRZ tổng hợp")
axs[1].legend(loc="lower left", fontsize=8)
f.tight_layout()
save(f, "f25_scm_fit_gap")

# ----- Giả dược theo không gian -----
vol = W[donors][pre].mean().sort_values(ascending=False)
plac_units = vol.index[:60]
pl_rows, gaps = [], {}
for u in plac_units:
    y = Y0[u]
    others = [d for d in donors if d != u]
    w, s = fit_w(y, Y0[others], demean=True)
    g = y - s
    rp, rq = np.sqrt(np.mean(g[pre] ** 2)), np.sqrt(np.mean(g[~pre] ** 2))
    pl_rows.append(dict(zone=u, rmspe_pre=rp, rmspe_post=rq, ratio=rq / rp, avg_gap_post=g[~pre].mean()))
    gaps[u] = g
pl = pd.DataFrame(pl_rows)
tr_ratio = out["demeaned"]["ratio"]
out["placebo_n"] = int(len(pl))
out["placebo_rank_p"] = float((1 + (pl.ratio >= tr_ratio).sum()) / (1 + len(pl)))
out["placebo_gap_p"] = float((1 + (pl.avg_gap_post.abs() >= abs(out["demeaned"]["avg_gap_post"])).sum()) / (1 + len(pl)))
pl = pl.merge(zw[["zone", "Zone", "Borough", "grp"]].drop_duplicates(), on="zone")
pl.to_csv(TAB / "t40_scm_placebo.csv", index=False)

f, ax = fig(6.8, 3.4)
for u, g in gaps.items():
    ax.plot(g.index, 100 * g, color=C["neutral"], lw=0.7)
ax.plot(yT.index, 100 * res["demeaned"][2], color=C["s1"], lw=2.2, label="CRZ")
ax.plot([], [], color=C["neutral"], lw=0.7, label=f"{len(gaps)} vùng giả dược")
ax.axhline(0, color=C["text2"], lw=0.8)
policy_line(ax, P)
ax.set_ylim(-60, 60)
ax.set_ylabel("Khoảng cách ×100")
ax.set_title("Giả dược theo không gian: khoảng cách SCM của CRZ và của các vùng đối chứng")
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=2)
save(f, "f26_scm_placebo")

f, ax = fig(6.0, 3.0)
ax.hist(pl.ratio, bins=25, color=C["neutral"], edgecolor="white")
ax.axvline(tr_ratio, color=C["s1"], lw=2)
ax.annotate(f"CRZ: {tr_ratio:.2f}", (tr_ratio, ax.get_ylim()[1] * 0.9), xytext=(5, 0),
            textcoords="offset points", color=C["text"])
ax.set_xlabel("Tỷ số RMSPE sau / trước")
ax.set_ylabel("Số vùng")
ax.set_title("Phân phối tỷ số RMSPE của các vùng giả dược")
save(f, "f27_scm_rmspe_ratio")

(LOG / "08_scm.json").write_text(json.dumps(dict(seconds=round(time.time() - t0, 1), **out), indent=2, default=float))
print(json.dumps(out, indent=1, default=float))
