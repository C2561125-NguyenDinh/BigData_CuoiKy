"""Phần mở đầu theo mẫu: bìa, lời cảm ơn, lời cam kết, tóm tắt, từ viết tắt."""
from docx.enum.text import WD_ALIGN_PARAGRAPH
from pathlib import Path

from docx.shared import Cm, Pt

from lib import vn, vint
from results import pct_log

TITLE = ("TÁC ĐỘNG KHÔNG ĐỒNG NHẤT VÀ HIỆU ỨNG LAN TỎA CỦA PHÍ GIẢM ÙN TẮC MANHATTAN "
         "LÊN THỊ TRƯỜNG GỌI XE CÔNG NGHỆ: TIẾP CẬN HỌC MÁY NHÂN QUẢ TRÊN KIẾN TRÚC "
         "LAKEHOUSE VỚI HÀNG TRĂM TRIỆU CHUYẾN ĐI")


STUDENT = "Đinh Nguyễn Tấn Nguyên – C25611252"
TEACHER = "TS. Nguyễn Thôn Dã"
COURSE = "Nghiên cứu Dữ liệu lớn trong kinh doanh"
COVER_IMG = Path(__file__).resolve().parent / "assets" / "uel_cover.jpg"


def cover(rp):
    """Trang bìa theo mẫu tiểu luận UEL: ảnh nền có viền, logo và dải màu; chữ đặt lên trên."""
    from docx.enum.section import WD_SECTION
    d = rp.doc
    s0 = d.sections[0]
    s0.left_margin, s0.right_margin = Cm(2.6), Cm(2.6)
    s0.top_margin, s0.bottom_margin = Cm(2.9), Cm(2.0)
    s0.different_first_page_header_footer = True   # bìa không in số ở chân trang
    rp.background(COVER_IMG)
    rp.P("KHOA HỆ THỐNG THÔNG TIN", indent=False, align="center", size=20, bold=True, space_after=0)
    sp = rp.P("", indent=False)
    sp.paragraph_format.space_after = Pt(140)
    rp.P("TIỂU LUẬN CUỐI KỲ", indent=False, align="center", size=14, bold=True, space_after=14)
    tp = rp.P(TITLE, indent=False, align="center", size=16, bold=True, space_after=8)
    tp.paragraph_format.line_spacing = 1.25
    tp.paragraph_format.space_after = Pt(30)
    rp.P(f"Môn học: {COURSE}", indent=False, align="center", size=16, bold=True, space_after=22)
    for lab, val, sa in (("GVHD:", TEACHER, 14), ("HVTH:", STUDENT, 0)):
        for txt, b, a in ((lab, True, 0), (val, False, sa)):
            p = rp.P(txt, indent=False, align="right", size=14, bold=b, space_after=a)
            p.paragraph_format.right_indent = Cm(2.9)
            p.paragraph_format.line_spacing = 1.2
    rp.FRAME("1", 0, 25.6, 21.0, size=12)
    rp.FRAME("TP.HCM, THÁNG 09/2026", 0, 26.8, 21.0, size=11, bold=True, color="FFFFFF")
    s1 = d.add_section(WD_SECTION.NEW_PAGE)
    s1.left_margin, s1.right_margin = Cm(3.0), Cm(2.0)
    s1.top_margin, s1.bottom_margin = Cm(2.0), Cm(2.0)
    s1.different_first_page_header_footer = False
    s1.footer.is_linked_to_previous = True
    rp._fresh = True


def commitment(rp, R):
    rp.H1("LỜI CAM KẾT", numbered=False, size=14)
    rp.PS(
        "Tôi xin cam đoan đồ án môn học này là công trình nghiên cứu do tôi thực hiện dưới sự hướng dẫn "
        "của TS. Nguyễn Thôn Dã trong khuôn khổ môn học Nghiên cứu Dữ liệu lớn trong kinh doanh. Toàn bộ "
        "dữ liệu được tải trực tiếp từ kho dữ liệu công khai của Ủy ban Taxi và Limousine thành phố New York "
        "(NYC Taxi & Limousine Commission). Mọi con số, bảng biểu và hình ảnh trong báo cáo đều được tạo ra "
        "tự động từ các tệp kết quả của mã nguồn đính kèm, không có số liệu nào được nhập tay hay ước đoán.",
        "Mã nguồn, dữ liệu trung gian ở các lớp Bronze, Silver, Gold và các tệp kết quả được lưu đầy đủ trong "
        "thư mục đồ án để người chấm có thể chạy lại và đối chiếu. Các tài liệu tham khảo được trích dẫn rõ "
        "nguồn.")
    rp.P("Thành phố Hồ Chí Minh, năm 2026", indent=False, align="right", italic=True)
    rp.P("Học viên thực hiện", indent=False, align="right", bold=True)
    rp.P(STUDENT.split(" – ")[0], indent=False, align="right")


