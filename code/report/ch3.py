"""Chương 3. Dữ liệu, kiến trúc pipeline và phương pháp nghiên cứu."""
import pandas as pd

from lib import vn, vint


def build(rp, R):
    man = R.t("t01")
    bs = R.t("t03")
    drift = R.t("t02")
    q = R.t("t07")
    qm = R.t("t06")
    rj = R.t("t13")
    run = R.t("t08")
    tot = R.t("t52")
    sto = R.t("t53")
    dim = R.t("t04")
    grp = R.t("t05")
    gold_rows = R.J["04_gold_consolidate"]["rows"]
    meta = R.J["07_did_main"]
    dml = R.J["09_dml"]
    nraw = int(bs.total_rows.sum())

    rp.H1("CHƯƠNG 3. DỮ LIỆU, KIẾN TRÚC PIPELINE VÀ PHƯƠNG PHÁP NGHIÊN CỨU")
    rp.P("Chương này mô tả cụ thể những gì đồ án đã làm: nguồn dữ liệu, cách tổ chức pipeline, các quy tắc chất lượng, "
         "cách xác định vùng xử lý, các bảng Gold, các thực nghiệm hiệu năng và chiến lược nhận dạng nhân quả. Mọi con số "
         "trong chương là kết quả chạy thực tế của mã nguồn.")

    # ---------------------------------------------------------------- 3.1
    rp.H2("3.1. Thiết kế nghiên cứu tổng thể")
    rp.H3("3.1.1. Đơn vị phân tích")
    rp.PS(
        "Dữ liệu gốc ở mức từng chuyến đi. Tuy nhiên, chính sách tác động theo không gian (vùng) và theo thời gian (ngày bắt đầu), "
        "nên đơn vị phân tích nhân quả chính là vùng đón khách × tuần. Tuần được định nghĩa từ Chủ nhật đến thứ Bảy, để tuần đầu "
        "tiên sau chính sách bắt đầu đúng vào Chủ nhật 05/01/2025 và không có tuần nào trộn lẫn ngày trước và sau chính sách. Ngoài "
        "ra, đồ án dùng ba đơn vị bổ trợ: vùng × ngày (để tách ngày thường và cuối tuần), vùng × khung giờ × tháng (để tách theo "
        "giờ) và cặp điểm đón – điểm trả × tháng (để phân loại luồng và áp dụng học máy nhân quả).",
        "Việc tổng hợp từ chuyến lên vùng × tuần không làm mất thông tin cần cho các câu hỏi nghiên cứu, vì chính sách không thay "
        "đổi trong một vùng và trong một tuần. Nó còn giúp giảm kích thước dữ liệu mô hình từ hàng trăm triệu dòng xuống vài chục "
        "nghìn dòng, để có thể chạy hàng trăm hồi quy trong suy luận hoán vị.")
    rp.H3("3.1.2. Quy trình tổng thể")
    rp.P("Hình 3.1 mô tả toàn bộ quy trình từ nguồn dữ liệu đến các lớp phân tích. Các bước được đánh số tương ứng với tệp mã "
         "nguồn trong thư mục code/.")
    rp.FIG(R.fig("f00"), "Kiến trúc pipeline Lakehouse và các lớp phân tích của đồ án")
    df = pd.DataFrame([
        ("00", "00_download_data.py / .ps1", "Tải 50 tệp dữ liệu thô từ NYC TLC", "data/raw"),
        ("01", "01_bronze_catalog.py", "Danh mục metadata, lệch lược đồ", "t01–t03"),
        ("02", "02_zone_dimension.py", "Bảng chiều vùng, xác định CRZ, quan hệ kề", "dim_zone, t04–t05"),
        ("03", "03_silver_gold_month.py", "Silver + Gold theo từng khúc tháng", "silver/, gold/_parts"),
        ("04", "04_gold_consolidate.py", "Hợp nhất Gold, nhật ký chất lượng", "gold/*.parquet, t06–t08"),
        ("05", "05_benchmark.py", "Thực nghiệm định dạng, bộ máy, cắt tỉa", "t09–t12"),
        ("06", "06_eda.py", "Phân tích khám phá", "t13–t29, f01–f18"),
        ("07", "07_did_main.py", "DiD, DDD, nghiên cứu sự kiện, OD, giờ", "t30–t37, f19–f24"),
        ("08", "08_synthetic_control.py", "Kiểm soát tổng hợp, giả dược", "t38–t40, f25–f27"),
        ("09", "09_dml_heterogeneity.py", "DML, AIPW, CATE, BLP, GATES", "t41–t47, f28–f31"),
        ("10", "10_spillover_robustness.py", "Lan tỏa, giả dược, hoán vị, độ vững", "t48–t51, f32–f34"),
        ("11", "11_appendix_tables.py", "Bảng phụ lục", "a01–a03"),
        ("12", "12_pipeline_figures.py", "Hình hiệu năng, sơ đồ kiến trúc", "t52–t53, f00, f35–f37"),
        ("13", "13_build_report.py", "Dựng báo cáo Word/PDF", "report/"),
    ], columns=["Bước", "Tệp mã nguồn", "Nội dung", "Đầu ra chính"])
    rp.TAB(df, "Các bước của pipeline và tệp mã nguồn tương ứng", widths=[1.2, 5.2, 5.4, 4.2], size=10,
           align=["center", "left", "left", "left"], source="Nguồn: mã nguồn của đồ án.")

    # ---------------------------------------------------------------- 3.2
    rp.H2("3.2. Nguồn dữ liệu")
    rp.H3("3.2.1. Dữ liệu chuyến đi của NYC TLC")
    rp.PS(
        "TLC công bố hồ sơ chuyến đi hằng tháng tại trang Trip Record Data. Đồ án dùng hai bộ: High Volume For-Hire Vehicle "
        "(HVFHV, gồm Uber, Lyft và các hãng nhỏ khác có trên 10.000 chuyến mỗi ngày) và Yellow Taxi. Mỗi tệp là một tháng, định "
        "dạng Parquet. Bảng 3.2 liệt kê các cột được sử dụng của bộ HVFHV và cách đồ án dùng chúng.",
        f"Tổng cộng có {len(man)} tệp chuyến đi, với {vint(bs[bs.service == 'hvfhv'].total_rows.iloc[0])} bản ghi HVFHV "
        f"({vn(bs[bs.service == 'hvfhv'].total_size_mb.iloc[0] / 1024, 2)} GB) và {vint(bs[bs.service == 'yellow'].total_rows.iloc[0])} "
        f"bản ghi taxi vàng ({vn(bs[bs.service == 'yellow'].total_size_mb.iloc[0] / 1024, 2)} GB). Hai tệp phụ là bảng tra 265 mã "
        f"vùng (taxi_zone_lookup.csv) và shapefile ranh giới vùng (taxi_zones.zip).")
    dd = pd.DataFrame([
        ("hvfhs_license_num", "Mã giấy phép hãng (HV0003 = Uber, HV0005 = Lyft)", "Thị phần hãng"),
        ("request_datetime", "Thời điểm hành khách gọi xe", "Thời gian chờ"),
        ("pickup_datetime / dropoff_datetime", "Thời điểm đón / trả khách", "Ngày, giờ, tuần, phân vùng"),
        ("PULocationID / DOLocationID", "Mã vùng đón / trả (1–263; 264, 265 là không xác định)", "Nhóm xử lý, luồng OD"),
        ("trip_miles, trip_time", "Quãng đường (dặm), thời lượng (giây)", "Tốc độ, quãng đường/chuyến"),
        ("base_passenger_fare", "Giá cước cơ sở trước phí và thuế", "Giá/dặm, giá/chuyến"),
        ("tolls, bcf, sales_tax", "Phí cầu đường, phí quỹ xe đen, thuế bán hàng", "Chi phí hành khách"),
        ("congestion_surcharge", "Phụ thu ùn tắc cấp bang (từ 2019)", "Chi phí hành khách"),
        ("airport_fee", "Phí sân bay", "Chi phí hành khách"),
        ("cbd_congestion_fee", "Phí CRZ (chỉ có từ 01/2025)", "Xác định vùng, doanh thu phí"),
        ("tips", "Tiền tip", "Tip/chuyến"),
        ("driver_pay", "Thu nhập tài xế cho chuyến, chưa gồm tip", "Thu nhập/dặm, tỷ lệ trả tài xế"),
        ("shared_request_flag", "Hành khách có yêu cầu đi chung", "Tỷ lệ yêu cầu đi chung"),
    ], columns=["Cột", "Ý nghĩa", "Sử dụng trong đồ án"])
    rp.TAB(dd, "Các cột của dữ liệu HVFHV được sử dụng", widths=[4.6, 6.6, 4.8], size=10,
           align=["left", "left", "left"], source="Nguồn: từ điển dữ liệu HVFHV của NYC TLC và lược đồ tệp thực tế.")
    rp.H3("3.2.2. Quy mô dữ liệu theo tháng")
    hvm = man[man.service == "hvfhv"].n_rows
    yem = man[man.service == "yellow"].n_rows
    rp.P(f"Hình 3.2 cho thấy số bản ghi thô của từng tháng. HVFHV dao động từ {vn(hvm.min() / 1e6, 1)} đến {vn(hvm.max() / 1e6, 1)} "
         f"triệu chuyến mỗi tháng và khá ổn định giữa hai năm, trong khi taxi vàng chỉ có từ {vn(yem.min() / 1e6, 1)} đến "
         f"{vn(yem.max() / 1e6, 1)} triệu chuyến, tức nhỏ hơn khoảng {vn(hvm.mean() / yem.mean(), 1)} lần.")
    rp.FIG(R.fig("f01"), "Số bản ghi thô theo tháng của HVFHV và taxi vàng, 01/2024 – 12/2025")
    mm = man.groupby("service").agg(min_rows=("n_rows", "min"), max_rows=("n_rows", "max"), mean_rows=("n_rows", "mean"),
                                    rg=("n_row_groups", "mean"), cols=("n_columns", "max"), comp=("compression", "first")).reset_index()
    mm["service"] = mm.service.map({"hvfhv": "HVFHV", "yellow": "Taxi vàng"})
    mt = pd.DataFrame({"Dịch vụ": mm.service, "Số dòng/tháng thấp nhất": mm.min_rows.map(vint),
                       "Cao nhất": mm.max_rows.map(vint), "Trung bình": mm.mean_rows.map(vint),
                       "Row group/tệp (TB)": mm.rg.map(lambda v: vn(v, 1)), "Số cột tối đa": mm.cols.map(vint),
                       "Nén": mm.comp})
    rp.TAB(mt, "Đặc điểm các tệp Bronze theo dịch vụ", widths=[2.4, 2.8, 2.4, 2.4, 2.2, 1.8, 2.0], size=10)
    rp.H3("3.2.3. Lệch lược đồ")
    added = drift.groupby("service").added.first().to_dict()
    nmonths = drift.groupby("service").month.count().to_dict()
    rp.PS(
        f"Bước Bronze so sánh lược đồ của mỗi tháng với tháng 01/2024. Kết quả phát hiện đúng một thay đổi: cột "
        f"{added.get('hvfhv', '')} được thêm vào ở cả {nmonths.get('hvfhv', 0)} tháng HVFHV và {nmonths.get('yellow', 0)} tháng "
        f"taxi vàng của năm 2025. Không có cột nào bị bỏ hay đổi kiểu. Lớp Silver xử lý bằng cách đọc cột này khi có và gán 0 "
        f"cho các tháng năm 2024, đúng với thực tế là chưa có phí.",
        "Việc phát hiện lệch lược đồ tự động có ý nghĩa thực tế: nếu TLC tiếp tục bổ sung cột trong tương lai, bước Bronze sẽ ghi "
        "nhận ngay mà không làm hỏng các bước sau.")

    # ---------------------------------------------------------------- 3.3
    import longpre
    if "t03x_bronze_summary_ext" in R.T:
        longpre.data_section(rp, R)

    rp.H2("3.3. Kiến trúc Lakehouse được triển khai")
    rp.H3("3.3.1. Lớp Bronze")
    rp.PS(
        "Lớp Bronze giữ nguyên 50 tệp tải về trong thư mục data/raw, không đổi tên, không sửa nội dung. Bước 01 chỉ đọc siêu dữ "
        "liệu ở chân tệp Parquet (số dòng, số row group, lược đồ, phương thức nén) và một truy vấn min/max trên cột thời gian đón "
        "khách. Nhờ vậy, việc lập danh mục 48 tệp chuyến đi với hơn nửa tỷ dòng chỉ mất "
        f"{vn(R.J['01_bronze_catalog']['seconds'], 1)} giây.")
    rp.H3("3.3.2. Lớp Silver")
    rp.PS(
        "Lớp Silver có ba nhiệm vụ. Thứ nhất, chuẩn hóa hai nguồn về một lược đồ chung gồm các trường: dịch vụ, mã hãng, thời điểm "
        "gọi, đón, trả, vùng đón, vùng trả, quãng đường, thời lượng, giá cước và các khoản phí, tiền tip, thu nhập tài xế, cờ đi "
        "chung. Với taxi vàng, thời lượng được tính từ hai mốc thời gian, thu nhập tài xế để trống. Thứ hai, gắn bảy cờ chất lượng "
        "cho từng bản ghi. Thứ ba, sinh các trường dẫn xuất: ngày, giờ, thứ, thời gian chờ (phút), tốc độ (dặm/giờ), nhóm vùng "
        "đón và trả, cờ chạm CRZ, tổng chi phí hành khách.",
        "Dữ liệu Silver được ghi dưới dạng Parquet nén ZSTD với row group một triệu dòng, phân vùng theo đường dẫn "
        "service=/year=/month=/part-k.parquet. Cách đặt tên theo kiểu Hive cho phép DuckDB, Spark hay Polars đọc trực tiếp và cắt "
        "tỉa phân vùng khi truy vấn theo dịch vụ hoặc tháng.")
    rp.H3("3.3.3. Xử lý theo khúc và giới hạn tài nguyên")
    hv = run[run.service == "hvfhv"]
    ye = run[run.service == "yellow"]
    rp.PS(
        "Máy chạy pipeline là một máy ảo Linux trên máy tính cá nhân của tác giả, có 2 lõi CPU và khoảng 3 GB RAM, mỗi lệnh bị giới "
        "hạn 180 giây. Thử nghiệm ban đầu cho thấy xử lý trọn một tháng HVFHV vượt giới hạn thời gian. Mỗi tháng HVFHV vì vậy được "
        "chia thành bốn khúc theo ngày đón (ngày 1–8, 9–16, 17–24 và phần còn lại); khúc cuối nhận thêm các bản ghi có thời điểm "
        "ngoài tháng hoặc rỗng để chúng vẫn được gắn cờ. Taxi vàng xử lý nguyên tháng. Tổng cộng có "
        f"{len(run)} phân vùng ({len(hv)} khúc HVFHV và {len(ye)} tháng taxi vàng).",
        f"DuckDB được đặt giới hạn bộ nhớ 1,8 GB, 2 luồng, tắt bảo toàn thứ tự chèn và cho phép tràn ra thư mục tạm. Với cấu hình "
        f"này, mỗi khúc HVFHV mất trung bình {vn(hv.sec_total.mean(), 1)} giây (từ {vn(hv.sec_total.min(), 1)} đến "
        f"{vn(hv.sec_total.max(), 1)} giây), mỗi tháng taxi vàng mất trung bình {vn(ye.sec_total.mean(), 1)} giây. Hình 3.3 cho thấy "
        f"thời gian tăng gần tuyến tính theo số dòng đầu vào.")
    rp.FIG(R.fig("f37"), "Thời gian xử lý mỗi phân vùng (Bronze → Silver → Gold) theo số dòng đầu vào")
    tt = tot.copy()
    tt["service"] = tt.service.map({"hvfhv": "HVFHV", "yellow": "Taxi vàng"})
    tb = pd.DataFrame({"Dịch vụ": tt.service, "Kiểm tra chất lượng (s)": tt.sec_quality.map(lambda v: vn(v, 1)),
                       "Ghi Silver (s)": tt.sec_silver.map(lambda v: vn(v, 1)), "Tạo Gold (s)": tt.sec_gold.map(lambda v: vn(v, 1)),
                       "Tổng (s)": tt.sec_total.map(lambda v: vn(v, 1)), "Dòng/giây": tt.rows_per_sec.map(vint)})
    rp.TAB(tb, "Tổng thời gian xử lý theo bước và thông lượng", widths=[2.6, 3.0, 2.6, 2.6, 2.4, 2.8], size=10.5)
    rp.P(f"Bước ghi Silver chiếm phần lớn thời gian ({vn(100 * tot.sec_silver.sum() / tot.sec_total.sum(), 1)}% tổng thời gian) "
         f"vì phải nén và ghi toàn bộ dữ liệu. Bước kiểm tra chất lượng chỉ chiếm {vn(100 * tot.sec_quality.sum() / tot.sec_total.sum(), 1)}% "
         f"nhờ DuckDB chỉ đọc các cột cần cho quy tắc. Toàn bộ pipeline Bronze → Gold cho hai dịch vụ mất "
         f"{vn(tot.sec_total.sum() / 60, 1)} phút thời gian tính toán.")
    rp.H3("3.3.4. Dung lượng theo lớp")
    s2 = sto.copy()
    s2["service"] = s2.service.map({"hvfhv": "HVFHV", "yellow": "Taxi vàng"})
    s2["ratio"] = s2.silver_mb / s2.bronze_mb
    rp.TAB(pd.DataFrame({"Dịch vụ": s2.service, "Bronze (MB)": s2.bronze_mb.map(lambda v: vn(v, 1)),
                         "Silver (MB)": s2.silver_mb.map(lambda v: vn(v, 1)), "Silver / Bronze": s2.ratio.map(lambda v: vn(v, 2))}),
           "Dung lượng lưu trữ theo lớp", widths=[3, 3, 3, 3], size=11)
    rp.PS(
        f"Lớp Silver lớn hơn Bronze khoảng {vn((s2.ratio.mean() - 1) * 100, 0)}% dù đã loại bỏ các bản ghi lỗi. Nguyên nhân là Silver "
        f"thêm mười trường dẫn xuất (ngày, giờ, thứ, thời gian chờ, tốc độ, hai nhóm vùng, cờ chạm CRZ, chi phí hành khách) và "
        f"các cột chuỗi nhóm vùng. Đây là đánh đổi có chủ ý: tính một lần ở Silver thay vì tính lại ở mọi truy vấn phía sau. "
        f"Tổng dung lượng lớp Gold chỉ khoảng nửa gigabyte, tức nhỏ hơn Silver hơn hai mươi lần.")

    rp.H3("3.3.5. Tổ chức thư mục của đồ án")
    rp.P("Cấu trúc thư mục phản ánh trực tiếp các lớp của kiến trúc. Người chấm có thể tìm mọi đầu vào, đầu ra trung gian và kết "
         "quả theo quy ước dưới đây.")
    rp.CODE("\n".join([
        "CongestionPricing_CaseStudy/",
        "├── code/                      mã nguồn (00–14), config.py, panels.py, causal.py, viz.py, run_all.sh",
        "│   └── report/                mã dựng báo cáo (lib.py, results.py, front.py, ch1–ch6.py, appendix.py)",
        "├── data/",
        "│   ├── raw/                   Bronze: 50 tệp gốc của TLC (không sửa đổi)",
        "│   ├── bronze/                danh mục metadata của lớp Bronze",
        "│   ├── silver/service=…/year=…/month=…/part-k.parquet   dữ liệu chuyến đã làm sạch",
        "│   └── gold/                  dim_zone, zone_adjacency, 7 bảng tổng hợp, _parts/ theo khúc",
        "├── outputs/",
        "│   ├── tables/                bảng kết quả CSV (t01–t59, a01–a03)",
        "│   ├── figures/               hình PNG (f00–f41)",
        "│   └── logs/                  nhật ký JSON của từng bước và từng phân vùng",
        "└── report/                    báo cáo Word và PDF",
    ]), size=9)
    rp.H3("3.3.6. Truy vấn chuẩn hóa và gắn cờ chất lượng")
    rp.P("Trích đoạn dưới đây là phần lõi của bước Silver cho HVFHV: chuẩn hóa tên cột, gán giá trị mặc định cho các khoản phí "
         "trống và đặt phí CBD bằng 0 cho các tháng trước 2025. Toàn bộ được thực hiện trong DuckDB, dữ liệu không đi qua pandas.")
    rp.CODE("\n".join([
        "SELECT 'hvfhv' AS service, hvfhs_license_num AS company_code,",
        "       request_datetime AS request_ts, pickup_datetime AS pickup_ts, dropoff_datetime AS dropoff_ts,",
        "       PULocationID AS pu, DOLocationID AS dl, trip_miles AS miles, trip_time::DOUBLE AS time_s,",
        "       base_passenger_fare AS fare, coalesce(tolls,0) AS tolls, coalesce(bcf,0) AS bcf,",
        "       coalesce(sales_tax,0) AS tax, coalesce(congestion_surcharge,0) AS cong_sur,",
        "       coalesce(airport_fee,0) AS airport_fee, {cbd} AS cbd_fee, coalesce(tips,0) AS tips, driver_pay,",
        "       (shared_request_flag = 'Y')::INT AS shared_req, (wav_request_flag = 'Y')::INT AS wav_req",
        "FROM read_parquet('{f}')",
        "-- {cbd} = coalesce(cbd_congestion_fee,0) nếu tháng ≥ 2025-01, ngược lại 0.0",
    ]), size=8.5)
    rp.P("Sau đó, mỗi quy tắc chất lượng là một biểu thức logic được ép kiểu thành số nguyên, ví dụ quy tắc Q3 là "
         "(miles IS NULL OR miles <= 0 OR miles > 100)::INT. Một câu lệnh tổng hợp duy nhất đếm số vi phạm của cả bảy quy tắc, rồi "
         "câu lệnh COPY ghi các dòng có tổng cờ bằng 0 ra Silver kèm các trường dẫn xuất. Các bảng Gold được tạo bằng GROUP BY ALL trên "
         "tệp Silver vừa ghi, trong cùng một tiến trình.")

    # ---------------------------------------------------------------- 3.4
    rp.H2("3.4. Kiểm soát chất lượng dữ liệu")
    rp.H3("3.4.1. Bảy quy tắc chất lượng")
    rules = pd.DataFrame([
        ("Q1", "Thời điểm đón nằm ngoài tháng của tệp hoặc rỗng", "q_out_of_month"),
        ("Q2", "Vùng đón hoặc trả rỗng hoặc ngoài 1–263 (264, 265 là không xác định)", "q_bad_zone"),
        ("Q3", "Quãng đường ≤ 0 hoặc > 100 dặm", "q_bad_miles"),
        ("Q4", "Thời lượng < 60 giây hoặc > 4 giờ", "q_bad_time"),
        ("Q5", "Giá cước cơ sở ≤ 0 hoặc > 1.000 USD", "q_bad_fare"),
        ("Q6", "Tốc độ trung bình > 80 dặm/giờ", "q_bad_speed"),
        ("Q7", "Thu nhập tài xế âm hoặc rỗng (chỉ HVFHV)", "q_bad_pay"),
    ], columns=["Mã", "Điều kiện loại bỏ", "Tên cờ trong mã"])
    rp.TAB(rules, "Các quy tắc chất lượng dữ liệu áp dụng ở lớp Silver", widths=[1.4, 10.2, 4.4], size=10.5,
           align=["center", "left", "left"], source="Nguồn: config.py và 03_silver_gold_month.py.")
    rp.PS(
        "Các ngưỡng được chọn theo tiêu chí vật lý và kinh doanh hiển nhiên, không tinh chỉnh theo kết quả. Chuyến dưới một phút "
        "thường là hủy chuyến; tốc độ trên 80 dặm/giờ trong nội thành là lỗi thiết bị; giá cước bằng 0 thường là chuyến điều chỉnh. "
        "Các vùng 264 và 265 là mã \"không xác định\" và \"ngoài New York\" của TLC, không gắn được với nhóm xử lý hay đối chứng.")
    rp.H3("3.4.2. Kết quả kiểm tra chất lượng")
    qq = q.copy()
    qq["service"] = qq.service.map({"hvfhv": "HVFHV", "yellow": "Taxi vàng"})
    tq = pd.DataFrame({"Dịch vụ": qq.service, "Bản ghi thô": qq.n_raw.map(vint), "Bị loại": qq.n_rejected.map(vint),
                       "Tỷ lệ loại (%)": qq.reject_pct.map(lambda v: vn(v, 2)), "Còn lại (Silver)": qq.n_silver.map(vint)})
    rp.TAB(tq, "Kết quả kiểm soát chất lượng theo dịch vụ", widths=[2.6, 3.6, 3.2, 2.8, 3.8], size=10.5)
    hvq = q[q.service == "hvfhv"].iloc[0]
    yeq = q[q.service == "yellow"].iloc[0]
    rp.PS(
        f"Với HVFHV, {vn(hvq.reject_pct, 2)}% bản ghi bị loại và gần như toàn bộ là do quy tắc Q2: "
        f"{vint(hvq.q_bad_zone)} bản ghi có vùng đón hoặc trả không xác định. Các quy tắc khác chỉ loại vài trăm nghìn bản ghi. "
        f"Với taxi vàng, tỷ lệ loại cao hơn ({vn(yeq.reject_pct, 2)}%) và phân bố đều hơn giữa các quy tắc, trong đó giá cước "
        f"không hợp lệ ({vint(yeq.q_bad_fare)} bản ghi) và quãng đường không hợp lệ ({vint(yeq.q_bad_miles)} bản ghi) là hai "
        f"nguyên nhân chính. Điều này phù hợp với việc dữ liệu taxi vàng được ghi từ đồng hồ tính cước, có nhiều chuyến điều chỉnh "
        f"và hủy hơn so với dữ liệu nền tảng.")
    rp.FIG(R.fig("f02"), "Tỷ lệ bản ghi vi phạm từng quy tắc chất lượng theo dịch vụ")
    rp.P("Phụ lục F trình bày số bản ghi bị loại theo từng tháng và từng quy tắc. Tỷ lệ loại ổn định qua các tháng, không có "
         "bước nhảy tại tháng 01/2025, nên việc làm sạch dữ liệu không tạo ra khác biệt giả giữa hai giai đoạn.")

    # ---------------------------------------------------------------- 3.5
    rp.H2("3.5. Xác định vùng xử lý bằng dữ liệu")
    rp.H3("3.5.1. Vấn đề ranh giới")
    rp.PS(
        "Ranh giới CRZ là đường 60 và các tuyến đường ven sông. Ranh giới các vùng taxi của TLC được vẽ từ trước và không trùng "
        "với đường 60. Một số vùng nằm trọn phía nam, một số vùng nằm trọn phía bắc, còn một số vùng bị đường 60 cắt ngang. Nếu "
        "gán tay danh sách vùng, sai sót ở các vùng vắt ranh giới sẽ làm lẫn đơn vị xử lý với đơn vị đối chứng.")
    rp.H3("3.5.2. Thủ tục phân loại")
    rp.PS(
        "Đồ án dùng chính dữ liệu thu phí để phân loại. Với mỗi vùng, xét các chuyến HVFHV có điểm đón và điểm trả cùng nằm trong "
        "vùng đó (chuyến nội vùng) trong quý I/2025, sau ngày 05/01. Nếu vùng nằm trọn trong CRZ, gần như mọi chuyến nội vùng đều "
        "bị thu phí; nếu vùng nằm ngoài, gần như không chuyến nào bị thu; nếu vùng vắt ranh giới, tỷ lệ nằm ở khoảng giữa. Quy tắc "
        "phân loại:")
    rp.BUL([
        "CRZ: tỷ lệ chuyến nội vùng bị thu phí ≥ 90%.",
        "Vắt ranh giới (CRZ_PARTIAL): tỷ lệ từ 10% đến dưới 90%.",
        "Manhattan phía bắc (MN_NORTH): các vùng Manhattan còn lại.",
        "Các quận ngoài (OUTER): Bronx, Brooklyn, Queens, Staten Island, trừ sân bay.",
        "Sân bay (AIRPORT): EWR (1), JFK (132), LaGuardia (138), được tách riêng vì có cấu trúc nhu cầu đặc thù.",
    ])
    rp.FIG(R.fig("f03"), "Phân nhóm 263 vùng taxi theo mức độ chịu phí CBD, xác định từ dữ liệu quý I/2025")
    gg = grp.copy()
    gg["grp"] = gg.grp.map({"CRZ": "CRZ", "CRZ_PARTIAL": "Vắt ranh giới", "MN_NORTH": "Manhattan phía bắc",
                            "OUTER": "Quận ngoài", "AIRPORT": "Sân bay", "UNKNOWN": "Không xác định"})
    rp.TAB(gg.rename(columns={"grp": "Nhóm", "Borough": "Quận", "n_zones": "Số vùng"}),
           "Số vùng theo nhóm và theo quận", widths=[5, 5, 3], size=11)
    part = dim[dim.grp == "CRZ_PARTIAL"][["LocationID", "Zone", "fee_share_hvfhv", "fee_share_yellow", "n_intra_hvfhv"]].copy()
    tp = pd.DataFrame({"Mã vùng": part.LocationID.map(vint), "Tên vùng": part.Zone,
                       "Tỷ lệ thu phí HVFHV (%)": (100 * part.fee_share_hvfhv).map(lambda v: vn(v, 1)),
                       "Tỷ lệ thu phí taxi vàng (%)": (100 * part.fee_share_yellow).map(lambda v: vn(v, 1)),
                       "Số chuyến nội vùng HVFHV": part.n_intra_hvfhv.map(vint)})
    rp.TAB(tp, "Sáu vùng vắt qua ranh giới CRZ và tỷ lệ chuyến nội vùng bị thu phí", widths=[1.8, 4.6, 3.2, 3.2, 3.2], size=10.5,
           align=["center", "left", "center", "center", "center"])
    crz = dim[dim.grp == "CRZ"]
    rp.PS(
        f"Kết quả phân loại có độ tách rõ: {len(crz)} vùng CRZ có tỷ lệ thu phí nội vùng từ "
        f"{vn(100 * crz.fee_share_hvfhv.min(), 1)}% đến {vn(100 * crz.fee_share_hvfhv.max(), 1)}%, trong khi mọi vùng Manhattan "
        f"phía bắc đều dưới {vn(100 * dim[dim.grp == 'MN_NORTH'].fee_share_hvfhv.max(), 1)}%. Sáu vùng vắt ranh giới gồm Công viên "
        f"Trung tâm, Lenox Hill Đông và Tây, Lincoln Square Đông và Tây, Upper East Side Nam, đúng là các vùng nằm quanh đường 60 "
        f"trên bản đồ Manhattan dưới đây. Tỷ lệ thu phí của taxi vàng ở các vùng này cho thứ tự tương tự, là một kiểm tra chéo độc lập. "
        f"Các vùng vắt ranh giới không được đưa vào nhóm xử lý hay đối chứng của đặc tả chính; phần độ vững sẽ thử gộp chúng vào "
        f"nhóm xử lý.")
    rp.FIG(R.fig("f04"), "Manhattan: vùng CRZ và sáu vùng vắt qua ranh giới (đánh số theo mã vùng TLC)", width_cm=10.5)
    rp.H3("3.5.3. Khoảng cách và quan hệ kề")
    rp.PS(
        "Từ shapefile, đồ án tính diện tích, tâm của từng vùng và khoảng cách từ đa giác vùng tới hợp các đa giác CRZ (đơn vị "
        "km, hệ tọa độ phẳng New York State Plane). Hai vùng được coi là kề nhau nếu khoảng cách giữa hai đa giác dưới 200 feet, "
        "ngưỡng đủ để bỏ qua một con phố ngăn cách. Thông tin khoảng cách được dùng để chia các vùng ngoài CRZ thành các dải 0–1 km, "
        "1–2,5 km, 2,5–5 km, 5–10 km và trên 10 km phục vụ phân tích lan tỏa.")

    # ---------------------------------------------------------------- 3.6
    rp.H2("3.6. Các bảng Gold và panel phân tích")
    rp.H3("3.6.1. Bảy bảng Gold")
    gdesc = {
        "zone_day_pu": ("dịch vụ × ngày × vùng đón", "Panel chính, EDA"),
        "zone_day_do": ("dịch vụ × ngày × vùng trả", "Lan tỏa phía điểm trả"),
        "grp_hour_day": ("dịch vụ × ngày × giờ × nhóm đón × nhóm trả", "Luồng, tốc độ theo giờ"),
        "company_grp_day": ("dịch vụ × hãng × ngày × nhóm đón × nhóm trả", "Thị phần hãng"),
        "zone_hour_month": ("dịch vụ × tháng × vùng đón × giờ", "Không đồng nhất theo giờ"),
        "od_month": ("dịch vụ × tháng × vùng đón × vùng trả", "Panel OD, DML"),
        "trip_sample": ("mẫu ngẫu nhiên 0,25% chuyến HVFHV, 1% taxi vàng", "Phân phối từng chuyến"),
    }
    gt = pd.DataFrame([(k, v[0], vint(gold_rows.get(k, 0)), v[1]) for k, v in gdesc.items()],
                      columns=["Bảng", "Khóa", "Số dòng", "Sử dụng"])
    rp.TAB(gt, "Các bảng Gold, khóa tổng hợp và số dòng", widths=[3.4, 6.0, 2.4, 4.2], size=10,
           align=["left", "left", "right", "left"])
    rp.PS(
        "Mọi bảng Gold (trừ mẫu chuyến) chỉ chứa các đại lượng cộng được: số chuyến, tổng giá cước, tổng thu nhập tài xế, tổng "
        "quãng đường, tổng thời lượng, tổng tip, tổng phí CBD, tổng chi phí hành khách, tổng thời gian chờ và số chuyến có thời "
        "gian chờ hợp lệ. Các chỉ tiêu trung bình như giá/dặm hay tốc độ được tính ở bước phân tích bằng tỷ số của tổng, đảm bảo "
        "trọng số đúng theo chuyến và cho phép tổng hợp tiếp lên bất kỳ cấp nào mà không sai lệch.")
    rp.H3("3.6.2. Các panel dùng cho suy luận nhân quả")
    zw = meta["hv_zone_week"]
    yw = meta["ye_zone_week"]
    od = meta["hv_od_month"]
    pt = pd.DataFrame([
        ("HVFHV vùng × tuần", f"{zw['zones']} vùng ({zw['treated']} xử lý, {zw['control']} đối chứng) × {zw['weeks']} tuần", vint(zw["obs"]), vint(zw["trips"])),
        ("Taxi vàng vùng × tuần", f"{yw['zones']} vùng ({yw['treated']} xử lý, {yw['control']} đối chứng) × {yw['weeks']} tuần", vint(yw["obs"]), vint(yw["trips"])),
        ("HVFHV vùng × ngày", f"{meta['hv_zone_day']['zones']} vùng × 731 ngày", vint(meta["hv_zone_day"]["obs"]), "–"),
        ("HVFHV cặp OD × tháng", f"{od['pairs']} cặp × 24 tháng", vint(od["obs"]), vint(od["trips"])),
    ], columns=["Panel", "Cấu trúc", "Số quan sát", "Số chuyến bao phủ"])
    rp.TAB(pt, "Quy mô các panel dùng cho suy luận nhân quả", widths=[3.6, 6.4, 2.8, 3.2], size=10,
           align=["left", "left", "right", "right"])
    rp.PS(
        "Panel vùng × tuần của HVFHV chỉ giữ các vùng CRZ, Manhattan phía bắc và quận ngoài có bình quân ít nhất 100 chuyến đón "
        "mỗi ngày trong năm 2024 và có dữ liệu ở mọi tuần. Ngưỡng này loại các vùng rất nhỏ như công viên, đảo, nghĩa trang, nơi "
        "log số chuyến dao động mạnh vì lý do ngẫu nhiên. Phần độ vững thử ngưỡng 50 và 300 chuyến. Với taxi vàng, ngưỡng là 20 "
        "chuyến mỗi ngày và nhóm đối chứng chỉ gồm Manhattan phía bắc; lý do được giải thích ở Chương 4.",
        "Panel cặp OD × tháng giữ các cặp có bình quân ít nhất 300 chuyến mỗi tháng năm 2024 và có dữ liệu đủ 24 tháng, với cả hai "
        f"đầu thuộc CRZ, Manhattan phía bắc hoặc quận ngoài. Kết quả có {od['by_type'].get('CRZ→CRZ', 0)} cặp CRZ→CRZ, "
        f"{od['by_type'].get('CRZ→ngoài', 0)} cặp CRZ→ngoài, {od['by_type'].get('ngoài→CRZ', 0)} cặp ngoài→CRZ và "
        f"{od['by_type'].get('không chạm CRZ', 0)} cặp không chạm CRZ.")

    # ---------------------------------------------------------------- 3.7
    rp.H2("3.7. Thiết kế thực nghiệm hiệu năng")
    rp.PS(
        "Để trả lời RQ1 bằng số đo thay vì nhận định chung, đồ án thực hiện ba nhóm thực nghiệm trên chính dữ liệu HVFHV tháng "
        "03/2024. Mỗi phép đo chạy trong một tiến trình Python riêng để đo bộ nhớ đỉnh (max RSS) và lặp ba lần, báo cáo trung vị.",
    )
    rp.BUL([
        "**Định dạng lưu trữ:** lấy 2 triệu dòng đầu, ghi ra CSV, CSV nén gzip, Parquet Snappy và Parquet ZSTD; đo dung lượng, thời "
        "gian ghi và thời gian chạy cùng một truy vấn tổng hợp theo vùng đón.",
        "**Bộ máy xử lý:** chạy cùng truy vấn (số chuyến, tổng giá cước, tổng thu nhập tài xế theo vùng đón) trên cả tháng "
        "(khoảng 21 triệu dòng) bằng DuckDB, pandas (đọc 3 cột rồi groupby) và PyArrow (đọc 3 cột rồi group_by).",
        "**Cắt tỉa cột và đẩy điều kiện lọc:** so sánh đọc 2 cột với đọc cả 24 cột, và lọc theo ngày (cột thời gian có thứ tự trong "
        "tệp) với lọc theo vùng (cột không có thứ tự).",
    ])

    # ---------------------------------------------------------------- 3.8
    rp.H2("3.8. Chiến lược nhận dạng nhân quả")
    rp.H3("3.8.1. Đặc tả chính")
    rp.P("Với vùng z và tuần t, gọi T_z = 1 nếu z thuộc CRZ, P_t = 1 nếu tuần t bắt đầu từ 05/01/2025 trở đi và D_zt = T_z · P_t. "
         "Đặc tả chính là:")
    rp.EQ("Y_zt = α_z + γ_t + β · D_zt + ε_zt")
    rp.PS(
        "với Y_zt là một trong các biến kết quả định nghĩa ở mục 3.8.6. Sai số chuẩn phân cụm theo vùng. Với log số chuyến, 100·(e^β − 1) là "
        "phần trăm thay đổi. Với các chỉ tiêu tỷ số (giá/dặm, tốc độ, thời gian chờ), β là thay đổi tuyệt đối theo đơn vị của biến.")
    rp.H3("3.8.2. Các đặc tả bổ sung")
    rp.BUL([
        "**DDD mùa vụ:** thêm hiệu ứng cố định T_z × tuần trong năm (52 mức). Vì tuần 0 của năm 2025 cách tuần 0 của năm 2024 đúng "
        "364 ngày, mỗi tuần năm 2025 được so với tuần cùng thứ tự và cùng ngày trong tuần của năm 2024.",
        "**TWFE có trọng số:** trọng số theo số chuyến bình quân ngày của vùng năm 2024, cho ước lượng đại diện cho chuyến đi thay "
        "vì cho vùng.",
        "**TWFE + xu hướng nhóm:** thêm biến T_z × (số tuần kể từ mốc)/52, cho phép nhóm xử lý có xu hướng tuyến tính riêng.",
        "**Nghiên cứu sự kiện theo tuần** (từ −52 đến +51) và **theo tháng** (từ −12 đến +11), hệ số được chuẩn hóa theo trung bình "
        "giai đoạn trước.",
        "**Panel cặp OD × tháng:** hiệu ứng cố định cặp và tháng, xử lý là cặp chạm CRZ, phân cụm theo vùng đón; tách riêng ba loại "
        "luồng CRZ→CRZ, CRZ→ngoài, ngoài→CRZ.",
        "**Không đồng nhất theo giờ:** panel vùng × khung giờ × tháng, ước lượng riêng cho năm khung giờ.",
        "**Không đồng nhất theo ngày:** panel vùng × ngày với tương tác D × cuối tuần.",
    ])
    rp.H3("3.8.3. Kiểm soát tổng hợp")
    rp.PS(
        "Chuỗi xử lý là tổng số chuyến HVFHV đón trong các vùng CRZ theo tuần, chia cho trung bình năm 2024 để có chỉ số bằng 1. "
        "Mỗi vùng đối chứng cũng được chuẩn hóa như vậy. Trọng số không âm, tổng bằng 1, được tìm bằng quy hoạch toàn phương SLSQP "
        "để cực tiểu tổng bình phương sai lệch trên các tuần năm 2024. Kiểm định giả dược không gian lặp lại quy trình cho 60 vùng "
        "đối chứng có lưu lượng lớn nhất, mỗi lần coi một vùng là \"xử lý\" và dùng các vùng đối chứng còn lại làm nguồn.")
    rp.H3("3.8.4. Học máy nhân quả trên cặp OD")
    ov = dml["overlap"]
    rp.PS(
        "Đơn vị là cặp OD có ít nhất 3.600 chuyến trong năm 2024. Kết quả là thay đổi cùng kỳ ΔY = Y(2025) − Y(2024) của log số "
        "chuyến, tốc độ và thu nhập tài xế/dặm. Xử lý D = 1 nếu cặp chạm CRZ. Biến kiểm soát chính (bộ \"rút gọn\") gồm các đặc "
        "trưng chuyến đi năm 2024: log lưu lượng, quãng đường và thời lượng trung bình, tiền tip trung bình, tỷ trọng Uber, tỷ "
        "trọng chuyến đêm và cờ chuyến nội vùng. Bộ \"đầy đủ\" thêm tốc độ, giá/dặm, thu nhập/dặm và biến giả quận của hai đầu.",
        f"Mọi mô hình phụ là LightGBM với cross-fitting 5 phần. Ước lượng gồm PLR (θ), AIPW trên vùng chồng lấn ê(X) ∈ [0,05; 0,95] "
        f"và DR-learner cho CATE với cross-fitting lần hai. Mẫu có {vint(ov['n'])} cặp OD, trong đó {vint(ov['n_treated'])} cặp chạm "
        f"CRZ. Không đưa khoảng cách tới CRZ vào X vì biến này gần như xác định hoàn toàn D.")
    rp.H3("3.8.5. Lan tỏa, giả dược và độ vững")
    rp.BUL([
        "**Lan tỏa không gian:** hồi quy log số chuyến đón và log số chuyến trả lên các biến giả (dải khoảng cách × sau chính sách), "
        "nhóm tham chiếu là các vùng cách CRZ trên 10 km. Phía điểm trả tách riêng khách đến từ ngoài CRZ và khách đến từ CRZ.",
        "**Giả dược theo thời gian:** chỉ dùng dữ liệu năm 2024 và giả định chính sách bắt đầu 07/07/2024, cho cả panel vùng × tuần "
        "và panel OD × tháng, có và không có xu hướng nhóm.",
        f"**Hoán vị:** {R.J['10_spillover_robustness_perm']['permutation']['n_perm']} lần gán ngẫu nhiên {zw['treated']} vùng đối chứng "
        "làm vùng xử lý, ước lượng lại TWFE chỉ trên các vùng đối chứng.",
        "**Bảng độ vững:** thay nhóm đối chứng, ngưỡng lưu lượng, định nghĩa nhóm xử lý, cửa sổ thời gian, trọng số, hiệu ứng cố định "
        "và cấp phân cụm.",
    ])
    rp.H3("3.8.6. Định nghĩa biến kết quả")
    vd = pd.DataFrame([
        ("ln_n", "log số chuyến đón", "ln(Σ chuyến)"),
        ("fare_pm", "Giá cước cơ sở/dặm (USD)", "Σ base_passenger_fare / Σ trip_miles"),
        ("pay_pm", "Thu nhập tài xế/dặm (USD)", "Σ driver_pay / Σ trip_miles"),
        ("fare_pt, pay_pt", "Giá cước, thu nhập tài xế mỗi chuyến", "Σ / số chuyến"),
        ("rider_pt", "Tổng chi phí hành khách/chuyến (USD)", "giá cước + phí cầu đường + BCF + thuế + phụ thu + phí sân bay + phí CBD"),
        ("cbd_pt", "Phí CBD/chuyến", "Σ cbd_congestion_fee / số chuyến"),
        ("tips_pt", "Tip/chuyến", "Σ tips / số chuyến"),
        ("pay_share", "Thu nhập tài xế/giá cước (%)", "100 · Σ driver_pay / Σ base_passenger_fare"),
        ("mph", "Tốc độ trung bình (dặm/giờ)", "Σ trip_miles / (Σ trip_time / 3600)"),
        ("miles_pt", "Quãng đường/chuyến (dặm)", "Σ trip_miles / số chuyến"),
        ("wait", "Thời gian chờ đón (phút)", "Σ (pickup − request) / số chuyến hợp lệ"),
        ("shared_pct", "Tỷ lệ yêu cầu đi chung (%)", "100 · Σ shared_request / số chuyến"),
    ], columns=["Tên biến", "Ý nghĩa", "Cách tính từ bảng Gold"])
    rp.TAB(vd, "Định nghĩa các biến kết quả", widths=[2.6, 5.2, 8.2], size=10, align=["left", "left", "left"],
           source="Nguồn: panels.py.")

    # ---------------------------------------------------------------- 3.9
    rp.H2("3.9. Môi trường tính toán và khả năng tái lập")
    env = pd.DataFrame([
        ("Hệ điều hành", "Linux (máy ảo trên Windows), 2 lõi CPU, khoảng 3 GB RAM"),
        ("Python", "3.10"),
        ("DuckDB", "1.5.5 (giới hạn bộ nhớ 1,8 GB, 2 luồng)"),
        ("PyArrow / pandas", "25.0.1 / 2.3.3"),
        ("statsmodels / scikit-learn / LightGBM", "0.15.0 / 1.7.2 / 4.7.0"),
        ("pyshp / shapely / matplotlib", "hiện hành / 2.1.2 / 3.10.9"),
        ("Apache Spark (PySpark) / Java", "3.5.3 / OpenJDK 11 (chế độ local[2], bộ nhớ driver 1.200 MB)"),
        ("Hạt giống ngẫu nhiên", "20250105 (mẫu chuyến, cross-fitting, hoán vị)"),
    ], columns=["Thành phần", "Phiên bản, cấu hình"])
    rp.TAB(env, "Môi trường tính toán", widths=[6, 10], size=10.5, align=["left", "left"],
           source="Nguồn: requirements.txt và config.py.")
    rp.PS(
        "Toàn bộ pipeline chạy bằng một lệnh bash code/run_all.sh từ thư mục gốc của đồ án. Các bước sau bước 04 chỉ đọc các bảng "
        "Gold nên có thể chạy lại độc lập trong vài phút. Mọi phép ngẫu nhiên dùng cùng một hạt giống, nên kết quả chạy lại trùng "
        "khớp. Báo cáo này được dựng bằng bước 13, đọc trực tiếp các tệp CSV và PNG trong thư mục outputs.")
    rp.H2("3.10. Các mô-đun mở rộng")
    mods = pd.DataFrame([
        ("15_spark_pipeline.py", "Tái lập bảng Gold bằng Spark, đối chứng từng ô; tám thực nghiệm hiệu năng và cơ chế", "Chương 5"),
        ("15b_compare_outputs.py", "So sánh bảng kết quả trước và sau khi sửa lỗi thượng nguồn", "Chương 5, 6"),
        ("16_governance_risk.py", "Danh mục, phả hệ, dấu băm, đối soát, biểu đồ kiểm soát, bất thường, k-ẩn danh, "
         "quyền riêng tư vi phân, RTO", "Chương 6"),
        ("17_business_analytics.py", "Tác động theo hãng, dự báo nhu cầu, công suất thống kê, định giá động, hạch toán tài nguyên",
         "Chương 7"),
        ("18_theory_sensitivity.py", "Kiểm định giả thuyết lý thuyết (liều – đáp ứng, tốc độ – lưu lượng, lan tỏa theo phơi nhiễm, "
         "thu nhập tài xế)", "Mục 4.15"),
        ("19_long_preperiod.py", "Nghiên cứu sự kiện theo tháng 2022–2025, giả dược năm 2024, điều chỉnh xu hướng, độ nhạy "
         "Rambachan–Roth (RM, SD)", "Mục 4.14.4, 4.14.5"),
    ], columns=["Bước", "Nội dung", "Kết quả ở"])
    rp.TAB(mods, "Các bước mở rộng của pipeline", widths=[4.4, 9.2, 2.4], size=10, align=["left", "left", "center"],
           source="Nguồn: thư mục code/.")
    rp.PS(
        "Ba bước 15 đến 17 đọc cùng các lớp Silver và Gold như các bước phân tích nhân quả, nên không làm thay đổi kết quả của "
        "Chương 4, với một ngoại lệ có chủ đích: đối chứng ở bước 15 phát hiện một lỗi ép kiểu ở bước 04, bước 04 được sửa và các "
        "bước 06 đến 14 được chạy lại trước khi dựng báo cáo này. Thiết kế thực nghiệm chi tiết của từng mô-đun được trình bày ở đầu "
        "chương tương ứng, để mỗi chương có thể đọc độc lập.")
    rp.H2("3.11. Tiểu kết Chương 3")
    rp.P(f"Chương 3 đã mô tả dữ liệu ({vint(nraw)} bản ghi thô), kiến trúc Lakehouse ba lớp với xử lý theo khúc, bảy quy tắc "
         f"chất lượng, thủ tục xác định vùng xử lý từ dữ liệu, bảy bảng Gold và bốn panel phân tích, cùng chiến lược nhận dạng "
         f"gồm nhiều thiết kế bổ trợ nhau, cùng ba mô-đun mở rộng về xử lý phân tán, quản trị dữ liệu và phân tích kinh doanh. "
         f"Chương 4 trình bày kết quả của phần phân tích nhân quả.")
