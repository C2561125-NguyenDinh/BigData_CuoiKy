"""Bước 16 - Quản trị dữ liệu, rủi ro và bảo mật trên chính tài sản dữ liệu của đồ án.

Các phần (mỗi phần ghi bảng vào outputs/tables và nhật ký vào outputs/logs/governance/):
  catalog          Danh mục dữ liệu (data catalog): mọi tập dữ liệu ở ba lớp, số dòng, số cột,
                   dung lượng, dấu vân tay lược đồ, khoảng thời gian.                      -> t68
  lineage          Phả hệ dữ liệu (lineage) trích tự động từ mã nguồn: bước nào đọc/ghi gì. -> t69, f47
  integrity [giây] Chuỗi cung ứng dữ liệu: băm SHA-256 mọi tệp Bronze (tăng dần, lũy đẳng). -> t70
  reconcile        Đối soát số dòng Bronze = Silver + bị loại, và Silver = metadata Parquet.   -> t71
  anomaly          Phát hiện bất thường theo ngày (z-score bền vững theo thứ trong tuần) và
                   biểu đồ kiểm soát tỷ lệ loại bỏ theo tháng (p-chart).                   -> t72, f48, f49
  tripanom         Phát hiện chuyến bất thường trên mẫu chuyến (Isolation Forest + quy tắc). -> t73, f50
  privacy          Rủi ro tái nhận dạng: k-ẩn danh theo các tổ hợp định danh gián tiếp.   -> t74, f51
  dp               Quyền riêng tư vi phân: nhiễu Laplace lên số chuyến công bố và ảnh hưởng
                   đến ước lượng DiD chính (đánh đổi riêng tư – hữu dụng).                -> t75, f52
  dr               Phục hồi sau sự cố: thời gian dựng lại từng lớp đo từ nhật ký (RTO).       -> t76
Chạy:  python code/16_governance_risk.py <phần>
"""
import hashlib
import json
import re
import sys
import time

import numpy as np
import pandas as pd

from config import GOLD, LOG, MONTHS, RAW, ROOT, SEED, SERVICES, SILVER, TAB, duck

GLOG = LOG / "governance"
GLOG.mkdir(parents=True, exist_ok=True)
CODE = ROOT / "code"


def wlog(name, rec):
    (GLOG / f"{name}.json").write_text(json.dumps(rec, indent=2, ensure_ascii=False, default=str))
    print(json.dumps(rec, ensure_ascii=False, default=str)[:800], flush=True)


# ------------------------------------------------------------------ catalog
def part_catalog():
    import pyarrow.parquet as pq
    rows = []

    def add(layer, name, files, owner):
        files = [f for f in files if f.exists()]
        if not files:
            return
        md = [pq.ParquetFile(f).metadata for f in files]
        sch = pq.ParquetFile(files[0]).schema_arrow
        fp = hashlib.md5(";".join(f"{f.name}:{f.type}" for f in sch).encode()).hexdigest()[:10]
        rows.append(dict(layer=layer, dataset=name, files=len(files), rows=sum(m.num_rows for m in md),
                         columns=len(sch), row_groups=sum(m.num_row_groups for m in md),
                         size_mb=round(sum(f.stat().st_size for f in files) / 2**20, 1),
                         schema_fp=fp, producer=owner))

    for svc, pre in (("hvfhv", "fhvhv"), ("yellow", "yellow")):
        for y in ("2024", "2025"):
            add("Bronze", f"{pre}_tripdata_{y}-*", sorted(RAW.glob(f"{pre}_tripdata_{y}-*.parquet")), "NYC TLC")
            add("Silver", f"service={svc}/year={y}", sorted((SILVER / f"service={svc}" / f"year={y}").rglob("*.parquet")),
                "03_silver_gold_month.py")
    for f in sorted(GOLD.glob("*.parquet")):
        add("Gold", f.stem, [f], "02/04/09")
    t = pd.DataFrame(rows)
    # Lệch lược đồ giữa các tệp cùng tập dữ liệu (số dấu vân tay khác nhau)
    drift = []
    for (layer, pre) in (("Bronze", "fhvhv"), ("Bronze", "yellow")):
        fps = {}
        for f in sorted(RAW.glob(f"{pre}_tripdata_*.parquet")):
            s = pq.ParquetFile(f).schema_arrow
            fps.setdefault(hashlib.md5(";".join(f"{x.name}:{x.type}" for x in s).encode()).hexdigest()[:10],
                           []).append(f.stem[-7:])
        drift.append(dict(layer=layer, source=pre, distinct_schemas=len(fps),
                          schemas={k: f"{v[0]}..{v[-1]} ({len(v)} tệp)" for k, v in fps.items()}))
    t.to_csv(TAB / "t68_data_catalog.csv", index=False)
    pd.DataFrame(drift).to_csv(TAB / "t68b_schema_fingerprints.csv", index=False)
    wlog("catalog", dict(datasets=len(t), total_rows=int(t.rows.sum()), total_mb=float(t.size_mb.sum()),
                         drift=drift))


