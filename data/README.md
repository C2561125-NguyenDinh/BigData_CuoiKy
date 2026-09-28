# Dữ liệu

Dữ liệu thô (~24 GB Parquet) và các lớp Bronze/Silver/Gold không được đưa lên GitHub vì dung lượng.

Tải lại dữ liệu thô vào `data/raw/`:

```bash
python code/00_download_data.py                                               # 2024–2025
powershell -ExecutionPolicy Bypass -File code/00_download_data.ps1            # 2024–2025 (Windows)
powershell -ExecutionPolicy Bypass -File code/00_download_data_2022_2023.ps1  # 2022–2023 (giai đoạn trước chính sách mở rộng)
```

Sau đó chạy `bash code/run_all.sh` để dựng lại Bronze → Silver → Gold, các bảng và hình trong `outputs/` và báo cáo trong `report/`.
