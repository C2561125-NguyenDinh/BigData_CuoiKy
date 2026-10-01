"""Chương 4. Kết quả thực nghiệm và phân tích."""
import numpy as np
import pandas as pd

from lib import pval, stars, vint, vn
from results import pct_log

SPEC_ORDER = ["TWFE", "DDD mùa vụ", "TWFE có trọng số", "TWFE + xu hướng nhóm"]
GL = {"CRZ": "CRZ", "CRZ_PARTIAL": "Vắt ranh giới", "MN_NORTH": "Manhattan phía bắc", "OUTER": "Quận ngoài",
      "AIRPORT": "Sân bay"}


def cse(b, se, p, d=3, scale=1.0):
    return f"{vn(scale * b, d)}{stars(p)} ({vn(scale * se, d)})"


def did_table(R, service, outcomes, sample="vùng×tuần"):
    d = R.t("t30")
    d = d[(d.service == service) & (d["sample"] == sample)]
    rows = []
    for y in outcomes:
        s = d[d.outcome == y]
        if s.empty:
            continue
        row = {"Biến kết quả": s.outcome_label.iloc[0]}
        pre = s.treated_pre_mean.iloc[0]
        row["TB nhóm xử lý trước"] = vn(pre, 2) if y != "ln_n" else "–"
        for sp in SPEC_ORDER:
            r = s[s.spec == sp]
            if r.empty:
                row[sp] = "–"
                continue
            r = r.iloc[0]
            row[sp] = cse(r.coef, r.se, r.p, 3)
        rows.append(row)
    return pd.DataFrame(rows)


