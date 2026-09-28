"""Bước 9 - Học máy nhân quả: Double/Debiased ML và tác động không đồng nhất.

Đơn vị: cặp vùng (điểm đón, điểm trả) có lưu lượng ổn định (panel OD bước 7).
Kết quả: thay đổi cùng kỳ ΔY = Y(2025) − Y(2024) cho từng cặp OD
  - dlog_n   : chênh lệch log tổng số chuyến cả năm
  - d_mph    : chênh lệch tốc độ trung bình
  - d_pay_pm : chênh lệch thu nhập tài xế/dặm
Xử lý: D = 1 nếu cặp OD chạm CRZ (điểm đón hoặc điểm trả trong CRZ).
Biến kiểm soát X: đặc trưng năm 2024 của cặp OD (quãng đường, thời lượng,
tốc độ, giá/dặm, log lưu lượng, tỷ trọng Uber, tỷ trọng chuyến đêm... ) và
quận của điểm đón/điểm trả. Không đưa khoảng cách tới CRZ vào X vì biến này
xác định gần như hoàn toàn D (vi phạm điều kiện chồng lấn).

Ước lượng:
  (1) PLR – mô hình tuyến tính từng phần (Chernozhukov và cộng sự, 2018),
      nuisance bằng LightGBM, cross-fitting 5 phần.
  (2) AIPW/DR – ước lượng bền vững kép, cắt xu hướng ở [0,05; 0,95].
  (3) CATE bằng DR-learner; kiểm định không đồng nhất bằng BLP và GATES
      (Chernozhukov, Demirer, Duflo, Fernández-Val).

Chạy:  python code/09_dml_heterogeneity.py
"""
import json
import time

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.model_selection import KFold

from config import GOLD, LOG, SEED, TAB
from panels import dim
from viz import C, fig, plt, save

t0 = time.time()
rng = np.random.default_rng(SEED)
o = pd.read_parquet(GOLD / "od_month.parquet")
o = o[o.service == "hvfhv"].copy()
dm = dim().set_index("LocationID")
o["pu_grp"], o["do_grp"] = o.pu.map(dm.grp), o.dl.map(dm.grp)
ok = ["CRZ", "MN_NORTH", "OUTER"]
o = o[o.pu_grp.isin(ok) & o.do_grp.isin(ok)]
o["yr"] = o.ym.str[:4].astype(int)
agg = o.groupby(["pu", "dl", "yr"])[["n", "fare", "pay", "miles", "time_s", "tips", "rider_cost"]].sum().unstack("yr")
agg = agg[(agg[("n", 2024)] >= 12 * 300) & (agg[("n", 2025)] > 0)]

# Đặc trưng 2024 bổ sung: tỷ trọng Uber và tỷ trọng giờ đêm từ mẫu chuyến
smp = pd.read_parquet(GOLD / "trip_sample.parquet", columns=["service", "d", "pu", "dl", "company_code", "hr"])
smp = smp[(smp.service == "hvfhv") & (pd.to_datetime(smp.d).dt.year == 2024)]
sf = smp.groupby(["pu", "dl"]).agg(uber_share=("company_code", lambda s: (s == "HV0003").mean()),
                                   night_share=("hr", lambda h: ((h <= 5) | (h >= 22)).mean()),
                                   n_sample=("hr", "size"))

df = pd.DataFrame(index=agg.index)
for yr in (2024, 2025):
    df[f"ln_n_{yr}"] = np.log(agg[("n", yr)])
    df[f"mph_{yr}"] = agg[("miles", yr)] / (agg[("time_s", yr)] / 3600)
    df[f"pay_pm_{yr}"] = agg[("pay", yr)] / agg[("miles", yr)]
    df[f"fare_pm_{yr}"] = agg[("fare", yr)] / agg[("miles", yr)]