# ------------------------------------------------------------------ lineage
def part_lineage():
    """Trích phả hệ từ mã: tên bảng Gold, tệp bảng (tNN) và hình (fNN) mà mỗi bước đọc hoặc ghi."""
    gold_names = sorted({p.stem for p in GOLD.glob("*.parquet")} | {"zone_adjacency"})
    steps = sorted(p for p in CODE.glob("[0-9][0-9]_*.py"))
    helpers = {"panels.py": (CODE / "panels.py").read_text(encoding="utf-8")}
    edges = []
    for p in steps:
        src = p.read_text(encoding="utf-8")
        name = p.stem
        # Bảng/hình được ghi
        w_tab = sorted(set(re.findall(r'TAB\s*/\s*f?"(t\d+[a-z]?_[^"{]+|a\d+_[^"{]+)', src)))
        w_fig = sorted(set(re.findall(r'save\(\s*f\s*,\s*f?"(f\d+[a-z]?_[^"{]+)"', src)))
        uses_panels = "from panels import" in src
        read_gold = [g for g in gold_names if re.search(rf"\b{g}\b", src) or (uses_panels and re.search(rf"\b{g}\b", helpers["panels.py"]))]
        writes_gold = []
        if name.startswith("02_"):
            writes_gold = ["dim_zone", "zone_adjacency", "zone_polygons"]
        elif name.startswith("04_"):
            writes_gold = [g for g in gold_names if g not in ("dim_zone", "zone_adjacency", "zone_polygons", "dml_od_dataset")]
        elif name.startswith("09_"):
            writes_gold = ["dml_od_dataset"]
        reads = [g for g in read_gold if g not in writes_gold]
        edges.append(dict(step=name, reads_gold=";".join(reads), writes_gold=";".join(writes_gold),
                          reads_raw=int("raw_file(" in src or "RAW" in src),
                          reads_silver=int("SILVER" in src or "silver_file(" in src or "month_dir(" in src),
                          writes_silver=int(name.startswith("03_")),
                          n_tables=len(w_tab), n_figures=len(w_fig),
                          tables=";".join(w_tab), figures=";".join(w_fig)))
    t = pd.DataFrame(edges)
    t.to_csv(TAB / "t69_lineage.csv", index=False)

    # Hình phả hệ: các cột Bronze → Silver → Gold → bước phân tích → sản phẩm
    from viz import C, fig, save
    f, ax = fig(7.0, 6.2)
    ax.axis("off")
    ax.set_xlim(0, 100)
    ana = [r for r in edges if r["n_tables"] + r["n_figures"] > 0 and not r["step"].startswith(("13_",))]
    n = len(ana)
    ys = np.linspace(95, 5, n)
    gold_y = {g: y for g, y in zip(gold_names, np.linspace(90, 10, len(gold_names)))}
    ax.set_ylim(0, 100)

    def node(x, y, txt, col, w=15, fs=6.2):
        ax.text(x, y, txt, ha="center", va="center", fontsize=fs, color=C["text"],
                bbox=dict(boxstyle="round,pad=0.3", fc=col, ec=C["text2"], lw=0.5), zorder=3)

    node(6, 50, "Bronze\n48 tệp chuyến\n+ bảng vùng", "#e4d6c3")
    node(22, 50, "Silver\n120 tệp\nservice/year/month", "#d9dde3")
    for g, y in gold_y.items():
        node(44, y, g, "#f3e2a6", fs=5.8)
        ax.annotate("", xy=(40, y), xytext=(26.5, 50), arrowprops=dict(arrowstyle="-", color=C["grid"], lw=0.6))
    ax.annotate("", xy=(18, 50), xytext=(10, 50), arrowprops=dict(arrowstyle="->", color=C["text2"]))
    for r, y in zip(ana, ys):
        lab = r["step"].split("_", 1)[0] + " " + r["step"].split("_", 1)[1][:18]
        node(72, y, lab, "#eef3fb", fs=5.8)
        node(93, y, f"{r['n_tables']} bảng · {r['n_figures']} hình", "#ffffff", fs=5.6)
        for g in r["reads_gold"].split(";"):
            if g in gold_y:
                ax.annotate("", xy=(65, y), xytext=(48.5, gold_y[g]),
                            arrowprops=dict(arrowstyle="-", color=C["s1"], lw=0.45, alpha=0.6))
        if r["reads_silver"] or r["reads_raw"]:
            ax.annotate("", xy=(65, y), xytext=(26.5, 50),
                        arrowprops=dict(arrowstyle="-", color=C["s2"], lw=0.45, alpha=0.6))
        ax.annotate("", xy=(86, y), xytext=(79, y), arrowprops=dict(arrowstyle="->", color=C["text2"], lw=0.5))
    ax.set_title("Phả hệ dữ liệu trích tự động từ mã nguồn", loc="left")
    save(f, "f47_lineage")
    wlog("lineage", dict(steps=len(edges), tables=int(t.n_tables.sum()), figures=int(t.n_figures.sum())))


