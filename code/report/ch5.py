"""Chương 5. Xử lý phân tán với Apache Spark: đối chứng chéo và phân tích hiệu năng."""
import json
import re

import numpy as np
import pandas as pd

from lib import vint, vn


def _clean_path(s):
    s = re.sub(r"file:/\S*?/CongestionPricing_CaseStudy", "file:<ROOT>", s)
    s = re.sub(r"file:/sessions/[^,\]\s]*", "file:<ROOT>/data/silver", s)
    return s


def _times(v):
    return " / ".join(vn(x, 2) for x in json.loads(v)) if isinstance(v, str) else "–"


def build(rp, R):
    rep = R.t("t60b").set_index("service")
    rpp = R.t("t60_spark")
    val = R.t("t61_spark")
    val0 = R.t("t61a")
    eng = R.t("t62").set_index("engine")
    sh = R.t("t63")
    sc = R.t("t64")
    ca = R.t("t65")
    pr = R.t("t66_spark")
    ar = R.t("t66b").set_index("arrow")
    sb = R.t("t67_stream")
    sh_h = R.t("t67b")
    vlog = R.JS["spark/validate"]
    vlog0 = R.JS["spark/validate_truoc_sua"]
    clog = R.JS["spark/cache"]
    slog = R.JS["spark/stream"]
    n_silver = int(rep.n_silver.sum())
    d0, s0, q0 = eng.loc["duckdb"], eng.loc["spark_df"], eng.loc["spark_sql"]

    rp.H1("CHƯƠNG 5. XỬ LÝ PHÂN TÁN VỚI APACHE SPARK: ĐỐI CHỨNG CHÉO VÀ PHÂN TÍCH HIỆU NĂNG")
    rp.PS(
        "Chương 4 đã cho thấy toàn bộ pipeline chạy được trên DuckDB, một bộ máy phân tích nhúng chạy trên một nút. Chương này đưa "
        "vào bộ máy thứ hai, Apache Spark, là nền tảng xử lý phân tán trong bộ nhớ được Chương 3 của bài giảng trình bày như công cụ "
        "trung tâm của phân tích dữ liệu lớn. Spark không thay DuckDB; nó được dùng để trả lời ba câu hỏi mà một đồ án chỉ "
        "dùng một bộ máy không trả lời được.",
        "Câu hỏi thứ nhất là tính đúng. Một bảng Gold do một bộ máy tạo ra có thể sai vì lỗi logic, lỗi ép kiểu hoặc lỗi của chính "
        "bộ máy, và những lỗi này thường không lộ ra khi chỉ nhìn vào kết quả phân tích. Tái lập cùng bảng bằng một bộ máy độc lập "
        "rồi so từng ô là một phép kiểm thử sai phân (differential testing) mạnh hơn nhiều so với đọc lại mã. Câu hỏi thứ hai là chi "
        "phí: mô hình phân tán của Spark tốn thêm bao nhiêu thời gian và bộ nhớ khi chạy trên đúng phần cứng mà DuckDB đã dùng. Câu "
        "hỏi thứ ba là cơ chế: các thành phần mà lý thuyết nêu ra, gồm bộ tối ưu Catalyst, thực thi truy vấn thích nghi, lưu đệm, "
        "cắt tỉa phân vùng, Apache Arrow và xử lý luồng có cấu trúc, tác động đo được đến đâu trên dữ liệu thật của đồ án.",
        "Ba câu hỏi này gộp lại thành câu hỏi nghiên cứu RQ5. Mục 5.1 mô tả thiết kế thực nghiệm. Mục 5.2 trình bày kết quả tái lập "
        "và đối chứng chéo, trong đó có một lỗi thật của pipeline được phát hiện nhờ Spark. Các mục 5.3 đến 5.8 lần lượt phân tích "
        "hiệu năng và từng cơ chế. Mục 5.9 thảo luận hàm ý cho việc chọn công cụ.")

    # ================================================================ 5.1
    rp.H2("5.1. Thiết kế thực nghiệm")
    rp.H3("5.1.1. Môi trường và cấu hình Spark")
    env = pd.DataFrame([
        ("Phiên bản", "Apache Spark 3.5.3 qua PySpark, OpenJDK 11"),
        ("Chế độ triển khai", "local[2]: driver và executor trong cùng một JVM, 2 luồng tác vụ"),
        ("Bộ nhớ driver", "1.200 MB (spark.driver.memory)"),
        ("Phân vùng xáo trộn mặc định", "8 (spark.sql.shuffle.partitions); thực nghiệm 5.4 thay đổi từ 1 đến 1.000"),
        ("Thực thi truy vấn thích nghi", "Bật (spark.sql.adaptive.enabled = true); thực nghiệm 5.4 so sánh khi tắt"),
        ("Múi giờ phiên", "UTC, để trường thời gian không bị dịch khi đọc Parquet"),
        ("Thư mục làm việc", "SPARK_WORK trên đĩa cục bộ của máy ảo (Spark cần quyền xóa tệp tạm)"),
        ("Dữ liệu vào", "Lớp Silver: 120 tệp Parquet ZSTD, phân vùng service=/year=/month="),
    ], columns=["Thành phần", "Cấu hình"])
    rp.TAB(env, "Cấu hình Spark dùng trong các thực nghiệm", widths=[5.0, 11.0], size=10.5, align=["left", "left"],
           source="Nguồn: code/15_spark_pipeline.py.")
    rp.PS(
        "Spark chạy ở chế độ local trên cùng máy ảo 2 lõi, khoảng 3 GB RAM đã dùng cho DuckDB. Lựa chọn này có chủ đích. Nếu chạy "
        "Spark trên một cụm nhiều nút, mọi khác biệt về thời gian sẽ trộn lẫn hiệu quả của bộ máy với lượng phần cứng được thêm vào. "
        "Giữ nguyên phần cứng cho phép tách riêng chi phí của mô hình lập trình phân tán: khởi động JVM, lập kế hoạch qua Catalyst, "
        "chia tác vụ, xáo trộn dữ liệu qua đĩa và tuần tự hóa giữa Python và JVM. Chế độ local vẫn đi qua đúng các thành phần này, "
        "chỉ khác là các executor nằm trong cùng một tiến trình.",
        "Một chi tiết vận hành đáng ghi lại: lần chạy đầu tiên, Spark không khởi động được vì máy ảo không phân giải được tên máy "
        "của chính nó, và sau đó không xóa được tệp tạm vì thư mục dự án được gắn từ Windows với quyền chỉ ghi, không xóa. Hai lỗi "
        "này được xử lý bằng biến môi trường SPARK_LOCAL_HOSTNAME và bằng cách đặt thư mục làm việc của Spark trên đĩa cục bộ. Chúng "
        "minh họa một điểm mà bài giảng nhấn mạnh ở mục 3.7: chi phí của một bộ máy phân tán nằm nhiều ở vận hành chứ không riêng ở "
        "thời gian tính toán.")
    rp.H3("5.1.2. Truy vấn chuẩn")
    rp.P("Mọi phép so sánh bộ máy dùng cùng một truy vấn: dựng bảng Gold zone_day_pu từ lớp Silver, tức tổng hợp theo dịch vụ, ngày "
         "và vùng đón với 17 chỉ tiêu cộng được. Truy vấn này được chọn vì nó là đầu vào của panel vùng × tuần, panel chính của toàn "
         "bộ phân tích nhân quả ở Chương 4. Nếu bảng này sai, gần như mọi ước lượng đều sai theo.")
    rp.CODE(
        "SELECT service, d, pu AS zone,\n"
        "       count(*) AS n, sum(fare) AS fare, sum(driver_pay) AS pay, sum(miles) AS miles,\n"
        "       sum(time_s) AS time_s, sum(tips) AS tips, sum(CAST(cbd_fee AS DOUBLE)) AS cbd,\n"
        "       sum(rider_cost) AS rider_cost, sum(cong_sur) AS cong_sur, sum(tolls) AS tolls,\n"
        "       sum(wait_min) AS wait_sum, count(wait_min) AS wait_n, sum(shared_req) AS shared_req,\n"
        "       sum(CAST(cbd_fee > 0 AS INT)) AS n_cbd, sum(CAST(do_grp = 'CRZ' AS INT)) AS n_to_crz,\n"
        "       sum(CAST(company_code = 'HV0003' AS INT)) AS n_uber,\n"
        "       sum(CAST(company_code = 'HV0005' AS INT)) AS n_lyft\n"
        "FROM silver GROUP BY service, d, pu", size=8.5)
    rp.P("Truy vấn được viết bằng SQL chuẩn để chạy nguyên văn trên cả DuckDB và Spark SQL. Với Spark, đồ án viết thêm một bản "
         "tương đương bằng API DataFrame để kiểm tra xem hai cách diễn đạt có cho cùng một kế hoạch thực thi và cùng hiệu năng không.")
    rp.H3("5.1.3. Các thực nghiệm")
    ex = pd.DataFrame([
        ("E1. Tái lập và đối chứng", "Toàn bộ 48 tháng-dịch vụ", "Chênh lệch từng ô giữa Spark và DuckDB", "5.2"),
        ("E2. So sánh bộ máy", "DuckDB, Spark DataFrame, Spark SQL; 1 tháng", "Thời gian lần 1, trung vị 3 lần, bộ nhớ đỉnh", "5.3"),
        ("E3. Mở rộng theo khối lượng", "1, 2, 3, 4, 6 tháng HVFHV", "Thời gian, thông lượng dòng/giây", "5.3"),
        ("E4. Xáo trộn và AQE", "1–1.000 phân vùng; AQE bật/tắt", "Thời gian truy vấn", "5.4"),
        ("E5. Lưu đệm", "3 truy vấn, trước và sau persist()", "Thời gian, dung lượng bộ đệm", "5.5"),
        ("E6. Cắt tỉa phân vùng", "5 điều kiện lọc trên toàn Silver", "Số tệp, dung lượng, số dòng được quét", "5.6"),
        ("E7. Apache Arrow", "toPandas() có/không Arrow", "Thời gian chuyển đổi", "5.7"),
        ("E8. Luồng có cấu trúc", "14 tệp ngày quanh 05/01/2025", "Độ trễ và thông lượng từng lô vi mô", "5.8"),
    ], columns=["Thực nghiệm", "Biến thay đổi", "Đại lượng đo", "Mục"])
    rp.TAB(ex, "Tám thực nghiệm với Spark", widths=[4.4, 5.0, 5.4, 1.2], size=10, align=["left", "left", "left", "center"],
           source="Nguồn: tác giả thiết kế.")
    rp.H3("5.1.4. Cách đo và giới hạn của phép đo")
    rp.PS(
        "Mỗi phép đo thời gian được lặp ba lần trong cùng một phiên. Lần đầu bao gồm chi phí biên dịch mã (whole-stage code "
        "generation của Spark, JIT của JVM) và đọc tệp từ đĩa lần đầu; các lần sau hưởng lợi từ bộ đệm trang của hệ điều hành. "
        "Báo cáo trình bày cả lần đầu và trung vị ba lần vì hai con số trả lời hai câu hỏi khác nhau: lần đầu gần với một tác vụ "
        "chạy theo lịch, trung vị gần với một phiên phân tích tương tác.",
        "Bộ nhớ được đo khác nhau cho hai bộ máy vì kiến trúc khác nhau. DuckDB chạy trong tiến trình Python, nên bộ nhớ đỉnh là "
        "kích thước tập thường trú lớn nhất (max RSS) của tiến trình đó. Spark chạy trong một JVM riêng, nên bộ nhớ đỉnh là VmHWM "
        "của tiến trình JVM, đọc từ /proc; phía Python chỉ giữ kết quả. Thời gian khởi động phiên Spark được đo riêng và không cộng "
        "vào thời gian truy vấn.",
        "Giới hạn chính là mọi phép đo đều trên một máy ảo dùng chung tài nguyên với hệ điều hành chủ, nên có dao động giữa các lần "
        "chạy. Chẳng hạn, thực nghiệm cắt tỉa phân vùng chạy hai lần trong ngày cho thời gian quét toàn bộ Silver khác nhau đáng kể. "
        "Vì vậy, chương này tập trung vào các khác biệt lớn (nhiều lần) và vào xu hướng, không diễn giải các chênh lệch nhỏ.")

    # ================================================================ 5.2
    rp.H2("5.2. Tái lập bảng Gold và đối chứng chéo")
    rp.H3("5.2.1. Kết quả tái lập")
    t = pd.DataFrame({
        "Dịch vụ": ["HVFHV", "Taxi vàng"],
        "Số tháng": [vint(rep.loc["hvfhv", "months"]), vint(rep.loc["yellow", "months"])],
        "Dòng Silver": [vint(rep.loc["hvfhv", "n_silver"]), vint(rep.loc["yellow", "n_silver"])],
        "Tổng thời gian (s)": [vn(rep.loc["hvfhv", "seconds"], 1), vn(rep.loc["yellow", "seconds"], 1)],
        "Trung vị/tháng (s)": [vn(rep.loc["hvfhv", "sec_median"], 2), vn(rep.loc["yellow", "sec_median"], 2)],
        "Triệu dòng/giây": [vn(rep.loc["hvfhv", "rows_per_sec"] / 1e6, 2), vn(rep.loc["yellow", "rows_per_sec"] / 1e6, 2)],
        "JVM đỉnh (MB)": [vn(rep.loc["hvfhv", "jvm_peak_mb"], 0), vn(rep.loc["yellow", "jvm_peak_mb"], 0)],
    })
    rp.TAB(t, "Tái lập bảng zone_day_pu bằng Spark trên toàn bộ lớp Silver", widths=[2.2, 1.6, 2.8, 2.4, 2.4, 2.2, 2.2],
           size=10, source="Nguồn: t60_spark_repro_partitions.csv, t60b_spark_repro_totals.csv.")
    hv = rpp[rpp.service == "hvfhv"]
    rp.PS(
        f"Spark đọc {vint(n_silver)} dòng Silver của 48 tháng-dịch vụ và ghi ra 48 phân vùng Parquet của bảng zone_day_pu trong tổng "
        f"cộng {vn(rep.seconds.sum(), 1)} giây, không tính {vn(hv.boot_s.iloc[0], 1)} giây khởi động phiên. Thời gian mỗi tháng HVFHV "
        f"có trung vị {vn(hv.seconds.median(), 2)} giây; tháng chậm nhất mất {vn(hv.seconds.max(), 2)} giây, là tháng được xử lý đầu "
        f"tiên trong một phiên, khi JVM chưa biên dịch mã nóng. Thông lượng chung khoảng "
        f"{vn(rep.loc['hvfhv', 'rows_per_sec'] / 1e6, 1)} triệu dòng mỗi giây. JVM cần khoảng {vn(rep.jvm_peak_mb.max(), 0)} MB ở đỉnh, "
        f"vừa trong giới hạn 1.200 MB của driver.",
        f"Con số này không so sánh trực tiếp được với thời gian của bước 03, vì bước 03 dựng cùng lúc bảy bảng Gold và mẫu chuyến đi "
        f"(tổng {vn(rep.duckdb_gold_all7_s.sum(), 0)} giây cho phần Gold). Phép so sánh cùng điều kiện được trình bày ở mục 5.3. Điểm "
        f"cần giữ lại ở đây là việc tái lập toàn bộ một bảng Gold bằng một bộ máy độc lập chỉ tốn vài phút, rẻ hơn rất nhiều so với "
        f"giá trị của thông tin mà nó mang lại, như mục tiếp theo cho thấy.")
    rp.H3("5.2.2. Đối chứng từng ô")
    rp.P(f"Hai bản của zone_day_pu được nối theo khóa (dịch vụ, ngày, vùng). Cả hai có đúng {vint(vlog['rows_spark'])} dòng và không "
         f"có khóa nào chỉ xuất hiện ở một bên. Với mỗi chỉ tiêu, đồ án tính số ô lệch về giá trị rỗng, chênh lệch tuyệt đối lớn nhất "
         f"và chênh lệch tương đối lớn nhất. Bảng dưới đây trình bày kết quả của lần đối chứng đầu tiên, trước khi sửa lỗi.")

    def vtab(v):
        rows = []
        for m in v.metric.unique():
            a = v[(v.metric == m) & (v.service == "hvfhv")].iloc[0]
            b = v[(v.metric == m) & (v.service == "yellow")].iloc[0]

            def f(r):
                if pd.isna(r.max_abs_diff):
                    return "(cột rỗng)"
                if r.max_abs_diff == 0:
                    return "0 (khớp tuyệt đối)"
                return f"{vn(r.max_abs_diff, 2) if r.max_abs_diff >= 0.005 else f'{r.max_abs_diff:.1e}'.replace('.', ',')} / " \
                       f"{f'{r.max_rel_diff:.1e}'.replace('.', ',') if r.max_rel_diff < 1e-3 else vn(100 * r.max_rel_diff, 2) + '%'}"
            rows.append((m, f(a), f(b)))
        return pd.DataFrame(rows, columns=["Chỉ tiêu", "HVFHV: lệch tuyệt đối / tương đối lớn nhất",
                                           "Taxi vàng: lệch tuyệt đối / tương đối lớn nhất"])
    rp.TAB(vtab(val0), "Đối chứng Spark – DuckDB, lần 1 (trước khi sửa lỗi)", widths=[2.6, 6.7, 6.7], size=9.5,
           align=["left", "center", "center"], source="Nguồn: t61a_spark_validation_truoc_sua.csv.")
    y0 = val0[(val0.service == "yellow") & (val0.metric == "cbd")].iloc[0]
    y1 = val[(val.service == "yellow") & (val.metric == "cbd")].iloc[0]
    rp.PS(
        "Kết quả chia thành ba loại. Loại thứ nhất là các chỉ tiêu đếm và các tổng của giá trị nguyên hoặc bội của 0,5 (số chuyến, "
        "thời lượng, phí CBD của HVFHV, số chuyến theo hãng): khớp tuyệt đối. Loại thứ hai là các tổng số thực như giá cước, quãng "
        "đường, tiền tip: lệch tương đối cỡ 1e-14 đến 1e-13. Đây không phải lỗi. Phép cộng số thực dấu phẩy động không có tính kết "
        "hợp, và hai bộ máy cộng theo thứ tự khác nhau vì chia dữ liệu thành các lô và luồng khác nhau. Độ lệch ở mức vài đơn vị của "
        "chữ số có nghĩa thứ mười bốn đúng bằng sai số làm tròn tích lũy dự kiến của số thực 64 bit.",
        f"Loại thứ ba là một chỉ tiêu duy nhất lệch thật: phí CBD của taxi vàng. Tổng phí theo Spark là {vn(y0.total_spark, 2)} USD, "
        f"theo DuckDB là {vn(y0.total_duckdb, 2)} USD, lệch tối đa {vn(y0.max_abs_diff, 2)} USD trên một ô, tức "
        f"{vn(100 * y0.max_rel_diff, 2)}% giá trị ô đó. Bản Spark khớp với tổng tính trực tiếp từ các tệp Silver, nên lỗi nằm ở phía "
        f"DuckDB.")
    rp.H3("5.2.3. Nguyên nhân lỗi và cách sửa")
    rp.PS(
        "Truy vết cho thấy lỗi không nằm ở truy vấn tổng hợp mà ở bước hợp nhất (bước 04). Bước 03 ghi mỗi khúc tháng ra một tệp "
        "Parquet riêng. Ở các tháng năm 2024, trước khi có phí, cột phí được gán hằng số 0,0, và DuckDB suy ra kiểu DECIMAL(2,1) cho "
        "hằng số này; tổng của nó trong tệp Gold có kiểu DECIMAL(38,1). Ở các tháng năm 2025, cột phí lấy từ dữ liệu gốc có kiểu số "
        "thực. Khi bước 04 đọc toàn bộ các tệp bằng read_parquet với mẫu đường dẫn, DuckDB mặc định lấy lược đồ của tệp đầu tiên theo "
        "thứ tự tên (HVFHV tháng 01/2024) và ép mọi tệp sau về lược đồ đó. Tổng phí của taxi vàng, vốn là bội số của 0,75 USD, bị làm "
        "tròn về một chữ số thập phân: 2,25 thành 2,3, 3,75 thành 3,8. HVFHV không bị ảnh hưởng vì phí 1,50 USD cho tổng là bội của "
        "0,5, luôn biểu diễn đúng với một chữ số thập phân.",
        f"Cách sửa là thêm tùy chọn union_by_name=true khi đọc, để DuckDB hợp nhất lược đồ theo tên cột và nâng kiểu lên kiểu rộng "
        f"nhất. Sau khi chạy lại bước 04 và các bước phân tích 06 đến 14, đối chứng lần hai cho chênh lệch tương đối lớn nhất của mọi "
        f"chỉ tiêu dưới 1e-9 và tổng phí CBD của taxi vàng hai bên khớp nhau ({vn(y1.total_spark, 2)} và {vn(y1.total_duckdb, 2)} "
        f"USD). Mọi con số trong báo cáo này đều dùng dữ liệu sau khi sửa.",
        f"Về độ lớn, lỗi nhỏ: tổng phí taxi vàng trong năm 2025 bị ghi cao hơn {vn(100 * (y0.total_duckdb / y0.total_spark - 1), 4)}%, "
        f"và các ước lượng DiD về phí trên mỗi chuyến của taxi vàng chỉ đổi ở chữ số thập phân thứ năm. Dù vậy, loại lỗi này cần lưu ý vì ba lý do. Nó im lặng: không "
        "có cảnh báo, không có lỗi thực thi. Nó phụ thuộc thứ tự tệp: nếu tệp đầu tiên thuộc năm 2025, lỗi sẽ không xảy ra. Và nó "
        "không thể phát hiện bằng cách xem kết quả phân tích, vì mọi con số đều hợp lý. Chỉ một phép tính độc lập mới lộ ra nó. Kết quả "
        "này là lý do thực nghiệm chính để dùng hai bộ máy trong một pipeline dữ liệu lớn: bộ máy thứ hai làm nhiệm vụ kiểm "
        "toán.")
    rp.TAB(vtab(val), "Đối chứng Spark – DuckDB, lần 2 (sau khi sửa lỗi)", widths=[2.6, 6.7, 6.7], size=9.5,
           align=["left", "center", "center"], source="Nguồn: t61_spark_validation.csv.")

    # ================================================================ 5.3
    rp.H2("5.3. So sánh bộ máy và khả năng mở rộng")
    rp.H3("5.3.1. Cùng truy vấn trên một tháng")
    t = pd.DataFrame({
        "Bộ máy": ["DuckDB", "Spark DataFrame", "Spark SQL"],
        "Ba lần chạy (s)": [_times(x.times) for x in (d0, s0, q0)],
        "Lần 1 (s)": [vn(x.first_s, 2) for x in (d0, s0, q0)],
        "Trung vị (s)": [vn(x.median_s, 2) for x in (d0, s0, q0)],
        "Triệu dòng/giây": [vn(x.rows_per_s_median / 1e6, 2) for x in (d0, s0, q0)],
        "Bộ nhớ đỉnh (MB)": [f"{vn(d0.py_peak_mb, 0)} (tiến trình)", f"{vn(s0.jvm_peak_mb, 0)} (JVM) + {vn(s0.py_peak_mb, 0)}",
                             f"{vn(q0.jvm_peak_mb, 0)} (JVM) + {vn(q0.py_peak_mb, 0)}"],
    })
    rp.TAB(t, f"DuckDB và Spark trên cùng truy vấn, {vint(d0.n_rows)} dòng HVFHV tháng 03/2025",
           widths=[2.8, 3.6, 1.6, 1.8, 2.2, 4.0], size=9.5, source="Nguồn: t62_spark_engine.csv.")
    rp.FIG(R.fig("f42"), "Thời gian truy vấn của DuckDB và Spark: một tháng (trái) và theo khối lượng dữ liệu (phải)")
    rp.PS(
        f"Ba bộ máy cho cùng {vint(d0.groups)} nhóm. DuckDB nhanh nhất ở cả lần đầu ({vn(d0.first_s, 2)} giây) lẫn trung vị "
        f"({vn(d0.median_s, 2)} giây). Spark chậm hơn {vn(s0.median_s / d0.median_s, 1)} lần theo trung vị và "
        f"{vn(s0.first_s / d0.first_s, 1)} lần ở lần đầu. Khoảng cách lớn hơn ở lần đầu phản ánh chi phí khởi động riêng của Spark: "
        f"biên dịch mã sinh ra từ kế hoạch truy vấn, nạp lớp Java và khởi tạo bộ quản lý bộ nhớ. Về bộ nhớ, JVM của Spark chiếm "
        f"khoảng {vn(s0.jvm_peak_mb, 0)} MB, gấp {vn(s0.jvm_peak_mb / d0.py_peak_mb, 1)} lần tiến trình DuckDB.",
        f"Spark DataFrame và Spark SQL cho thời gian gần như trùng nhau ({vn(s0.median_s, 2)} và {vn(q0.median_s, 2)} giây). Đây là "
        f"điều lý thuyết dự đoán: cả hai cách viết đều được Catalyst dịch về cùng một cây kế hoạch logic, tối ưu bằng cùng bộ quy tắc "
        f"và sinh cùng một kế hoạch vật lý. Vì hiệu năng như nhau, lựa chọn giữa SQL và DataFrame chỉ còn phụ thuộc vào khả năng "
        f"bảo trì mã.")
    rp.H3("5.3.2. Mở rộng theo khối lượng dữ liệu")
    rows = []
    fits = {}
    for e, lab in (("duckdb", "DuckDB"), ("spark_df", "Spark DataFrame")):
        d = sc[sc.engine == e].sort_values("k_months")
        b, a = np.polyfit(d.n_rows / 1e6, d.median_s, 1)
        fits[e] = (a, b)
        for _, r in d.iterrows():
            rows.append((lab, vint(r.k_months), vn(r.n_rows / 1e6, 1), vn(r.first_s, 2), vn(r.median_s, 2),
                         vn(r.rows_per_s / 1e6, 2),
                         vn(r.jvm_peak_mb, 0) if pd.notna(r.jvm_peak_mb) else vn(r.py_peak_mb, 0)))
    rp.TAB(pd.DataFrame(rows, columns=["Bộ máy", "Số tháng", "Triệu dòng", "Lần 1 (s)", "Trung vị (s)", "Triệu dòng/giây",
                                       "Bộ nhớ đỉnh (MB)"]),
           "Thời gian truy vấn theo số tháng HVFHV năm 2025", widths=[3.0, 1.6, 2.0, 2.0, 2.2, 2.6, 2.6], size=10,
           source="Nguồn: t64_spark_scale.csv. Bộ nhớ của Spark là JVM, của DuckDB là tiến trình.")
    ad, bd = fits["duckdb"]
    as_, bs = fits["spark_df"]
    dd6 = sc[(sc.engine == "duckdb") & (sc.k_months == 6)].iloc[0]
    ss6 = sc[(sc.engine == "spark_df") & (sc.k_months == 6)].iloc[0]
    dd1 = sc[(sc.engine == "duckdb") & (sc.k_months == 1)].iloc[0]
    rp.PS(
        f"Khi khối lượng tăng từ 1 lên 6 tháng (từ {vn(dd1.n_rows / 1e6, 1)} lên {vn(dd6.n_rows / 1e6, 1)} triệu dòng), thời gian của "
        f"cả hai bộ máy tăng gần tuyến tính. Hồi quy tuyến tính thời gian trung vị theo số triệu dòng cho hệ số góc "
        f"{vn(bd, 3)} giây trên một triệu dòng với DuckDB và {vn(bs, 3)} giây với Spark. Nói cách khác, chi phí biên của Spark cao "
        f"hơn khoảng {vn(bs / bd, 1)} lần. Ở mức 6 tháng, DuckDB cần {vn(dd6.median_s, 1)} giây và Spark cần {vn(ss6.median_s, 1)} "
        f"giây.",
        f"Bộ nhớ cho thấy khác biệt về thiết kế. Bộ nhớ của DuckDB tăng dần theo khối lượng (từ {vn(dd1.py_peak_mb, 0)} lên "
        f"{vn(dd6.py_peak_mb, 0)} MB), trong khi bộ nhớ JVM của Spark gần như không đổi quanh {vn(sc[sc.engine == 'spark_df'].jvm_peak_mb.mean(), 0)} "
        f"MB. Spark cấp phát một vùng nhớ cố định theo cấu hình ngay từ đầu và xử lý dữ liệu theo từng phân vùng tệp, nên bộ nhớ "
        f"phụ thuộc vào cấu hình hơn là vào khối lượng. DuckDB cấp phát theo nhu cầu, nhỏ hơn nhiều ở khối lượng nhỏ nhưng vẫn tăng "
        f"theo số nhóm trong bảng băm.",
        "Trên một nút, Spark không có lợi thế nào về tốc độ. Lợi thế của nó chỉ xuất hiện khi thêm nút: vì thời gian tăng tuyến tính "
        "theo dữ liệu và công việc được chia thành các tác vụ độc lập theo tệp, về nguyên tắc có thể giảm thời gian gần tỷ lệ với số "
        "nút, trong khi DuckDB bị giới hạn ở tài nguyên của một máy. Đồ án không có cụm để kiểm chứng điều này, nên chỉ nêu như một "
        "dự đoán dựa trên cấu trúc tác vụ.")

    # ================================================================ 5.4
    rp.H2("5.4. Xáo trộn dữ liệu và thực thi truy vấn thích nghi")
    on = sh[sh.aqe == True].set_index("shuffle")  # noqa: E712
    off = sh[sh.aqe == False].set_index("shuffle")  # noqa: E712
    ks = sorted(on.index)
    t = pd.DataFrame({"Số phân vùng xáo trộn": [vint(k) for k in ks],
                      "Tắt AQE: trung vị (s)": [vn(off.loc[k, "median_s"], 2) for k in ks],
                      "Tắt AQE: lần 1 (s)": [vn(off.loc[k, "first_s"], 2) for k in ks],
                      "Bật AQE: trung vị (s)": [vn(on.loc[k, "median_s"], 2) for k in ks],
                      "Bật AQE: lần 1 (s)": [vn(on.loc[k, "first_s"], 2) for k in ks]})
    rp.TAB(t, "Thời gian truy vấn theo số phân vùng xáo trộn, có và không có AQE", widths=[3.6, 3.1, 3.1, 3.1, 3.1], size=10,
           source="Nguồn: t63_spark_shuffle.csv.")
    rp.FIG(R.fig("f43"), "Ảnh hưởng của số phân vùng xáo trộn đến thời gian truy vấn khi bật và tắt AQE", width_cm=13.5)
    best_off = off.median_s.idxmin()
    rp.PS(
        "Truy vấn tổng hợp trong Spark được thực hiện qua hai giai đoạn. Giai đoạn một tổng hợp cục bộ trong từng tác vụ đọc tệp. "
        "Giai đoạn hai chia kết quả trung gian theo giá trị băm của khóa nhóm thành một số phân vùng xáo trộn, ghi xuống đĩa, rồi các "
        "tác vụ của giai đoạn sau đọc lại và tổng hợp lần cuối. Số phân vùng xáo trộn là một tham số mà người dùng phải chọn. Quá ít "
        "phân vùng làm mỗi tác vụ quá lớn; quá nhiều phân vùng tạo ra hàng nghìn tác vụ nhỏ, mỗi tác vụ tốn chi phí lập lịch và mở "
        "tệp cố định.",
        f"Khi tắt AQE, thời gian thấp nhất đạt ở {vint(best_off)} phân vùng ({vn(off.loc[best_off, 'median_s'], 2)} giây). Từ 64 phân "
        f"vùng trở lên, thời gian tăng rõ: ở 200 phân vùng, giá trị mặc định của Spark, trung vị là {vn(off.loc[200, 'median_s'], 2)} "
        f"giây, và ở 1.000 phân vùng, thời gian lên "
        f"{vn(off.loc[1000, 'median_s'], 2)} giây, gấp {vn(off.loc[1000, 'median_s'] / off.loc[best_off, 'median_s'], 1)} lần mức tốt "
        f"nhất. Kết quả trung gian của truy vấn này rất nhỏ (vài nghìn nhóm), nên gần như toàn bộ chi phí thêm là chi phí quản lý tác "
        f"vụ.",
        f"Khi bật AQE, đường thời gian gần như phẳng: từ 1 đến 1.000 phân vùng, trung vị nằm trong khoảng {vn(on.median_s.min(), 2)} "
        f"đến {vn(on.median_s.max(), 2)} giây. Cơ chế nằm ở toán tử AQEShuffleRead trong kế hoạch vật lý (mục 5.6): sau khi giai đoạn "
        f"một kết thúc, Spark đọc thống kê kích thước thật của từng phân vùng xáo trộn và gộp các phân vùng nhỏ lại trước khi chạy "
        f"giai đoạn hai. Tham số do người dùng đặt trở thành giới hạn trên thay vì số tác vụ thật. Với người phân tích, hàm ý thực "
        f"tiễn là khi dùng Spark 3 trở lên thì nên bật AQE và không cần tinh chỉnh số phân vùng xáo trộn cho từng truy vấn.")

    # ================================================================ 5.5
    rp.H2("5.5. Lưu đệm trong bộ nhớ và phả hệ của phép biến đổi")
    g = ca[ca["query"] != "vật chất hóa bộ đệm"].groupby(["query", "phase"]).seconds.median().unstack()
    mat = float(ca[ca["query"] == "vật chất hóa bộ đệm"].seconds.iloc[0])
    t = pd.DataFrame({"Truy vấn": [q.split("_", 1)[1] for q in g.index],
                      "Đọc lại từ Parquet (s)": [vn(v, 2) for v in g["không lưu đệm"]],
                      "Từ bộ đệm (s)": [vn(v, 2) for v in g["lưu đệm"]],
                      "Chênh lệch (s)": [vn(a - b, 2) for a, b in zip(g["không lưu đệm"], g["lưu đệm"])]})
    rp.TAB(t, "Thời gian ba truy vấn trước và sau khi lưu đệm DataFrame một tháng HVFHV (trung vị 2 lần)",
           widths=[4.0, 4.0, 4.0, 4.0], size=10.5, source="Nguồn: t65_spark_cache.csv.")
    rp.FIG(R.fig("f44"), "Thời gian truy vấn khi đọc lại từ Parquet và khi đọc từ bộ đệm trong bộ nhớ", width_cm=13.5)
    saved = float((g["không lưu đệm"] - g["lưu đệm"]).sum())
    rp.PS(
        f"Nguyên lý tính toán trong bộ nhớ ở mục 3.1 của bài giảng gợi ý rằng giữ dữ liệu trong RAM sẽ làm các truy vấn lặp lại nhanh "
        f"hơn nhiều. Thực nghiệm lưu đệm (persist với mức MEMORY_AND_DISK) mười cột của tháng 03/2025 cho kết quả khác kỳ vọng. Việc "
        f"vật chất hóa bộ đệm mất {vn(mat, 1)} giây và chiếm {vn(clog['cache_mem_mb'], 1)} MB trong bộ nhớ, không tràn xuống đĩa. Sau "
        f"đó, ba truy vấn chỉ nhanh hơn tổng cộng {vn(saved, 2)} giây, và truy vấn nhóm × giờ còn chậm hơn khi đọc từ bộ đệm. JVM đạt "
        f"đỉnh {vn(clog['jvm_peak_mb'], 0)} MB, cao gấp đôi so với khi không lưu đệm.",
        "Lý do là điểm xuất phát đã rất nhanh. Parquet ZSTD là định dạng cột nén tốt, bộ đọc vector hóa của Spark giải nén theo lô, "
        "và sau lần đọc đầu các tệp đã nằm trong bộ đệm trang của hệ điều hành. Bộ đệm của Spark lưu dữ liệu ở dạng cột trong bộ nhớ "
        "với nén nhẹ, nên việc quét nó không rẻ hơn bao nhiêu so với giải nén Parquet từ bộ đệm trang, trong khi áp lực bộ nhớ lên "
        "JVM tăng. Lưu đệm có lợi rõ khi phép tính tạo ra DataFrame tốn kém (nhiều phép nối, hàm do người dùng định nghĩa) hoặc khi "
        "cùng dữ liệu được quét hàng chục lần, như trong các thuật toán học máy lặp. Với các truy vấn quét đơn giản trên Parquet, "
        "như phần lớn công việc của đồ án, nó không đáng chi phí.",
        "Thực nghiệm này cũng cho phép quan sát trực tiếp khái niệm phả hệ (lineage) của Spark. Mỗi DataFrame giữ chuỗi phép biến đổi "
        "từ tệp nguồn. Khi một phân vùng bộ đệm bị mất, Spark không cần bản sao mà tính lại phân vùng đó theo chuỗi này. Đoạn trích "
        "dưới đây là phả hệ RDD của truy vấn vùng × ngày, do chính Spark in ra: tác vụ đọc tệp (FileScanRDD) ở đáy, các phép chiếu và "
        "tổng hợp cục bộ, ranh giới xáo trộn (ShuffledRowRDD, đánh dấu bằng thụt lề) và tổng hợp cuối.")
    lin = _clean_path(R.text("spark/lineage_q1.txt"))
    lin = "\n".join(line[:110] for line in lin.splitlines()[:16])
    rp.CODE(lin, size=7.5)

    # ================================================================ 5.6
    rp.H2("5.6. Cắt tỉa phân vùng, đẩy điều kiện lọc và kế hoạch thực thi")
    t = pd.DataFrame({"Điều kiện lọc": pr.case, "Tệp quét": pr.files.map(vint), "Phân vùng": pr.partitions.map(vint),
                      "Dung lượng tệp (MB)": pr.scanned_mb.map(lambda v: vn(v, 1)),
                      "Dòng đọc ra": pr.rows_scanned.map(vint), "Thời gian (s)": pr.seconds.map(lambda v: vn(v, 2))})
    rp.TAB(t, "Tác động của cắt tỉa phân vùng kiểu Hive và đẩy điều kiện lọc trong Spark", widths=[5.4, 1.6, 1.8, 2.4, 2.8, 2.0],
           size=9.5, align=["left"] + ["center"] * 5, source="Nguồn: t66_spark_pruning.csv; số tệp và số dòng đọc từ số liệu của "
           "toán tử quét trong kế hoạch vật lý đã thực thi.")
    a, b = pr.iloc[0], pr.iloc[3]
    c = pr.iloc[4]
    rp.PS(
        f"Lớp Silver được tổ chức theo thư mục service=/year=/month=. Spark tự nhận các cấp thư mục này thành cột phân vùng khi đọc. "
        f"Khi điều kiện lọc chỉ dùng cột phân vùng, Spark loại các thư mục không phù hợp ngay ở bước lập danh sách tệp, trước khi mở "
        f"bất kỳ tệp nào. Kết quả đo khớp chính xác với cấu trúc thư mục: lọc theo dịch vụ còn {vint(pr.files.iloc[1])} tệp, thêm "
        f"năm còn {vint(pr.files.iloc[2])} tệp, thêm tháng còn {vint(b.files)} tệp của một phân vùng. Thời gian giảm từ "
        f"{vn(a.seconds, 1)} giây xuống {vn(b.seconds, 2)} giây.",
        f"Dòng cuối của bảng cho thấy một cơ chế khác. Điều kiện lọc trên cột ngày d không phải là cột phân vùng, nên Spark vẫn phải "
        f"xét cả {vint(c.files)} tệp. Tuy vậy, số dòng thật sự được đọc ra chỉ là {vint(c.rows_scanned)}, đúng bằng số chuyến trong "
        f"tháng 03/2025 của hai dịch vụ, và thời gian chỉ {vn(c.seconds, 1)} giây. Nguyên nhân là đẩy điều kiện lọc xuống bộ đọc "
        f"Parquet: bộ đọc so điều kiện với thống kê min/max của cột d trong chân mỗi nhóm dòng và bỏ qua các nhóm dòng không thể chứa "
        f"ngày tháng 3. Vì mỗi tệp Silver chỉ chứa chuyến của đúng một tháng, mọi nhóm dòng của các tháng khác đều bị bỏ qua, nên số "
        f"dòng đọc ra trùng khớp với số chuyến của tháng 03/2025. Cột dung lượng trong bảng là kích thước danh nghĩa của các tệp được "
        f"xét, không phải số byte thật sự đọc. Đây là cùng cơ chế đã quan sát với DuckDB ở mục 4.1.3, và cho thấy cách tổ chức dữ liệu "
        f"khi ghi quyết định hiệu quả của truy vấn khi đọc.",
        "Kế hoạch vật lý dạng rút gọn của truy vấn có lọc theo tháng được trình bày dưới đây. Có thể đọc thấy toàn bộ những gì chương "
        "này đã đo: điều kiện phân vùng được đẩy vào bước quét (PartitionFilters), chỉ hai cột cần dùng được đọc (ReadSchema), tổng "
        "hợp được chia thành tổng hợp cục bộ và tổng hợp cuối quanh bước xáo trộn (Exchange), và AQE thay kế hoạch ban đầu bằng kế "
        "hoạch cuối có bước gộp phân vùng (AQEShuffleRead: coalesced). Các toán tử có dấu sao được gộp vào một hàm Java sinh tự "
        "động (whole-stage code generation) thay vì gọi từng toán tử qua giao diện lặp.")
    plan = _clean_path(R.text("spark/plan_pruned.txt"))
    keep = plan.split("\n\n\n")[0] + "\n\n" + "\n".join(
        [ln for ln in plan.splitlines() if ln.startswith(("(1) Scan", "PartitionFilters", "ReadSchema", "Batched",
                                                           "(7) AQEShuffleRead", "Arguments: coalesced"))])
    rp.CODE(keep, size=7.5)

    # ================================================================ 5.7
    rp.H2("5.7. Trao đổi dữ liệu giữa Spark và Python qua Apache Arrow")
    a0, a1 = ar.loc[False], ar.loc[True]
    rp.TAB(pd.DataFrame({"Cấu hình": ["Không dùng Arrow (tuần tự hóa từng dòng)", "Dùng Arrow (truyền theo lô cột)"],
                         "Số dòng × cột": [f"{vint(a0.rows)} × {vint(a0.cols)}"] * 2,
                         "Trung vị (s)": [vn(a0.median_s, 2), vn(a1.median_s, 2)],
                         "Nhanh nhất – chậm nhất (s)": [f"{vn(a0.min_s, 2)} – {vn(a0.max_s, 2)}", f"{vn(a1.min_s, 2)} – {vn(a1.max_s, 2)}"]}),
           "Thời gian chuyển một DataFrame Spark sang pandas", widths=[6.0, 3.4, 2.6, 4.0], size=10,
           align=["left", "center", "center", "center"], source="Nguồn: t66b_spark_arrow.csv.")
    rp.PS(
        f"Khi phân tích bằng PySpark, kết quả thường phải được chuyển từ JVM sang Python để vẽ hình hoặc ước lượng mô hình. Mục 3.4 "
        f"của bài giảng giới thiệu Apache Arrow như định dạng cột chuẩn trong bộ nhớ để làm việc này. Không có Arrow, Spark tuần tự "
        f"hóa từng dòng bằng pickle, gửi qua socket và Python dựng lại từng đối tượng. Có Arrow, dữ liệu được gửi theo lô cột nhị "
        f"phân mà pandas đọc trực tiếp. Với {vint(a0.rows)} dòng tám cột, thời gian giảm từ {vn(a0.median_s, 1)} giây xuống "
        f"{vn(a1.median_s, 1)} giây, nhanh hơn {vn(a0.median_s / a1.median_s, 1)} lần.",
        "Đây là khác biệt lớn nhất trong mọi thực nghiệm của chương, và nguyên nhân nằm ở ranh giới giữa hai môi trường chạy chứ "
        "không ở bộ máy tính toán. Trong thực tế, nhiều pipeline PySpark chậm vì chuyển dữ liệu qua ranh giới "
        "JVM – Python không có Arrow, hoặc vì dùng hàm do người dùng định nghĩa bằng Python chạy từng dòng.")

    # ================================================================ 5.8
    rp.H2("5.8. Xử lý luồng có cấu trúc để giám sát chính sách")
    rp.H3("5.8.1. Thiết kế")
    rp.PS(
        "Mục 2.4.7 đã nêu rằng nếu cơ quan quản lý muốn giám sát chính sách hằng ngày, kiến trúc cần một nhánh xử lý luồng. Thực "
        "nghiệm này dựng nhánh đó bằng Spark Structured Streaming. Hai tuần dữ liệu HVFHV từ 29/12/2024 đến 11/01/2025, bao quanh ngày "
        "bắt đầu thu phí, được tách thành 14 tệp theo ngày và đặt vào một thư mục hạ cánh. Luồng đọc thư mục này với "
        "maxFilesPerTrigger = 1, nên mỗi tệp là một lô vi mô, mô phỏng tình huống mỗi ngày nền tảng gửi lên một tệp.",
        "Phép tính trên luồng là tổng hợp theo cửa sổ một giờ của thời điểm đón (thời gian sự kiện, không phải thời gian xử lý) và "
        "theo hãng: số chuyến, số chuyến chạm CRZ, số chuyến có phí CBD, tổng phí, quãng đường và thời lượng. Mốc nước (watermark) "
        "được đặt hai giờ: một cửa sổ chỉ được phát ra khi thời gian sự kiện lớn nhất đã đi qua điểm kết thúc cửa sổ hơn hai giờ, và "
        "dữ liệu đến muộn hơn mức này bị bỏ. Kết quả được ghi ở chế độ append ra Parquet, trạng thái và vị trí đọc được ghi vào thư "
        "mục checkpoint, nên luồng có thể dừng và chạy tiếp mà không tính trùng.")
    rp.H3("5.8.2. Kết quả")
    t = pd.DataFrame({"Lô": sb.batch.map(vint), "Dòng vào": sb.rows.map(vint),
                      "Thời gian lô (ms)": sb.trigger_ms.map(vint), "Trong đó addBatch (ms)": sb.add_batch_ms.map(vint),
                      "Dòng/giây": sb.rows_per_s.map(lambda v: vint(v)),
                      "Mốc nước sau lô": sb.watermark.str.slice(0, 16).str.replace("T", " ").where(~sb.watermark.str.startswith("1970"), "chưa có"),
                      "Dòng trạng thái": sb.state_rows.map(vint)})
    rp.TAB(t, "Số liệu của từng lô vi mô trong Structured Streaming", widths=[1.0, 2.2, 2.2, 2.4, 2.2, 3.8, 2.2], size=9,
           source="Nguồn: t67_stream_batches.csv (từ StreamingQueryProgress của Spark).")
    rp.FIG(R.fig("f46"), "Thời gian xử lý và số dòng của từng lô vi mô")
    first = sb.iloc[0]
    rest = sb.iloc[3:]
    rp.PS(
        f"Luồng xử lý {vint(sb.rows.sum())} dòng trong {vint(len(sb))} lô, tổng thời gian thực {vn(slog['wall_s'], 1)} giây. Lô đầu "
        f"mất {vn(first.trigger_ms / 1000, 2)} giây vì phải biên dịch kế hoạch và khởi tạo kho trạng thái; từ lô thứ tư trở đi, mỗi "
        f"lô khoảng {vint(rest.rows.mean())} dòng chỉ mất trung bình {vn(rest.trigger_ms.mean() / 1000, 2)} giây, thông lượng tăng "
        f"dần đến {vint(sb.rows_per_s.max())} dòng mỗi giây ở lô cuối nhờ JVM đã tối ưu mã nóng. Kho trạng thái chỉ giữ "
        f"{vint(sb.state_rows.max())} dòng, tức các cửa sổ giờ chưa đóng của ba hãng, và dùng dưới "
        f"{vn(sb.state_mem_mb.max(), 2)} MB. Mốc nước tăng đều mỗi lô đúng một ngày, trễ hai giờ so với thời điểm đón muộn nhất của "
        f"ngày trước đó.")
    lab45 = rp.FIG(R.fig("f45"), "Các cửa sổ 1 giờ do Structured Streaming phát ra quanh ngày bắt đầu thu phí")
    sh_h["hour"] = pd.to_datetime(sh_h["hour"])
    sh_h["pct"] = 100 * sh_h.n_cbd / sh_h.n
    post = sh_h[sh_h.hour >= "2025-01-05"]
    pre = sh_h[sh_h.hour < "2025-01-05"]
    rp.PS(
        f"{lab45} là đầu ra của luồng, không phải của một phép tính theo lô sau đó. Trước 23:00 ngày 04/01/2025, tỷ lệ chuyến có phí "
        f"CBD gần như bằng 0 ở mọi giờ (tối đa {vn(pre.iloc[:-1].pct.max(), 3)}%); riêng cửa sổ 23:00–24:00 ngày 04/01 có {vn(pre.iloc[-1].pct, 1)}%, là "
        f"các chuyến đón trước nửa đêm nhưng đi vào vùng sau thời điểm bắt đầu thu phí. Ngay trong cửa sổ đầu tiên sau nửa đêm ngày "
        f"05/01, tỷ lệ này nhảy lên "
        f"{vn(post.pct.iloc[0], 1)}% và dao động trong khoảng {vn(post.pct.min(), 1)}% đến {vn(post.pct.max(), 1)}% trong những ngày "
        f"sau. Một hệ thống giám sát đọc luồng này sẽ ghi nhận việc chính sách bắt đầu có hiệu lực trong vòng một chu kỳ lô.",
        "Trong triển khai thật, thư mục hạ cánh sẽ được thay bằng một hàng đợi thông điệp như Kafka, và lô vi mô có thể ngắn đến vài "
        "giây. Logic phép tính không đổi. Điểm quan trọng về kiến trúc là các chỉ tiêu tính trên luồng đều là đại lượng cộng được, "
        "cùng dạng với các bảng Gold, nên kết quả luồng có thể ghi thẳng vào lớp Gold và được ước lượng nhân quả định kỳ trên cùng "
        "một định nghĩa. Đây là cách hợp nhất xử lý lô và luồng mà mục 3.3 của bài giảng mô tả với Flink; Structured Streaming đạt "
        "được cùng mục tiêu bằng cách coi luồng là một bảng tăng dần.")

    # ================================================================ 5.9
    rp.H2("5.9. Thảo luận: chọn công cụ theo quy mô")
    rp.PS(
        f"Tổng hợp các thực nghiệm, trên một máy 2 lõi, 3 GB RAM và khoảng nửa tỷ dòng, DuckDB nhanh hơn Spark khoảng "
        f"{vn(bs / bd, 1)} lần về chi phí biên, dùng ít bộ nhớ hơn nhiều ở khối lượng nhỏ, và không có chi phí khởi động JVM. Đây là "
        f"kết quả đúng với lý thuyết: Spark được thiết kế để chia việc trên nhiều nút và chịu lỗi khi một nút hỏng, và cái giá của "
        f"thiết kế đó là chi phí cố định cho mỗi tác vụ, cho mỗi lần xáo trộn và cho việc chạy trên JVM. Trên một nút, cái giá này "
        f"không được bù lại.",
        "Tuy vậy, kết luận \"không cần Spark\" là quá vội. Chương này cho thấy ba vai trò mà Spark đảm nhận tốt ngay cả ở quy mô này. "
        "Vai trò thứ nhất là kiểm toán: bản tái lập độc lập phát hiện một lỗi ép kiểu mà không phép kiểm tra nào khác phát hiện. Vai "
        "trò thứ hai là đường nâng cấp: cùng mã SQL chạy được trên cụm khi dữ liệu mở rộng sang toàn bộ lịch sử TLC hoặc khi cần xử "
        "lý đồng thời cho nhiều người dùng, với hành vi đã được kiểm chứng trên dữ liệu nhỏ. Vai trò thứ ba là xử lý luồng có trạng "
        "thái với bảo đảm chạy tiếp sau sự cố, điều DuckDB không được thiết kế để làm.",
        "Mục 3.5 của bài giảng còn nêu Ray và Dask như các lựa chọn phân tán gần với Python hơn. Đồ án không đo hai công cụ này, nhưng "
        "các kết quả trên cho phép dự đoán vị trí của chúng: vì chi phí trong bài toán này chủ yếu nằm ở quét và tổng hợp dữ liệu "
        "dạng bảng, một bộ máy có tối ưu truy vấn và đọc Parquet vector hóa sẽ có lợi thế; lợi thế của Ray nằm ở các tác vụ tính toán "
        "không đồng dạng như huấn luyện nhiều mô hình song song, chẳng hạn bước cross-fitting của DML ở Chương 4.",
        "Hàm ý cho thực hành trong doanh nghiệp là quy tắc chọn công cụ dựa trên ba ngưỡng đo được, không dựa trên thói quen: dữ liệu "
        "cần xử lý trong một lần có vượt khả năng của một máy (kể cả khi đã tận dụng tràn đĩa) hay không; có yêu cầu chịu lỗi và chạy "
        "liên tục hay không; và có nhiều người dùng đồng thời hay không. Với bài toán của đồ án, chỉ ngưỡng thứ hai được đáp ứng, và "
        "chỉ cho nhánh luồng.")
    rp.H2("5.10. Tiểu kết Chương 5")
    rp.P(f"Chương 5 đã đưa Apache Spark vào pipeline như bộ máy thứ hai. Spark tái lập toàn bộ bảng zone_day_pu từ "
         f"{vint(n_silver)} dòng Silver trong vài phút; phép đối chứng từng ô phát hiện và giúp sửa một lỗi ép kiểu im lặng ở bước "
         f"hợp nhất Gold. Trên cùng phần cứng một nút, Spark chậm hơn DuckDB và tốn bộ nhớ hơn, nhưng các cơ chế của nó hoạt động đúng "
        f"như lý thuyết: Catalyst cho cùng kế hoạch với SQL và DataFrame, AQE loại bỏ gần hết tác động của việc chọn sai số phân vùng "
        f"xáo trộn, cắt tỉa phân vùng giảm số tệp quét từ {vint(a.files)} xuống {vint(b.files)}, Arrow rút ngắn việc chuyển dữ liệu "
        f"sang pandas {vn(a0.median_s / a1.median_s, 1)} lần, và Structured Streaming phát hiện thời điểm chính sách có hiệu lực ngay "
        f"trong lô đầu sau đó. Lưu đệm là ngoại lệ: với Parquet nén trên đĩa cục bộ, nó không đáng chi phí.")
