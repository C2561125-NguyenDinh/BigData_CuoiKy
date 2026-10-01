"""Các phụ lục: hồ sơ vùng, bảng theo tháng, theo giờ, hệ số sự kiện, SCM, chất lượng, tệp kết quả, mã nguồn."""
import numpy as np
import pandas as pd

from lib import pval, stars, vint, vn

GL = {"CRZ": "CRZ", "CRZ_PARTIAL": "Vắt ranh giới", "MN_NORTH": "Manhattan phía bắc", "OUTER": "Quận ngoài",
      "AIRPORT": "Sân bay", "UNKNOWN": "Không xác định"}


def _zone_profiles(rp, R):
    a = R.t("a01")
    hv = a[a.service == "hvfhv"].copy()
    ye = a[a.service == "yellow"].set_index("zone")
    rp.appendix("A", "PHỤ LỤC A. HỒ SƠ CHI TIẾT THEO VÙNG")
    rp.P("Phụ lục này trình bày hồ sơ của từng vùng taxi thuộc Manhattan (CRZ, vắt ranh giới và Manhattan phía bắc) và của 60 vùng "
         "quận ngoài có lưu lượng HVFHV lớn nhất năm 2024, là các vùng đóng góp nhiều nhất vào nhóm đối chứng. Mỗi hồ sơ so "
         "sánh cùng cửa sổ lịch 05/01 – 31/12 của hai năm 2024 và 2025. Số chuyến được tính bình quân mỗi ngày; các chỉ tiêu khác là "
         "trung bình theo chuyến đón tại vùng. Nhận xét dưới mỗi bảng được sinh tự động từ chính các con số trong bảng.")
    order = ["CRZ", "CRZ_PARTIAL", "MN_NORTH", "OUTER"]
    rp.P("Để danh mục bảng và mục lục gọn, các hồ sơ vùng trong phụ lục này không được liệt kê riêng trong danh mục; mục lục chỉ "
         "liệt kê đến cấp nhóm vùng.")
    for g in order:
        k = 0
        sub = hv[hv.grp == g].sort_values("zone")
        if g == "OUTER":
            sub = sub.sort_values("pu_per_day_2024", ascending=False).head(60).sort_values(["Borough", "zone"])
        rp.H2(f"A.{order.index(g) + 1}. Nhóm {GL[g]} ({len(sub)} vùng)" if g != "OUTER" else
              f"A.{order.index(g) + 1}. Quận ngoài: 60 vùng có lưu lượng lớn nhất")
        for _, r in sub.iterrows():
            k += 1
            rp.quiet = True
            rp.H3(f"A.{order.index(g) + 1}.{k}. Vùng {int(r.zone)} – {r.Zone}")
            rows = [
                ("Chuyến HVFHV đón/ngày", r.pu_per_day_2024, r.pu_per_day_2025, 0),
                ("Chuyến HVFHV trả/ngày", r.do_per_day_2024, r.do_per_day_2025, 0),
                ("Giá cước cơ sở/chuyến (USD)", r.fare_pt_2024, r.fare_pt_2025, 2),
                ("Thu nhập tài xế/chuyến (USD)", r.pay_pt_2024, r.pay_pt_2025, 2),
                ("Tốc độ trung bình (dặm/giờ)", r.mph_2024, r.mph_2025, 2),
                ("Thời gian chờ (phút)", r.wait_2024, r.wait_2025, 2),
                ("Phí CBD/chuyến (USD)", r.cbd_pt_2024, r.cbd_pt_2025, 3),
                ("% chuyến đón có đích trong CRZ", r.share_to_crz_2024, r.share_to_crz_2025, 1),
            ]
            if r.zone in ye.index and not pd.isna(ye.loc[r.zone, "pu_per_day_2024"]):
                yr = ye.loc[r.zone]
                rows.append(("Chuyến taxi vàng đón/ngày", yr.pu_per_day_2024, yr.pu_per_day_2025, 0))
            df = pd.DataFrame([(n, vn(x, d), vn(y, d), vn(y - x, d, sign=True),
                                vn(100 * (y / x - 1), 1, sign=True) if x and not pd.isna(x) and x != 0 else "–")
                               for n, x, y, d in rows],
                              columns=["Chỉ tiêu", "2024", "2025", "Chênh lệch", "%"])
            where = GL[g] if g != "OUTER" else r.Borough
            rp.TAB(df, f"Hồ sơ vùng {int(r.zone)} – {r.Zone} ({where}, cách CRZ {vn(r.dist_to_crz_km, 2)} km)",
                   widths=[6.4, 2.4, 2.4, 2.4, 2.4], size=10, source=None)
            parts = []
            if not pd.isna(r.pu_yoy_pct):
                parts.append(f"Số chuyến đón {'giảm' if r.pu_yoy_pct < 0 else 'tăng'} {vn(abs(r.pu_yoy_pct), 1)}%")
            if not pd.isna(r.mph_2024) and not pd.isna(r.mph_2025):
                dv = r.mph_2025 - r.mph_2024
                parts.append(f"tốc độ {'tăng' if dv > 0 else 'giảm'} {vn(abs(dv), 2)} dặm/giờ")
            if not pd.isna(r.wait_2024) and not pd.isna(r.wait_2025):
                dw = r.wait_2025 - r.wait_2024
                parts.append(f"thời gian chờ {'giảm' if dw < 0 else 'tăng'} {vn(abs(dw), 2)} phút")
            if parts:
                rp.P("So với cùng kỳ: " + ", ".join(parts) + ".", size=12)
            rp.quiet = False