# ------------------------------------------------------------------ integrity
def part_integrity(budget):
    t0 = time.time()
    man = GLOG / "sha256_manifest.json"
    done = json.loads(man.read_text()) if man.exists() else {}
    files = sorted(RAW.glob("*.parquet")) + sorted(RAW.glob("*.csv")) + sorted(RAW.glob("*.zip"))
    for f in files:
        if f.name in done and done[f.name]["bytes"] == f.stat().st_size:
            continue
        if time.time() - t0 > budget:
            break
        t = time.perf_counter()
        h = hashlib.sha256()
        with open(f, "rb") as fh:
            for chunk in iter(lambda: fh.read(8 << 20), b""):
                h.update(chunk)
        el = time.perf_counter() - t
        done[f.name] = dict(sha256=h.hexdigest(), bytes=f.stat().st_size, seconds=round(el, 2))
        man.write_text(json.dumps(done, indent=1))
    left = [f.name for f in files if f.name not in done]
    print("integrity: đã băm", len(done), "tệp; còn", len(left))
    if not left:
        t = pd.DataFrame([dict(file=k, **v) for k, v in done.items()]).sort_values("file")
        t["mb_per_s"] = t.bytes / 2**20 / t.seconds.replace(0, np.nan)
        t.to_csv(TAB / "t70_sha256_manifest.csv", index=False)
        # Kiểm tra lại (xác minh) ngẫu nhiên 3 tệp: băm lại và so khớp
        rng = np.random.default_rng(SEED)
        chk = []
        for name in rng.choice(t.file.values, 3, replace=False):
            h = hashlib.sha256()
            with open(RAW / name, "rb") as fh:
                for chunk in iter(lambda: fh.read(8 << 20), b""):
                    h.update(chunk)
            chk.append(dict(file=name, match=h.hexdigest() == done[name]["sha256"]))
        wlog("integrity", dict(files=len(t), total_gb=round(t.bytes.sum() / 2**30, 2),
                               seconds=round(t.seconds.sum(), 1),
                               throughput_mb_s=round(t.bytes.sum() / 2**20 / t.seconds.sum(), 1),
                               reverify=chk))


# ------------------------------------------------------------------ reconcile
def part_reconcile():
    import pyarrow.parquet as pq
    q = pd.read_csv(TAB / "t06_quality_by_month.csv")
    man = pd.read_csv(TAB / "t01_bronze_manifest.csv")
    rows = []
    for _, r in q.iterrows():
        y, m = r.month.split("-")
        sd = SILVER / f"service={r.service}" / f"year={y}" / f"month={m}"
        meta_rows = sum(pq.ParquetFile(f).metadata.num_rows for f in sd.glob("*.parquet"))
        b = man[(man.service == r.service) & (man.month == r.month)]
        bronze_rows = int(b.n_rows.iloc[0]) if len(b) else None
        rows.append(dict(service=r.service, month=r.month, bronze_rows=bronze_rows, n_raw_processed=int(r.n_raw),
                         n_rejected=int(r.n_rejected), n_silver_log=int(r.n_silver), n_silver_parquet=meta_rows,
                         check_bronze=bool(bronze_rows == r.n_raw), check_balance=bool(r.n_raw == r.n_rejected + r.n_silver),
                         check_silver=bool(meta_rows == r.n_silver)))
    t = pd.DataFrame(rows)
    t.to_csv(TAB / "t71_reconciliation.csv", index=False)
    wlog("reconcile", dict(partitions=len(t), pass_bronze=int(t.check_bronze.sum()),
                           pass_balance=int(t.check_balance.sum()), pass_silver=int(t.check_silver.sum())))


