"""Mô hình lý thuyết và giả thuyết (mục 2.11) và kiểm định các giả thuyết (mục 4.15)."""
import numpy as np
import pandas as pd

from lib import pval, stars, vint, vn
from results import pct_log


def model(rp, R):
    rp.H2("2.11. Mô hình lý thuyết và giả thuyết nghiên cứu")
    rp.P("Mục này xây dựng một mô hình đơn giản gồm bốn khối: cầu chuyến đi theo chi phí tổng quát, quan hệ tốc độ – lưu lượng, "
         "cơ chế lan tỏa qua mạng lưới chuyến đi và cơ chế phân bổ gánh nặng của phí. Mục đích không phải mô hình hóa toàn bộ thị "
         "trường, mà suy ra các giả thuyết có thể bác bỏ được bằng dữ liệu, trong đó có những dự báo định lượng về hình dạng của "
         "tác động chứ không chỉ về dấu. Các giả thuyết được kiểm định ở mục 4.15.")
    rp.H3("2.11.1. Cầu chuyến đi theo chi phí tổng quát")
    rp.P("Gọi q_od là số chuyến gọi xe từ vùng o đến vùng d, p_od là giá hành khách trả, T_od là thời gian di chuyển và v là giá "
         "trị thời gian. Cầu có độ co giãn không đổi theo chi phí tổng quát:")
    rp.EQ("q_od = A_od · (p_od + v · T_od)^(−ε)")
    rp.P("Khi chuyến đi chạm vùng thu phí, giá tăng thêm τ = 1,50 USD. Nếu tạm bỏ qua thay đổi của thời gian di chuyển, thay đổi "
         "log số chuyến là:")
    rp.EQ("Δ ln q_od ≈ −ε · ln(1 + τ / (p_od + v · T_od))")
    rp.PS(
        "Phương trình cho hai dự báo. **H1:** số chuyến chạm CRZ giảm. **H1b (liều – đáp ứng):** với ε không đổi giữa các cặp OD, "
        "mức giảm tỷ lệ thuận với ln(1 + τ/p), nên chuyến rẻ và ngắn, nơi phí chiếm tỷ trọng lớn trong giá, phải giảm mạnh hơn. Nếu "
        "dữ liệu không cho thấy gradient này, hoặc ε khác nhau giữa các nhóm chuyến (chẳng hạn chuyến ngắn có nhiều phương án thay "
        "thế hơn), hoặc thành phần thời gian v·T lớn đến mức làm phẳng quan hệ.",
        "Với chuyến đi chung, mỗi hành khách là một bản ghi chuyến và chịu phí riêng, trong khi giá của chuyến đi chung thấp hơn chuyến "
        "đi riêng. Vì vậy τ/p của chuyến đi chung cao hơn, và **H5:** tỷ lệ yêu cầu đi chung giảm mạnh hơn tổng số chuyến.")
    rp.H3("2.11.2. Quan hệ tốc độ – lưu lượng")
    rp.P("Theo hàm của Bureau of Public Roads (1964), thời gian di chuyển trên một đoạn đường phụ thuộc vào tỷ số lưu lượng V trên "
         "năng lực K:")
    rp.EQ("T = T₀ · [1 + α · (V / K)^β],   α ≈ 0,15;  β ≈ 4")
    rp.P("Lấy vi phân, thay đổi log tốc độ S = L/T khi lưu lượng giảm là:")
    rp.EQ("Δ ln S ≈ [α β (V/K)^β / (1 + α (V/K)^β)] · (−Δ ln V)")
    rp.PS(
        "Hệ số trong ngoặc tăng rất nhanh theo V/K vì β lớn. Hai dự báo: **H2:** tốc độ tăng khi lưu lượng vào vùng giảm. **H2b "
        "(độ lồi):** cùng một mức giảm lưu lượng tạo ra mức tăng tốc độ lớn hơn ở các giờ có lưu lượng cao. Nói cách khác, lợi ích về "
        "tốc độ phải tập trung ở giờ đông, chứ không phân bố đều.",
        "Mô hình cũng cho một dự báo động. Tốc độ tăng làm giảm thành phần v·T của chi phí tổng quát, kéo một phần lưu lượng quay lại, "
        "đúng cơ chế mà Duranton và Turner (2011) ghi nhận ở quy mô toàn quốc. **H6:** mức tăng tốc độ lớn nhất ngay sau khi áp dụng và "
        "giảm dần theo thời gian khi nhu cầu điều chỉnh.")
    rp.H3("2.11.3. Lan tỏa qua mạng lưới chuyến đi")
    rp.P("Xét một vùng z nằm ngoài CRZ. Gọi e_z là tỷ trọng chuyến đón tại z có điểm trả trong CRZ trước chính sách (mức phơi nhiễm). "
         "Nếu chỉ các chuyến này bị phí tác động, với cùng tác động δ = Δ ln q của chuyến chạm CRZ, thì:")
    rp.EQ("Δ ln q_z = ln(1 + e_z · (e^δ − 1)) ≈ e_z · (e^δ − 1)")
    rp.P("**H3 (lan tỏa theo liều):** tác động lên vùng ngoài CRZ tỷ lệ thuận với e_z, với hệ số góc xấp xỉ e^δ − 1. Nếu hệ số góc "
         "ước lượng lớn hơn đáng kể giá trị cơ học này, có một kênh lan tỏa hành vi bổ sung, như hành khách thay đổi thói quen ở cả "
         "khu vực xung quanh hoặc tài xế tránh khu vực gần ranh giới.")
    rp.H3("2.11.4. Phân bổ gánh nặng")
    rp.PS(
        "Phí được ghi thành một dòng riêng trên hóa đơn và nền tảng thu hộ, nên phần phí danh nghĩa đến thẳng hành khách. Câu hỏi là "
        "giá cơ sở có thay đổi không. Theo Weyl và Fabinger (2013), tỷ lệ chuyển thuế phụ thuộc vào độ cong của đường cầu và cấu trúc "
        "cạnh tranh, nên lý thuyết không cho một dự báo dấu chắc chắn cho giá cơ sở. Riêng thu nhập tài xế, quy định của TLC tính thu "
        "nhập tối thiểu theo quãng đường và thời gian, dạng pay = a · dặm + b · phút, nên:")
    rp.EQ("pay / dặm = a + b · 60 / S")
    rp.P("**H4:** khi tốc độ S tăng, thu nhập tài xế mỗi dặm giảm một lượng cơ học ≈ b · 60 · (1/S₁ − 1/S₀), kể cả khi công thức "
         "trả lương không đổi. Đây là một kênh ít được chú ý: chính việc giảm ùn tắc làm giảm thu nhập mỗi dặm của tài xế khi thu nhập "
         "gắn với thời gian.")
    hyp = pd.DataFrame([
        ("H1", "Cầu theo chi phí tổng quát", "Số chuyến chạm CRZ giảm", "DiD, SCM, DML (Chương 4)"),
        ("H1b", "Cầu, ε không đổi", "Mức giảm tăng theo tỷ trọng phí τ/p", "DiD theo ngũ phân vị τ/p"),
        ("H2", "Tốc độ – lưu lượng (BPR)", "Tốc độ tăng", "DiD tốc độ"),
        ("H2b", "Độ lồi của BPR", "Tăng tốc độ lớn hơn ở giờ lưu lượng cao", "Hồi quy theo lưu lượng giờ"),
        ("H3", "Lan tỏa qua mạng chuyến đi", "Tác động ngoài CRZ tỷ lệ với phơi nhiễm, hệ số góc ≈ e^δ − 1", "DiD liều liên tục"),
        ("H4", "Thu nhập theo phút và dặm", "Thu nhập/dặm giảm cơ học khi tốc độ tăng", "So sánh dự báo cơ học với DiD"),
        ("H5", "Phí theo chuyến, không ưu đãi đi chung", "Tỷ lệ đi chung giảm mạnh hơn tổng số chuyến", "DiD tỷ lệ đi chung"),
        ("H6", "Nhu cầu cảm ứng", "Tăng tốc độ lớn nhất lúc đầu rồi giảm dần", "DiD theo độ dài giai đoạn sau"),
    ], columns=["Giả thuyết", "Khối mô hình", "Dự báo", "Cách kiểm định"])
    rp.TAB(hyp, "Các giả thuyết suy ra từ mô hình lý thuyết", widths=[1.8, 4.2, 5.6, 4.4], size=10, align=["center", "left", "left", "left"],
           source="Nguồn: tác giả xây dựng.")


