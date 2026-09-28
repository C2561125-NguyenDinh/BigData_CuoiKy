"""Giai đoạn trước chính sách mở rộng 2022–2024 (mục 3.2.4 và 4.14.4–4.14.5)."""
import numpy as np
import pandas as pd

from lib import pval, stars, vint, vn
from results import pct_log


def data_section(rp, R):
    """Mô tả dữ liệu mở rộng, đặt trong Chương 3."""
    m = R.t("t01x")
    s = R.t("t03x")
    q = R.t("t07x")
    part = R.t("t08x")
    n_ext = int(s.total_rows.sum())
    n_main = int(R.t("t03").total_rows.sum())
    rp.H3("3.2.4. Dữ liệu mở rộng cho giai đoạn trước chính sách 2022–2023")
    t = pd.DataFrame({"Dịch vụ": s.service.map({"hvfhv": "HVFHV", "yellow": "Taxi vàng"}), "Số tệp": s.files.map(vint),
                      "Số bản ghi": s.total_rows.map(vint), "Dung lượng (MB)": s.total_size_mb.map(lambda v: vn(v, 1))})
    rp.TAB(t, "Dữ liệu mở rộng 01/2022–12/2023 ở lớp Bronze", widths=[3.2, 2.4, 4.4, 3.6], size=10.5,
           source="Nguồn: t03x_bronze_summary_ext.csv.")
    hv = q[q.service == "hvfhv"].iloc[0]
    ye = q[q.service == "yellow"].iloc[0]
    persisted = part.silver_persisted.fillna(True).astype(bool) if "silver_persisted" in part else pd.Series([True] * len(part))
    hvp = part[(part.service == "hvfhv")]
    rate_p = (hvp[persisted.loc[hvp.index]].n_raw.sum() / hvp[persisted.loc[hvp.index]].sec_total.sum())
    rate_n = (hvp[~persisted.loc[hvp.index]].n_raw.sum() / hvp[~persisted.loc[hvp.index]].sec_total.sum())
    rp.PS(
        f"Hạn chế lớn nhất của thiết kế ban đầu là chỉ có một năm trước chính sách, khiến không tách được xu hướng dài hạn khỏi mùa "
        f"vụ và không chạy được giả dược cho đặc tả khử mùa vụ. Đồ án vì vậy bổ sung 24 tháng dữ liệu 2022–2023 của cả hai dịch vụ, "
        f"gồm {vint(n_ext)} bản ghi. Cùng với dữ liệu chính, tổng khối lượng được xử lý là {vint(n_ext + n_main)} bản ghi trong 48 "
        f"tháng. Lược đồ của các tệp 2022–2023 giống năm 2024 ngoại trừ kiểu số nguyên của cột vùng (int64 thay vì int32), được "
        f"chuẩn hóa ở bước Silver.",
        f"Dữ liệu mở rộng đi qua cùng bảy quy tắc chất lượng; tỷ lệ bị loại là {vn(hv.reject_pct, 2)}% với HVFHV và "
        f"{vn(ye.reject_pct, 2)}% với taxi vàng. Khác với giai đoạn chính, lớp Silver chỉ được ghi xuống đĩa cho "
        f"{vint(persisted.sum())} trong {vint(len(part))} phân vùng đầu tiên. Với phần còn lại, bảng chuyến đã làm sạch chỉ tồn tại "
        f"trong bộ nhớ DuckDB trong lúc tính các phân vùng Gold. Lựa chọn này tăng thông lượng xử lý HVFHV từ khoảng "
        f"{vint(rate_p)} lên {vint(rate_n)} bản ghi mỗi giây ({vn(rate_n / rate_p, 1)} lần) trên máy của đồ án, vì bước tốn kém nhất "
        f"là ghi Parquet nén qua lớp chia sẻ thư mục của máy ảo, và không làm mất khả năng tái lập vì lớp Bronze được giữ nguyên. Các bảng Gold dài (2022–2025) được "
        f"ghi riêng vào thư mục data/gold/long và không thay thế các bảng Gold chính, nên mọi kết quả của giai đoạn 2024–2025 ở các "
        f"chương khác giữ nguyên.")


