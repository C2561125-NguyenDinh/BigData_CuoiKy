"""Quy ước trình bày hình dùng chung cho mọi hình trong báo cáo.

Bảng màu phân loại dùng thứ tự cố định (không xoay vòng), đã kiểm tra độ
phân biệt với người mù màu. Nhóm xử lý (CRZ) luôn mang màu 1, nhóm đối chứng
luôn mang màu 2, để người đọc nhận diện nhất quán giữa các hình.
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager  # noqa: F401

from config import FIG

C = dict(s1="#2a78d6", s2="#eb6834", s3="#1baf7a", s4="#eda100", s5="#e87ba4",
         s6="#008300", s7="#4a3aa7", s8="#e34948",
         text="#0b0b0b", text2="#52514e", muted="#8a8984", grid="#e4e3df",
         surface="#ffffff", neutral="#c9c8c2", neutral_dark="#8f8e88",
         div_neg="#2a78d6", div_mid="#f0efec", div_pos="#e34948")
SEQ = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
GROUP_COLOR = {"CRZ": C["s1"], "CRZ_PARTIAL": C["s2"], "MN_NORTH": C["s3"],
               "OUTER": C["neutral"], "AIRPORT": C["neutral_dark"], "UNKNOWN": "#ffffff"}
GROUP_LABEL = {"CRZ": "Trong vùng thu phí (CRZ)", "CRZ_PARTIAL": "Vắt qua ranh giới",
               "MN_NORTH": "Manhattan phía bắc", "OUTER": "Các quận ngoài",
               "AIRPORT": "Sân bay", "UNKNOWN": "Không xác định"}

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9.5, "axes.titlesize": 10.5,
    "axes.labelsize": 9.5, "axes.edgecolor": C["grid"], "axes.labelcolor": C["text2"],
    "axes.titleweight": "bold", "axes.titlecolor": C["text"], "axes.titlelocation": "left",
    "axes.grid": True, "grid.color": C["grid"], "grid.linewidth": 0.6,
    "axes.spines.top": False, "axes.spines.right": False,
    "xtick.color": C["text2"], "ytick.color": C["text2"],
    "xtick.labelsize": 8.5, "ytick.labelsize": 8.5,
    "legend.frameon": False, "legend.fontsize": 8.5, "lines.linewidth": 2.0,
    "figure.dpi": 110, "savefig.dpi": 200, "savefig.bbox": "tight",
    "figure.facecolor": C["surface"], "axes.facecolor": C["surface"],
})


def fig(w=6.6, h=3.4, **kw):
    return plt.subplots(figsize=(w, h), **kw)


def policy_line(ax, x, label="05/01/2025: bắt đầu thu phí"):
    ax.axvline(x, color=C["text2"], lw=1.0, ls="--", zorder=1)
    ax.annotate(label, xy=(x, 1), xycoords=("data", "axes fraction"), xytext=(4, -4),
                textcoords="offset points", va="top", fontsize=8, color=C["text2"])


def save(f, name):
    f.savefig(FIG / f"{name}.png")
    plt.close(f)
    return FIG / f"{name}.png"
