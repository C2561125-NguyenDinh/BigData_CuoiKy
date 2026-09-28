"""Nạp mọi bảng kết quả (outputs/tables/*.csv) và nhật ký (outputs/logs/*.json).

Mọi con số xuất hiện trong báo cáo được lấy qua các hàm ở đây, không gõ tay.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd


class Results:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.tab_dir = self.root / "outputs" / "tables"
        self.fig_dir = self.root / "outputs" / "figures"
        self.log_dir = self.root / "outputs" / "logs"
        self.T = {p.stem: pd.read_csv(p) for p in sorted(self.tab_dir.glob("*.csv"))}
        self.J = {p.stem: json.loads(p.read_text()) for p in sorted(self.log_dir.glob("*.json"))}
        # Nhật ký của các bước 15–17 nằm trong thư mục con (spark/, governance/, business/)
        self.JS = {f"{p.parent.name}/{p.stem}": json.loads(p.read_text())
                   for sub in ("spark", "governance", "business") for p in sorted((self.log_dir / sub).glob("*.json"))}

    def text(self, rel):
        """Đọc tệp văn bản trong outputs/logs (ví dụ kế hoạch thực thi của Spark)."""
        return (self.log_dir / rel).read_text(encoding="utf-8")

    def t(self, key):
        """Bảng theo tiền tố tên tệp, ví dụ t('t30')."""
        for k, v in self.T.items():
            if k == key or k.startswith(key + "_"):
                return v
        raise KeyError(key)

    def fig(self, key):
        for p in sorted(self.fig_dir.glob("*.png")):
            if p.stem == key or p.stem.startswith(key + "_"):
                return p
        raise KeyError(key)

    # ---------------- các truy xuất thường dùng
    def did(self, service, outcome, spec="TWFE", sample="vùng×tuần"):
        d = self.t("t30")
        r = d[(d.service == service) & (d.outcome == outcome) & (d.spec == spec) & (d["sample"] == sample)]
        return r.iloc[0]

    def od(self, flow, outcome):
        d = self.t("t35")
        return d[(d.flow == flow) & (d.outcome == outcome)].iloc[0]

    def rob(self, spec_prefix):
        d = self.t("t51")
        return d[d.spec.str.startswith(spec_prefix)].iloc[0]

    def desc(self, grp, yr, col, service="hvfhv"):
        d = self.t("t26") if service == "hvfhv" else self.t("t27")
        return float(d[(d.grp == grp) & (d.yr == yr)][col].iloc[0])

    def dml(self, outcome, xset="rút gọn"):
        d = self.t("t41b")
        return d[(d.outcome == outcome) & (d.x_set == xset)].iloc[0]

    def dml_main(self, outcome):
        d = self.t("t41")
        return d[d.outcome == outcome].iloc[0]

    def placebo(self, outcome, od=False):
        d = self.t("t49b") if od else self.t("t49")
        return d[d.outcome == outcome].iloc[0]

    def spill(self, side, outcome, band):
        d = self.t("t48")
        return d[(d.side == side) & (d.outcome == outcome) & (d.band == band)].iloc[0]

    def hour(self, hbin, outcome):
        d = self.t("t33")
        return d[(d.hbin == hbin) & (d.outcome == outcome)].iloc[0]


def pct_log(b):
    return 100 * (np.exp(b) - 1)