df["dlog_n"] = df.ln_n_2025 - df.ln_n_2024
df["d_mph"] = df.mph_2025 - df.mph_2024
df["d_pay_pm"] = df.pay_pm_2025 - df.pay_pm_2024
df["miles_pt"] = agg[("miles", 2024)] / agg[("n", 2024)]
df["min_pt"] = agg[("time_s", 2024)] / agg[("n", 2024)] / 60
df["tips_pt"] = agg[("tips", 2024)] / agg[("n", 2024)]
df = df.reset_index()
df = df.merge(sf.reset_index(), on=["pu", "dl"], how="left")
df["pu_boro"] = df.pu.map(dm.Borough)
df["do_boro"] = df.dl.map(dm.Borough)
df["same_zone"] = (df.pu == df.dl).astype(int)
df["D"] = ((df.pu.map(dm.grp) == "CRZ") | (df.dl.map(dm.grp) == "CRZ")).astype(int)
df["ftype"] = np.select([(df.pu.map(dm.grp) == "CRZ") & (df.dl.map(dm.grp) == "CRZ"),
                         df.pu.map(dm.grp) == "CRZ", df.dl.map(dm.grp) == "CRZ"],
                        ["CRZ→CRZ", "CRZ→ngoài", "ngoài→CRZ"], "không chạm CRZ")
for b in ["Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"]:
    df[f"pu_{b[:3]}"] = (df.pu_boro == b).astype(int)
    df[f"do_{b[:3]}"] = (df.do_boro == b).astype(int)
BORO = [c for c in df.columns if c[:3] in ("pu_", "do_") and c[3:6] in ("Man", "Bro", "Que", "Sta")]
X_SETS = {
    # Bộ chính: chỉ đặc trưng của chuyến đi, không mã hóa trực tiếp vị trí
    "rút gọn": ["ln_n_2024", "miles_pt", "min_pt", "tips_pt", "uber_share", "night_share", "same_zone"],
    # Bộ đầy đủ: thêm tốc độ, giá/dặm, thu nhập/dặm và quận (vi phạm chồng lấn mạnh)
    "đầy đủ": ["ln_n_2024", "mph_2024", "fare_pm_2024", "pay_pm_2024", "miles_pt", "min_pt", "tips_pt",
               "uber_share", "night_share", "same_zone"] + BORO,
}
allx = sorted(set(sum(X_SETS.values(), [])))
df[allx] = df[allx].fillna(df[allx].median())
df.to_parquet(GOLD / "dml_od_dataset.parquet", index=False)
MAIN = "rút gọn"
X_COLS = X_SETS[MAIN]

X = df[X_COLS].to_numpy()
D = df.D.to_numpy()
K = 5
kf = KFold(K, shuffle=True, random_state=SEED)
params = dict(n_estimators=400, learning_rate=0.03, num_leaves=15, min_child_samples=40,
              subsample=0.8, subsample_freq=1, colsample_bytree=0.8, reg_lambda=1.0,
              random_state=SEED, verbose=-1, n_jobs=2)

# Xu hướng (propensity) – dùng chung cho mọi kết quả
e_hat = np.zeros(len(df))
for tr, te in kf.split(X):
    clf = lgb.LGBMClassifier(**params).fit(X[tr], D[tr])
    e_hat[te] = clf.predict_proba(X[te])[:, 1]
df["e_hat"] = e_hat
from sklearn.metrics import roc_auc_score
overlap = dict(auc_propensity=float(roc_auc_score(D, e_hat)),
               share_trimmed=float(((e_hat < 0.05) | (e_hat > 0.95)).mean()),
               n=int(len(df)), n_treated=int(D.sum()))

f, ax = fig(6.2, 3.0)
bins = np.linspace(0, 1, 41)
ax.hist(e_hat[D == 1], bins=bins, color=C["s1"], alpha=0.75, label="Cặp OD chạm CRZ")
ax.hist(e_hat[D == 0], bins=bins, color=C["s2"], alpha=0.6, label="Cặp OD không chạm CRZ")
for v in (0.05, 0.95):
    ax.axvline(v, color=C["text2"], lw=0.8, ls="--")