def _all_zones(rp, R):
    a = R.t("a01")
    hv = a[a.service == "hvfhv"].copy()
    rp.appendix("B", "PHỤ LỤC B. BẢNG TỔNG HỢP 263 VÙNG TAXI")
    rp.P("Bảng dưới đây liệt kê mọi vùng có chuyến HVFHV trong dữ liệu, sắp theo quận và mã vùng, với số chuyến đón bình quân mỗi "
         "ngày, tốc độ và thời gian chờ trong cửa sổ 05/01 – 31/12 của hai năm.")
    for boro in ["Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island", "EWR"]:
        sub = hv[hv.Borough == boro].sort_values("zone")
        if sub.empty:
            continue
        df = pd.DataFrame({"Mã": sub.zone.map(vint), "Tên vùng": sub.Zone, "Nhóm": sub.grp.map(GL),
                           "Đón/ngày 2024": sub.pu_per_day_2024.map(lambda v: vn(v, 0)),
                           "Đón/ngày 2025": sub.pu_per_day_2025.map(lambda v: vn(v, 0)),
                           "Thay đổi %": sub.pu_yoy_pct.map(lambda v: vn(v, 1)),
                           "Dặm/giờ 2024": sub.mph_2024.map(lambda v: vn(v, 1)), "Dặm/giờ 2025": sub.mph_2025.map(lambda v: vn(v, 1)),
                           "Chờ 2024": sub.wait_2024.map(lambda v: vn(v, 1)), "Chờ 2025": sub.wait_2025.map(lambda v: vn(v, 1))})
        rp.TAB(df, f"Chỉ tiêu HVFHV theo vùng – {boro}", widths=[0.9, 3.9, 2.2, 1.5, 1.5, 1.3, 1.2, 1.2, 1.1, 1.1],
               size=8, align=["center", "left", "left"] + ["center"] * 7, source="Nguồn: a01_zone_detail.csv.")


def _months(rp, R):
    m = R.t("a02")
    rp.appendix("C", "PHỤ LỤC C. CHỈ TIÊU THEO THÁNG VÀ NHÓM VÙNG")
    for svc, name in (("hvfhv", "HVFHV"), ("yellow", "taxi vàng")):
        for g in ["CRZ", "CRZ_PARTIAL", "MN_NORTH", "OUTER", "AIRPORT"]:
            sub = m[(m.service == svc) & (m.grp == g)].sort_values("ym")
            if sub.empty:
                continue
            cols = {"Tháng": sub.ym, "Chuyến/ngày": sub.trips_per_day.map(lambda v: vn(v, 0)),
                    "Giá/chuyến": sub.fare_pt.map(lambda v: vn(v, 2)), "Dặm/giờ": sub.mph.map(lambda v: vn(v, 2)),
                    "Phí CBD/chuyến": sub.cbd_pt.map(lambda v: vn(v, 3)), "% chuyến bị tính phí": sub.share_cbd.map(lambda v: vn(v, 1))}
            w = [2.0, 2.6, 2.4, 2.4, 2.6, 2.8]
            if svc == "hvfhv":
                cols["TN tài xế/chuyến"] = sub.pay_pt.map(lambda v: vn(v, 2))
                cols["Chờ (phút)"] = sub.wait.map(lambda v: vn(v, 2))
                w += [2.4, 2.0]
            rp.TAB(pd.DataFrame(cols), f"Chỉ tiêu theo tháng – {name}, nhóm vùng đón {GL[g]}", widths=w, size=9,
                   source="Nguồn: a02_month_group_detail.csv.")