# ------------------------------------------------------------------ anomaly
def part_anomaly():
    from viz import C, fig, save, policy_line
    con = duck()
    d = con.execute(f"""SELECT service, d, pu_grp, sum(n) AS n FROM '{(GOLD / 'grp_hour_day.parquet').as_posix()}'
                        GROUP BY ALL""").df()
    d["d"] = pd.to_datetime(d.d)
    out = []
    for (svc, grp), g in d.groupby(["service", "pu_grp"]):
        if grp not in ("CRZ", "MN_NORTH", "OUTER", "AIRPORT"):
            continue
        g = g.sort_values("d").set_index("d")
        s = np.log(g.n)
        # Kỳ vọng: trung vị của cùng thứ trong tuần trong cửa sổ ±28 ngày (không gồm chính ngày đó)
        exp, mad = [], []
        for day in s.index:
            win = s[(s.index >= day - pd.Timedelta(days=28)) & (s.index <= day + pd.Timedelta(days=28))
                    & (s.index.dayofweek == day.dayofweek) & (s.index != day)]
            med = win.median()
            exp.append(med)
            mad.append(1.4826 * np.median(np.abs(win - med)))
        g["expected_log"] = exp
        g["mad"] = mad
        g["z"] = (s - g.expected_log) / g.mad.replace(0, np.nan)
        g["dev_pct"] = 100 * (np.exp(s - g.expected_log) - 1)
        g["service"], g["grp"] = svc, grp
        out.append(g.reset_index())
    a = pd.concat(out)
    a["flag"] = a.z.abs() > 3.5
    a.to_csv(TAB / "t72_daily_anomaly_scores.csv", index=False)
    fl = a[a.flag & (a.service == "hvfhv") & (a.grp == "CRZ")].sort_values("z")
    fl[["d", "n", "dev_pct", "z"]].to_csv(TAB / "t72b_anomaly_days_crz.csv", index=False)
    summ = a.groupby(["service", "grp"]).agg(days=("d", "count"), flagged=("flag", "sum"),
                                             flagged_low=("z", lambda z: int((z < -3.5).sum())),
                                             flagged_high=("z", lambda z: int((z > 3.5).sum()))).reset_index()
    summ.to_csv(TAB / "t72c_anomaly_summary.csv", index=False)
    # Hình f48
    h = a[(a.service == "hvfhv") & (a.grp == "CRZ")].sort_values("d")
    f, axes = fig(6.8, 4.2, nrows=2, sharex=True)
    axes[0].plot(h.d, h.n / 1e3, color=C["s1"], lw=0.9, label="Thực tế")
    axes[0].plot(h.d, np.exp(h.expected_log) / 1e3, color=C["neutral_dark"], lw=0.9, label="Kỳ vọng (trung vị cùng thứ)")
    axes[0].scatter(h.d[h.flag], h.n[h.flag] / 1e3, color=C["s8"], s=14, zorder=3, label="Bất thường |z|>3,5")
    axes[0].set_ylabel("Nghìn chuyến/ngày")
    axes[0].legend(loc="lower left", ncol=3, fontsize=7.5)
    axes[0].set_title("Phát hiện ngày bất thường: số chuyến HVFHV đón trong CRZ")
    axes[1].bar(h.d, h.z.clip(-15, 15), color=np.where(h.flag, C["s8"], C["neutral"]), width=1.0)
    axes[1].axhline(3.5, color=C["text2"], lw=0.7, ls=":")
    axes[1].axhline(-3.5, color=C["text2"], lw=0.7, ls=":")
    axes[1].set_ylabel("z bền vững (cắt ±15)")
    policy_line(axes[1], P_TS)
    f.tight_layout()
    save(f, "f48_anomaly_days")
    # Biểu đồ kiểm soát tỷ lệ loại bỏ theo tháng. Với n ~ 2e7 bản ghi mỗi tháng, giới hạn p-chart nhị thức
    # rất hẹp nên hầu như tháng nào cũng "vượt kiểm soát" (quá phân tán). Biểu đồ p' của Laney (2002) hiệu
    # chỉnh bằng độ lệch chuẩn của z-score ước lượng từ khoảng biến động di chuyển (moving range).
    q = pd.read_csv(TAB / "t06_quality_by_month.csv")
    rowsq = []
    f, axes = fig(6.8, 3.0, ncols=2)
    for ax, svc in zip(axes, SERVICES):
        s = q[q.service == svc].sort_values("month")
        pbar = s.n_rejected.sum() / s.n_raw.sum()
        sig = np.sqrt(pbar * (1 - pbar) / s.n_raw)
        p = s.n_rejected / s.n_raw
        z = (p - pbar) / sig
        sigma_z = np.mean(np.abs(np.diff(z))) / 1.128
        ucl, lcl = pbar + 3 * sig, pbar - 3 * sig
        ucl2, lcl2 = pbar + 3 * sig * sigma_z, np.maximum(pbar - 3 * sig * sigma_z, 0)
        out_c = (p > ucl) | (p < lcl)
        out_l = (p > ucl2) | (p < lcl2)
        rowsq.append(dict(service=svc, pbar_pct=100 * pbar, months=len(s), out_p_chart=int(out_c.sum()),
                          sigma_z=float(sigma_z), out_laney=int(out_l.sum()),
                          laney_months=";".join(s.month[out_l].tolist()),
                          p_min_pct=100 * p.min(), p_max_pct=100 * p.max()))
        ax.plot(range(len(s)), 100 * p, marker="o", ms=3, color=C["s1"], label="Tỷ lệ loại")
        ax.plot(range(len(s)), 100 * ucl2, color=C["s8"], lw=0.8, ls="--", label="Giới hạn p' (Laney)")
        ax.plot(range(len(s)), 100 * lcl2, color=C["s8"], lw=0.8, ls="--")
        ax.plot(range(len(s)), 100 * ucl, color=C["neutral_dark"], lw=0.6, ls=":", label="Giới hạn p nhị thức")
        ax.plot(range(len(s)), 100 * lcl, color=C["neutral_dark"], lw=0.6, ls=":")
        ax.axhline(100 * pbar, color=C["text2"], lw=0.8)
        ax.set_xticks(range(0, len(s), 6), [m[2:] for m in s.month.values[::6]])
        ax.set_title("HVFHV" if svc == "hvfhv" else "Taxi vàng")
        ax.set_ylabel("% chuyến bị loại")
    axes[0].legend(fontsize=6.5, loc="upper left")
    f.tight_layout()
    save(f, "f49_pchart_reject")
    pd.DataFrame(rowsq).to_csv(TAB / "t72d_pchart_reject.csv", index=False)
    wlog("anomaly", dict(summary=summ.to_dict("records"), crz_flagged=len(fl), pchart=rowsq))


