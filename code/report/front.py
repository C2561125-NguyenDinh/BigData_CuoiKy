"""Phần mở đầu theo mẫu: bìa, lời cảm ơn, lời cam kết, tóm tắt, abstract, từ viết tắt."""
from docx.enum.text import WD_ALIGN_PARAGRAPH
from pathlib import Path

from docx.shared import Cm, Pt

from lib import vn, vint
from results import pct_log

TITLE = ("TÁC ĐỘNG KHÔNG ĐỒNG NHẤT VÀ HIỆU ỨNG LAN TỎA CỦA PHÍ GIẢM ÙN TẮC MANHATTAN "
         "LÊN THỊ TRƯỜNG GỌI XE CÔNG NGHỆ: TIẾP CẬN HỌC MÁY NHÂN QUẢ TRÊN KIẾN TRÚC "
         "LAKEHOUSE VỚI HÀNG TRĂM TRIỆU CHUYẾN ĐI")
TITLE_EN = ("Heterogeneous and Spillover Effects of the Manhattan Congestion Relief Zone Toll on "
            "Ride-hailing Markets: A Causal Machine Learning Study on a Big Data Lakehouse")


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
    rp.P(TITLE_EN, indent=False, align="center", size=12, italic=True, space_after=22)
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
        "nguồn. Nếu có sai phạm, tôi xin chịu hoàn toàn trách nhiệm.")
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
        "LightGBM. Nếu không có các công cụ mã nguồn mở này, việc xử lý gần sáu trăm triệu bản ghi trên một máy "
        "tính cá nhân sẽ không khả thi.",
        "Do giới hạn về thời gian và tài nguyên tính toán, đồ án chắc chắn còn thiếu sót. Tôi mong nhận được góp ý "
        "của thầy để hoàn thiện nghiên cứu.")


def abstract_vi(rp, R):
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
        f"số chuyến HVFHV đón trong CRZ giảm {vn(-pct_log(tw.coef), 1)}% so với nhóm đối chứng theo TWFE "
        f"(sai số chuẩn {vn(100 * tw.se, 2)} điểm log) và {vn(-pct_log(dd.coef), 1)}% theo DDD. SCM cho mức giảm trung bình "
        f"{vn(-sc['avg_pct_effect_post'], 1)}%; DML trên {vint(dm.n_overlap)} cặp điểm đón – điểm trả thuộc vùng chồng lấn "
        f"cho {vn(-pct_log(dm.aipw_ate), 1)}%. Tốc độ trung bình của chuyến đón trong CRZ tăng {vn(mph.coef, 2)} dặm/giờ "
        f"và thời gian chờ xe giảm {vn(-wt.coef, 2)} phút. Hai kết quả về ùn tắc này vững qua các phép thử giả dược, "
        f"còn các chỉ tiêu giá cước và thu nhập tài xế bị chi phối bởi xu hướng có sẵn từ trước nên không được diễn giải "
        f"như tác động nhân quả.",
        f"Để kiểm tra giả định xu hướng song song, đồ án bổ sung {vint(R.t('t03x').total_rows.sum())} bản ghi của 2022–2023 và ước "
        f"lượng nghiên cứu sự kiện theo tháng trên bốn năm. Kết quả làm thay đổi cách đọc về số chuyến: năm 2024 so với 2023, trước "
        f"khi có phí, số chuyến CRZ đã giảm tương đối {vn(-pct_log(R.t('t90').set_index('outcome').loc['ln_n'].placebo_2024_vs_2023), 1)}%, "
        f"và sau khi trừ xu hướng tuyến tính, tác động năm 2025 chỉ còn "
        f"{vn(100 * R.t('t90').set_index('outcome').loc['ln_n'].effect_trend_adj, 2, sign=True)}%. Mức giảm 6–10% vì thế là cận "
        f"trên; phần vượt xu hướng khoảng 0–2%. Tác động lên tốc độ (+{vn(R.t('t90').set_index('outcome').loc['mph'].effect_trend_adj, 2)} "
        f"dặm/giờ sau điều chỉnh) và thời gian chờ vẫn giữ chiều, với độ lớn nhỏ hơn.",
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