def thanks(rp):
    rp.H1("LỜI CẢM ƠN", numbered=False, size=14)
    rp.PS(
        "Tôi xin gửi lời cảm ơn đến TS. Nguyễn Thôn Dã, giảng viên môn Nghiên cứu Dữ liệu lớn trong kinh doanh. "
        "Các chương về kiến trúc Lakehouse, lưu trữ dạng cột, xử lý hiệu năng cao, dự báo và phân tích rủi ro "
        "trong bài giảng là khung sườn để tôi thiết kế pipeline và lựa chọn phương pháp cho đồ án này.",
        "Tôi cũng cảm ơn Ủy ban Taxi và Limousine thành phố New York đã công bố dữ liệu chuyến đi ở mức chi tiết "
        "từng chuyến, cùng cộng đồng phát triển DuckDB, Apache Spark, Apache Arrow, pandas, statsmodels, scikit-learn và "
        "LightGBM. Nếu không có các công cụ mã nguồn mở này, việc xử lý hơn một tỷ bản ghi trên một máy "
        "tính cá nhân sẽ không khả thi.",
        "Do giới hạn về thời gian và tài nguyên tính toán, đồ án chắc chắn còn thiếu sót. Tôi mong nhận được góp ý "
        "của thầy để hoàn thiện nghiên cứu.")


