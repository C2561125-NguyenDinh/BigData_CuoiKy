# Đồ án Nghiên cứu Dữ liệu lớn trong kinh doanh – Case study phí giảm ùn tắc Manhattan

**Báo cáo:** [`report/BaoCao_DoAn_BigData_PhiUnTacManhattan.pdf`](report/BaoCao_DoAn_BigData_PhiUnTacManhattan.pdf) (bản Word: `.docx` cùng thư mục)

**Đề tài:** Tác động không đồng nhất và hiệu ứng lan tỏa của phí giảm ùn tắc Manhattan lên thị trường gọi xe công nghệ:
tiếp cận học máy nhân quả trên kiến trúc Lakehouse với hàng trăm triệu chuyến đi.

Dữ liệu: hồ sơ chuyến đi HVFHV (Uber, Lyft) và taxi vàng của NYC TLC, 01/2022–12/2025 (khoảng 1,1 tỷ bản ghi thô).
Phân tích chính dùng 2024–2025; 2022–2023 dùng để kiểm tra xu hướng trước chính sách.

## Kết luận chính, xếp theo mức độ chắc chắn

1. **Thời gian chờ xe trong vùng thu phí giảm**: giữ nguyên qua sai số Conley, phân cụm hai chiều, wild cluster bootstrap,
   hiệu chỉnh kiểm định bội và 5/6 đặc tả xu hướng dài hạn.
2. **Tốc độ chuyến đi tăng**: có ý nghĩa ở phần lớn đặc tả, nhưng độ lớn phụ thuộc giả định xu hướng.
3. **Số chuyến gọi xe**: giảm 6–10% so với năm trước, nhưng CRZ đã giảm tương đối từ trước chính sách; tùy giả định xu
   hướng, tác động của phí nằm trong khoảng 0 đến khoảng 10%. Dữ liệu không xác định được con số chính xác hơn.
4. **Giá cước, thu nhập tài xế**: không kết luận được do xu hướng có sẵn.

Chi tiết ở mục 4.14–4.16 của báo cáo; bảng `outputs/tables/t90`, `t92`–`t95`.

## Nội dung thư mục

| Thư mục | Nội dung |
|---|---|
| `code/` | Mã nguồn bước 00–21 (đánh số theo thứ tự chạy), `config.py`, `panels.py`, `causal.py`, `viz.py`, `run_all.py`, `run_all.sh`, `requirements.txt` |
| `code/report/` | Mã dựng báo cáo Word/PDF từ kết quả (không có số liệu gõ tay) |
| `data/gold/` | Lớp Gold (bảng tổng hợp, ~240 MB): đủ để chạy lại mọi phân tích nhân quả mà không cần dữ liệu thô |
| `data/README.md` | Hướng dẫn tải dữ liệu thô (~24 GB, không đưa lên kho) |
| `outputs/tables/` | Mọi bảng kết quả (CSV) dùng trong báo cáo |
| `outputs/figures/` | Mọi hình (PNG) dùng trong báo cáo |
| `outputs/logs/` | Nhật ký chạy của từng bước và từng phân vùng |
| `report/` | Báo cáo hoàn chỉnh `.pdf` và `.docx` |

## Chạy lại

```bash
pip install -r code/requirements.txt

# Cách 1 – nhanh, không cần tải dữ liệu thô: chạy lại phân tích 06–11, 14, 17–20 từ lớp Gold kèm theo kho và dựng báo cáo
python code/run_all.py --from-gold

# Cách 2 – toàn bộ pipeline từ đầu: tải ~24 GB dữ liệu thô, dựng Bronze → Silver → Gold, mọi thực nghiệm và báo cáo
python code/run_all.py              # thêm --no-spark nếu không có Java 11+, --no-report nếu không có LibreOffice
```

`run_all.py` chạy được trên Windows, macOS và Linux; `run_all.sh` là bản bash tương đương. Dữ liệu thô:
`code/00_download_data.py` (2024–2025) và `code/00_download_data_2022_2023.py` (2022–2023); bản PowerShell `.ps1` vẫn được giữ.
Bước 13 (dựng báo cáo) cần LibreOffice (`soffice`) và `pdftotext`. Trên máy 2 lõi, 3 GB RAM, bước 03 mất khoảng 84 phút cho
2024–2025; các bước phân tích chỉ đọc lớp Gold và chạy trong vài phút.

## Các bước

| Bước | Nội dung |
|---|---|
| 00 | Tải dữ liệu thô NYC TLC |
| 01–04 | Bronze (danh mục, lệch lược đồ), bảng chiều vùng, Silver + Gold theo tháng, hợp nhất Gold (`ext`: 2022–2023) |
| 05 | Thực nghiệm định dạng lưu trữ, bộ máy xử lý, cắt tỉa cột |
| 06–11, 14 | Khám phá dữ liệu, DiD/DDD/nghiên cứu sự kiện, kiểm soát tổng hợp, DML, lan tỏa và độ vững, bảng phụ lục |
| 12, 13 | Hình pipeline; dựng báo cáo |
| 15, 15b | Apache Spark: tái lập Gold, đối chứng từng ô với DuckDB, 8 thực nghiệm hiệu năng |
| 16 | Quản trị dữ liệu, quyền riêng tư (k-ẩn danh, quyền riêng tư vi phân), rủi ro |
| 17 | Phân tích phục vụ quyết định kinh doanh |
| 18 | Kiểm định giả thuyết của mô hình lý thuyết |
| 19 | Giai đoạn trước chính sách 2022–2025, giả dược theo năm, điều chỉnh xu hướng, Rambachan–Roth |
| 20 | Suy luận bền vững: sai số Conley, phân cụm hai chiều, wild cluster bootstrap, Holm/BH/Romano–Wolf, sáu dạng xu hướng, Rambachan–Roth có bootstrap, DML theo ngưỡng cắt và ATO |
| 21 | Dựng lại một số phân vùng Gold 2022–2023 từ Bronze để kiểm chứng (Silver các tháng này không lưu bền) |

## Ghi chú vận hành

- Spark và DuckDB cần xóa được tệp tạm. Nếu thư mục dự án nằm trên ổ không cho xóa, đặt `SPARK_WORK` và `DUCKDB_TMP` sang
  thư mục cục bộ (ví dụ `$HOME/spark_work`, `$HOME/duck_tmp`). Trên máy ảo không phân giải được tên máy, cần
  `SPARK_LOCAL_HOSTNAME=localhost` (mã đã đặt sẵn).
- Trên máy 3 GB RAM, HVFHV từ 08/2022 được chia 6 khúc mỗi tháng và Silver của các tháng này (cùng mọi tháng taxi vàng
  2022–2023) chỉ giữ trong bộ nhớ; bước 21 kiểm chứng rằng Gold của các tháng này dựng lại được đúng từ Bronze.
- Đối chứng ở bước 15 từng phát hiện lỗi ép kiểu ở bước 04 (phí CBD của taxi vàng bị làm tròn khi hợp nhất lược đồ); đã sửa
  bằng `union_by_name=true`, `t61a_*` lưu kết quả đối chứng trước khi sửa.