def tests(rp, R):
    tw = R.did("hvfhv", "ln_n")
    mp = R.did("hvfhv", "mph")
    shp = R.did("hvfhv", "shared_pct")
    h1 = R.t("t83")
    h2 = R.t("t84_speed")
    h2m = R.t("t84b")
    h3 = R.t("t85_spillover")
    h3b = R.t("t85b")
    h4 = R.t("t86").iloc[0]
    pw = R.t("t80")
    meta = R.J["18_theory_sensitivity"]
    od_all = R.od("Tất cả chuyến chạm CRZ", "ln_n")
    rp.H2("4.15. Đối chiếu kết quả với các giả thuyết lý thuyết")
    rp.P("Mục này kiểm định tám giả thuyết của mục 2.11. Với H1, H2, H5 và H6, bằng chứng đã có ở các mục trước. Với H1b, H2b, H3 và "
         "H4, bước 18 của pipeline ước lượng thêm các đặc tả được thiết kế riêng cho từng dự báo.")
    rp.H3("4.15.1. H1b: liều – đáp ứng theo tỷ trọng phí")
    t = pd.DataFrame({"Ngũ phân vị τ/p": h1.quintile.map(vint), "Số cặp OD": h1.pairs.map(vint),
                      "Chi phí chuyến 2024 (USD)": h1.p0_mean.map(lambda v: vn(v, 2)),
                      "τ/p (%)": (100 * h1.fee_share).map(lambda v: vn(v, 2)),
                      "Quãng đường TB (dặm)": h1.miles_mean.map(lambda v: vn(v, 2)),
                      "Tác động (%)": [f"{vn(pct_log(c), 2)}{stars(p)}" for c, p in zip(h1.coef, h1.p)],
                      "SE": h1.se.map(lambda v: vn(v, 4)),
                      "ε ngụ ý": h1.implied_elasticity.map(lambda v: vn(v, 2))})
    rp.TAB(t, "Tác động lên số chuyến theo ngũ phân vị tỷ trọng phí trong giá (panel cặp OD × tháng)",
           widths=[1.8, 1.6, 2.4, 1.6, 2.2, 2.2, 1.6, 1.6], size=9.5,
           source="Nguồn: t83_dose_response_fee_share.csv. Mỗi ngũ phân vị so với toàn bộ cặp không chạm CRZ; FE cặp và tháng; cụm theo vùng đón.")
    m1 = meta["h1b"]
    rp.PS(
        f"Tỷ trọng phí tăng từ {vn(100 * h1.fee_share.iloc[0], 1)}% ở nhóm chuyến đắt nhất (trung bình {vn(h1.miles_mean.iloc[0], 1)} "
        f"dặm) lên {vn(100 * h1.fee_share.iloc[-1], 1)}% ở nhóm rẻ nhất ({vn(h1.miles_mean.iloc[-1], 1)} dặm), tức hơn gấp đôi. Nếu ε "
        f"không đổi, tác động ở nhóm cuối phải lớn gấp đôi nhóm đầu. Thực tế, tác động chỉ đi từ {vn(pct_log(h1.coef.iloc[0]), 1)}% "
        f"đến trong khoảng {vn(pct_log(h1.coef.iloc[1:].max()), 1)}% đến {vn(pct_log(h1.coef.iloc[1:].min()), 1)}% ở bốn nhóm còn lại. "
        f"Hồi quy có trọng số của tác động theo ln(1 + τ/p) cho hệ số góc {vn(m1['slope'], 3)} (sai số chuẩn {vn(m1['slope_se'], 3)}): "
        f"đúng dấu dự báo nhưng chỉ có ý nghĩa ở mức 10%, và nhỏ hơn nhiều so với mức mà ε không đổi ngụ ý.",
        f"Vì vậy H1b chỉ được ủng hộ yếu. Độ co giãn ngụ ý giảm từ {vn(h1.implied_elasticity.iloc[0], 1)} ở chuyến dài xuống "
        f"{vn(h1.implied_elasticity.iloc[-1], 1)} ở chuyến ngắn. Thành phần thời gian v·T trong chi phí tổng quát không giải thích được "
        f"điều này: chuyến dài có v·T lớn, nên tỷ trọng phí trong chi phí tổng quát còn nhỏ hơn tỷ trọng trong giá, và độ co giãn ngụ ý "
        f"của chuyến dài lẽ ra còn cao hơn nữa. Hai cách giải thích còn lại là độ co giãn khác nhau giữa các nhóm khách (chuyến dài "
        f"chạm CRZ chủ yếu là chuyến giữa CRZ và quận ngoài, với cơ cấu khách khác chuyến ngắn trong trung tâm), và phản ứng theo địa "
        f"điểm: hành khách phản ứng với việc phải đi vào vùng có phí như một sự kiện rời rạc, hơn là với tỷ lệ phí trên giá. Kết luận "
        f"thận trọng là mô hình ε đồng nhất không mô tả tốt dữ liệu: tác động gần như không đổi ở mức khoảng 9–12% ở mọi nhóm, thay vì "
        f"tăng theo tỷ trọng phí.")
    rp.H3("4.15.2. H2b: độ lồi của quan hệ tốc độ – lưu lượng")
    t = pd.DataFrame({"Đặc tả": h2m.model, "Biến": h2m.term.map({"v_rel": "Lưu lượng tương đối", "v_rel2": "Lưu lượng tương đối²",
                                                                 "weekend": "Cuối tuần"}),
                      "Hệ số": [f"{vn(c, 3)}{stars(p)}" for c, p in zip(h2m.coef, h2m.p)], "SE": h2m.se.map(lambda v: vn(v, 3)),
                      "p": h2m.p.map(pval), "R²": h2m.r2.map(lambda v: vn(v, 3))})
    rp.TAB(t, "Mức tăng tốc độ theo giờ × loại ngày hồi quy theo lưu lượng CRZ→CRZ năm 2024",
           widths=[4.4, 3.6, 2.2, 1.8, 1.8, 1.6], size=10, align=["left", "left"] + ["center"] * 4,
           source=f"Nguồn: t84b_speed_gain_vs_flow_models.csv; {vint(h2m.n.iloc[0])} ô giờ × loại ngày; sai số chuẩn HC1.")
    lab56 = rp.FIG(R.fig("f56"), "Kiểm định ba giả thuyết: liều – đáp ứng theo tỷ trọng phí (trái), tốc độ – lưu lượng (giữa), "
                               "lan tỏa theo mức phơi nhiễm (phải)")
    a1 = h2m[(h2m.model == "Tuyến tính theo lưu lượng")].iloc[0]
    q2 = h2m[(h2m.model == "Bậc hai theo lưu lượng") & (h2m.term == "v_rel2")].iloc[0]
    hi = h2.sort_values("trips_per_hour").iloc[-6:]
    lo = h2.sort_values("trips_per_hour").iloc[:6]
    rp.PS(
        f"Đơn vị quan sát là 48 ô giờ × loại ngày. Biến phụ thuộc là mức tăng tốc độ của chuyến CRZ→CRZ so với chuyến trong quận ngoài "
        f"(sai khác kép mô tả ở mục 4.6.4), biến giải thích là lưu lượng chuyến CRZ→CRZ trung bình mỗi giờ năm 2024, chuẩn hóa về giờ cao "
        f"nhất. Hệ số tuyến tính là {vn(a1.coef, 3)} (p {pval(a1.p)}), tương quan hạng Spearman {vn(a1.spearman_rho, 2)}: ở sáu giờ có "
        f"lưu lượng cao nhất, tốc độ tăng trung bình {vn(hi.did_vs_outer.mean(), 2)} dặm/giờ, so với {vn(lo.did_vs_outer.mean(), 2)} ở "
        f"sáu giờ thấp nhất. Số hạng bậc hai dương ({vn(q2.coef, 3)}, p {pval(q2.p)}) phù hợp với độ lồi mà hàm BPR dự báo, dù chỉ ở mức "
        f"ý nghĩa 10%.",
        "H2b được ủng hộ ở mức vừa phải. Với 48 quan sát và biến giải thích là lưu lượng gọi xe chứ không phải tổng lưu lượng mọi "
        "phương tiện, độ chính xác không thể cao; nhưng cả dấu, hình dạng và thứ tự hạng đều khớp với dự báo. Kết quả này cũng giải thích "
        "vì sao mức tăng tốc độ tập trung ở chiều tối ngày thường như mục 4.6.4 đã mô tả.")
    rp.H3("4.15.3. H3: lan tỏa theo mức phơi nhiễm")
    t = pd.DataFrame({"Mẫu": h3["sample"], "Biến": h3.outcome.map({"ln_n": "log số chuyến", "mph": "Tốc độ (dặm/giờ)"}),
                      "Hệ số (sau × phơi nhiễm)": [f"{vn(c, 3)}{stars(p)}" for c, p in zip(h3.coef, h3.p)],
                      "SE": h3.se.map(lambda v: vn(v, 3)), "Số vùng": h3.n_zones.map(vint),
                      "Phơi nhiễm P10–P90 (%)": [f"{vn(100 * a, 1)}–{vn(100 * b, 1)}" for a, b in zip(h3.exp_p10, h3.exp_p90)]})
    rp.TAB(t, "Tác động sau chính sách theo mức phơi nhiễm của các vùng ngoài CRZ", widths=[4.0, 2.8, 3.4, 1.6, 1.6, 2.6], size=10,
           align=["left", "left"] + ["center"] * 4,
           source="Nguồn: t85_spillover_dose_response.csv. Phơi nhiễm = tỷ trọng chuyến đón tại vùng có điểm trả trong CRZ năm 2024; "
                  "FE vùng và tuần; cụm theo vùng.")
    r0 = h3[(h3["sample"] == "Mọi vùng ngoài CRZ") & (h3.outcome == "ln_n")].iloc[0]
    rm = h3[(h3["sample"] == "Mọi vùng ngoài CRZ") & (h3.outcome == "mph")].iloc[0]
    mech = float(np.exp(od_all.coef) - 1)
    t = pd.DataFrame({"Nhóm phơi nhiễm": ["1 (tham chiếu)"] + [vint(b) for b in h3b.bin],
                      "Phơi nhiễm TB (%)": [vn(100 * meta["h3_bin1_exposure"], 1)] + [vn(100 * e, 1) for e in h3b.exposure_mean],
                      "Tác động so với nhóm 1 (%)": ["0"] + [f"{vn(pct_log(c), 2)}{stars(p)}" for c, p in zip(h3b.coef, h3b.p)],
                      "SE": ["–"] + [vn(s, 4) for s in h3b.se]})
    rp.TAB(t, "Tác động lên số chuyến theo ngũ phân vị phơi nhiễm", widths=[3.6, 3.6, 4.4, 2.4], size=10,
           source="Nguồn: t85b_spillover_by_exposure_bin.csv.")
    rp.PS(
        f"Hệ số của tương tác sau chính sách × phơi nhiễm trên 206 vùng ngoài CRZ là {vn(r0.coef, 3)} (sai số chuẩn {vn(r0.se, 3)}): "
        f"vùng có phơi nhiễm cao hơn 10 điểm phần trăm mất thêm khoảng {vn(-10 * r0.coef, 1)}% số chuyến. Kết quả vững khi bỏ vùng vắt "
        f"ranh giới và khi chỉ dùng quận ngoài. Chiều của tác động khớp với H3.",
        f"Độ lớn thì không khớp với dự báo cơ học. Với tác động lên chuyến chạm CRZ trên panel OD là δ = {vn(od_all.coef, 3)}, hệ số góc "
        f"cơ học là e^δ − 1 = {vn(mech, 3)}. Hệ số ước lượng lớn gấp khoảng {vn(r0.coef / mech, 1)} lần. Bảng theo ngũ phân vị cho thấy "
        f"lý do: bốn nhóm phơi nhiễm thấp gần như không đổi so với nhau, toàn bộ tác động tập trung ở nhóm phơi nhiễm cao nhất (trung bình "
        f"{vn(100 * h3b.exposure_mean.iloc[-1], 1)}%), với mức giảm {vn(-pct_log(h3b.coef.iloc[-1]), 1)}%. Nhóm này gồm các vùng sát ranh "
        f"giới, nơi không chỉ chuyến vào CRZ mà cả chuyến nội bộ trong khu vực cũng giảm. Như vậy, lan tỏa có hai thành phần: thành phần "
        f"cơ học theo phơi nhiễm, và một thành phần hành vi tập trung ở vùng lân cận ranh giới, lớn hơn thành phần cơ học.",
        f"Về tốc độ, tương tác phơi nhiễm cũng dương ({vn(rm.coef, 3)}): vùng có nhiều chuyến vào CRZ được lợi về tốc độ nhiều hơn, vì "
        f"một phần hành trình của các chuyến này nằm trong vùng đường đã thông thoáng hơn. Kết quả này nhất quán với phát hiện của Cook "
        f"và cộng sự (2025) rằng tốc độ tăng cả trên các tuyến ngoài vùng có nhiều chuyến đi vào vùng.")
    rp.H3("4.15.4. H4: thu nhập tài xế mỗi dặm giảm cơ học khi tốc độ tăng")
    rp.PS(
        f"Ước lượng b, thu nhập tài xế cho mỗi phút, bằng hồi quy thu nhập mỗi dặm theo số phút mỗi dặm trên panel vùng × tuần năm "
        f"2024 với hiệu ứng cố định vùng và tuần, cho b = {vn(h4.b_pay_per_minute, 3)} USD/phút (sai số chuẩn {vn(h4.b_se, 3)}). Với tốc "
        f"độ trước chính sách {vn(h4.mph_pre, 2)} dặm/giờ và mức tăng {vn(h4.d_mph, 2)} dặm/giờ, dự báo cơ học là thu nhập mỗi dặm "
        f"thay đổi {vn(h4.predicted_d_pay_pm, 3)} USD. Hệ số DiD quan sát được lại là {vn(h4.did_d_pay_pm, 3)} USD (sai số chuẩn "
        f"{vn(h4.did_d_pay_pm_se, 3)}), ngược dấu với dự báo.",
        "Kết quả này có hai cách đọc, và cả hai đều quan trọng. Thứ nhất, nó cho thấy nếu hệ số DiD đúng, phải có một yếu tố khác làm "
        "tăng thu nhập mỗi dặm trong CRZ đủ để lấn át hiệu ứng cơ học của tốc độ, chẳng hạn nền tảng tăng tỷ lệ chia cho tài xế trong "
        "vùng có phí để giữ nguồn cung. Thứ hai, và phù hợp hơn với các phép thử ở mục 4.14, hệ số DiD của thu nhập mỗi dặm chịu xu "
        "hướng có sẵn, nên phép so sánh này là một lý do độc lập nữa để không diễn giải nó như tác động nhân quả. H4 vì vậy chưa kiểm "
        "định được bằng dữ liệu hiện có; giá trị của nó là cho biết thành phần cơ học cần được tách ra trước khi đánh giá bất kỳ thay "
        "đổi nào của thu nhập tài xế.")
    rp.H3("4.15.5. Tổng hợp")
    lp = R.t("t90").set_index("outcome")
    shr_rel = 100 * shp.coef / shp.treated_pre_mean
    a4 = pw[(pw.post_weeks == pw.post_weeks.min()) & (pw.outcome == "mph")].iloc[0]
    a52 = pw[(pw.post_weeks == pw.post_weeks.max()) & (pw.outcome == "mph")].iloc[0]
    summ = pd.DataFrame([
        ("H1", "Số chuyến giảm", f"{vn(pct_log(tw.coef), 1)}% (TWFE, một năm trước); {vn(pct_log(lp.loc['ln_n'].effect_trend_adj), 1)}% sau điều chỉnh xu hướng 2023–2024", "Ủng hộ một phần: không tách được khỏi xu hướng có sẵn"),
        ("H1b", "Giảm theo tỷ trọng phí", f"Hệ số góc {vn(m1['slope'], 2)}, p ≈ 0,07; gradient yếu hơn nhiều so với dự báo", "Ủng hộ yếu"),
        ("H2", "Tốc độ tăng", f"+{vn(mp.coef, 2)} dặm/giờ; +{vn(lp.loc['mph'].effect_trend_adj, 2)} sau điều chỉnh xu hướng 2023–2024", "Ủng hộ"),
        ("H2b", "Tăng nhiều hơn ở giờ đông", f"Hệ số {vn(a1.coef, 3)}, p {pval(a1.p)}; số hạng bậc hai dương", "Ủng hộ vừa phải"),
        ("H3", "Lan tỏa theo phơi nhiễm", f"Hệ số {vn(r0.coef, 2)}, lớn gấp {vn(r0.coef / mech, 1)} lần dự báo cơ học", "Ủng hộ về chiều; có thêm kênh hành vi"),
        ("H4", "Thu nhập/dặm giảm cơ học", f"Dự báo {vn(h4.predicted_d_pay_pm, 2)} USD, DiD {vn(h4.did_d_pay_pm, 2)} USD (chịu tiền xu hướng)", "Chưa kiểm định được"),
        ("H5", "Đi chung giảm mạnh hơn", f"Tỷ lệ đi chung {vn(shr_rel, 0)}% so với mức nền; giả dược 2024−2023 bằng tác động 2025−2024 ({vn(lp.loc['shared_pct'].placebo_2024_vs_2023, 2)} điểm %)", "Ủng hộ một phần: có xu hướng có sẵn"),
        ("H6", "Tăng tốc độ giảm dần", f"{vn(a4.coef, 2)} dặm/giờ sau {vint(a4.post_weeks)} tuần; {vn(a52.coef, 2)} sau {vint(a52.post_weeks)} tuần", "Ủng hộ"),
    ], columns=["Giả thuyết", "Dự báo", "Bằng chứng", "Kết luận"])
    rp.TAB(summ, "Tổng hợp kết quả kiểm định các giả thuyết lý thuyết", widths=[1.8, 3.6, 7.0, 3.6], size=9.5,
           align=["center", "left", "left", "left"], source="Nguồn: tác giả tổng hợp từ t30, t80, t83–t86, t90.")
    rp.P("Ba giả thuyết được ủng hộ rõ (tốc độ tăng, lan tỏa theo phơi nhiễm về chiều, lợi ích tốc độ giảm dần), bốn được ủng hộ một "
         "phần và một chưa kiểm định được. Điểm yếu lớn nhất so với mô hình là H1: dữ liệu 2022–2025 cho thấy số chuyến CRZ đã giảm "
         "tương đối từ trước, nên dự báo cơ bản nhất của mô hình cầu không được xác nhận chắc chắn. Hai điểm khác mô hình không giải "
         "thích tốt là hình dạng của liều – đáp ứng theo giá (tác động gần như không đổi theo tỷ trọng phí) và độ lớn của lan tỏa ở vùng "
         "sát ranh giới. Cả hai đều chỉ ra cùng một hướng mở rộng mô hình: phản ứng của hành khách không chỉ phụ thuộc vào mức tăng giá "
         "của từng chuyến, mà vào việc chuyến đi đó có gắn với khu vực trung tâm hay không, một dạng phản ứng theo địa điểm mà mô hình cầu "
         "theo từng cặp OD không nắm được.")
