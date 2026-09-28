"""Bước 12 - Hình và bảng về hiệu năng pipeline (từ nhật ký chạy thực tế).

Chạy:  python code/12_pipeline_figures.py
"""
import json

import numpy as np
import pandas as pd

from config import LOG, TAB
from viz import C, fig, plt, save

fmt = pd.read_csv(TAB / "t09_bench_format.csv")
eng = pd.read_csv(TAB / "t10_bench_engine.csv")
pru = pd.read_csv(TAB / "t11_bench_pruning.csv")
run = pd.read_csv(TAB / "t08_partition_runtime.csv")
qm = pd.read_csv(TAB / "t06_quality_by_month.csv")
man = pd.read_csv(TAB / "t01_bronze_manifest.csv")

f, axs = fig(6.8, 3.0, ncols=2)
axs[0].barh(fmt.format, fmt.size_mb, color=[C["s2"], C["s2"], C["s1"], C["s1"]])
axs[0].invert_yaxis()
axs[0].set_xlabel("MB (2 triệu dòng HVFHV)")
axs[0].set_title("Kích thước tệp", fontsize=9.5)
axs[1].barh(fmt.format, fmt.agg_query_s_median, color=[C["s2"], C["s2"], C["s1"], C["s1"]])
axs[1].invert_yaxis()
axs[1].set_yticklabels([])
axs[1].set_xlabel("Giây (trung vị 3 lần)")
axs[1].set_title("Thời gian truy vấn tổng hợp theo vùng", fontsize=9.5)
for ax, col in ((axs[0], "size_mb"), (axs[1], "agg_query_s_median")):
    for i, v in enumerate(fmt[col]):
        ax.annotate(f"{v:.2f}" if v < 10 else f"{v:.0f}", (v, i), xytext=(3, 0), textcoords="offset points",
                    va="center", fontsize=8, color=C["text2"])
f.suptitle("So sánh định dạng lưu trữ trên cùng lát cắt dữ liệu", x=0.02, ha="left", fontsize=10.5,
           fontweight="bold")
f.tight_layout()
save(f, "f35_bench_format")

f, axs = fig(6.8, 2.8, ncols=2)
lab = [e.split(" (")[0] for e in eng.engine]
axs[0].bar(lab, eng.seconds_median, color=C["s1"], width=0.55)
axs[0].set_ylabel("Giây (trung vị)")
axs[0].set_title("Thời gian", fontsize=9.5)
axs[1].bar(lab, eng.max_rss_mb, color=C["s3"], width=0.55)
axs[1].set_ylabel("MB")
axs[1].set_title("Bộ nhớ đỉnh (max RSS)", fontsize=9.5)
f.suptitle("Ba bộ máy xử lý trên 1 tháng HVFHV đầy đủ (21,3 triệu dòng)", x=0.02, ha="left",
           fontsize=10.5, fontweight="bold")
f.tight_layout()
save(f, "f36_bench_engine")

r = run[run.service == "hvfhv"].copy()
r["rows_m"] = r.n_raw / 1e6
f, ax = fig(6.4, 3.0)
ax.scatter(r.rows_m, r.sec_total, s=18, color=C["s1"], label="HVFHV (khúc 1/4 tháng)")
ry = run[run.service == "yellow"]
ax.scatter(ry.n_raw / 1e6, ry.sec_total, s=18, color=C["s2"], label="Taxi vàng (cả tháng)")
ax.set_xlabel("Triệu dòng đầu vào")
ax.set_ylabel("Giây (Bronze → Silver → Gold)")
ax.set_title("Thời gian xử lý mỗi phân vùng theo số dòng")
ax.legend()
save(f, "f37_partition_runtime")

tot = run.groupby("service")[["sec_quality", "sec_silver", "sec_gold", "sec_total", "n_raw", "silver_mb"]].sum()
tot["rows_per_sec"] = tot.n_raw / tot.sec_total
tot.to_csv(TAB / "t52_pipeline_totals.csv")
size = man.groupby("service").size_mb.sum().rename("bronze_mb").to_frame().join(tot.silver_mb)
size.to_csv(TAB / "t53_storage_by_layer.csv")
print(tot, size)

# ---------------- Sơ đồ kiến trúc pipeline (vẽ từ cấu hình thực tế) ----------------
from matplotlib.patches import FancyBboxPatch

gold_rows = json.loads((LOG / "04_gold_consolidate.json").read_text())["rows"]
f, ax = plt.subplots(figsize=(6.8, 4.4))
ax.set_xlim(0, 100)
ax.set_ylim(0, 64)
ax.axis("off")


def box(x, y, w, h, title, lines, col):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.2",
                                facecolor=col, edgecolor=C["text2"], lw=0.8))
    ax.text(x + w / 2, y + h - 2.6, title, ha="center", va="top", fontsize=8.6, fontweight="bold", color=C["text"])
    for i, t in enumerate(lines):
        ax.text(x + w / 2, y + h - 7.2 - 3.6 * i, t, ha="center", va="top", fontsize=6.8, color=C["text"])


def arrow(x1, y1, x2, y2):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="->", color=C["text2"], lw=1.1))


nb = int(man.n_rows.sum())
box(1, 38, 22, 24, "Nguồn", ["NYC TLC (CloudFront)", "48 tệp Parquet", "HVFHV + taxi vàng", "01/2024 – 12/2025", f"{nb/1e6:,.1f} triệu dòng".replace(",", "X").replace(".", ",").replace("X", ".")], "#f0efec")
box(27, 38, 22, 24, "Bronze", ["Tệp gốc, bất biến", "Danh mục metadata", "Phát hiện lệch lược đồ", f"{man.size_mb.sum()/1024:,.1f} GB".replace(".", ","), "t01–t03"], "#e4d6c3")
box(53, 38, 22, 24, "Silver", ["Lược đồ chung", "7 quy tắc chất lượng", "Parquet ZSTD", "service/year/month", f"{int(qm.n_silver.sum())/1e6:,.1f} triệu dòng".replace(",", "X").replace(".", ",").replace("X", ".")], "#d9dde3")
box(77, 38, 22, 24, "Gold", ["7 bảng tổng hợp", "vùng×ngày, OD×tháng", "nhóm×giờ×ngày", "mẫu 0,25% chuyến", "dim_zone, kề nhau"], "#f3e2a6")
arrow(23.5, 50, 26.5, 50)
arrow(49.5, 50, 52.5, 50)
arrow(75.5, 50, 76.5, 50)
box(1, 4, 30, 26, "Phân tích mô tả", ["EDA, bản đồ, chuỗi thời gian", "Doanh thu phí CBD", "Tốc độ, thời gian chờ", "Hiệu năng định dạng/bộ máy"], "#eef3fb")
box(35, 4, 30, 26, "Suy luận nhân quả", ["DiD / TWFE / DDD mùa vụ", "Nghiên cứu sự kiện", "Kiểm soát tổng hợp", "Giả dược, hoán vị, độ vững"], "#eef3fb")
box(69, 4, 30, 26, "Học máy nhân quả", ["DML (PLR, AIPW)", "DR-learner cho CATE", "BLP, GATES, CLAN", "LightGBM, cross-fitting"], "#eef3fb")
for x in (16, 50, 84):
    arrow(88, 37.5, x, 30.8)
ax.text(50, 63.5, "DuckDB (SQL, thực thi vector hóa, giới hạn bộ nhớ 1,8 GB) · Python · Pandas · statsmodels/SciPy · LightGBM",
        ha="center", va="bottom", fontsize=7, color=C["text2"])
save(f, "f00_architecture")