def abstract_vi(rp, R):
    t93 = R.t("t93")
    t93w, t93m = t93[t93.outcome == "wait"], t93[t93.outcome == "mph"]
    m = R.J["07_did_main"]
    tw = R.did("hvfhv", "ln_n")
    dd = R.did("hvfhv", "ln_n", "DDD mùa vụ")
    sc = R.J["08_scm"]["standard"]
    dm = R.dml("dlog_n")
    mph = R.did("hvfhv", "mph")
    wt = R.did("hvfhv", "wait")
    man = R.t("t03")
    nraw = int(man.total_rows.sum())
    q = R.t("t07")
    nsil = int(q.n_silver.sum())
    rev = R.t("t16")
    eng = R.t("t62").set_index("engine")
    uniq = R.t("t74").set_index("qi").loc["Vùng đón, vùng trả, giây đón (như bản công bố)", "unique_pct"]
    co = R.t("t77_company")
    uber = co[(co.outcome == "ln_uber") & (co.spec == "TWFE")].pct.iloc[0]
    lyft = co[(co.outcome == "ln_lyft") & (co.spec == "TWFE")].pct.iloc[0]
    rp.H1("TÓM TẮT", numbered=False, size=14)
    rp.PS(
        "Ngày 05/01/2025, thành phố New York bắt đầu thu phí đối với phương tiện đi vào khu vực Manhattan từ đường 60 "
        "trở xuống, gọi là Congestion Relief Zone (CRZ). Với xe gọi công nghệ cỡ lớn như Uber và Lyft, mỗi chuyến có "
        "điểm đầu hoặc điểm cuối trong vùng bị cộng 1,50 USD; với taxi vàng là 0,75 USD. Đồ án đánh giá chính sách này "
        "bằng dữ liệu chuyến đi ở mức từng chuyến của NYC TLC trong 24 tháng, từ 01/2024 đến 12/2025.",
        f"Về kỹ thuật dữ liệu lớn, đồ án xây dựng một pipeline theo kiến trúc Lakehouse ba lớp Bronze–Silver–Gold "
        f"bằng DuckDB và Parquet, chạy được trên máy có khoảng 3 GB RAM. Dữ liệu thô gồm {vint(nraw)} bản ghi "
        f"({vn(man.total_size_mb.sum() / 1024, 1)} GB Parquet). Sau bảy quy tắc kiểm soát chất lượng còn {vint(nsil)} "
        f"chuyến hợp lệ, được tổng hợp thành bảy bảng Gold. Vùng chịu phí không được gán tay mà suy ra từ tỷ lệ "
        f"chuyến nội vùng bị thu phí trong quý I/2025, cho kết quả 38 vùng nằm trọn trong CRZ và 6 vùng vắt qua ranh giới.",
        f"Về suy luận nhân quả, đồ án kết hợp sai khác kép với hai chiều hiệu ứng cố định (TWFE), sai khác bậc ba "
        f"khử mùa vụ (DDD), nghiên cứu sự kiện, kiểm soát tổng hợp (SCM) và học máy nhân quả (Double/Debiased ML, "
        f"AIPW, DR-learner với LightGBM). Trên panel {m['hv_zone_week']['zones']} vùng × {m['hv_zone_week']['weeks']} tuần, "
        f"thời gian chờ xe của chuyến đón trong CRZ giảm {vn(-wt.coef, 2)} phút và tốc độ trung bình tăng {vn(mph.coef, 2)} dặm/giờ "
        f"so với nhóm đối chứng. Số chuyến HVFHV đón trong CRZ giảm {vn(-pct_log(tw.coef), 1)}% theo TWFE (sai số chuẩn "
        f"{vn(100 * tw.se, 2)} điểm log), {vn(-pct_log(dd.coef), 1)}% theo DDD, {vn(-sc['avg_pct_effect_post'], 1)}% theo SCM và "
        f"{vn(-pct_log(dm.aipw_ate), 1)}% theo DML trên {vint(dm.n_overlap)} cặp điểm đón – điểm trả thuộc vùng chồng lấn. Các kết "
        f"quả này giữ ý nghĩa thống kê với sai số Conley, phân cụm hai chiều, wild cluster bootstrap và hiệu chỉnh kiểm định bội. Các "
        f"chỉ tiêu giá cước và thu nhập tài xế bị chi phối bởi xu hướng có sẵn từ trước nên không được diễn giải như tác động nhân quả.",
        f"Để kiểm tra giả định xu hướng song song, đồ án bổ sung {vint(R.t('t03x').total_rows.sum())} bản ghi của 2022–2023 và ước "
        f"lượng nghiên cứu sự kiện theo tháng trên bốn năm với sáu cách chọn năm gốc và dạng xu hướng. Kết quả xếp các kết luận theo "
        f"mức độ chắc chắn. Thời gian chờ giảm ở {int((t93w.ci_high_wild < 0).sum())} trên {len(t93w)} đặc tả. Tốc độ tăng ở "
        f"{int((t93m.ci_low_wild > 0).sum())} đặc tả, nhưng độ lớn phụ thuộc giả định. Số chuyến của CRZ đã giảm tương đối "
        f"{vn(-pct_log(R.t('t90').set_index('outcome').loc['ln_n'].placebo_2024_vs_2023), 1)}% trong năm 2024, trước khi có phí; tùy "
        f"giả định xu hướng, tác động của phí lên số chuyến nằm trong khoảng từ 0 đến khoảng 10%, nên mức giảm 6–10% của các thiết "
        f"kế một năm là cận trên và dữ liệu không xác định được con số chính xác hơn.",
        f"Tổng phí CBD ghi nhận trong dữ liệu năm 2025 là {vn(rev[rev.service == 'hvfhv'].cbd.sum() / 1e6, 1)} triệu USD "
        f"từ HVFHV và {vn(rev[rev.service == 'yellow'].cbd.sum() / 1e6, 1)} triệu USD từ taxi vàng. Phân tích lan tỏa cho "
        f"thấy mức giảm lan ra các vùng lân cận ngoài ranh giới và nhỏ dần theo khoảng cách, nên dùng Manhattan phía bắc "
        f"làm nhóm đối chứng duy nhất sẽ đánh giá thấp tác động.",
        f"Ba mô-đun mở rộng bám theo các chương còn lại của học phần. Thứ nhất, Apache Spark tái lập bảng Gold chính từ "
        f"{vint(R.t('t60b').n_silver.sum())} dòng Silver; phép đối chứng từng ô với DuckDB phát hiện một lỗi ép kiểu im lặng ở bước "
        f"hợp nhất, được sửa trước khi dựng báo cáo. Trên cùng phần cứng một nút, Spark chậm hơn DuckDB khoảng "
        f"{vn(eng.loc['spark_df', 'median_s'] / eng.loc['duckdb', 'median_s'], 1)} lần; AQE, cắt tỉa phân vùng, Apache Arrow và "
        f"Structured Streaming được đo trực tiếp. Thứ hai, về quản trị dữ liệu và rủi ro, {vn(uniq, 1)}% chuyến là duy nhất ở mức "
        f"chi tiết của bản công bố, trong khi bảng vùng × ngày có quyền riêng tư vi phân với ε = 0,01 vẫn giữ nguyên kết luận về số "
        f"chuyến. Thứ ba, về giá trị kinh doanh, số chuyến Uber giảm {vn(-uber, 1)}% so với {vn(-lyft, 1)}% của Lyft, và mô hình "
        f"dự báo nhu cầu chính xác nhất cho phản thực tế trái chiều với DiD, một phần vì chuỗi đối chứng bị lan tỏa.",
        "Từ khóa: dữ liệu lớn, Lakehouse, DuckDB, Apache Spark, phí ùn tắc, gọi xe công nghệ, sai khác kép, kiểm soát tổng hợp, "
        "Double Machine Learning, quyền riêng tư vi phân, quản trị dữ liệu, xu hướng trước chính sách.")


