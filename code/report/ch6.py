"""Chương 6. Quản trị dữ liệu, quyền riêng tư và quản trị rủi ro."""
import numpy as np
import pandas as pd

from lib import vint, vn
from results import pct_log


def build(rp, R):
    cat = R.t("t68_data")
    fpr = R.t("t68b")
    lin = R.t("t69")
    sha = R.t("t70")
    rec = R.t("t71")
    an = R.t("t72_daily")
    anb = R.t("t72b")
    anc = R.t("t72c")
    pch = R.t("t72d").set_index("service")
    tr = R.t("t73_trip")
    trp = R.t("t73b")
    trc = R.t("t73c")
    trd = R.t("t73d")
    kan = R.t("t74")
    dp = R.t("t75b")
    rto = R.t("t76")
    q = R.t("t06")
    ilog = R.JS["governance/integrity"]
    tlog = R.JS["governance/tripanom"]
    dlog = R.JS["governance/dp"]
    plog = R.JS["governance/privacy"]

    rp.H1("CHƯƠNG 6. QUẢN TRỊ DỮ LIỆU, QUYỀN RIÊNG TƯ VÀ QUẢN TRỊ RỦI RO")
    rp.PS(
        "Một pipeline cho kết quả đúng hôm nay chưa đủ để được tin dùng lâu dài. Người dùng kết quả cần biết dữ liệu nào nằm ở đâu, "
        "được tạo ra từ đâu, có bị thay đổi không, chất lượng có ổn định không, và việc công bố nó có gây hại cho ai không. Chương 2 "
        "và Chương 7 của bài giảng gọi chung các câu hỏi này là quản trị dữ liệu và quản trị rủi ro. Chương này trả lời chúng trên "
        "chính tài sản dữ liệu của đồ án, bằng các phép đo có thể chạy lại, thay vì chỉ mô tả khung lý thuyết.",
        "Câu hỏi nghiên cứu tương ứng là RQ6: tài sản dữ liệu của đồ án có những rủi ro nào về tính toàn vẹn, chất lượng và quyền "
        "riêng tư, và có thể công bố dữ liệu tổng hợp theo cách bảo vệ quyền riêng tư mà vẫn giữ được kết luận chính sách hay "
        "không. Bảng 6.1 đối chiếu từng chủ đề của bài giảng với phần triển khai trong chương.")
    fw = pd.DataFrame([
        ("2.6 Metadata và Data Catalog", "Danh mục dữ liệu tự động cho ba lớp, dấu vân tay lược đồ", "6.1", "t68"),
        ("2.6 Metadata (phả hệ)", "Phả hệ trích tự động từ mã nguồn: bước nào đọc, ghi bảng nào", "6.2", "t69, hình phả hệ"),
        ("7.5 Bảo vệ chuỗi cung ứng số", "Băm SHA-256 mọi tệp nguồn; kiểm tra lại ngẫu nhiên", "6.3", "t70"),
        ("2.7 Kiểm soát chất lượng", "Đối soát số dòng giữa các lớp; biểu đồ kiểm soát tỷ lệ loại", "6.4", "t71, t72d"),
        ("7.2 Phát hiện bất thường tự động", "Ngày bất thường theo z-score bền vững", "6.5", "t72"),
        ("7.1 Phát hiện gian lận", "Chuyến bất thường: Isolation Forest và quy tắc nghiệp vụ", "6.6", "t73"),
        ("2.8 Quyền riêng tư và tuân thủ", "Đo rủi ro tái nhận dạng bằng k-ẩn danh", "6.7", "t74"),
        ("2.8 Quyền riêng tư (công nghệ)", "Quyền riêng tư vi phân cho bảng công bố, đo ảnh hưởng tới DiD", "6.8", "t75"),
        ("7.4, 7.7 Zero Trust và phục hồi", "Thời gian dựng lại từng lớp (RTO) đo từ nhật ký", "6.9", "t76"),
        ("7.8 Khung quản trị rủi ro", "Sổ đăng ký rủi ro dựa trên bằng chứng của chương", "6.10", "Sổ đăng ký rủi ro"),
    ], columns=["Chủ đề bài giảng", "Triển khai trong đồ án", "Mục", "Kết quả"])
    rp.TAB(fw, "Đối chiếu chủ đề quản trị dữ liệu và rủi ro của bài giảng với phần triển khai", widths=[4.2, 7.2, 1.2, 3.4],
           size=10, align=["left", "left", "center", "left"], source="Nguồn: tác giả tổng hợp.")

    # ================================================================ 6.1
    rp.H2("6.1. Danh mục dữ liệu và siêu dữ liệu")
    t = pd.DataFrame({"Lớp": cat.layer, "Tập dữ liệu": cat.dataset, "Tệp": cat.files.map(vint), "Số dòng": cat.rows.map(vint),
                      "Cột": cat["columns"].map(vint), "Nhóm dòng": cat.row_groups.map(vint),
                      "MB": cat.size_mb.map(lambda v: vn(v, 1)), "Vân tay lược đồ": cat.schema_fp})
    rp.TAB(t, "Danh mục dữ liệu của đồ án, tạo tự động từ siêu dữ liệu Parquet", widths=[1.5, 4.6, 1.1, 2.6, 1.1, 1.6, 1.6, 2.1],
           size=9, align=["left", "left"] + ["center"] * 6, source="Nguồn: t68_data_catalog.csv.")
    br = cat[cat.layer == "Bronze"]
    sv = cat[cat.layer == "Silver"]
    gd = cat[cat.layer == "Gold"]
    rp.PS(
        f"Danh mục được dựng bằng cách đọc chân tệp Parquet, không mở dữ liệu, nên chạy trong vài giây cho cả "
        f"{vn(cat.size_mb.sum() / 1024, 1)} GB. Mỗi dòng ghi số tệp, số dòng, số cột, số nhóm dòng, dung lượng và một dấu vân tay lược "
        f"đồ, là mã băm của danh sách tên và kiểu cột. Ba lớp có quy mô rất khác nhau: Bronze {vint(br.rows.sum())} dòng, Silver "
        f"{vint(sv.rows.sum())} dòng sau khi loại bản ghi lỗi, Gold chỉ {vint(gd.rows.sum())} dòng. Lớp Gold chiếm "
        f"{vn(100 * gd.size_mb.sum() / br.size_mb.sum(), 1)}% dung lượng của Bronze nhưng chứa mọi thông tin mà các phân tích nhân "
        f"quả cần.",
        f"Dấu vân tay lược đồ cho phép phát hiện lệch lược đồ tự động. Ở lớp Bronze, mỗi nguồn có đúng hai lược đồ, tách chính xác "
        f"tại ranh giới 2024/2025 do cột cbd_congestion_fee được thêm vào. Ở lớp Silver, mọi phân vùng có cùng số cột nhưng dấu vân tay "
        f"vẫn khác nhau giữa các năm. Chính khác biệt này, cụ thể là kiểu của cột phí (DECIMAL ở năm 2024, số thực ở năm 2025), là "
        f"gốc của lỗi ép kiểu phát hiện ở mục 5.2. Như vậy, danh mục đã chứa sẵn tín hiệu cảnh báo; điều còn thiếu là một quy "
        f"tắc tự động buộc các phân vùng của cùng một bảng phải có cùng dấu vân tay. Đây là một ví dụ cụ thể cho luận điểm của mục 2.6 "
        f"bài giảng rằng danh mục dữ liệu chỉ có giá trị khi được gắn với kiểm tra tự động.")

    # ================================================================ 6.2
    rp.H2("6.2. Phả hệ dữ liệu")
    rp.FIG(R.fig("f47"), "Phả hệ dữ liệu của đồ án: từ Bronze, Silver, các bảng Gold đến từng bước phân tích và sản phẩm", width_cm=15.5)
    deps = lin[lin.reads_gold.fillna("").str.contains("zone_day_pu")]
    chg = R.t("t61c")
    rp.PS(
        f"Phả hệ được trích tự động từ mã nguồn của {vint(len(lin))} bước: với mỗi tệp mã, chương trình tìm tên các bảng Gold được "
        f"nhắc đến (trực tiếp hoặc qua mô-đun panels.py), các tệp bảng kết quả được ghi (tiền tố tNN) và các hình được lưu (tiền tố "
        f"fNN). Tổng cộng các bước tạo ra {vint(lin.n_tables.sum())} tệp bảng và {vint(lin.n_figures.sum())} hình. Cách trích này "
        f"không hoàn hảo, vì nó dựa trên tên chứ không dựa trên thực thi, nhưng có ưu điểm là luôn cập nhật theo mã mà không cần "
        f"người khai báo.",
        f"Giá trị thực tiễn của phả hệ thể hiện khi có sự cố. Khi lỗi ép kiểu ở bước 04 được phát hiện, câu hỏi đầu tiên là những kết "
        f"quả nào bị ảnh hưởng. Theo phả hệ, bảng zone_day_pu được {vint(len(deps))} bước đọc "
        f"({', '.join(deps.step.str.split('_').str[0])}), và các bảng Gold khác chứa cột phí cũng được hợp nhất ở cùng bước. Vì vậy "
        f"toàn bộ các bước từ 06 đến 14 được chạy lại, rồi bước 15b so từng tệp bảng kết quả với bản chụp trước khi sửa: trong "
        f"{vint(len(chg))} tệp được so, chỉ {vint(chg.changed.sum())} tệp thay đổi "
        f"({', '.join(chg[chg.changed].file.str.replace('.csv', '', regex=False))}), và các cột thay đổi đều là chỉ tiêu phí CBD hoặc "
        f"các đại lượng suy ra từ nó (trong t30 là các dòng phí CBD mỗi chuyến của taxi vàng). Không có phả hệ và phép so sánh này, "
        f"cách an toàn duy nhất là chạy lại mọi thứ mà không biết chắc thay đổi nằm ở đâu.")

    # ================================================================ 6.3
    rp.H2("6.3. Tính toàn vẹn và chuỗi cung ứng dữ liệu")
    rp.PS(
        f"Dữ liệu nguồn của đồ án đến từ một bên thứ ba qua mạng phân phối nội dung. Mục 7.5 của bài giảng xếp loại rủi ro này vào "
        f"chuỗi cung ứng số: tệp có thể bị hỏng khi tải, bị thay thế bởi phiên bản khác khi nguồn công bố lại, hoặc bị sửa trên máy "
        f"lưu trữ. Mọi phân tích phía sau đều thừa hưởng rủi ro đó. Biện pháp cơ bản là ghi lại dấu băm mật mã của từng tệp ngay khi "
        f"nhận và kiểm tra lại trước mỗi lần xử lý.",
        f"Đồ án tính SHA-256 cho {vint(ilog['files'])} tệp của lớp Bronze, tổng {vn(ilog['total_gb'], 2)} GB, trong "
        f"{vn(ilog['seconds'], 1)} giây, tức khoảng {vn(ilog['throughput_mb_s'], 1)} MB mỗi giây, giới hạn bởi tốc độ đọc của ổ đĩa "
        f"qua lớp chia sẻ thư mục của máy ảo. Việc băm được làm tăng dần, lưu kết quả sau mỗi tệp, nên có thể dừng và chạy tiếp. Ba "
        f"tệp chọn ngẫu nhiên được băm lại để kiểm tra: "
        f"{', '.join(c['file'] for c in ilog['reverify'])}; cả ba đều "
        f"{'khớp' if all(c['match'] for c in ilog['reverify']) else 'KHÔNG khớp'}. Danh sách đầy đủ nằm ở Phụ lục H.",
        "Trong một hệ thống vận hành, bản kê dấu băm này đóng vai trò hợp đồng giữa lớp Bronze và các lớp sau: nhật ký của mỗi phân "
        "vùng Silver nên ghi dấu băm của tệp nguồn đã dùng, để khi nguồn thay đổi thì biết chính xác phân vùng nào cần xử lý lại. Đây "
        "cũng là cách các định dạng bảng giao dịch như Delta Lake và Iceberg ghi nhận phiên bản dữ liệu, chỉ khác ở mức chi tiết.")

    # ================================================================ 6.4
    rp.H2("6.4. Đối soát giữa các lớp và giám sát chất lượng")
    rp.H3("6.4.1. Đối soát số dòng")
    rp.P(f"Với mỗi trong {vint(len(rec))} phân vùng tháng-dịch vụ, đồ án kiểm tra ba đẳng thức: số dòng trong siêu dữ liệu tệp Bronze "
         f"bằng số dòng mà bước 03 đã đọc; số dòng đã đọc bằng số dòng bị loại cộng số dòng vào Silver; và số dòng Silver ghi trong "
         f"nhật ký bằng số dòng trong siêu dữ liệu các tệp Silver. Kết quả: {vint(rec.check_bronze.sum())}/{vint(len(rec))}, "
         f"{vint(rec.check_balance.sum())}/{vint(len(rec))} và {vint(rec.check_silver.sum())}/{vint(len(rec))} phân vùng đạt. Không "
         f"có bản ghi nào bị mất hoặc bị đếm hai lần giữa các lớp, kể cả khi mỗi tháng HVFHV được xử lý thành bốn khúc riêng.")
    rp.H3("6.4.2. Biểu đồ kiểm soát tỷ lệ loại bỏ")
    ph, py = pch.loc["hvfhv"], pch.loc["yellow"]
    rp.FIG(R.fig("f49"), "Biểu đồ kiểm soát tỷ lệ bản ghi bị loại theo tháng: giới hạn p nhị thức và giới hạn p' của Laney")
    y24 = q[(q.service == "yellow") & (q.month < "2025-01")]
    y25 = q[(q.service == "yellow") & (q.month >= "2025-01")]
    fare24 = 100 * y24.q_bad_fare.sum() / y24.n_raw.sum()
    fare25 = 100 * y25.q_bad_fare.sum() / y25.n_raw.sum()
    h24 = q[(q.service == "hvfhv") & (q.month < "2025-01")]
    h25 = q[(q.service == "hvfhv") & (q.month >= "2025-01")]
    rp.PS(
        f"Tỷ lệ bản ghi bị loại của mỗi tháng được theo dõi như một quá trình sản xuất. Biểu đồ p chuẩn đặt giới hạn kiểm soát ở ±3 "
        f"độ lệch chuẩn nhị thức quanh tỷ lệ trung bình. Với khoảng 20 triệu bản ghi mỗi tháng, giới hạn này hẹp đến mức cả "
        f"{vint(ph.out_p_chart)}/{vint(ph.months)} tháng HVFHV và {vint(py.out_p_chart)}/{vint(py.months)} tháng taxi vàng đều nằm "
        f"ngoài. Đây là vấn đề đã biết của biểu đồ kiểm soát trên dữ liệu lớn: khi n rất lớn, biến động giữa các tháng do nguyên "
        f"nhân thông thường đã lớn hơn nhiều so với biến động nhị thức, nên biểu đồ báo động liên tục và mất giá trị.",
        f"Biểu đồ p' của Laney (2002) xử lý bằng cách ước lượng độ phân tán thật từ khoảng biến động di chuyển của z-score. Hệ số hiệu "
        f"chỉnh ước lượng được là {vn(ph.sigma_z, 1)} cho HVFHV và {vn(py.sigma_z, 1)} cho taxi vàng, nghĩa là độ phân tán thật lớn "
        f"hơn độ phân tán nhị thức hàng chục lần. Với giới hạn p', HVFHV chỉ còn {vint(ph.out_laney)} tháng vượt kiểm soát "
        f"({ph.laney_months.replace(';', ', ')}), và tỷ lệ loại dao động quanh {vn(ph.pbar_pct, 2)}% (năm 2024: "
        f"{vn(100 * h24.n_rejected.sum() / h24.n_raw.sum(), 2)}%, năm 2025: {vn(100 * h25.n_rejected.sum() / h25.n_raw.sum(), 2)}%). "
        f"Đây là quá trình ổn định.",
        f"Taxi vàng thì khác: {vint(py.out_laney)} tháng vượt giới hạn p', và tỷ lệ loại tăng từ khoảng {vn(100 * y24.n_rejected.sum() / y24.n_raw.sum(), 1)}% "
        f"năm 2024 lên {vn(100 * y25.n_rejected.sum() / y25.n_raw.sum(), 1)}% năm 2025, cao nhất {vn(py.p_max_pct, 1)}%. Phân rã theo "
        f"quy tắc cho thấy nguyên nhân chính là quy tắc giá cước (giá không dương hoặc vượt 1.000 USD): tỷ lệ vi phạm quy tắc này tăng "
        f"từ {vn(fare24, 2)}% lên {vn(fare25, 2)}% số bản ghi. Sự thay đổi bắt đầu đúng tháng 01/2025, trùng với thời điểm có phí. Đồ án "
        f"không xác định được nguyên nhân từ dữ liệu, nhưng hàm ý đối với phân tích nhân quả là rõ: nếu bản ghi bị loại khác nhau "
        f"giữa vùng xử lý và vùng đối chứng, mẫu Silver của taxi vàng năm 2025 có thể bị chọn lọc theo cách tương quan với chính "
        f"sách. Đây là một lý do nữa, bên cạnh những lý do đã nêu ở mục 4.13, để coi kết quả của taxi vàng là kém chắc chắn hơn "
        f"HVFHV.")

    # ================================================================ 6.5
    rp.H2("6.5. Phát hiện ngày bất thường")
    rp.PS(
        "Giám sát chất lượng ở mức bản ghi không phát hiện được các vấn đề ở mức tổng hợp, chẳng hạn một ngày thiếu dữ liệu vì lỗi "
        "truyền tệp, hoặc một ngày có lưu lượng bất thường vì sự kiện bên ngoài. Mục 7.2 của bài giảng đề xuất phát hiện bất thường "
        "tự động cho mục đích này. Đồ án dùng một phương pháp đơn giản, minh bạch và bền với ngoại lai: với mỗi ngày và mỗi nhóm vùng, "
        "giá trị kỳ vọng của log số chuyến là trung vị của các ngày cùng thứ trong cửa sổ ±28 ngày (không gồm chính ngày đó), thang "
        "đo là độ lệch tuyệt đối trung vị (MAD) nhân 1,4826, và ngày có |z| > 3,5 được đánh dấu.")
    rp.FIG(R.fig("f48"), "Số chuyến HVFHV đón trong CRZ theo ngày, giá trị kỳ vọng và các ngày bất thường")
    t = pd.DataFrame({"Dịch vụ": anc.service.map({"hvfhv": "HVFHV", "yellow": "Taxi vàng"}),
                      "Nhóm vùng": anc.grp.map({"CRZ": "CRZ", "MN_NORTH": "Manhattan phía bắc", "OUTER": "Quận ngoài",
                                                "AIRPORT": "Sân bay"}),
                      "Số ngày": anc.days.map(vint), "Bất thường": anc.flagged.map(vint),
                      "Thấp bất thường": anc.flagged_low.map(vint), "Cao bất thường": anc.flagged_high.map(vint)})
    rp.TAB(t, "Số ngày bất thường theo dịch vụ và nhóm vùng, 2024–2025", widths=[2.4, 4.0, 2.0, 2.4, 2.6, 2.6], size=10,
           source="Nguồn: t72c_anomaly_summary.csv.")
    from pandas.tseries.holiday import USFederalHolidayCalendar
    hol = USFederalHolidayCalendar().holidays("2024-01-01", "2025-12-31", return_name=True)
    top = anb.copy()
    top["d"] = pd.to_datetime(top.d)
    top = top.reindex(top.z.abs().sort_values(ascending=False).index).head(20)

    HN = {"New Year's Day": "Năm mới", "Birthday of Martin Luther King, Jr.": "Ngày Martin Luther King",
          "Washington's Birthday": "Ngày Tổng thống", "Memorial Day": "Ngày Tưởng niệm",
          "Juneteenth National Independence Day": "Ngày Juneteenth", "Independence Day": "Ngày Độc lập (04/07)",
          "Labor Day": "Ngày Lao động", "Columbus Day": "Ngày Columbus", "Veterans Day": "Ngày Cựu chiến binh",
          "Thanksgiving Day": "Lễ Tạ ơn", "Christmas Day": "Giáng sinh"}

    def near(d):
        for dd, name in hol.items():
            if abs((d - dd).days) <= 1:
                return HN.get(name, name) + ("" if d == dd else " (±1 ngày)")
        if (d.month == 12 and d.day >= 24) or (d.month == 1 and d.day <= 3):
            return "Kỳ nghỉ cuối năm"
        if d == pd.Timestamp("2025-01-05"):
            return "Ngày đầu thu phí CRZ"
        return ""
    DOW = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ nhật"]
    t = pd.DataFrame({"Ngày": top.d.dt.strftime("%d/%m/%Y"), "Thứ": top.d.dt.dayofweek.map(lambda i: DOW[i]),
                      "Số chuyến": top.n.map(vint), "Lệch so với kỳ vọng": top.dev_pct.map(lambda v: vn(v, 1, pct=True, sign=True)),
                      "z bền vững": top.z.map(lambda v: vn(v, 1)), "Ngày lễ liên bang gần nhất": top.d.map(near)})
    rp.TAB(t, "Hai mươi ngày bất thường nhất của số chuyến HVFHV đón trong CRZ", widths=[2.4, 2.0, 2.2, 2.8, 2.0, 4.6], size=9.5,
           align=["center"] * 5 + ["left"], source="Nguồn: t72b_anomaly_days_crz.csv; ngày lễ theo lịch liên bang Hoa Kỳ của pandas.")
    crz = anc[(anc.service == "hvfhv") & (anc.grp == "CRZ")].iloc[0]
    n_h = int(top.d.map(near).ne("").sum())
    rp.PS(
        f"Trong {vint(crz.days)} ngày, phương pháp đánh dấu {vint(crz.flagged)} ngày bất thường với CRZ, phần lớn là thấp bất thường "
        f"({vint(crz.flagged_low)} ngày). Trong 20 ngày bất thường nhất, {vint(n_h)} ngày trùng hoặc liền kề ngày lễ liên bang hay kỳ "
        f"nghỉ cuối năm, như Ngày Độc lập 04/07, Lễ Tạ ơn, Giáng sinh và Ngày Tưởng niệm. Đây là kiểm tra thực tế cho phương pháp: nó "
        f"tìm lại được các sự kiện đã biết mà không cần được cho biết trước. Ngày 05/01/2025 cũng nằm trong danh sách bất thường thấp.",
        "Tỷ lệ ngày bị đánh dấu khá cao (khoảng 7–8%) vì cửa sổ so sánh chỉ gồm tám ngày cùng thứ, nên MAD ước lượng nhỏ và nhạy, "
        "và vì ở đầu năm 2024 cửa sổ bị cắt một phía. Trong vận hành thật, ngưỡng nên được chọn theo chi phí của cảnh báo sai so với "
        "cảnh báo bỏ sót, và lịch ngày lễ nên được đưa vào mô hình kỳ vọng. Với phân tích nhân quả, danh sách này có công dụng trực "
        "tiếp: nó cho biết các tuần nào có thể làm nhiễu panel vùng × tuần. Vì các ngày lễ rơi vào cùng tuần trong năm ở cả hai năm, "
        "đặc tả DDD khử mùa vụ ở Chương 4 đã tự động kiểm soát phần lớn ảnh hưởng này.")

    # ================================================================ 6.6
    rp.H2("6.6. Phát hiện chuyến đi bất thường")
    rp.PS(
        f"Mục 7.1 của bài giảng trình bày phát hiện gian lận trong giao dịch. Với dữ liệu chuyến đi, gian lận có thể là ghi quãng "
        f"đường hoặc giá cước sai, chuyến ảo để nhận thưởng, hoặc lỗi thiết bị. Đồ án không có nhãn gian lận, nên bài toán là phát "
        f"hiện bất thường không giám sát. Isolation Forest (Liu, Ting và Zhou, 2008) được huấn luyện trên {vint(tlog['n'])} chuyến "
        f"HVFHV của mẫu 0,25% với tám đặc trưng: log quãng đường, log thời lượng, log giá cước, log thu nhập tài xế, tốc độ, log giá "
        f"mỗi dặm, tỷ lệ thu nhập tài xế trên giá và tỷ lệ tip trên giá. Thuật toán cô lập mỗi điểm bằng các phép chia ngẫu nhiên; "
        f"điểm bất thường là điểm bị cô lập sau ít phép chia. Ngưỡng được đặt để đánh dấu 0,5% chuyến. Việc huấn luyện và chấm điểm mất "
        f"{vn(tlog['fit_score_s'], 1)} giây.")
    t = pd.DataFrame({"Quy tắc": tr.rule, "Số chuyến": tr.n.map(vint), "% mẫu": tr.pct.map(lambda v: vn(v, 3)),
                      "% cũng bị Isolation Forest đánh dấu": tr.overlap_iso_pct.map(lambda v: vn(v, 1))})
    rp.TAB(t, "Quy tắc nghiệp vụ và mức trùng với Isolation Forest", widths=[7.0, 2.4, 2.0, 4.6], size=10,
           align=["left", "center", "center", "center"], source="Nguồn: t73_trip_anomaly_rules.csv.")
    t = trp.rename(columns={"Unnamed: 0": "Đặc trưng"})
    lab = {"miles": "Quãng đường (dặm)", "time_s": "Thời lượng (giây)", "fare": "Giá cước (USD)", "driver_pay": "Thu nhập tài xế (USD)",
           "mph": "Tốc độ (dặm/giờ)", "fare_pm": "Giá / dặm (USD)", "pay_ratio": "Thu nhập tài xế / giá", "tip_ratio": "Tip / giá",
           "wait_min": "Thời gian chờ (phút)"}
    t["Đặc trưng"] = t["Đặc trưng"].map(lab)
    for c in ("Bình thường", "Bất thường"):
        t[c] = t[c].map(lambda v: vn(v, 2))
    rp.TAB(t, "Trung vị các đặc trưng của chuyến bình thường và bất thường", widths=[6, 5, 5], size=10.5,
           source="Nguồn: t73b_trip_anomaly_profile.csv.")
    rp.FIG(R.fig("f50"), "Quãng đường và giá cước của chuyến bình thường và chuyến bị Isolation Forest đánh dấu", width_cm=14)
    r0 = tr.iloc[0]
    ab = trp.set_index(trp.columns[0])
    d_pre, d_post = trd[(trd.crz == False) & (trd.post == False)].iso_flag.iloc[0], trd[(trd.crz == False) & (trd.post == True)].iso_flag.iloc[0]  # noqa: E712
    c_pre, c_post = trd[(trd.crz == True) & (trd.post == False)].iso_flag.iloc[0], trd[(trd.crz == True) & (trd.post == True)].iso_flag.iloc[0]  # noqa: E712
    rp.PS(
        f"Chuyến bị đánh dấu có trung vị quãng đường {vn(ab.loc['miles', 'Bất thường'], 1)} dặm so với "
        f"{vn(ab.loc['miles', 'Bình thường'], 1)} dặm của chuyến bình thường, giá cước {vn(ab.loc['fare', 'Bất thường'], 1)} so với "
        f"{vn(ab.loc['fare', 'Bình thường'], 1)} USD, và đặc biệt là tỷ lệ tip {vn(ab.loc['tip_ratio', 'Bất thường'], 2)} so với "
        f"{vn(ab.loc['tip_ratio', 'Bình thường'], 2)}. Nói cách khác, phần lớn chuyến bất thường là chuyến dài có tip cao, tức nằm ở "
        f"đuôi của phân phối nhiều chiều, không nhất thiết là gian lận. Các quy tắc nghiệp vụ cụ thể (tip lớn hơn giá, tốc độ gần "
        f"bằng 0 trong chuyến dài, cùng vùng đón trả nhưng đi xa) trùng với Isolation Forest ở mức 18–25%, cho thấy hai cách tiếp cận "
        f"bổ sung cho nhau.",
        f"Quy tắc đầu tiên trong bảng cho thấy cần hiểu nghiệp vụ trước khi đặt quy tắc. Nếu coi \"thu nhập tài xế lớn hơn giá cước cộng tip\" là dấu "
        f"hiệu bất thường, {vn(r0.pct, 1)}% chuyến sẽ bị đánh dấu, và chỉ {vn(r0.overlap_iso_pct, 1)}% trong số đó bị Isolation "
        f"Forest coi là bất thường. Ở New York, thu nhập tài xế HVFHV được tính theo công thức tối thiểu của TLC dựa trên thời gian và "
        f"quãng đường, độc lập với giá mà nền tảng thu của khách (mục 2.3.3), nên nền tảng có thể trả tài xế nhiều hơn giá thu ở chuyến "
        f"ngắn hoặc chuyến có khuyến mãi. Đây là hiện tượng thường xuyên, không phải bất thường. Một hệ thống phát hiện gian lận dựa "
        f"trên quy tắc viết mà không có kiến thức này sẽ tạo ra hàng chục triệu cảnh báo sai mỗi năm trên toàn bộ dữ liệu.",
        f"Tỷ lệ chuyến bất thường tăng sau chính sách ở cả chuyến chạm CRZ (từ {vn(c_pre, 2)}% lên {vn(c_post, 2)}%) và chuyến không "
        f"chạm CRZ (từ {vn(d_pre, 2)}% lên {vn(d_post, 2)}%), với mức tăng gần như bằng nhau. Như vậy, phí không làm thay đổi đáng kể "
        f"tỷ lệ chuyến bất thường của riêng vùng chịu phí; mức tăng chung phản ánh thay đổi của phân phối chuyến đi giữa hai năm, mà "
        f"Isolation Forest huấn luyện trên dữ liệu gộp hai năm diễn giải như bất thường.")

    # ================================================================ 6.7
    rp.H2("6.7. Rủi ro tái nhận dạng trong dữ liệu công bố")
    rp.PS(
        "TLC không công bố định danh hành khách, tài xế hay biển số, và chỉ công bố vị trí ở mức vùng taxi. Câu hỏi là mức ẩn danh "
        "này đủ đến đâu. Khung k-ẩn danh (Sweeney, 2002) trả lời bằng cách xét các thuộc tính định danh gián tiếp (quasi-identifier): "
        "những thuộc tính mà một người ngoài có thể biết về một chuyến cụ thể, chẳng hạn nơi và lúc một người được đón. Một bản ghi là "
        "k-ẩn danh nếu có ít nhất k−1 bản ghi khác trùng với nó trên mọi thuộc tính định danh gián tiếp. Nếu k = 1, người biết các "
        "thuộc tính đó xác định được duy nhất chuyến đi và đọc được mọi thuộc tính còn lại, như giá cước, tip và điểm trả.",
        f"Đồ án đo k cho {vint(plog['trips'])} chuyến HVFHV tháng {plog['month'].split('-')[1]}/{plog['month'].split('-')[0]} với "
        f"mười tổ hợp thuộc tính, từ thô nhất (quận đón, quận trả trong tháng) đến đúng mức chi tiết của bản công bố (vùng đón, vùng "
        f"trả và thời điểm đón đến giây). Với mỗi tổ hợp, đồ án đếm kích thước từng lớp tương đương bằng một phép GROUP BY trên DuckDB "
        f"và tính tỷ lệ chuyến nằm trong lớp có k = 1, k < 5 và k < 10.")
    t = pd.DataFrame({"Thuộc tính định danh gián tiếp": kan.qi, "Số lớp": kan.classes.map(vint),
                      "k = 1 (%)": kan.unique_pct.map(lambda v: vn(v, 2)), "k < 5 (%)": kan.lt5_pct.map(lambda v: vn(v, 2)),
                      "k < 10 (%)": kan.lt10_pct.map(lambda v: vn(v, 2)), "k trung vị": kan.median_class.map(vint)})
    rp.TAB(t, "Tỷ lệ chuyến nằm trong lớp tương đương nhỏ theo mức chi tiết của thuộc tính định danh gián tiếp",
           widths=[6.4, 2.2, 1.8, 1.8, 1.9, 1.9], size=9.5, align=["left"] + ["center"] * 5,
           source="Nguồn: t74_privacy_kanonymity.csv.")
    rp.FIG(R.fig("f51"), "Rủi ro tái nhận dạng theo mức chi tiết của thuộc tính định danh gián tiếp")
    kz = kan.set_index("qi")
    sec = kz.loc["Vùng đón, vùng trả, giây đón (như bản công bố)"]
    mnt = kz.loc["Vùng đón, vùng trả, phút đón"]
    hr = kz.loc["Vùng đón, vùng trả, ngày, giờ"]
    dy = kz.loc["Vùng đón, vùng trả, ngày"]
    bh = kz.loc["Quận đón, quận trả, ngày, giờ"]
    rp.PS(
        f"Kết quả cho thấy tổng quát hóa không gian ở mức vùng không bảo vệ được quyền riêng tư khi thời gian được công bố chính xác. "
        f"Ở đúng mức chi tiết của bản công bố, {vn(sec.unique_pct, 2)}% chuyến là duy nhất. Nếu người ngoài chỉ biết thời điểm đón đến "
        f"phút, tỷ lệ này vẫn là {vn(mnt.unique_pct, 1)}%. Giả sử một người được chụp ảnh lên xe ở một góc phố vào một phút xác định và "
        f"người ngoài biết người đó về khu nào: với xác suất gần như chắc chắn, người ngoài tìm được đúng chuyến đi và biết người đó đã "
        f"trả bao nhiêu, tip bao nhiêu. Đây chính là loại tấn công liên kết đã được nêu trong tài liệu về dữ liệu taxi New York "
        f"(Douriez và cộng sự, 2016) và trong nghiên cứu về tính duy nhất của dữ liệu di chuyển (de Montjoye và cộng sự, 2013).",
        f"Rủi ro giảm rất nhanh khi thời gian được làm thô. Ở mức vùng × ngày × giờ, còn {vn(hr.unique_pct, 1)}% chuyến duy nhất và "
        f"{vn(hr.lt5_pct, 1)}% chuyến có k < 5. Ở mức vùng × ngày, chỉ {vn(dy.unique_pct, 2)}% chuyến là duy nhất. Nếu vùng được gộp "
        f"thành quận, ngay cả ở mức ngày × giờ, tỷ lệ chuyến duy nhất chỉ còn {vn(bh.unique_pct, 3)}%. Hàm ý là quyết định công bố "
        f"nên cân nhắc cả hai chiều không gian và thời gian cùng lúc: bản công bố hiện tại đã thô về không gian nhưng rất chi tiết về "
        f"thời gian, và chiều thời gian là chiều mang rủi ro.",
        "Đối với đồ án, kết quả này có hai hàm ý. Thứ nhất, mọi phân tích của đồ án đều ở mức tổng hợp tối thiểu là vùng × ngày, và "
        "các bảng Gold không chứa thời điểm đón chi tiết, nên việc công bố các bảng Gold không tạo thêm rủi ro. Riêng bảng mẫu chuyến "
        "đi giữ nguyên thời điểm và chỉ nên dùng nội bộ. Thứ hai, trong khung của Nghị định 13/2023/NĐ-CP và GDPR, dữ liệu mà 99% bản "
        "ghi có thể được liên kết với một người cụ thể khi có thêm thông tin bên ngoài khó có thể được coi là dữ liệu ẩn danh hoàn "
        "toàn; một doanh nghiệp Việt Nam công bố dữ liệu tương tự cần đánh giá rủi ro này trước.")

    # ================================================================ 6.8
    rp.H2("6.8. Quyền riêng tư vi phân cho bảng công bố")
    rp.PS(
        "Nếu dữ liệu vi mô có rủi ro, một lựa chọn là chỉ công bố bảng tổng hợp. Nhưng bảng tổng hợp cũng có thể rò rỉ thông tin khi "
        "các ô nhỏ hoặc khi nhiều bảng được đối chiếu với nhau. Quyền riêng tư vi phân (Dwork và cộng sự, 2006; Dwork và Roth, 2014) "
        "cho một bảo đảm có thể chứng minh: kết quả công bố gần như không đổi dù có hay không có một bản ghi bất kỳ trong dữ liệu. Cơ "
        "chế Laplace đạt ε-quyền riêng tư vi phân cho một phép đếm bằng cách cộng nhiễu Laplace với thang đo 1/ε, vì thêm hoặc bớt một "
        "chuyến làm phép đếm đổi tối đa 1. ε nhỏ nghĩa là riêng tư hơn và nhiễu hơn.",
        "Câu hỏi thực nghiệm là: nếu TLC chỉ công bố bảng số chuyến theo vùng × ngày có nhiễu Laplace, người đánh giá chính sách còn "
        "rút ra được kết luận của Chương 4 không? Đồ án cộng nhiễu độc lập vào từng ô vùng × ngày của bảng zone_day_pu, dựng lại panel "
        "vùng × tuần với đúng tập vùng như bản gốc, và ước lượng lại TWFE log số chuyến. Mỗi mức ε được lặp 40 lần với hạt giống cố "
        "định.")
    base = dp.baseline_coef.iloc[0]
    t = pd.DataFrame({"ε": dp.eps.map(lambda v: vn(v, 3)),
                      "Độ lệch chuẩn nhiễu mỗi ô": dp.noise_sd_cell.map(lambda v: vn(v, 1)),
                      "Nhiễu / ô nhỏ (P5) (%)": dp.noise_rel_p5_cell_pct.map(lambda v: vn(v, 1)),
                      "Tác động TB (%)": dp.pct_effect_mean.map(lambda v: vn(v, 2)),
                      "Độ chệch (×100)": dp.bias.map(lambda v: vn(100 * v, 3)),
                      "Độ lệch chuẩn giữa lần lặp (×100)": dp.sd_coef.map(lambda v: vn(100 * v, 3)),
                      "RMSE (×100)": dp.rmse.map(lambda v: vn(100 * v, 3))})
    rp.TAB(t, f"Ước lượng TWFE log số chuyến khi bảng vùng × ngày được cộng nhiễu Laplace (40 lần lặp mỗi ε; bản gốc: "
              f"{vn(pct_log(base), 2)}%)", widths=[1.4, 2.6, 2.4, 2.2, 2.2, 3.0, 2.2], size=9.5,
           source="Nguồn: t75b_dp_summary.csv, t75_dp_replications.csv.")
    rp.FIG(R.fig("f52"), "Đánh đổi giữa ngân sách riêng tư ε và ước lượng tác động lên số chuyến", width_cm=14)
    e1 = dp[dp.eps == 0.05].iloc[0]
    e2 = dp[dp.eps == 0.01].iloc[0]
    e3 = dp[dp.eps == 0.001].iloc[0]
    rp.PS(
        f"Với ε từ 0,05 trở lên, ước lượng gần như không đổi: tác động trung bình là {vn(e1.pct_effect_mean, 2)}% so với "
        f"{vn(pct_log(base), 2)}% của bản gốc, và độ lệch chuẩn giữa các lần lặp nhỏ hơn sai số chuẩn thống kê của ước lượng gốc "
        f"({vn(100 * dp.baseline_se.iloc[0], 3)}) hàng chục lần. Ở ε = 0,01, một mức riêng tư rất chặt theo tiêu chuẩn thực hành, "
        f"RMSE vẫn chỉ {vn(100 * e2.rmse, 3)} điểm log. Chỉ khi ε = 0,001, nhiễu mỗi ô có độ lệch chuẩn {vn(e3.noise_sd_cell, 0)} chuyến, "
        f"lớn gấp {vn(e3.noise_rel_p5_cell_pct / 100, 1)} lần ô nhỏ ở phân vị 5, ước lượng mới bị kéo về 0 (còn "
        f"{vn(e3.pct_effect_mean, 2)}%). Hiện tượng kéo về 0 này là chệch do sai số đo lường ở biến phụ thuộc dạng log khi phải cắt "
        f"số đếm âm về 1, chứ không phải do nhiễu trung bình khác 0.",
        f"Kết quả rộng hơn là đánh đổi riêng tư – hữu dụng phụ thuộc rất mạnh vào mức tổng hợp mà câu hỏi phân tích cần. Câu hỏi của "
        f"đồ án được trả lời trên panel vùng × tuần với {vint(dlog['zones'])} vùng, mỗi ô tuần gộp bảy ô ngày có hàng trăm đến hàng "
        f"nghìn chuyến, nên nhiễu bảo vệ từng chuyến gần như biến mất khi tổng hợp. Cục Điều tra Dân số Hoa Kỳ đã áp dụng quyền riêng "
        f"tư vi phân cho kết quả điều tra dân số 2020 dựa trên cùng lập luận (Abowd, 2018). Đối với TLC, điều này gợi ý một mô hình "
        f"công bố hai tầng: bảng tổng hợp có nhiễu ở mức chi tiết khá cao cho công chúng, và dữ liệu vi mô chỉ cho nhà nghiên cứu qua "
        f"thỏa thuận sử dụng.",
        "Cần nói rõ giới hạn của bảo đảm này. Thực nghiệm dùng quyền riêng tư vi phân ở mức chuyến: nó bảo vệ việc một chuyến cụ thể "
        "có mặt hay không, không bảo vệ một hành khách đi nhiều chuyến. Bảo vệ ở mức người dùng cần biết định danh người dùng để giới "
        "hạn số chuyến mỗi người đóng góp, thông tin mà dữ liệu công bố không có. Ngoài ra, mỗi bảng công bố thêm tiêu tốn thêm ngân "
        "sách riêng tư, nên tổng ε của một chương trình công bố nhiều bảng phải được quản lý như một ngân sách thật.")

    # ================================================================ 6.9
    rp.H2("6.9. Bảo mật, Zero Trust và phục hồi sau sự cố")
    rp.H3("6.9.1. Phân loại tài sản và nguyên tắc Zero Trust")
    zt = pd.DataFrame([
        ("Bronze (tệp gốc TLC)", "Công khai", "Toàn vẹn: dấu băm SHA-256; chỉ đọc sau khi nhận", "Tải lại từ nguồn"),
        ("Silver (chuyến đã làm sạch)", "Nội bộ, rủi ro tái nhận dạng cao", "Quyền đọc theo vai trò; không xuất ra ngoài", "Dựng lại từ Bronze"),
        ("Gold: bảng tổng hợp", "Có thể công bố", "Kiểm tra kích thước ô nhỏ; có thể cộng nhiễu (mục 6.8)", "Dựng lại từ Silver"),
        ("Gold: mẫu chuyến đi", "Nội bộ, rủi ro như Silver", "Chỉ dùng cho mô tả; không công bố", "Dựng lại từ Silver"),
        ("Mã nguồn và cấu hình", "Nội bộ hoặc công khai", "Quản lý phiên bản; rà soát khi thay đổi", "Kho mã"),
        ("Bảng kết quả và báo cáo", "Công bố sau kiểm duyệt", "Sinh tự động từ Gold; không có số gõ tay", "Chạy lại bước 06–17 và 13"),
    ], columns=["Tài sản", "Mức nhạy cảm", "Biện pháp kiểm soát", "Phục hồi"])
    rp.TAB(zt, "Phân loại tài sản dữ liệu và biện pháp kiểm soát", widths=[3.6, 3.4, 5.4, 3.6], size=9.5,
           align=["left"] * 4, source="Nguồn: tác giả đề xuất dựa trên kết quả mục 6.7 và 6.8.")
    rp.PS(
        "Kiến trúc Zero Trust (Rose và cộng sự, 2020), được trình bày ở mục 7.4 của bài giảng, bỏ giả định rằng mọi thứ bên trong "
        "mạng nội bộ là đáng tin. Mỗi yêu cầu truy cập được xác thực và cấp quyền riêng, theo nguyên tắc quyền tối thiểu. Áp dụng vào "
        "pipeline của đồ án, phân loại tài sản đúng quan trọng hơn lựa chọn công nghệ. Kết quả mục 6.7 cho thấy dữ liệu ở mức "
        "chuyến, dù ở Bronze hay Silver, có rủi ro tái nhận dạng cao; Silver còn được làm sạch và dễ truy vấn hơn nên cần kiểm soát "
        "truy cập chặt nhất. Ngược lại, lớp Gold chiếm chưa tới hai phần trăm dung lượng nhưng chứa toàn bộ thông tin cần cho phân tích và có thể công bố. Việc "
        "tách bạch này cho phép cấp cho phần lớn người dùng phân tích quyền đọc Gold mà không bao giờ chạm vào dữ liệu vi mô.")
    rp.H3("6.9.2. Mục tiêu thời gian phục hồi")
    t = pd.DataFrame({"Tình huống": rto.scenario, "Cách dựng lại": rto.rebuild, "Thời gian (phút)": rto.minutes.map(lambda v: vn(v, 1))})
    rp.TAB(t, "Thời gian phục hồi (RTO) đo từ nhật ký thực thi của pipeline", widths=[5.2, 7.6, 3.2], size=10,
           align=["left", "left", "center"], source="Nguồn: t76_recovery_rto.csv.")
    rp.PS(
        f"Mục 7.7 của bài giảng về phục hồi sau sự cố dùng hai chỉ tiêu: thời gian phục hồi mục tiêu (RTO) và điểm phục hồi mục tiêu "
        f"(RPO). Vì mỗi lớp của pipeline được dựng lại hoàn toàn từ lớp trước bằng mã có tính lũy đẳng, RTO có thể đo trực tiếp từ "
        f"nhật ký thay vì ước đoán. Mất toàn bộ Silver và Gold tốn khoảng {vn(rto.minutes.iloc[1], 0)} phút để dựng lại; mất riêng Gold "
        f"tốn khoảng {vn(rto.minutes.iloc[0], 0)} phút; mất một tháng HVFHV chỉ tốn khoảng {vn(rto.minutes.iloc[2], 1)} phút nhờ phân "
        f"vùng. RPO bằng 0 đối với dữ liệu, vì Bronze là bản sao của nguồn công khai và các lớp sau là hàm tất định của Bronze. Chỉ mã "
        f"nguồn và cấu hình là không tái tạo được và cần sao lưu theo quy tắc 3-2-1.",
        "Kiến trúc medallion có tính lũy đẳng còn có một lợi thế: chiến lược sao lưu có thể chỉ tập trung vào lớp "
        "Bronze và mã nguồn, còn Silver và Gold được coi là bộ đệm có thể tính lại. Cái giá phải trả là thời gian tính lại, và bảng trên "
        "cho biết chính xác cái giá đó.")

    # ================================================================ 6.10
    rp.H2("6.10. Sổ đăng ký rủi ro")
    rr = pd.DataFrame([
        ("Ép kiểu im lặng khi hợp nhất lược đồ", "Đã xảy ra (mục 5.2)", "Thấp (đã sửa)", "Đối chứng Spark; vân tay lược đồ; union_by_name"),
        ("Nguồn công bố lại tệp đã tải", "Có thể", "Trung bình", "Dấu băm SHA-256; ghi dấu băm vào nhật ký phân vùng"),
        ("Thay đổi chất lượng khác nhau giữa nhóm xử lý và đối chứng",
         "Đã quan sát ở taxi vàng (mục 6.4.2)", "Cao với kết quả taxi vàng", "Biểu đồ p'; phân tích riêng theo quy tắc loại bỏ"),
        ("Nhóm đối chứng bị ảnh hưởng lan tỏa", "Đã quan sát (mục 4.12)", "Cao với độ lớn ước lượng", "Loại vùng lân cận; báo cáo nhiều nhóm đối chứng"),
        ("Tái nhận dạng hành khách từ dữ liệu vi mô", "Rất cao ở mức chi tiết gốc (mục 6.7)", "Cao (pháp lý, uy tín)",
         "Chỉ công bố Gold; làm thô thời gian; quyền riêng tư vi phân"),
        ("Cảnh báo sai do quy tắc thiếu hiểu nghiệp vụ", "Đã quan sát (mục 6.6)", "Trung bình (chi phí vận hành)",
         "Kết hợp mô hình không giám sát với quy tắc có kiểm chứng"),
        ("Mất dữ liệu trung gian", "Có thể", "Thấp", "Dựng lại từ Bronze (thời gian ở mục 6.9.2)"),
        ("Hiểu sai kết quả có tiền xu hướng", "Đã quan sát với giá cước (mục 4.14)", "Cao với khuyến nghị chính sách",
         "Giả dược cho từng chỉ tiêu; không kết luận khi thất bại"),
    ], columns=["Rủi ro", "Khả năng / bằng chứng", "Mức ảnh hưởng", "Biện pháp kiểm soát"])
    rp.TAB(rr, "Sổ đăng ký rủi ro của pipeline và của các kết luận", widths=[4.4, 3.8, 3.0, 4.8], size=9.5,
           align=["left"] * 4, source="Nguồn: tác giả tổng hợp từ các kết quả của Chương 4, 5 và 6.")
    rp.PS(
        "Khung quản trị rủi ro ở mục 7.8 của bài giảng đề xuất nhận diện, đánh giá, xử lý và giám sát rủi ro một cách có hệ thống. Sổ "
        "đăng ký trên khác các danh sách rủi ro thường gặp ở một điểm: mỗi rủi ro được gắn với bằng chứng cụ thể trong đồ án, và phần "
        "lớn không phải là giả định mà đã xảy ra hoặc đã được đo. Bốn trong tám rủi ro liên quan đến tính đúng của kết luận phân tích "
        "chứ không phải đến an ninh hạ tầng. Với các dự án phân tích dữ liệu lớn, rủi ro lớn nhất thường là đưa ra quyết "
        "định dựa trên một con số sai mà không ai biết là sai, nhiều hơn là rủi ro bị tấn công.")
    rp.H2("6.11. Tiểu kết Chương 6")
    rp.P(f"Chương 6 đã áp dụng các công cụ quản trị dữ liệu và rủi ro lên chính tài sản dữ liệu của đồ án. Danh mục và phả hệ tự "
         f"động cho biết dữ liệu nằm ở đâu và kết quả nào phụ thuộc vào bảng nào; dấu băm và đối soát xác nhận toàn bộ {vint(len(rec))} "
         f"phân vùng không mất hay trùng bản ghi. Biểu đồ kiểm soát p' cho thấy chất lượng dữ liệu HVFHV ổn định, còn taxi vàng có "
         f"thay đổi rõ từ 01/2025, một rủi ro cho các kết luận về taxi vàng. Về quyền riêng tư, {vn(sec.unique_pct, 1)}% chuyến là duy "
         f"nhất ở mức chi tiết của bản công bố, nhưng bảng tổng hợp vùng × ngày có thể được bảo vệ bằng quyền riêng tư vi phân ở mức "
         f"ε = 0,01 mà không làm thay đổi kết luận chính sách về số chuyến.")
