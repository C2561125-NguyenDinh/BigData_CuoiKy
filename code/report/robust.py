"""Mục 4.14.6: suy luận bền vững (bước 20) - sai số không gian, wild bootstrap, kiểm định bội,
độ nhạy với dạng xu hướng, Rambachan–Roth có bootstrap và DML theo ngưỡng cắt."""
import pandas as pd

from lib import vn, vint
from results import pct_log


def _rng(s, y, scale=1.0):
    v = s[s.outcome == y].set_index("spec").effect * scale
    return v


def summary(R):
    """Các con số dùng chung cho tóm tắt, Chương 8 và 9."""
    t = R.t("t93")
    out = {}
    for y in ("ln_n", "mph", "wait"):
        s = t[t.outcome == y].set_index("spec")
        sig = s[(s.ci_low_wild > 0) | (s.ci_high_wild < 0)]
        out[y] = dict(s=s, n_spec=len(s), n_neg=int((s.ci_high_wild < 0).sum()), n_pos=int((s.ci_low_wild > 0).sum()),
                      n_null=int(len(s) - len(sig)))
    return out


def section(rp, R):
    A = R.t("t92").set_index("outcome")
    MT = R.t("t92b")
    T = R.t("t93")
    BR = R.t("t94b")
    CT = R.t("t94_rr")
    DM = R.t("t95")
    rp.H3("4.14.6. Suy luận bền vững: sai số không gian, bootstrap, kiểm định bội và dạng xu hướng")
    rp.PS(
        "Các mục trước dùng sai số chuẩn phân cụm theo vùng với 237 cụm và kiểm định từng chỉ tiêu riêng lẻ. Cách làm này có ba điểm "
        "yếu. Các vùng nằm cạnh nhau có thể chịu cùng cú sốc trong cùng tuần, nên tương quan không gian không được tính vào sai số. Số "
        "vùng chịu phí chỉ là 37, nên phân phối tiệm cận của thống kê t có thể kém chính xác. Và khi kiểm định hàng chục chỉ tiêu và "
        "đặc tả, một số kết quả có ý nghĩa thống kê chỉ do ngẫu nhiên. Bước 20 của pipeline kiểm tra lại các kết quả chính theo cả ba "
        "hướng, đồng thời đo xem kết luận về xu hướng ở mục 4.14.4 phụ thuộc thế nào vào cách chọn năm gốc và dạng xu hướng.")
    rows = []
    for y in A.index:
        r = A.loc[y]
        rows.append((r.label, vn(r.coef, 3), vn(r.se_cr1, 4), vn(r.se_twoway, 4), vn(r.se_conley10, 4),
                     vn(r.p_wild, 4), vn(r.holm_wild, 4), vn(r.romano_wolf, 4)))
    rp.TAB(pd.DataFrame(rows, columns=["Chỉ tiêu (TWFE, HVFHV)", "Hệ số", "SE vùng", "SE hai chiều", "SE Conley 10 km",
                                       "p wild", "p Holm", "p Romano–Wolf"]),
           "Tác động chính với các cách tính sai số và hiệu chỉnh kiểm định bội", widths=[4.4, 1.5, 1.5, 1.6, 1.7, 1.6, 1.6, 2.1],
           size=9, align=["left"] + ["center"] * 7, source="Nguồn: t92_inference_main.csv.")
    w = A.loc["wait"]
    m = A.loc["mph"]
    n = A.loc["ln_n"]
    pp = A.loc["pay_pm"]
    rp.PS(
        f"Sai số Conley (1999) cộng thêm tương quan giữa các vùng trong bán kính cho trước (nhân Bartlett) vào tương quan theo thời gian trong "
        f"từng vùng. Với bán kính 10 km, sai số của log số chuyến tăng từ {vn(n.se_cr1, 4)} lên {vn(n.se_conley10, 4)}, tức khoảng "
        f"{vn(n.se_conley10 / n.se_cr1, 1)} lần; sai số phân cụm hai chiều theo vùng và tuần (Cameron, Gelbach và Miller, 2011) cũng tăng khoảng "
        f"{vn(n.se_twoway / n.se_cr1, 1)} lần. Tương quan không gian vì vậy là có thật và sai số trong các bảng trước đánh giá thấp độ "
        f"bất định. Tuy vậy, với log số chuyến, tốc độ và thời gian chờ, hệ số vẫn lớn hơn nhiều lần sai số đã hiệu chỉnh. Chỉ tiêu "
        f"đổi kết luận là thu nhập tài xế mỗi dặm: hệ số {vn(pp.coef, 3)} có p = {vn(pp.p_twoway, 2)} với sai số hai chiều và "
        f"p = {vn(pp.p_conley10, 2)} với sai số Conley, nên không còn ý nghĩa thống kê.",
        f"Wild cluster bootstrap theo vùng (Cameron, Gelbach và Miller, 2008; {vint(9999)} lần, trọng số sáu điểm của Webb, 2023, giả thuyết không được áp đặt khi tính p) không "
        f"dựa vào phân phối tiệm cận. Cả tám chỉ tiêu đều có p bootstrap ở mức sàn 0,0001, và khoảng tin cậy bootstrap-t gần với "
        f"khoảng tin cậy thông thường. Hiệu chỉnh Holm (1979) và Romano–Wolf (2005) cho họ tám chỉ tiêu không làm chỉ tiêu nào mất ý nghĩa. Với "
        f"toàn bộ {len(MT)} hệ số của bảng DiD chính (mọi chỉ tiêu, mọi đặc tả, hai dịch vụ), {int((MT.p < 0.05).sum())} hệ số có "
        f"p < 0,05; sau hiệu chỉnh Holm còn {int((MT.p_holm < 0.05).sum())} và sau hiệu chỉnh Benjamini–Hochberg (1995) còn "
        f"{int((MT.q_bh < 0.05).sum())}. Kiểm định bội vì vậy không phải là vấn đề chính của đồ án: các hệ số lớn có ý nghĩa rất mạnh. "
        f"Vấn đề chính là các hệ số đó có phản ánh tác động của phí hay xu hướng có sẵn, điều mà sai số chuẩn không trả lời được.")
    # --- dạng xu hướng
    labs = T.drop_duplicates("spec").set_index("spec").spec_label
    rows = []
    for sk in labs.index:
        s = T[T.spec == sk].set_index("outcome")

        def cell(y, sc=1.0, d=2):
            r = s.loc[y]
            return f"{vn(r.effect * sc, d, sign=True)} [{vn(r.ci_low_wild * sc, d)}; {vn(r.ci_high_wild * sc, d)}]"
        rows.append((f"{sk}. {labs[sk]}", cell("ln_n", 100, 1), cell("mph"), cell("wait")))
    rp.TAB(pd.DataFrame(rows, columns=["Đặc tả", "Log số chuyến ×100", "Tốc độ (dặm/giờ)", "Thời gian chờ (phút)"]),
           "Tác động năm 2025 trên panel 2022–2025 theo năm gốc và dạng xu hướng (KTC 95% wild bootstrap)",
           widths=[6.4, 3.3, 3.1, 3.2], size=9, align=["left", "center", "center", "center"],
           source="Nguồn: t93_trend_spec_sensitivity.csv.")
    rp.FIG(R.fig("f59"), "Tác động năm 2025 theo sáu đặc tả xu hướng, khoảng tin cậy wild bootstrap")
    S = {y: T[T.outcome == y].set_index("spec") for y in ("ln_n", "mph", "wait")}
    ln, sp, wt = S["ln_n"], S["mph"], S["wait"]
    rp.PS(
        f"Sáu đặc tả trả lời câu hỏi: kết luận ở mục 4.14.4 có phụ thuộc vào năm gốc 2022, vốn còn chịu đợt dịch Omicron, hay vào giả "
        f"định xu hướng tuyến tính không. S1 là đặc tả của mục 4.14.4. S2 bỏ tháng Một và tháng Hai của mọi năm, loại các tháng chịu "
        f"Omicron đầu năm 2022 khỏi cả năm gốc lẫn phần so sánh. S3 bỏ hẳn năm 2022 và dùng 2023 làm năm gốc, chỉ còn 12 tháng 2024 "
        f"để ước lượng xu hướng. S4 cho phép xu hướng bậc hai. S5 giữ năm gốc 2022 nhưng chỉ ước lượng xu hướng từ 12 tháng 2024. S6 "
        f"không điều chỉnh xu hướng, tương đương so sánh 2025 với 2024.",
        f"Thời gian chờ là kết quả ổn định nhất: giảm có ý nghĩa ở {int((wt.ci_high_wild < 0).sum())} trên {len(wt)} đặc tả, từ "
        f"{vn(-wt.effect.drop('S5').max(), 2)} đến {vn(-wt.effect.drop('S5').min(), 2)} phút; chỉ S5 cho hệ số gần 0 "
        f"({vn(wt.loc['S5'].effect, 2, sign=True)} phút). Tốc độ tăng có ý nghĩa ở {int((sp.ci_low_wild > 0).sum())} đặc tả "
        f"({vn(sp.loc['S2'].effect, 2)} đến {vn(sp.loc['S6'].effect, 2)} dặm/giờ), không khác 0 khi cho phép xu hướng bậc hai "
        f"({vn(sp.loc['S4'].effect, 2, sign=True)}) và đổi dấu ở S5 ({vn(sp.loc['S5'].effect, 2, sign=True)}). Số chuyến nhạy nhất: "
        f"ước lượng đi từ {vn(100 * ln.effect.max(), 1, sign=True)}% ({ln.effect.idxmax()}) đến {vn(100 * ln.effect.min(), 1, sign=True)}% ({ln.effect.idxmin()}), "
        f"với S1 gần 0, S2 {vn(100 * ln.loc['S2'].effect, 1, sign=True)}% và S4 {vn(100 * ln.loc['S4'].effect, 1, sign=True)}%.",
        f"S5 là đặc tả kém tin cậy nhất: một xu hướng ước lượng từ 12 tháng được ngoại suy thêm 12 tháng, nên sai số nhỏ của độ dốc "
        f"cũng đủ làm ước lượng đổi dấu; sai số chuẩn của S5 lớn gấp khoảng {vn(ln.loc['S5'].se_wild / ln.loc['S1'].se_wild, 1)} lần S1 "
        f"với số chuyến. Bỏ S5 ra, thời gian chờ giảm ở mọi đặc tả và tốc độ tăng ở bốn trên năm. Số chuyến thì không có kết luận ổn "
        f"định ngay cả khi bỏ S5: ước lượng nằm từ khoảng 0 (S1) đến {vn(100 * ln.loc['S3'].effect, 1, sign=True)}% (S3) và "
        f"{vn(100 * ln.loc['S6'].effect, 1, sign=True)}% khi không điều chỉnh xu hướng (S6), tùy việc xu hướng giảm tương đối của CRZ "
        f"trước chính sách được giả định là kéo dài hay không. Dữ liệu TLC không đủ để chọn giữa các giả định này.")
    # --- Rambachan–Roth có bootstrap
    rows = []
    lab = {"ln_n": "Log số chuyến", "mph": "Tốc độ (dặm/giờ)", "wait": "Thời gian chờ (phút)"}
    for _, r in BR.iterrows():
        rows.append((f"{lab[r.outcome]}, {r.spec}", vn(r.theta_rm, 3), vn(r.max_pre_delta, 3), vn(r.breakdown_RM, 3),
                     vn(r.theta_sd, 3), vn(r.breakdown_SD_rel_se, 1)))
    rp.TAB(pd.DataFrame(rows, columns=["Chỉ tiêu, đặc tả", "Tác động (RM)", "max |Δβ| trước", "M̄ phá vỡ", "Tác động (SD)",
                                       "Độ chệch phá vỡ (SD), × SE"]),
           "Giá trị phá vỡ Rambachan–Roth với khoảng tin cậy bootstrap cho tập nhận dạng", widths=[4.4, 2.1, 2.2, 1.9, 2.1, 3.3],
           size=9, align=["left"] + ["center"] * 5, source="Nguồn: t94_rr_bootstrap.csv, t94b_rr_breakdown.csv.")
    rp.FIG(R.fig("f60"), "Khoảng tin cậy bootstrap của tác động theo M̄ (lớp độ lớn tương đối), đặc tả S1 và S2")
    b = BR.set_index(["spec", "outcome"])
    rp.PS(
        "Mục 4.14.5 cộng độ chệch lớn nhất vào hai đầu khoảng tin cậy và coi biến động lớn nhất trước chính sách là hằng số. Ở đây "
        "biến động đó được ước lượng lại trong mỗi lần wild bootstrap cùng với hệ số, và khoảng tin cậy lấy phân vị 2,5% của cận dưới "
        "và 97,5% của cận trên của tập nhận dạng (theo tinh thần Imbens và Manski, 2004). Cách làm này vẫn bảo thủ hơn khoảng tin cậy "
        "có điều kiện của Rambachan và Roth (2023), nhưng không còn bỏ qua sai số của chính đại lượng dùng để chuẩn hóa.",
        f"Khi bỏ tháng Một và tháng Hai (S2), biến động lớn nhất trước chính sách của log số chuyến giảm từ "
        f"{vn(b.loc[('S1', 'ln_n')].max_pre_delta, 3)} xuống {vn(b.loc[('S2', 'ln_n')].max_pre_delta, 3)}, cho thấy phần lớn nhiễu đến từ "
        f"các tháng đầu năm. Giá trị phá vỡ RM của thời gian chờ tăng lên {vn(b.loc[('S2', 'wait')].breakdown_RM, 3)} và của số chuyến lên "
        f"{vn(b.loc[('S2', 'ln_n')].breakdown_RM, 3)}, còn của tốc độ vẫn rất nhỏ ({vn(b.loc[('S2', 'mph')].breakdown_RM, 3)}). Không chỉ tiêu "
        f"nào đạt mốc M̄ = 1. Theo lớp SD, tác động lên thời gian chờ chỉ mất ý nghĩa khi độ chệch tích lũy do độ cong của xu hướng "
        f"vượt khoảng {vn(b.loc[('S1', 'wait')].breakdown_SD_rel_se, 0)}–{vn(b.loc[('S2', 'wait')].breakdown_SD_rel_se, 0)} lần sai số chuẩn; "
        f"với tốc độ là khoảng {vn(b.loc[('S2', 'mph')].breakdown_SD_rel_se, 1)}–{vn(b.loc[('S1', 'mph')].breakdown_SD_rel_se, 1)} lần, "
        f"và với số chuyến là 0 (S1) đến {vn(b.loc[('S2', 'ln_n')].breakdown_SD_rel_se, 1)} lần (S2).")
    # --- DML
    rows = []
    ylab = {"dlog_n": "Δ log số chuyến", "d_mph": "Δ tốc độ", "d_pay_pm": "Δ thu nhập tài xế/dặm"}
    for _, r in DM.iterrows():
        rows.append((ylab[r.outcome], r.estimator + (f", ngưỡng {r.trim}" if r.trim != "không cắt" else ""), vint(r.n_used),
                     vn(r.estimate, 4), vn(r.se_iid, 4), vn(r.se_cluster_pu, 4)))
    rp.TAB(pd.DataFrame(rows, columns=["Kết quả", "Ước lượng", "Số cặp OD", "Tác động", "SE độc lập", "SE cụm vùng đón"]),
           "DML: độ nhạy theo ngưỡng cắt xu hướng, ước lượng trọng số chồng lấn và sai số phân cụm", widths=[3.2, 5.6, 1.8, 1.8, 1.8, 2.2],
           size=9, align=["left", "left", "center", "center", "center", "center"], source="Nguồn: t95_dml_trimming.csv.")
    dn = DM[DM.outcome == "dlog_n"]
    dsp = DM[DM.outcome == "d_mph"]
    ato = dn[dn.estimator.str.startswith("ATO")].iloc[0]
    rp.PS(
        f"Ở mục 4.11, ước lượng AIPW chỉ dùng các cặp OD có xu hướng trong [0,05; 0,95]. Khi đổi ngưỡng từ 0,01 đến 0,10 hoặc dùng "
        f"ngưỡng tối ưu của Crump, Hotz, Imbens và Mitnik (2009), mức giảm số chuyến nằm trong khoảng "
        f"{vn(-100 * dn.estimate.max(), 1)}–{vn(-100 * dn.estimate.min(), 1)} điểm log, và tốc độ tăng "
        f"{vn(dsp.estimate.min(), 2)}–{vn(dsp.estimate.max(), 2)} dặm/giờ. Ước lượng trọng số chồng lấn (ATO) của Li, Morgan và "
        f"Zaslavsky (2018) dùng toàn bộ {vint(ato.n_used)} cặp, không cắt bỏ cặp nào mà giảm trọng số các cặp gần như chắc chắn chạm "
        f"hoặc không chạm CRZ, cho {vn(-100 * ato.estimate, 1)} điểm log. Kết quả DML vì vậy không phụ thuộc vào ngưỡng cắt. Điểm cần "
        f"sửa là sai số: các cặp OD có chung vùng đón không độc lập, và sai số phân cụm theo vùng đón lớn hơn sai số giả định độc lập "
        f"khoảng {vn((dn.se_cluster_pu / dn.se_iid).mean(), 1)} lần. Kết luận không đổi vì hệ số vẫn lớn hơn nhiều lần sai số đã hiệu "
        f"chỉnh. Cần lưu ý rằng DML ở đây cũng so sánh 2025 với 2024, nên chịu cùng vấn đề xu hướng có sẵn như các thiết kế một năm.")
    rp.P("Các cách tính sai số chặt hơn và hiệu chỉnh kiểm định bội không làm thay đổi kết luận nào ngoài thu nhập tài xế "
         "mỗi dặm. Điều quyết định độ tin cậy của từng kết luận là giả định về xu hướng. Theo thứ tự từ chắc chắn nhất: thời gian chờ "
         "giảm ở mọi đặc tả trừ S5; tốc độ tăng ở phần lớn đặc tả nhưng độ lớn phụ thuộc giả định; số chuyến có thể giảm từ 0 đến khoảng "
         "10% và dữ liệu hiện có không xác định được con số cụ thể.")