def build(rp, R):
    meta = R.J["07_did_main"]
    zw = meta["hv_zone_week"]
    rp.H1("CHƯƠNG 4. KẾT QUẢ THỰC NGHIỆM VÀ PHÂN TÍCH")
    rp.P("Chương này trình bày kết quả theo thứ tự của câu hỏi nghiên cứu. Mục 4.1 báo cáo hiệu năng của pipeline (RQ1). Các "
         "mục 4.2 đến 4.4 mô tả dữ liệu sau xử lý. Các mục 4.5 đến 4.12 trình bày ước lượng nhân quả về số chuyến, tốc độ, thời "
         "gian chờ (RQ2, RQ3), giá và thu nhập như phép kiểm tra phương pháp, tác động không đồng nhất và lan tỏa (RQ4). Mục 4.13 và 4.14 là các phép thử độ "
         "tin cậy. Mục 4.15 đối chiếu kết quả với các giả thuyết lý thuyết của mục 2.11, và mục 4.16 tổng hợp kết quả theo câu hỏi nghiên cứu.")

    # ================================================================ 4.1
    fm = R.t("t09")
    en = R.t("t10")
    pr = R.t("t11")
    rg = R.t("t12")
    rp.H2("4.1. Hiệu năng của pipeline dữ liệu lớn")
    rp.H3("4.1.1. Định dạng lưu trữ")
    csv = fm[fm.format == "CSV"].iloc[0]
    zs = fm[fm.format == "Parquet ZSTD"].iloc[0]
    sn = fm[fm.format == "Parquet Snappy"].iloc[0]
    gz = fm[fm.format == "CSV.gz"].iloc[0]
    t = pd.DataFrame({"Định dạng": fm.format, "Dung lượng (MB)": fm.size_mb.map(lambda v: vn(v, 1)),
                      "So với CSV": fm.size_ratio_vs_csv.map(lambda v: vn(v, 3)),
                      "Thời gian ghi (s)": fm.write_s.map(lambda v: vn(v, 1)),
                      "Truy vấn – trung vị (s)": fm.agg_query_s_median.map(lambda v: vn(v, 3)),
                      "Truy vấn – min–max (s)": [f"{vn(a, 3)} – {vn(b, 3)}" for a, b in zip(fm.agg_query_s_min, fm.agg_query_s_max)]})
    rp.TAB(t, f"So sánh bốn định dạng lưu trữ trên {vint(csv.rows)} dòng HVFHV tháng 03/2024",
           widths=[3.0, 2.6, 2.2, 2.6, 2.8, 2.8], size=10.5)
    rp.FIG(R.fig("f35"), "Dung lượng tệp và thời gian truy vấn tổng hợp theo định dạng lưu trữ")
    rp.PS(
        f"Parquet ZSTD chiếm {vn(zs.size_mb, 1)} MB, bằng {vn(100 * zs.size_ratio_vs_csv, 1)}% dung lượng CSV không nén "
        f"({vn(csv.size_mb, 1)} MB). Nén gzip đưa CSV xuống {vn(gz.size_mb, 1)} MB, tức vẫn lớn hơn Parquet ZSTD "
        f"{vn(gz.size_mb / zs.size_mb, 2)} lần. Khác biệt lớn hơn nằm ở thời gian truy vấn: cùng một phép tổng hợp theo vùng đón "
        f"mất {vn(csv.agg_query_s_median, 2)} giây trên CSV nhưng chỉ {vn(zs.agg_query_s_median, 2)} giây trên Parquet ZSTD, "
        f"nhanh hơn {vn(csv.agg_query_s_median / zs.agg_query_s_median, 1)} lần. Lý do là truy vấn chỉ cần hai cột trong khi CSV "
        f"buộc phải đọc và phân tích cú pháp toàn bộ dòng.",
        f"Giữa hai kiểu nén của Parquet, ZSTD nhỏ hơn Snappy {vn(100 * (1 - zs.size_mb / sn.size_mb), 1)}% còn thời gian truy vấn "
        f"gần như tương đương ({vn(zs.agg_query_s_median, 3)} và {vn(sn.agg_query_s_median, 3)} giây). Kết quả này là cơ sở để lớp "
        f"Silver chọn ZSTD. Thời gian ghi CSV ({vn(csv.write_s, 1)} giây) lâu hơn Parquet ZSTD ({vn(zs.write_s, 1)} giây) cũng vì "
        f"CSV phải chuyển mọi giá trị sang dạng văn bản.")
    rp.H3("4.1.2. Bộ máy xử lý")
    t2 = pd.DataFrame({"Bộ máy": en.engine, "Trung vị (s)": en.seconds_median.map(lambda v: vn(v, 2)),
                       "Nhanh nhất – chậm nhất (s)": [f"{vn(a, 2)} – {vn(b, 2)}" for a, b in zip(en.seconds_min, en.seconds_max)],
                       "Bộ nhớ đỉnh (MB)": en.max_rss_mb.map(lambda v: vn(v, 0)), "Số nhóm": en.groups.map(vint)})
    rp.TAB(t2, "So sánh ba bộ máy xử lý trên cùng truy vấn tổng hợp một tháng HVFHV", widths=[5.4, 2.4, 3.4, 2.6, 2.2], size=10.5)
    rp.FIG(R.fig("f36"), "Thời gian và bộ nhớ đỉnh của ba bộ máy xử lý")
    ddb = en[en.engine.str.startswith("DuckDB")].iloc[0]
    pdn = en[en.engine.str.startswith("Pandas")].iloc[0]
    pya = en[en.engine.str.startswith("PyArrow")].iloc[0]
    rp.PS(
        f"Ba bộ máy cho cùng {vint(ddb.groups)} nhóm kết quả. Về thời gian, PyArrow ({vn(pya.seconds_median, 2)} giây) và DuckDB "
        f"({vn(ddb.seconds_median, 2)} giây) tương đương, pandas chậm hơn ({vn(pdn.seconds_median, 2)} giây) và dao động mạnh "
        f"giữa các lần chạy. Khác biệt quyết định là bộ nhớ: DuckDB chỉ dùng {vn(ddb.max_rss_mb, 0)} MB vì xử lý luồng theo lô và "
        f"không giữ toàn bộ cột trong bộ nhớ, trong khi PyArrow cần {vn(pya.max_rss_mb, 0)} MB và pandas cần {vn(pdn.max_rss_mb, 0)} "
        f"MB, tức gấp {vn(pdn.max_rss_mb / ddb.max_rss_mb, 1)} lần DuckDB. Trên máy khoảng 3 GB RAM, pandas chỉ xử lý được vài "
        f"tháng cùng lúc trước khi hết bộ nhớ, còn DuckDB có thể xử lý toàn bộ nhờ cơ chế tràn đĩa.",
        "Kết quả này giải thích lựa chọn kiến trúc của đồ án: DuckDB đảm nhận toàn bộ các bước nặng (Silver, Gold), còn pandas chỉ "
        "được dùng ở bước phân tích trên các bảng Gold nhỏ.")
    rp.H3("4.1.3. Cắt tỉa cột và đẩy điều kiện lọc")
    t3 = pd.DataFrame({"Phép thử": pr.test, "Trung vị (s)": pr.seconds_median.map(lambda v: vn(v, 3)),
                       "Bộ nhớ đỉnh (MB)": pr.max_rss_mb.map(lambda v: vn(v, 0)), "Giá trị đầu tiên trả về": pr.first_value})
    rp.TAB(t3, "Tác động của cắt tỉa cột và đẩy điều kiện lọc trong DuckDB (1 tháng HVFHV)", widths=[7.4, 2.4, 2.6, 3.6],
           size=10.5, align=["left", "center", "center", "center"])
    a, b, c, d = pr.iloc[0], pr.iloc[1], pr.iloc[2], pr.iloc[3]
    rp.PS(
        f"Đọc toàn bộ 24 cột mất {vn(b.seconds_median, 2)} giây, gấp {vn(b.seconds_median / a.seconds_median, 1)} lần so với chỉ "
        f"đọc hai cột ({vn(a.seconds_median, 2)} giây). Đây là lợi ích trực tiếp của lưu trữ dạng cột. Khi thêm điều kiện lọc một "
        f"ngày trên cột thời gian đón, truy vấn còn nhanh hơn nữa ({vn(c.seconds_median, 3)} giây) vì thời gian đón trong tệp TLC "
        f"gần như tăng dần: mỗi trong số {len(rg)} row group có khoảng thời gian đón hẹp, nên DuckDB bỏ qua được phần lớn row group "
        f"nhờ thống kê min/max. Ngược lại, lọc theo vùng đón ({vn(d.seconds_median, 3)} giây) không nhanh hơn đáng kể so với đọc hai "
        f"cột, vì mọi row group đều chứa đủ các vùng.",
        "Hàm ý thực tiễn là thứ tự sắp xếp dữ liệu khi ghi quyết định hiệu quả của đẩy điều kiện lọc. Lớp Silver được phân vùng theo "
        "tháng và giữ thứ tự thời gian bên trong, phù hợp với các truy vấn theo thời gian là loại truy vấn chính của đồ án.")
    rp.H3("4.1.4. Tổng hợp về RQ1")
    tot = R.t("t52")
    rp.P(f"Toàn bộ {vint(R.t('t03').total_rows.sum())} bản ghi được xử lý từ Bronze đến Gold trong "
         f"{vn(tot.sec_total.sum() / 60, 1)} phút thời gian tính toán trên 2 lõi CPU, với bộ nhớ DuckDB không vượt 1,8 GB. Trong các "
         f"lựa chọn thiết kế, định dạng cột nén ZSTD và bộ máy thực thi vector hóa có giới hạn bộ nhớ là hai yếu tố làm cho việc này "
         f"khả thi. Việc chia tháng thành khúc làm tăng số phân vùng nhưng không làm tăng tổng thời gian, vì thời gian tăng gần tuyến "
         f"tính theo số dòng. Chương 5 so sánh thêm với Apache Spark trên cùng dữ liệu và cùng phần cứng.")

    # ================================================================ 4.2
    rp.H2("4.2. Mô tả dữ liệu sau xử lý")
    rp.H3("4.2.1. Chỉ tiêu mô tả theo nhóm vùng")
    d26 = R.t("t26")
    d26 = d26[d26.grp.isin(["CRZ", "CRZ_PARTIAL", "MN_NORTH", "OUTER", "AIRPORT"])].copy()
    d26["Nhóm"] = d26.grp.map(GL)
    t4 = pd.DataFrame({"Nhóm vùng đón": d26["Nhóm"], "Năm": d26.yr.astype(int).astype(str),
                       "Chuyến/ngày": d26.trips_per_day.map(vint), "Giá cước/chuyến": d26.fare_per_trip.map(lambda v: vn(v, 2)),
                       "TN tài xế/chuyến": d26.pay_per_trip.map(lambda v: vn(v, 2)), "Dặm/chuyến": d26.miles_per_trip.map(lambda v: vn(v, 2)),
                       "Phút/chuyến": d26.min_per_trip.map(lambda v: vn(v, 1)), "Dặm/giờ": d26.mph.map(lambda v: vn(v, 2)),
                       "Chờ (phút)": d26.wait_min.map(lambda v: vn(v, 2)), "Phí CBD/chuyến": d26.cbd_per_trip.map(lambda v: vn(v, 3))})
    rp.TAB(t4, "Chỉ tiêu mô tả chuyến HVFHV theo nhóm vùng đón và năm", widths=[2.8, 1.2, 1.8, 1.6, 1.6, 1.4, 1.4, 1.4, 1.4, 1.6],
           size=9.5)
    c24 = lambda col: R.desc("CRZ", 2024, col)
    c25 = lambda col: R.desc("CRZ", 2025, col)
    o24 = lambda col: R.desc("OUTER", 2024, col)
    o25 = lambda col: R.desc("OUTER", 2025, col)
    rp.PS(
        f"Các vùng CRZ là thị trường đậm đặc nhất tính theo diện tích. Năm 2024, bình quân mỗi ngày có {vint(c24('trips_per_day'))} "
        f"chuyến HVFHV đón khách trong CRZ, so với {vint(o24('trips_per_day'))} chuyến ở toàn bộ các quận ngoài, dù diện tích quận "
        f"ngoài lớn hơn hàng chục lần. Chuyến đón trong CRZ ngắn hơn về quãng đường ({vn(c24('miles_per_trip'), 2)} so với "
        f"{vn(o24('miles_per_trip'), 2)} dặm) nhưng đắt hơn ({vn(c24('fare_per_trip'), 2)} so với {vn(o24('fare_per_trip'), 2)} "
        f"USD giá cước cơ sở) và chậm hơn rõ rệt ({vn(c24('mph'), 2)} so với {vn(o24('mph'), 2)} dặm/giờ).",
        f"Sang năm 2025, số chuyến/ngày đón trong CRZ giảm xuống {vint(c25('trips_per_day'))} "
        f"({vn(100 * (c25('trips_per_day') / c24('trips_per_day') - 1), 1)}%), trong khi ở quận ngoài tăng lên "
        f"{vint(o25('trips_per_day'))} ({vn(100 * (o25('trips_per_day') / o24('trips_per_day') - 1), 1)}%). Tốc độ trung bình trong CRZ "
        f"tăng từ {vn(c24('mph'), 2)} lên {vn(c25('mph'), 2)} dặm/giờ, còn ở quận ngoài giảm từ {vn(o24('mph'), 2)} xuống "
        f"{vn(o25('mph'), 2)}. Thời gian chờ trong CRZ giảm từ {vn(c24('wait_min'), 2)} xuống {vn(c25('wait_min'), 2)} phút. Phí CBD "
        f"trung bình trên mỗi chuyến đón trong CRZ năm 2025 là {vn(c25('cbd_per_trip'), 3)} USD, sát mức 1,50 USD vì gần như mọi "
        f"chuyến đón trong CRZ đều bị tính phí. Đây là các so sánh thô trước – sau; phần nhân quả ở các mục sau sẽ tách chúng khỏi "
        f"xu hướng chung.")
    rp.H3("4.2.2. Taxi vàng")
    d27 = R.t("t27")
    y = lambda g, yr, col: float(d27[(d27.grp == g) & (d27.yr == yr)][col].iloc[0])
    rp.PS(
        f"Taxi vàng có cấu trúc không gian khác hẳn: năm 2024 có {vint(y('CRZ', 2024, 'trips'))} chuyến đón trong CRZ nhưng chỉ "
        f"{vint(y('OUTER', 2024, 'trips'))} chuyến đón ở quận ngoài. Năm 2025, số chuyến taxi vàng đón trong CRZ tăng lên "
        f"{vint(y('CRZ', 2025, 'trips'))} ({vn(100 * (y('CRZ', 2025, 'trips') / y('CRZ', 2024, 'trips') - 1), 1)}%), còn ở quận ngoài "
        f"tăng lên {vint(y('OUTER', 2025, 'trips'))}, tức hơn gấp đôi.")
    vd = R.t("t27b")
    vp = vd[vd.pu_grp.isin(["CRZ", "MN_NORTH", "OUTER"])].pivot_table(index=["vendor", "pu_grp"], columns="yr", values="n",
                                                                         aggfunc="sum").fillna(0).reset_index()
    vp["chg"] = 100 * (vp[2025] / vp[2024].replace(0, np.nan) - 1)
    rp.TAB(pd.DataFrame({"VendorID": vp.vendor.map(vint), "Nhóm vùng đón": vp.pu_grp.map(GL),
                         "2024": vp[2024].map(vint), "2025": vp[2025].map(vint),
                         "Thay đổi (%)": vp.chg.map(lambda v: vn(v, 1))}),
           "Số chuyến taxi vàng (dữ liệu thô) theo nhà cung cấp, nhóm vùng đón và năm", widths=[2.2, 4.2, 3.2, 3.2, 3.2],
           size=10.5, source="Nguồn: t27b_yellow_vendor_by_year_group.csv, tính trực tiếp từ lớp Bronze.")
    v = lambda ven, g, yr: float(vp[(vp.vendor == ven) & (vp.pu_grp == g)][yr].iloc[0])
    rp.PS(
        f"Bảng trên cho thấy mức tăng ở quận ngoài đến chủ yếu từ hai nhà cung cấp chính: VendorID 2 tăng từ "
        f"{vint(v(2, 'OUTER', 2024))} lên {vint(v(2, 'OUTER', 2025))} chuyến, VendorID 1 từ {vint(v(1, 'OUTER', 2024))} lên "
        f"{vint(v(1, 'OUTER', 2025))}. Hai nhà cung cấp mới (VendorID 6 và 7) có xuất hiện nhiều hơn năm 2025 nhưng quy mô ở quận "
        f"ngoài nhỏ. Dữ liệu không cho biết nguyên nhân của mức tăng này. Điều chắc chắn là nó không liên quan trực tiếp đến CRZ và "
        f"làm cho các vùng quận ngoài không còn là đối chứng phù hợp cho taxi vàng. Đồ án vì vậy chỉ dùng Manhattan phía bắc làm "
        f"nhóm đối chứng chính cho taxi vàng và báo cáo đặc tả gồm quận ngoài như một phép thử độ nhạy.")

    # ================================================================ 4.3
    rp.H2("4.3. Diễn biến theo thời gian")
    rp.H3("4.3.1. Số chuyến theo ngày")
    lf05 = rp.FIG(R.fig("f05"), "Số chuyến HVFHV theo nhóm vùng đón, trung bình trượt 7 ngày, 01/2024 – 12/2025")
    rp.PS(
        f"{lf05} cho thấy nhịp mùa vụ rõ rệt ở cả ba nhóm: số chuyến giảm vào tuần lễ Tạ ơn và tuần cuối năm, tăng mạnh vào đầu "
        "tháng 12, giảm nhẹ vào mùa hè. Mùa vụ của CRZ mạnh hơn quận ngoài, đặc biệt là cú sụt vào tuần cuối năm khi văn phòng đóng "
        "cửa. Chính loại khác biệt này làm so sánh đơn giản trước – sau và giả định xu hướng song song kém tin cậy. "
        "Ngay sau ngày 05/01/2025, đường CRZ không có bước nhảy lớn; thay đổi thể hiện rõ hơn khi so sánh cùng kỳ.")
    rp.H3("4.3.2. Tăng trưởng cùng kỳ theo tuần")
    yy = R.t("t15")
    rp.FIG(R.fig("f06"), "Tăng trưởng cùng kỳ số chuyến HVFHV theo tuần ISO, 2025 so với 2024")
    neg = int((yy.CRZ < yy.OUTER).sum())
    rp.PS(
        f"So sánh cùng tuần giữa hai năm loại bỏ phần lớn mùa vụ. Trung bình qua {len(yy)} tuần ISO, số chuyến đón trong CRZ thay đổi "
        f"{vn(yy.CRZ.mean(), 2)}% so với cùng kỳ, Manhattan phía bắc {vn(yy.MN_NORTH.mean(), 2)}% và quận ngoài "
        f"{vn(yy.OUTER.mean(), 2)}%. Trong {neg}/{len(yy)} tuần, tăng trưởng của CRZ thấp hơn quận ngoài. Khoảng cách xấp xỉ "
        f"{vn(yy.OUTER.mean() - yy.CRZ.mean(), 1)} điểm phần trăm này là ước lượng thô đầu tiên về tác động, trước khi kiểm soát "
        f"các yếu tố khác. Manhattan phía bắc nằm ở giữa, gợi ý rằng khu vực này cũng chịu ảnh hưởng một phần.")
    rp.H3("4.3.3. Bản đồ thay đổi cùng kỳ")
    zz = R.t("t25")
    rp.FIG(R.fig("f16"), "Thay đổi cùng kỳ số chuyến HVFHV theo vùng đón (05/01 – 31/12), 2025 so với 2024", width_cm=13.5)
    zg = zz.groupby("grp").yoy_pct.agg(["count", "mean", "median", "min", "max"]).reset_index()
    zg = zg[zg.grp.isin(GL)]
    rp.TAB(pd.DataFrame({"Nhóm": zg.grp.map(GL), "Số vùng": zg["count"].map(vint), "Trung bình (%)": zg["mean"].map(lambda v: vn(v, 2)),
                         "Trung vị (%)": zg["median"].map(lambda v: vn(v, 2)), "Thấp nhất (%)": zg["min"].map(lambda v: vn(v, 2)),
                         "Cao nhất (%)": zg["max"].map(lambda v: vn(v, 2))}),
           "Phân bố thay đổi cùng kỳ số chuyến đón theo vùng (vùng có ít nhất 5.000 chuyến năm 2024)",
           widths=[4, 2, 2.5, 2.5, 2.5, 2.5], size=10.5)
    crz = zz[zz.grp == "CRZ"]
    rp.P(f"Bản đồ cho thấy một mẫu hình không gian rất rõ: gần như toàn bộ Manhattan có màu xanh (giảm), còn phần lớn các quận "
         f"ngoài có màu đỏ (tăng). Trong {len(crz)} vùng CRZ, {int((crz.yoy_pct < 0).sum())} vùng giảm, mức giảm trung vị "
         f"{vn(-crz.yoy_pct.median(), 2)}%. Các vùng Manhattan phía bắc giáp ranh giới cũng giảm, trong khi các vùng xa hơn ở phía "
         f"bắc đảo gần như không đổi. Mẫu hình này là gợi ý đầu tiên về hiệu ứng lan tỏa được phân tích ở mục 4.11.")
    rp.H3("4.3.4. So sánh HVFHV và taxi vàng trong CRZ")
    lf17 = rp.FIG(R.fig("f17"), "Chỉ số số chuyến đón trong CRZ theo tuần, HVFHV và taxi vàng (trung bình tuần năm 2024 = 100)")
    ix = R.t("t28")
    ix["week"] = pd.to_datetime(ix.iloc[:, 0])
    post = ix[ix.week >= "2025-01-05"]
    rp.P(f"Trong CRZ, chỉ số của taxi vàng giai đoạn sau chính sách có trung bình {vn(post.yellow.mean(), 1)}, còn HVFHV là "
         f"{vn(post.hvfhv.mean(), 1)}. Hai dịch vụ có mùa vụ giống nhau trong năm 2024 nhưng tách ra sau ngày 05/01/2025: taxi vàng, "
         f"với mức phí thấp bằng một nửa, không giảm như HVFHV. Đây là bằng chứng mô tả về sự thay thế một phần từ gọi xe sang taxi "
         f"trong vùng chịu phí.")

    # ================================================================ 4.4
    rp.H2("4.4. Doanh thu phí, cấu trúc luồng và nhịp theo giờ")
    rp.H3("4.4.1. Phí CBD ghi nhận trong dữ liệu")
    rev = R.t("t16")
    rp.FIG(R.fig("f07"), "Tổng phí CBD ghi nhận trong dữ liệu chuyến đi theo tháng và dịch vụ, năm 2025")
    rv = rev.pivot(index="ym", columns="service", values=["cbd", "share_charged", "avg_fee_charged"])
    trv = pd.DataFrame({"Tháng": rv.index,
                        "HVFHV (triệu USD)": rv[("cbd", "hvfhv")].map(lambda v: vn(v / 1e6, 2)),
                        "Taxi vàng (triệu USD)": rv[("cbd", "yellow")].map(lambda v: vn(v / 1e6, 2)),
                        "% chuyến HVFHV bị tính": rv[("share_charged", "hvfhv")].map(lambda v: vn(v, 1)),
                        "% chuyến taxi vàng bị tính": rv[("share_charged", "yellow")].map(lambda v: vn(v, 1)),
                        "Phí TB/chuyến bị tính HVFHV": rv[("avg_fee_charged", "hvfhv")].map(lambda v: vn(v, 3)),
                        "Phí TB taxi vàng": rv[("avg_fee_charged", "yellow")].map(lambda v: vn(v, 3))}).reset_index(drop=True)
    rp.TAB(trv, "Phí CBD ghi nhận trong dữ liệu theo tháng, năm 2025", widths=[1.8, 2.3, 2.3, 2.4, 2.4, 2.4, 2.4], size=9.5)
    hv = rev[rev.service == "hvfhv"]
    ye = rev[rev.service == "yellow"]
    rp.PS(
        f"Cộng cả năm, dữ liệu ghi nhận {vn(hv.cbd.sum() / 1e6, 2)} triệu USD phí CBD từ HVFHV và {vn(ye.cbd.sum() / 1e6, 2)} triệu "
        f"USD từ taxi vàng. Phí trung bình trên mỗi chuyến bị tính đúng bằng 1,50 USD với HVFHV và 0,75 USD với taxi vàng ở mọi "
        f"tháng, khớp với biểu phí của MTA và cho thấy phí được áp dụng liên tục suốt năm 2025. Khoảng {vn(100 * hv.n_cbd.sum() / hv.n.sum(), 1)}% "
        f"chuyến HVFHV và {vn(100 * ye.n_cbd.sum() / ye.n.sum(), 1)}% chuyến taxi vàng bị tính phí, phản ánh việc taxi vàng tập "
        f"trung ở Manhattan hơn nhiều so với HVFHV.",
        "Cần lưu ý rằng đây là phí ghi nhận trên hóa đơn chuyến đi, không phải số tiền MTA thực thu, vì đồ án không có dữ liệu đối "
        "soát giữa các hãng và MTA. Tuy vậy, con số cho thấy quy mô đáng kể của nguồn thu từ riêng hai dịch vụ này.")
    rp.H3("4.4.2. Cấu trúc luồng giữa các nhóm vùng")
    fs = R.t("t18")
    fs = fs[fs.pu_grp.isin(GL) & fs.do_grp.isin(GL)].copy()
    fs = fs.sort_values("2024", ascending=False).head(14)
    rp.TAB(pd.DataFrame({"Nhóm đón": fs.pu_grp.map(GL), "Nhóm trả": fs.do_grp.map(GL), "Tỷ trọng 2024 (%)": fs["2024"].map(lambda v: vn(v, 2)),
                         "Tỷ trọng 2025 (%)": fs["2025"].map(lambda v: vn(v, 2)), "Thay đổi (điểm %)": fs.change_pp.map(lambda v: vn(v, 2, sign=True))}),
           "Tỷ trọng các luồng chính trong tổng số chuyến HVFHV (14 luồng lớn nhất)", widths=[3.6, 3.6, 2.8, 2.8, 3.0], size=10.5,
           align=["left", "left", "center", "center", "center"])
    cc = R.t("t18")
    g = lambda a, b, c: float(cc[(cc.pu_grp == a) & (cc.do_grp == b)][c].iloc[0])
    rp.P(f"Luồng nội bộ CRZ (CRZ→CRZ) là luồng lớn thứ hai, chiếm {vn(g('CRZ', 'CRZ', '2024'), 2)}% tổng số chuyến năm 2024 và giảm "
         f"xuống {vn(g('CRZ', 'CRZ', '2025'), 2)}% năm 2025, mức giảm lớn nhất trong mọi luồng ({vn(g('CRZ', 'CRZ', 'change_pp'), 2)} "
         f"điểm phần trăm). Luồng giữa CRZ và Manhattan phía bắc theo cả hai chiều cũng giảm. Luồng nội bộ các quận ngoài tăng "
         f"{vn(g('OUTER', 'OUTER', 'change_pp'), 2)} điểm phần trăm. Luồng CRZ ra sân bay gần như không đổi, phù hợp với thực tế là "
         f"chuyến ra sân bay có giá cao và ít nhạy với một khoản phí nhỏ.")
    rp.H3("4.4.3. Nhịp theo giờ")
    rp.FIG(R.fig("f08"), "Số chuyến HVFHV có điểm đầu hoặc điểm cuối trong CRZ, trung bình theo giờ đón")
    hp = R.t("t19")
    hp["chg"] = 100 * (hp["2025"] / hp["2024"] - 1)
    worst = hp.sort_values("chg").head(3)
    best = hp.sort_values("chg").tail(3)
    rp.P(f"Số chuyến chạm CRZ giảm ở mọi giờ nhưng không đều. Mức giảm lớn nhất rơi vào khung đêm muộn: giờ "
         f"{', '.join(str(int(h)) for h in worst.hr)} giảm lần lượt {', '.join(vn(-v, 1) + '%' for v in worst.chg)}. Khung sáng "
         f"sớm và giờ đi làm buổi sáng giảm ít nhất (giờ {', '.join(str(int(h)) for h in best.hr)}: "
         f"{', '.join(vn(v, 1) + '%' for v in best.chg)}). Chuyến đi làm có ít phương án thay thế về thời gian, còn chuyến giải trí "
         f"buổi tối linh hoạt hơn.")
    rp.H3("4.4.4. Thị phần hãng")
    rp.FIG(R.fig("f15"), "Thị phần Uber theo tháng trên toàn thành phố và trong các chuyến chạm CRZ")
    cs = R.t("t23")
    pre_u = cs[cs.ym < "2025-01"].HV0003.mean()
    post_u = cs[cs.ym >= "2025-03"].HV0003.mean()
    rp.P(f"Thị phần Uber trung bình năm 2024 là {vn(pre_u, 1)}% và giảm xuống {vn(post_u, 1)}% trong giai đoạn 03–12/2025, phần còn "
         f"lại chủ yếu thuộc về Lyft. Sự thay đổi xảy ra từ tháng 03/2025, tức hai tháng sau khi phí có hiệu lực, và diễn ra tương "
         f"tự ở cả chuyến chạm CRZ lẫn toàn thành phố. Vì vậy khó quy nó cho phí CRZ; khả năng cao hơn là do chiến lược cạnh tranh "
         f"giữa hai hãng. Đồ án không đưa thay đổi này vào phần kết luận nhân quả, nhưng đây là một ví dụ về các cú sốc đồng thời mà "
         f"thiết kế đối chứng phải hấp thụ.")

    rp.H3("4.4.5. Luồng sân bay")
    af = R.t("t58")
    af = af[af.pu_grp.isin(GL) & af.do_grp.isin(GL)].copy()
    rp.TAB(pd.DataFrame({"Nhóm đón": af.pu_grp.map(GL), "Nhóm trả": af.do_grp.map(GL),
                         "Chuyến/ngày 2024": af["2024"].map(lambda v: vn(v, 0)), "Chuyến/ngày 2025": af["2025"].map(lambda v: vn(v, 0)),
                         "Thay đổi (%)": af.chg_pct.map(lambda v: vn(v, 2, sign=True))}),
           "Số chuyến HVFHV/ngày của các luồng có đầu sân bay (05/01 – 31/12)", widths=[3.6, 3.6, 2.9, 2.9, 3.0], size=10.5,
           align=["left", "left", "center", "center", "center"], source="Nguồn: t58_airport_flows.csv.")
    g_ = lambda a, b: af[(af.pu_grp == a) & (af.do_grp == b)].iloc[0]
    rp.P(f"Chuyến từ CRZ ra sân bay tăng {vn(g_('CRZ', 'AIRPORT').chg_pct, 2)}% và chuyến từ sân bay vào CRZ tăng "
         f"{vn(g_('AIRPORT', 'CRZ').chg_pct, 2)}%, trong khi các luồng sân bay với quận ngoài gần như không đổi hoặc giảm nhẹ. Luồng sân "
         f"bay là loại chuyến dài, giá cao (trên 50 USD giá cước cơ sở), nên khoản phí 1,50 USD chỉ chiếm vài phần trăm chi phí và "
         f"hành khách ít có phương án thay thế tiện lợi khi mang hành lý. Kết quả này là một phép thử tự nhiên cho lập luận về độ co "
         f"giãn: nơi phí chiếm tỷ trọng nhỏ, số chuyến gần như không phản ứng.")

    # ================================================================ 4.5
    rp.H2("4.5. Tác động lên số chuyến")
    rp.H3("4.5.1. Kết quả DiD trên panel vùng × tuần")
    tw = R.did("hvfhv", "ln_n")
    dd = R.did("hvfhv", "ln_n", "DDD mùa vụ")
    ww = R.did("hvfhv", "ln_n", "TWFE có trọng số")
    tr = R.did("hvfhv", "ln_n", "TWFE + xu hướng nhóm")
    t5 = did_table(R, "hvfhv", ["ln_n"])
    rp.TAB(t5, f"Tác động lên log số chuyến HVFHV đón theo bốn đặc tả (panel {zw['zones']} vùng × {zw['weeks']} tuần)",
           widths=[3.6, 1.6, 2.7, 2.7, 2.7, 2.7], size=10,
           source=f"Ghi chú: hệ số (sai số chuẩn phân cụm theo vùng, {zw['zones']} cụm); *** p<0,01; ** p<0,05; * p<0,1. "
                  "Nguồn: t30_did_main.csv.")
    rp.PS(
        f"Đặc tả TWFE cho hệ số {vn(tw.coef, 4)} với sai số chuẩn {vn(tw.se, 4)}, tương ứng số chuyến đón trong CRZ giảm "
        f"{vn(-pct_log(tw.coef), 2)}% so với phản thực. Khoảng tin cậy 95% là [{vn(-pct_log(tw.ci_high), 2)}%; "
        f"{vn(-pct_log(tw.ci_low), 2)}%] mức giảm. DDD mùa vụ, so sánh mỗi tuần năm 2025 với tuần cùng vị trí năm 2024, cho mức "
        f"giảm {vn(-pct_log(dd.coef), 2)}%, rất gần TWFE. Điều này cho thấy mùa vụ riêng của CRZ không làm lệch ước lượng trung "
        f"bình cả năm, dù nó ảnh hưởng mạnh đến từng tuần.",
        f"Khi có trọng số theo lưu lượng năm 2024, mức giảm còn {vn(-pct_log(ww.coef), 2)}%. Mức nhỏ hơn cho thấy các vùng CRZ có lưu "
        f"lượng lớn giảm ít hơn các vùng CRZ nhỏ về tỷ lệ phần trăm. Ước lượng không trọng số đại diện cho vùng, "
        f"ước lượng có trọng số đại diện cho chuyến đi.",
        f"Đặc tả có xu hướng tuyến tính riêng cho nhóm xử lý cho kết quả khác hẳn: hệ số {vn(tr.coef, 4)} (p = {pval(tr.p)}), tức không "
        f"có mức giảm. Đặc tả này không nên được đọc là bằng chứng ngược chiều. Như mục 4.13 sẽ cho thấy, khi áp dụng cùng đặc tả "
        f"cho một ngày chính sách giả trong năm 2024, nó cũng tạo ra các \"tác động\" lớn và có ý nghĩa thống kê, nghĩa là xu hướng "
        f"tuyến tính đang hấp thụ mùa vụ chứ không phải xu hướng thực. Với chỉ một năm trước chính sách, không thể tách xu hướng "
        f"dài hạn khỏi mùa vụ một cách đáng tin.")
    rp.H3("4.5.2. Nghiên cứu sự kiện theo tuần")
    ev = R.t("t31")
    evh = ev[(ev.service == "hvfhv") & (ev.spec == "TWFE")]
    lf19 = rp.FIG(R.fig("f19"), "Nghiên cứu sự kiện theo tuần cho log số chuyến HVFHV đón trong CRZ (chuẩn hóa theo trung bình 52 tuần trước)")
    pre = evh[evh.k < 0]
    postc = evh[evh.k >= 0]
    rp.PS(
        f"{lf19} trình bày hệ số theo tuần đã chuẩn hóa sao cho trung bình giai đoạn trước bằng 0. Trong giai đoạn trước, các hệ "
        f"số dao động quanh 0 với biên độ lớn quanh các dịp lễ (độ lệch chuẩn {vn(100 * pre.coef_c.std(), 2)} điểm log ×100), nhưng "
        f"không có xu hướng đơn điệu rõ ràng trong phần lớn năm. Kiểm định Wald chung bác bỏ giả thuyết mọi hệ số trước chính sách "
        f"bằng nhau (p {pval(evh.pretrend_p.iloc[0])}), điều dễ hiểu với sai số chuẩn rất nhỏ và mùa vụ lễ hội mạnh.",
        f"Sau chính sách, trung bình các hệ số tuần là {vn(100 * postc.coef_c.mean(), 2)} điểm log ×100, với "
        f"{int((postc.ci_high_c < 0).sum())}/{len(postc)} tuần có khoảng tin cậy nằm hoàn toàn dưới 0. Mức giảm xuất hiện ngay từ các "
        f"tuần đầu tiên và duy trì suốt năm, không có dấu hiệu mờ dần. Đây là động thái phù hợp với một cú sốc giá cố định.")
    lf21 = rp.FIG(R.fig("f21"), "Tác động theo tuần sau khi khử mùa vụ nhóm (DDD): so sánh từng tuần năm 2025 với tuần cùng vị trí năm 2024")
    evd = ev[(ev.service == "hvfhv") & (ev.spec == "DDD mùa vụ")]
    rp.P(f"{lf21} cho góc nhìn bổ sung: mỗi điểm là tác động của một tuần năm 2025 khi so với tuần tương ứng năm 2024. Với HVFHV, "
         f"{int((evd.coef < 0).sum())}/{len(evd)} tuần có hệ số âm, trung bình {vn(100 * evd.coef.mean(), 2)} điểm log ×100, và "
         f"{int((evd.ci_high < 0).sum())} tuần có khoảng tin cậy nằm hoàn toàn dưới 0. Đường của HVFHV nằm trong khoảng từ "
         f"{vn(100 * evd.coef.min(), 1)} đến {vn(100 * evd.coef.max(), 1)} điểm, khá ổn định.")
    evd2 = evd.copy()
    evd2["month"] = (pd.Timestamp("2025-01-05") + pd.to_timedelta(evd2.k * 7, unit="D")).dt.to_period("M").astype(str)
    mth = evd2.groupby("month").agg(coef=("coef", "mean"), n=("coef", "size"), neg=("coef", lambda v: int((v < 0).sum()))).reset_index()
    rp.TAB(pd.DataFrame({"Tháng": mth.month, "Số tuần": mth.n.map(vint), "TB hệ số DDD ×100": (100 * mth.coef).map(lambda v: vn(v, 2)),
                         "% thay đổi tương ứng": mth.coef.map(lambda v: vn(pct_log(v), 2)), "Số tuần hệ số âm": mth.neg.map(vint)}),
           "Trung bình hệ số DDD theo tháng của năm 2025 (HVFHV, log số chuyến đón)", widths=[2.6, 2.2, 3.6, 3.6, 3.2], size=10.5,
           source="Ghi chú: tuần được gán vào tháng của ngày bắt đầu tuần. Nguồn: t31_event_study_weekly_ln_n.csv.")
    rp.P(f"Tổng hợp theo tháng, tác động DDD thấp nhất vào tháng {mth.loc[mth.coef.idxmax(), 'month']} "
         f"({vn(pct_log(mth.coef.max()), 2)}%) và mạnh nhất vào tháng {mth.loc[mth.coef.idxmin(), 'month']} "
         f"({vn(pct_log(mth.coef.min()), 2)}%). Không tháng nào có tác động trung bình dương. Biến động giữa các tháng phản ánh một "
         f"phần sai lệch mùa vụ giữa hai năm (ví dụ vị trí của các ngày lễ trong tuần), nên không nên diễn giải từng tháng riêng lẻ.")

    rp.H3("4.5.3. Tỷ lệ yêu cầu đi chung")
    sh = R.did("hvfhv", "shared_pct")
    shd = R.did("hvfhv", "shared_pct", "DDD mùa vụ")
    rp.P(f"Tỷ lệ chuyến có yêu cầu đi chung trong các vùng CRZ trước chính sách là {vn(sh.treated_pre_mean, 2)}%. TWFE ước lượng tỷ lệ "
         f"này giảm {vn(-sh.coef, 3)} điểm phần trăm (sai số chuẩn {vn(sh.se, 3)}), DDD cho {vn(-shd.coef, 3)} điểm. So với mức nền, "
         f"đây là mức giảm tương đối khoảng {vn(-100 * sh.coef / sh.treated_pre_mean, 1)}%, lớn hơn nhiều so với mức giảm tổng số "
         f"chuyến. Kết quả cùng chiều với Pandey, Guler và Gayah (2026): phí tính theo chuyến chứ không theo hành khách làm chuyến "
         f"đi chung, vốn có giá thấp, chịu tỷ lệ tăng chi phí lớn hơn.")

    # ================================================================ 4.6
    rp.H2("4.6. Tác động lên tốc độ và thời gian chờ")
    rp.H3("4.6.1. Kết quả DiD")
    t6 = did_table(R, "hvfhv", ["mph", "wait", "miles_pt"])
    rp.TAB(t6, "Tác động lên tốc độ, thời gian chờ và quãng đường/chuyến (HVFHV, vùng × tuần)",
           widths=[3.6, 1.6, 2.7, 2.7, 2.7, 2.7], size=10,
           source="Ghi chú: như Bảng DiD số chuyến. Nguồn: t30_did_main.csv.")
    mp = R.did("hvfhv", "mph")
    mpd = R.did("hvfhv", "mph", "DDD mùa vụ")
    mpt = R.did("hvfhv", "mph", "TWFE + xu hướng nhóm")
    wt = R.did("hvfhv", "wait")
    wtd = R.did("hvfhv", "wait", "DDD mùa vụ")
    rp.PS(
        f"Tốc độ trung bình của chuyến đón trong CRZ tăng {vn(mp.coef, 3)} dặm/giờ theo TWFE và {vn(mpd.coef, 3)} dặm/giờ theo DDD, "
        f"trên mức nền {vn(mp.treated_pre_mean, 2)} dặm/giờ, tức tăng khoảng {vn(100 * mp.coef / mp.treated_pre_mean, 1)}%. Khác với "
        f"số chuyến, đặc tả có xu hướng nhóm cho mức tăng còn lớn hơn ({vn(mpt.coef, 3)} dặm/giờ), nên kết luận về tốc độ không phụ "
        f"thuộc vào cách xử lý xu hướng. Lưu ý tốc độ đo trên chuyến đón trong CRZ bao gồm cả đoạn đường ngoài vùng của các chuyến "
        f"đi ra ngoài; phần 4.6.3 xem riêng chuyến nội vùng.",
        f"Thời gian chờ giảm {vn(-wt.coef, 3)} phút theo TWFE và {vn(-wtd.coef, 3)} phút theo DDD, trên nền {vn(wt.treated_pre_mean, 2)} "
        f"phút, tức giảm khoảng {vn(-100 * wt.coef / wt.treated_pre_mean, 1)}%. Kết quả này phù hợp với cơ chế thị trường hai phía đã "
        f"nêu ở Chương 2: khi nhu cầu trong vùng giảm, xe rảnh nhiều hơn và thời gian ghép cặp ngắn lại. Tốc độ đường phố cao hơn "
        f"cũng rút ngắn thời gian xe chạy đến điểm đón.")
    rp.H3("4.6.2. Động thái theo tháng")
    lf22 = rp.FIG(R.fig("f22"), "Nghiên cứu sự kiện theo tháng cho sáu chỉ tiêu (HVFHV, panel vùng × tuần, chuẩn hóa theo trung bình 2024)",
           width_cm=15.5)
    em = R.t("t32")
    jump = em.groupby("outcome").jump_3v3.first()
    rp.PS(
        f"{lf22} cho thấy hai kiểu động thái khác nhau. Với tốc độ, các hệ số năm 2024 dao động quanh 0 và có một bước nhảy rõ "
        f"ngay tháng 01/2025; chênh lệch giữa trung bình ba tháng đầu sau và ba tháng cuối trước chính sách là "
        f"{vn(jump['mph'], 3)} dặm/giờ. Với thời gian chờ, bước nhảy là {vn(jump['wait'], 3)} phút. Đây là dạng động thái mà một cú "
        f"sốc chính sách thật sự tạo ra.",
        f"Với giá cước/dặm, thu nhập tài xế/dặm và chi phí hành khách/chuyến, hình ảnh hoàn toàn khác: các hệ số tăng đều đặn suốt "
        f"năm 2024 rồi tiếp tục xu hướng đó sang năm 2025, không có bước nhảy tại mốc chính sách. Chênh lệch ba tháng sau so với ba "
        f"tháng trước còn âm ({vn(jump['fare_pm'], 3)} USD/dặm với giá cước, {vn(jump['rider_pt'], 3)} USD/chuyến với chi phí hành "
        f"khách), vì quý IV/2024 là giai đoạn giá cao của mùa lễ. Như vậy, khoảng cách giá giữa CRZ và vùng đối chứng đã nới rộng từ "
        f"trước chính sách. Các hệ số DiD dương cho giá ở mục 4.7 phản ánh chủ yếu xu hướng này.")
    rp.H3("4.6.3. Tốc độ theo loại luồng và theo giờ")
    rp.FIG(R.fig("f10"), "Tốc độ trung bình theo tháng của ba loại luồng chuyến HVFHV")
    sm = R.t("t21")
    sm["d"] = sm.iloc[:, 0]
    c = sm.columns[1]
    jan24 = float(sm[sm.d == "2024-01"][c].iloc[0])
    jan25 = float(sm[sm.d == "2025-01"][c].iloc[0])
    dec24 = float(sm[sm.d == "2024-12"][c].iloc[0])
    rp.P(f"Chuyến nội vùng CRZ có tốc độ trung bình {vn(dec24, 2)} dặm/giờ vào tháng 12/2024 và tăng lên {vn(jan25, 2)} dặm/giờ vào "
         f"tháng 01/2025, cao hơn cả tháng 01/2024 ({vn(jan24, 2)} dặm/giờ). Hai luồng đối chứng không có bước nhảy tương tự. Sau "
         f"quý I/2025, tốc độ trong CRZ dần trở lại nhịp mùa vụ quen thuộc, giảm vào mùa thu và cuối năm, nhưng vẫn ở mức ngang hoặc "
         f"cao hơn cùng kỳ năm trước trong phần lớn các tháng.")
    rp.FIG(R.fig("f09"), "Tốc độ trung bình của chuyến HVFHV nội vùng CRZ theo giờ đón, năm 2024 và 2025")
    sp = R.t("t20")
    sp["chg"] = sp["2025"] - sp["2024"]
    rp.P(f"Theo giờ, tốc độ trung bình cả năm của chuyến nội vùng CRZ tăng nhiều nhất vào buổi chiều và tối "
         f"(từ 14 đến 18 giờ, mức tăng {vn(sp[(sp.hr >= 14) & (sp.hr <= 18)].chg.mean(), 2)} dặm/giờ), là khung giờ đông nhất và "
         f"chậm nhất. Vào đêm và rạng sáng, khi đường đã thông thoáng, tốc độ gần như không đổi. Mẫu hình này đúng như lý thuyết dự "
         f"báo: giảm lưu lượng có tác dụng lớn nhất khi đường gần mức bão hòa.")

    rp.H3("4.6.4. Tốc độ theo giờ và loại ngày")
    lf40 = rp.FIG(R.fig("f40"), "Chênh lệch thay đổi tốc độ cùng kỳ theo giờ và loại ngày: luồng CRZ→CRZ trừ luồng quận ngoài→quận ngoài")
    hd = R.t("t57")
    wd = hd[hd.daytype == "Ngày thường"]
    we_ = hd[hd.daytype == "Cuối tuần"]
    rp.PS(
        f"{lf40} là một sai khác kép mô tả ở cấp luồng: với mỗi giờ và loại ngày, lấy thay đổi tốc độ cùng kỳ của chuyến nội vùng "
        f"CRZ trừ đi thay đổi tương ứng của chuyến nội bộ quận ngoài. Vào ngày thường, chênh lệch dương ở hầu hết các giờ, lớn nhất "
        f"vào tối muộn (giờ 20–23: trung bình {vn(wd[wd.hr >= 20].did_vs_outer.mean(), 2)} dặm/giờ) và âm nhẹ vào khung 06–07 giờ. Vào "
        f"cuối tuần, chênh lệch dương ở mọi giờ, trung bình {vn(we_.did_vs_outer.mean(), 2)} dặm/giờ.",
        "Kết quả cuối tuần ở đây khác với tương tác D × cuối tuần trên panel vùng × ngày, vốn cho tốc độ cuối tuần gần như không đổi. "
        "Hai phép đo khác nhau về đối tượng: panel vùng × ngày tính mọi chuyến đón trong CRZ, kể cả chuyến đi ra quận ngoài qua cầu và "
        "đường cao tốc, còn hình này chỉ tính chuyến có cả hai đầu trong CRZ. Tốc độ trên đường phố nội vùng cuối tuần có cải thiện, "
        "nhưng phần đường ngoài vùng của chuyến đi ra ngoài thì không. Đây là ví dụ cho thấy việc chọn đơn vị đo ảnh hưởng thế nào đến "
        "kết luận về không đồng nhất.")

    # ================================================================ 4.7
    rp.H2("4.7. Giá cước, chi phí hành khách và thu nhập tài xế")
    rp.H3("4.7.1. Kết quả DiD")
    t7 = did_table(R, "hvfhv", ["fare_pm", "fare_pt", "rider_pt", "cbd_pt", "tips_pt", "pay_pm", "pay_pt", "pay_share"])
    rp.TAB(t7, "Tác động lên giá cước, chi phí hành khách và thu nhập tài xế (HVFHV, vùng × tuần)",
           widths=[3.6, 1.6, 2.7, 2.7, 2.7, 2.7], size=9.5,
           source="Ghi chú: như Bảng DiD số chuyến. Nguồn: t30_did_main.csv.")
    rt = R.did("hvfhv", "rider_pt")
    cb = R.did("hvfhv", "cbd_pt")
    fp = R.did("hvfhv", "fare_pt")
    fpt = R.did("hvfhv", "fare_pt", "TWFE + xu hướng nhóm")
    rp.PS(
        f"Phí CBD/chuyến của các vùng CRZ tăng {vn(cb.coef, 3)} USD, đúng với cơ chế phí: không phải mọi chuyến đón trong CRZ đều "
        f"bị tính trong mọi tuần (một phần nhỏ chuyến có dữ liệu phí bằng 0), nên mức trung bình thấp hơn 1,50 USD một chút. Tổng chi "
        f"phí hành khách/chuyến tăng {vn(rt.coef, 3)} USD theo TWFE, gấp {vn(rt.coef / cb.coef, 2)} lần mức phí. Giá cước cơ sở tăng "
        f"{vn(fp.coef, 3)} USD/chuyến, thu nhập tài xế tăng {vn(R.did('hvfhv', 'pay_pt').coef, 3)} USD/chuyến, còn tỷ lệ thu nhập tài "
        f"xế trên giá cước giảm {vn(-R.did('hvfhv', 'pay_share').coef, 2)} điểm phần trăm.",
        f"Nếu đọc các con số này như tác động nhân quả, ta sẽ kết luận rằng nền tảng đã tăng giá cước cơ sở trong CRZ cùng lúc với "
        f"phí, khiến hành khách chịu gần gấp đôi mức phí danh nghĩa, trong khi phần tăng thêm chủ yếu thuộc về nền tảng. Tuy nhiên, "
        f"kết luận này không đứng vững. Như {lf22} cho thấy, giá cước và chi phí hành khách của CRZ đã tăng nhanh hơn vùng đối chứng "
        f"trong suốt năm 2024. Khi cho phép xu hướng nhóm, dấu của tác động lên giá cước đảo ngược ({vn(fpt.coef, 3)} USD/chuyến). Phép "
        f"thử giả dược ở mục 4.13 còn cho thấy một \"tác động\" giả vào tháng 07/2024 có độ lớn tương đương. Vì vậy, đồ án không kết "
        f"luận về tác động của phí lên giá cước cơ sở và thu nhập tài xế.")
    rp.H3("4.7.2. Phân phối chi phí hành khách")
    rp.FIG(R.fig("f18"), "Phân phối tổng chi phí hành khách/chuyến từ mẫu 0,25% chuyến HVFHV, theo năm và loại chuyến")
    qq = R.t("t29")
    q = lambda tc, yr, col: float(qq[(qq.touch_crz == tc) & (qq.yr == yr)][col].iloc[0])
    rp.P(f"Trên mẫu {vint(R.J['06_eda']['n_sample_hvfhv'])} chuyến, trung vị chi phí của chuyến chạm CRZ tăng từ "
         f"{vn(q(1, 2024, '0.5'), 2)} lên {vn(q(1, 2025, '0.5'), 2)} USD, phân vị 90 tăng từ {vn(q(1, 2024, '0.9'), 2)} lên "
         f"{vn(q(1, 2025, '0.9'), 2)} USD. Với chuyến không chạm CRZ, trung vị gần như không đổi ({vn(q(0, 2024, '0.5'), 2)} và "
         f"{vn(q(0, 2025, '0.5'), 2)} USD). Toàn bộ phân phối của chuyến chạm CRZ dịch sang phải nhiều hơn mức phí, nhất quán với "
         f"bảng DiD, nhưng như đã phân tích, phần vượt mức phí không thể tách khỏi xu hướng có sẵn.")
    rp.H3("4.7.3. Diễn biến giá theo tháng")
    rp.FIG(R.fig("f11"), "Giá cước cơ sở trên mỗi dặm theo tháng, chuyến chạm CRZ và không chạm CRZ")
    rp.FIG(R.fig("f12"), "Thu nhập tài xế trên mỗi dặm theo tháng, chuyến chạm CRZ và không chạm CRZ")
    pp = R.t("t22")
    rp.P("Hai hình trên xác nhận trực quan kết luận của mục 4.7.1. Giá cước/dặm của chuyến chạm CRZ có xu hướng tăng và mùa vụ mạnh, "
         "với đỉnh vào tháng 12 của cả hai năm. Thu nhập tài xế/dặm của cả hai loại chuyến đi cùng nhau trong phần lớn thời gian, "
         "phản ánh công thức thu nhập tối thiểu do TLC quy định áp dụng chung cho mọi chuyến. Không có bước nhảy nào tại tháng "
         "01/2025 đủ lớn để tách khỏi dao động mùa vụ.")
    rp.FIG(R.fig("f13"), "Thời gian chờ từ lúc gọi xe đến lúc đón theo tháng, chuyến chạm CRZ và không chạm CRZ")
    rp.FIG(R.fig("f14"), "Tỷ lệ thu nhập tài xế trên giá cước cơ sở theo tháng")

    rp.H3("4.7.4. Thành phần quãng đường chuyến")
    lf41 = rp.FIG(R.fig("f41"), "Phân bố quãng đường chuyến HVFHV theo loại chuyến và năm (mẫu 0,25%, 05/01 – 31/12)")
    dc = R.t("t59")
    c_ = lambda tc, yr, col: float(dc[(dc.touch_crz == tc) & (dc.yr == yr)][col].iloc[0])
    rp.P(f"Một lo ngại khi so sánh giá và tốc độ trung bình là thành phần chuyến thay đổi: nếu chuyến ngắn giảm mạnh hơn, giá trung "
         f"bình mỗi chuyến tăng và tốc độ trung bình thay đổi mà không phản ánh thay đổi trên từng loại chuyến. {lf41} cho thấy thành "
         f"phần quãng đường của chuyến chạm CRZ thay đổi rất ít: tỷ trọng chuyến dưới 1 dặm từ {vn(c_(1, 2024, '<1'), 2)}% lên "
         f"{vn(c_(1, 2025, '<1'), 2)}%, chuyến 5–10 dặm từ {vn(c_(1, 2024, '5–10'), 2)}% lên {vn(c_(1, 2025, '5–10'), 2)}%. Thay đổi thành "
         f"phần vì vậy không đủ lớn để giải thích mức tăng giá cước/chuyến hay tốc độ. Điều này củng cố kết luận rằng mức tăng tốc độ là "
         f"thay đổi thực trên đường, còn mức tăng giá chủ yếu đến từ xu hướng giá có sẵn chứ không phải từ dịch chuyển thành phần.")

    # ================================================================ 4.8
    rp.H2("4.8. Phân tích trên panel cặp điểm đón – điểm trả")
    rp.H3("4.8.1. Tác động theo loại luồng")
    od = R.t("t35")
    flows = ["Tất cả chuyến chạm CRZ", "CRZ→CRZ", "CRZ→ngoài", "ngoài→CRZ"]
    lab = {"ln_n": "log số chuyến", "mph": "Tốc độ (dặm/giờ)", "shared_pct": "Tỷ lệ đi chung (%)", "fare_pt": "Giá cước/chuyến",
           "pay_pt": "TN tài xế/chuyến", "rider_pt": "Chi phí hành khách/chuyến", "cbd_pt": "Phí CBD/chuyến"}
    rows = []
    for y, l in lab.items():
        row = {"Biến kết quả": l}
        for f in flows:
            r = od[(od.flow == f) & (od.outcome == y)].iloc[0]
            row[f] = cse(r.coef, r.se, r.p, 3)
        rows.append(row)
    rp.TAB(pd.DataFrame(rows), "Tác động theo loại luồng trên panel cặp OD × tháng", widths=[3.6, 3.1, 3.1, 3.1, 3.1], size=10,
           source="Ghi chú: hiệu ứng cố định cặp và tháng; sai số chuẩn phân cụm theo vùng đón. Nhóm đối chứng là các cặp không chạm "
                  "CRZ. Nguồn: t35_did_od_pairs.csv.")
    a = R.od("Tất cả chuyến chạm CRZ", "ln_n")
    b1 = R.od("CRZ→CRZ", "ln_n")
    b2 = R.od("CRZ→ngoài", "ln_n")
    b3 = R.od("ngoài→CRZ", "ln_n")
    m1 = R.od("CRZ→CRZ", "mph")
    m2 = R.od("CRZ→ngoài", "mph")
    rp.PS(
        f"Trên panel cặp OD, số chuyến của các cặp chạm CRZ giảm {vn(-pct_log(a.coef), 2)}% so với các cặp không chạm, gần với ước "
        f"lượng trên panel vùng × tuần. Mức giảm lớn nhất thuộc luồng nội vùng CRZ→CRZ ({vn(-pct_log(b1.coef), 2)}%), tiếp theo là "
        f"ngoài→CRZ ({vn(-pct_log(b3.coef), 2)}%) và CRZ→ngoài ({vn(-pct_log(b2.coef), 2)}%). Luồng nội vùng gồm các chuyến ngắn, giá "
        f"thấp, nên khoản phí 1,50 USD chiếm tỷ lệ lớn nhất trong chi phí chuyến đi; các chuyến này cũng dễ được thay bằng đi bộ, xe "
        f"đạp hoặc tàu điện ngầm.",
        f"Tốc độ tăng ở mọi loại luồng, nhưng tăng ít nhất ở luồng nội vùng ({vn(m1.coef, 3)} dặm/giờ) và nhiều hơn ở luồng CRZ→ngoài "
        f"({vn(m2.coef, 3)} dặm/giờ). Một cách giải thích là chuyến đi ra ngoài có phần lớn quãng đường trên các trục chính và cầu, "
        f"nơi lưu lượng xe con cá nhân giảm mạnh nhờ phí ngày, còn chuyến nội vùng chịu nhiều ảnh hưởng của đèn tín hiệu và người đi "
        f"bộ, vốn không đổi.")
    rp.H3("4.8.2. Nghiên cứu sự kiện theo tháng trên panel OD")
    rp.FIG(R.fig("f24"), "Nghiên cứu sự kiện theo tháng trên panel cặp OD: log số chuyến của cặp chạm CRZ so với cặp không chạm")
    eo = R.t("t37")
    rp.P(f"Các hệ số năm 2024 dao động trong khoảng {vn(100 * eo[eo.k < 0].coef_c.min(), 1)} đến "
         f"{vn(100 * eo[eo.k < 0].coef_c.max(), 1)} điểm log ×100 quanh mức trung bình. Từ tháng 01/2025, các hệ số chuyển sang âm "
         f"và có xu hướng sâu thêm theo thời gian, đạt {vn(100 * eo[eo.k >= 0].coef_c.min(), 1)} điểm ở tháng thấp nhất. Mức giảm "
         f"sâu dần có thể phản ánh việc hành khách điều chỉnh thói quen từ từ, nhưng cũng có thể một phần là do xu hướng giảm có sẵn "
         f"của các cặp chạm CRZ; với một năm dữ liệu trước chính sách, hai giải thích này không tách được hoàn toàn.")

    # ================================================================ 4.9
    rp.H2("4.9. Tác động không đồng nhất theo thời gian trong ngày và trong tuần")
    rp.H3("4.9.1. Theo khung giờ")
    hh = R.t("t33")
    rows = []
    for hb in sorted(hh.hbin.unique()):
        row = {"Khung giờ": hb}
        for y, l in (("ln_n", "log số chuyến"), ("mph", "Tốc độ"), ("wait", "Thời gian chờ"), ("fare_pm", "Giá cước/dặm")):
            r = hh[(hh.hbin == hb) & (hh.outcome == y)].iloc[0]
            row[l] = cse(r.coef, r.se, r.p, 3)
        row["Tốc độ nền"] = vn(hh[(hh.hbin == hb) & (hh.outcome == "mph")].pre_mean.iloc[0], 2)
        rows.append(row)
    rp.TAB(pd.DataFrame(rows), "Tác động DiD theo khung giờ đón (panel vùng × khung giờ × tháng)",
           widths=[2.2, 3.0, 2.8, 2.8, 2.8, 2.4], size=10,
           source="Ghi chú: hiệu ứng cố định vùng và tháng, ước lượng riêng từng khung giờ; phân cụm theo vùng. Nguồn: t33.")
    rp.FIG(R.fig("f23"), "Tác động DiD theo khung giờ đón lên log số chuyến và tốc độ")
    h1 = R.hour("06–09", "ln_n")
    h0 = R.hour("00–05", "ln_n")
    h4 = R.hour("20–23", "ln_n")
    s1 = R.hour("06–09", "mph")
    s4 = R.hour("20–23", "mph")
    s3 = R.hour("16–19", "mph")
    rp.PS(
        f"Số chuyến giảm ít nhất vào khung 06–09 giờ ({vn(-pct_log(h1.coef), 2)}%) và nhiều nhất vào khung 00–05 giờ "
        f"({vn(-pct_log(h0.coef), 2)}%) và 20–23 giờ ({vn(-pct_log(h4.coef), 2)}%). Kết quả khớp với phân tích mô tả ở mục 4.4.3: "
        f"chuyến đi làm buổi sáng ít co giãn, chuyến buổi tối và đêm khuya linh hoạt hơn.",
        f"Tốc độ tăng mạnh nhất vào buổi chiều và tối (16–19 giờ: {vn(s3.coef, 3)}; 20–23 giờ: {vn(s4.coef, 3)} dặm/giờ) và gần như "
        f"không tăng vào khung 06–09 giờ ({vn(s1.coef, 3)} dặm/giờ, p = {pval(s1.p)}). Giờ cao điểm buổi sáng có dòng xe chủ yếu là "
        f"xe đi làm và xe giao hàng, ít phản ứng với phí; còn chiều tối là lúc giảm lưu lượng tạo ra khác biệt lớn nhất về tốc độ.")
    rp.H3("4.9.2. Ngày thường và cuối tuần")
    we = R.t("t34")
    rows = []
    for y, l in (("ln_n", "log số chuyến"), ("mph", "Tốc độ (dặm/giờ)"), ("wait", "Thời gian chờ (phút)"), ("fare_pm", "Giá cước/dặm")):
        s = we[we.outcome == y]
        a = s[s.term == "D"].iloc[0]
        b = s[s.term == "D_we"].iloc[0]
        rows.append({"Biến kết quả": l, "D (ngày thường)": cse(a.coef, a.se, a.p, 3), "D × cuối tuần": cse(b.coef, b.se, b.p, 3),
                     "Tổng cuối tuần": vn(a.coef + b.coef, 3)})
    rp.TAB(pd.DataFrame(rows), "Tác động theo ngày thường và cuối tuần (panel vùng × ngày)", widths=[4, 4, 4, 4], size=10.5,
           source="Ghi chú: hiệu ứng cố định vùng và ngày; phân cụm theo vùng. Nguồn: t34_heterogeneity_weekend.csv.")
    a = we[(we.outcome == "mph") & (we.term == "D")].iloc[0]
    b = we[(we.outcome == "mph") & (we.term == "D_we")].iloc[0]
    rp.P(f"Mức giảm số chuyến không khác biệt có ý nghĩa giữa ngày thường và cuối tuần. Tốc độ tăng {vn(a.coef, 3)} dặm/giờ vào ngày "
         f"thường, nhưng tương tác với cuối tuần là {vn(b.coef, 3)}, nên vào cuối tuần tốc độ gần như không đổi hoặc giảm nhẹ. Một "
         f"cách giải thích là đường phố cuối tuần vốn ít bão hòa hơn, nên giảm lưu lượng ít cải thiện tốc độ; ngoài ra thành phần "
         f"phương tiện vào vùng cuối tuần (khách du lịch, mua sắm) có thể ít nhạy với phí hơn ngày thường.")

    # ================================================================ 4.10
    rp.H2("4.10. Kiểm soát tổng hợp")
    sc = R.J["08_scm"]
    st = sc["standard"]
    wts = R.t("t38_scm_weights_standard")
    rp.FIG(R.fig("f25"), "Kiểm soát tổng hợp: chỉ số số chuyến HVFHV đón trong CRZ thực tế và tổng hợp, cùng khoảng cách giữa hai chuỗi")
    top = wts[wts.weight > 0.001].copy()
    rp.TAB(pd.DataFrame({"Mã vùng": top.zone.map(vint), "Tên vùng": top.Zone, "Quận": top.Borough, "Nhóm": top.grp.map(GL),
                         "Trọng số": top.weight.map(lambda v: vn(v, 3))}),
           "Các vùng có trọng số dương trong CRZ tổng hợp", widths=[2, 5.4, 2.8, 3.4, 2.4], size=10.5,
           align=["center", "left", "left", "left", "center"])
    rp.PS(
        f"Tối ưu hóa chọn {st['n_donors_positive']} vùng đối chứng với trọng số dương, trong đó năm vùng có trọng số lớn nhất là "
        f"{', '.join(top.Zone.head(5))} ({vn(100 * top.weight.head(5).sum(), 1)}% tổng trọng số). Đây là các vùng đô thị đậm đặc có nhịp mùa vụ gần CRZ nhất. RMSPE giai đoạn "
        f"trước là {vn(st['rmspe_pre'], 4)} (trên thang chỉ số bằng 1), tức sai số khớp khoảng {vn(100 * st['rmspe_pre'], 1)}%.",
        f"Sau chính sách, chuỗi CRZ thực tế nằm dưới chuỗi tổng hợp trong phần lớn các tuần. Khoảng cách trung bình là "
        f"{vn(st['avg_gap_post'], 4)}, tương ứng mức giảm trung bình {vn(-st['avg_pct_effect_post'], 2)}% so với phản thực. RMSPE sau "
        f"chính sách tăng lên {vn(st['rmspe_post'], 4)}, tỷ số sau/trước là {vn(st['ratio'], 2)}. Khoảng cách có xu hướng rộng dần "
        f"vào cuối năm 2025. Phiên bản khử trung bình cho kết quả trùng khớp, vì sau khi chuẩn hóa mỗi chuỗi theo trung bình năm 2024, "
        f"thành phần mức đã bằng nhau giữa chuỗi xử lý và mọi vùng đối chứng.")
    rp.FIG(R.fig("f26"), "Giả dược theo không gian: khoảng cách SCM của CRZ so với của 60 vùng đối chứng lớn nhất")
    rp.FIG(R.fig("f27"), "Phân phối tỷ số RMSPE sau/trước của các vùng giả dược và vị trí của CRZ")
    pl = R.t("t40")
    rp.PS(
        f"Kiểm định giả dược không gian cho hai kết luận khác nhau tùy thống kê được dùng. Theo tỷ số RMSPE sau/trước, CRZ đứng ở mức "
        f"giá trị p = {vn(sc['placebo_rank_p'], 3)}, tức {int((pl.ratio >= st['ratio']).sum())}/{sc['placebo_n']} vùng giả dược có tỷ "
        f"số cao hơn. Theo độ lớn khoảng cách trung bình sau chính sách, giá trị p là {vn(sc['placebo_gap_p'], 3)}: không vùng giả "
        f"dược nào có khoảng cách trung bình lớn bằng CRZ.",
        "Sự khác biệt đến từ bản chất của hai thống kê. Tỷ số RMSPE nhạy với độ khớp trước chính sách: một vùng nhỏ khớp rất tốt (RMSPE "
        "trước nhỏ) chỉ cần lệch vừa phải cũng có tỷ số cao. Ba vùng có tỷ số cao nhất là "
        f"{', '.join(pl.sort_values('ratio', ascending=False).Zone.head(3))}, với khoảng cách sau chính sách lần lượt "
        f"{', '.join(vn(v, 3) for v in pl.sort_values('ratio', ascending=False).avg_gap_post.head(3))}; nhiều vùng trong nhóm tỷ số "
        "cao có khoảng cách dương, tức tăng trưởng nhanh hơn phản thực. Khoảng cách trung bình mới là đại lượng trực "
        "tiếp của câu hỏi \"CRZ có giảm nhiều hơn mức ngẫu nhiên không\". Theo thống kê này, kết quả SCM có ý nghĩa ở mức 5%.")

    # ================================================================ 4.11
    rp.H2("4.11. Học máy nhân quả và tác động không đồng nhất")
    rp.H3("4.11.1. Kiểm tra chồng lấn")
    dm = R.J["09_dml"]
    ov = dm["overlap"]
    sens = R.t("t41b")
    rp.FIG(R.fig("f28"), "Phân phối điểm xu hướng cross-fitted của cặp OD chạm và không chạm CRZ (bộ biến rút gọn)")
    rg_ = sens[(sens.x_set == "rút gọn") & (sens.outcome == "dlog_n")].iloc[0]
    fu_ = sens[(sens.x_set == "đầy đủ") & (sens.outcome == "dlog_n")].iloc[0]
    rp.PS(
        f"Bước đầu tiên là kiểm tra chồng lấn. Với bộ biến đầy đủ ({int(fu_.n_features)} đặc trưng, gồm "
        f"quận và tốc độ, giá/dặm năm 2024), mô hình xu hướng phân tách hai nhóm gần như hoàn hảo: AUC = {vn(fu_.auc_propensity, 4)}, "
        f"chỉ {vn(100 * fu_.share_in_overlap, 1)}% cặp OD ({vint(fu_.n_overlap)} cặp) có ê(X) trong khoảng [0,05; 0,95]. Tức là "
        f"với đặc trưng vị trí, ta luôn đoán đúng một cặp có chạm CRZ hay không, và không còn đơn vị đối chứng tương đồng để so "
        f"sánh.",
        f"Với bộ biến rút gọn ({int(rg_.n_features)} đặc trưng chuyến đi, không có thông tin vị trí trực tiếp), AUC giảm xuống "
        f"{vn(rg_.auc_propensity, 4)} và {vn(100 * rg_.share_in_overlap, 1)}% cặp ({vint(rg_.n_overlap)} cặp, trong đó "
        f"{vint(rg_.n_treated_overlap)} cặp chạm CRZ) nằm trong vùng chồng lấn. Đồ án dùng bộ rút gọn làm đặc tả chính và ghi rõ rằng "
        f"ước lượng đại diện cho tổng thể cặp OD trong vùng chồng lấn, không phải cho mọi cặp OD.")
    rp.H3("4.11.2. Tác động trung bình")
    rows = []
    for _, r in sens.iterrows():
        sc_ = 100 if r.outcome == "dlog_n" else 1
        rows.append({"Bộ biến": r.x_set, "Kết quả": {"dlog_n": "Δ log số chuyến (×100)", "d_mph": "Δ tốc độ (dặm/giờ)",
                                                      "d_pay_pm": "Δ thu nhập tài xế/dặm"}[r.outcome],
                     "AUC xu hướng": vn(r.auc_propensity, 3), "Số cặp chồng lấn": vint(r.n_overlap),
                     "PLR θ (SE)": f"{vn(sc_ * r.plr_theta, 3)} ({vn(sc_ * r.plr_se, 3)})",
                     "AIPW ATE (SE)": f"{vn(sc_ * r.aipw_ate, 3)} ({vn(sc_ * r.aipw_se, 3)})"})
    rp.TAB(pd.DataFrame(rows), "Ước lượng DML (PLR) và AIPW theo hai bộ biến kiểm soát", widths=[2.0, 4.2, 2.2, 2.4, 2.6, 2.6], size=10,
           source="Ghi chú: LightGBM, cross-fitting 5 phần; AIPW trên vùng ê(X) ∈ [0,05; 0,95]. Nguồn: t41b.")
    ma = R.dml_main("dlog_n")
    rp.PS(
        f"Với bộ rút gọn, PLR cho θ = {vn(100 * rg_.plr_theta, 2)} và AIPW cho ATE = {vn(100 * rg_.aipw_ate, 2)} điểm log ×100, tức số "
        f"chuyến của cặp chạm CRZ giảm khoảng {vn(-pct_log(rg_.aipw_ate), 1)}% so với phản thực cùng kỳ. Chênh lệch thô (không kiểm "
        f"soát) là {vn(100 * ma.naive_diff, 2)}. Như vậy, việc kiểm soát đặc trưng chuyến đi thu hẹp khoảng cách một phần nhưng mức "
        f"giảm vẫn rõ rệt và nằm trong khoảng của các ước lượng DiD. Với bộ đầy đủ, ước lượng nhỏ hơn "
        f"({vn(100 * fu_.aipw_ate, 2)}), nhưng ước lượng này chỉ dựa trên {vint(fu_.n_overlap)} cặp OD đặc biệt có đặc trưng vị trí "
        f"trung gian, nên không đại diện.",
        f"Với tốc độ, cả hai bộ biến đều cho mức tăng trong khoảng {vn(sens[sens.outcome == 'd_mph'].aipw_ate.min(), 2)} đến "
        f"{vn(sens[sens.outcome == 'd_mph'].aipw_ate.max(), 2)} dặm/giờ, rất gần kết quả DiD. Với thu nhập tài xế/dặm, DML cho giá trị "
        f"âm nhỏ ({vn(sens[(sens.x_set == 'rút gọn') & (sens.outcome == 'd_pay_pm')].aipw_ate.iloc[0], 3)} "
        f"USD/dặm), trái dấu với DiD vùng × tuần. Sự không nhất quán về dấu này là thêm một lý do để không kết luận về thu nhập tài xế.")
    rp.H3("4.11.3. Kiểm định không đồng nhất: BLP và GATES")
    bl = R.t("t42")
    rp.TAB(pd.DataFrame({"Kết quả": bl.outcome.map({"dlog_n": "Δ log số chuyến", "d_mph": "Δ tốc độ", "d_pay_pm": "Δ thu nhập/dặm"}),
                         "β₁ (ATE)": [f"{vn(a, 4)} ({vn(b, 4)})" for a, b in zip(bl.beta1, bl.se1)],
                         "β₂ (không đồng nhất)": [f"{vn(a, 3)} ({vn(b, 3)})" for a, b in zip(bl.beta2, bl.se2)],
                         "t của β₂": bl.t2.map(lambda v: vn(v, 2))}),
           "Kiểm định BLP cho tác động không đồng nhất", widths=[4, 4, 4, 3], size=10.5,
           source="Ghi chú: sai số chuẩn vững phương sai thay đổi (HC0). Nguồn: t42_dml_blp.csv.")
    rp.P(f"Hệ số β₂ của cả ba kết quả đều dương và có t-thống kê lớn (từ {vn(bl.t2.min(), 1)} đến {vn(bl.t2.max(), 1)}), nghĩa là "
         f"CATE ước lượng mang tín hiệu thật về sự khác biệt tác động giữa các cặp OD, không chỉ là nhiễu. Giá trị β₂ nhỏ hơn 1 "
         f"(khoảng {vn(bl.beta2.mean(), 2)}) cho thấy CATE ước lượng có phương sai lớn hơn phương sai thật và cần được co về trung "
         f"bình khi diễn giải.")
    rp.FIG(R.fig("f29"), "GATES: tác động trung bình theo nhóm ngũ phân vị của CATE ước lượng")
    gt = R.t("t43")
    gl = gt[gt.outcome == "dlog_n"]
    gm = gt[gt.outcome == "d_mph"]
    rp.P(f"GATES cho log số chuyến trải từ {vn(100 * gl.gate.min(), 2)} ở nhóm thấp nhất đến {vn(100 * gl.gate.max(), 2)} ở nhóm cao "
         f"nhất (×100), mọi nhóm đều âm. Với tốc độ, tác động trải từ {vn(gm.gate.min(), 3)} đến {vn(gm.gate.max(), 3)} dặm/giờ, mọi "
         f"nhóm đều dương. Không có nhóm nào có tác động ngược dấu, nên không đồng nhất ở đây là khác biệt về độ lớn chứ không phải về "
         f"chiều.")
    rp.H3("4.11.4. Đặc trưng của nhóm chịu tác động mạnh")
    cl = R.t("t44")
    cln = cl[cl.outcome == "dlog_n"]
    fl = {"miles_pt": "Quãng đường/chuyến (dặm)", "min_pt": "Thời lượng/chuyến (phút)", "mph_2024": "Tốc độ 2024",
          "fare_pm_2024": "Giá cước/dặm 2024", "ln_n_2024": "log lưu lượng 2024", "uber_share": "Tỷ trọng Uber",
          "night_share": "Tỷ trọng chuyến đêm", "D": "Tỷ lệ chạm CRZ"}
    rp.TAB(pd.DataFrame({"Đặc trưng": cln.feature.map(fl), "Nhóm giảm mạnh nhất (G1)": cln.low_group.map(lambda v: vn(v, 3)),
                         "Nhóm giảm ít nhất (G5)": cln.high_group.map(lambda v: vn(v, 3))}),
           "CLAN: đặc trưng trung bình của nhóm có tác động lên số chuyến mạnh nhất và yếu nhất", widths=[6, 5, 5], size=10.5)
    g = lambda f, c: float(cln[cln.feature == f][c].iloc[0])
    rp.P(f"Nhóm có mức giảm số chuyến mạnh nhất (G1, theo τ̂ thấp nhất) có tốc độ năm 2024 cao hơn ({vn(g('mph_2024', 'low_group'), 2)} "
         f"so với {vn(g('mph_2024', 'high_group'), 2)} dặm/giờ), thời lượng chuyến ngắn hơn ({vn(g('min_pt', 'low_group'), 1)} so với "
         f"{vn(g('min_pt', 'high_group'), 1)} phút) và ít chuyến đêm hơn. Nhóm giảm ít nhất (G5) có tỷ lệ chuyến đêm cao hơn và thời "
         f"lượng dài hơn. Tỷ lệ cặp chạm CRZ ở G5 ({vn(g('D', 'high_group'), 2)}) cao hơn G1 "
         f"({vn(g('D', 'low_group'), 2)}): CATE được ước lượng cho mọi cặp, kể cả cặp đối chứng, nên G1 bao gồm nhiều cặp không chạm "
         f"CRZ có đặc trưng khiến chúng sẽ rất nhạy nếu bị tính phí.")
    rp.FIG(R.fig("f30"), "CATE ước lượng theo quãng đường trung bình của cặp OD chạm CRZ")
    cd = R.t("t46")
    rp.P(f"Theo quãng đường, CATE trung bình của cặp chạm CRZ là {vn(100 * cd.tau.iloc[0], 2)} ở nhóm chuyến ngắn nhất (trung bình "
         f"{vn(cd.miles.iloc[0], 2)} dặm) và {vn(100 * cd.tau.iloc[-1], 2)} ở nhóm dài nhất ({vn(cd.miles.iloc[-1], 2)} dặm). Chuyến "
         f"ngắn nhạy hơn, khớp với lập luận tỷ lệ phí trên chi phí chuyến đi ở Chương 2, dù độ dốc không lớn.")
    rp.FIG(R.fig("f31"), "Tỷ trọng đóng góp (gain) của các đặc trưng trong mô hình CATE cho Δ log số chuyến")
    imp = R.t("t45")
    ii = imp[imp.outcome == "dlog_n"].sort_values("gain", ascending=False)
    rp.P(f"Trong mô hình CATE, tiền tip trung bình ({vn(100 * ii[ii.feature == 'tips_pt'].gain.iloc[0], 1)}% gain), quãng đường "
         f"({vn(100 * ii[ii.feature == 'miles_pt'].gain.iloc[0], 1)}%) và log lưu lượng "
         f"({vn(100 * ii[ii.feature == 'ln_n_2024'].gain.iloc[0], 1)}%) là ba đặc trưng đóng góp nhiều nhất. Tiền tip trung bình "
         f"có thể đóng vai trò đại diện cho mức thu nhập của hành khách và loại chuyến đi (công tác, giải trí). Chỉ số gain chỉ phản "
         f"ánh mức độ mô hình sử dụng đặc trưng, không phải quan hệ nhân quả của đặc trưng đó.")

    rp.H3("4.11.5. Tác động riêng theo từng vùng CRZ")
    ze = R.t("t54").sort_values("pct_ln_n")
    zm = R.J["14_extra"]["zone_effects"]
    lf38 = rp.FIG(R.fig("f38"), "Tác động DiD riêng của từng vùng CRZ lên số chuyến đón (%)", width_cm=10.5)
    rp.PS(
        f"Thay vì một hệ số chung, có thể ước lượng một hệ số riêng cho mỗi vùng CRZ bằng tương tác D × vùng trong cùng mô hình TWFE. "
        f"Kết quả rất đồng nhất về chiều: cả {zm['n_negative']}/{zm['n']} vùng có hệ số âm, và {zm['n_sig_negative']} vùng có khoảng tin "
        f"cậy 95% nằm hoàn toàn dưới 0. Tốc độ tăng ở {zm['n_mph_positive']}/{zm['n']} vùng. Mức giảm số chuyến trải từ "
        f"{vn(-ze.pct_ln_n.max(), 1)}% ({ze.Zone.iloc[-1]}) đến {vn(-ze.pct_ln_n.min(), 1)}% ({ze.Zone.iloc[0]}).",
        f"{lf38} cho thấy bốn vùng giảm mạnh nhất là {', '.join(ze.Zone.head(4))}, phần lớn là khu dân cư ở phía đông nam Manhattan. "
        f"Bốn vùng giảm nhẹ nhất là {', '.join(ze.Zone.tail(4))}, phần lớn là khu văn phòng và đầu mối giao thông, nơi nhu cầu đi lại "
        f"ít linh hoạt hơn.")
    rp.FIG(R.fig("f39"), "Tác động theo vùng CRZ so với quy mô vùng và độ sâu bên trong CRZ")
    mr = R.t("t55")
    lab_m = {"const": "Hằng số", "log_pre_per_day": "log chuyến/ngày 2024", "share_to_crz": "% chuyến có đích trong CRZ",
             "depth_km": "Độ sâu trong CRZ (km)", "fare_pt_pre": "Giá cước/chuyến 2024 (USD)"}
    rows = []
    for t_ in mr.term.unique():
        r1 = mr[(mr.outcome == "b_ln_n") & (mr.term == t_)].iloc[0]
        r2 = mr[(mr.outcome == "b_mph") & (mr.term == t_)].iloc[0]
        rows.append({"Biến giải thích": lab_m[t_], "Tác động lên log số chuyến": cse(r1.coef, r1.se, r1.p, 4),
                     "Tác động lên tốc độ": cse(r2.coef, r2.se, r2.p, 4)})
    r2b = mr[mr.outcome == "b_ln_n"].r2.iloc[0]
    r2m = mr[mr.outcome == "b_mph"].r2.iloc[0]
    rp.TAB(pd.DataFrame(rows), f"Hồi quy tác động theo vùng lên đặc trưng vùng ({int(mr.n.iloc[0])} vùng CRZ; R² = {vn(r2b, 3)} và {vn(r2m, 3)})",
           widths=[5.6, 5.2, 5.2], size=10.5,
           source="Ghi chú: WLS với trọng số nghịch đảo phương sai của hệ số vùng; sai số chuẩn HC1. Nguồn: t55.")
    fr = mr[(mr.outcome == "b_ln_n") & (mr.term == "fare_pt_pre")].iloc[0]
    dp = mr[(mr.outcome == "b_mph") & (mr.term == "depth_km")].iloc[0]
    rp.P(f"Hồi quy tác động theo vùng lên đặc trưng vùng cho thấy biến giải thích mạnh nhất cho mức giảm số chuyến là giá cước "
         f"trung bình năm 2024: vùng có giá cước/chuyến cao hơn 1 USD giảm ít hơn {vn(100 * fr.coef, 2)} điểm log ×100 (p = {pval(fr.p)}). "
         f"Kết quả này nhất quán với lập luận tỷ lệ phí trên giá: nơi chuyến đi đắt, phí cố định 1,50 USD là một tỷ lệ nhỏ. Quy mô vùng "
         f"và độ sâu bên trong CRZ không giải thích được mức giảm số chuyến. Với tốc độ, vùng càng sâu bên trong CRZ tăng tốc độ càng "
         f"nhiều ({vn(dp.coef, 3)} dặm/giờ mỗi km, p = {pval(dp.p)}), phù hợp với việc lưu lượng giảm mạnh nhất ở lõi vùng thu phí.")

    # ================================================================ 4.12
    rp.H2("4.12. Hiệu ứng lan tỏa không gian")
    rp.H3("4.12.1. Lan tỏa theo dải khoảng cách")
    rp.FIG(R.fig("f32"), "Tác động theo dải khoảng cách tới ranh giới CRZ, phía điểm đón và phía điểm trả (so với vùng cách trên 10 km)")
    sp = R.t("t48")
    bands = ["CRZ", "Vắt ranh giới", "0–1 km", "1–2,5 km", "2,5–5 km", "5–10 km"]
    rows = []
    for b in bands:
        row = {"Dải": b, "Số vùng": vint(sp[(sp.side == "điểm đón") & (sp.band == b)].n_zones.iloc[0])}
        for side, y, l in (("điểm đón", "ln_n", "Chuyến đón"), ("điểm trả", "ln_n", "Chuyến trả"),
                           ("điểm trả", "ln_nocrz", "Trả, khách từ ngoài CRZ"), ("điểm trả", "ln_from_crz", "Trả, khách từ CRZ")):
            r = sp[(sp.side == side) & (sp.outcome == y) & (sp.band == b)].iloc[0]
            row[l] = cse(r.coef, r.se, r.p, 3)
        rows.append(row)
    rp.TAB(pd.DataFrame(rows), "Tác động theo dải khoảng cách tới CRZ (log số chuyến, so với vùng cách trên 10 km)",
           widths=[2.4, 1.6, 3.0, 3.0, 3.0, 3.0], size=9.5,
           source="Ghi chú: panel vùng × tuần, hiệu ứng cố định vùng và tuần; phân cụm theo vùng. Nguồn: t48_spillover_bands.csv.")
    b01 = R.spill("điểm đón", "ln_n", "0–1 km")
    b12 = R.spill("điểm đón", "ln_n", "1–2,5 km")
    b25 = R.spill("điểm đón", "ln_n", "2,5–5 km")
    b510 = R.spill("điểm đón", "ln_n", "5–10 km")
    bc = R.spill("điểm đón", "ln_n", "CRZ")
    fc01 = R.spill("điểm trả", "ln_from_crz", "0–1 km")
    rp.PS(
        f"So với các vùng cách CRZ trên 10 km, số chuyến đón trong CRZ giảm {vn(-pct_log(bc.coef), 2)}%. Mức giảm lan ra ngoài ranh "
        f"giới và nhỏ dần theo khoảng cách: dải 0–1 km giảm {vn(-pct_log(b01.coef), 2)}%, dải 1–2,5 km giảm {vn(-pct_log(b12.coef), 2)}%, "
        f"dải 2,5–5 km giảm {vn(-pct_log(b25.coef), 2)}% và dải 5–10 km giảm {vn(-pct_log(b510.coef), 2)}%. Các vùng vắt ranh giới giảm "
        f"gần bằng CRZ. Phía điểm trả có mẫu hình tương tự.",
        "Mẫu hình giảm dần theo khoảng cách có hai hàm ý. Thứ nhất, một phần lớn chuyến đi của các vùng lân cận có đầu kia trong CRZ, "
        "nên chúng cũng chịu phí; đây là lan tỏa qua mạng lưới chuyến đi chứ không phải hiệu ứng riêng của vùng. Thứ hai, dùng các vùng "
        "Manhattan phía bắc làm nhóm đối chứng sẽ đánh giá thấp tác động vì chính nhóm này bị ảnh hưởng; mục 4.14 xác nhận điều này.",
        f"Ở cột cuối, số chuyến từ CRZ trả khách ở dải 0–1 km ngoài ranh giới tăng "
        f"{vn(pct_log(fc01.coef), 2)}% (p = {pval(fc01.p)}), trong khi số chuyến từ CRZ trả khách trong CRZ giảm. Nhìn từ phía hành "
        f"khách, chuyến CRZ→CRZ bị tính phí giống chuyến CRZ→ngoài, nên động cơ né phí không nằm ở đây. Một cách giải thích hợp lý hơn "
        f"là một phần hành khách chọn đích đến ngay bên ngoài ranh giới khi có lựa chọn tương đương, hoặc các chuyến nội vùng dài "
        f"được thay bằng chuyến kết thúc ở vùng lân cận. Bằng chứng này gợi ý nhưng chưa đủ để kết luận về hành vi né phí có chủ "
        f"đích.")

    rp.H3("4.12.2. Lan tỏa theo quận")
    sb = R.t("t56")
    sb = sb[sb.n_near > 0]
    rp.TAB(pd.DataFrame({"Quận": sb.borough, "Số vùng trong 5 km": sb.n_near.map(vint),
                         "Hệ số log số chuyến đón": [cse(a, b, c, 4) for a, b, c in zip(sb.coef, sb.se, sb.p)],
                         "% thay đổi": sb.coef.map(lambda v: vn(pct_log(v), 2))}),
           "Tác động lên các vùng ngoài CRZ cách ranh giới không quá 5 km, theo quận (so với các vùng xa hơn)",
           widths=[3.2, 3.2, 5.6, 3.0], size=10.5, source="Nguồn: t56_spillover_by_borough.csv.")
    bm = sb[sb.borough == "Manhattan"].iloc[0]
    bb = sb[sb.borough == "Brooklyn"].iloc[0]
    bq = sb[sb.borough == "Queens"].iloc[0]
    rp.P(f"Lan tỏa không đều giữa các quận. Các vùng Manhattan ngoài CRZ trong bán kính 5 km giảm {vn(-pct_log(bm.coef), 2)}%, các "
         f"vùng Brooklyn gần CRZ giảm {vn(-pct_log(bb.coef), 2)}%, còn các vùng Queens gần CRZ không thay đổi có ý nghĩa "
         f"({vn(pct_log(bq.coef), 2)}%, p = {pval(bq.p)}). Một giải thích khả dĩ là mức độ gắn kết của chuyến đi với khu trung tâm khác "
         f"nhau giữa các quận, nhưng đồ án chưa kiểm tra trực tiếp giả thuyết này. Không có vùng Bronx nào nằm trong bán kính 5 km.")

    # ================================================================ 4.13
    rp.H2("4.13. Taxi vàng")
    t8 = did_table(R, "yellow", ["ln_n", "fare_pm", "fare_pt", "rider_pt", "cbd_pt", "mph", "miles_pt"])
    rp.TAB(t8, "Tác động lên taxi vàng (đối chứng: Manhattan phía bắc; panel vùng × tuần)",
           widths=[3.6, 1.6, 2.7, 2.7, 2.7, 2.7], size=9.5, source="Ghi chú: như Bảng DiD số chuyến. Nguồn: t30_did_main.csv.")
    yt = R.did("yellow", "ln_n")
    yw_ = R.did("yellow", "ln_n", "TWFE có trọng số")
    ya = R.did("yellow", "ln_n", sample="vùng×tuần, đối chứng gồm quận ngoài")
    yaw = R.did("yellow", "ln_n", "TWFE có trọng số", sample="vùng×tuần, đối chứng gồm quận ngoài")
    ymp = R.did("yellow", "mph")
    rp.FIG(R.fig("f20"), "Nghiên cứu sự kiện theo tuần cho log số chuyến taxi vàng đón trong CRZ")
    rp.PS(
        f"Kết quả của taxi vàng kém ổn định hơn nhiều so với HVFHV. Với nhóm đối chứng là Manhattan phía bắc, TWFE không trọng số "
        f"cho hệ số {vn(yt.coef, 3)} (p = {pval(yt.p)}), nhưng TWFE có trọng số theo lưu lượng cho {vn(yw_.coef, 4)} (p = {pval(yw_.p)}), "
        f"tức gần như không có tác động tính theo chuyến. Ước lượng không trọng số bị chi phối bởi một số vùng CRZ nhỏ có số chuyến "
        f"taxi dao động mạnh. Khi gộp cả quận ngoài vào nhóm đối chứng, hệ số không trọng số là {vn(ya.coef, 3)} và có trọng số là "
        f"{vn(yaw.coef, 3)}; con số không trọng số rất lớn phản ánh sự bùng nổ số chuyến taxi vàng ở các quận ngoài đã nói ở mục 4.2.2, "
        f"không phải tác động của phí.",
        f"Diễn giải thận trọng nhất là số chuyến taxi vàng trong CRZ không giảm tương ứng với HVFHV. Kết hợp với chỉ số mô tả ở {lf17}, "
        f"điều này phù hợp với giả thuyết một phần hành khách chuyển từ gọi xe sang taxi, loại phương tiện chịu phí thấp bằng "
        f"một nửa và có thể đón ngay trên đường phố. Tốc độ taxi vàng có hệ số {vn(ymp.coef, 3)} (p = {pval(ymp.p)}) trong đặc tả không "
        f"trọng số nhưng không có ý nghĩa trong đặc tả có trọng số; đồ án không đưa ra kết luận về tốc độ từ dữ liệu taxi vàng.")

    # ================================================================ 4.14
    rp.H2("4.14. Kiểm định độ tin cậy")
    rp.H3("4.14.1. Giả dược theo thời gian")
    p1 = R.t("t49")
    lab2 = {"ln_n": "log số chuyến", "fare_pm": "Giá cước/dặm", "pay_pm": "TN tài xế/dặm", "fare_pt": "Giá cước/chuyến",
            "pay_pt": "TN tài xế/chuyến", "rider_pt": "Chi phí hành khách/chuyến", "mph": "Tốc độ", "wait": "Thời gian chờ",
            "miles_pt": "Dặm/chuyến"}
    rows = []
    for _, r in p1.iterrows():
        rows.append({"Biến": lab2.get(r.outcome, r.outcome),
                     "Giả dược 07/2024": cse(r.placebo_coef, r.placebo_se, r.placebo_p, 3),
                     "Giả dược + xu hướng": cse(r.placebo_trend_coef, r.placebo_trend_se, r.placebo_trend_p, 3),
                     "Thật 01/2025": cse(r.real_coef, r.real_se, r.real_p, 3),
                     "Thật + xu hướng": cse(r.real_trend_coef, r.real_trend_se, r.real_trend_p, 3)})
    rp.TAB(pd.DataFrame(rows), "Giả dược theo thời gian trên panel vùng × tuần (chính sách giả 07/07/2024, chỉ dữ liệu 2024)",
           widths=[3.4, 3.2, 3.2, 3.1, 3.1], size=9.5,
           source="Ghi chú: TWFE, phân cụm theo vùng. Nguồn: t49_placebo_time.csv.")
    pln = R.placebo("ln_n")
    plm = R.placebo("mph")
    plw = R.placebo("wait")
    plf = R.placebo("fare_pt")
    rp.PS(
        "Phép thử giả dược đặt ra câu hỏi: nếu áp dụng đúng quy trình ước lượng cho một ngày không có chính sách, ta có tìm thấy "
        "\"tác động\" không? Kết quả phân loại các biến thành hai nhóm rõ rệt.",
        f"Nhóm thứ nhất gồm tốc độ và thời gian chờ. Giả dược cho tốc độ là {vn(plm.placebo_coef, 3)}, ngược dấu với tác động thật "
        f"({vn(plm.real_coef, 3)}). Giả dược cho thời gian chờ là {vn(plw.placebo_coef, 3)} (p = {pval(plw.placebo_p)}), gần bằng 0, "
        f"trong khi tác động thật là {vn(plw.real_coef, 3)}. Hai kết quả về điều kiện di chuyển vì vậy vượt qua phép thử.",
        f"Nhóm thứ hai gồm giá cước, thu nhập tài xế và chi phí hành khách. Giả dược cho giá cước/chuyến là {vn(plf.placebo_coef, 3)} "
        f"USD, có ý nghĩa thống kê và cùng độ lớn với tác động thật ({vn(plf.real_coef, 3)} USD). Tình hình tương tự với thu nhập tài "
        f"xế và giá/dặm. Khi thêm xu hướng nhóm, các hệ số giả dược đổi dấu và vẫn có ý nghĩa. Như vậy, các biến giá có cả xu hướng "
        f"lẫn mùa vụ riêng giữa CRZ và vùng đối chứng, đủ để tạo ra \"tác động\" giả với mọi đặc tả thử nghiệm. Đây là cơ sở để đồ án "
        f"không diễn giải nhân quả các hệ số về giá.",
        f"Với số chuyến, giả dược cho hệ số {vn(pln.placebo_coef, 3)}, tức CRZ đã tăng chậm hơn đối chứng khoảng "
        f"{vn(-pct_log(pln.placebo_coef), 1)}% giữa nửa đầu và nửa cuối năm 2024. Con số này nhỏ hơn nhiều so với tác động thật "
        f"({vn(pln.real_coef, 3)}), nhưng không bằng 0. Một phần của nó là mùa vụ (nửa cuối năm có mùa lễ, khi CRZ có biên độ dao động "
        f"lớn hơn), phần còn lại có thể là xu hướng. Điều này cho thấy ước lượng TWFE có thể đánh giá cao mức giảm, và các ước lượng "
        f"SCM và DML, vốn thấp hơn, là cận dưới hợp lý.")
    p2 = R.t("t49b")
    rows = []
    for _, r in p2.iterrows():
        rows.append({"Biến": lab2.get(r.outcome, r.outcome),
                     "Giả dược 07/2024": cse(r.placebo_coef, r.placebo_se, r.placebo_p, 3),
                     "Giả dược + xu hướng": cse(r.placebo_trend_coef, r.placebo_trend_se, r.placebo_trend_p, 3),
                     "Thật 01/2025": cse(r.real_coef, r.real_se, r.real_p, 3),
                     "Thật + xu hướng": cse(r.real_trend_coef, r.real_trend_se, r.real_trend_p, 3)})
    rp.TAB(pd.DataFrame(rows), "Giả dược theo thời gian trên panel cặp OD × tháng", widths=[3.4, 3.2, 3.2, 3.1, 3.1], size=9.5,
           source="Ghi chú: hiệu ứng cố định cặp và tháng; phân cụm theo vùng đón. Nguồn: t49b_placebo_time_od.csv.")
    om = R.placebo("mph", od=True)
    on = R.placebo("ln_n", od=True)
    rp.P(f"Trên panel cặp OD, kết luận tương tự. Tốc độ có giả dược {vn(om.placebo_coef, 3)} (âm) và giả dược có xu hướng "
         f"{vn(om.placebo_trend_coef, 3)} (p = {pval(om.placebo_trend_p)}), trong khi tác động thật dương với mọi đặc tả "
         f"({vn(om.real_coef, 3)} và {vn(om.real_trend_coef, 3)}). Số chuyến có giả dược {vn(on.placebo_coef, 3)} so với tác động "
         f"thật {vn(on.real_coef, 3)}; với xu hướng nhóm, tác động thật còn {vn(on.real_trend_coef, 3)} và giả dược là "
         f"{vn(on.placebo_trend_coef, 3)}. Mọi đặc tả đều cho tác động thật âm hơn giả dược tương ứng.")
    rp.H3("4.14.2. Suy luận hoán vị")
    pm = R.J["10_spillover_robustness_perm"]["permutation"]
    rp.FIG(R.fig("f33"), "Phân phối hệ số DiD khi gán xử lý ngẫu nhiên cho các vùng đối chứng (500 lần) và ước lượng thật")
    rp.P(f"Khi gán ngẫu nhiên nhãn xử lý cho {zw['treated']} trong số {zw['control']} vùng đối chứng, hệ số DiD có trung bình "
         f"{vn(pm['perm_mean'], 4)} và độ lệch chuẩn {vn(pm['perm_sd'], 4)}; 95% giá trị nằm trong [{vn(pm['perm_p2_5'], 4)}; "
         f"{vn(pm['perm_p97_5'], 4)}]. Ước lượng thật {vn(pm['real'], 4)} nằm xa ngoài phân phối này, giá trị p hoán vị hai phía là "
         f"{vn(pm['p_two_sided'], 4)}, bằng mức nhỏ nhất có thể đạt với {pm['n_perm']} lần lặp. Không một cách gán ngẫu nhiên nào tạo "
         f"ra mức giảm lớn như CRZ.")
    rp.H3("4.14.3. Bảng độ vững")
    rb = R.t("t51")
    rp.TAB(pd.DataFrame({"Đặc tả": rb.spec, "Hệ số (SE)": [cse(a, b, c, 4) for a, b, c in zip(rb.coef, rb.se, rb.p)],
                         "% thay đổi": rb.pct.map(lambda v: vn(v, 2)), "Số vùng (xử lý)": [f"{vint(a)} ({vint(b)})" for a, b in zip(rb.n_zones, rb.n_treated)],
                         "Số quan sát": rb.n_obs.map(vint)}),
           "Độ vững của tác động lên log số chuyến HVFHV đón qua các đặc tả", widths=[6.6, 3.0, 1.8, 2.4, 2.2], size=9.5,
           align=["left", "center", "center", "center", "center"], source="Nguồn: t51_robustness_ln_n.csv.")
    rp.FIG(R.fig("f34"), "Hệ số DiD log số chuyến qua các đặc tả, kèm khoảng tin cậy 95%")
    mn = R.rob("Đối chứng chỉ Manhattan")
    ou = R.rob("Đối chứng chỉ các quận ngoài")
    h1 = R.rob("Chỉ 01–06")
    h2 = R.rob("Chỉ 07–12")
    rp.PS(
        f"Trong {len(rb)} đặc tả, {int((rb.coef < 0).sum())} đặc tả cho hệ số âm. Ngoại lệ duy nhất là đặc tả có xu hướng tuyến tính "
        f"nhóm, đã được chỉ ra là không đáng tin qua phép thử giả dược. Thay đổi ngưỡng lưu lượng (50 hay 300 chuyến/ngày), gộp vùng "
        f"vắt ranh giới vào nhóm xử lý, bỏ tuần lễ cuối năm, bỏ bốn tuần đầu hay dùng panel theo ngày đều cho mức giảm trong khoảng "
        f"{vn(-rb[~rb.spec.str.contains('xu hướng|Manhattan|FE quận')].pct.max(), 1)}% đến "
        f"{vn(-rb[~rb.spec.str.contains('xu hướng|Manhattan|FE quận')].pct.min(), 1)}%.",
        f"Khi chỉ dùng Manhattan phía bắc làm đối chứng, mức giảm còn {vn(-mn.pct, 2)}%, so với {vn(-ou.pct, 2)}% khi chỉ dùng quận "
        f"ngoài. Khác biệt này khớp với kết quả lan tỏa ở mục 4.12: Manhattan phía bắc bị ảnh hưởng gián tiếp nên không phải đối chứng "
        f"sạch. Đặc tả hiệu ứng cố định quận × tuần, vốn chỉ so sánh trong nội bộ Manhattan, cho đúng kết quả của đặc tả đối chứng "
        f"Manhattan phía bắc vì hai đặc tả dùng cùng một biến thiên.",
        f"Tác động trong nửa cuối năm 2025 ({vn(-h2.pct, 2)}%) lớn hơn nửa đầu ({vn(-h1.pct, 2)}%), nhất quán với nghiên cứu sự kiện "
        f"trên panel OD. Phân cụm theo quận thay vì vùng làm sai số chuẩn tăng lên nhưng với chỉ 5 cụm, kết quả này chỉ có tính tham "
        f"khảo.")

    import longpre
    if "t90_long_placebo_trend" in R.T:
        longpre.analysis_section(rp, R)
    if "t93_trend_spec_sensitivity" in R.T:
        import robust
        robust.section(rp, R)
    import theory
    theory.tests(rp, R)
    # ================================================================ 4.16
    rp.H2("4.16. Tổng hợp kết quả theo câu hỏi nghiên cứu")
    sc_ = R.J["08_scm"]["standard"]
    lp = R.t("t90").set_index("outcome").loc["ln_n"] if "t90_long_placebo_trend" in R.T else None
    ests = pd.DataFrame([
        ("TWFE, vùng × tuần", vn(-pct_log(tw.coef), 2), f"[{vn(-pct_log(tw.ci_high), 2)}; {vn(-pct_log(tw.ci_low), 2)}]"),
        ("DDD mùa vụ", vn(-pct_log(dd.coef), 2), f"[{vn(-pct_log(dd.ci_high), 2)}; {vn(-pct_log(dd.ci_low), 2)}]"),
        ("TWFE có trọng số", vn(-pct_log(ww.coef), 2), f"[{vn(-pct_log(ww.ci_high), 2)}; {vn(-pct_log(ww.ci_low), 2)}]"),
        ("Panel cặp OD × tháng", vn(-pct_log(R.od('Tất cả chuyến chạm CRZ', 'ln_n').coef), 2),
         f"[{vn(-pct_log(R.od('Tất cả chuyến chạm CRZ', 'ln_n').ci_high), 2)}; {vn(-pct_log(R.od('Tất cả chuyến chạm CRZ', 'ln_n').ci_low), 2)}]"),
        ("Kiểm soát tổng hợp", vn(-sc_["avg_pct_effect_post"], 2), "p (khoảng cách) = " + vn(R.J["08_scm"]["placebo_gap_p"], 3)),
        ("DML – AIPW (vùng chồng lấn)", vn(-pct_log(rg_.aipw_ate), 2),
         f"[{vn(-pct_log(rg_.aipw_ate + 1.96 * rg_.aipw_se), 2)}; {vn(-pct_log(rg_.aipw_ate - 1.96 * rg_.aipw_se), 2)}]"),
        ("Đối chứng chỉ Manhattan phía bắc (bị lan tỏa)", vn(-mn.pct, 2), f"[{vn(-pct_log(mn.ci_high), 2)}; {vn(-pct_log(mn.ci_low), 2)}]"),
        ("Pandey, Guler, Gayah (2026) – tham chiếu", "5,95", "–"),
    ] + ([("Dữ liệu 2022–2025, điều chỉnh xu hướng 2023–2024 (mục 4.14.4, S1)", vn(-pct_log(lp.effect_trend_adj), 2),
           f"[{vn(-pct_log(lp.effect_trend_adj + 1.96 * lp.effect_trend_adj_se), 2)}; {vn(-pct_log(lp.effect_trend_adj - 1.96 * lp.effect_trend_adj_se), 2)}]"),
          ("Dữ liệu 2022–2025, gia tốc so với thay đổi năm 2024", vn(-pct_log(lp.accel), 2),
           f"[{vn(-pct_log(lp.accel + 1.96 * lp.accel_se), 2)}; {vn(-pct_log(lp.accel - 1.96 * lp.accel_se), 2)}]")] if lp is not None else [])
      + ([(f"Dữ liệu 2022–2025, đặc tả {k} (mục 4.14.6)", vn(-pct_log(r.effect), 2),
           f"[{vn(-pct_log(r.ci_high_wild), 2)}; {vn(-pct_log(r.ci_low_wild), 2)}]")
          for k, r in R.t("t93").query("outcome == 'ln_n' and spec in ['S2', 'S3', 'S4']").set_index("spec").iterrows()]
         if "t93_trend_spec_sensitivity" in R.T else []),
    columns=["Phương pháp", "Mức giảm số chuyến (%)", "KTC 95% / suy luận"])
    rp.TAB(ests, "Tổng hợp các ước lượng mức giảm số chuyến HVFHV chạm CRZ", widths=[7.4, 3.6, 5.0], size=10.5,
           align=["left", "center", "center"])
    rp.P("Bảng trên đặt các ước lượng cạnh nhau. Mọi thiết kế dựa trên một năm trước chính sách đều cho thấy số chuyến giảm trong "
         "khoảng từ khoảng 6% đến 10%, và ước lượng tham chiếu của Pandey, Guler và Gayah (2026) nằm ở cận dưới của khoảng này. Các dòng "
         "dùng dữ liệu 2022–2025 cho thấy con số này phụ thuộc vào giả định về xu hướng: điều chỉnh theo xu hướng tuyến tính 2023–2024 "
         "cho tác động gần 0, bỏ các tháng đầu năm hoặc cho phép xu hướng bậc hai cho mức giảm khoảng 2–4%, còn dùng năm 2023 làm gốc cho "
         "mức giảm gần bằng thiết kế một năm. Khoảng 6–10% vì vậy là cận trên, đạt được khi xu hướng giảm tương đối trước đó tự dừng lại "
         "đúng lúc chính sách bắt đầu; dữ liệu không đủ để chọn một con số cụ thể trong khoảng từ 0 đến khoảng 10%.")
    summ = pd.DataFrame([
        ("RQ1", "Pipeline Lakehouse, DuckDB, Parquet", f"{vint(R.t('t03').total_rows.sum())} bản ghi trong {vn(tot.sec_total.sum() / 60, 1)} phút; Parquet ZSTD nhỏ hơn CSV {vn(1 / zs.size_ratio_vs_csv, 1)} lần; DuckDB dùng ít bộ nhớ nhất", "Cao"),
        ("RQ2", "Số chuyến", "Giảm 6–10% với một năm trước chính sách; với dữ liệu 2022–2025, từ khoảng 0 đến khoảng 10% tùy giả định xu hướng", "Thấp: chưa xác định được độ lớn"),
        ("RQ3", "Tốc độ, thời gian chờ", f"Thời gian chờ −{vn(-wt.coef, 2)} phút (một năm), giảm ở mọi đặc tả xu hướng trừ đặc tả kém tin cậy nhất; tốc độ +{vn(mp.coef, 2)} dặm/giờ (một năm), tăng ở phần lớn đặc tả, độ lớn phụ thuộc giả định", "Thời gian chờ: cao; tốc độ: trung bình"),
        ("RQ4", "Không đồng nhất, lan tỏa", "Giảm mạnh hơn vào đêm, chuyến ngắn; tốc độ tăng mạnh chiều tối; lan tỏa giảm dần tới 5–10 km", "Trung bình"),
    ], columns=["Câu hỏi", "Nội dung", "Kết quả chính", "Mức độ chắc chắn"])
    rp.TAB(summ, "Đối chiếu câu hỏi nghiên cứu, kết quả và mức độ chắc chắn", widths=[1.6, 3.4, 8.0, 3.0], size=10,
           align=["center", "left", "left", "left"])
    rp.H2("4.17. Tiểu kết Chương 4")
    rp.P("Chương 4 cho thấy pipeline xử lý được toàn bộ dữ liệu với chi phí tính toán thấp và các lựa chọn kỹ thuật có tác động đo "
         "được. Về nhân quả, với một năm trước chính sách, mọi thiết kế đều cho thấy số chuyến gọi xe chạm CRZ giảm, tốc độ tăng và thời "
         "gian chờ giảm, nhất quán giữa các phương pháp và vượt qua suy luận hoán vị, wild bootstrap, sai số Conley và hiệu chỉnh kiểm "
         "định bội. Khi mở rộng giai đoạn trước chính sách về 2022, kết luận phân hóa theo mức độ chắc chắn: thời gian chờ giảm ở mọi "
         "đặc tả xu hướng hợp lý; tốc độ tăng ở phần lớn đặc tả nhưng độ lớn phụ thuộc giả định; còn số chuyến đã giảm tương đối từ năm "
         "2023, nên tác động nhân quả lên số chuyến nằm đâu đó từ 0 đến khoảng 10% và không xác định được chính xác hơn. Tác động không đồng nhất theo khung giờ, loại luồng và khoảng cách, và lan ra các vùng lân cận "
         "theo mức phơi nhiễm. Các chỉ tiêu giá cước và thu nhập tài xế bị chi phối bởi xu hướng có sẵn nên không thể kết luận. Chương 8 "
         "thảo luận ý nghĩa của các kết quả này, sau khi Chương 5 đến 7 bổ sung phần xử lý phân tán, quản trị dữ liệu và phân tích kinh "
         "doanh.")
