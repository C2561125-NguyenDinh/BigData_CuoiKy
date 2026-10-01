"""Chương 9. Kết luận và kiến nghị."""
from lib import vn, vint
from results import pct_log


def build(rp, R):
    tw = R.did("hvfhv", "ln_n")
    dd = R.did("hvfhv", "ln_n", "DDD mùa vụ")
    mp = R.did("hvfhv", "mph")
    wt = R.did("hvfhv", "wait")
    sc = R.J["08_scm"]["standard"]
    dm = R.dml("dlog_n")
    tot = R.t("t52")
    fm = R.t("t09")
    en = R.t("t10")
    rev = R.t("t16")
    zs = fm[fm.format == "Parquet ZSTD"].iloc[0]
    csv = fm[fm.format == "CSV"].iloc[0]
    ddb = en[en.engine.str.startswith("DuckDB")].iloc[0]
    pdn = en[en.engine.str.startswith("Pandas")].iloc[0]
    b1 = R.od("CRZ→CRZ", "ln_n")
    fc01 = R.spill("điểm trả", "ln_from_crz", "0–1 km")
    mn = R.rob("Đối chứng chỉ Manhattan")
    ou = R.rob("Đối chứng chỉ các quận ngoài")
    lp = R.t("t90").set_index("outcome")
    ln, lm, lw = lp.loc["ln_n"], lp.loc["mph"], lp.loc["wait"]
    t93 = R.t("t93")
    t93l = t93[t93.outcome == "ln_n"].set_index("spec")
    t93m, t93w = t93[t93.outcome == "mph"], t93[t93.outcome == "wait"]

    rp.H1("CHƯƠNG 9. KẾT LUẬN VÀ KIẾN NGHỊ")
    rp.H2("9.1. Kết luận tổng quát")
    rp.PS(
        f"Đồ án đã đánh giá tác động của phí vùng giảm ùn tắc Manhattan, có hiệu lực từ 05/01/2025, lên thị trường gọi xe công nghệ và "
        f"taxi vàng bằng toàn bộ {vint(R.t('t03').total_rows.sum())} bản ghi chuyến đi của NYC TLC trong 24 tháng 2024–2025, cùng {vint(R.t('t03x').total_rows.sum())} bản ghi của 24 tháng 2022–2023 dùng cho "
        f"giai đoạn trước chính sách mở rộng. Công việc gồm hai phần "
        f"gắn chặt với nhau: xây dựng một pipeline Lakehouse có kiểm soát chất lượng để biến dữ liệu thô thành các bảng phân tích đáng "
        f"tin, và áp dụng nhiều thiết kế suy luận nhân quả, từ sai khác kép đến kiểm soát tổng hợp và học máy nhân quả, để ước lượng tác "
        f"động và kiểm tra độ tin cậy của chúng.",
        "Đồ án cũng tái lập bảng phân tích chính bằng Apache Spark để kiểm toán kết quả và đo chi phí của xử lý phân tán, "
        "đánh giá rủi ro quản trị và quyền riêng tư của chính tài sản dữ liệu, và chuyển kết quả thành thông tin cho quyết định kinh "
        "doanh. Về chính sách, kết quả được xếp theo mức độ chắc chắn. Chắc chắn nhất là thời gian chờ xe giảm: kết quả giữ nguyên "
        "qua mọi cách tính sai số, hiệu chỉnh kiểm định bội và hầu hết các giả định về xu hướng dài hạn. Tốc độ tăng, tập trung vào "
        "các giờ đông nhất, nhưng độ lớn phụ thuộc giả định về xu hướng. Số chuyến gọi xe chạm vùng giảm 6–10% so với năm trước, "
        "nhưng dữ liệu 2022–2025 cho thấy CRZ đã giảm tương đối từ trước; tùy giả định xu hướng, tác động của phí nằm trong khoảng "
        "từ 0 đến khoảng 10%, và dữ liệu không đủ để chọn một con số. Dữ liệu hiện có không cho phép kết luận về tác động lên giá "
        "cước cơ sở và thu nhập tài xế.")
    rp.P("Về lý thuyết, mô hình bốn khối ở mục 2.11 cho tám giả thuyết; ba được dữ liệu ủng hộ rõ (tốc độ tăng, lợi ích tốc độ giảm "
         "dần theo thời gian, lan tỏa theo mức phơi nhiễm về chiều), bốn được ủng hộ một phần (số chuyến giảm, liều – đáp ứng theo tỷ "
         "trọng phí, độ lồi của quan hệ tốc độ – lưu lượng, chuyến đi chung giảm mạnh hơn), và một chưa kiểm định được (thu nhập tài "
         "xế). Với tốc độ, giả thuyết được ủng hộ về chiều nhưng độ lớn phụ thuộc giả định xu hướng. Hai điểm lệch có hệ thống so với mô hình, tác động gần như không đổi theo tỷ trọng phí và lan tỏa mạnh "
         "ở vùng sát ranh giới, gợi ý rằng hành khách phản ứng với việc đi vào vùng thu phí như một sự kiện theo địa điểm, hơn là với "
         "mức tăng giá của từng chuyến.")
    rp.H2("9.2. Trả lời các câu hỏi nghiên cứu")
    rp.H3("9.2.1. RQ1: kiến trúc và chi phí xử lý")
    rp.P(f"Pipeline Bronze–Silver–Gold trên DuckDB và Parquet xử lý toàn bộ dữ liệu trong {vn(tot.sec_total.sum() / 60, 1)} phút trên "
         f"máy 2 lõi, khoảng 3 GB RAM. Parquet ZSTD nhỏ hơn CSV {vn(1 / zs.size_ratio_vs_csv, 1)} lần và cho truy vấn tổng hợp nhanh "
         f"hơn {vn(csv.agg_query_s_median / zs.agg_query_s_median, 1)} lần. DuckDB dùng {vn(ddb.max_rss_mb, 0)} MB bộ nhớ cho truy vấn "
         f"một tháng, so với {vn(pdn.max_rss_mb, 0)} MB của pandas. Cắt tỉa cột và đẩy điều kiện lọc theo thời gian cho lợi ích lớn nhờ "
         f"dữ liệu được lưu theo thứ tự thời gian.")
    rp.H3("9.2.2. RQ2: tác động lên số chuyến")
    rp.P(f"Số chuyến HVFHV đón trong CRZ giảm {vn(-pct_log(tw.coef), 1)}% theo TWFE, {vn(-pct_log(dd.coef), 1)}% theo DDD khử mùa vụ, "
         f"{vn(-sc['avg_pct_effect_post'], 1)}% theo kiểm soát tổng hợp và {vn(-pct_log(dm.aipw_ate), 1)}% theo AIPW trên cặp OD thuộc "
         f"vùng chồng lấn. Kết quả vượt qua suy luận hoán vị và vững qua hầu hết các đặc tả thay thế. Luồng nội vùng CRZ→CRZ giảm mạnh "
         f"nhất ({vn(-pct_log(b1.coef), 1)}%). Tuy vậy, "
         f"với dữ liệu 2022–2025, giả dược 2024 so với 2023 đã cho {vn(pct_log(ln.placebo_2024_vs_2023), 1)}%, và sau khi trừ xu "
         f"hướng tuyến tính, tác động còn {vn(100 * ln.effect_trend_adj, 2, sign=True)}% (sai số chuẩn {vn(100 * ln.effect_trend_adj_se, 2)} "
         f"điểm %). Khi đổi năm gốc hoặc dạng xu hướng (mục 4.14.6), ước lượng đi từ khoảng 0 đến {vn(100 * t93l.loc['S3'].effect, 1, sign=True)}%. "
         f"Kết luận vì vậy là: phí có thể làm số chuyến giảm từ 0 đến khoảng 10%; phạm vi 6–10% là cận trên, đúng khi xu hướng "
         f"giảm tương đối 2023–2024 không kéo dài sang 2025, và dữ liệu TLC không xác định được con số chính xác hơn.")
    rp.H3("9.2.3. RQ3: tác động lên ùn tắc")
    rp.P(f"Tốc độ trung bình của chuyến đón trong CRZ tăng {vn(mp.coef, 2)} dặm/giờ và thời gian chờ giảm {vn(-wt.coef, 2)} phút. Hai kết "
         f"quả có bước nhảy rõ tại mốc chính sách, vượt qua giả dược theo thời gian. Với dữ liệu 2022–2025, sau điều chỉnh xu hướng, tốc độ "
         f"vẫn tăng {vn(lm.effect_trend_adj, 2)} dặm/giờ (sai số chuẩn {vn(lm.effect_trend_adj_se, 3)}) và thời gian chờ giảm "
         f"{vn(-lw.effect_trend_adj, 2)} phút; độ lớn nhỏ hơn nhưng chiều không đổi. Qua sáu đặc tả năm gốc và dạng xu hướng, thời gian "
         f"chờ giảm ở {int((t93w.ci_high_wild < 0).sum())} đặc tả và tốc độ tăng ở {int((t93m.ci_low_wild > 0).sum())} đặc tả. Thời gian "
         f"chờ là bằng chứng vững nhất của đồ án về việc chính sách cải thiện điều kiện di chuyển; tốc độ ủng hộ cùng kết luận nhưng "
         f"với độ lớn kém chắc chắn hơn. Sai số Conley, phân cụm hai chiều, wild bootstrap và hiệu chỉnh Holm, Romano–Wolf đều không "
         f"làm hai kết quả này mất ý nghĩa thống kê.")
    rp.H3("9.2.4. RQ4: không đồng nhất và lan tỏa")
    rp.P(f"Số chuyến giảm mạnh hơn vào đêm và tối, ít hơn vào giờ đi làm buổi sáng; tốc độ tăng mạnh nhất vào chiều tối ngày thường. "
         f"Kiểm định BLP xác nhận có không đồng nhất thật theo đặc trưng chuyến đi, với chuyến ngắn nhạy hơn. Về không gian, mức giảm "
         f"lan tới các vùng cách CRZ vài km; dùng Manhattan phía bắc làm đối chứng cho mức giảm {vn(-mn.pct, 1)}%, so với "
         f"{vn(-ou.pct, 1)}% khi dùng quận ngoài. Số chuyến từ CRZ trả khách ở dải 0–1 km ngoài ranh giới tăng "
         f"{vn(pct_log(fc01.coef), 1)}%.")
    rp.H3("9.2.5. RQ5: xử lý phân tán với Spark")
    rep = R.t("t60b")
    v1 = R.JS["spark/validate"]
    eng = R.t("t62").set_index("engine")
    ar = R.t("t66b").set_index("arrow")
    rp.P(f"Spark tái lập toàn bộ bảng Gold zone_day_pu từ {vint(rep.n_silver.sum())} dòng Silver trong {vn(rep.seconds.sum() / 60, 1)} "
         f"phút, khớp với bản DuckDB trên cả {vint(v1['rows_spark'])} dòng sau khi sửa một lỗi ép kiểu ở bước hợp nhất mà chính phép đối "
         f"chứng này phát hiện. Trên cùng máy một nút, Spark chậm hơn DuckDB khoảng "
         f"{vn(eng.loc['spark_df', 'median_s'] / eng.loc['duckdb', 'median_s'], 1)} lần cho một tháng dữ liệu. AQE làm cho hiệu năng gần "
         f"như không phụ thuộc vào số phân vùng xáo trộn, cắt tỉa phân vùng và đẩy điều kiện lọc hoạt động như lý thuyết, Arrow rút "
         f"ngắn việc chuyển dữ liệu sang pandas {vn(ar.loc[False, 'median_s'] / ar.loc[True, 'median_s'], 1)} lần, còn lưu đệm không "
         f"đem lại lợi ích với truy vấn quét trên Parquet. Structured Streaming phát hiện thời điểm chính sách có hiệu lực ngay trong lô "
         f"vi mô đầu tiên sau đó.")
    rp.H3("9.2.6. RQ6: quản trị dữ liệu, quyền riêng tư và rủi ro")
    kan = R.t("t74").set_index("qi")
    dp = R.t("t75b")
    rec = R.t("t71")
    pch = R.t("t72d").set_index("service")
    e01 = dp[dp.eps == 0.01].iloc[0]
    rp.P(f"Toàn bộ {vint(len(rec))} phân vùng vượt qua ba phép đối soát số dòng giữa các lớp, và 50 tệp nguồn có dấu băm SHA-256 để "
         f"kiểm tra tính toàn vẹn. Chất lượng dữ liệu HVFHV ổn định theo biểu đồ kiểm soát p' ({vint(pch.loc['hvfhv', 'out_laney'])} "
         f"tháng vượt giới hạn), còn taxi vàng có tỷ lệ loại bỏ tăng rõ từ 01/2025, làm giảm độ tin cậy của kết quả taxi vàng. Ở mức chi "
         f"tiết của bản công bố, {vn(kan.loc['Vùng đón, vùng trả, giây đón (như bản công bố)', 'unique_pct'], 1)}% chuyến là duy nhất, "
         f"nên dữ liệu vi mô có rủi ro tái nhận dạng cao; rủi ro giảm mạnh khi thời gian được làm thô. Bảng vùng × ngày có quyền riêng "
         f"tư vi phân với ε = 0,01 vẫn cho tác động lên số chuyến là {vn(e01.pct_effect_mean, 2)}%, gần như trùng với bản gốc.")
    rp.H3("9.2.7. RQ7: giá trị kinh doanh")
    co = R.t("t77_company")
    u = co[(co.outcome == "ln_uber") & (co.spec == "TWFE")].iloc[0]
    ly = co[(co.outcome == "ln_lyft") & (co.spec == "TWFE")].iloc[0]
    fa = R.t("t78")
    rp.P(f"Phí ảnh hưởng không đều giữa các hãng (Uber {vn(u.pct, 1)}%, Lyft {vn(ly.pct, 1)}%). Dự báo nhu cầu đạt sai số khoảng "
         f"{vn(fa.mape_pct.min(), 0)}% trên giai đoạn giữ lại, đủ cho vận hành, nhưng dùng làm phản thực tế thì cho kết quả từ "
         f"{vn(fa.post_effect_pct.min(), 1)}% đến {vn(fa.post_effect_pct.max(), 1, sign=True)}% tùy chuỗi đối chứng; mô hình dự báo tốt "
         f"nhất lại sai chiều vì chuỗi đối chứng bị lan tỏa. Tác động lên số chuyến lớn dần và tác động lên tốc độ nhỏ dần theo thời "
         f"gian, nên đánh giá sau vài tuần không đại diện cho dài hạn. Chi phí tài nguyên của tài sản dữ liệu nhỏ, còn giá trị nằm ở "
         f"các quyết định về một khoản thu phí hàng trăm triệu USD mỗi năm.")
    rp.H2("9.3. Kiến nghị")
    rp.H3("9.3.1. Kiến nghị chính sách")
    rp.BUL([
        "Duy trì chính sách vì có bằng chứng về cải thiện tốc độ và thời gian chờ, đồng thời tạo nguồn thu đáng kể.",
        "Xem xét ưu đãi phí cho chuyến đi chung được ghép thành công để không làm giảm hình thức đi lại tiết kiệm không gian đường.",
        "Nghiên cứu cơ cấu phí phân biệt theo giờ cho xe gọi công nghệ, vì lợi ích về tốc độ tập trung ở chiều tối.",
        "Giám sát các vùng ngay ngoài ranh giới để phát hiện ùn tắc dịch chuyển.",
        "Công bố định kỳ các chỉ số giám sát (số chuyến, tốc độ, thời gian chờ theo vùng) tính từ dữ liệu TLC, vì chi phí tính toán rất thấp.",
    ])
    rp.H3("9.3.2. Kiến nghị về phương pháp và dữ liệu")
    rp.BUL([
        "Bổ sung dữ liệu 2019 để có một năm gốc không chịu ảnh hưởng đại dịch; sáu đặc tả ở mục 4.14.6 cho thấy kết luận về số chuyến "
        "phụ thuộc chủ yếu vào giả định này.",
        "Áp dụng khoảng tin cậy có điều kiện của Rambachan và Roth (2023) bằng gói HonestDiD khi có bản cài đặt đã được kiểm chứng; "
        "đồ án dùng khoảng tin cậy bootstrap bảo thủ hơn cho tập nhận dạng.",
        "Báo cáo sai số có tính đến tương quan không gian (Conley hoặc phân cụm hai chiều) cho mọi panel theo vùng, vì sai số chỉ phân "
        "cụm theo vùng đánh giá thấp độ bất định khoảng 2–3,5 lần với các chỉ tiêu chính trong dữ liệu này.",
        "Kết hợp dữ liệu thu phí của MTA, cảm biến giao thông và lượt quẹt thẻ tàu điện ngầm để đo tác động lên toàn hệ thống.",
        "Xây dựng CATE ở cấp chuyến với đặc trưng thời gian chi tiết để cải thiện chồng lấn trong học máy nhân quả.",
        "Đưa đối chứng bằng một bộ máy thứ hai (như Spark ở Chương 5) và kiểm tra vân tay lược đồ thành bước bắt buộc trước khi công bố "
        "bảng Gold.",
        "Khi công bố dữ liệu vi mô, làm thô thời điểm đón trả (ví dụ theo giờ) hoặc thay bằng bảng tổng hợp có quyền riêng tư vi phân.",
        "Không dùng dự báo \"thực tế so với kỳ vọng\" làm ước lượng tác động nếu chưa kiểm tra chuỗi đối chứng có bị chính sách ảnh "
        "hưởng hay không.",
    ])
    rp.H2("9.4. Hướng nghiên cứu tiếp theo")
    rp.PS(
        "Hướng thứ nhất là theo dõi tác động dài hạn. Các nghiên cứu về Stockholm và London cho thấy tác động lên lưu lượng thường được "
        "duy trì, còn tác động lên tốc độ có thể mờ dần. Dữ liệu TLC năm 2026 đã được công bố và có thể đưa trực tiếp vào pipeline hiện "
        "tại để kiểm tra xu hướng này.",
        "Hướng thứ hai là mô hình hóa phía cung: phân tích thu nhập theo giờ của tài xế và mức độ sử dụng xe, cần dữ liệu ở cấp tài xế mà "
        "TLC không công bố công khai. Hướng thứ ba là đánh giá tác động phân phối: hành khách ở các khu vực thu nhập khác nhau chịu ảnh "
        "hưởng thế nào, bằng cách ghép dữ liệu điều tra dân số theo vùng.",
        "Về kỹ thuật, bước 15 có thể được chạy lại trên một cụm Spark nhiều nút để đo khả năng mở rộng theo số nút, điều mà đồ án "
        "chỉ dự đoán được từ cấu trúc tác vụ. Về quyền riêng tư, nếu có định danh người dùng, có thể thử quyền riêng tư vi phân ở mức "
        "người dùng thay vì mức chuyến. Pipeline cũng có thể chuyển sang chế độ tăng dần theo tháng với định dạng bảng giao dịch như Delta Lake hoặc Apache "
        "Iceberg, để hỗ trợ cập nhật và truy vấn theo phiên bản (time travel) như mục 2.4 của bài giảng đã trình bày.")
    rp.H2("9.5. Kết luận cuối")
    rp.P(f"Với {vn(rev.cbd.sum() / 1e6, 1)} triệu USD phí ghi nhận trong một năm từ riêng hai dịch vụ, tốc độ tăng và thời gian chờ "
         f"giảm, phí CRZ là một can thiệp có tác động đo được lên thị trường gọi xe New York. Đồ án cho thấy dữ liệu chuyến đi "
         f"công khai, xử lý bằng một pipeline Lakehouse gọn nhẹ, được kiểm toán bằng một bộ máy phân tán độc lập, quản trị bằng danh "
         f"mục, phả hệ và đo lường rủi ro quyền riêng tư, và phân tích bằng các phương pháp nhân quả được kiểm tra chéo, đủ để đưa ra "
         f"những kết luận có căn cứ, đồng thời chỉ rõ những câu hỏi mà dữ liệu chưa trả lời được.")