ax.set_xlabel("Xác suất ước lượng thuộc nhóm xử lý ê(X)")
ax.set_ylabel("Số cặp OD")
ax.set_title("Kiểm tra chồng lấn: phân phối điểm xu hướng (cross-fitted)")
ax.legend()
save(f, "f28_dml_overlap")

results, gates_all, blp_all, clan_all, imp_all, sens_rows = [], [], [], [], [], []
keep = (e_hat >= 0.05) & (e_hat <= 0.95)
for yname, ylab in (("dlog_n", "Δ log số chuyến"), ("d_mph", "Δ tốc độ (dặm/giờ)"), ("d_pay_pm", "Δ thu nhập tài xế/dặm")):
    Y = df[yname].to_numpy()
    g_hat = np.zeros(len(df))
    mu1 = np.zeros(len(df))
    mu0 = np.zeros(len(df))
    for tr, te in kf.split(X):
        g_hat[te] = lgb.LGBMRegressor(**params).fit(X[tr], Y[tr]).predict(X[te])
        t1, t0_ = tr[D[tr] == 1], tr[D[tr] == 0]
        mu1[te] = lgb.LGBMRegressor(**params).fit(X[t1], Y[t1]).predict(X[te])
        mu0[te] = lgb.LGBMRegressor(**params).fit(X[t0_], Y[t0_]).predict(X[te])
    # (1) PLR
    yr_, dr_ = Y - g_hat, D - e_hat
    theta = np.sum(dr_ * yr_) / np.sum(dr_ ** 2)
    psi = (yr_ - theta * dr_) * dr_
    se_plr = np.sqrt(np.mean(psi ** 2) / np.mean(dr_ ** 2) ** 2 / len(Y))
    # (2) AIPW trên vùng chồng lấn
    ec = np.clip(e_hat, 0.05, 0.95)
    phi = mu1 - mu0 + D * (Y - mu1) / ec - (1 - D) * (Y - mu0) / (1 - ec)
    ate = phi[keep].mean()
    se_ate = phi[keep].std(ddof=1) / np.sqrt(keep.sum())
    att_w = D[keep] / D[keep].mean()
    att = np.mean(att_w * (Y[keep] - mu0[keep]) - (1 - D[keep]) * ec[keep] / (1 - ec[keep]) * (Y[keep] - mu0[keep]) / D[keep].mean())
    naive = Y[D == 1].mean() - Y[D == 0].mean()
    # (3) DR-learner cho CATE (cross-fit lần 2)
    tau = np.zeros(len(df))
    Xk, phik = X[keep], phi[keep]
    idx_keep = np.where(keep)[0]
    imp = np.zeros(len(X_COLS))
    for tr, te in KFold(K, shuffle=True, random_state=SEED + 1).split(Xk):
        mdl = lgb.LGBMRegressor(**{**params, "n_estimators": 300, "num_leaves": 7, "min_child_samples": 80}).fit(Xk[tr], phik[tr])
        tau[idx_keep[te]] = mdl.predict(Xk[te])
        imp += mdl.booster_.feature_importance("gain")
    imp_all.append(pd.DataFrame(dict(outcome=yname, feature=X_COLS, gain=imp / imp.sum())))
    tk = tau[keep]
    # BLP: phi = b1 + b2 (tau - mean tau)
    Z = np.c_[np.ones(keep.sum()), tk - tk.mean()]
    b = np.linalg.lstsq(Z, phik, rcond=None)[0]
    res_ = phik - Z @ b
    Vb = np.linalg.inv(Z.T @ Z) @ (Z.T * res_ ** 2) @ Z @ np.linalg.inv(Z.T @ Z)
    blp_all.append(dict(outcome=yname, beta1=b[0], se1=np.sqrt(Vb[0, 0]), beta2=b[1], se2=np.sqrt(Vb[1, 1]),
                        t2=b[1] / np.sqrt(Vb[1, 1])))
    # GATES theo ngũ phân vị của tau
    qg = pd.qcut(tk, 5, labels=False, duplicates="drop")
    for gidx in sorted(np.unique(qg)):
        sel = qg == gidx
        gates_all.append(dict(outcome=yname, group=int(gidx) + 1, n=int(sel.sum()), gate=phik[sel].mean(),
                              se=phik[sel].std(ddof=1) / np.sqrt(sel.sum()), tau_mean=tk[sel].mean()))
    # CLAN: đặc trưng trung bình ở nhóm tác động thấp nhất và cao nhất
    lo_, hi_ = qg == qg.min(), qg == qg.max()
    dk = df.loc[keep].reset_index(drop=True)
    for c in ["miles_pt", "min_pt", "mph_2024", "fare_pm_2024", "ln_n_2024", "uber_share", "night_share", "D"]:
        clan_all.append(dict(outcome=yname, feature=c, low_group=dk.loc[lo_, c].mean(), high_group=dk.loc[hi_, c].mean()))
    df[f"tau_{yname}"] = tau
    df.loc[~keep, f"tau_{yname}"] = np.nan
    results.append(dict(outcome=yname, outcome_label=ylab, naive_diff=naive, plr_theta=theta, plr_se=se_plr,
                        aipw_ate=ate, aipw_se=se_ate, aipw_att=att, n_used=int(keep.sum()),
                        r2_g=1 - np.mean((Y - g_hat) ** 2) / np.var(Y)))
    print(results[-1], flush=True)