def _flows(rp, R):
    f = R.t("a03")
    f = f[f.service == "hvfhv"]
    rp.appendix("D", "PHỤ LỤC D. LUỒNG CHUYẾN THEO GIỜ")
    rp.P("Mỗi bảng trình bày một luồng giữa hai nhóm vùng: số chuyến bình quân mỗi ngày, tốc độ và giá cước/chuyến theo giờ đón, "
         "trong cửa sổ 05/01 – 31/12 của hai năm.")
    for a, b in (("CRZ", "CRZ"), ("CRZ", "OUTER"), ("OUTER", "CRZ"), ("CRZ", "MN_NORTH"), ("MN_NORTH", "CRZ"),
                 ("MN_NORTH", "MN_NORTH"), ("OUTER", "OUTER"), ("CRZ", "AIRPORT")):
        sub = f[(f.pu_grp == a) & (f.do_grp == b)].pivot_table(index="hr", columns="yr", values=["per_day", "mph", "fare_pt"])
        df = pd.DataFrame({"Giờ": sub.index.astype(int).astype(str),
                           "Chuyến/ngày 2024": sub[("per_day", 2024)].map(lambda v: vn(v, 0)),
                           "Chuyến/ngày 2025": sub[("per_day", 2025)].map(lambda v: vn(v, 0)),
                           "Thay đổi %": (100 * (sub[("per_day", 2025)] / sub[("per_day", 2024)] - 1)).map(lambda v: vn(v, 1)),
                           "Dặm/giờ 2024": sub[("mph", 2024)].map(lambda v: vn(v, 2)), "Dặm/giờ 2025": sub[("mph", 2025)].map(lambda v: vn(v, 2)),
                           "Giá/chuyến 2024": sub[("fare_pt", 2024)].map(lambda v: vn(v, 2)),
                           "Giá/chuyến 2025": sub[("fare_pt", 2025)].map(lambda v: vn(v, 2))})
        rp.TAB(df, f"Luồng {GL[a]} → {GL[b]} theo giờ đón (HVFHV)", widths=[1.2, 2.2, 2.2, 1.8, 2.1, 2.1, 2.2, 2.2], size=9,
               source="Nguồn: a03_flow_hour_detail.csv.")