P_TS = pd.Timestamp("2025-01-05")


# ------------------------------------------------------------------ tripanom
def part_tripanom():
    from sklearn.ensemble import IsolationForest
    from viz import C, fig, save
    s = pd.read_parquet(GOLD / "trip_sample.parquet",
                        columns=["service", "company_code", "pu", "dl", "miles", "time_s", "fare", "driver_pay",
                                 "tips", "wait_min", "mph", "pu_grp", "do_grp", "cbd_fee", "d", "hr"])
    s = s[s.service == "hvfhv"].dropna(subset=["miles", "time_s", "fare", "driver_pay"]).copy()
    s["fare_pm"] = s.fare / s.miles
    s["pay_ratio"] = s.driver_pay / s.fare
    s["tip_ratio"] = s.tips / s.fare
    feats = ["miles", "time_s", "fare", "driver_pay", "mph", "fare_pm", "pay_ratio", "tip_ratio"]
    X = s[feats].copy()
    for c in ("miles", "time_s", "fare", "driver_pay", "fare_pm"):
        X[c] = np.log(X[c].clip(lower=1e-3))
    X = X.replace([np.inf, -np.inf], np.nan).fillna(X.median())
    t0 = time.perf_counter()
    iso = IsolationForest(n_estimators=200, contamination=0.005, random_state=SEED, n_jobs=2).fit(X)
    s["score"] = -iso.score_samples(X)
    s["iso_flag"] = iso.predict(X) == -1
    el = time.perf_counter() - t0
    # Quy tắc nghiệp vụ minh bạch
    rules = {
        "Thu nhập tài xế > giá cước + tip": s.driver_pay > s.fare + s.tips,
        "Giá cước / dặm > 30 USD": s.fare_pm > 30,
        "Tip > giá cước": s.tips > s.fare,
        "Tốc độ < 2 dặm/giờ và thời gian > 30 phút": (s.mph < 2) & (s.time_s > 1800),
        "Cùng vùng đón/trả và quãng đường > 10 dặm": (s.pu == s.dl) & (s.miles > 10),
    }
    rr = []
    for k, m in rules.items():
        rr.append(dict(rule=k, n=int(m.sum()), pct=100 * m.mean(), overlap_iso_pct=100 * (m & s.iso_flag).sum() / max(m.sum(), 1)))
    rr.append(dict(rule="Isolation Forest (ngưỡng 0,5%)", n=int(s.iso_flag.sum()), pct=100 * s.iso_flag.mean(),
                   overlap_iso_pct=100.0))
    pd.DataFrame(rr).to_csv(TAB / "t73_trip_anomaly_rules.csv", index=False)
    prof = s.groupby("iso_flag")[["miles", "time_s", "fare", "driver_pay", "mph", "fare_pm", "pay_ratio", "tip_ratio",
                                   "wait_min"]].median().T
    prof.columns = ["Bình thường" if not c else "Bất thường" for c in prof.columns]
    prof.to_csv(TAB / "t73b_trip_anomaly_profile.csv")
    comp = pd.crosstab(s.company_code, s.iso_flag, normalize="index") * 100
    comp.to_csv(TAB / "t73c_trip_anomaly_by_company.csv")
    grp = (s.assign(crz=(s.pu_grp == "CRZ") | (s.do_grp == "CRZ"),
                    post=pd.to_datetime(s.d) >= P_TS)
           .groupby(["crz", "post"]).iso_flag.mean() * 100).reset_index()
    grp.to_csv(TAB / "t73d_trip_anomaly_by_crz_period.csv", index=False)
    f, ax = fig(6.4, 3.4)
    nm = s[~s.iso_flag].sample(min(40000, (~s.iso_flag).sum()), random_state=SEED)
    ab = s[s.iso_flag]
    ax.scatter(nm.miles, nm.fare, s=1.5, color=C["neutral"], alpha=0.5, label="Bình thường (mẫu)", rasterized=True)
    ax.scatter(ab.miles, ab.fare, s=3, color=C["s8"], alpha=0.8, label="Bất thường (Isolation Forest)", rasterized=True)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Quãng đường (dặm, thang log)")
    ax.set_ylabel("Giá cước cơ sở (USD, thang log)")
    ax.set_title("Chuyến bất thường trên mẫu 0,25% chuyến HVFHV")
    ax.legend(markerscale=4)
    save(f, "f50_trip_anomaly")
    wlog("tripanom", dict(n=len(s), flagged=int(s.iso_flag.sum()), fit_score_s=round(el, 1), rules=rr))


