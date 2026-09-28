#!/usr/bin/env bash
# Chạy toàn bộ pipeline của đồ án theo đúng thứ tự.
# Dùng:  bash code/run_all.sh        (chạy từ thư mục gốc CongestionPricing_CaseStudy)
# Yêu cầu: Java 11+ cho bước 15; đã có 50 tệp dữ liệu thô 2024–2025 trong data/raw (xem code/00_download_data.ps1 hoặc 00_download_data.py)
set -euo pipefail
cd "$(dirname "$0")/.."

python code/01_bronze_catalog.py          # Bronze: danh mục metadata, lệch lược đồ
python code/02_zone_dimension.py          # Bảng chiều vùng, xác định CRZ từ dữ liệu
python code/03_silver_gold_month.py all   # Silver + Gold theo từng khúc tháng (120 phân vùng)
python code/04_gold_consolidate.py        # Hợp nhất Gold, nhật ký chất lượng
python code/05_benchmark.py format        # Thực nghiệm định dạng lưu trữ
python code/05_benchmark.py engine        # Thực nghiệm bộ máy xử lý
python code/05_benchmark.py pruning       # Cắt tỉa cột, đẩy điều kiện lọc
python code/06_eda.py                     # Phân tích khám phá
python code/07_did_main.py                # DiD, DDD, nghiên cứu sự kiện, OD, không đồng nhất
python code/08_synthetic_control.py       # Kiểm soát tổng hợp và giả dược không gian
python code/09_dml_heterogeneity.py       # DML, AIPW, CATE, BLP, GATES
python code/10_spillover_robustness.py all  # Lan tỏa, giả dược thời gian, hoán vị, độ vững
python code/11_appendix_tables.py         # Bảng phụ lục
python code/12_pipeline_figures.py        # Hình hiệu năng pipeline và sơ đồ kiến trúc
python code/14_extra_analysis.py          # Phân tích bổ sung: tác động theo vùng, lan tỏa theo quận, sân bay
# Bước 15: xử lý phân tán bằng Apache Spark (cần Java 11+ và pyspark). SPARK_WORK trỏ tới thư mục
# làm việc có quyền xóa tệp (Spark tạo và xóa thư mục _temporary, checkpoint).
export SPARK_WORK="${SPARK_WORK:-$PWD/data/_spark}"
python code/15_spark_pipeline.py repro        # Tái lập bảng Gold zone_day_pu bằng Spark (48 tháng-dịch vụ)
python code/04_gold_consolidate.py            # (đã sửa lỗi ép kiểu phát hiện nhờ bước 15; chạy lại là lũy đẳng)
python code/15_spark_pipeline.py validate     # Đối chứng từng ô Spark với DuckDB
for e in duckdb spark_df spark_sql; do python code/15_spark_pipeline.py engine $e; done
for p in 1 2 4 8 16 32 64 200 1000; do
  python code/15_spark_pipeline.py shuffle $p; python code/15_spark_pipeline.py shuffle $p noaqe
done
for k in 1 2 3 4 6; do
  python code/15_spark_pipeline.py scale duckdb $k; python code/15_spark_pipeline.py scale spark_df $k
done
python code/15_spark_pipeline.py cache
python code/15_spark_pipeline.py prune
python code/15_spark_pipeline.py arrow
python code/15_spark_pipeline.py stream_prep
python code/15_spark_pipeline.py stream
python code/15_spark_pipeline.py report
# Bước 16: quản trị dữ liệu, quyền riêng tư, rủi ro
for p in catalog lineage integrity reconcile anomaly tripanom privacy dp dr; do python code/16_governance_risk.py $p; done
# Bước 17: phân tích phục vụ quyết định kinh doanh
for p in company forecast power pricing tco; do python code/17_business_analytics.py $p; done
python code/18_theory_sensitivity.py      # Kiểm định giả thuyết lý thuyết (H1b, H2b, H3, H4)
# Bước 19: giai đoạn trước chính sách mở rộng 2022–2023 (cần 48 tệp thô của 00_download_data_2022_2023.ps1).
# Các bảng chính 2024–2025 không đổi: kết quả mở rộng ghi vào _parts_ext, partitions_ext và gold/long/.
# DUCKDB_TMP trỏ tới thư mục có quyền xóa tệp (DuckDB tạo và xóa tệp tạm khi tràn bộ nhớ).
export DUCKDB_TMP="${DUCKDB_TMP:-$PWD/data/_duck_tmp}"
python code/01_bronze_catalog.py ext      # Bronze 2022–2023: t01x, t02x, t03x
python code/03_silver_gold_month.py ext   # Silver + Gold theo tháng 2022–2023 (một số tháng giữ Silver trong bộ nhớ)
python code/04_gold_consolidate.py ext    # Hợp nhất Gold 2022–2025 vào gold/long/, t06x–t08x
python code/19_long_preperiod.py          # Nghiên cứu sự kiện 2022–2025, giả dược, điều chỉnh xu hướng, Rambachan–Roth
python code/13_build_report.py            # Dựng báo cáo Word/PDF từ các bảng và hình ở trên
