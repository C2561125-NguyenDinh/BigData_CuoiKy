# Dữ liệu

`data/gold/` có sẵn trong kho: các bảng tổng hợp của lớp Gold (khoảng 240 MB), đủ để chạy lại mọi phân tích nhân quả
và dựng báo cáo bằng `python code/run_all.py --from-gold`.

Dữ liệu thô (khoảng 24 GB Parquet), lớp Bronze/Silver và các phân vùng Gold trung gian không được đưa lên kho vì dung lượng.
Tải lại dữ liệu thô vào `data/raw/`:

```bash
python code/00_download_data.py             # 2024–2025
python code/00_download_data_2022_2023.py   # 2022–2023 (giai đoạn trước chính sách mở rộng)
```

Bản PowerShell tương đương: `code/00_download_data.ps1`, `code/00_download_data_2022_2023.ps1`.
Sau đó chạy `python code/run_all.py` để dựng lại toàn bộ Bronze → Silver → Gold, các bảng, hình và báo cáo.
