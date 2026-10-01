"""Bước 13 - Dựng báo cáo đồ án (Word + PDF) từ các bảng và hình trong outputs/.

Quy trình hai lượt:
  Lượt 1: dựng tài liệu với danh mục chưa có số trang, xuất PDF bằng LibreOffice,
          dò số trang của từng tiêu đề, chú thích hình và bảng trong PDF.
  Lượt 2: dựng lại tài liệu với số trang đã đo và xuất bản cuối.
Không có số liệu nào được gõ tay: nội dung các chương đọc kết quả qua report/results.py.

Chạy:  python code/13_build_report.py
Yêu cầu: python-docx, LibreOffice (lệnh soffice), poppler-utils (pdftotext).
"""
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "report"))
ROOT = HERE.parent
OUT_DIR = ROOT / "report"
OUT_DIR.mkdir(exist_ok=True)
NAME = "BaoCao_DoAn_BigData_PhiUnTacManhattan"

from lib import Report  # noqa: E402
from results import Results  # noqa: E402
import front, ch1, ch2, ch3, ch4, ch5, ch6, ch7, ch8, ch9, refs, appendix  # noqa: E402,E401


FRONT_TOC = ["LỜI CẢM ƠN", "LỜI CAM KẾT", "TÓM TẮT", "DANH MỤC TỪ VIẾT TẮT",
             "DANH MỤC BẢNG BIỂU", "DANH MỤC HÌNH ẢNH"]


def build(pages):
    R = Results(ROOT)
    rp = Report(pages)
    front.cover(rp)
    front.thanks(rp)
    front.commitment(rp, R)
    front.abstract_vi(rp, R)
    # Dựng nội dung một lần vào tài liệu tạm để biết danh sách tiêu đề, hình, bảng,
    # rồi mới chèn các danh mục vào trước phần nội dung của tài liệu chính.
    tmp = Report(pages)
    for m in (ch1, ch2, ch3, ch4, ch5, ch6, ch7, ch8, ch9):
        m.build(tmp, R)
    refs.build(tmp, R)
    appendix.build(tmp, R)
    # Thứ tự theo mẫu: mục lục, danh mục từ viết tắt, danh mục bảng biểu, danh mục hình ảnh
    rp.H1("MỤC LỤC", numbered=False, toc=False, size=14)
    rp.LISTING([(1, t) for t in FRONT_TOC] + tmp.heads, "toc")
    front.abbreviations(rp)
    rp.H1("DANH MỤC BẢNG BIỂU", numbered=False, toc=False, size=14)
    rp.LISTING([(1, f"{a}. {b}") for a, b in tmp.tabs], "tab")
    rp.H1("DANH MỤC HÌNH ẢNH", numbered=False, toc=False, size=14)
    rp.LISTING([(1, f"{a}. {b}") for a, b in tmp.figs], "fig")
    # Dựng nội dung thật vào tài liệu chính (lặp lại để đánh số khớp)
    for m in (ch1, ch2, ch3, ch4, ch5, ch6, ch7, ch8, ch9):
        m.build(rp, R)
    refs.build(rp, R)
    appendix.build(rp, R)
    return rp, tmp


def norm(s):
    s = unicodedata.normalize("NFC", s)
    return re.sub(r"\s+", " ", s).strip().lower()


def to_pdf(docx_path):
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(docx_path.parent),
                    str(docx_path)], check=True, capture_output=True, timeout=1800)
    return docx_path.with_suffix(".pdf")


def measure(pdf, rp, tmp):
    txt = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True).stdout
    pages = [norm(p) for p in txt.split("\f")]
    found = {}
    # Bỏ qua các trang danh mục khi dò (chúng chứa chính các chuỗi cần tìm)
    toc_end = 0
    for i, p in enumerate(pages):
        if "chương 1. giới thiệu nghiên cứu" in p and "......" not in p and i > 3:
            toc_end = i
            break

    def find(text, start):
        key = norm(text)[:70]
        for i in range(start, len(pages)):
            if key in pages[i]:
                return i
        return None

    cursor = 0
    # Tiêu đề phần mở đầu: trang bắt đầu bằng đúng tiêu đề (tránh khớp nhầm dòng trong mục lục)
    for t in FRONT_TOC:
        key = norm(t)
        for i in range(cursor, len(pages)):
            if pages[i].startswith(key):
                found[f"toc|{t}"] = i + 1
                cursor = i
                break
    cursor = toc_end
    for lvl, t in tmp.heads:
        i = find(t, cursor)
        if i is not None:
            found[f"toc|{t}"] = i + 1
            cursor = i
    cursor = toc_end
    for a, b in tmp.figs:
        i = find(f"{a}. {b}", cursor)
        if i is not None:
            found[f"fig|{a}. {b}"] = i + 1
            cursor = i
    cursor = toc_end
    for a, b in tmp.tabs:
        i = find(f"{a}. {b}", cursor)
        if i is not None:
            found[f"tab|{a}. {b}"] = i + 1
            cursor = i
    return found, len(pages) - (1 if pages and not pages[-1] else 0)


if __name__ == "__main__":
    work = OUT_DIR / "_build"
    work.mkdir(exist_ok=True)
    pages = {}
    for it in range(3):
        rp, tmp = build(pages)
        d = work / f"{NAME}.docx"
        rp.save(d)
        pdf = to_pdf(d)
        new, npages = measure(pdf, rp, tmp)
        missing = (len(tmp.heads) + len(FRONT_TOC) + len(tmp.figs) + len(tmp.tabs)) - len(new)
        print(f"lượt {it + 1}: {npages} trang, dò được {len(new)} mục, thiếu {missing}", flush=True)
        if new == pages:
            break
        pages = new
    shutil.copy(d, OUT_DIR / f"{NAME}.docx")
    shutil.copy(pdf, OUT_DIR / f"{NAME}.pdf")
    print("Đã ghi", OUT_DIR / f"{NAME}.docx", "và .pdf;", npages, "trang;",
          len(tmp.figs), "hình;", len(tmp.tabs), "bảng")
