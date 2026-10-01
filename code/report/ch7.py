"""Chương 7. Giá trị kinh doanh và chiến lược dữ liệu."""
import numpy as np
import pandas as pd

from lib import pval, stars, vint, vn
from results import pct_log


def build(rp, R):
    co = R.t("t77_company")
    cd = R.t("t77b").iloc[0]
    fa = R.t("t78")
    fm = R.t("t79_forecast")
    fd = R.t("t79b")
    pw = R.t("t80")
    pe = R.t("t81")
    tco = R.t("t82")
    flog = R.JS["business/forecast"]
    tw = R.did("hvfhv", "ln_n")
    rev = R.t("t16")

    rp.H1("CHƯƠNG 7. GIÁ TRỊ KINH DOANH VÀ CHIẾN LƯỢC DỮ LIỆU")
    rp.PS(
        "Các chương trước đo tác động của chính sách từ góc nhìn của người đánh giá chính sách. Chương này đổi góc nhìn sang doanh "
        "nghiệp: một nền tảng gọi xe, một cơ quan vận tải hoặc một đơn vị cung cấp dữ liệu sẽ dùng cùng tài sản dữ liệu này để ra "
        "quyết định gì, và giá trị của tài sản đó được đo thế nào. Nội dung bám theo ba chương ứng dụng của bài giảng: dự báo nhu cầu "
        "và quản trị vận hành (Chương 4), phân tích khách hàng và thử nghiệm quy mô lớn (Chương 5), định giá và thương mại hóa dữ liệu "
        "(Chương 6).",
        "Chương này trả lời câu hỏi nghiên cứu RQ5 (mục 1.4.1). Mục 7.1 phân tích tác động theo hãng. Mục 7.2 so sánh dự báo nhu cầu với "
        "suy luận nhân quả. Mục 7.3 tính quy mô dữ liệu cần cho một thử nghiệm chính sách. Mục 7.4 xem xét định giá động. Mục 7.5 tổng "
        "hợp phân khúc chuyến đi. Mục 7.6 và 7.7 bàn về giá trị của tài sản dữ liệu và lộ trình chiến lược.")

    # ================================================================ 7.1
    rp.H2("7.1. Tác động theo hãng và cạnh tranh trong vùng thu phí")
    rows = []
    for y in ("ln_uber", "ln_lyft", "uber_share"):
        for sp in ("TWFE", "DDD mùa vụ"):
            r = co[(co.outcome == y) & (co.spec == sp)].iloc[0]
            rows.append((r.outcome_label, sp, f"{vn(r.coef, 4)}{stars(r.p)}", vn(r.se, 4),
                         f"[{vn(r.ci_low, 4)}; {vn(r.ci_high, 4)}]",
                         vn(r.pct, 2) + "%" if pd.notna(r.pct) else vn(r.coef, 2) + " điểm %"))
    rp.TAB(pd.DataFrame(rows, columns=["Biến kết quả", "Đặc tả", "Hệ số", "SE", "KTC 95%", "Tác động"]),
           "Tác động của phí CRZ lên số chuyến theo hãng và thị phần của Uber (panel vùng × tuần)",
           widths=[4.4, 2.6, 2.2, 1.6, 3.2, 2.0], size=9.5, align=["left", "left"] + ["center"] * 4,
           source="Nguồn: t77_company_did.csv. *, **, *** tương ứng p < 0,1; 0,05; 0,01; sai số chuẩn phân cụm theo vùng.")
    u = co[(co.outcome == "ln_uber") & (co.spec == "TWFE")].iloc[0]
    ly = co[(co.outcome == "ln_lyft") & (co.spec == "TWFE")].iloc[0]
    sh = co[(co.outcome == "uber_share") & (co.spec == "TWFE")].iloc[0]
    rp.PS(
        f"Số chuyến Uber đón trong CRZ giảm {vn(-u.pct, 1)}% so với phản thực tế, trong khi số chuyến Lyft giảm "
        f"{vn(-ly.pct, 1)}%. Hồi quy xếp chồng hai hãng với hiệu ứng cố định vùng × hãng và tuần × hãng cho chênh lệch giữa hai hệ số "
        f"là {vn(cd.coef, 4)} (sai số chuẩn {vn(cd.se, 4)}, p {pval(cd.p)}), nên khác biệt này không phải ngẫu nhiên. Hệ quả trực tiếp "
        f"là thị phần của Uber trong HVFHV tại CRZ giảm {vn(-sh.coef, 2)} điểm phần trăm, trên nền {vn(sh.treated_pre_mean, 1)}% năm "
        f"2024. Kết quả gần như không đổi khi thêm hiệu ứng cố định nhóm × tuần trong năm.",
        "Đồ án không có dữ liệu giá theo hãng ở mức đủ chi tiết để giải thích khác biệt này, nên chỉ có thể nêu các giả thuyết có "
        "thể kiểm định. Một là khác biệt về cơ cấu khách hàng: nếu Uber có tỷ trọng chuyến ngắn nội vùng cao hơn, và đây là loại chuyến "
        "nhạy nhất với phí (mục 4.8), Uber sẽ mất nhiều hơn. Hai là khác biệt về chiến lược chuyển phí: một hãng có thể hấp thụ một "
        "phần phí qua khuyến mãi trong khi hãng kia chuyển toàn bộ. Ba là khác biệt về phía cung: nếu tài xế đa nền tảng ưu tiên nhận "
        "chuyến của hãng trả tốt hơn trong vùng có phí, số chuyến hoàn thành của từng hãng sẽ phản ánh cả cạnh tranh trên thị trường "
        "tài xế. Với một nền tảng, đây là loại thông tin cạnh tranh có giá trị cao mà dữ liệu công khai cung cấp miễn phí cho cả đối thủ.")

    # ================================================================ 7.2
    rp.H2("7.2. Dự báo nhu cầu và giới hạn của dự báo làm phản thực tế")
    rp.H3("7.2.1. Thiết kế")
    rp.PS(
        "Mục 2.9.1 đã trình bày cách dùng dự báo nhu cầu làm phản thực tế: huấn luyện mô hình trên giai đoạn trước sự kiện, rồi "
        "diễn giải chênh lệch giữa thực tế và dự báo ở giai đoạn sau là tác động. Cách làm này phổ biến trong doanh nghiệp vì chỉ "
        "cần chuỗi thời gian, không cần thiết kế nhận dạng. Mục này kiểm tra nó trên chính dữ liệu của đồ án.",
        "Đồ án áp dụng cách tiếp cận này cho log số chuyến HVFHV đón trong CRZ theo ngày, với năm mô hình: Ridge chỉ dùng lịch (thứ "
        "trong tuần, ngày lễ liên bang và ngày liền kề, kỳ nghỉ cuối năm, sóng điều hòa theo năm) có xu hướng tuyến tính; Ridge thêm "
        "hai chuỗi đối chứng là log số chuyến của Manhattan phía bắc và quận ngoài, có và không có xu hướng; Ridge chỉ thêm chuỗi quận "
        "ngoài; và LightGBM với lịch và hai chuỗi đối chứng. Mô hình được huấn luyện trên dữ liệu đến 31/10/2024 và đánh giá trên "
        "giai đoạn giữ lại từ 01/11/2024 đến 04/01/2025, gồm cả kỳ nghỉ cuối năm, một thử thách khó. Quy tắc chọn được định trước: "
        "mô hình có sai số phần trăm tuyệt đối trung bình (MAPE) thấp nhất trên giai đoạn giữ lại được dùng làm phản thực tế chính.")
    rp.H3("7.2.2. Kết quả")
    t = pd.DataFrame({"Mô hình": fa.model, "MAPE giữ lại (%)": fa.mape_pct.map(lambda v: vn(v, 2)),
                      "RMSE (chuyến/ngày)": fa.rmse.map(vint), "Chệch (%)": fa.bias_pct.map(lambda v: vn(v, 2)),
                      "Chênh lệch sau chính sách (%)": fa.post_effect_pct.map(lambda v: vn(v, 2, sign=True))})
    rp.TAB(t, "Độ chính xác dự báo trên giai đoạn giữ lại và chênh lệch thực tế – dự báo sau chính sách",
           widths=[6.4, 2.2, 2.4, 1.8, 3.2], size=9.5, align=["left"] + ["center"] * 4,
           source="Nguồn: t78_forecast_accuracy.csv. Mô hình naive không dùng được để dự báo xa nên không có chênh lệch sau chính sách.")
    rp.FIG(R.fig("f53"), "Số chuyến thực tế và dự báo phản thực tế của mô hình được chọn (trên) và chênh lệch theo tháng (dưới)")
    best = fa[fa.model == flog["best"]].iloc[0]
    rng = fa.post_effect_pct.dropna()
    ou = fa[fa.model == "Ridge: lịch + quận ngoài"].iloc[0]
    rp.PS(
        f"Mô hình có MAPE thấp nhất là \"{flog['best']}\" ({vn(best.mape_pct, 2)}%). Phản thực tế của nó cho chênh lệch trung bình "
        f"sau chính sách là {vn(best.post_effect_pct, 2, sign=True)}%, tức số chuyến thực tế còn cao hơn dự báo. Kết quả này trái "
        f"chiều với mọi thiết kế nhân quả ở Chương 4, vốn cho mức giảm khoảng {vn(-pct_log(tw.coef), 1)}%. Năm mô hình cho "
        f"chênh lệch từ {vn(rng.min(), 1)}% đến {vn(rng.max(), 1, sign=True)}%, một khoảng rộng hơn cả độ lớn của tác động cần đo. Trong khi đó, "
        f"MAPE của bốn mô hình tốt nhất chỉ khác nhau khoảng {vn(fa.mape_pct.iloc[3] - fa.mape_pct.iloc[0], 1)} điểm phần trăm.",
        f"Nguyên nhân có thể đọc từ hệ số của mô hình được chọn. Hệ số của log số chuyến Manhattan phía bắc là "
        f"{vn(flog['coef']['ln_mn'], 3)}, nghĩa là dự báo cho CRZ gần như bám theo chuỗi này. Nhưng mục 4.12 đã cho thấy Manhattan "
        f"phía bắc bị lan tỏa: số chuyến ở đây cũng giảm sau chính sách. Khi chuỗi đối chứng bị ảnh hưởng, phản thực tế bị kéo xuống "
        f"theo, và tác động bị triệt tiêu hoặc đảo dấu. Thêm vào đó, xu hướng tuyến tính ước lượng từ mười tháng được ngoại suy ra "
        f"mười hai tháng. Mô hình chỉ dùng chuỗi quận ngoài, ít bị lan tỏa hơn, cho {vn(ou.post_effect_pct, 1)}%, gần với kết quả "
        f"DiD, dù MAPE của nó chỉ đứng thứ {list(fa.model).index('Ridge: lịch + quận ngoài') + 1} trong bảng.",
        "Dữ liệu 2022–2025 ở mục 4.14.4 cho thêm một cách đọc. Số chuyến CRZ đã giảm tương đối khoảng "
        f"{vn(-100 * R.t('t90').set_index('outcome').loc['ln_n'].pre_slope_per_month, 2)} điểm phần trăm mỗi tháng từ trước chính "
        "sách, và sau khi trừ xu hướng này, tác động gần bằng không. Mô hình có xu hướng tuyến tính riêng vì thế không hẳn sai: nó "
        "ngoại suy một xu hướng có thật, và chênh lệch gần bằng không của nó phù hợp với ước lượng điều chỉnh xu hướng hơn là với "
        "các thiết kế chỉ dùng một năm trước chính sách. Điều đó không làm mô hình này trở thành ước lượng nhân quả đáng tin, vì chuỗi "
        "giải thích vẫn bị lan tỏa, nhưng nó cho thấy khoảng cách giữa dự báo và DiD một phần do cách hai phương pháp xử lý xu hướng.",
        "Kết quả này có hệ quả về phương pháp vượt ra ngoài đồ án. Độ chính xác dự báo trên giai đoạn giữ lại đo khả năng mô "
        "hình tái hiện quan hệ giữa các chuỗi khi không có can thiệp. Nó không đo được việc quan hệ đó có còn đúng sau can thiệp hay "
        "không, vì chính can thiệp có thể làm thay đổi các chuỗi giải thích. Chọn mô hình phản thực tế theo sai số dự báo vì vậy có "
        "thể chọn đúng mô hình tệ nhất về mặt nhân quả. Brodersen và cộng sự (2015) nêu rõ giả định rằng các chuỗi đối chứng không bị "
        "can thiệp ảnh hưởng; dữ liệu của đồ án cho thấy giả định này bị vi phạm theo cách có thể đo được. Trong doanh nghiệp, nơi các "
        "đánh giá kiểu \"thực tế so với dự báo\" rất phổ biến, bài học là mọi chuỗi đối chứng phải được kiểm tra độc lập về khả năng "
        "bị ảnh hưởng, ngoài việc kiểm tra độ tương quan.",
        "Dù vậy, mô hình dự báo vẫn có giá trị vận hành. Sai số dự báo ngày khoảng 9% trên giai đoạn khó nhất trong năm là đủ tốt để "
        "lập kế hoạch cung xe, và phần dư dự báo là đầu vào tự nhiên cho hệ thống phát hiện bất thường ở mục 6.5. Điều cần tránh là "
        "dùng cùng mô hình đó để trả lời câu hỏi nhân quả.")

    # ================================================================ 7.3
    rp.H2("7.3. Quy mô dữ liệu cần cho một thử nghiệm chính sách")
    rp.PS(
        "Mục 5.7 của bài giảng trình bày thử nghiệm A/B ở quy mô dữ liệu lớn. Một câu hỏi thiết kế trung tâm của mọi thử nghiệm là "
        "cần bao nhiêu dữ liệu để phát hiện một tác động có độ lớn cho trước. Với chính sách công, câu hỏi tương ứng là: sau bao lâu "
        "thì có thể đánh giá được chính sách? Đồ án trả lời bằng cách cắt giai đoạn sau chính sách còn 4, 8, 13, 26, 39 và 52 tuần, "
        "giữ nguyên toàn bộ giai đoạn trước, và ước lượng lại TWFE cho ba biến kết quả. Tác động nhỏ nhất phát hiện được (MDE) với "
        "công suất 80% và mức ý nghĩa 5% được tính bằng 2,8 lần sai số chuẩn (Bloom, 1995).")
    rows = []
    for L in sorted(pw.post_weeks.unique()):
        s = pw[pw.post_weeks == L].set_index("outcome")
        rows.append((vint(L), f"{vn(pct_log(s.loc['ln_n', 'coef']), 2)}%{stars(s.loc['ln_n', 'p'])}",
                     vn(s.loc["ln_n", "mde80_pct"], 2) + "%",
                     f"{vn(s.loc['mph', 'coef'], 3)}{stars(s.loc['mph', 'p'])}", vn(s.loc["mph", "mde80"], 3),
                     f"{vn(s.loc['wait', 'coef'], 3)}{stars(s.loc['wait', 'p'])}", vn(s.loc["wait", "mde80"], 3)))
    rp.TAB(pd.DataFrame(rows, columns=["Tuần sau", "Số chuyến: ước lượng", "Số chuyến: MDE", "Tốc độ: ước lượng",
                                       "Tốc độ: MDE", "Chờ: ước lượng", "Chờ: MDE"]),
           "Ước lượng và tác động nhỏ nhất phát hiện được theo độ dài giai đoạn sau chính sách",
           widths=[1.6, 2.6, 2.2, 2.4, 2.0, 2.4, 2.0], size=9.5, source="Nguồn: t80_power_mde.csv. Tốc độ theo dặm/giờ, thời gian chờ theo phút.")
    rp.FIG(R.fig("f54"), "Giá trị tuyệt đối của ước lượng và MDE theo số tuần sau chính sách")
    a4 = pw[(pw.post_weeks == 4)].set_index("outcome")
    a52 = pw[(pw.post_weeks == 52)].set_index("outcome")
    rp.PS(
        f"Hai quy luật hiện ra. Thứ nhất, MDE giảm khi có thêm dữ liệu nhưng giảm chậm: với số chuyến, từ {vn(a4.loc['ln_n', 'mde80_pct'], 2)}% "
        f"sau 4 tuần xuống {vn(a52.loc['ln_n', 'mde80_pct'], 2)}% sau 52 tuần. Mức giảm chậm vì sai số chuẩn phân cụm theo vùng bị chi "
        f"phối bởi số vùng, vốn cố định, hơn là bởi số tuần. Do đó, sau vài tháng, dữ liệu mới chủ yếu làm tăng độ tin cậy về "
        f"động thái chứ không cải thiện nhiều độ chính xác của tác động trung bình.",
        f"Thứ hai, và quan trọng hơn cho quyết định, bản thân tác động thay đổi theo thời gian. Mức giảm số chuyến sau 4 tuần chỉ là "
        f"{vn(-pct_log(a4.loc['ln_n', 'coef']), 1)}%, sau 13 tuần là {vn(-pct_log(pw[(pw.post_weeks == 13) & (pw.outcome == 'ln_n')].coef.iloc[0]), 1)}% "
        f"và sau 52 tuần là {vn(-pct_log(a52.loc['ln_n', 'coef']), 1)}%. Ngược lại, mức tăng tốc độ lớn nhất ở giai đoạn đầu "
        f"({vn(a4.loc['mph', 'coef'], 2)} dặm/giờ sau 4 tuần) và giảm dần về {vn(a52.loc['mph', 'coef'], 2)} dặm/giờ khi tính cả năm. "
        f"Hai xu hướng ngược chiều gợi ý rằng hành khách điều chỉnh chậm (thói quen thay đổi dần), còn hệ thống giao thông điều chỉnh "
        f"nhanh rồi một phần lưu lượng quay lại khi đường thông thoáng hơn, đúng hiện tượng nhu cầu cảm ứng mà lý thuyết giao thông dự "
        f"báo. Tất cả các ước lượng này đều có ý nghĩa thống kê ngay từ tuần thứ tư, nên công suất đủ; điều cần lưu ý là tác động "
        f"đo sớm không đại diện cho tác động dài hạn.",
        "Với doanh nghiệp chạy thử nghiệm, hàm ý tương tự đã được ghi nhận trong tài liệu thử nghiệm trực tuyến dưới tên hiệu ứng mới "
        "lạ và hiệu ứng thích nghi (Kohavi, Tang và Xu, 2020): quyết định dựa trên vài tuần đầu có thể đánh giá sai tác động dài hạn "
        "theo cả hai chiều. Dữ liệu lớn giải quyết được bài toán công suất, nhưng không giải quyết được bài toán thời gian.")

    # ================================================================ 7.4
    rp.H2("7.4. Định giá động: giá có phản ứng với nhu cầu trong ngày không?")
    rows = []
    GL = {"CRZ": "CRZ", "MN_NORTH": "Manhattan phía bắc", "OUTER": "Quận ngoài"}
    for g in ("CRZ", "MN_NORTH", "OUTER"):
        for per in (2024, 2025):
            s = pe[(pe.group == g) & (pe.period == per)].set_index("term")
            rows.append((GL[g], vint(per), f"{vn(s.loc['ln_n', 'coef'], 3)}{stars(s.loc['ln_n', 'p'])}", vn(s.loc["ln_n", "se"], 3),
                         f"{vn(s.loc['ln_mph', 'coef'], 3)}{stars(s.loc['ln_mph', 'p'])}", vn(s.loc["ln_mph", "se"], 3),
                         vint(s.n_obs.iloc[0]), vn(s.within_r2.iloc[0], 3)))
    rp.TAB(pd.DataFrame(rows, columns=["Nhóm vùng", "Năm", "Hệ số log số chuyến", "SE", "Hệ số log tốc độ", "SE", "Số quan sát",
                                       "R² trong"]),
           "Độ co giãn của giá cước mỗi dặm theo số chuyến và tốc độ giữa các giờ trong ngày",
           widths=[3.2, 1.2, 2.6, 1.4, 2.6, 1.4, 2.0, 1.6], size=9.5, align=["left"] + ["center"] * 7,
           source="Nguồn: t81_price_demand_elasticity.csv. Hiệu ứng cố định vùng × tháng; biến thiên chỉ giữa các giờ; cụm theo vùng.")
    c24 = pe[(pe.group == "CRZ") & (pe.period == 2024)].set_index("term")
    sg = pe[(pe.term == "ln_n") & (pe.p < 0.05)]
    sig_txt = ("không có trường hợp nào có ý nghĩa ở mức 5%" if sg.empty else
               "chỉ có ý nghĩa ở mức 5% trong " + ", ".join(f"{GL[r.group]} năm {int(r.period)} ({vn(r.coef, 3)})" for _, r in sg.iterrows()))
    c25 = pe[(pe.group == "CRZ") & (pe.period == 2025)].set_index("term")
    rp.PS(
        "Mục 6.4 của bài giảng trình bày định giá linh hoạt (dynamic pricing), mà giá tăng đột biến theo cầu của các nền tảng gọi xe "
        "là ví dụ điển hình (Castillo, Knoepfle và Weyl, 2017). Dữ liệu TLC không có hệ số tăng giá, nhưng cho phép một kiểm tra gián "
        "tiếp: trong cùng một vùng và cùng một tháng, giữa các giờ có nhiều chuyến và ít chuyến, giá cước mỗi dặm có khác nhau không? "
        "Hồi quy log giá mỗi dặm theo log số chuyến và log tốc độ, với hiệu ứng cố định vùng × tháng, trả lời câu hỏi này.",
        f"Kết quả là giá mỗi dặm gần như không phản ứng với số chuyến ở mức giờ trung bình tháng: hệ số của log số chuyến trong CRZ là "
        f"{vn(c24.loc['ln_n', 'coef'], 3)} năm 2024 và {vn(c25.loc['ln_n', 'coef'], 3)} năm 2025, đều không có ý nghĩa ở mức 5%. Trong "
        f"khi đó, hệ số của log tốc độ là {vn(c24.loc['ln_mph', 'coef'], 3)} và {vn(c25.loc['ln_mph', 'coef'], 3)}, rất có ý nghĩa: "
        f"khi tốc độ thấp hơn 10%, giá mỗi dặm cao hơn khoảng {vn(-c24.loc['ln_mph', 'coef'] * 10, 1)}%. Hệ số của tốc độ âm và có ý "
        f"nghĩa ở cả ba nhóm vùng và hai năm; hệ số của số chuyến đều nhỏ, {sig_txt}. Mẫu hình này cho thấy phần biến thiên giá giữa các giờ chủ yếu đến từ cấu trúc giá theo thời gian và quãng đường (chuyến "
        f"chậm tốn nhiều phút hơn trên mỗi dặm), không phải từ tăng giá theo khối lượng cầu.",
        "Cần thận trọng với cách đọc này. Giá tăng đột biến phản ứng với mất cân bằng cung cầu tức thời trong vài phút và vài trăm mét, "
        "trong khi dữ liệu ở đây đã được trung bình theo vùng, giờ và tháng. Một giờ có nhiều chuyến cũng thường là giờ có nhiều tài xế, "
        "nên tỷ lệ cung cầu có thể không đổi. Kết quả vì vậy không bác bỏ việc có định giá động, mà cho thấy ở mức tổng hợp mà cơ quan "
        "quản lý quan sát được, định giá động không phải là yếu tố chính của biến thiên giá giữa các giờ, và phí CRZ không làm thay đổi "
        "điều đó.")

    # ================================================================ 7.5
    rp.H2("7.5. Phân khúc chuyến đi và hàm ý cá nhân hóa")
    g = R.t("t43")
    ft = R.t("t47")
    ap = R.t("t58")
    gn = g[g.outcome == "dlog_n"].sort_values("group")
    gm = g[g.outcome == "d_mph"].sort_values("group")
    rows = [(f"Nhóm {int(r.group)}", vn(pct_log(r.gate), 2) + "%", vn(m.gate, 3)) for (_, r), (_, m) in
            zip(gn.iterrows(), gm.iterrows())]
    rp.TAB(pd.DataFrame(rows, columns=["Nhóm GATES (ngũ phân vị CATE của chính biến kết quả)", "Số chuyến", "Tốc độ (dặm/giờ)"]),
           "Tác động trung bình theo nhóm (GATES) của số chuyến và tốc độ", widths=[7.6, 4.2, 4.2], size=10,
           align=["left", "center", "center"],
           source="Nguồn: t43_dml_gates.csv (Chương 4). Mỗi biến kết quả được chia nhóm theo CATE ước lượng của riêng nó.")
    rows = [(f"{r.ftype}", vn(pct_log(r.tau_dlog_n), 2) + "%", vn(r.tau_d_mph, 3), vint(r.n)) for _, r in ft.iterrows()]
    rp.TAB(pd.DataFrame(rows, columns=["Loại luồng", "CATE trung bình: số chuyến", "CATE trung bình: tốc độ (dặm/giờ)", "Số cặp OD"]),
           "Tác động có điều kiện trung bình theo loại luồng", widths=[4.4, 4.0, 4.6, 3.0], size=10,
           align=["left", "center", "center", "center"], source="Nguồn: t47_cate_by_flowtype.csv (Chương 4).")
    cl = R.t("t44")
    clm = cl[(cl.outcome == "dlog_n") & (cl.feature == "miles_pt")].iloc[0]
    crz_ap = ap[(ap.pu_grp == "CRZ") & (ap.do_grp == "AIRPORT")].iloc[0]
    ap_crz = ap[(ap.pu_grp == "AIRPORT") & (ap.do_grp == "CRZ")].iloc[0]
    rp.PS(
        f"Chương 5 của bài giảng đặt cá nhân hóa và dự báo giá trị vòng đời khách hàng ở trung tâm của phân tích khách hàng. Dữ liệu "
        f"TLC không có định danh khách hàng, nên không thể tính giá trị vòng đời hay xác suất rời bỏ ở mức cá nhân. Đơn vị gần nhất "
        f"với \"khách hàng\" mà dữ liệu cho phép là cặp điểm đón – điểm trả, và kết quả CATE ở Chương 4 chính là một phân khúc hóa theo "
        f"độ nhạy với chi phí. Nhóm GATES nhạy nhất giảm {vn(-pct_log(gn.gate.iloc[0]), 1)}% số chuyến, nhóm ít nhạy nhất giảm "
        f"{vn(-pct_log(gn.gate.iloc[-1]), 1)}%, và phân tích CLAN cho thấy nhóm nhạy nhất có quãng đường trung bình "
        f"{vn(clm.low_group, 2)} dặm so với {vn(clm.high_group, 2)} dặm của nhóm ít nhạy nhất. Về tốc độ, mọi nhóm đều được lợi, từ "
        f"{vn(gm.gate.iloc[0], 2)} đến {vn(gm.gate.iloc[-1], 2)} dặm/giờ.",
        f"Với một nền tảng, khác biệt về độ nhạy này định hình chiến lược phân khúc. Phân khúc nhạy giá (chuyến ngắn, thời lượng ngắn) là nơi cần "
        f"khuyến mãi có mục tiêu nếu muốn giữ khối lượng. Phân khúc ít nhạy nhưng được lợi về tốc độ là nơi có thể nhấn mạnh thời gian "
        f"di chuyển ngắn hơn như một giá trị. Chuyến sân bay là trường hợp đặc biệt: số chuyến từ CRZ ra sân bay mỗi ngày thay đổi "
        f"{vn(crz_ap.chg_pct, 1, sign=True)}% và từ sân bay vào CRZ thay đổi {vn(ap_crz.chg_pct, 1, sign=True)}% giữa hai năm, gần như "
        f"không bị ảnh hưởng. Đây là phân khúc có giá trị cao, ít phương án thay thế và ít nhạy với phí.",
        "Khi doanh nghiệp có định danh khách hàng, cùng phương pháp DR-learner có thể ước lượng độ nhạy ở mức cá nhân, tức là mô hình "
        "uplift. Điều kiện chồng lấn mà Chương 4 phân tích sẽ trở thành điều kiện thiết kế: cần có khách hàng ở mọi phân khúc được và "
        "không được can thiệp, điều mà một thử nghiệm ngẫu nhiên bảo đảm nhưng một chính sách theo vùng thì không.")

    # ================================================================ 7.6
    rp.H2("7.6. Giá trị và chi phí của tài sản dữ liệu")
    rp.H3("7.6.1. Hạch toán tài nguyên")
    t = pd.DataFrame({"Hạng mục": tco["item"], "Giá trị": tco.value.map(lambda v: vn(v, 2)), "Đơn vị": tco.unit,
                      "Ghi chú": tco.note.fillna("")})
    rp.TAB(t, "Hạch toán tài nguyên của pipeline, đo từ nhật ký và siêu dữ liệu", widths=[6.6, 2.0, 1.8, 5.6], size=9.5,
           align=["left", "center", "center", "left"], source="Nguồn: t82_resource_accounting.csv.")
    g = tco.set_index("item")
    rp.PS(
        "Mục 6.5 của bài giảng đặt ra bài toán đo ROI và TCO của dự án dữ liệu lớn. Phần chi phí có thể đo chính xác từ nhật ký, và "
        "bảng trên tổng hợp các con số đó bằng đơn vị vật lý (GB, phút, lõi·giây) thay vì tiền. Lựa chọn không quy ra tiền là có chủ "
        "đích: đơn giá lưu trữ và tính toán thay đổi theo nhà cung cấp, vùng và thời điểm, còn đơn vị vật lý thì không. Người đọc có "
        "thể nhân với đơn giá hiện hành của mình.",
        f"Bảng trên cho hai kết luận. Thứ nhất, lớp Gold chỉ chiếm {vn(g.loc['Tỷ lệ Gold / Bronze theo dung lượng', 'value'], 2)}% dung "
        f"lượng của Bronze. Chi phí lưu trữ lâu dài cho mục đích phân tích vì vậy gần như không đáng kể nếu chỉ giữ Gold, và Bronze "
        f"có thể tải lại từ nguồn khi cần. Thứ hai, chi phí xử lý của bước làm sạch và tổng hợp là khoảng "
        f"{vn(g.loc['Tài nguyên xử lý Silver+Gold trên mỗi triệu dòng Bronze', 'value'], 1)} lõi·giây cho mỗi triệu dòng, còn tái lập "
        f"một bảng Gold bằng Spark chỉ khoảng {vn(g.loc['Tái lập zone_day_pu bằng Spark trên mỗi triệu dòng Silver', 'value'], 2)} lõi·giây "
        f"cho mỗi triệu dòng. Phần lớn chi phí nằm ở bước ghi lớp Silver đầy đủ, không phải ở tổng hợp. Nếu chỉ cần Gold, một kiến "
        f"trúc bỏ qua việc ghi Silver sẽ rẻ hơn nhiều, đổi lại mất khả năng truy vấn linh hoạt ở mức chuyến.")
    rp.H3("7.6.2. Định giá tài sản dữ liệu")
    rp.PS(
        f"Phía giá trị khó đo hơn. Moody và Walsh (1999) đề xuất ba cách tiếp cận định giá thông tin tương tự định giá tài sản: theo "
        f"chi phí tạo ra, theo giá thị trường và theo giá trị sử dụng. Với tài sản của đồ án, cách thứ nhất cho con số thấp, vì dữ liệu "
        f"nguồn miễn phí và chi phí xử lý nhỏ như bảng trên. Cách thứ hai không áp dụng được vì không có thị trường cho dữ liệu này. "
        f"Cách thứ ba là cách có ý nghĩa: giá trị nằm ở các quyết định mà thông tin làm thay đổi. Để có hình dung về quy mô, dữ liệu "
        f"ghi nhận {vn(rev.cbd.sum() / 1e6, 1)} triệu USD phí CBD trong năm 2025 chỉ từ hai dịch vụ; một quyết định điều chỉnh mức "
        f"phí hay cơ cấu phí theo giờ, dựa trên các ước lượng như của đồ án, tác động trực tiếp đến khoản thu này và đến thời gian "
        f"di chuyển của hàng trăm nghìn chuyến mỗi ngày.",
        "Laney (2017) lập luận rằng doanh nghiệp nên quản lý thông tin như một tài sản với các chỉ tiêu giá trị riêng, dù chuẩn mực "
        "kế toán chưa cho phép ghi nhận nó trên bảng cân đối. Trong đồ án, giá trị của dữ liệu nằm ở lớp tổng hợp đã được kiểm chứng "
        "hơn là ở dữ liệu thô: cùng tệp nguồn công khai, nhưng chỉ sau khi có pipeline có kiểm soát chất "
        "lượng, đối chứng chéo và các thiết kế nhận dạng đáng tin thì nó mới đủ độ tin cậy để dùng cho quyết định.")
    rp.H3("7.6.3. Các sản phẩm dữ liệu có thể thương mại hóa")
    prod = pd.DataFrame([
        ("Chỉ số ùn tắc theo vùng và giờ", "Cơ quan quản lý, doanh nghiệp logistics", "Bảng Gold grp_hour_day, zone_hour_month; nhánh luồng mục 5.8",
         "Gián tiếp (cải thiện quyết định) hoặc thuê bao"),
        ("Bảng tổng hợp có quyền riêng tư vi phân", "Nhà nghiên cứu, công chúng", "zone_day_pu cộng nhiễu (mục 6.8)", "Công bố mở"),
        ("Dịch vụ đánh giá chính sách theo yêu cầu", "Chính quyền, hiệp hội ngành", "Toàn bộ pipeline và thiết kế nhân quả", "Dịch vụ tư vấn"),
        ("Cảnh báo bất thường ngày", "Nhà vận hành nền tảng", "Mục 6.5 và mô hình dự báo mục 7.2", "Gián tiếp (vận hành)"),
        ("Phân khúc độ nhạy theo cặp OD", "Bộ phận giá và marketing của nền tảng", "CATE, GATES (Chương 4, mục 7.5)", "Gián tiếp (giá, khuyến mãi)"),
    ], columns=["Sản phẩm", "Người dùng", "Thành phần từ đồ án", "Hình thức giá trị"])
    rp.TAB(prod, "Các sản phẩm dữ liệu có thể xây dựng từ tài sản của đồ án", widths=[4.0, 3.6, 5.0, 3.4], size=9.5,
           align=["left"] * 4, source="Nguồn: tác giả đề xuất.")
    rp.P("Mục 6.2 và 6.3 của bài giảng phân biệt thương mại hóa trực tiếp (bán dữ liệu) và gián tiếp (dùng dữ liệu để tạo giá trị "
         "gia tăng). Với dữ liệu gốc là tài sản công, thương mại hóa trực tiếp không phù hợp. Các sản phẩm trong bảng đều thuộc loại "
         "gián tiếp hoặc dịch vụ, nơi giá trị nằm ở năng lực xử lý và phân tích chứ không ở quyền sở hữu dữ liệu. Kết quả mục 6.7 còn "
         "đặt ra một giới hạn: mọi sản phẩm công bố ra ngoài phải ở mức tổng hợp đủ thô hoặc có nhiễu, không phải dữ liệu vi mô.")

    # ================================================================ 7.7
    rp.H2("7.7. Lộ trình chiến lược dữ liệu")
    road = pd.DataFrame([
        ("1. Nền tảng (đã làm trong đồ án)", "Lakehouse ba lớp; kiểm soát chất lượng; danh mục, phả hệ, dấu băm; đối chứng hai bộ máy",
         "Đối soát 100% phân vùng; lỗi được phát hiện trước khi công bố"),
        ("2. Phân tích định kỳ", "Chạy lại theo tháng khi TLC công bố dữ liệu mới; báo cáo tự động sinh từ Gold",
         "Thời gian từ khi có dữ liệu đến báo cáo"),
        ("3. Giám sát gần thời gian thực", "Nhánh luồng (mục 5.8) nối với hàng đợi thông điệp; cảnh báo bất thường ngày",
         "Độ trễ phát hiện sự kiện"),
        ("4. Công bố có kiểm soát", "Bảng tổng hợp có quyền riêng tư vi phân; quản lý ngân sách ε", "Tổng ε đã dùng; số yêu cầu dữ liệu vi mô"),
        ("5. Mở rộng và tổ chức", "Chuyển sang cụm khi dữ liệu vượt một máy; trung tâm xuất sắc dữ liệu; văn hóa kiểm chứng",
         "Tỷ lệ quyết định có đánh giá nhân quả đi kèm"),
    ], columns=["Giai đoạn", "Nội dung", "Chỉ tiêu theo dõi"])
    rp.TAB(road, "Lộ trình chiến lược dữ liệu đề xuất cho một cơ quan quản lý vận tải", widths=[4.4, 7.2, 4.4], size=9.5,
           align=["left"] * 3, source="Nguồn: tác giả đề xuất.")
    rp.PS(
        "Mục 6.6 đến 6.8 của bài giảng bàn về văn hóa ra quyết định dựa trên dữ liệu, trung tâm xuất sắc và lộ trình chiến lược. Lộ "
        "trình trên được sắp theo thứ tự phụ thuộc: không thể giám sát theo thời gian thực nếu chưa có định nghĩa chỉ tiêu ổn định ở "
        "lớp Gold, và không thể công bố có kiểm soát nếu chưa đo được rủi ro tái nhận dạng. Giai đoạn cuối cố ý đặt việc chuyển sang "
        "cụm tính toán phân tán sau cùng, vì Chương 5 cho thấy ở quy mô hiện tại nó chưa đem lại lợi ích tốc độ.",
        "Về văn hóa, ba phát hiện chính của đồ án đều đến từ việc thử "
        "bác bỏ kết quả của chính mình: tác động lên giá cước không vượt qua giả dược (Chương 4), bảng Gold có lỗi ép kiểu (Chương 5), "
        "và mô hình dự báo tốt nhất cho phản thực tế sai (mục 7.2). Một tổ chức ra quyết định dựa trên dữ liệu vì vậy cần ghi nhận công "
        "sức kiểm chứng kết quả, bên cạnh việc đưa ra con số.")
    rp.H2("7.8. Tiểu kết Chương 7")
    rp.P(f"Chương 7 đã chuyển kết quả sang góc nhìn kinh doanh. Phí CRZ ảnh hưởng không đều giữa các hãng: Uber giảm "
         f"{vn(-u.pct, 1)}% số chuyến trong vùng, Lyft giảm {vn(-ly.pct, 1)}%, và thị phần Uber giảm {vn(-sh.coef, 2)} điểm phần trăm. "
         f"Dự báo nhu cầu có độ chính xác đủ cho vận hành, nhưng dùng làm phản thực tế thì cho kết quả phụ thuộc mạnh vào chuỗi đối "
         f"chứng, và mô hình dự báo tốt nhất lại cho kết quả sai chiều vì chuỗi đối chứng bị lan tỏa. Tác động lên số chuyến lớn dần "
         f"theo thời gian còn tác động lên tốc độ nhỏ dần, nên đánh giá sớm không đại diện cho dài hạn. Ở mức tổng hợp, giá mỗi dặm "
         f"phản ứng với tốc độ chứ không với khối lượng chuyến. Chi phí tài nguyên của toàn bộ tài sản dữ liệu nhỏ so với giá trị "
         f"quyết định mà nó hỗ trợ.")
