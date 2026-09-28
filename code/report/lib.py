"""Thư viện dựng báo cáo Word (python-docx) theo định dạng luận văn.

A4, lề trái 3 cm, phải 2 cm, trên/dưới 2 cm; Times New Roman 13, giãn dòng 1,5,
thụt đầu dòng 1 cm, căn đều hai bên. Hình đánh số theo chương (Hình 3.1),
chú thích dưới hình; bảng đánh số theo chương (Bảng 3.1), tiêu đề trên bảng.
Mục lục, danh mục hình và danh mục bảng được dựng hai lượt: lượt 1 xuất PDF
để đo số trang thực tế, lượt 2 điền số trang vào các danh mục.
"""
import math
import re

import numpy as np
import pandas as pd
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

FONT = "Times New Roman"


# ---------------------------------------------------------------- định dạng số
def vn(x, d=1, pct=False, sign=False):
    """Định dạng số kiểu Việt Nam: dấu phẩy thập phân, dấu chấm phân tách nghìn."""
    if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))):
        return "–"
    s = f"{x:+,.{d}f}" if sign else f"{x:,.{d}f}"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return s + ("%" if pct else "")


def vint(x):
    return vn(float(x), 0)


def pval(p):
    if p is None or (isinstance(p, float) and math.isnan(p)):
        return "–"
    if p < 0.001:
        return "< 0,001"
    return vn(p, 3)


def stars(p):
    return "***" if p < 0.01 else ("**" if p < 0.05 else ("*" if p < 0.1 else ""))


