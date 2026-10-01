"""Chương 8. Thảo luận kết quả, hàm ý quản trị và hạn chế."""
import pandas as pd

from lib import vn, vint
from results import pct_log


def build(rp, R):
    tw = R.did("hvfhv", "ln_n")
    dd = R.did("hvfhv", "ln_n", "DDD mùa vụ")
    mp = R.did("hvfhv", "mph")
    wt = R.did("hvfhv", "wait")
    cb = R.did("hvfhv", "cbd_pt")
    rt = R.did("hvfhv", "rider_pt")
    sc = R.J["08_scm"]["standard"]
    dm = R.dml("dlog_n")
    b1 = R.od("CRZ→CRZ", "ln_n")
    rev = R.t("t16")
    tot = R.t("t52")
    fm = R.t("t09")
    en = R.t("t10")
    d26 = R.t("t26")
    crz_rider = float(d26[(d26.grp == "CRZ") & (d26.yr == 2024)].rider_cost.iloc[0] / d26[(d26.grp == "CRZ") & (d26.yr == 2024)].trips.iloc[0])

    rp.H1("CHƯƠNG 8. THẢO LUẬN KẾT QUẢ, HÀM Ý QUẢN TRỊ VÀ HẠN CHẾ")
    rp.P("Các chương 4 đến 7 đã trình bày các con số. Chương này đặt chúng vào bối cảnh: các kết quả nói gì về cơ chế của chính sách, chúng "
         "khớp hay lệch với lý thuyết và các nghiên cứu khác ở đâu, doanh nghiệp và cơ quan quản lý có thể rút ra điều gì, và giới "
         "hạn của bằng chứng nằm ở đâu.")

    rp.H2("8.1. Về kỹ thuật dữ liệu lớn")
    rp.H3("8.1.1. Quy mô vừa phải và lựa chọn công cụ")
    cat = R.t("t68_data")
    s64 = R.t("t64")
    import numpy as np
    bd = np.polyfit(s64[s64.engine == "duckdb"].n_rows / 1e6, s64[s64.engine == "duckdb"].median_s, 1)[0]
    bs = np.polyfit(s64[s64.engine == "spark_df"].n_rows / 1e6, s64[s64.engine == "spark_df"].median_s, 1)[0]
    rp.PS(
        f"Một kết luận thực tiễn của đồ án là quy mô dữ liệu của bài toán, khoảng {vn(R.t('t03').total_rows.sum() / 1e6, 0)} triệu "
        f"bản ghi và {vn(cat[cat.layer == 'Bronze'].size_mb.sum() / 1024, 1)} GB Parquet nén, nằm ở vùng mà nhiều người mặc định phải "
        f"dùng cụm Spark, nhưng thực tế xử lý được trên một máy ảo 2 lõi, 3 GB RAM trong {vn(tot.sec_total.sum() / 60, 0)} phút. Điều "
        f"kiện để làm được là ba lựa chọn đi cùng nhau: định dạng cột nén, bộ máy thực thi vector hóa có giới hạn bộ nhớ và cơ chế "
        f"tràn đĩa, và chia việc thành các phân vùng lũy đẳng. Thiếu một trong ba, bài toán sẽ vượt tài nguyên.",
        f"Chương 5 đã kiểm chứng trực tiếp nhận định này thay vì chỉ lập luận: trên cùng phần cứng, chi phí biên của Spark là "
        f"{vn(bs, 3)} giây cho mỗi triệu dòng so với {vn(bd, 3)} giây của DuckDB, và JVM cần bộ nhớ cố định lớn hơn nhiều. Nhưng Chương "
        f"5 cũng cho thấy Spark có ba vai trò mà DuckDB không thay thế được ngay cả ở quy mô này: kiểm toán độc lập (phát hiện lỗi ép "
        f"kiểu), đường nâng cấp khi dữ liệu vượt một máy, và xử lý luồng có trạng thái. Quan điểm của mục 3.8 trong bài giảng về tối ưu "
        f"chi phí tính toán vì vậy cần được hiểu đúng: chọn công cụ theo quy mô và tần suất thực tế, nhưng một bộ máy thứ hai với chi "
        f"phí thấp có thể đáng giá vì giúp kiểm soát chất lượng, dù không nhanh hơn.")
    rp.H3("8.1.2. Chất lượng dữ liệu ảnh hưởng đến kết luận nhân quả")
    q = R.t("t07")
    rp.PS(
        f"Quy tắc chất lượng loại nhiều dữ liệu nhất là vùng không xác định ({vn(100 * q[q.service == 'hvfhv'].q_bad_zone.iloc[0] / q[q.service == 'hvfhv'].n_raw.iloc[0], 2)}% "
        f"bản ghi HVFHV). Nếu tỷ lệ này thay đổi khác nhau giữa CRZ và vùng đối chứng quanh thời điểm chính sách, chẳng hạn do ứng dụng "
        f"thay đổi cách ghi vị trí, kết quả nhân quả sẽ bị ảnh hưởng. Phụ lục F cho thấy tỷ lệ loại ổn định qua 24 tháng, nhưng đây là "
        f"một điểm cần được theo dõi thường xuyên nếu pipeline được dùng để giám sát chính sách lâu dài.",
        "Cách xác định vùng xử lý từ dữ liệu thu phí cũng liên quan đến chất lượng dữ liệu. Nếu gán tay theo ranh giới đường 60, "
        "sáu vùng vắt ranh giới sẽ bị xếp nhầm vào nhóm này hay nhóm kia. Với các chính sách khác mà ranh giới không trùng với đơn vị "
        "thống kê, cách làm tương tự có thể áp dụng miễn là có một biến trong dữ liệu phản ánh trực tiếp việc chịu chính sách.")

    rp.H3("8.1.3. Chi phí tính toán như một chỉ tiêu quản trị")
    run = R.t("t08")
    rp.PS(
        f"Nhật ký phân vùng cho phép tính chính xác chi phí tính toán của pipeline: {vn(run.sec_total.sum() / 3600, 2)} giờ "
        f"thời gian chạy trên máy 2 lõi cho {len(run)} phân vùng, bộ nhớ DuckDB không vượt 1,8 GB, dung lượng lưu trữ tổng của ba lớp "
        f"khoảng {vn((R.t('t53').bronze_mb.sum() + R.t('t53').silver_mb.sum()) / 1024, 1)} GB cộng khoảng nửa gigabyte cho Gold. Các con "
        f"số này đủ nhỏ để quy trình giám sát chính sách có thể chạy định kỳ mỗi tháng trên hạ tầng rất khiêm tốn, hoặc trên một máy "
        f"ảo đám mây cỡ nhỏ trong vài giờ.",
        "Trong khung ROI và TCO của Chương 6 bài giảng, phần lớn chi phí của một dự án như thế này nằm ở công sức thiết kế, còn hạ "
        "tầng tốn rất ít: xác định vùng xử lý, lựa chọn đối chứng, xây dựng các phép thử giả dược. Một khi pipeline đã "
        "được xây dựng và kiểm chứng, chi phí biên của việc đánh giá thêm một chỉ tiêu hay thêm một tháng dữ liệu gần như bằng 0.")

    rp.H2("8.2. Về tác động lên số chuyến")
    rp.H3("8.2.1. Độ lớn so với lý thuyết")
    lo, hi = min(-sc["avg_pct_effect_post"], -pct_log(tw.coef)), max(-sc["avg_pct_effect_post"], -pct_log(tw.coef))
    rp.PS(
        f"Mức giảm số chuyến trong khoảng {vn(lo, 1)}% đến {vn(hi, 1)}% cần được so với mức tăng chi phí. Tổng chi phí hành khách "
        f"trung bình của chuyến đón trong CRZ năm 2024 là {vn(crz_rider, 2)} USD, nên riêng khoản phí 1,50 USD làm chi phí tăng khoảng "
        f"{vn(100 * 1.5 / crz_rider, 1)}%. Nếu mọi mức giảm số chuyến đều do phí, độ co giãn ngụ ý theo công thức ở mục 2.1.2 sẽ vào "
        f"khoảng {vn(-lo / (100 * 1.5 / crz_rider), 1)} đến {vn(-hi / (100 * 1.5 / crz_rider), 1)}, tức cầu rất co giãn. Con số này "
        f"cao hơn đáng kể so với độ co giãn thường được báo cáo cho dịch vụ gọi xe.",
        "Có ba cách giải thích không loại trừ nhau. Thứ nhất, chi phí thực tế tăng nhiều hơn mức phí danh nghĩa nếu giá cước cơ sở cũng "
        "tăng; đồ án không xác định được phần này nhưng phân phối chi phí hành khách cho thấy nó có thể không nhỏ. Thứ hai, cầu của "
        "chuyến ngắn trong khu trung tâm rất co giãn vì có nhiều phương án thay thế gần như miễn phí về tiền (đi bộ, xe đạp) hoặc rẻ "
        "(tàu điện ngầm, taxi với phí thấp hơn). Thứ ba, một phần mức giảm có thể là xu hướng có sẵn chưa được kiểm soát hết, như phép "
        "thử giả dược về số chuyến gợi ý. Mục 4.14.6 xác nhận điều này: với dữ liệu 2022–2025, tác động lên số chuyến nằm trong "
        "khoảng từ 0 đến khoảng 10% tùy giả định xu hướng. Vì vậy, phạm vi 6–10% là cận trên của tác động tổng hợp của phí cùng mọi "
        "phản ứng đi kèm trong năm đầu, và độ co giãn ngụ ý ở trên cũng là cận trên, không phải độ co giãn thuần theo giá.")
    rp.H3("8.2.2. So sánh với nghiên cứu khác")
    rp.PS(
        "Pandey, Guler và Gayah (2026) báo cáo mức giảm 5,95% tổng số chuyến của các công ty gọi xe. Con số này nằm ở cận dưới của "
        "phạm vi mà đồ án tìm thấy và gần với kết quả kiểm soát tổng hợp. Sự chênh lệch có thể đến từ định nghĩa nhóm xử lý và đối "
        "chứng: đồ án dùng vùng xác định từ dữ liệu thu phí, loại vùng vắt ranh giới và vùng nhỏ, và tách riêng Manhattan phía bắc. "
        "Kết quả lan tỏa cho thấy nếu nhóm đối chứng chứa nhiều vùng gần CRZ, ước lượng sẽ nhỏ hơn. Ngược lại, TWFE không trọng số "
        "đại diện cho vùng nên nhạy với các vùng CRZ nhỏ, có thể làm ước lượng lớn hơn. Hai kết quả vì vậy nhất quán về chiều và "
        "tương thích về độ lớn khi xét đến khác biệt thiết kế.",
        f"Về chuyến đi chung, cả hai nghiên cứu đều thấy mức giảm tương đối lớn hơn nhiều so với tổng số chuyến. Đồ án đo tỷ lệ chuyến "
        f"có yêu cầu đi chung giảm khoảng {vn(-100 * R.did('hvfhv', 'shared_pct').coef / R.did('hvfhv', 'shared_pct').treated_pre_mean, 0)}% "
        f"so với mức nền, cùng chiều với phát hiện của Pandey và cộng sự. Kết quả này đặt ra một câu hỏi thiết kế chính sách: phí tính "
        f"theo chuyến làm tăng chi phí trên mỗi hành khách của chuyến đi chung nhiều hơn chuyến đi riêng, trái với mục tiêu giảm số "
        f"xe trên đường.")
    rp.H3("8.2.3. Luồng nào nhạy nhất")
    rp.PS(
        f"Luồng nội vùng CRZ→CRZ giảm mạnh nhất ({vn(-pct_log(b1.coef), 1)}%). Đây là các chuyến ngắn, thường dưới vài dặm, trong khu "
        f"vực có mật độ tàu điện ngầm dày đặc. Về chính sách, nhóm này cũng là nhóm mà việc giảm chuyến ít gây thiệt hại phúc lợi nhất, "
        f"vì phương án thay thế sẵn có. Chuyến ra sân bay, ngược lại, gần như không đổi về tỷ trọng, phù hợp với độ co giãn thấp của "
        f"chuyến đi có giá trị cao và ít phương án thay thế.")

    rp.H2("8.3. Về tác động lên ùn tắc")
    rp.H3("8.3.1. Tốc độ và thời gian chờ như bằng chứng trực tiếp")
    rp.PS(
        f"Mục tiêu tuyên bố của chính sách là giảm ùn tắc. Dữ liệu gọi xe cho phép đo điều này gián tiếp qua tốc độ của chính các chuyến "
        f"đi. Mức tăng {vn(mp.coef, 2)} dặm/giờ trên nền {vn(mp.treated_pre_mean, 1)} dặm/giờ nghe có vẻ khiêm tốn, nhưng cần đặt trong "
        f"bối cảnh: tốc độ khu trung tâm vào giờ cao điểm buổi chiều chỉ khoảng 7 dặm/giờ, và mức tăng tập trung đúng vào các giờ đó. "
        f"Kết quả tốc độ có bước nhảy rõ tại mốc chính sách, vượt qua giả dược theo thời gian (giả dược ngược dấu), không nhạy với xu "
        f"hướng nhóm và được xác nhận bởi cả DML. Tuy vậy, với dữ liệu 2022–2025, độ lớn của nó phụ thuộc vào giả định về xu hướng "
        f"dài hạn: tốc độ tăng có ý nghĩa ở phần lớn đặc tả nhưng không khác 0 khi cho phép xu hướng bậc hai (mục 4.14.6). Trong hai "
        f"chỉ tiêu ùn tắc, thời gian chờ là kết quả vững hơn.",
        f"Thời gian chờ giảm {vn(-wt.coef, 2)} phút, và vẫn giảm ở mọi đặc tả xu hướng trừ đặc tả kém tin cậy nhất, là lợi ích trực tiếp cho hành khách còn lại trong hệ thống. Nó cũng cho thấy phí có "
        f"tác động qua hai kênh: đường thông thoáng hơn và nguồn cung xe tương đối dồi dào hơn so với cầu. Về mặt phúc lợi, những hành "
        f"khách vẫn đi xe gọi công nghệ trả thêm phí nhưng nhận lại thời gian di chuyển và chờ đợi ngắn hơn.")
    pw80 = R.t("t80")
    m4 = pw80[(pw80.post_weeks == pw80.post_weeks.min()) & (pw80.outcome == "mph")].iloc[0]
    rp.P(f"So với Cook và cộng sự (2025), những người dùng dữ liệu tốc độ Google Maps và báo cáo tốc độ trung bình trong vùng tăng từ "
         f"8,2 lên 9,7 dặm/giờ (khoảng 15%) trong hai tháng đầu, mức tăng của đồ án nhỏ hơn: {vn(100 * mp.coef / mp.treated_pre_mean, 1)}% "
         f"tính trung bình cả năm và {vn(100 * m4.coef / mp.treated_pre_mean, 1)}% trong {vint(m4.post_weeks)} tuần đầu. Ba lý do làm hai "
         f"con số khác nhau về định nghĩa chứ không mâu thuẫn. Thứ nhất, tốc độ của đồ án là tốc độ trung bình của cả chuyến, gồm cả "
         f"đoạn nằm ngoài vùng. Thứ hai, mức tăng giảm dần theo thời gian (giả thuyết H6, mục 4.15), nên trung bình cả năm nhỏ hơn hai "
         f"tháng đầu. Thứ ba, nhóm đối chứng của đồ án là các vùng trong cùng thành phố, vốn cũng được lợi một phần (mục 4.15.3), trong "
         f"khi Cook và cộng sự dùng các thành phố khác làm đối chứng.")
    rp.H3("8.3.2. Giới hạn của thước đo tốc độ")
    rp.PS(
        "Tốc độ chuyến gọi xe không phải tốc độ của mọi phương tiện. Chuyến gọi xe có thể chọn tuyến khác, và thành phần chuyến thay đổi "
        "khi chuyến ngắn giảm mạnh hơn chuyến dài. Đồ án giảm thiểu vấn đề thành phần bằng cách đo tốc độ trên panel cặp OD với hiệu "
        "ứng cố định cặp, nơi tuyến đường về cơ bản không đổi, và kết quả vẫn dương. Tuy nhiên, để khẳng định tác động lên toàn bộ giao "
        "thông, cần dữ liệu cảm biến giao thông hoặc dữ liệu GPS của xe buýt, nằm ngoài phạm vi của đồ án.")
    rp.H3("8.3.3. Không đồng nhất theo giờ và theo ngày")
    rp.PS(
        "Tốc độ tăng mạnh nhất vào chiều tối ngày thường và gần như không tăng vào giờ cao điểm buổi sáng hay cuối tuần. Mẫu hình này "
        "phù hợp với lý thuyết đường cong tốc độ – lưu lượng: khi lưu lượng gần mức bão hòa, giảm một ít xe tạo ra cải thiện lớn về tốc "
        "độ. Nó cũng gợi ý rằng một cơ cấu phí phân biệt theo giờ chi tiết hơn có thể đạt hiệu quả cao hơn cùng mức thu. Đây là "
        "khuyến nghị của Vickrey (1969) về phí thay đổi theo thời gian.")

    rp.H2("8.4. Về giá cước, chi phí hành khách và thu nhập tài xế")
    rp.H3("8.4.1. Vì sao không kết luận")
    rp.PS(
        f"Kết quả DiD thô cho thấy chi phí hành khách của chuyến đón trong CRZ tăng {vn(rt.coef, 2)} USD, gấp "
        f"{vn(rt.coef / cb.coef, 1)} lần phí CBD. Đồ án không dùng con số này làm kết "
        f"luận vì ba bằng chứng: xu hướng giá của CRZ đã tách khỏi vùng đối chứng trong suốt năm 2024; phép thử giả dược tháng 07/2024 "
        f"tạo ra \"tác động\" có ý nghĩa với cùng độ lớn; và đặc tả có xu hướng nhóm đảo dấu kết quả. Khi ba phép thử cùng thất bại, "
        f"hệ số DiD không còn diễn giải được như tác động nhân quả.",
        "Điều duy nhất có thể nói chắc chắn là khoản phí 1,50 USD được chuyển toàn bộ sang hóa đơn hành khách, vì nó được ghi riêng trên "
        "hóa đơn. Việc nền tảng có điều chỉnh giá cơ sở hay không, và phần điều chỉnh đó được chia thế nào giữa nền tảng và tài xế, cần "
        "một thiết kế khác: dữ liệu dài hơn trước chính sách để mô hình hóa xu hướng giá, hoặc dữ liệu từ bên trong nền tảng về thuật "
        "toán định giá.")
    rp.H3("8.4.2. Ý nghĩa đối với phương pháp")
    rp.PS(
        "Về phương pháp, trường hợp này cho thấy giả định xu hướng song song có thể đúng với một biến kết quả và sai "
        "với biến khác trong cùng một thiết kế. Số chuyến, tốc độ, thời gian chờ và giá cước đều được đo trên cùng vùng, cùng tuần, "
        "nhưng chỉ một số biến có động thái trước chính sách đủ ổn định. Việc chạy phép thử giả dược riêng cho từng biến, thay vì chỉ "
        "cho biến chính, là cần thiết. Đây cũng là tinh thần của Roth và cộng sự (2023) và Rambachan và Roth (2023) về việc đánh giá "
        "tính đáng tin của giả định xu hướng song song một cách minh bạch.")

    rp.H2("8.5. Về hiệu ứng lan tỏa")
    rp.PS(
        "Mức giảm lan ra các vùng lân cận và nhỏ dần theo khoảng cách. Có hai cách đọc. Cách thứ nhất là lan tỏa qua mạng lưới chuyến "
        "đi: nhiều chuyến từ các vùng lân cận có đích trong CRZ, nên chịu phí và giảm theo. Cách thứ hai là lan tỏa hành vi: hành khách "
        "và tài xế thay đổi thói quen ở cả khu vực xung quanh. Dữ liệu cho thấy cách thứ nhất chiếm phần lớn, vì phía điểm trả, số chuyến "
        "của khách đến từ ngoài CRZ trả ở dải lân cận giảm ít hơn nhiều so với CRZ, trong khi số chuyến từ CRZ trả ở ngay ngoài ranh "
        "giới lại tăng.",
        "Về phương pháp, kết quả lan tỏa là cảnh báo quan trọng cho mọi đánh giá dùng các vùng lân cận làm đối chứng. Với CRZ, dùng "
        "Manhattan phía bắc làm đối chứng cho mức giảm chỉ khoảng một nửa so với dùng quận ngoài. Một nghiên cứu chỉ dùng Manhattan phía "
        "bắc với lập luận \"đó là các vùng tương đồng nhất\" sẽ đánh giá thấp tác động một cách có hệ thống.")

    rp.H2("8.6. Về học máy nhân quả")
    rp.H3("8.6.1. Chồng lấn là vấn đề trung tâm")
    fu = R.dml("dlog_n", "đầy đủ")
    rp.PS(
        f"Ứng dụng DML trong đồ án cho thấy khi áp dụng học máy nhân quả cho chính sách không gian, chồng lấn là vấn đề khó hơn "
        f"việc chọn thuật toán. Với bộ biến đầy đủ, AUC của mô hình xu hướng là {vn(fu.auc_propensity, 3)}; mô hình \"biết\" gần như "
        f"chắc chắn cặp nào chạm CRZ. Trong tình huống đó, mọi ước lượng dựa trên trọng số xu hướng chỉ đại diện cho một tập con rất nhỏ "
        f"và đặc biệt. Báo cáo ước lượng mà không báo cáo chồng lấn sẽ gây hiểu nhầm.",
        f"Lựa chọn của đồ án là dùng bộ biến rút gọn chỉ gồm đặc trưng chuyến đi. Lựa chọn này có cái giá: nếu có yếu tố gắn với vị trí "
        f"vừa ảnh hưởng đến xu hướng số chuyến vừa tương quan với việc chạm CRZ, ước lượng sẽ chệch. Việc kết quả DML "
        f"({vn(-pct_log(dm.aipw_ate), 1)}%) nằm trong khoảng của các thiết kế DiD và SCM là một kiểm tra chéo hữu ích, nhưng không thay "
        f"thế được giả định.")
    rp.H3("8.6.2. Giá trị của CATE")
    rp.PS(
        "Kiểm định BLP xác nhận có không đồng nhất thật. GATES cho thấy mọi nhóm đều giảm số chuyến và tăng tốc độ, chỉ khác độ lớn. Đặc "
        "trưng giải thích sự khác biệt là quãng đường, thời lượng, tỷ trọng chuyến đêm và mức tip. Với doanh nghiệp nền tảng, thông tin "
        "này có giá trị trực tiếp: nó cho biết phân khúc chuyến nào mất khách nhiều nhất khi chi phí tăng, và vì vậy cần chính sách giá "
        "hoặc khuyến mãi bù đắp. Đây là dạng phân tích uplift được đề cập ở Chương 5 của bài giảng, áp dụng cho một cú sốc chi phí thay "
        "vì một chiến dịch marketing.")

    rp.H2("8.7. Hàm ý quản trị và chính sách")
    rp.H3("8.7.1. Đối với cơ quan quản lý")
    rp.BUL([
        f"Phí đạt được mục tiêu giảm ùn tắc ở mức đo được qua tốc độ và thời gian chờ, và tạo nguồn thu đáng kể: riêng hai dịch vụ "
        f"HVFHV và taxi vàng ghi nhận {vn(rev.cbd.sum() / 1e6, 1)} triệu USD phí trong dữ liệu năm 2025.",
        "Cơ cấu phí theo chuyến đang bất lợi cho chuyến đi chung. Có thể xem xét giảm phí cho chuyến đi chung được ghép thành công, "
        "để phí phản ánh đúng số xe trên đường thay vì số giao dịch.",
        "Tốc độ tăng không đều theo giờ. Một cơ cấu phí phân biệt theo giờ chi tiết hơn cho xe gọi công nghệ có thể tạo cải thiện lớn "
        "hơn với cùng mức thu.",
        "Cần giám sát các vùng ngay ngoài ranh giới, nơi có dấu hiệu tăng chuyến trả khách từ CRZ, để phát hiện sớm ùn tắc dịch chuyển.",
        "Dữ liệu chuyến đi công khai của TLC, cùng một pipeline như đồ án, đủ để giám sát chính sách gần như theo thời gian thực với chi "
        "phí rất thấp.",
    ])
    rp.H3("8.7.2. Đối với doanh nghiệp nền tảng")
    rp.BUL([
        "Chuyến ngắn nội vùng và chuyến đêm là phân khúc nhạy nhất; đây là nơi mất thị phần sang taxi, tàu điện ngầm hoặc đi bộ.",
        "Thời gian chờ giảm trong CRZ có nghĩa là xe dư thừa tương đối; điều phối xe sang vùng lân cận hoặc giờ khác có thể cải thiện "
        "thu nhập theo giờ của tài xế.",
        "Taxi vàng, với phí bằng một nửa, là đối thủ được lợi. Chiến lược giá cho chuyến ngắn trong CRZ cần tính đến chênh lệch phí này.",
        "Tác động không đều giữa các hãng (mục 7.1): hãng mất nhiều chuyến hơn cần xem lại cơ cấu khách hàng và chính sách chuyển phí.",
        "Đánh giá kiểu \"thực tế so với dự báo\" dễ sai khi chuỗi đối chứng bị ảnh hưởng (mục 7.2); cần thiết kế nhân quả cho các quyết định lớn.",
    ])
    rp.H3("8.7.3. Đối với phân tích dữ liệu trong doanh nghiệp")
    rp.PS(
        "Ngoài nội dung chính sách, đồ án minh họa một quy trình mà các doanh nghiệp có dữ liệu giao dịch quy mô lớn có thể áp dụng để "
        "đánh giá bất kỳ thay đổi nào có ranh giới rõ về không gian hoặc thời gian: một khoản thuế mới, một thay đổi giá theo vùng, một "
        "đối thủ mới vào thị trường. Các thành phần gồm pipeline Lakehouse có kiểm soát chất lượng, xác định nhóm chịu tác động từ chính "
        "dữ liệu, nhiều thiết kế nhận dạng đối chiếu nhau và phép thử giả dược cho từng chỉ tiêu. Trong thuật ngữ của Chương 6 của bài "
        "giảng, đây là một cách biến dữ liệu thành giá trị ra quyết định có thể đo lường được.")

    rp.H2("8.8. Hạn chế của nghiên cứu")
    lim = pd.DataFrame([
        ("Năm gốc 2022 còn chịu ảnh hưởng COVID-19", "Xu hướng trước chính sách có thể là phục hồi sau đại dịch, không kéo dài tuyến tính",
         "Đã kiểm tra bằng sáu đặc tả năm gốc và dạng xu hướng (mục 4.14.6); cần dữ liệu 2019 làm mốc thứ hai"),
        ("Tác động lên số chuyến phụ thuộc giả định xu hướng", "Ước lượng từ 0 đến khoảng 10% tùy đặc tả; điểm gãy RR nhỏ",
         "Thêm vùng đối chứng tương đồng; dữ liệu lưu lượng xe con"),
        ("Silver 2022–2023 không lưu bền cho phần lớn tháng", "Muốn kiểm toán từng chuyến phải dựng lại từ Bronze",
         "Đã kiểm chứng dựng lại Gold từ Bronze khớp với Gold đang dùng (bước 21, mục 3.2.4)" if "t96_regeneration_check" in R.T
         else "Lưu Silver trên máy có RAM lớn hơn hoặc lưu trữ đám mây"),
        ("Không có dữ liệu xe con cá nhân", "Không đo trực tiếp lưu lượng giao thông vào vùng", "Kết hợp dữ liệu cảm biến giao thông, dữ liệu thu phí của MTA"),
        ("Tốc độ đo trên chuyến gọi xe", "Có thể khác tốc độ của toàn bộ phương tiện", "Dùng dữ liệu GPS xe buýt MTA"),
        ("Giá cước chịu xu hướng có sẵn", "Không kết luận được về phân bổ gánh nặng; vấn đề này được đặt ngoài phạm vi", "Dữ liệu giá theo chuyến của nền tảng; thiết kế có nhóm đối chứng ngoài New York"),
        ("Tương quan không gian giữa các vùng", "Sai số Conley và hai chiều lớn hơn sai số theo vùng 2–3,5 lần; thu nhập tài xế/dặm mất ý nghĩa", "Đã báo cáo ở mục 4.14.6; các kết quả chính không đổi"),
        ("Chồng lấn thấp trong DML", "Ước lượng chỉ đại diện cho vùng chồng lấn", "Đã kiểm tra ngưỡng cắt và ước lượng ATO (mục 4.14.6); thiết kế ở cấp chuyến"),
        ("Không quan sát hành khách cá nhân", "Không đo được phương thức thay thế cụ thể", "Kết hợp dữ liệu lượt quẹt thẻ tàu điện ngầm"),
        ("Phí ghi nhận khác phí thực thu", "Doanh thu phí chỉ là ước lượng từ hóa đơn", "Đối chiếu với báo cáo tài chính của MTA"),
        ("Taxi vàng có biến động riêng ở quận ngoài", "Kết quả taxi vàng kém ổn định", "Phân tích riêng theo nhà cung cấp và loại chuyến"),
        ("Tỷ lệ loại bỏ của taxi vàng tăng từ 01/2025", "Mẫu Silver taxi vàng năm 2025 có thể bị chọn lọc", "Phân tích độ nhạy với quy tắc giá cước (mục 6.4.2)"),
        ("Spark chỉ chạy trên một nút", "Chưa đo được khả năng mở rộng theo số nút", "Chạy lại bước 15 trên cụm đám mây"),
        ("Quyền riêng tư vi phân ở mức chuyến", "Không bảo vệ hành khách đi nhiều chuyến", "Cần định danh người dùng để giới hạn đóng góp"),
        ("Dự báo phản thực tế phụ thuộc chuỗi đối chứng", "Không dùng được làm ước lượng nhân quả chính", "Chọn chuỗi đối chứng theo kiểm tra lan tỏa"),
    ], columns=["Hạn chế", "Ảnh hưởng đến kết luận", "Hướng khắc phục"])
    rp.TAB(lim, "Tổng hợp các hạn chế, ảnh hưởng và hướng khắc phục", widths=[4.4, 6.0, 5.6], size=10,
           align=["left", "left", "left"], source="Nguồn: tác giả tổng hợp.")
    rp.PS(
        "Hạn chế quan trọng nhất là cách xử lý xu hướng trước chính sách. Dữ liệu 2022–2023 đã được bổ sung và cho thấy số chuyến CRZ "
        "giảm tương đối từ trước, nhưng năm gốc 2022 còn chịu ảnh hưởng của làn sóng Omicron và quá trình phục hồi sau đại dịch. Nếu "
        "xu hướng đó là phục hồi đang chậm lại thì trừ đi xu hướng tuyến tính sẽ làm tác động bị ước lượng thấp; nếu nó là dịch chuyển "
        "lâu dài của hoạt động ra khỏi khu trung tâm thì các ước lượng một năm sẽ bị phóng đại. Dữ liệu TLC không phân biệt được hai "
        "khả năng này. Mục 4.14.6 cho thấy riêng việc chọn năm gốc và dạng xu hướng đã làm ước lượng thay đổi từ khoảng 0 đến "
        "khoảng 10%, nên đồ án không đưa ra một con số cụ thể cho tác động lên số chuyến; khoảng 6–10% của các thiết kế một năm là cận "
        "trên.",
        "Các hạn chế còn lại chủ yếu liên quan đến phạm vi dữ liệu TLC. Chúng không làm thay đổi các kết luận chính về chiều của tác "
        "động lên tốc độ và thời gian chờ, nhưng giới hạn khả năng mở rộng kết luận sang toàn bộ hệ thống giao thông.")
    rp.H2("8.9. Tiểu kết Chương 8")
    rp.P("Chương 8 đã thảo luận ý nghĩa của các kết quả. Về kỹ thuật, bài toán quy mô hàng trăm triệu bản ghi có thể xử lý trên máy "
         "cá nhân khi kết hợp đúng các lựa chọn kiến trúc. Về chính sách, phí CRZ làm giảm thời gian chờ, kết quả vững nhất của đồ án, "
         "và nhiều khả năng làm tăng tốc độ; mức giảm số chuyến gọi xe trùng phần lớn với xu hướng có sẵn từ 2022, nên độ lớn của nó "
         "chưa kết luận chắc chắn. Về phương pháp, việc kiểm tra giả dược cho từng chỉ "
         "tiêu và kiểm tra chồng lấn trong học máy nhân quả là cần thiết để phân biệt kết quả đáng tin với kết quả chỉ phản ánh xu "
         "hướng có sẵn.")