def _events(rp, R):
    ev = R.t("t31")
    em = R.t("t32")
    rp.appendix("E", "PHỤ LỤC E. HỆ SỐ ĐẦY ĐỦ CỦA CÁC NGHIÊN CỨU SỰ KIỆN")
    for svc, name in (("hvfhv", "HVFHV"), ("yellow", "taxi vàng")):
        e = ev[(ev.service == svc) & (ev.spec == "TWFE")].sort_values("k")
        wk0 = pd.Timestamp("2025-01-05")
        df = pd.DataFrame({"k (tuần)": e.k.map(vint),
                           "Tuần bắt đầu": [(wk0 + pd.Timedelta(days=7 * int(k))).strftime("%d/%m/%Y") for k in e.k],
                           "Hệ số chuẩn hóa ×100": (100 * e.coef_c).map(lambda v: vn(v, 2)),
                           "SE ×100": (100 * e.se_c).map(lambda v: vn(v, 2)),
                           "KTC 95%": [f"[{vn(100 * a, 2)}; {vn(100 * b, 2)}]" for a, b in zip(e.ci_low_c, e.ci_high_c)]})
        rp.TAB(df, f"Hệ số nghiên cứu sự kiện theo tuần, log số chuyến đón – {name} (TWFE, chuẩn hóa theo trung bình kỳ trước)",
               widths=[1.8, 3.0, 3.4, 2.6, 5.2], size=8.5, source="Nguồn: t31_event_study_weekly_ln_n.csv.")
        d = ev[(ev.service == svc) & (ev.spec == "DDD mùa vụ")].sort_values("k")
        df = pd.DataFrame({"k (tuần)": d.k.map(vint),
                           "Tuần bắt đầu": [(wk0 + pd.Timedelta(days=7 * int(k))).strftime("%d/%m/%Y") for k in d.k],
                           "Hệ số ×100": (100 * d.coef).map(lambda v: vn(v, 2)), "SE ×100": (100 * d.se).map(lambda v: vn(v, 2)),
                           "p": d.p.map(pval)})
        rp.TAB(df, f"Hệ số DDD theo tuần sau chính sách, log số chuyến đón – {name}", widths=[1.8, 3.0, 3.2, 3.0, 5.0],
               size=8.5, source="Nguồn: t31_event_study_weekly_ln_n.csv.")
    lab = {"fare_pm": "Giá cước/dặm", "pay_pm": "TN tài xế/dặm", "rider_pt": "Chi phí hành khách/chuyến", "mph": "Tốc độ",
           "wait": "Thời gian chờ", "miles_pt": "Dặm/chuyến"}
    piv = em.pivot_table(index="k", columns="outcome", values="coef_c")
    pse = em.pivot_table(index="k", columns="outcome", values="se_c")
    df = pd.DataFrame({"k (tháng)": piv.index.astype(int).astype(str)})
    for o, l in lab.items():
        df[l] = [f"{vn(a, 3)} ({vn(b, 3)})" for a, b in zip(piv[o], pse[o])]
    rp.TAB(df, "Hệ số nghiên cứu sự kiện theo tháng cho sáu chỉ tiêu (HVFHV; hệ số chuẩn hóa, sai số chuẩn trong ngoặc)",
           widths=[1.6, 2.4, 2.4, 2.6, 2.4, 2.4, 2.2], size=8.5, source="Nguồn: t32_event_study_monthly_hvfhv.csv.")
    ze = R.t("t54").sort_values("zone")
    df = pd.DataFrame({"Mã": ze.zone.map(vint), "Vùng": ze.Zone,
                       "log số chuyến": [f"{vn(a, 4)} ({vn(b, 4)})" for a, b in zip(ze.b_ln_n, ze.se_ln_n)],
                       "% thay đổi": ze.pct_ln_n.map(lambda v: vn(v, 2)),
                       "Tốc độ": [f"{vn(a, 3)} ({vn(b, 3)})" for a, b in zip(ze.b_mph, ze.se_mph)],
                       "Thời gian chờ": [f"{vn(a, 3)} ({vn(b, 3)})" for a, b in zip(ze.b_wait, ze.se_wait)],
                       "Chuyến/ngày 2024": ze.pre_per_day.map(lambda v: vn(v, 0)), "Độ sâu (km)": ze.depth_km.map(lambda v: vn(v, 2))})
    rp.TAB(df, "Hệ số DiD riêng của từng vùng CRZ (sai số chuẩn trong ngoặc)", widths=[1.0, 3.8, 2.6, 1.5, 2.2, 2.2, 1.6, 1.1],
           size=8, align=["center", "left"] + ["center"] * 6, source="Nguồn: t54_zone_specific_effects.csv.")
    eo = R.t("t37")
    df = pd.DataFrame({"k (tháng)": eo.k.map(vint), "Hệ số ×100": (100 * eo.coef_c).map(lambda v: vn(v, 2)),
                       "SE ×100": (100 * eo.se_c).map(lambda v: vn(v, 2)),
                       "KTC 95%": [f"[{vn(100 * a, 2)}; {vn(100 * b, 2)}]" for a, b in zip(eo.ci_low_c, eo.ci_high_c)]})
    rp.TAB(df, "Hệ số nghiên cứu sự kiện theo tháng trên panel cặp OD (log số chuyến)", widths=[2.4, 3.6, 3.6, 6.4], size=9,
           source="Nguồn: t37_event_od_ln_n.csv.")