# ---------------------------------------------------------------- tài liệu
class Report:
    def __init__(self, pages=None):
        self.doc = Document()
        self.pages = pages or {}          # key -> số trang (từ lượt đo)
        self.chapter = 0
        self.prefix = None
        self.quiet = False   # True: không đưa H3 và bảng vào mục lục / danh mục bảng
        self.fig_no = 0
        self.tab_no = 0
        self.eq_no = 0
        self.figs, self.tabs, self.heads = [], [], []
        self._setup()

    # -------- cấu hình trang và kiểu
    def _setup(self):
        sec = self.doc.sections[0]
        sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
        sec.left_margin, sec.right_margin = Cm(3.0), Cm(2.0)
        sec.top_margin, sec.bottom_margin = Cm(2.0), Cm(2.0)
        sec.footer_distance = Cm(1.0)
        st = self.doc.styles
        n = st["Normal"]
        n.font.name, n.font.size = FONT, Pt(13)
        n.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
        pf = n.paragraph_format
        pf.line_spacing, pf.space_after, pf.space_before = 1.5, Pt(6), Pt(0)
        pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        pf.first_line_indent = Cm(1.0)
        for lvl, size, align in ((1, 16, WD_ALIGN_PARAGRAPH.CENTER), (2, 14, WD_ALIGN_PARAGRAPH.LEFT),
                                 (3, 13, WD_ALIGN_PARAGRAPH.LEFT)):
            h = st[f"Heading {lvl}"]
            h.font.name, h.font.size, h.font.bold = FONT, Pt(size), True
            h.font.italic = lvl == 3 and False
            h.font.color.rgb = RGBColor(0, 0, 0)
            rpr = h.element.get_or_add_rPr()
            rf = rpr.find(qn("w:rFonts"))
            if rf is None:
                rf = OxmlElement("w:rFonts")
                rpr.append(rf)
            for a in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
                rf.set(qn(a), FONT)
            for a in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
                if rf.get(qn(a)) is not None:
                    del rf.attrib[qn(a)]
            hp = h.paragraph_format
            hp.space_before, hp.space_after = Pt(10), Pt(8)
            hp.alignment, hp.first_line_indent = align, Cm(0)
            hp.line_spacing = 1.3
            hp.keep_with_next = True
        self._footer_page_number(sec)

    def _footer_page_number(self, sec):
        p = sec.footer.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.first_line_indent = Cm(0)
        r = p.add_run()
        for tag, txt in (("begin", None), (None, "PAGE"), ("end", None)):
            if tag:
                el = OxmlElement("w:fldChar")
                el.set(qn("w:fldCharType"), tag)
                r._r.append(el)
            else:
                it = OxmlElement("w:instrText")
                it.set(qn("xml:space"), "preserve")
                it.text = txt
                r._r.append(it)
        r.font.size = Pt(12)

    # -------- tiện ích đoạn
    def _runs(self, p, text, size=None, italic=False, bold=False):
        """Hỗ trợ **đậm** và _nghiêng_ đơn giản trong chuỗi."""
        parts = re.split(r"(\*\*[^*]+\*\*|__[^_]+__)", text)
        for part in parts:
            if not part:
                continue
            b, i, t = bold, italic, part
            if part.startswith("**") and part.endswith("**"):
                b, t = True, part[2:-2]
            elif part.startswith("__") and part.endswith("__"):
                i, t = True, part[2:-2]
            r = p.add_run(t)
            r.bold, r.italic = b, i
            if size:
                r.font.size = Pt(size)
        return p

    def P(self, text, indent=True, align=None, size=None, italic=False, bold=False, space_after=None, keep=False):
        p = self.doc.add_paragraph()
        if not indent:
            p.paragraph_format.first_line_indent = Cm(0)
        if align == "center":
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        elif align == "left":
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        elif align == "right":
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        if space_after is not None:
            p.paragraph_format.space_after = Pt(space_after)
        if keep:
            p.paragraph_format.keep_with_next = True
        self._runs(p, text, size, italic, bold)
        return p

    def PS(self, *texts):
        for t in texts:
            self.P(t)

    def BUL(self, items, numbered=False):
        for k, it in enumerate(items, 1):
            p = self.doc.add_paragraph()
            pf = p.paragraph_format
            pf.left_indent, pf.first_line_indent = Cm(1.0), Cm(-0.5)
            lab = f"{k}) " if numbered else "– "
            self._runs(p, lab + it)

    def pagebreak(self):
        p = self.doc.add_paragraph()
        p.paragraph_format.first_line_indent = Cm(0)
        p.add_run().add_break(WD_BREAK.PAGE)

    # -------- tiêu đề
    def H1(self, text, numbered=True, toc=True, newpage=True, size=None):
        if newpage and len(self.doc.paragraphs) > 0 and not getattr(self, "_fresh", False):
            self.pagebreak()
        self._fresh = False
        if numbered:
            self.chapter += 1
            self.fig_no = self.tab_no = self.eq_no = 0
        h = self.doc.add_heading(text, level=1)
        if size:
            for r in h.runs:
                r.font.size = Pt(size)
        if toc:
            self.heads.append((1, text))
        return h

    # -------- trang bìa theo mẫu UEL: ảnh nền toàn trang, khung chữ định vị tuyệt đối
    def background(self, path):
        """Chèn ảnh nền phủ toàn trang, nằm sau chữ, neo vào đoạn hiện tại."""
        p = self.doc.add_paragraph()
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.space_after = Pt(0)
        run = p.add_run()
        sec = self.doc.sections[-1]
        run.add_picture(str(path), width=sec.page_width, height=sec.page_height)
        inline = run._r.find(".//" + qn("wp:inline"))
        graphic = inline.find(qn("a:graphic"))
        cx, cy = inline.find(qn("wp:extent")).get("cx"), inline.find(qn("wp:extent")).get("cy")
        from lxml import etree
        ns = ('xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
              'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"')
        xml = (f'<wp:anchor {ns} distT="0" distB="0" distL="0" distR="0" simplePos="0" relativeHeight="0" '
               f'behindDoc="1" locked="1" layoutInCell="1" allowOverlap="1"><wp:simplePos x="0" y="0"/>'
               f'<wp:positionH relativeFrom="page"><wp:posOffset>0</wp:posOffset></wp:positionH>'
               f'<wp:positionV relativeFrom="page"><wp:posOffset>0</wp:posOffset></wp:positionV>'
               f'<wp:extent cx="{cx}" cy="{cy}"/><wp:effectExtent l="0" t="0" r="0" b="0"/><wp:wrapNone/>'
               f'<wp:docPr id="9001" name="Cover background"/><wp:cNvGraphicFramePr/></wp:anchor>')
        anchor = etree.fromstring(xml)
        anchor.append(graphic)
        inline.getparent().replace(inline, anchor)
        return p

    def FRAME(self, text, x_cm, y_cm, w_cm, size=11, bold=False, color=None, align="center"):
        """Đoạn văn trong khung định vị tuyệt đối theo trang (dùng cho dòng ngày tháng trên dải màu bìa)."""
        p = self.doc.add_paragraph()
        pf = p.paragraph_format
        pf.first_line_indent, pf.space_after, pf.line_spacing = Cm(0), Pt(0), 1.0
        p.alignment = {"center": WD_ALIGN_PARAGRAPH.CENTER, "left": WD_ALIGN_PARAGRAPH.LEFT}[align]
        fr = OxmlElement("w:framePr")
        tw = lambda c: str(int(round(c / 2.54 * 1440)))
        for k, v in (("w:w", tw(w_cm)), ("w:hSpace", "0"), ("w:wrap", "around"), ("w:vAnchor", "page"),
                     ("w:hAnchor", "page"), ("w:x", tw(x_cm)), ("w:y", tw(y_cm))):
            fr.set(qn(k), v)
        p._p.get_or_add_pPr().insert(0, fr)
        r = p.add_run(text)
        r.font.size, r.bold = Pt(size), bold
        if color:
            r.font.color.rgb = RGBColor.from_string(color)
        return p

    def appendix(self, letter, title):
        """Mở một phụ lục mới: đánh số hình, bảng theo chữ cái (A.1, B.1...)."""
        self.prefix = letter
        self.quiet = False
        self.fig_no = self.tab_no = self.eq_no = 0
        return self.H1(title, numbered=False)

    def H2(self, text):
        self.heads.append((2, text))
        return self.doc.add_heading(text, level=2)

    def H3(self, text):
        if not self.quiet:
            self.heads.append((3, text))
        return self.doc.add_heading(text, level=3)

    # -------- hình
    def FIG(self, path, caption, width_cm=15.5, source="Nguồn: kết quả tính toán của tác giả từ dữ liệu NYC TLC."):
        self.fig_no += 1
        lab = f"Hình {self.prefix or self.chapter}.{self.fig_no}"
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.keep_with_next = True
        p.paragraph_format.space_after = Pt(2)
        p.add_run().add_picture(str(path), width=Cm(width_cm))
        c = self.doc.add_paragraph()
        c.alignment = WD_ALIGN_PARAGRAPH.CENTER
        c.paragraph_format.first_line_indent = Cm(0)
        c.paragraph_format.line_spacing = 1.15
        c.paragraph_format.space_after = Pt(2)
        c.paragraph_format.keep_with_next = bool(source)
        r = c.add_run(lab + ". ")
        r.bold, r.font.size = True, Pt(12)
        r2 = c.add_run(caption)
        r2.font.size = Pt(12)
        if source:
            s = self.doc.add_paragraph()
            s.alignment = WD_ALIGN_PARAGRAPH.CENTER
            s.paragraph_format.first_line_indent = Cm(0)
            s.paragraph_format.space_after = Pt(10)
            s.paragraph_format.line_spacing = 1.0
            rr = s.add_run(source)
            rr.italic, rr.font.size = True, Pt(10.5)
        self.figs.append((lab, caption))
        return lab

    # -------- phương trình
    def EQ(self, text):
        self.eq_no += 1
        lab = f"({self.chapter}.{self.eq_no})"
        p = self.doc.add_paragraph()
        p.paragraph_format.first_line_indent = Cm(0)
        ts = p.paragraph_format.tab_stops
        ts.add_tab_stop(Cm(8.0), WD_TAB_ALIGNMENT.CENTER)
        ts.add_tab_stop(Cm(16.0), WD_TAB_ALIGNMENT.RIGHT)
        r = p.add_run("\t" + text)
        r.italic = True
        p.add_run("\t" + lab)
        return lab

    # -------- bảng
    def TAB(self, df, caption, widths=None, size=10.5, align=None, source="Nguồn: kết quả tính toán của tác giả.",
            header_bold=True, first_col_left=True, autofit=False):
        if caption is not None:
            self.tab_no += 1
        lab = f"Bảng {self.prefix or self.chapter}.{self.tab_no}"
        c = self.doc.add_paragraph() if caption is not None else None
        if c is None:
            return self._table_body(df, widths, size, align, source, header_bold, first_col_left, None)
        return self._caption_and_table(c, lab, caption, df, widths, size, align, source, header_bold, first_col_left)

    def _caption_and_table(self, c, lab, caption, df, widths, size, align, source, header_bold, first_col_left):
        c.alignment = WD_ALIGN_PARAGRAPH.CENTER
        c.paragraph_format.first_line_indent = Cm(0)
        c.paragraph_format.keep_with_next = True
        c.paragraph_format.line_spacing = 1.15
        c.paragraph_format.space_before = Pt(6)
        r = c.add_run(lab + ". ")
        r.bold, r.font.size = True, Pt(12)
        r2 = c.add_run(caption)
        r2.font.size = Pt(12)
        self._table_body(df, widths, size, align, source, header_bold, first_col_left, (lab, caption))
        return lab

    def _table_body(self, df, widths, size, align, source, header_bold, first_col_left, reg):
        cols = list(df.columns)
        t = self.doc.add_table(rows=1, cols=len(cols))
        t.style = "Table Grid"
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        total = 16.0
        if widths is None:
            widths = [total / len(cols)] * len(cols)
        else:
            s = sum(widths)
            widths = [w * total / s for w in widths]
        hdr = t.rows[0]
        self._repeat_header(hdr)
        for j, name in enumerate(cols):
            self._cell(hdr.cells[j], str(name), size, header_bold, "center", shade="E8E6E1")
        for _, row in df.iterrows():
            cells = t.add_row().cells
            for j, v in enumerate(row):
                al = "left" if (j == 0 and first_col_left) else (align[j] if align else "center")
                self._cell(cells[j], "" if v is None else str(v), size, False, al)
        if len(df) <= 16:
            # Bảng ngắn: giữ trọn trên một trang
            for row in t.rows[:-1]:
                for cell in row.cells:
                    for p in cell.paragraphs:
                        p.paragraph_format.keep_with_next = True
        for row in t.rows:
            trPr = row._tr.get_or_add_trPr()
            cs = OxmlElement("w:cantSplit")
            trPr.append(cs)
        t.autofit = False
        tblPr = t._tbl.tblPr
        lay = OxmlElement("w:tblLayout")
        lay.set(qn("w:type"), "fixed")
        tblPr.append(lay)
        for j, gc in enumerate(t._tbl.tblGrid.findall(qn("w:gridCol"))):
            gc.set(qn("w:w"), str(int(widths[j] * 567)))
        for row in t.rows:
            for j, cell in enumerate(row.cells):
                cell.width = Cm(widths[j])
        if source:
            s = self.doc.add_paragraph()
            s.paragraph_format.first_line_indent = Cm(0)
            s.paragraph_format.space_after = Pt(10)
            s.paragraph_format.line_spacing = 1.0
            rr = s.add_run(source)
            rr.italic, rr.font.size = True, Pt(10.5)
        else:
            self.doc.add_paragraph().paragraph_format.space_after = Pt(4)
        if reg and not self.quiet:
            self.tabs.append(reg)

    def _repeat_header(self, row):
        trPr = row._tr.get_or_add_trPr()
        el = OxmlElement("w:tblHeader")
        el.set(qn("w:val"), "true")
        trPr.append(el)

    def _cell(self, cell, text, size, bold, align, shade=None):
        cell.text = ""
        p = cell.paragraphs[0]
        pf = p.paragraph_format
        pf.first_line_indent, pf.space_after, pf.space_before = Cm(0), Pt(1), Pt(1)
        pf.line_spacing = 1.05
        p.alignment = {"left": WD_ALIGN_PARAGRAPH.LEFT, "center": WD_ALIGN_PARAGRAPH.CENTER,
                       "right": WD_ALIGN_PARAGRAPH.RIGHT}[align]
        r = p.add_run(text)
        r.font.size, r.bold = Pt(size), bold
        if shade:
            tcPr = cell._tc.get_or_add_tcPr()
            sh = OxmlElement("w:shd")
            sh.set(qn("w:val"), "clear")
            sh.set(qn("w:color"), "auto")
            sh.set(qn("w:fill"), shade)
            tcPr.append(sh)

    # -------- khối mã nguồn
    def CODE(self, text, size=8):
        for line in text.split("\n"):
            p = self.doc.add_paragraph()
            pf = p.paragraph_format
            pf.first_line_indent, pf.space_after, pf.space_before = Cm(0), Pt(0), Pt(0)
            pf.line_spacing = 1.0
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            r = p.add_run(line if line else " ")
            r.font.name = "Courier New"
            r._element.rPr.rFonts.set(qn("w:eastAsia"), "Courier New")
            r.font.size = Pt(size)

    # -------- danh mục có số trang (mục lục, hình, bảng)
    def LISTING(self, entries, kind):
        """entries: list (level, text). Số trang lấy từ self.pages theo khóa kind|text."""
        # Kiểu theo mẫu: mục cấp 1 sát lề, cấp 2 và 3 thụt dần; số mục và tên mục cách nhau bằng tab;
        # đường dẫn chấm tới số trang canh phải.
        width = 16.0
        for lvl, text in entries:
            p = self.doc.add_paragraph()
            pf = p.paragraph_format
            pg = self.pages.get(f"{kind}|{text}", "")
            if kind == "toc":
                m = re.match(r"^((?:CHƯƠNG \d+\.)|(?:\d+(?:\.\d+)*\.)|(?:PHỤ LỤC [A-Z]\.))\s+(.*)$", text)
                lead = {1: 0.0, 2: 0.6, 3: 1.2}.get(lvl, 0)
                numw = {1: 2.4 if (m and m.group(1).startswith(("CHƯƠNG", "PHỤ LỤC"))) else 1.0,
                        2: 1.2, 3: 1.6}.get(lvl, 1.0)
                pf.left_indent, pf.first_line_indent = Cm(lead + (numw if m else 0)), Cm(-(numw if m else 0))
                if m:
                    pf.tab_stops.add_tab_stop(Cm(lead + numw), WD_TAB_ALIGNMENT.LEFT)
                    body = f"{m.group(1)}\t{m.group(2)}"
                else:
                    body = text
            else:
                pf.left_indent, pf.first_line_indent = Cm(0), Cm(0)
                body = text
            pf.space_after, pf.space_before, pf.line_spacing = Pt(3), Pt(0), 1.15
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            pf.tab_stops.add_tab_stop(Cm(width), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
            r = p.add_run(body)
            r.font.size = Pt(12)
            r2 = p.add_run(f"\t{pg}")
            r2.font.size = Pt(12)

    def save(self, path):
        self.doc.save(str(path))


def fmt_df(df, spec):
    """Định dạng DataFrame theo đặc tả {cột: số chữ số thập phân | hàm}."""
    out = df.copy()
    for c, f in spec.items():
        if c not in out:
            continue
        if callable(f):
            out[c] = out[c].map(f)
        else:
            out[c] = out[c].map(lambda v, d=f: vn(v, d) if pd.notna(v) else "–")
    return out