# Độ nhạy: bộ biến đầy đủ (chỉ ước lượng ATE, kèm chẩn đoán chồng lấn)
for xs_name, xs in X_SETS.items():
    Xs_ = df[xs].to_numpy()
    e2 = np.zeros(len(df))
    for tr, te in kf.split(Xs_):
        e2[te] = lgb.LGBMClassifier(**params).fit(Xs_[tr], D[tr]).predict_proba(Xs_[te])[:, 1]
    keep2 = (e2 >= 0.05) & (e2 <= 0.95)
    for yname in ("dlog_n", "d_mph", "d_pay_pm"):
        Y = df[yname].to_numpy()
        g2, m1, m0 = np.zeros(len(df)), np.zeros(len(df)), np.zeros(len(df))
        for tr, te in kf.split(Xs_):
            g2[te] = lgb.LGBMRegressor(**params).fit(Xs_[tr], Y[tr]).predict(Xs_[te])
            t1, t0_ = tr[D[tr] == 1], tr[D[tr] == 0]
            m1[te] = lgb.LGBMRegressor(**params).fit(Xs_[t1], Y[t1]).predict(Xs_[te])
            m0[te] = lgb.LGBMRegressor(**params).fit(Xs_[t0_], Y[t0_]).predict(Xs_[te])
        yr_, dr_ = Y - g2, D - e2
        th = np.sum(dr_ * yr_) / np.sum(dr_ ** 2)
        ps = (yr_ - th * dr_) * dr_
        se_ = np.sqrt(np.mean(ps ** 2) / np.mean(dr_ ** 2) ** 2 / len(Y))
        ec2 = np.clip(e2, 0.05, 0.95)
        ph = m1 - m0 + D * (Y - m1) / ec2 - (1 - D) * (Y - m0) / (1 - ec2)
        sens_rows.append(dict(x_set=xs_name, n_features=len(xs), outcome=yname, auc_propensity=roc_auc_score(D, e2),
                              share_in_overlap=keep2.mean(), n_overlap=int(keep2.sum()),
                              n_treated_overlap=int(D[keep2].sum()), plr_theta=th, plr_se=se_,
                              aipw_ate=ph[keep2].mean(), aipw_se=ph[keep2].std(ddof=1) / np.sqrt(keep2.sum())))
