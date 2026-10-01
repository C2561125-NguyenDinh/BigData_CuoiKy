"""Chương 2. Cơ sở lý thuyết và tổng quan nghiên cứu."""
import pandas as pd


def build(rp, R):
    rp.H1("CHƯƠNG 2. CƠ SỞ LÝ THUYẾT VÀ TỔNG QUAN NGHIÊN CỨU")
    rp.P("Chương này trình bày bốn nhóm cơ sở lý thuyết mà đồ án dựa vào: kinh tế học định giá ùn tắc và phân bổ gánh "
         "nặng của phí; đặc điểm của thị trường gọi xe công nghệ; kiến trúc và kỹ thuật dữ liệu lớn; và các phương pháp "
         "suy luận nhân quả từ dữ liệu quan sát, bao gồm học máy nhân quả. Phần cuối tổng quan các nghiên cứu thực nghiệm "
         "liên quan và rút ra khoảng trống mà đồ án hướng tới.")

    rp.H2("2.1. Kinh tế học định giá ùn tắc")
    rp.H3("2.1.1. Ùn tắc như một ngoại tác")
    rp.PS(
        "Xét một đoạn đường có lưu lượng q xe mỗi giờ. Chi phí thời gian trung bình mà mỗi người đi đường phải chịu, ký hiệu "
        "c(q), tăng theo q vì xe càng đông thì tốc độ càng chậm. Mỗi người khi quyết định có đi hay không chỉ so sánh lợi ích "
        "của chuyến đi với c(q). Tuy nhiên, chiếc xe thứ q còn làm tăng thời gian của q − 1 xe khác. Chi phí biên xã hội vì "
        "vậy lớn hơn chi phí trung bình:")
    rp.EQ("MSC(q) = c(q) + q · c′(q)")
    rp.PS(
        "Thành phần q·c′(q) là chi phí ngoại tác. Ở trạng thái cân bằng tự do, lưu lượng dừng tại điểm mà lợi ích biên của "
        "chuyến đi cuối cùng bằng c(q), cao hơn mức tối ưu xã hội q* tại đó lợi ích biên bằng MSC(q). Walters (1961) là người "
        "đầu tiên ước lượng khoảng chênh này bằng đường cong tốc độ – lưu lượng thực nghiệm. Vickrey (1969) mở rộng sang mô hình "
        "ùn tắc theo thời gian, trong đó người đi đường có thể dời giờ xuất phát, và chỉ ra rằng phí thay đổi theo thời gian có "
        "thể xóa gần hết hàng đợi mà không làm giảm nhiều số chuyến.",
        "Mức phí Pigou tối ưu bằng đúng chi phí ngoại tác tại q*:")
    rp.EQ("τ* = q* · c′(q*)")
    rp.PS(
        "Trong thực tế, cơ quan quản lý không biết chính xác c(q) và đường cầu, nên mức phí được chọn theo cân nhắc thực tiễn: "
        "đủ lớn để thay đổi hành vi, đủ đơn giản để người dân hiểu, và tạo đủ nguồn thu cho mục tiêu đầu tư. Phí CRZ ở New York "
        "được thiết kế chủ yếu theo ràng buộc nguồn thu cho hệ thống giao thông công cộng, nên không có lý do để kỳ vọng mức phí "
        "này trùng với mức Pigou lý thuyết (Small và Verhoef, 2007).")
    rp.H3("2.1.2. Phản ứng của nhu cầu và độ co giãn")
    rp.PS(
        "Tác động của phí lên số chuyến phụ thuộc vào độ co giãn của cầu theo tổng chi phí chuyến đi. Với chuyến gọi xe, tổng "
        "chi phí gồm giá cước, các khoản phí, tiền tip và thời gian chờ. Nếu gọi p là tổng chi phí bằng tiền và ε là độ co giãn "
        "của cầu theo giá, thì một khoản phí τ được chuyển hoàn toàn sang hành khách sẽ làm số chuyến thay đổi xấp xỉ:")
    rp.EQ("Δq / q ≈ ε · τ / p")
    rp.PS(
        "Công thức này cho một phép kiểm tra hợp lý thô. Với chi phí trung bình của chuyến chạm CRZ khoảng vài chục USD và phí "
        "1,50 USD, mức tăng chi phí danh nghĩa chỉ vài phần trăm. Một mức giảm số chuyến lớn hơn nhiều so với mức tăng này hàm ý "
        "hoặc cầu rất co giãn, hoặc chi phí thực tế tăng nhiều hơn mức phí danh nghĩa, hoặc có yếu tố khác cùng lúc làm giảm nhu "
        "cầu. Đồ án dùng lập luận này để đối chiếu các ước lượng thực nghiệm ở Chương 8.",
        "Cầu đi lại còn có thể phản ứng theo những kênh không làm giảm số người đi: đổi phương thức sang tàu điện ngầm hoặc taxi "
        "(phí taxi thấp hơn), đổi điểm đón hoặc điểm trả ra ngoài ranh giới, đổi giờ đi, hoặc gộp nhiều việc vào một chuyến. Các "
        "kênh này tạo ra hiệu ứng lan tỏa không gian và thay thế giữa các dịch vụ, là lý do đồ án phân tích cả vùng lân cận và "
        "taxi vàng.")
    rp.H3("2.1.3. Phân bổ gánh nặng của phí")
    rp.PS(
        "Lý thuyết phân bổ gánh nặng thuế (tax incidence) cho biết người chịu thuế thực sự không phụ thuộc vào ai là người nộp "
        "mà phụ thuộc vào độ co giãn tương đối của cung và cầu. Trong thị trường cạnh tranh, tỷ lệ chuyển giá sang người mua "
        "bằng ε_S / (ε_S − ε_D), với ε_S là độ co giãn cung và ε_D là độ co giãn cầu (ε_D < 0). Khi cung rất co giãn, người mua "
        "gánh gần hết. Thị trường gọi xe không phải thị trường cạnh tranh hoàn hảo: nền tảng đặt giá bằng thuật toán, tài xế "
        "được trả theo công thức riêng và cơ quan quản lý quy định mức thu nhập tối thiểu của tài xế. Với độc quyền hoặc cạnh "
        "tranh không hoàn hảo, tỷ lệ chuyển giá có thể vượt 1 (over-shifting) nếu đường cầu đủ lồi.",
        "Với phí CRZ, khoản 1,50 USD được ghi riêng trên hóa đơn và cộng vào tổng tiền của hành khách, nên phần chuyển giá trực "
        "tiếp là hoàn toàn. Câu hỏi thực chất là nền tảng có điều chỉnh giá cước cơ sở và phần trả cho tài xế hay không. Đây là "
        "câu hỏi thực nghiệm mà, như Chương 4 sẽ cho thấy, rất khó trả lời vì trong cùng giai đoạn còn nhiều yếu tố khác tác động "
        "lên giá cước.")

    rp.H2("2.2. Kinh nghiệm quốc tế về phí ùn tắc theo vùng")
    rp.H3("2.2.1. Singapore, London và Stockholm")
    rp.PS(
        "Singapore là nơi đầu tiên áp dụng phí vào khu trung tâm, từ năm 1975 với hệ thống giấy phép khu vực, sau đó chuyển "
        "sang thu phí điện tử (Electronic Road Pricing) năm 1998 với mức phí thay đổi theo giờ và theo đoạn đường. London áp "
        "dụng phí ngày cho khu trung tâm từ tháng 2/2003. Leape (2006) tổng kết rằng lưu lượng xe vào vùng giảm rõ rệt ngay "
        "sau khi áp dụng và thời gian di chuyển trong vùng được cải thiện trong những năm đầu, nhưng một phần cải thiện về tốc "
        "độ bị xói mòn về sau do dung lượng đường bị dành cho các mục đích khác.",
        "Stockholm là trường hợp được nghiên cứu kỹ nhất vì có giai đoạn thử nghiệm, trưng cầu ý dân rồi mới áp dụng chính thức. "
        "Eliasson (2009) thực hiện phân tích chi phí – lợi ích và kết luận lợi ích về thời gian vượt chi phí vận hành hệ thống. "
        "Börjesson và cộng sự (2012) theo dõi năm năm sau và thấy mức giảm lưu lượng được duy trì, trong khi sự ủng hộ của người "
        "dân tăng lên sau khi họ trải nghiệm kết quả. Một bài học chung là tác động ban đầu lên lưu lượng thường đáng kể, còn tác "
        "động lên tốc độ phụ thuộc vào cách dung lượng đường được quản lý sau đó.")
    rp.H3("2.2.2. Điểm khác biệt của trường hợp New York")
    rp.PS(
        "Trường hợp New York có ba khác biệt đáng lưu ý. Thứ nhất, thị phần của xe gọi công nghệ trong giao thông khu trung tâm "
        "rất lớn, trong khi ở London năm 2003 hay Stockholm năm 2006 các nền tảng này chưa tồn tại. Thứ hai, taxi và xe cho thuê "
        "không trả phí ngày mà trả theo từng chuyến, tức là phí đánh trực tiếp vào giao dịch dịch vụ thay vì vào phương tiện. "
        "Thứ ba, dữ liệu từng chuyến của các dịch vụ này được công bố công khai theo tháng, cho phép đánh giá chính sách với độ "
        "phân giải mà các nghiên cứu trước không có.")

    rp.H2("2.3. Thị trường gọi xe công nghệ")
    rp.H3("2.3.1. Cấu trúc thị trường hai phía")
    rp.PS(
        "Nền tảng gọi xe là thị trường hai phía: một phía là hành khách, phía kia là tài xế, nền tảng đứng giữa ghép cặp và đặt "
        "giá. Cramer và Krueger (2016) cho thấy tài xế Uber có tỷ lệ thời gian chở khách cao hơn taxi truyền thống, một phần nhờ "
        "thuật toán ghép cặp. Cohen và cộng sự (2016) dùng dữ liệu hệ số tăng giá của Uber để ước lượng đường cầu và thặng dư "
        "người tiêu dùng, cho thấy dữ liệu giao dịch quy mô lớn có thể trả lời những câu hỏi kinh tế học vốn cần thực nghiệm tốn "
        "kém.",
        "Trong thị trường hai phía, một cú sốc chi phí ở phía hành khách lan sang phía tài xế qua thời gian chờ và mức độ sử dụng "
        "xe. Nếu nhu cầu trong CRZ giảm, số xe rảnh tăng, thời gian chờ của hành khách giảm, còn thu nhập theo giờ của tài xế có "
        "thể giảm dù thu nhập theo chuyến không đổi. Vì vậy thời gian chờ là chỉ tiêu cần theo dõi bên cạnh tốc độ.")
    rp.H3("2.3.2. Gọi xe và ùn tắc")
    rp.PS(
        "Erhardt và cộng sự (2019) ước lượng rằng sự phát triển của các công ty gọi xe tại San Francisco góp phần đáng kể vào mức "
        "gia tăng ùn tắc giai đoạn 2010–2016, qua việc tăng quãng đường xe chạy, kể cả quãng đường chạy không để đón khách. Kết "
        "quả này là một trong những lập luận chính để đưa xe gọi công nghệ vào diện chịu phí ùn tắc. Ở chiều ngược lại, tốc độ "
        "của xe gọi công nghệ phản ánh trực tiếp tình trạng đường phố, nên dữ liệu chuyến đi của chúng là nguồn quan sát ùn tắc có "
        "độ phủ rộng.")
    rp.H3("2.3.3. Khung quy định tại New York")
    rp.PS(
        "Tại New York, TLC quản lý giấy phép và quy định mức thu nhập tối thiểu của tài xế HVFHV theo công thức dựa trên thời "
        "gian và quãng đường, được điều chỉnh định kỳ. Từ năm 2019, các chuyến đi qua Manhattan phía nam đường 96 đã chịu phụ thu "
        "ùn tắc cấp bang (2,75 USD cho xe cho thuê và 2,50 USD cho taxi). Các quy định này tạo ra những thay đổi giá và thu nhập "
        "không liên quan đến phí CRZ và là nguồn gây nhiễu mà thiết kế nhận dạng phải tính đến.")

    rp.H2("2.4. Kiến trúc và hạ tầng dữ liệu lớn")
    rp.H3("2.4.1. Từ kho dữ liệu đến Lakehouse")
    rp.PS(
        "Chương 1 của bài giảng môn học mô tả ba kỷ nguyên của kiến trúc dữ liệu doanh nghiệp. Kho dữ liệu (data warehouse) tập "
        "trung dữ liệu có cấu trúc chặt chẽ, tối ưu cho báo cáo nhưng tốn kém và chậm thích ứng. Hồ dữ liệu (data lake) trên HDFS "
        "hoặc lưu trữ đối tượng cho phép lưu dữ liệu thô với nguyên lý schema-on-read, nhưng dễ trở thành \"đầm lầy dữ liệu\" khi "
        "thiếu quản trị. Lakehouse kết hợp hai hướng: dữ liệu nằm trên lưu trữ rẻ ở định dạng mở, còn lớp siêu dữ liệu và bộ máy "
        "truy vấn cung cấp tính năng quản lý lược đồ và hiệu năng gần với kho dữ liệu (Armbrust và cộng sự, 2021).",
        "Mô hình medallion là cách tổ chức dữ liệu phổ biến trong Lakehouse. Lớp Bronze chứa dữ liệu thô đúng như khi thu nhận, "
        "không sửa đổi, để luôn có thể xử lý lại. Lớp Silver chứa dữ liệu đã làm sạch, chuẩn hóa lược đồ và gắn khóa nghiệp vụ. "
        "Lớp Gold chứa các bảng tổng hợp phục vụ trực tiếp cho phân tích và mô hình. Đồ án áp dụng đúng mô hình này.")
    rp.H3("2.4.2. Tách rời lưu trữ và tính toán")
    rp.PS(
        "Nguyên lý tách rời lưu trữ và tính toán (mục 1.7 của bài giảng) cho phép lưu dữ liệu ở một nơi và đưa bộ máy tính toán "
        "đến đọc khi cần. Trong đồ án, dữ liệu nằm dưới dạng tệp Parquet trên ổ đĩa, còn DuckDB được khởi tạo trong từng tiến "
        "trình Python, đọc tệp, tính toán rồi giải phóng bộ nhớ. Không có máy chủ cơ sở dữ liệu thường trực. Cách làm này tương "
        "tự mô hình serverless trên đám mây, chỉ khác ở quy mô.")
    rp.H3("2.4.3. Định dạng lưu trữ dạng cột")
    rp.PS(
        "Apache Parquet là định dạng lưu trữ dạng cột, kế thừa ý tưởng lưu trữ lồng nhau của hệ thống Dremel (Melnik và cộng sự, "
        "2010). Một tệp Parquet được chia thành các nhóm dòng (row group); trong mỗi nhóm dòng, dữ liệu của từng cột được lưu liền "
        "nhau thành các khối (column chunk), mã hóa (dictionary, run-length) rồi nén. Chân tệp chứa lược đồ và thống kê min/max "
        "của từng cột trong từng nhóm dòng.",
        "Cấu trúc này mang lại ba lợi ích cho phân tích. Thứ nhất là cắt tỉa cột (column pruning): truy vấn chỉ đọc các cột cần "
        "dùng. Thứ hai là đẩy điều kiện lọc xuống (predicate pushdown): bộ máy so sánh điều kiện với thống kê min/max để bỏ qua "
        "cả nhóm dòng không thể thỏa mãn. Thứ ba là nén hiệu quả vì dữ liệu cùng kiểu, cùng miền giá trị nằm cạnh nhau. Mục 2.3 "
        "của bài giảng so sánh Parquet với Avro (dạng dòng, phù hợp ghi luồng) và ORC (dạng cột, phổ biến trong hệ sinh thái "
        "Hive). Đồ án đo trực tiếp các lợi ích này trên dữ liệu thật ở Chương 4.")
    rp.H3("2.4.4. Bộ máy xử lý trong bộ nhớ và thực thi vector hóa")
    rp.PS(
        "MapReduce (Dean và Ghemawat, 2008) đặt nền móng cho xử lý phân tán nhưng ghi dữ liệu trung gian xuống đĩa sau mỗi bước. "
        "Spark (Zaharia và cộng sự, 2016) giữ dữ liệu trong bộ nhớ và phục hồi lỗi bằng phả hệ phép biến đổi, nhanh hơn nhiều cho "
        "các tác vụ lặp. Ở quy mô một máy, các bộ máy phân tích nhúng như DuckDB (Raasveldt và Mühleisen, 2019) áp dụng thực thi "
        "vector hóa: mỗi toán tử xử lý một lô vài nghìn giá trị của cùng một cột, tận dụng bộ nhớ đệm CPU, và có thể tràn dữ liệu "
        "ra đĩa khi vượt giới hạn bộ nhớ. Apache Arrow chuẩn hóa định dạng cột trong bộ nhớ, cho phép DuckDB, pandas và PyArrow "
        "trao đổi dữ liệu mà không phải sao chép.",
        "Với bài toán của đồ án, dữ liệu một tháng HVFHV (khoảng 20 triệu dòng) vừa trên một máy, nhưng 24 tháng thì không. Chiến "
        "lược phù hợp là xử lý theo phân vùng với DuckDB và giới hạn bộ nhớ làm bộ máy chính. Đây cũng là tinh thần của mục 3.6 và "
        "3.8 trong bài giảng: chọn công cụ theo quy mô thực tế để tối ưu chi phí tính toán. Đồ án vẫn chạy Spark trên cùng dữ liệu "
        "(Chương 5) để kiểm chứng nhận định này bằng số đo và để có một bộ máy độc lập đối chứng kết quả.")
    rp.H3("2.4.5. Điều phối, tính lũy đẳng và khả năng tái lập")
    rp.PS(
        "Một pipeline dữ liệu lớn cần chạy lại được từng phần mà không làm hỏng kết quả, gọi là tính lũy đẳng (idempotency). Trong "
        "đồ án, mỗi phân vùng Silver và Gold được xác định duy nhất bởi bộ (dịch vụ, tháng, khúc) và được ghi đè hoàn toàn khi chạy "
        "lại. Mỗi phân vùng ghi một tệp nhật ký JSON chứa số dòng, số lỗi theo quy tắc và thời gian từng bước. Trình điều phối "
        "đơn giản chỉ chạy những phân vùng chưa có nhật ký. Cách làm này đạt được các tính chất quan trọng nhất của công cụ điều "
        "phối như Airflow (mục 3.7 của bài giảng) mà không cần hạ tầng riêng.")

    rp.H3("2.4.6. Định dạng bảng giao dịch: Delta Lake và Apache Iceberg")
    rp.PS(
        "Parquet là định dạng tệp, không phải định dạng bảng. Khi nhiều tệp Parquet cùng tạo thành một bảng, cần một lớp siêu dữ liệu "
        "để biết tệp nào thuộc phiên bản nào của bảng, lược đồ hiện hành là gì và thao tác ghi nào đã hoàn tất. Delta Lake và Apache "
        "Iceberg, được trình bày ở mục 2.4 của bài giảng, giải quyết việc này bằng nhật ký giao dịch: mỗi lần ghi tạo một bản ghi mới "
        "trong nhật ký, liệt kê các tệp được thêm và bớt. Nhờ đó bảng có tính nguyên tử (ACID), cho phép truy vấn theo phiên bản cũ "
        "(time travel) và tiến hóa lược đồ có kiểm soát.",
        "Đồ án không dùng Delta Lake hay Iceberg vì hai lý do. Thứ nhất, dữ liệu TLC được công bố theo tháng và không bị sửa sau đó, "
        "nên bài toán chỉ có thao tác ghi thêm theo phân vùng, không có cập nhật hay xóa. Thứ hai, mỗi phân vùng Silver và Gold được "
        "ghi đè hoàn toàn bởi một tiến trình duy nhất, nên không có xung đột ghi đồng thời. Trong điều kiện đó, quy ước đặt tên theo "
        "phân vùng Hive kết hợp nhật ký JSON cho từng phân vùng đã đủ bảo đảm tính nhất quán. Nếu pipeline được mở rộng để nhiều người "
        "cùng ghi, hoặc để sửa dữ liệu lịch sử, chuyển sang một định dạng bảng giao dịch sẽ là bước cần thiết.")
    rp.H3("2.4.7. Xử lý luồng và giám sát gần thời gian thực")
    rp.PS(
        "Mục 3.3 của bài giảng giới thiệu Apache Flink cho xử lý luồng thời gian thực. Với đánh giá chính sách, độ trễ theo tháng của "
        "dữ liệu TLC là chấp nhận được, nên xử lý theo lô là lựa chọn tự nhiên. Tuy nhiên, nếu cơ quan quản lý muốn giám sát chính sách "
        "hằng ngày, chẳng hạn phát hiện sớm ùn tắc dịch chuyển ra ngoài ranh giới, kiến trúc có thể được bổ sung một nhánh luồng: dữ "
        "liệu chuyến đi từ các nền tảng được đẩy qua hàng đợi thông điệp, Flink tính các chỉ tiêu cửa sổ trượt (số chuyến, tốc độ theo "
        "vùng và giờ), còn lớp Lakehouse tiếp tục là nơi lưu trữ dài hạn và tính toán nhân quả định kỳ. Các bảng Gold của đồ án được "
        "thiết kế chỉ chứa đại lượng cộng được, nên có thể được cập nhật tăng dần từ luồng mà không phải tính lại từ đầu.")
    rp.H3("2.4.8. Chi phí sở hữu và giá trị của dữ liệu")
    rp.PS(
        "Chương 6 của bài giảng nhấn mạnh việc đo lường tổng chi phí sở hữu (TCO) và lợi tức đầu tư (ROI) của dự án dữ liệu lớn. Chi "
        "phí của một pipeline gồm lưu trữ, tính toán, nhân lực phát triển và vận hành. Giá trị đến từ các quyết định được cải thiện nhờ "
        "dữ liệu. Với đánh giá chính sách công, giá trị khó quy ra tiền trực tiếp, nhưng có thể nhìn qua câu hỏi: nếu không có dữ liệu "
        "và pipeline, cơ quan quản lý sẽ phải dựa vào khảo sát hoặc đếm xe tại vài điểm, tốn kém hơn nhiều và cho độ phân giải thấp "
        "hơn. Đồ án không định giá bằng tiền, nhưng báo cáo chi phí tính toán thực tế (số phút CPU, bộ nhớ, dung lượng) để làm cơ sở "
        "cho các ước tính như vậy.")

    rp.H3("2.4.9. Mô hình tính toán của Apache Spark")
    rp.PS(
        "Spark được xây dựng quanh khái niệm tập dữ liệu phân tán có khả năng phục hồi (Resilient Distributed Dataset, RDD) "
        "(Zaharia và cộng sự, 2012). Một RDD là một tập bất biến được chia thành các phân vùng nằm trên nhiều nút. Mỗi RDD ghi lại "
        "phả hệ (lineage) của nó, tức chuỗi phép biến đổi từ dữ liệu nguồn. Khi một phân vùng bị mất do nút hỏng, Spark tính lại "
        "đúng phân vùng đó theo phả hệ thay vì phải sao chép dữ liệu ra nhiều nơi như HDFS. Đây là nền tảng của nguyên lý tính toán "
        "trong bộ nhớ mà mục 3.1 của bài giảng trình bày: dữ liệu trung gian được giữ trong RAM giữa các bước, chỉ ghi xuống đĩa ở "
        "ranh giới xáo trộn.",
        "Các phép biến đổi được chia thành hai loại. Phép biến đổi hẹp (lọc, chiếu, tổng hợp cục bộ) chỉ cần dữ liệu của một phân "
        "vùng đầu vào, nên được gộp thành một giai đoạn (stage) chạy liền mạch. Phép biến đổi rộng (nhóm theo khóa, nối) cần dữ liệu "
        "từ mọi phân vùng, nên phải xáo trộn (shuffle): mỗi tác vụ ghi kết quả trung gian được chia theo giá trị băm của khóa xuống "
        "đĩa, và các tác vụ của giai đoạn sau đọc lại. Đồ thị có hướng không chu trình (DAG) của các giai đoạn là đơn vị lập lịch của "
        "Spark. Xáo trộn là thao tác tốn kém nhất, và số phân vùng xáo trộn là tham số hiệu năng quan trọng nhất mà người dùng phải "
        "chọn.",
        "Spark SQL (Armbrust và cộng sự, 2015) bổ sung một tầng cao hơn. Truy vấn viết bằng SQL hoặc API DataFrame được dịch thành "
        "cây kế hoạch logic, bộ tối ưu Catalyst áp dụng các quy tắc như đẩy điều kiện lọc xuống, cắt tỉa cột và gộp phép chiếu, rồi "
        "sinh kế hoạch vật lý. Bộ máy Tungsten sinh mã Java cho cả một giai đoạn (whole-stage code generation) thay vì gọi từng toán "
        "tử. Từ Spark 3.0, thực thi truy vấn thích nghi (Adaptive Query Execution, AQE) cho phép tối ưu lại kế hoạch giữa các giai "
        "đoạn dựa trên thống kê thật của dữ liệu trung gian, chẳng hạn gộp các phân vùng xáo trộn quá nhỏ. Với PySpark, việc chuyển "
        "dữ liệu giữa JVM và Python có thể dùng Apache Arrow để truyền theo lô cột thay vì tuần tự hóa từng dòng.")
    rp.H3("2.4.10. Xử lý luồng có cấu trúc")
    rp.PS(
        "Structured Streaming (Armbrust và cộng sự, 2018) coi một luồng dữ liệu là một bảng không giới hạn được nối thêm dòng liên "
        "tục. Người dùng viết truy vấn như trên bảng tĩnh, và Spark thực thi nó tăng dần theo các lô vi mô (micro-batch). Ba khái "
        "niệm then chốt là thời gian sự kiện (thời điểm sự việc xảy ra, khác với thời điểm dữ liệu đến), cửa sổ thời gian (nhóm các "
        "sự kiện theo khoảng thời gian cố định hoặc trượt) và mốc nước (watermark), là ngưỡng trễ tối đa mà hệ thống chờ dữ liệu đến "
        "muộn trước khi đóng một cửa sổ và giải phóng trạng thái của nó. Trạng thái và vị trí đọc của luồng được ghi vào thư mục "
        "checkpoint, cho phép chạy tiếp sau sự cố mà không tính trùng hay bỏ sót.",
        "So với Apache Flink ở mục 3.3 của bài giảng, vốn xử lý từng sự kiện với độ trễ mili giây, mô hình lô vi mô có độ trễ cao hơn "
        "nhưng dùng chung bộ máy và chung ngữ nghĩa với xử lý lô. Với bài toán giám sát chính sách, nơi độ trễ vài giây đến vài phút "
        "là chấp nhận được, lợi thế về tính thống nhất quan trọng hơn độ trễ.")

    rp.H2("2.5. Chất lượng dữ liệu và quản trị dữ liệu")
    rp.H3("2.5.1. Các chiều chất lượng dữ liệu")
    rp.PS(
        "Wang và Strong (1996) phân loại chất lượng dữ liệu theo góc nhìn người sử dụng thành các nhóm: chất lượng nội tại (chính "
        "xác, khách quan), chất lượng theo ngữ cảnh (đầy đủ, kịp thời, phù hợp), chất lượng biểu diễn và khả năng truy cập. Với dữ "
        "liệu chuyến đi, lỗi thường gặp thuộc nhóm nội tại: vùng không xác định, quãng đường bằng 0, thời lượng âm, giá cước bất "
        "thường, tốc độ phi thực tế, thời điểm nằm ngoài tháng của tệp.",
        "Mục 2.7 của bài giảng nhấn mạnh rằng kiểm soát chất lượng cần được tự động hóa và ghi lại, không phải một bước làm sạch "
        "thủ công. Đồ án cài đặt bảy quy tắc dưới dạng cờ 0/1 cho từng bản ghi, đếm số vi phạm theo quy tắc cho từng phân vùng, "
        "rồi chỉ giữ các bản ghi không vi phạm quy tắc nào. Cách này cho phép đo quy tắc nào loại nhiều dữ liệu nhất và kiểm tra "
        "việc loại dữ liệu có khác nhau giữa các nhóm hay không.")
    rp.H3("2.5.2. Lệch lược đồ")
    rp.PS(
        "Lệch lược đồ (schema drift) xảy ra khi cấu trúc dữ liệu thay đổi theo thời gian. Trong dữ liệu TLC, cột "
        "cbd_congestion_fee chỉ xuất hiện từ tháng 01/2025. Nếu đọc gộp hai năm mà không xử lý, truy vấn sẽ lỗi hoặc cột sẽ nhận "
        "giá trị rỗng không kiểm soát. Lớp Bronze của đồ án phát hiện lệch lược đồ bằng cách so sánh lược đồ từng tháng với tháng "
        "đầu tiên, còn lớp Silver chuẩn hóa bằng cách gán phí bằng 0 cho các tháng trước chính sách, đúng với thực tế.")
    rp.H3("2.5.3. Quyền riêng tư")
    rp.PS(
        "TLC chỉ công bố vị trí ở mức vùng taxi và không công bố định danh tài xế, biển số hay hành khách. Đây là một ví dụ về "
        "tổng quát hóa không gian để giảm rủi ro nhận dạng lại, phù hợp với tinh thần của GDPR và Nghị định 13/2023/NĐ-CP về bảo "
        "vệ dữ liệu cá nhân được nêu ở mục 2.8 của bài giảng. Đồ án không cố gắng khôi phục thông tin cá nhân và mọi kết quả đều "
        "ở mức tổng hợp. Chương 6 đo trực tiếp mức độ bảo vệ mà cách tổng quát hóa này đem lại.")
    rp.H3("2.5.4. Danh mục dữ liệu, phả hệ và tính toàn vẹn")
    rp.PS(
        "Mục 2.6 của bài giảng mô tả hệ thống siêu dữ liệu và danh mục dữ liệu (data catalog) như xương sống của quản trị dữ liệu "
        "doanh nghiệp. Một danh mục trả lời câu hỏi dữ liệu nào tồn tại, nằm ở đâu, có cấu trúc gì và do ai tạo ra. Phả hệ dữ liệu "
        "(data lineage) trả lời câu hỏi một bảng được tạo ra từ những bảng nào qua những bước nào, và ngược lại, nếu một bảng thay đổi "
        "thì những kết quả nào bị ảnh hưởng. Hai thành phần này thường được duy trì bằng các công cụ chuyên dụng như Apache Atlas "
        "hoặc Unity Catalog; ở quy mô đồ án, chúng có thể được trích tự động từ siêu dữ liệu Parquet và từ mã nguồn.",
        "Tính toàn vẹn của dữ liệu nguồn là một phần của an ninh chuỗi cung ứng số (mục 7.5 của bài giảng). Hàm băm mật mã như SHA-256 "
        "cho mỗi tệp một dấu vân tay 256 bit; chỉ cần một bit thay đổi, dấu vân tay thay đổi hoàn toàn. Lưu dấu băm khi nhận dữ liệu và "
        "kiểm tra lại trước khi xử lý là biện pháp tối thiểu để phát hiện tệp hỏng hoặc bị thay thế.")
    rp.H3("2.5.5. k-ẩn danh và rủi ro tái nhận dạng")
    rp.PS(
        "Việc xóa định danh trực tiếp (tên, số điện thoại) không đủ để ẩn danh dữ liệu. Sweeney (2002) chỉ ra rằng tổ hợp một vài "
        "thuộc tính tưởng như vô hại, gọi là định danh gián tiếp (quasi-identifier), thường đủ để xác định duy nhất một người khi đối "
        "chiếu với nguồn thông tin khác. Mô hình k-ẩn danh yêu cầu mỗi bản ghi trùng với ít nhất k−1 bản ghi khác trên mọi định danh "
        "gián tiếp. De Montjoye và cộng sự (2013) cho thấy với dữ liệu di chuyển, chỉ bốn điểm không gian – thời gian đã đủ xác định "
        "duy nhất 95% người dùng. Riêng dữ liệu taxi New York, Douriez và cộng sự (2016) phân tích các rủi ro tái nhận dạng khi dữ liệu "
        "chuyến đi được công bố ở mức chi tiết cao và đề xuất các phương án làm thô dữ liệu.")
    rp.H3("2.5.6. Quyền riêng tư vi phân")
    rp.PS(
        "Quyền riêng tư vi phân (Dwork và cộng sự, 2006; Dwork và Roth, 2014) định nghĩa quyền riêng tư như một tính chất của cơ chế "
        "công bố, không phải của dữ liệu. Một cơ chế ngẫu nhiên M đạt ε-quyền riêng tư vi phân nếu với mọi cặp tập dữ liệu D và D′ "
        "chỉ khác nhau một bản ghi và mọi tập kết quả S, xác suất M(D) ∈ S không vượt quá e^ε lần xác suất M(D′) ∈ S. Nói cách khác, "
        "người quan sát kết quả không thể biết chắc một bản ghi cụ thể có trong dữ liệu hay không.")
    rp.EQ("M(D) = f(D) + Laplace(Δf / ε)")
    rp.PS(
        "Cơ chế Laplace ở phương trình trên đạt bảo đảm này bằng cách cộng nhiễu Laplace có thang đo Δf/ε, với Δf là độ nhạy của hàm "
        "f, tức mức thay đổi lớn nhất của f khi thêm hoặc bớt một bản ghi. Với phép đếm, Δf = 1. Tham số ε, gọi là ngân sách riêng tư, "
        "điều chỉnh sự đánh đổi: ε nhỏ bảo vệ tốt hơn nhưng nhiễu hơn. Các ngân sách cộng dồn khi công bố nhiều kết quả trên cùng dữ "
        "liệu. Cục Điều tra Dân số Hoa Kỳ đã áp dụng phương pháp này cho điều tra dân số năm 2020 (Abowd, 2018).")
    rp.H3("2.5.7. Phát hiện bất thường, bảo mật và phục hồi")
    rp.PS(
        "Phát hiện bất thường (mục 7.2 của bài giảng) có thể dựa trên thống kê hoặc học máy. Cách tiếp cận thống kê cổ điển là biểu "
        "đồ kiểm soát của Shewhart, trong đó biểu đồ p theo dõi tỷ lệ lỗi với giới hạn ±3 độ lệch chuẩn nhị thức (Montgomery, 2019). "
        "Khi cỡ mẫu mỗi kỳ rất lớn, giới hạn nhị thức trở nên quá hẹp vì biến động thật giữa các kỳ lớn hơn nhiều so với biến động "
        "lấy mẫu; biểu đồ p′ của Laney (2002) hiệu chỉnh bằng cách ước lượng độ phân tán thật từ khoảng biến động di chuyển. Về học "
        "máy, Isolation Forest (Liu, Ting và Zhou, 2008) cô lập các điểm bằng cây phân chia ngẫu nhiên; điểm bất thường là điểm bị cô "
        "lập sau ít lần chia, và thuật toán không cần nhãn.",
        "Về bảo mật, kiến trúc Zero Trust (Rose và cộng sự, 2020) thay giả định \"bên trong mạng là an toàn\" bằng nguyên tắc xác "
        "thực và cấp quyền cho mọi yêu cầu, quyền tối thiểu và giả định đã bị xâm nhập. Về phục hồi sau sự cố (mục 7.7 của bài giảng), "
        "hai chỉ tiêu chuẩn là thời gian phục hồi mục tiêu (RTO), tức thời gian tối đa để khôi phục dịch vụ, và điểm phục hồi mục "
        "tiêu (RPO), tức lượng dữ liệu tối đa có thể mất.")

    rp.H2("2.6. Suy luận nhân quả từ dữ liệu quan sát")
    rp.H3("2.6.1. Khung kết quả tiềm năng")
    rp.PS(
        "Gọi Y_it(1) là kết quả của đơn vị i tại thời điểm t nếu chịu chính sách và Y_it(0) là kết quả nếu không chịu. Tác động "
        "của chính sách lên đơn vị đó là Y_it(1) − Y_it(0). Vấn đề cơ bản của suy luận nhân quả là ta chỉ quan sát được một trong "
        "hai kết quả. Đại lượng mục tiêu thường là tác động trung bình trên nhóm được xử lý (ATT):")
    rp.EQ("ATT = E[ Y_it(1) − Y_it(0) | D_i = 1, t ≥ t₀ ]")
    rp.P("Các phương pháp dưới đây là những cách khác nhau để xây dựng phản thực E[Y_it(0) | D_i = 1, t ≥ t₀] từ dữ liệu quan "
         "sát, mỗi cách dựa trên một giả định khác nhau.")
    rp.H3("2.6.2. Sai khác kép và hai chiều hiệu ứng cố định")
    rp.P("Sai khác kép so sánh thay đổi trước – sau của nhóm xử lý với thay đổi trước – sau của nhóm đối chứng. Với nhiều đơn vị "
         "và nhiều thời kỳ, đặc tả hai chiều hiệu ứng cố định (TWFE) là:")
    rp.EQ("Y_it = α_i + γ_t + β · D_it + ε_it")
    rp.PS(
        "trong đó α_i hấp thụ mọi khác biệt không đổi theo thời gian giữa các đơn vị, γ_t hấp thụ mọi cú sốc chung của từng thời "
        "kỳ, D_it = 1 nếu đơn vị i thuộc nhóm xử lý và t sau chính sách. Hệ số β xác định ATT dưới giả định xu hướng song song: "
        "nếu không có chính sách, kết quả trung bình của hai nhóm sẽ biến động cùng nhau (Angrist và Pischke, 2009).",
        "Khi mọi đơn vị xử lý bắt đầu chịu chính sách cùng một thời điểm, như trường hợp CRZ, TWFE không gặp vấn đề trọng số âm mà "
        "các nghiên cứu gần đây chỉ ra cho thiết kế có nhiều thời điểm xử lý (Goodman-Bacon, 2021; Callaway và Sant'Anna, 2021). "
        "Vấn đề chính ở đây là giả định xu hướng song song, vì khu trung tâm có mùa vụ và xu hướng riêng.")
    rp.H3("2.6.3. Nghiên cứu sự kiện")
    rp.P("Nghiên cứu sự kiện thay biến D bằng một tập biến giả theo thời gian tương đối so với mốc chính sách:")
    rp.EQ("Y_it = α_i + γ_t + Σ_{k≠−1} β_k · 1[t − t₀ = k] · T_i + ε_it")
    rp.PS(
        "Các hệ số β_k với k < 0 là phép kiểm tra xu hướng trước chính sách: nếu chúng khác 0 một cách có hệ thống, giả định xu "
        "hướng song song đáng ngờ. Các hệ số với k ≥ 0 mô tả động thái của tác động. Roth và cộng sự (2023) lưu ý rằng kiểm định "
        "tiền xu hướng có độ mạnh hạn chế, và việc không bác bỏ được không chứng minh xu hướng song song. Ngược lại, khi mẫu rất "
        "lớn, kiểm định gần như luôn bác bỏ, nên cần đọc độ lớn và hình dạng của các hệ số chứ không chỉ giá trị p. Rambachan và "
        "Roth (2023) đề xuất cách đánh giá độ nhạy của kết luận khi cho phép vi phạm xu hướng song song trong một giới hạn nhất "
        "định.",
        "Việc chọn kỳ mốc ảnh hưởng đến cách đọc hình. Nếu kỳ mốc rơi vào một tuần có biến động bất thường, chẳng hạn tuần lễ cuối "
        "năm, toàn bộ đường hệ số bị dịch lên hoặc xuống. Đồ án vì vậy chuẩn hóa lại các hệ số theo trung bình của toàn bộ giai "
        "đoạn trước chính sách, và tính lại sai số chuẩn bằng phép biến đổi tuyến tính tương ứng của ma trận hiệp phương sai.")
    rp.H3("2.6.4. Khử mùa vụ bằng sai khác bậc ba")
    rp.PS(
        "Khi nhóm xử lý có mùa vụ riêng, có thể bổ sung hiệu ứng cố định nhóm × tuần trong năm, ký hiệu δ_{g(i),w(t)}. Khi đó β được "
        "xác định từ chênh lệch giữa năm sau và năm trước của khoảng cách xử lý – đối chứng trong cùng tuần của năm. Giả định cần "
        "thiết chuyển từ \"xu hướng song song\" sang \"mùa vụ ổn định giữa hai năm\". Nhược điểm là khi chỉ có một năm trước chính "
        "sách, thiết kế này không thể đồng thời kiểm soát cả mùa vụ nhóm lẫn xu hướng tuyến tính riêng của nhóm, vì hai thành phần "
        "gần như đa cộng tuyến hoàn toàn với biến xử lý.")
    rp.H3("2.6.5. Kiểm soát tổng hợp")
    rp.P("Phương pháp kiểm soát tổng hợp (Abadie, Diamond và Hainmueller, 2010) xây dựng phản thực cho một đơn vị xử lý duy nhất "
         "bằng tổ hợp lồi của các đơn vị đối chứng:")
    rp.EQ("Ŷ_1t(0) = Σ_j w_j · Y_jt,  w_j ≥ 0,  Σ_j w_j = 1")
    rp.PS(
        "Trọng số được chọn để khớp chuỗi kết quả trong giai đoạn trước chính sách. Ưu điểm là tính minh bạch: ta biết chính xác "
        "phản thực được tạo từ những vùng nào với trọng số bao nhiêu. Suy luận dựa vào kiểm định giả dược theo không gian: lần "
        "lượt coi mỗi đơn vị đối chứng là đơn vị xử lý, tính tỷ số RMSPE sau/trước, rồi xem đơn vị xử lý thật đứng ở đâu trong phân "
        "phối (Abadie, 2021). Ferman và Pinto (2021) phân tích trường hợp khớp trước chính sách không hoàn hảo và đề xuất phiên "
        "bản khử trung bình.")
    rp.H3("2.6.6. Suy luận hoán vị và sai số chuẩn phân cụm")
    rp.PS(
        "Với dữ liệu panel, sai số của cùng một đơn vị qua các thời kỳ tương quan với nhau. Bertrand, Duflo và Mullainathan (2004) "
        "chỉ ra rằng bỏ qua tương quan này làm sai số chuẩn bị đánh giá thấp nghiêm trọng. Cách xử lý chuẩn là phân cụm sai số theo "
        "đơn vị (Cameron và Miller, 2015). Khi số cụm đủ lớn, sai số chuẩn phân cụm đáng tin. Suy luận hoán vị bổ sung một góc nhìn "
        "khác: gán ngẫu nhiên nhãn xử lý cho các đơn vị đối chứng nhiều lần để xây dựng phân phối của hệ số dưới giả thuyết không có "
        "tác động, không phụ thuộc vào giả định tiệm cận.")
    rp.H3("2.6.7. Ước lượng hiệu ứng cố định nhiều chiều")
    rp.PS(
        "Với hàng trăm vùng và hàng trăm tuần, việc đưa biến giả cho từng vùng và từng tuần vào hồi quy tạo ra ma trận lớn không cần "
        "thiết. Định lý Frisch–Waugh–Lovell cho phép khử hiệu ứng cố định trước rồi mới hồi quy. Với nhiều chiều hiệu ứng cố định, "
        "phép khử được thực hiện bằng chiếu luân phiên: lần lượt trừ trung bình theo từng chiều cho tới khi hội tụ (Guimarães và "
        "Portugal, 2010; Correia, 2016). Đồ án tự cài đặt thuật toán này có hỗ trợ trọng số, kèm sai số chuẩn phân cụm CR1 với hiệu "
        "chỉnh bậc tự do.")

    rp.H2("2.7. Học máy nhân quả")
    rp.H3("2.7.1. Double/Debiased Machine Learning")
    rp.P("Khi tác động phụ thuộc vào nhiều biến kiểm soát X theo dạng hàm chưa biết, mô hình tuyến tính từng phần (PLR) là:")
    rp.EQ("Y = θ · D + g(X) + U,   D = m(X) + V")
    rp.P("Chernozhukov và cộng sự (2018) chỉ ra rằng nếu ước lượng g và m bằng học máy rồi thay vào một cách ngây thơ, ước lượng θ "
         "sẽ bị chệch do chính sai số của học máy. Giải pháp gồm hai thành phần. Thứ nhất, dùng hàm điểm trực giao Neyman, tức là "
         "hồi quy phần dư của Y lên phần dư của D, để sai số bậc một của các ước lượng phụ không ảnh hưởng đến θ. Thứ hai, dùng "
         "cross-fitting: chia mẫu thành K phần, ước lượng hàm phụ trên K − 1 phần và tính phần dư trên phần còn lại, để tránh quá "
         "khớp. Ước lượng thu được là:")
    rp.EQ("θ̂ = Σ_i (D_i − m̂(X_i))(Y_i − ĝ(X_i)) / Σ_i (D_i − m̂(X_i))²")
    rp.H3("2.7.2. Ước lượng bền vững kép AIPW")
    rp.P("Ước lượng trọng số nghịch đảo xác suất tăng cường (AIPW) kết hợp mô hình kết quả μ_d(X) = E[Y | D = d, X] và mô hình "
         "xu hướng e(X) = P(D = 1 | X). Điểm ảnh hưởng của từng quan sát là:")
    rp.EQ("φ_i = μ̂₁ − μ̂₀ + D_i (Y_i − μ̂₁) / ê − (1 − D_i)(Y_i − μ̂₀) / (1 − ê)")
    rp.PS(
        "Trung bình của φ_i là ước lượng ATE, nhất quán nếu một trong hai mô hình đúng. Điều kiện quan trọng là chồng lấn: e(X) phải "
        "nằm xa 0 và 1. Khi các đơn vị xử lý và đối chứng khác nhau quá xa về X, ê(X) tiến sát 0 hoặc 1, trọng số bùng nổ và ước "
        "lượng mất ổn định. Thực hành phổ biến là cắt bỏ các quan sát có ê(X) ngoài khoảng [0,05; 0,95] và báo cáo rõ tổng thể mà "
        "ước lượng đại diện.")
    rp.H3("2.7.3. Tác động không đồng nhất: DR-learner, BLP và GATES")
    rp.PS(
        "Tác động trung bình có điều kiện CATE τ(x) = E[Y(1) − Y(0) | X = x] có thể ước lượng bằng DR-learner: hồi quy điểm ảnh "
        "hưởng φ_i lên X bằng một mô hình học máy (Kennedy, 2023). Vì τ̂(x) có thể chứa nhiễu, Chernozhukov, Demirer, Duflo và "
        "Fernández-Val (2018) đề xuất không suy luận trực tiếp trên τ̂ mà dùng nó như một chỉ số để kiểm định. Bộ dự báo tuyến tính "
        "tốt nhất (BLP) hồi quy φ lên hằng số và τ̂ − E[τ̂]; hệ số của thành phần thứ hai khác 0 cho thấy có tác động không đồng "
        "nhất thật sự. GATES chia mẫu theo phân vị của τ̂ và ước lượng tác động trung bình trong từng nhóm. CLAN so sánh đặc trưng "
        "trung bình của nhóm có tác động cao nhất và thấp nhất.")
    rp.H3("2.7.4. LightGBM làm mô hình phụ")
    rp.PS(
        "Các hàm phụ trong DML có thể được ước lượng bằng bất kỳ phương pháp học máy đủ linh hoạt nào. Đồ án chọn LightGBM (Ke và "
        "cộng sự, 2017), thuật toán tăng cường độ dốc dựa trên histogram với cây phát triển theo lá, vì tốc độ cao, xử lý tốt cả "
        "biến liên tục lẫn nhị phân và đã được kiểm chứng rộng rãi trên dữ liệu dạng bảng. Các siêu tham số được cố định trước (tốc "
        "độ học 0,03; 400 cây; 15 lá; tối thiểu 40 quan sát mỗi lá) thay vì tinh chỉnh theo kết quả nhân quả, để tránh chọn mô hình "
        "theo đáp án mong muốn.")

    rp.H2("2.8. Tổng quan các nghiên cứu liên quan")
    rp.H3("2.8.1. Đánh giá phí ùn tắc ở các thành phố khác")
    rp.PS(
        "Tài liệu về phí ùn tắc theo vùng hình thành qua ba thế hệ. Thế hệ thứ nhất đánh giá các chương trình ở Singapore, London và "
        "Stockholm bằng dữ liệu đếm xe tại điểm cố định và khảo sát hành trình (Olszewski và Xie, 2005; Santos và Shaffer, 2004; Leape, "
        "2006; Eliasson, 2009; Börjesson và cộng sự, 2012). Ở London và Stockholm, lưu lượng xe vào vùng giảm khoảng một phần năm ngay "
        "sau khi áp dụng và tốc độ tăng rõ, nhưng ở London phần lợi ích về tốc độ mờ dần trong các năm sau. Điểm mạnh là "
        "đo trực tiếp lưu lượng; điểm yếu là độ phân giải không gian và thời gian thấp, khó tách tác động theo loại chuyến đi.",
        "Thế hệ thứ hai dùng thiết kế bán thực nghiệm để đánh giá các kết quả thứ cấp. Gibson và Carnovale (2015) dùng biên giới của "
        "vùng Area C ở Milan để ước lượng tác động lên hành vi lái xe và ô nhiễm, kể cả ở khu vực ngay "
        "ngoài ranh giới. Percoco (2013) cũng cho Milan, Green, Heywood và Navarro (2020) cho London, và Simeonova và cộng sự (2021) cho Stockholm "
        "đánh giá tác động lên ô nhiễm không khí và sức khỏe, với kết quả không đồng nhất giữa các chất ô nhiễm. Thế hệ thứ ba dùng dữ "
        "liệu hành vi cá nhân và thử nghiệm ngẫu nhiên: Kreindler (2024) chạy thử nghiệm định giá theo giờ cao điểm ở Bangalore bằng "
        "dữ liệu GPS điện thoại và ước lượng lợi ích cân bằng của phí tối ưu là nhỏ vì cầu kém co giãn theo giờ khởi hành; Hanna, "
        "Kreindler và Olken (2017) khai thác việc bãi bỏ đột ngột quy định xe nhiều người ở Jakarta để đo tác động lan ra toàn mạng lưới.",
        "Về cơ chế, Duranton và Turner (2011) cung cấp bằng chứng cho \"quy luật cơ bản của ùn tắc\": lưu lượng tăng gần tỷ lệ với năng "
        "lực đường, nên mọi cải thiện tốc độ đều có xu hướng bị nhu cầu cảm ứng bào mòn. Anderson (2014) cho thấy giao thông công cộng "
        "làm giảm đáng kể ùn tắc trên các trục song song, nghĩa là phương án thay thế bằng tàu điện ảnh hưởng lớn đến độ co giãn của cầu "
        "đi xe. Small, Winston và Yan (2005) ước lượng giá trị thời gian và độ tin cậy của người lái, tham số trung tâm trong phúc lợi "
        "của phí ùn tắc. Athey và Imbens (2017) nhận định rằng dữ liệu giao dịch quy mô lớn đang thay đổi cách đánh giá chính sách, "
        "cho phép dùng sai khác kép và kiểm soát tổng hợp ở mức chi tiết mà trước đây không có.")
    rp.H3("2.8.2. Gọi xe công nghệ và ùn tắc")
    rp.PS(
        "Nhóm tài liệu thứ hai nghiên cứu quan hệ giữa gọi xe công nghệ và ùn tắc. Erhardt và cộng sự (2019) ước lượng rằng các công ty "
        "gọi xe là nguyên nhân lớn nhất của mức tăng ùn tắc ở San Francisco giai đoạn 2010–2016. Schaller (2021) dùng dữ liệu của chính "
        "New York và các thành phố khác để chỉ ra rằng gọi xe làm tăng tổng số dặm xe chạy, kể cả khi tính cả chuyến đi chung, vì quãng "
        "đường xe chạy rỗng và vì chuyến gọi xe thay thế chủ yếu cho giao thông công cộng và đi bộ. Beojone và Geroliminis (2021) mô "
        "phỏng ở quy mô thành phố và cho thấy xe chạy rỗng để đón khách làm giảm hiệu quả của mạng lưới. Tirachini (2020) tổng hợp "
        "tài liệu quốc tế và kết luận rằng tác động ròng của gọi xe lên ùn tắc phần lớn là tiêu cực khi không có chính sách quản lý.",
        "Về kinh tế học nền tảng, Cramer và Krueger (2016) so sánh hiệu suất sử dụng xe của Uber và taxi, Cohen và cộng sự (2016) ước "
        "lượng đường cầu và thặng dư tiêu dùng từ dữ liệu giao dịch của Uber, và Castillo, Knoepfle và Weyl (2017) phân tích vai trò "
        "của định giá tăng đột biến. Rochet và Tirole (2003) cung cấp khung lý thuyết cho thị trường hai phía, còn Weyl và Fabinger "
        "(2013) cho khung chung về tỷ lệ chuyển thuế sang người mua trong các cấu trúc thị trường khác nhau, là cơ sở cho giả thuyết "
        "H5 ở mục 2.11.")
    rp.H3("2.8.3. Đánh giá phí CRZ tại New York")
    rp.PS(
        "Vì chính sách có hiệu lực từ đầu năm 2025, tài liệu học thuật còn ít và phần lớn ở dạng bài làm việc. Cook và cộng sự (2025) "
        "dùng dữ liệu tốc độ của Google Maps từ 09/2024 đến 02/2025, so với năm thành phố đối chứng, và báo cáo tốc độ trung bình trong "
        "vùng tăng từ 8,2 lên 9,7 dặm/giờ, tức khoảng 15%, với mức tăng lớn hơn vào chiều ngày thường và tối cuối tuần, cùng mức tăng "
        "tốc độ trên các tuyến ngoài vùng có nhiều chuyến đi vào vùng. Pandey, Guler và Gayah (2026) dùng dữ liệu TLC và sai khác kép, "
        "báo cáo tổng số chuyến của các công ty gọi xe giảm 5,95%, số yêu cầu đi chung giảm 38,08% và số chuyến đi chung được ghép "
        "thành công giảm 50,87%, và cho rằng việc không có ưu đãi phí cho chuyến đi chung đã khuếch đại tác động lên loại chuyến này.",
        "Hai nghiên cứu này bổ sung cho nhau nhưng đều để lại khoảng trống. Nghiên cứu thứ nhất đo tốc độ trên đường nhưng không đo cầu "
        "đi lại; nghiên cứu thứ hai đo cầu nhưng dừng ở tác động trung bình, không phân tích tốc độ theo chuyến, thời gian chờ, lan tỏa "
        "theo mức phơi nhiễm hay tác động không đồng nhất.")
    rp.H3("2.8.4. Học máy nhân quả trong giao thông và kinh doanh")
    rp.PS(
        "Học máy nhân quả được dùng ngày càng nhiều trong marketing (mô hình uplift, được đề cập ở Chương 5 của bài giảng), định giá "
        "và đánh giá chính sách. Trong giao thông, các ứng dụng chủ yếu là ước lượng tác động không đồng nhất của thay đổi giá hoặc "
        "dịch vụ lên các nhóm hành khách. Một vấn đề ít được thảo luận là điều kiện chồng lấn: khi đơn vị xử lý khác biệt có hệ "
        "thống về không gian, mô hình xu hướng dễ phân tách gần hoàn hảo hai nhóm. Đồ án đo trực tiếp vấn đề này và so sánh kết quả "
        "với các bộ biến kiểm soát khác nhau.")
    rp.H3("2.8.5. Tổng hợp")
    m01 = R.t("t01")
    yr0, yr1 = m01.month.min()[:4], m01.month.max()[:4]
    rp.P("Bảng dưới đây hệ thống hóa các nghiên cứu chính theo dữ liệu, phương pháp, kết quả chính và giới hạn, và đặt đồ án vào "
         "bối cảnh đó.")
    df = pd.DataFrame([
        ("Santos và Shaffer (2004); Leape (2006)", "London; đếm xe", "Mô tả trước – sau", "Lưu lượng vào vùng giảm, tốc độ tăng", "Không có nhóm đối chứng chặt"),
        ("Olszewski và Xie (2005)", "Singapore; dữ liệu lưu lượng", "Mô hình lưu lượng", "Phản ứng lưu lượng theo mức phí và giờ", "Một thành phố, phí điện tử"),
        ("Eliasson (2009); Börjesson và cs. (2012)", "Stockholm; đếm xe, khảo sát", "Thử nghiệm rồi áp dụng lâu dài; CBA", "Lưu lượng giảm bền vững, lợi ích ròng dương", "Độ phân giải thấp"),
        ("Percoco (2013); Gibson, Carnovale (2015)", "Milan (Ecopass, Area C)", "Sai khác kép, so sánh quanh ranh giới", "Hành vi lái xe, ô nhiễm trong và ngoài vùng", "Không tách loại chuyến"),
        ("Green, Heywood, Navarro (2020)", "London; trạm quan trắc", "Sai khác kép", "Tác động không đồng nhất lên các chất ô nhiễm", "Chỉ kết quả môi trường"),
        ("Simeonova và cs. (2021)", "Stockholm; dữ liệu y tế", "Sai khác kép", "Giảm hen suyễn ở trẻ em", "Chỉ kết quả sức khỏe"),
        ("Hanna, Kreindler, Olken (2017)", "Jakarta; dữ liệu Google Maps", "Thực nghiệm tự nhiên", "Ùn tắc tăng mạnh trên toàn mạng sau khi bỏ quy định", "Chính sách khác (xe nhiều người)"),
        ("Kreindler (2024)", "Bangalore; GPS điện thoại", "Thử nghiệm ngẫu nhiên + mô hình cân bằng", "Cầu kém co giãn theo giờ; lợi ích phí tối ưu nhỏ", "Phí theo cá nhân, không theo vùng"),
        ("Duranton, Turner (2011)", "Mỹ; lưu lượng đường", "Biến công cụ", "Quy luật cơ bản của ùn tắc", "Không đánh giá phí"),
        ("Anderson (2014)", "Los Angeles; đình công tàu điện", "Gián đoạn thời gian", "Giao thông công cộng giảm ùn tắc", "Không đánh giá phí"),
        ("Erhardt và cs. (2019)", "San Francisco; dữ liệu API", "Mô hình mạng lưới", "Gọi xe góp phần lớn vào tăng ùn tắc", "Không đánh giá chính sách phí"),
        ("Schaller (2021)", "New York và các thành phố Mỹ", "Tính toán số dặm xe chạy", "Gọi xe, kể cả đi chung, làm tăng số dặm xe", "Mô tả, không nhân quả"),
        ("Beojone, Geroliminis (2021)", "Mô phỏng quy mô thành phố", "Mô hình vĩ mô mạng lưới", "Xe chạy rỗng làm giảm hiệu quả mạng", "Dựa trên mô phỏng"),
        ("Cohen và cs. (2016); Castillo và cs. (2017)", "Dữ liệu nội bộ Uber", "Gián đoạn giá, lý thuyết", "Đường cầu; vai trò của giá tăng đột biến", "Không đánh giá chính sách công"),
        ("Cook và cs. (2025)", "New York; Google Maps", "Sai khác kép với 5 thành phố đối chứng", "Tốc độ trong vùng tăng khoảng 15%", "Không đo cầu đi lại"),
        ("Pandey, Guler, Gayah (2026)", "New York; chuyến TLC", "Sai khác kép", "Chuyến gọi xe giảm 5,95%; đi chung giảm mạnh", "Chỉ tác động trung bình"),
        ("Đồ án này", f"New York; chuyến TLC {yr0}–{yr1}, Lakehouse", "DiD, DDD, SCM, DML, liều – đáp ứng", "Số chuyến, tốc độ, chờ, lan tỏa, CATE, theo hãng", "Tốc độ đo trên chuyến gọi xe"),
    ], columns=["Nghiên cứu", "Bối cảnh, dữ liệu", "Phương pháp", "Kết quả chính", "Giới hạn chính"])
    rp.TAB(df, "Hệ thống hóa các nghiên cứu liên quan và vị trí của đồ án", widths=[3.6, 3.0, 3.0, 3.6, 2.8], size=9,
           align=["left"] * 5, source="Nguồn: tác giả tổng hợp.")

    rp.H2("2.9. Giá trị kinh doanh của dữ liệu lớn")
    rp.H3("2.9.1. Dự báo nhu cầu và dự báo làm phản thực tế")
    rp.PS(
        "Dự báo nhu cầu (mục 4.4 của bài giảng) là ứng dụng vận hành quen thuộc nhất của dữ liệu lớn. Các mô hình từ hồi quy có biến "
        "lịch, mô hình chuỗi thời gian đến học máy dạng cây đều được dùng, và được đánh giá bằng sai số trên dữ liệu giữ lại như MAPE "
        "hay RMSE (Hyndman và Athanasopoulos, 2021). Một cách dùng mở rộng là coi dự báo cho giai đoạn sau một sự kiện là phản thực "
        "tế. Brodersen và cộng sự (2015) chính thức hóa cách này bằng mô hình chuỗi thời gian cấu trúc Bayes với các chuỗi đối chứng "
        "làm biến giải thích (CausalImpact). Giả định then chốt là các chuỗi đối chứng không bị sự kiện ảnh hưởng.")
    rp.H3("2.9.2. Thử nghiệm quy mô lớn và công suất thống kê")
    rp.PS(
        "Thử nghiệm có kiểm soát trực tuyến (A/B testing) là cách doanh nghiệp số đo tác động của thay đổi sản phẩm (Kohavi, Tang "
        "và Xu, 2020). Hai vấn đề thiết kế trung tâm là công suất thống kê và tính ổn định theo thời gian của tác động. Tác động nhỏ "
        "nhất phát hiện được (MDE) với công suất 1−β và mức ý nghĩa α xấp xỉ (z₁₋α/₂ + z₁₋β) nhân sai số chuẩn của ước lượng, tức "
        "khoảng 2,8 lần sai số chuẩn với α = 5% và công suất 80% (Bloom, 1995). Về thời gian, tác động đo trong vài tuần đầu có thể "
        "khác tác động dài hạn do hiệu ứng mới lạ hoặc do người dùng thích nghi dần.")
    rp.H3("2.9.3. Định giá động trong nền tảng gọi xe")
    rp.PS(
        "Định giá động (mục 6.4 của bài giảng) là việc điều chỉnh giá theo điều kiện cung cầu tức thời. Với nền tảng gọi xe, Castillo, "
        "Knoepfle và Weyl (2017) chỉ ra rằng tăng giá khi cầu vượt cung không chỉ phân bổ xe cho người trả giá cao nhất mà còn ngăn "
        "hệ thống rơi vào trạng thái xe phải đi rất xa để đón khách. Giá cuối cùng khách trả vì vậy là tổng của thành phần theo thời "
        "gian, quãng đường và hệ số điều chỉnh theo cung cầu, cộng các khoản phí và thuế.")
    rp.H3("2.9.4. Định giá tài sản dữ liệu, ROI và TCO")
    rp.PS(
        "Moody và Walsh (1999) đề xuất định giá thông tin theo ba cách tương tự định giá tài sản hữu hình: theo chi phí, theo giá thị "
        "trường và theo giá trị sử dụng, đồng thời nêu các đặc điểm riêng của thông tin như có thể dùng chung mà không hao mòn và giá "
        "trị tăng khi được kết hợp. Laney (2017) phát triển thành khung quản lý thông tin như tài sản. Mục 6.1 đến 6.5 của bài giảng "
        "đặt các khái niệm này trong bối cảnh dự án dữ liệu lớn, với ROI đo bằng giá trị quyết định và TCO gồm lưu trữ, tính toán, "
        "nhân lực và vận hành.")

    rp.H2("2.10. Khoảng trống nghiên cứu và khung phân tích")
    rp.H3("2.10.1. Khoảng trống nghiên cứu")
    rp.BUL([
        "Ước lượng trung bình hiện có chưa được kiểm tra bằng các thiết kế khác nhau (khử mùa vụ, kiểm soát tổng hợp, học máy nhân "
        "quả) để xem kết quả nhạy thế nào với giả định.",
        "Chưa có bằng chứng về tác động lên tốc độ và thời gian chờ, hai thước đo gắn trực tiếp với mục tiêu giảm ùn tắc.",
        "Chưa có phân tích lan tỏa không gian sang các vùng ngay ngoài ranh giới, nơi dễ xảy ra hành vi né phí.",
        "Chưa có phân tích tác động không đồng nhất theo đặc trưng chuyến đi kèm kiểm tra chồng lấn.",
        "Chưa có mô tả tái lập được về pipeline dữ liệu cần thiết để xử lý toàn bộ dữ liệu ở mức từng chuyến.",
        "Các đánh giá dựa trên dữ liệu lớn hiếm khi kiểm chứng chính bảng dữ liệu phân tích bằng một bộ máy độc lập, và hiếm khi đo "
        "rủi ro quyền riêng tư của dữ liệu mà chúng sử dụng.",
    ])
    rp.H3("2.10.2. Khung phân tích của đồ án")
    rp.PS(
        "Khung phân tích gồm ba tầng. Tầng dữ liệu biến dữ liệu thô thành các bảng Gold có kiểm soát chất lượng và đo chi phí xử lý "
        "(RQ1). Tầng nhận dạng ước lượng tác động trung bình bằng các thiết kế độc lập và kiểm tra chéo (RQ2). Tầng không đồng "
        "nhất phân rã tác động theo loại luồng, khung giờ, khoảng cách và đặc trưng chuyến đi (RQ3). Ba mô-đun mở rộng bao quanh ba "
        "tầng này: kiểm toán và đo chi phí xử lý phân tán (phần thứ hai của RQ1), quản trị dữ liệu và quyền riêng tư (RQ4), và "
        "chuyển kết quả thành thông tin kinh doanh (RQ5).",
        "Nguyên tắc xuyên suốt là một kết luận chỉ được coi là vững khi nhiều thiết kế dựa trên các giả định khác nhau cho kết quả "
        "cùng chiều và tương đương về độ lớn, và khi các phép thử giả dược không tạo ra một \"tác động\" có độ lớn tương đương.")
    import theory
    theory.model(rp, R)
    rp.H2("2.12. Tiểu kết Chương 2")
    rp.P("Chương 2 đã trình bày cơ sở kinh tế học của phí ùn tắc và phân bổ gánh nặng, đặc điểm của thị trường gọi xe, các khái "
         "niệm kiến trúc dữ liệu lớn được vận dụng (Lakehouse, medallion, Parquet, thực thi vector hóa, tính lũy đẳng), các phương "
         "pháp suy luận nhân quả (TWFE, nghiên cứu sự kiện, DDD, SCM, hoán vị), học máy nhân quả (DML, AIPW, DR-learner, BLP, "
         "GATES), mô hình tính toán của Spark, các công cụ quản trị dữ liệu và quyền riêng tư (danh mục, phả hệ, k-ẩn danh, quyền "
         "riêng tư vi phân, biểu đồ kiểm soát, Isolation Forest) và các khái niệm về giá trị kinh doanh của dữ liệu, cùng một mô hình lý thuyết gồm bốn khối cho tám giả thuyết kiểm định được. Tổng quan cho thấy đánh giá phí CRZ mới dừng ở tác động trung bình lên số chuyến. Chương 3 trình bày cách đồ án "
         "hiện thực hóa khung phân tích trên dữ liệu thật.")