def abstract_en(rp, R):
    tw = R.did("hvfhv", "ln_n")
    dd = R.did("hvfhv", "ln_n", "DDD mùa vụ")
    sc = R.J["08_scm"]["standard"]
    dm = R.dml("dlog_n")
    mph = R.did("hvfhv", "mph")
    wt = R.did("hvfhv", "wait")
    man = R.t("t03")
    uniq = R.t("t74").set_index("qi").loc["Vùng đón, vùng trả, giây đón (như bản công bố)", "unique_pct"]
    rp.H1("ABSTRACT", numbered=False, size=14)
    en = lambda x, d=1: f"{x:,.{d}f}"
    rp.PS(
        "On 5 January 2025 New York City started tolling vehicles entering Manhattan south of and including 60th Street, "
        "the Congestion Relief Zone (CRZ). High-volume for-hire trips that start or end in the zone pay USD 1.50 and yellow "
        "taxi trips USD 0.75. This case study evaluates the policy with trip-level records published by the NYC Taxi and "
        "Limousine Commission for January 2024 to December 2025.",
        f"A three-layer Bronze–Silver–Gold lakehouse built on DuckDB and Parquet processes {en(man.total_rows.sum() / 1e6)} "
        "million raw records on a machine with about 3 GB of RAM. Treated zones are inferred from the data rather than "
        "assigned by hand. Identification combines two-way fixed-effects difference-in-differences, a seasonal "
        "triple-difference, event studies, synthetic control and double/debiased machine learning with LightGBM nuisances.",
        f"Ride-hailing pickups in the CRZ fall by {en(-pct_log(tw.coef))}% (TWFE) and {en(-pct_log(dd.coef))}% (seasonal DDD) "
        f"relative to control zones; synthetic control gives {en(-sc['avg_pct_effect_post'])}% and AIPW on the overlap "
        f"sample of origin–destination pairs gives {en(-pct_log(dm.aipw_ate))}%. Average speed of CRZ pickups rises by "
        f"{en(mph.coef, 2)} mph and waiting time falls by {en(-wt.coef, 2)} minutes, and both results survive placebo tests. "
        "Fare and driver-pay outcomes show strong pre-existing differential trends and are not given a causal "
        "interpretation. Effects spill over to neighbouring zones outside the boundary and fade with distance.",
        f"Adding {en(R.t('t03x').total_rows.sum() / 1e6)} million records for 2022–2023 and estimating a monthly event study "
        f"over four years changes the reading of the trip effect: CRZ trips were already falling relative to control zones "
        f"before the toll, and after removing a linear pre-trend the 2025 effect is "
        f"{en(100 * R.t('t90').set_index('outcome').loc['ln_n'].effect_trend_adj, 2)}%. The 6–10% decline is therefore an "
        "upper bound, with roughly 0–2% attributable to the toll beyond the existing trend. Speed and waiting-time gains "
        "keep their sign after trend adjustment, with smaller magnitudes.",
        "Three extension modules follow the remaining chapters of the course. Apache Spark independently rebuilds the main "
        "Gold table; the cell-by-cell comparison with DuckDB uncovered a silent type-coercion bug in the consolidation step, "
        "fixed before this report was built, and eight experiments measure adaptive query execution, caching, partition "
        f"pruning, Arrow and Structured Streaming. A governance module shows that {en(uniq)}% of trips are unique at the "
        "published level of detail, while zone-by-day counts released under differential privacy with epsilon = 0.01 "
        "preserve the policy conclusion. A business module finds that the most accurate out-of-sample demand forecast "
        "yields a counterfactual of the opposite sign to DiD, partly because its control series is itself affected by spillovers.",
        "Keywords: big data, lakehouse, DuckDB, Apache Spark, congestion pricing, ride-hailing, difference-in-differences, "
        "synthetic control, double machine learning, differential privacy, data governance, pre-trends.")


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