# ------------------------------------------------------------------ privacy
def part_privacy():
    """k-ẩn danh trên một tháng Silver HVFHV: với mỗi tổ hợp định danh gián tiếp (quasi-identifier),
    tính tỷ lệ chuyến nằm trong lớp tương đương có kích thước 1 (duy nhất), < 5 và < 10."""
    from viz import C, fig, save
    con = duck()
    y, m = "2025", "03"
    src = (SILVER / "service=hvfhv" / f"year={y}" / f"month={m}" / "*.parquet").as_posix()
    dz = (GOLD / "dim_zone.parquet").as_posix()
    con.execute(f"""CREATE TEMP TABLE t AS SELECT s.pu, s.dl, s.d, s.hr, s.company_code, s.pickup_ts, s.request_ts,
                    s.dow, zp.Borough AS pb, zd.Borough AS db
                    FROM read_parquet('{src}') s
                    LEFT JOIN '{dz}' zp ON s.pu = zp.LocationID LEFT JOIN '{dz}' zd ON s.dl = zd.LocationID""")
    n = con.execute("SELECT count(*) FROM t").fetchone()[0]
    qis = [
        ("Quận đón, quận trả, tháng", "pb, db"),
        ("Quận đón, quận trả, ngày", "pb, db, d"),
        ("Quận đón, quận trả, ngày, giờ", "pb, db, d, hr"),
        ("Vùng đón, vùng trả", "pu, dl"),
        ("Vùng đón, vùng trả, thứ, giờ", "pu, dl, dow, hr"),
        ("Vùng đón, vùng trả, ngày", "pu, dl, d"),
        ("Vùng đón, vùng trả, ngày, giờ", "pu, dl, d, hr"),
        ("Vùng đón, vùng trả, ngày, giờ, hãng", "pu, dl, d, hr, company_code"),
        ("Vùng đón, vùng trả, phút đón", "pu, dl, date_trunc('minute', pickup_ts)"),
        ("Vùng đón, vùng trả, giây đón (như bản công bố)", "pu, dl, pickup_ts"),
    ]
    rows = []
    for lab, cols in qis:
        t = time.perf_counter()
        r = con.execute(f"""WITH g AS (SELECT count(*) AS k FROM t GROUP BY {cols})
            SELECT count(*) AS classes, sum(k) AS trips,
                   sum(CASE WHEN k=1 THEN k ELSE 0 END) AS k1, sum(CASE WHEN k<5 THEN k ELSE 0 END) AS k5,
                   sum(CASE WHEN k<10 THEN k ELSE 0 END) AS k10, median(k) AS med_k FROM g""").fetchone()
        rows.append(dict(qi=lab, columns=cols, classes=r[0], trips=r[1], unique_pct=100 * r[2] / r[1],
                         lt5_pct=100 * r[3] / r[1], lt10_pct=100 * r[4] / r[1], median_class=r[5],
                         seconds=round(time.perf_counter() - t, 2)))
        print(rows[-1], flush=True)
    tb = pd.DataFrame(rows)
    tb.to_csv(TAB / "t74_privacy_kanonymity.csv", index=False)
    plot_privacy()
    wlog("privacy", dict(month=f"{y}-{m}", trips=n, results=rows))