def _scm(rp, R):
    rp.appendix("F", "PHỤ LỤC F. KIỂM SOÁT TỔNG HỢP, HOÁN VỊ VÀ CHẤT LƯỢNG DỮ LIỆU")
    rp.H2("F.1. Kết quả giả dược không gian của kiểm soát tổng hợp")
    pl = R.t("t40").sort_values("ratio", ascending=False)
    df = pd.DataFrame({"Mã": pl.zone.map(vint), "Vùng": pl.Zone, "Quận": pl.Borough, "RMSPE trước": pl.rmspe_pre.map(lambda v: vn(v, 4)),
                       "RMSPE sau": pl.rmspe_post.map(lambda v: vn(v, 4)), "Tỷ số": pl.ratio.map(lambda v: vn(v, 2)),
                       "Khoảng cách TB sau": pl.avg_gap_post.map(lambda v: vn(v, 4))})
    rp.TAB(df, "Kết quả SCM cho 60 vùng giả dược, sắp theo tỷ số RMSPE", widths=[1.1, 4.2, 2.3, 2.1, 2.1, 1.8, 2.4], size=8.5,
           align=["center", "left", "left"] + ["center"] * 4, source="Nguồn: t40_scm_placebo.csv.")
    sr = R.t("t39")
    df = pd.DataFrame({"Tuần": pd.to_datetime(sr.week).dt.strftime("%d/%m/%Y"), "CRZ thực tế": sr.treated_index.map(lambda v: vn(v, 4)),
                       "CRZ tổng hợp": sr.synth_standard.map(lambda v: vn(v, 4)),
                       "Khoảng cách ×100": (100 * (sr.treated_index - sr.synth_standard)).map(lambda v: vn(v, 2))})
    rp.TAB(df, "Chuỗi chỉ số tuần của CRZ thực tế và CRZ tổng hợp", widths=[4, 4, 4, 4], size=8.5, source="Nguồn: t39_scm_series.csv.")
    rp.H2("F.2. Phân phối hoán vị")
    pm = R.t("t50")
    qs = pm.perm_coef.quantile([0.01, 0.025, 0.05, 0.25, 0.5, 0.75, 0.95, 0.975, 0.99])
    rp.TAB(pd.DataFrame({"Phân vị": [vn(100 * q, 1) + "%" for q in qs.index], "Hệ số ×100": (100 * qs.values).round(4)}).assign(
        **{"Hệ số ×100": lambda d: d["Hệ số ×100"].map(lambda v: vn(v, 3))}),
        "Các phân vị của phân phối hoán vị (500 lần)", widths=[4, 4], size=10, source="Nguồn: t50_permutation.csv.")
    rp.H2("F.3. Chất lượng dữ liệu theo tháng")
    q = R.t("t06")
    for svc, name in (("hvfhv", "HVFHV"), ("yellow", "taxi vàng")):
        s = q[q.service == svc]
        df = pd.DataFrame({"Tháng": s.month, "Bản ghi thô": s.n_raw.map(vint), "Vùng lỗi": s.q_bad_zone.map(vint),
                           "Dặm lỗi": s.q_bad_miles.map(vint), "Thời lượng lỗi": s.q_bad_time.map(vint),
                           "Giá lỗi": s.q_bad_fare.map(vint), "Tốc độ lỗi": s.q_bad_speed.map(vint),
                           "Tỷ lệ loại %": s.reject_pct.map(lambda v: vn(v, 2)), "Silver": s.n_silver.map(vint)})
        rp.TAB(df, f"Kết quả kiểm soát chất lượng theo tháng – {name}", widths=[1.5, 2.1, 1.8, 1.6, 1.8, 1.6, 1.5, 1.6, 2.5], size=8,
               source="Nguồn: t06_quality_by_month.csv.")
    rp.H2("F.4. Danh mục tệp Bronze")
    m = R.t("t01")
    df = pd.DataFrame({"Tệp": m.file, "MB": m.size_mb.map(lambda v: vn(v, 1)), "Số dòng": m.n_rows.map(vint),
                       "Row group": m.n_row_groups.map(vint), "Số cột": m.n_columns.map(vint), "Lược đồ": m.schema_fingerprint})
    rp.TAB(df, "Danh mục 48 tệp chuyến đi ở lớp Bronze", widths=[5.4, 1.6, 2.6, 1.8, 1.4, 2.4], size=8.5,
           align=["left"] + ["center"] * 5, source="Nguồn: t01_bronze_manifest.csv.")
    rp.H2("F.5. Nhật ký thời gian theo phân vùng")
    r = R.t("t08")
    df = pd.DataFrame({"Dịch vụ": r.service, "Tháng": r.month, "Khúc": r.chunk.map(vint), "Dòng vào": r.n_raw.map(vint),
                       "Dòng Silver": r.n_silver.map(vint), "Chất lượng (s)": r.sec_quality.map(lambda v: vn(v, 1)),
                       "Silver (s)": r.sec_silver.map(lambda v: vn(v, 1)), "Gold (s)": r.sec_gold.map(lambda v: vn(v, 1)),
                       "Tổng (s)": r.sec_total.map(lambda v: vn(v, 1)), "MB": r.silver_mb.map(lambda v: vn(v, 1))})
    rp.TAB(df, "Thời gian xử lý của từng phân vùng", widths=[1.5, 1.6, 1.1, 2.2, 2.2, 1.7, 1.5, 1.4, 1.4, 1.4], size=8,
           source="Nguồn: t08_partition_runtime.csv.")