def analysis_section(rp, R):
    """Kết quả với giai đoạn trước chính sách mở rộng, đặt trong mục 4.14."""
    sm = R.t("t90").set_index("outcome")
    meta = R.J["19_long_preperiod"]
    idx = R.t("t89b")
    rp.H3("4.14.4. Giai đoạn trước chính sách mở rộng: khử mùa vụ và giả dược theo năm")
    rp.PS(
        f"Với dữ liệu 2022–2025, đồ án ước lượng một nghiên cứu sự kiện theo tháng trên panel {vint(meta['zones'])} vùng × 48 tháng "
        f"({vint(meta['treated'])} vùng CRZ), có hiệu ứng cố định vùng, tháng và nhóm xử lý × tháng trong năm. Năm 2022 là năm gốc: mỗi "
        f"hệ số β_m đo chênh lệch CRZ – đối chứng của tháng m so với cùng tháng năm 2022, nên mùa vụ riêng của CRZ đã được khử. Ba "
        f"năm 2023, 2024 và 2025 cho 36 hệ số, trong đó 24 hệ số trước chính sách cho phép kiểm tra trực tiếp hai điều mà thiết kế ban "
        f"đầu không kiểm tra được: năm 2024 có khác năm 2023 không (giả dược với chính sách giả 01/2024), và xu hướng trước chính sách "
        f"có ổn định không.",
        "Bốn đại lượng được báo cáo. Giả dược là chênh lệch trung bình năm 2024 so với 2023. Tác động thô là chênh lệch 2025 so với "
        "2024, tương đương đặc tả DDD mùa vụ của mục 4.5. Tác động sau điều chỉnh xu hướng ngoại suy xu hướng tuyến tính theo tháng ước "
        "lượng từ 24 tháng 2023–2024. Gia tốc là chênh lệch của thay đổi năm 2025 so với thay đổi năm 2024, tức một sai khác bậc hai "
        "theo năm, đúng khi xu hướng tương đối thay đổi đều mỗi năm.")
    lab57 = rp.FIG(R.fig("f57"), "Hệ số nghiên cứu sự kiện khử mùa vụ theo tháng, 2023–2025 (năm gốc 2022)")
    rows = []
    for y in sm.index:
        r = sm.loc[y]
        rows.append((r.label, f"{vn(r.placebo_2024_vs_2023, 3)}{stars(r.placebo_p)}",
                     f"{vn(r.effect_2025_vs_2024, 3)}{stars(r.effect_p)}",
                     f"{vn(r.effect_trend_adj, 3)}{stars(r.effect_trend_adj_p)}", vn(r.effect_trend_adj_se, 3),
                     f"{vn(r.accel, 3)}{stars(r.accel_p)}", vn(r.accel_se, 3)))
    rp.TAB(pd.DataFrame(rows, columns=["Biến kết quả", "Giả dược 2024−2023", "Tác động thô 2025−2024",
                                       "Sau điều chỉnh xu hướng", "SE", "Gia tốc", "SE"]),
           "Giả dược theo năm, tác động thô, tác động sau điều chỉnh xu hướng và gia tốc (panel vùng × tháng 2022–2025)",
           widths=[4.4, 2.2, 2.4, 2.4, 1.3, 2.0, 1.3], size=9, align=["left"] + ["center"] * 6,
           source="Nguồn: t90_long_placebo_trend.csv. Sai số chuẩn phân cụm theo vùng; *, **, *** tương ứng p < 0,1; 0,05; 0,01.")
    n, s_, w_ = sm.loc["ln_n"], sm.loc["mph"], sm.loc["wait"]
    f_, p_ = sm.loc["fare_pm"], sm.loc["pay_pm"]
    i = idx.set_index("ym")
    ratio = lambda y: float(i.loc[f"{y}-12", "crz"] / i.loc[f"{y}-12", "control"]) if f"{y}-12" in i.index else np.nan
    rp.PS(
        f"Kết quả quan trọng nhất của mục này là về số chuyến. {lab57} và chuỗi chỉ số theo tháng cho thấy số chuyến HVFHV trong CRZ đã "
        f"giảm tương đối so với nhóm đối chứng một cách đều đặn từ năm 2023, trước khi có chính sách: độ dốc trước chính sách là "
        f"{vn(100 * n.pre_slope_per_month, 2)} điểm log mỗi tháng. Giả dược 2024 so với 2023 là {vn(pct_log(n.placebo_2024_vs_2023), 1)}%, "
        f"gần bằng tác động thô 2025 so với 2024 ({vn(pct_log(n.effect_2025_vs_2024), 1)}%). Khi ngoại suy xu hướng tuyến tính, tác động "
        f"còn {vn(pct_log(n.effect_trend_adj), 2)}% (sai số chuẩn {vn(100 * n.effect_trend_adj_se, 2)} điểm log), không khác 0. Với giả "
        f"định thay đổi hằng năm không đổi, gia tốc là {vn(pct_log(n.accel), 1)}% (p {pval(n.accel_p)}).",
        f"Nói cách khác, phần lớn mức giảm khoảng 6–10% mà các thiết kế dựa trên một năm trước chính sách tìm thấy trùng với một xu hướng "
        f"giảm tương đối đã có từ trước. Phạm vi tác động tương thích với dữ liệu ba năm là từ khoảng 0 (nếu xu hướng tháng tiếp diễn "
        f"tuyến tính) đến khoảng {vn(-pct_log(n.accel), 0)}% (nếu thay đổi năm tiếp diễn đều), và chỉ lên tới mức của thiết kế ban đầu nếu "
        f"xu hướng giảm tương đối tự dừng lại đúng vào tháng 01/2025. Không có lý do độc lập nào để tin vào khả năng cuối cùng. Đây là một "
        f"điều chỉnh lớn so với kết luận ban đầu về số chuyến và được đưa vào các chương thảo luận và kết luận.",
        f"Tốc độ và thời gian chờ cho bức tranh khác. Tốc độ cũng có xu hướng tăng tương đối trước chính sách (giả dược "
        f"{vn(s_.placebo_2024_vs_2023, 2)} dặm/giờ), nhưng tác động thô năm 2025 ({vn(s_.effect_2025_vs_2024, 2)} dặm/giờ) lớn gấp đôi, "
        f"và sau điều chỉnh xu hướng vẫn còn {vn(s_.effect_trend_adj, 2)} dặm/giờ (sai số chuẩn {vn(s_.effect_trend_adj_se, 3)}); gia "
        f"tốc là {vn(s_.accel, 2)} dặm/giờ. Thời gian chờ gần như không có xu hướng trước (giả dược {vn(w_.placebo_2024_vs_2023, 2)} phút) "
        f"và giảm {vn(-w_.effect_2025_vs_2024, 2)} phút năm 2025; sau điều chỉnh xu hướng còn {vn(-w_.effect_trend_adj, 2)} phút. Hai "
        f"biến này vì vậy vẫn cho bằng chứng về tác động của chính sách, với độ lớn nhỏ hơn ước lượng ban đầu: khoảng một phần ba đến "
        f"một nửa đối với tốc độ và khoảng hai phần ba đối với thời gian chờ.",
        f"Với giá cước và thu nhập tài xế, dữ liệu dài hơn xác nhận nhận định của mục 4.14.1: cả hai có xu hướng trước chính sách mạnh "
        f"và giả dược có ý nghĩa. Sau điều chỉnh xu hướng, giá cước cơ sở mỗi dặm tăng {vn(f_.effect_trend_adj, 3)} USD và thu nhập tài xế "
        f"mỗi dặm tăng {vn(p_.effect_trend_adj, 3)} USD, nhưng chiều của các ước lượng này thay đổi tùy cách mô hình hóa xu hướng (so "
        f"với tháng cuối trước chính sách, chúng lần lượt là {vn(f_.effect_vs_last_pre, 3)} và {vn(p_.effect_vs_last_pre, 3)}), nên đồ án "
        f"giữ kết luận không xác định.")
    rp.H3("4.14.5. Độ nhạy với vi phạm xu hướng song song (Rambachan–Roth)")
    rp.PS(
        "Rambachan và Roth (2023) đề xuất thay câu hỏi \"xu hướng song song có đúng không\" bằng câu hỏi \"xu hướng song song phải sai "
        "đến mức nào thì kết luận mới đổi\". Hai lớp giới hạn được dùng. Với lớp độ lớn tương đối (RM), biến động của độ lệch xu hướng "
        "sau chính sách giữa hai tháng liên tiếp không vượt quá M̄ lần biến động lớn nhất quan sát được trước chính sách. Với lớp độ "
        "trơn (SD), độ lệch so với xu hướng tuyến tính ngoại suy có sai phân bậc hai không vượt quá M mỗi tháng. Giá trị phá vỡ là M̄ "
        "hoặc M nhỏ nhất làm khoảng tin cậy chứa 0.",
        "Đồ án cài đặt phiên bản đơn giản hóa và bảo thủ của hai lớp này: độ chệch lớn nhất có thể được cộng trực tiếp vào hai đầu "
        "khoảng tin cậy thông thường, thay vì dùng khoảng tin cậy tối ưu có độ dài cố định của các tác giả. Khoảng thu được vì vậy "
        "rộng hơn khoảng của Rambachan và Roth, và giá trị phá vỡ là cận dưới của giá trị phá vỡ thật. Tác động theo RM được chuẩn hóa so "
        "với tháng cuối trước chính sách (12/2024) như trong bài gốc.")
    rows = []
    for y in sm.index:
        r = sm.loc[y]
        rows.append((r.label, vn(r.effect_vs_last_pre, 3), vn(r.max_pre_delta, 3), vn(r.breakdown_RM, 3),
                     vn(r.effect_trend_adj, 3), vn(r.breakdown_SD, 4)))
    rp.TAB(pd.DataFrame(rows, columns=["Biến kết quả", "Tác động (RM)", "max |Δβ| trước", "M̄ phá vỡ", "Tác động (SD)", "M phá vỡ"]),
           "Giá trị phá vỡ theo hai lớp giới hạn của Rambachan–Roth", widths=[5.0, 2.2, 2.2, 2.0, 2.4, 2.2], size=9.5,
           align=["left"] + ["center"] * 5, source="Nguồn: t90_long_placebo_trend.csv, t91_rr_relative_magnitudes.csv, t91b_rr_smoothness.csv.")
    rp.FIG(R.fig("f58"), "Khoảng tin cậy của tác động theo M̄ trong lớp độ lớn tương đối")
    robust = [sm.loc[y].label for y in sm.index if sm.loc[y].breakdown_RM >= 1]
    rp.PS(
        "Một giá trị phá vỡ M̄ ≥ 1 nghĩa là kết luận vẫn đứng vững kể cả khi độ lệch xu hướng sau chính sách biến động mạnh như tháng "
        "biến động nhất trước chính sách; đây là mốc mà Rambachan và Roth dùng để đánh giá một kết quả là vững. "
        + (f"Các biến đạt mốc này: {', '.join(robust)}. " if robust else
           f"Không biến nào đạt mốc này; giá trị phá vỡ lớn nhất là {vn(sm.breakdown_RM.max(), 3)} ({sm.loc[sm.breakdown_RM.idxmax()].label}). ")
        + f"Nguyên nhân chính là biến động tháng sang tháng của các hệ số trước chính sách rất lớn so với tác động, ví dụ với số chuyến "
          f"biến động lớn nhất là {vn(n.max_pre_delta, 3)} điểm log, chủ yếu ở các tháng Một khi mùa vụ của năm gốc 2022 (đợt dịch "
          f"đầu năm) không lặp lại. Lớp RM dùng biến động lớn nhất làm thước đo nên rất khắt khe khi có một vài tháng ngoại lệ.",
        f"Lớp SD phù hợp hơn với dữ liệu này vì nó cho phép xu hướng tuyến tính và chỉ giới hạn độ cong. Với tốc độ, tác động sau điều "
        f"chỉnh xu hướng chỉ mất ý nghĩa khi độ cong của xu hướng vượt {vn(s_.breakdown_SD, 4)} dặm/giờ mỗi tháng²; với thời gian chờ là "
        f"{vn(w_.breakdown_SD, 4)} phút mỗi tháng². Với số chuyến, tác động sau điều chỉnh xu hướng không khác 0 ngay cả khi M = 0. Kết hợp "
        f"với mục 4.14.4, bằng chứng về tốc độ và thời gian chờ đứng vững trước giả định xu hướng tuyến tính, còn bằng chứng về số chuyến "
        f"thì không.")