def plot_privacy():
    from viz import C, fig, save
    tb = pd.read_csv(TAB / "t74_privacy_kanonymity.csv")
    f, ax = fig(6.8, 3.8)
    yy = range(len(tb))
    ax.barh([i + 0.27 for i in yy], tb.unique_pct, 0.27, color=C["s8"], label="k = 1 (duy nhất)")
    ax.barh(list(yy), tb.lt5_pct, 0.27, color=C["s4"], label="k < 5")
    ax.barh([i - 0.27 for i in yy], tb.lt10_pct, 0.27, color=C["s1"], label="k < 10")
    ax.set_yticks(list(yy), tb.qi, fontsize=7)
    ax.invert_yaxis()
    ax.set_xlabel("% chuyến trong lớp tương đương nhỏ")
    ax.set_title("Rủi ro tái nhận dạng theo mức chi tiết của định danh gián tiếp")
    ax.legend(loc="upper right")
    save(f, "f51_privacy_kanonymity")


# ------------------------------------------------------------------ dp
def part_dp():
    """Nhiễu Laplace (ε-DP ở mức chuyến, độ nhạy 1) lên từng ô vùng × ngày của bảng công bố,
    sau đó dựng lại panel vùng × tuần và ước lượng lại TWFE log số chuyến."""
    from causal import fe_ols
    from panels import W0, W_END, P, dim, MIN_DAILY
    from viz import C, fig, save
    z = pd.read_parquet(GOLD / "zone_day_pu.parquet", columns=["service", "d", "zone", "n"])
    z = z[z.service == "hvfhv"].copy()
    z["d"] = pd.to_datetime(z.d)
    z = z[(z.d >= W0) & (z.d <= W_END)]
    z["wk"] = z.d - pd.to_timedelta((z.d.dt.dayofweek + 1) % 7, unit="D")
    dm = dim()[["LocationID", "grp"]]
    z = z.merge(dm, left_on="zone", right_on="LocationID")
    z = z[z.grp.isin(["CRZ", "MN_NORTH", "OUTER"])]
    # Tập vùng cố định như bản không nhiễu (panels.zone_week)
    wk0 = z.groupby(["zone", "wk", "grp"]).n.sum().reset_index()
    pre = wk0[wk0.wk < P].groupby("zone").n.sum() / ((P - W0).days)
    keep = pre[pre >= MIN_DAILY["hvfhv"]].index
    full = wk0.groupby("zone").wk.nunique()
    keep = [k for k in keep if full.get(k, 0) == wk0.wk.nunique()]
    z = z[z.zone.isin(keep)].copy()

    def estimate(zz):
        g = zz.groupby(["zone", "wk", "grp"]).n.sum().reset_index()
        g["treat"] = (g.grp == "CRZ").astype(int)
        g["D"] = g.treat * (g.wk >= P).astype(int)
        g["ln_n"] = np.log(g.n.clip(lower=1))
        res, info, _ = fe_ols(g, "ln_n", ["D"], ["zone", "wk"], "zone")
        return res.coef.iloc[0], res.se.iloc[0], info["n_obs"]

    b0, se0, nobs = estimate(z)
    rng = np.random.default_rng(SEED)
    rows = [dict(eps=np.inf, rep=0, coef=b0, se=se0)]
    t0 = time.perf_counter()
    cell_small = z.n.quantile(0.05)
    for eps in (0.001, 0.005, 0.01, 0.05, 0.1, 1.0):
        for rep in range(40):
            zz = z.copy()
            zz["n"] = np.maximum(zz.n + rng.laplace(0, 1 / eps, len(zz)), 1)
            b, se, _ = estimate(zz)
            rows.append(dict(eps=eps, rep=rep + 1, coef=b, se=se))
    r = pd.DataFrame(rows)
    r.to_csv(TAB / "t75_dp_replications.csv", index=False)
    s = r[np.isfinite(r.eps)].groupby("eps").agg(mean_coef=("coef", "mean"), sd_coef=("coef", "std"),
                                                 mean_se=("se", "mean")).reset_index()
    s["bias"] = s.mean_coef - b0
    s["rmse"] = np.sqrt(s.bias ** 2 + s.sd_coef ** 2)
    s["noise_sd_cell"] = np.sqrt(2) / s.eps
    s["noise_rel_p5_cell_pct"] = 100 * s.noise_sd_cell / cell_small
    s["pct_effect_mean"] = 100 * (np.exp(s.mean_coef) - 1)
    s["baseline_coef"], s["baseline_se"] = b0, se0
    s.to_csv(TAB / "t75b_dp_summary.csv", index=False)
    f, ax = fig(6.4, 3.0)
    ax.errorbar(s.eps, 100 * (np.exp(s.mean_coef) - 1), yerr=[100 * (np.exp(s.mean_coef) - np.exp(s.mean_coef - 1.96 * s.sd_coef)),
                100 * (np.exp(s.mean_coef + 1.96 * s.sd_coef) - np.exp(s.mean_coef))],
                fmt="o-", color=C["s1"], capsize=3, label="Có nhiễu Laplace (trung bình ± 1,96 độ lệch chuẩn)")
    ax.axhline(100 * (np.exp(b0) - 1), color=C["s2"], ls="--", lw=1, label="Không nhiễu")
    ax.set_xscale("log")
    ax.set_xlabel("Ngân sách riêng tư ε (thang log; nhỏ hơn = riêng tư hơn)")
    ax.set_ylabel("Tác động lên số chuyến (%)")
    ax.set_title("Đánh đổi riêng tư – hữu dụng của bảng công bố vùng × ngày")
    ax.legend(fontsize=7.5)
    save(f, "f52_dp_tradeoff")
    wlog("dp", dict(cells=len(z), zones=len(keep), obs=nobs, baseline=b0, seconds=round(time.perf_counter() - t0, 1),
                    cell_p5=float(cell_small)))


