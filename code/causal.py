"""Thư viện ước lượng nhân quả dùng chung (tự cài đặt, minh bạch từng bước).

- demean_fe: khử nhiều hiệu ứng cố định bằng phép chiếu luân phiên
  (alternating projections, còn gọi là thuật toán Guimarães–Portugal /
  "within" nhiều chiều), có hỗ trợ trọng số.
- fe_ols: hồi quy OLS sau khi khử hiệu ứng cố định, sai số chuẩn phân cụm
  (CR1, hiệu chỉnh bậc tự do kiểu Stata).
- event_study: hệ số động theo thời gian tương đối so với mốc chính sách.
"""
import numpy as np
import pandas as pd


def demean_fe(df, cols, fes, w=None, tol=1e-10, max_iter=500):
    """Khử trung bình theo nhiều nhóm hiệu ứng cố định cho các cột `cols`."""
    X = df[cols].to_numpy(dtype=float).copy()
    ww = np.ones(len(df)) if w is None else np.asarray(w, dtype=float)
    codes = [pd.factorize(df[f])[0] for f in fes]
    sizes = [c.max() + 1 for c in codes]
    wsum = [np.bincount(c, weights=ww, minlength=s) for c, s in zip(codes, sizes)]
    for it in range(max_iter):
        X_old = X.copy()
        for c, s, ws in zip(codes, sizes, wsum):
            for j in range(X.shape[1]):
                m = np.bincount(c, weights=ww * X[:, j], minlength=s) / np.where(ws > 0, ws, 1)
                X[:, j] -= m[c]
        if np.max(np.abs(X - X_old)) < tol:
            break
    return X, it + 1


def fe_ols(df, y, xs, fes, cluster, w=None):
    """OLS với hiệu ứng cố định `fes`, sai số chuẩn phân cụm theo `cluster`.

    Trả về DataFrame hệ số (coef, se, t, p, ci_low, ci_high) và thông tin mô hình.
    """
    from scipy import stats
    d = df.dropna(subset=[y] + xs).reset_index(drop=True)
    ww = None if w is None else d[w].to_numpy(dtype=float)
    Z, n_iter = demean_fe(d, [y] + xs, fes, ww)
    yt, Xt = Z[:, 0], Z[:, 1:]
    sw = np.ones(len(d)) if ww is None else np.sqrt(ww)
    Xs, ys = Xt * sw[:, None], yt * sw
    XtX = Xs.T @ Xs
    XtX_inv = np.linalg.pinv(XtX)
    b = XtX_inv @ (Xs.T @ ys)
    e = ys - Xs @ b
    g = pd.factorize(d[cluster])[0]
    G = g.max() + 1
    scores = np.zeros((G, Xs.shape[1]))
    np.add.at(scores, g, Xs * e[:, None])
    meat = scores.T @ scores
    n, k = Xs.shape
    k_fe = sum(d[f].nunique() for f in fes) - (len(fes) - 1)
    adj = G / (G - 1) * (n - 1) / max(n - k - k_fe, 1)
    V = adj * XtX_inv @ meat @ XtX_inv
    se = np.sqrt(np.clip(np.diag(V), 0, None))
    tval = b / np.where(se > 0, se, np.nan)
    p = 2 * stats.t.sf(np.abs(tval), df=G - 1)
    crit = stats.t.ppf(0.975, df=G - 1)
    res = pd.DataFrame(dict(term=xs, coef=b, se=se, t=tval, p=p,
                            ci_low=b - crit * se, ci_high=b + crit * se))
    ss_res = float(e @ e)
    ss_tot = float(ys @ ys)
    info = dict(n_obs=int(n), n_clusters=int(G), n_fe_levels=int(k_fe),
                within_r2=1 - ss_res / ss_tot if ss_tot > 0 else np.nan, demean_iter=int(n_iter))
    return res, info, V


def event_study(df, y, treat, rel, fes, cluster, ref=-1, lo=None, hi=None, w=None):
    """Hệ số động: y = FE + sum_k beta_k * treat * 1[rel == k] (bỏ mốc ref).

    Các kỳ ngoài [lo, hi] được gộp vào hai đầu mút (binning)."""
    d = df.copy()
    r = d[rel].clip(lower=lo, upper=hi) if lo is not None else d[rel]
    ks = sorted(k for k in r.unique() if k != ref)
    names = []
    for k in ks:
        nm = f"ev_{'m' if k < 0 else 'p'}{abs(int(k))}"
        d[nm] = ((r == k) & (d[treat] == 1)).astype(float)
        names.append(nm)
    res, info, V = fe_ols(d, y, names, fes, cluster, w)
    res["k"] = ks
    # Chuẩn hóa lại mốc so sánh: trừ trung bình của TOÀN BỘ các kỳ trước chính sách
    # (kể cả kỳ ref có hệ số 0). Phép biến đổi tuyến tính L áp dụng cho cả hệ số và
    # ma trận hiệp phương sai, nên sai số chuẩn được tính lại đúng.
    kk = np.array(ks)
    n_pre = int((kk < 0).sum()) + (1 if ref < 0 else 0)
    a = np.where(kk < 0, 1.0 / n_pre, 0.0)
    L = np.eye(len(ks)) - np.ones((len(ks), 1)) @ a[None, :]
    bc = L @ res.coef.to_numpy()
    Vc = L @ V @ L.T
    sc = np.sqrt(np.clip(np.diag(Vc), 0, None))
    from scipy import stats
    crit = stats.t.ppf(0.975, df=info["n_clusters"] - 1)
    res["coef_c"], res["se_c"] = bc, sc
    res["ci_low_c"], res["ci_high_c"] = bc - crit * sc, bc + crit * sc
    return res, info, V


def _center_matrix(ks, ref=-1):
    kk = np.array(ks)
    n_pre = int((kk < 0).sum()) + (1 if ref < 0 else 0)
    a = np.where(kk < 0, 1.0 / n_pre, 0.0)
    return np.eye(len(ks)) - np.ones((len(ks), 1)) @ a[None, :]


def pretrend_wald_centered(res, V, ref=-1):
    """Kiểm định Wald: mọi hệ số trước chính sách (đã chuẩn hóa theo trung bình kỳ trước) bằng nhau,
    tức là không có biến động có hệ thống trước chính sách quanh mức trung bình."""
    from scipy import stats
    L = _center_matrix(list(res.k), ref)
    Vc = L @ V @ L.T
    idx = np.where(res.k.to_numpy() < 0)[0]
    b = res.coef_c.to_numpy()[idx]
    Vs = Vc[np.ix_(idx, idx)]
    wald = float(b @ np.linalg.pinv(Vs) @ b)
    dof = int(np.linalg.matrix_rank(Vs))
    return dict(wald=wald, dof=dof, p=float(stats.chi2.sf(wald, dof)))


def pretrend_wald(res, V, upto=-2):
    """Kiểm định Wald chung: mọi hệ số trước chính sách (k <= upto) bằng 0."""
    from scipy import stats
    idx = np.where(res.k.to_numpy() <= upto)[0]
    if len(idx) == 0:
        return dict(wald=np.nan, dof=0, p=np.nan)
    b = res.coef.to_numpy()[idx]
    Vs = V[np.ix_(idx, idx)]
    wald = float(b @ np.linalg.pinv(Vs) @ b)
    return dict(wald=wald, dof=int(len(idx)), p=float(stats.chi2.sf(wald, len(idx))))