def _files(rp, R):
    rp.appendix("G", "PHỤ LỤC G. DANH MỤC TỆP KẾT QUẢ")
    rows = []
    for k, v in R.T.items():
        rows.append((f"outputs/tables/{k}.csv", vint(len(v)), vint(v.shape[1])))
    rp.TAB(pd.DataFrame(rows, columns=["Tệp bảng kết quả", "Số dòng", "Số cột"]), "Danh mục các tệp bảng kết quả",
           widths=[10, 3, 3], size=9, align=["left", "center", "center"], source=None)
    figs = sorted(p.name for p in R.fig_dir.glob("*.png"))
    rp.TAB(pd.DataFrame({"Tệp hình": [f"outputs/figures/{f}" for f in figs]}), "Danh mục các tệp hình", widths=[16], size=9,
           align=["left"], source=None)


def _logs(rp, R):
    import re
    rp.appendix("H", "PHỤ LỤC H. NHẬT KÝ XỬ LÝ PHÂN TÁN VÀ QUẢN TRỊ DỮ LIỆU")
    rp.P("Phụ lục này trình bày các bảng chi tiết của Chương 5 và Chương 6: thời gian tái lập từng phân vùng bằng Spark, kết quả "
         "đối chứng đầy đủ, bản kê dấu băm SHA-256 của lớp Bronze, kết quả đối soát số dòng, phả hệ chi tiết và kế hoạch logic của "
         "Spark.")
    rp.H2("H.1. Tái lập bảng zone_day_pu bằng Spark theo phân vùng")
    r = R.t("t60_spark").sort_values(["service", "month"])
    df = pd.DataFrame({"Dịch vụ": r.service, "Tháng": r.month, "Dòng Silver": r.n_silver.map(vint),
                       "Thời gian (s)": r.seconds.map(lambda v: vn(v, 2)), "Dòng/giây": r.rows_per_sec.map(vint),
                       "JVM đỉnh (MB)": r.jvm_peak_mb.map(lambda v: vn(v, 0))})
    rp.TAB(df, "Thời gian tái lập của 48 phân vùng tháng-dịch vụ", widths=[2.2, 2.2, 3.4, 2.6, 3.0, 2.6], size=8.5,
           source="Nguồn: t60_spark_repro_partitions.csv.")
    rp.H2("H.2. Đối chứng chi tiết Spark – DuckDB")
    for key, name in (("t61a", "trước khi sửa lỗi"), ("t61_spark", "sau khi sửa lỗi")):
        v = R.t(key)
        df = pd.DataFrame({"Dịch vụ": v.service, "Chỉ tiêu": v.metric, "Số ô": v.cells.map(vint),
                           "Lệch rỗng": v.null_mismatch.map(vint),
                           "Lệch tuyệt đối max": v.max_abs_diff.map(lambda x: "–" if pd.isna(x) else f"{x:.3g}".replace(".", ",")),
                           "Lệch tương đối max": v.max_rel_diff.map(lambda x: "–" if pd.isna(x) else f"{x:.3g}".replace(".", ",")),
                           "Tổng Spark": v.total_spark.map(lambda x: vn(x, 2)), "Tổng DuckDB": v.total_duckdb.map(lambda x: vn(x, 2))})
        rp.TAB(df, f"Đối chứng từng chỉ tiêu, {name}", widths=[1.5, 2.0, 1.6, 1.3, 2.1, 2.1, 2.7, 2.7], size=7.5,
               source=f"Nguồn: {key}.")
    rp.H2("H.3. Bản kê dấu băm SHA-256 của lớp Bronze")
    h = R.t("t70")
    df = pd.DataFrame({"Tệp": h.file, "Byte": h.bytes.map(vint), "SHA-256": h.sha256, "MB/s": h.mb_per_s.map(lambda v: vn(v, 0))})
    rp.TAB(df, "Dấu băm SHA-256 của 50 tệp nguồn", widths=[4.4, 2.2, 8.4, 1.0], size=6.5,
           align=["left", "center", "left", "center"], source="Nguồn: t70_sha256_manifest.csv.")
    rp.H2("H.4. Đối soát số dòng giữa các lớp")
    c = R.t("t71")
    ok = lambda b: "Đạt" if b else "KHÔNG ĐẠT"
    df = pd.DataFrame({"Dịch vụ": c.service, "Tháng": c.month, "Bronze": c.bronze_rows.map(vint),
                       "Bị loại": c.n_rejected.map(vint), "Silver": c.n_silver_parquet.map(vint),
                       "Bronze = đã đọc": c.check_bronze.map(ok), "Cân đối": c.check_balance.map(ok),
                       "Silver khớp": c.check_silver.map(ok)})
    rp.TAB(df, "Kết quả ba phép đối soát cho 48 phân vùng", widths=[1.6, 1.6, 2.5, 2.1, 2.5, 2.0, 1.8, 1.9], size=8,
           source="Nguồn: t71_reconciliation.csv.")
    rp.H2("H.5. Phả hệ chi tiết theo bước")
    l = R.t("t69")
    df = pd.DataFrame({"Bước": l.step, "Đọc Gold": l.reads_gold.fillna("").str.replace(";", ", "),
                       "Ghi Gold": l.writes_gold.fillna("").str.replace(";", ", "),
                       "Bảng": l.n_tables.map(vint), "Hình": l.n_figures.map(vint)})
    rp.TAB(df, "Các bảng Gold mà mỗi bước đọc, ghi và số sản phẩm tạo ra", widths=[3.6, 6.4, 3.6, 1.2, 1.2], size=7.5,
           align=["left", "left", "left", "center", "center"], source="Nguồn: t69_lineage.csv.")
    rp.H2("H.6. Kế hoạch logic của truy vấn có cắt tỉa phân vùng")
    txt = R.text("spark/plan_logical.txt")
    txt = re.sub(r"file:/\S*?/CongestionPricing_CaseStudy", "file:<ROOT>", txt)
    txt = re.sub(r"file:/sessions/[^,\]\s]*", "file:<ROOT>/data/silver", txt)
    txt = "\n".join(line[:120] for line in txt.splitlines())
    rp.CODE(txt, size=7)
    rp.H2("H.7. Kết quả cửa sổ giờ của Structured Streaming")
    sh = R.t("t67b")
    sh["hour"] = pd.to_datetime(sh["hour"])
    df = pd.DataFrame({"Giờ bắt đầu": sh.hour.dt.strftime("%d/%m %H:%M"), "Chuyến": sh.n.map(vint), "Chạm CRZ": sh.n_crz.map(vint),
                       "Có phí CBD": sh.n_cbd.map(vint), "Phí (USD)": sh.cbd.map(lambda v: vn(v, 2))})
    rp.quiet = True
    rp.TAB(df, "Các cửa sổ 1 giờ do luồng phát ra (tổng ba hãng)", widths=[3.2, 3.2, 3.2, 3.2, 3.2], size=8,
           source="Nguồn: t67b_stream_hourly.csv.")
    rp.quiet = False