pd.DataFrame(sens_rows).to_csv(TAB / "t41b_dml_sensitivity_xsets.csv", index=False)
pd.DataFrame(results).to_csv(TAB / "t41_dml_ate.csv", index=False)
pd.DataFrame(blp_all).to_csv(TAB / "t42_dml_blp.csv", index=False)
gates = pd.DataFrame(gates_all)
gates.to_csv(TAB / "t43_dml_gates.csv", index=False)
pd.DataFrame(clan_all).to_csv(TAB / "t44_dml_clan.csv", index=False)
pd.concat(imp_all).to_csv(TAB / "t45_dml_cate_importance.csv", index=False)
df.to_parquet(GOLD / "dml_od_dataset.parquet", index=False)

f, axs = fig(6.8, 3.0, ncols=3)
for ax, (y, ttl, sc) in zip(axs, (("dlog_n", "Δ log số chuyến ×100", 100), ("d_mph", "Δ tốc độ (dặm/giờ)", 1),
                                  ("d_pay_pm", "Δ thu nhập/dặm (USD)", 1))):
    g = gates[gates.outcome == y]
    ax.bar(g.group, sc * g.gate, color=C["s1"], width=0.6)
    ax.errorbar(g.group, sc * g.gate, yerr=sc * 1.96 * g.se, fmt="none", ecolor=C["text2"], elinewidth=1)
    ax.axhline(0, color=C["text2"], lw=0.8)
    ax.set_title(ttl, fontsize=9)
    ax.set_xlabel("Nhóm theo τ̂ (1 thấp → 5 cao)")
f.suptitle("GATES: tác động trung bình theo nhóm ngũ phân vị của CATE ước lượng", x=0.02, ha="left",
           fontsize=10.5, fontweight="bold")
f.tight_layout()
save(f, "f29_dml_gates")

# CATE theo quãng đường chuyến và theo loại luồng
dk = df[keep].copy()
dk["dist_bin"] = pd.qcut(dk.miles_pt, 8)
cb = dk[dk.D == 1].groupby("dist_bin", observed=True).agg(tau=("tau_dlog_n", "mean"), miles=("miles_pt", "mean"), n=("pu", "size"))
cb.to_csv(TAB / "t46_cate_by_distance.csv")
ft = dk.groupby("ftype").agg(tau_dlog_n=("tau_dlog_n", "mean"), tau_d_mph=("tau_d_mph", "mean"),
                             tau_d_pay_pm=("tau_d_pay_pm", "mean"), n=("pu", "size"))
ft.to_csv(TAB / "t47_cate_by_flowtype.csv")
f, ax = fig(6.2, 3.0)
ax.plot(cb.miles, 100 * cb.tau, color=C["s1"], marker="o")
ax.axhline(0, color=C["text2"], lw=0.8)
ax.set_xlabel("Quãng đường trung bình của cặp OD năm 2024 (dặm)")
ax.set_ylabel("τ̂ log số chuyến ×100")
ax.set_title("CATE ước lượng theo quãng đường chuyến (cặp OD chạm CRZ)")
save(f, "f30_cate_by_distance")

imp = pd.concat(imp_all)
f, ax = fig(6.2, 3.4)
ii = imp[imp.outcome == "dlog_n"].sort_values("gain").tail(10)
ax.barh(ii.feature, ii.gain, color=C["s1"])
ax.set_xlabel("Tỷ trọng gain trong mô hình CATE")
ax.set_title("Đặc trưng giải thích sự khác biệt tác động (Δ log số chuyến)")
save(f, "f31_cate_importance")

(LOG / "09_dml.json").write_text(json.dumps(dict(seconds=round(time.time() - t0, 1), overlap=overlap, x_sets=X_SETS, main=MAIN), indent=2, default=float))
print(overlap, "time", round(time.time() - t0, 1))