ABBR = [
    ("AIPW", "Augmented Inverse Probability Weighting – ước lượng trọng số nghịch đảo xác suất tăng cường"),
    ("AQE", "Adaptive Query Execution – thực thi truy vấn thích nghi của Spark"),
    ("ATE / ATT", "Tác động trung bình / tác động trung bình trên nhóm được xử lý"),
    ("BLP", "Best Linear Predictor – bộ dự báo tuyến tính tốt nhất của CATE"),
    ("CATE", "Conditional Average Treatment Effect – tác động trung bình có điều kiện"),
    ("CBD", "Central Business District – khu thương mại trung tâm (tên cột phí trong dữ liệu TLC)"),
    ("CLAN", "Classification Analysis – so sánh đặc trưng giữa nhóm tác động cao và thấp"),
    ("CRZ", "Congestion Relief Zone – vùng giảm ùn tắc ở Manhattan"),
    ("DAG", "Directed Acyclic Graph – đồ thị có hướng không chu trình (kế hoạch thực thi của Spark)"),
    ("DDD", "Sai khác bậc ba (ở đây: khử mùa vụ theo nhóm × tuần trong năm)"),
    ("DiD", "Difference-in-Differences – sai khác kép"),
    ("DML", "Double/Debiased Machine Learning – học máy khử chệch kép"),
    ("DP", "Differential Privacy – quyền riêng tư vi phân"),
    ("DR", "Doubly Robust – bền vững kép"),
    ("FE", "Fixed Effects – hiệu ứng cố định"),
    ("GATES", "Group Average Treatment Effects – tác động trung bình theo nhóm"),
    ("HVFHV / HVFHS", "High Volume For-Hire Vehicle/Service – dịch vụ xe cho thuê số lượng lớn (Uber, Lyft)"),
    ("KTC", "Khoảng tin cậy"),
    ("JVM", "Java Virtual Machine – máy ảo Java, môi trường chạy của Spark"),
    ("MAD", "Median Absolute Deviation – độ lệch tuyệt đối trung vị"),
    ("MAPE", "Mean Absolute Percentage Error – sai số phần trăm tuyệt đối trung bình"),
    ("MDE", "Minimum Detectable Effect – tác động nhỏ nhất phát hiện được"),
    ("MN", "Manhattan"),
    ("MTA", "Metropolitan Transportation Authority – cơ quan vận tải đô thị New York"),
    ("OD", "Origin–Destination – cặp điểm đón và điểm trả"),
    ("PLR", "Partially Linear Regression – hồi quy tuyến tính từng phần"),
    ("RDD", "Resilient Distributed Dataset – tập dữ liệu phân tán có khả năng phục hồi"),
    ("RMSPE", "Root Mean Squared Prediction Error – căn bậc hai sai số dự báo bình phương trung bình"),
    ("RPO / RTO", "Recovery Point / Time Objective – điểm và thời gian phục hồi mục tiêu"),
    ("SCM", "Synthetic Control Method – phương pháp kiểm soát tổng hợp"),
    ("SE", "Standard Error – sai số chuẩn"),
    ("SHA-256", "Secure Hash Algorithm 256 bit – hàm băm mật mã dùng kiểm tra toàn vẹn tệp"),
    ("TLC", "NYC Taxi & Limousine Commission – Ủy ban Taxi và Limousine New York"),
    ("TWFE", "Two-Way Fixed Effects – hai chiều hiệu ứng cố định"),
    ("YoY", "Year over Year – so với cùng kỳ năm trước"),
    ("ZSTD", "Zstandard – thuật toán nén dùng cho tệp Parquet"),
]


def abbreviations(rp):
    import pandas as pd
    rp.H1("DANH MỤC TỪ VIẾT TẮT", numbered=False, size=14)
    df = pd.DataFrame(ABBR, columns=["Từ viết tắt", "Diễn giải"])
    rp.TAB(df, None, widths=[3.2, 12.8], size=11, align=["left", "left"], source=None)