def _code(rp, R):
    rp.appendix("I", "PHỤ LỤC I. MÃ NGUỒN VÀ HƯỚNG DẪN CHẠY LẠI")
    rp.H2("I.1. Kho mã nguồn trên GitHub")
    rp.P("Toàn bộ mã nguồn, báo cáo, các bảng và hình kết quả được lưu tại kho GitHub:", indent=False)
    _link(rp, GITHUB_URL)
    repo = pd.DataFrame([
        ("code/", "Mã nguồn bước 00–20, config.py, panels.py, causal.py, viz.py, run_all.py, run_all.sh, requirements.txt"),
        ("code/report/", "Mã dựng báo cáo Word/PDF từ các bảng và hình trong outputs/"),
        ("outputs/tables, figures, logs", "Mọi bảng (CSV), hình (PNG) và nhật ký chạy được dùng trong báo cáo"),
        ("report/", "Báo cáo hoàn chỉnh dạng .pdf và .docx"),
        ("data/gold/", "Lớp Gold: các bảng tổng hợp đủ để chạy lại mọi phân tích nhân quả"),
        ("data/README.md", "Hướng dẫn tải lại dữ liệu thô NYC TLC (khoảng 24 GB, không đưa lên kho)"),
    ], columns=["Thư mục", "Nội dung"])
    rp.TAB(repo, "Cấu trúc kho mã nguồn trên GitHub", widths=[4.6, 11.4], size=10.5, align=["left", "left"],
           source="Nguồn: " + GITHUB_URL)
    gold = R.root / "data" / "gold"
    gmb = sum(p.stat().st_size for p in list(gold.glob("*.parquet")) + [gold / "long" / "zone_day_pu.parquet"]
              if p.exists()) / 1e6
    rp.H2("I.2. Chạy lại kết quả")
    rp.P(f"Cài thư viện bằng pip install -r code/requirements.txt. Kho đã kèm lớp Gold (khoảng {vn(gmb, 0)} MB), nên lệnh "
         "python code/run_all.py --from-gold chạy lại các bước phân tích 06–11, 14, 17–20 và dựng lại báo cáo mà không cần tải dữ "
         "liệu thô. Lệnh python code/run_all.py không kèm tùy chọn chạy toàn bộ pipeline từ đầu: tải dữ liệu thô bằng "
         "00_download_data.py và 00_download_data_2022_2023.py, dựng Bronze, Silver, Gold, các thực nghiệm hiệu năng, Spark, quản trị "
         "dữ liệu và mọi phân tích. Các tệp run_all.py và tệp tải dữ liệu chạy được trên Windows, macOS và Linux.")
    rp.H2("I.3. Danh mục tệp mã nguồn")
    code_dir = R.root / "code"
    files = ["config.py", "00_download_data.py", "00_download_data_2022_2023.py", "01_bronze_catalog.py", "02_zone_dimension.py",
             "03_silver_gold_month.py", "04_gold_consolidate.py", "05_benchmark.py", "panels.py", "causal.py", "viz.py",
             "06_eda.py", "07_did_main.py", "08_synthetic_control.py", "09_dml_heterogeneity.py", "10_spillover_robustness.py",
             "11_appendix_tables.py", "12_pipeline_figures.py", "13_build_report.py", "14_extra_analysis.py",
             "15_spark_pipeline.py", "15b_compare_outputs.py", "16_governance_risk.py", "17_business_analytics.py",
             "18_theory_sensitivity.py", "19_long_preperiod.py", "20_inference_robustness.py", "run_all.py", "run_all.sh",
             "requirements.txt"]
    q3 = chr(34) * 3
    rows, total = [], 0
    for fn in files:
        p = code_dir / fn
        if not p.exists():
            continue
        txt = p.read_text(encoding="utf-8")
        total += len(txt.splitlines())
        doc = ""
        if fn.endswith(".py") and txt.lstrip().startswith(q3):
            doc = txt.lstrip()[3:].split("\n")[0].strip().rstrip(".")
        elif fn.endswith(".sh"):
            doc = "Bản bash tương đương của run_all.py"
        elif fn == "requirements.txt":
            doc = "Danh sách thư viện Python và phiên bản"
        rows.append((fn, doc, vint(len(txt.splitlines()))))
    rp.TAB(pd.DataFrame(rows, columns=["Tệp", "Nội dung", "Số dòng"]), "Danh mục tệp mã nguồn trong thư mục code/",
           widths=[4.6, 9.8, 1.6], size=9, align=["left", "left", "center"], source="Nguồn: kho GitHub, thư mục code/.")
    rp.P(f"Tổng cộng {vint(total)} dòng mã trong {len(rows)} tệp, chưa kể {len(list((code_dir / 'report').glob('*.py')))} tệp "
         "dựng báo cáo trong code/report/. Toàn văn mã nguồn được lưu trên kho GitHub thay vì in trong báo cáo.")


GITHUB_URL = "https://github.com/C2561125-NguyenDinh/BigData_CuoiKy"


def _link(rp, url):
    """Đoạn chứa một siêu liên kết ngoài có thể bấm được."""
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.opc.constants import RELATIONSHIP_TYPE as RT
    from docx.shared import Cm
    p = rp.doc.add_paragraph()
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.left_indent = Cm(1.0)
    rid = rp.doc.part.relate_to(url, RT.HYPERLINK, is_external=True)
    h = OxmlElement("w:hyperlink")
    h.set(qn("r:id"), rid)
    r = OxmlElement("w:r")
    rpr = OxmlElement("w:rPr")
    for tag, val in (("w:color", "1F4E9A"), ("w:u", "single")):
        e = OxmlElement(tag)
        e.set(qn("w:val"), val)
        rpr.append(e)
    r.append(rpr)
    t = OxmlElement("w:t")
    t.text = url
    r.append(t)
    h.append(r)
    p._p.append(h)
    return p


def build(rp, R):
    _zone_profiles(rp, R)
    _all_zones(rp, R)
    _months(rp, R)
    _flows(rp, R)
    _events(rp, R)
    _scm(rp, R)
    _files(rp, R)
    _logs(rp, R)
    _code(rp, R)