# ------------------------------------------------------------------ dr
def part_dr():
    q = pd.read_csv(TAB / "t08_partition_runtime.csv")
    bronze = pd.read_csv(TAB / "t01_bronze_manifest.csv")
    g04 = json.loads((LOG / "04_gold_consolidate.json").read_text())["seconds"]
    steps = {}
    for f in LOG.glob("*.json"):
        try:
            d = json.loads(f.read_text())
            if isinstance(d, dict) and "seconds" in d:
                steps[f.stem] = d["seconds"]
        except Exception:
            pass
    ana = sum(v for k, v in steps.items() if k[:2] in ("06", "07", "08", "09", "10", "11", "14"))
    rows = [
        dict(scenario="Mất lớp Gold (còn Silver)", rebuild="Chạy lại phần Gold của bước 03 + bước 04",
             seconds=float(q.sec_gold.sum() + g04)),
        dict(scenario="Mất lớp Silver và Gold (còn Bronze)", rebuild="Chạy lại bước 03 toàn bộ + bước 04",
             seconds=float(q.sec_total.sum() + g04)),
        dict(scenario="Mất một phân vùng tháng HVFHV", rebuild="Chạy lại 4 khúc của tháng đó",
             seconds=float(q[q.service == "hvfhv"].groupby("month").sec_total.sum().median())),
        dict(scenario="Mất toàn bộ kết quả phân tích (còn Gold)", rebuild="Chạy lại các bước 06–11, 14",
             seconds=float(ana)),
    ]
    t = pd.DataFrame(rows)
    t["minutes"] = t.seconds / 60
    sizes = dict(bronze_gb=bronze.size_mb.sum() / 1024)
    t.to_csv(TAB / "t76_recovery_rto.csv", index=False)
    wlog("dr", dict(rows=rows, **sizes))


if __name__ == "__main__":
    part = sys.argv[1]
    arg = sys.argv[2:]
    fn = {"catalog": part_catalog, "lineage": part_lineage, "reconcile": part_reconcile, "anomaly": part_anomaly,
          "tripanom": part_tripanom, "privacy": part_privacy, "privacy_fig": plot_privacy, "dp": part_dp, "dr": part_dr}
    if part == "integrity":
        part_integrity(float(arg[0]) if arg else 1e9)
    elif part in fn:
        fn[part]()
    else:
        raise SystemExit(__doc__)
