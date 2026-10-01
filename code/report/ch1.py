"""Chương 1. Giới thiệu nghiên cứu."""
from lib import vn, vint


def build(rp, R):
    man = R.t("t03")
    nraw = int(man.total_rows.sum())
    rev = R.t("t16")
    hv_share = rev[rev.service == "hvfhv"]
    share_charged = 100 * hv_share.n_cbd.sum() / hv_share.n.sum()

    rp.H1("CHƯƠNG 1. GIỚI THIỆU NGHIÊN CỨU")
    rp.H2("1.1. Bối cảnh nghiên cứu")
    rp.H3("1.1.1. Ùn tắc đô thị và ý tưởng định giá đường")
    rp.PS(
        "Ùn tắc giao thông là một dạng ngoại tác điển hình. Khi một chiếc xe đi vào con đường đã đông, người lái chỉ tính "
        "thời gian và chi phí của chính mình, còn phần thời gian bị kéo dài thêm cho mọi xe khác thì không ai trả. Kết quả "
        "là đường phố bị sử dụng quá mức so với mức tối ưu xã hội. Ý tưởng đánh phí để người đi đường tự gánh chi phí biên "
        "mà họ gây ra đã có từ Pigou (1920) và được Vickrey (1969) phát triển thành lý thuyết định giá ùn tắc hiện đại. "
        "Trong gần một thế kỷ, ý tưởng này chủ yếu tồn tại trên giấy vì khó đo lường, khó thu phí và khó thuyết phục cử tri.",
        "Điều kiện kỹ thuật đã thay đổi. Hệ thống thu phí điện tử, camera đọc biển số và thiết bị định vị trên từng xe cho "
        "phép thu phí theo vùng mà không cần trạm dừng. Singapore áp dụng từ năm 1975 và chuyển sang thu phí điện tử năm "
        "1998, London từ năm 2003, Stockholm thử nghiệm năm 2006 rồi áp dụng chính thức năm 2007. Các nghiên cứu đánh giá "
        "những chương trình này (Leape, 2006; Eliasson, 2009; Börjesson và cộng sự, 2012) đều ghi nhận lưu lượng xe vào vùng "
        "thu phí giảm đáng kể, song cũng cho thấy kết quả phụ thuộc nhiều vào cấu trúc mạng lưới giao thông, mức phí và các "
        "phương thức thay thế sẵn có.")
    rp.H3("1.1.2. Chính sách phí vùng giảm ùn tắc tại New York")
    rp.PS(
        "New York là thành phố đầu tiên ở Hoa Kỳ triển khai phí ùn tắc theo vùng. Từ ngày 05/01/2025, Cơ quan Vận tải "
        "Đô thị (MTA) thu phí đối với phương tiện đi vào Manhattan từ đường 60 trở xuống, được gọi là Congestion Relief "
        "Zone (CRZ). Xe con cá nhân trả phí theo ngày. Taxi và xe cho thuê không trả theo lượt vào vùng mà trả theo từng "
        "chuyến có liên quan đến vùng: theo công bố của MTA, mỗi chuyến của dịch vụ xe cho thuê số lượng lớn (HVFHV, tức "
        "Uber và Lyft) bị tính 1,50 USD, còn taxi vàng, taxi xanh và các xe cho thuê khác bị tính 0,75 USD. Khoản phí này "
        "được cộng vào hóa đơn của hành khách và xuất hiện trong dữ liệu chuyến đi dưới tên cột cbd_congestion_fee.",
        "Trước chính sách, New York đã có một khoản phụ thu ùn tắc từ năm 2019 áp cho chuyến taxi và xe cho thuê đi qua "
        "Manhattan phía nam đường 96. Khoản phụ thu này vẫn giữ nguyên trong năm 2025. Như vậy, phí CRZ là một cú sốc giá "
        "cộng thêm, có ranh giới địa lý rõ ràng và có ngày bắt đầu xác định. Đây là cấu trúc gần với một thí nghiệm tự nhiên: "
        "một nhóm khu vực chịu phí từ một thời điểm cụ thể, các khu vực khác thì không.",
        f"Trong dữ liệu năm 2025, khoảng {vn(share_charged, 1)}% số chuyến HVFHV trên toàn thành phố có ghi nhận phí CBD. "
        f"Con số này cho thấy chính sách chạm tới khoảng một phần ba thị trường gọi xe, dù CRZ chỉ chiếm một diện tích nhỏ "
        f"của thành phố. Chính mức độ tập trung đó làm cho câu hỏi về tác động trở nên có ý nghĩa với cả hành khách, tài xế, "
        f"doanh nghiệp nền tảng và cơ quan quản lý.")
    rp.H3("1.1.3. Dữ liệu chuyến đi như một tài sản dữ liệu lớn")
    rp.PS(
        "Ủy ban Taxi và Limousine New York (TLC) công bố hồ sơ từng chuyến của taxi vàng, taxi xanh và xe cho thuê theo "
        "tháng dưới định dạng Parquet. Riêng nhóm HVFHV, mỗi tháng có khoảng 19–22 triệu chuyến, mỗi chuyến có thời điểm gọi "
        "xe, thời điểm đón, thời điểm trả, vùng đón, vùng trả, quãng đường, thời lượng, giá cước cơ sở, các loại phí, tiền "
        "tip và thu nhập của tài xế. Đây là dữ liệu có đủ các đặc trưng của dữ liệu lớn mà bài giảng của môn học nêu ra: "
        "khối lượng lớn, cập nhật đều đặn, có lệch lược đồ giữa các giai đoạn và có sai sót ở mức từng bản ghi.",
        f"Đồ án sử dụng 24 tháng dữ liệu HVFHV và taxi vàng, tổng cộng {vint(nraw)} bản ghi thô. Với quy mô này, cách làm quen "
        f"thuộc là đọc toàn bộ vào pandas rồi phân tích không còn khả thi trên máy tính cá nhân. Việc đánh giá chính sách vì vậy "
        f"đòi hỏi một kiến trúc xử lý dữ liệu đúng nghĩa: tách lớp lưu trữ và lớp tính toán, dùng định dạng cột nén, xử lý theo "
        f"phân vùng, kiểm soát chất lượng tự động và chỉ đưa các bảng tổng hợp nhỏ vào bước mô hình hóa.")

    rp.H2("1.2. Vấn đề nghiên cứu")
    rp.H3("1.2.1. Tác động trung bình đã có ước lượng ban đầu, nhưng còn thô")
    rp.PS(
        "Ngay sau khi chính sách có hiệu lực, một số nghiên cứu nhanh đã sử dụng dữ liệu TLC để đo mức thay đổi số chuyến "
        "gọi xe. Pandey, Guler và Gayah (2026) dùng sai khác kép và báo cáo tổng số chuyến của các công ty gọi xe giảm "
        "5,95%, trong khi số yêu cầu đi chung giảm mạnh hơn nhiều. Các ước lượng như vậy trả lời câu hỏi \"trung bình giảm "
        "bao nhiêu\" nhưng để lại ba khoảng trống: tác động khác nhau thế nào giữa các loại chuyến và khung giờ; phần nhu cầu "
        "bị mất có dịch chuyển sang các vùng lân cận hay không; và ai là người thực sự gánh khoản phí. Đồ án tập trung vào hai "
        "khoảng trống đầu; khoảng trống thứ ba cần dữ liệu giá theo chuyến của nền tảng nên nằm ngoài phạm vi.",
        "Ba khoảng trống này quan trọng vì chúng quyết định cách đọc con số trung bình. Nếu nhu cầu chỉ dịch chuyển điểm "
        "đón ra ngoài ranh giới vài trăm mét, mức giảm trong vùng không đồng nghĩa với giảm số người đi lại. Nếu vùng đối "
        "chứng bị ảnh hưởng gián tiếp, ước lượng sai khác kép sẽ bị chệch. Nếu nền tảng tăng giá cước cơ sở cùng lúc với "
        "phí, gánh nặng của hành khách lớn hơn mức phí danh nghĩa.")
    rp.H3("1.2.2. Thách thức nhận dạng nhân quả")
    rp.PS(
        "Vùng CRZ không được chọn ngẫu nhiên. Đây là khu trung tâm thương mại và du lịch, có nhịp mùa vụ khác hẳn các quận "
        "ngoài: đông vào dịp lễ cuối năm, thưa vào mùa hè, nhạy với lượng khách du lịch và lịch làm việc tại văn phòng. Nếu "
        "so sánh đơn giản năm 2025 với năm 2024, ta trộn lẫn tác động của phí với xu hướng riêng của khu trung tâm. Nếu so "
        "sánh CRZ với vùng ngoài trong cùng tuần, ta phải giả định hai nhóm có xu hướng song song khi không có chính sách, "
        "một giả định cần được kiểm tra chứ không thể chấp nhận mặc nhiên.",
        "Một thách thức khác là sự chồng lấn thấp giữa nhóm xử lý và nhóm đối chứng. Các cặp điểm đón – điểm trả chạm CRZ "
        "có quãng đường, tốc độ và giá cước khác biệt có hệ thống so với các cặp ở quận ngoài. Các phương pháp học máy nhân "
        "quả chỉ cho kết quả đáng tin trong vùng mà hai nhóm có đặc trưng tương tự nhau, và vùng này cần được xác định bằng dữ "
        "liệu.")
    rp.H3("1.2.3. Thách thức kỹ thuật dữ liệu")
    rp.PS(
        "Ở góc độ kỹ thuật, vấn đề là làm sao biến gần sáu trăm triệu bản ghi thô thành các bảng phân tích đáng tin, trong "
        "điều kiện tài nguyên hạn chế, với quy trình có thể chạy lại và kiểm tra. Lược đồ dữ liệu thay đổi giữa hai năm "
        "(cột cbd_congestion_fee chỉ xuất hiện từ tháng 01/2025), một phần bản ghi có vùng không xác định hoặc giá trị bất "
        "thường, và ranh giới đường 60 cắt ngang một số vùng taxi. Mỗi lựa chọn xử lý ở đây đều ảnh hưởng đến kết quả nhân "
        "quả, nên cần được ghi lại và đo lường.")

    rp.H2("1.3. Mục tiêu nghiên cứu")
    rp.H3("1.3.1. Mục tiêu tổng quát")
    rp.P("Đồ án nhằm đánh giá tác động nhân quả của phí vùng giảm ùn tắc Manhattan lên thị trường gọi xe công nghệ, "
         "bao gồm nhu cầu, điều kiện di chuyển, giá cước và thu nhập tài xế, đồng thời xây dựng một pipeline dữ liệu lớn "
         "theo kiến trúc Lakehouse đủ tin cậy để các ước lượng có thể được tái lập.")
    rp.H3("1.3.2. Mục tiêu cụ thể")
    rp.BUL([
        "Xây dựng pipeline Bronze–Silver–Gold xử lý toàn bộ dữ liệu HVFHV và taxi vàng 2024–2025, có kiểm soát chất lượng, "
        "ghi nhật ký và đo hiệu năng.",
        "Xác định tập vùng chịu phí bằng dữ liệu thay vì gán tay, và nhận diện các vùng nằm vắt qua ranh giới.",
        "Ước lượng tác động trung bình của phí lên số chuyến, tốc độ, thời gian chờ, giá cước, chi phí hành khách và thu "
        "nhập tài xế bằng nhiều thiết kế nhận dạng khác nhau.",
        "Ước lượng tác động không đồng nhất theo loại luồng, khung giờ, ngày trong tuần và đặc trưng của cặp điểm đón – "
        "điểm trả bằng học máy nhân quả.",
        "Đo hiệu ứng lan tỏa không gian sang các vùng lân cận ranh giới.",
        "Kiểm tra độ tin cậy của các kết luận bằng giả dược theo thời gian, giả dược theo không gian, suy luận hoán vị và "
        "một loạt đặc tả thay thế.",
        "Tái lập bảng phân tích chính bằng Apache Spark để đối chứng chéo với DuckDB, và đo tác động của các cơ chế xử lý phân tán "
        "(tối ưu truy vấn, xáo trộn, lưu đệm, cắt tỉa phân vùng, Arrow, xử lý luồng) trên chính dữ liệu của đề tài.",
        "Đánh giá quản trị dữ liệu và rủi ro của tài sản dữ liệu: danh mục, phả hệ, tính toàn vẹn, giám sát chất lượng, phát hiện "
        "bất thường, rủi ro tái nhận dạng và khả năng công bố có quyền riêng tư vi phân.",
        "Chuyển kết quả thành thông tin cho quyết định kinh doanh: tác động theo hãng, dự báo nhu cầu, quy mô dữ liệu cần cho thử "
        "nghiệm, định giá động và giá trị của tài sản dữ liệu.",
    ], numbered=True)

    rp.H2("1.4. Câu hỏi nghiên cứu")
    rp.H3("1.4.1. Năm câu hỏi nghiên cứu")
    rp.BUL([
        "**RQ1.** Kiến trúc Lakehouse với DuckDB và Parquet có xử lý được toàn bộ dữ liệu trong điều kiện tài nguyên hạn "
        "chế không, các lựa chọn định dạng và bộ máy xử lý ảnh hưởng thế nào đến chi phí tính toán, và một bộ máy phân tán "
        "(Apache Spark) có tái lập đúng kết quả với chi phí bao nhiêu trên cùng phần cứng?",
        "**RQ2.** Phí CRZ làm thay đổi số chuyến gọi xe chạm vùng và điều kiện di chuyển, thể hiện qua tốc độ chuyến đi và "
        "thời gian chờ xe, bao nhiêu so với phản thực không có chính sách?",
        "**RQ3.** Tác động có khác nhau giữa loại luồng, khung giờ, ngày trong tuần và đặc trưng chuyến đi không, và có lan "
        "sang các vùng lân cận ranh giới không?",
        "**RQ4.** Tài sản dữ liệu của đồ án có những rủi ro nào về toàn vẹn, chất lượng và quyền riêng tư, và có thể công bố "
        "dữ liệu tổng hợp bảo vệ quyền riêng tư mà vẫn giữ được kết luận chính sách không?",
        "**RQ5.** Kết quả tạo ra thông tin gì cho quyết định kinh doanh, và phương pháp nào đáng tin cho từng loại quyết định?",
    ])
    rp.H3("1.4.2. Mức độ chắc chắn kỳ vọng của từng câu trả lời")
    rp.PS(
        "Các câu hỏi không có cùng mức độ trả lời được. RQ1 là câu hỏi kỹ thuật, được trả lời trực tiếp bằng số đo thời gian, "
        "dung lượng, bộ nhớ và phép đối chứng từng ô giữa hai bộ máy. RQ2 có cấu trúc nhận dạng rõ ràng, nên có thể trả lời bằng "
        "nhiều phương pháp độc lập để đối chiếu. RQ3 dựa trên các giả định mạnh hơn, đặc biệt là giả định chồng lấn trong học máy "
        "nhân quả. RQ4 lại là câu hỏi đo lường trực tiếp trên tài sản dữ liệu, nên có thể trả lời chắc chắn trong phạm vi phần "
        "cứng và dữ liệu của đồ án. RQ5 kết hợp cả hai loại, và độ tin cậy của từng câu trả lời phụ thuộc vào thiết kế được dùng. "
        "Đồ án chủ động báo cáo cả những trường hợp dữ liệu không đủ để kết luận.",
        "Câu hỏi phí được chuyển sang hành khách và tài xế như thế nào không được đặt thành câu hỏi nghiên cứu. Giá cước và thu "
        "nhập tài xế chịu ảnh hưởng của những thay đổi quy định và chiến lược giá khác diễn ra trong cùng giai đoạn, và dữ liệu TLC "
        "không có đủ thông tin để tách các yếu tố này. Các chỉ tiêu giá vẫn được ước lượng, nhưng chỉ để làm ví dụ về cách xu hướng "
        "có sẵn có thể tạo ra tác động giả trong thiết kế sai khác kép.")

    rp.H2("1.5. Phạm vi nghiên cứu")
    rp.H3("1.5.1. Phạm vi dữ liệu và thời gian")
    rp.PS(
        "Dữ liệu gồm hồ sơ chuyến HVFHV và taxi vàng từ ngày 01/01/2024 đến ngày 31/12/2025, cùng bảng tra vùng và bản đồ "
        "263 vùng taxi của TLC. Giai đoạn trước chính sách của phân tích chính kéo dài một năm (01/2024 – 04/01/2025), giai đoạn sau gần một năm "
        "(05/01/2025 – 31/12/2025). Dữ liệu 2022–2023 của cả hai dịch vụ được bổ sung để kiểm tra xu hướng trước chính sách trên "
        "ba năm (mục 3.2.4 và 4.14.4); các bảng Gold của phân tích chính không đổi. Đơn vị không gian nhỏ nhất là vùng taxi, vì TLC không công bố tọa độ chính xác để bảo vệ "
        "quyền riêng tư của hành khách.",
        "Taxi xanh và xe cho thuê thông thường không được đưa vào vì quy mô nhỏ và phần lớn hoạt động ngoài Manhattan. Lưu "
        "lượng xe con cá nhân không có trong dữ liệu TLC, nên đồ án không đo trực tiếp tổng lưu lượng giao thông vào vùng mà "
        "đo gián tiếp qua tốc độ của các chuyến gọi xe.")
    rp.H3("1.5.2. Phạm vi kết luận")
    rp.PS(
        "Kết luận của đồ án áp dụng cho thị trường gọi xe và taxi trong năm đầu thực hiện chính sách. Tác động dài hạn, tác động "
        "lên giao thông công cộng, chất lượng không khí, hoạt động kinh doanh trong vùng và việc phân bổ gánh nặng của phí giữa "
        "hành khách, tài xế và nền tảng nằm ngoài phạm vi. Các ước lượng về giá cước và thu nhập tài xế được trình bày như một "
        "phép kiểm tra phương pháp, kèm cảnh báo về xu hướng có sẵn, và không được dùng làm căn cứ cho khuyến nghị chính sách.")

    rp.H2("1.6. Phương pháp nghiên cứu tổng quát")
    rp.H3("1.6.1. Kỹ thuật dữ liệu lớn")
    rp.PS(
        "Pipeline được tổ chức theo mô hình medallion của kiến trúc Lakehouse. Lớp Bronze giữ nguyên các tệp Parquet gốc và "
        "chỉ lập danh mục metadata. Lớp Silver chuẩn hóa hai nguồn về một lược đồ chung, gắn cờ chất lượng và ghi lại các "
        "chuyến hợp lệ theo phân vùng dịch vụ – năm – tháng. Lớp Gold chứa bảy bảng tổng hợp phục vụ phân tích. DuckDB được "
        "dùng làm bộ máy tính toán nhúng, đọc Parquet trực tiếp theo cột, giới hạn bộ nhớ 1,8 GB và tràn ra đĩa khi cần. Mỗi "
        "tháng HVFHV được chia thành bốn khúc theo ngày để vừa bộ nhớ và giới hạn thời gian của môi trường chạy.")
    rp.H3("1.6.2. Suy luận nhân quả")
    rp.PS(
        "Thiết kế chính là sai khác kép trên panel vùng × tuần với hiệu ứng cố định vùng và tuần. Để xử lý mùa vụ riêng của "
        "khu trung tâm, đồ án bổ sung hiệu ứng cố định nhóm × tuần trong năm (sai khác bậc ba khử mùa vụ). Nghiên cứu sự kiện "
        "theo tuần và theo tháng cho phép quan sát động thái trước và sau chính sách. Kiểm soát tổng hợp xây dựng một \"CRZ "
        "giả định\" từ tổ hợp các vùng đối chứng. Học máy nhân quả (DML, AIPW, DR-learner) được áp dụng ở cấp cặp điểm đón – "
        "điểm trả để ước lượng tác động có điều kiện theo đặc trưng chuyến đi.")
    rp.H3("1.6.3. Kiểm định độ tin cậy")
    rp.PS(
        "Mỗi kết luận chính đi kèm ít nhất một phép thử có thể bác bỏ nó: giả dược theo thời gian với ngày chính sách giả "
        f"07/07/2024, giả dược theo không gian trong kiểm soát tổng hợp, suy luận hoán vị với {R.J['10_spillover_robustness_perm']['permutation']['n_perm']} "
        f"lần gán xử lý ngẫu nhiên và bảng độ vững gồm {len(R.t('t51'))} đặc tả thay thế. Sai số chuẩn được kiểm tra lại bằng sai số "
        "Conley có tương quan không gian, phân cụm hai chiều và wild cluster bootstrap, kèm hiệu chỉnh kiểm định bội; giả định xu "
        "hướng song song được kiểm tra trên dữ liệu 2022–2025 với sáu dạng xu hướng và phân tích độ nhạy Rambachan–Roth. Những chỉ "
        "tiêu không vượt qua được các phép thử này được báo cáo là chưa xác định được tác động.")

    rp.H3("1.6.4. Xử lý phân tán, quản trị dữ liệu và phân tích kinh doanh")
    rp.PS(
        "Ba mô-đun mở rộng bám theo các chương còn lại của bài giảng. Mô-đun xử lý phân tán chạy Apache Spark trên cùng lớp Silver, "
        "tái lập bảng Gold chính và so sánh từng ô với bản của DuckDB, rồi đo tám thực nghiệm về hiệu năng và cơ chế. Mô-đun quản trị "
        "dữ liệu và rủi ro áp dụng danh mục dữ liệu, phả hệ, dấu băm, đối soát, biểu đồ kiểm soát, phát hiện bất thường, k-ẩn danh và "
        "quyền riêng tư vi phân lên chính tài sản dữ liệu. Mô-đun phân tích kinh doanh ước lượng tác động theo hãng, so sánh dự báo nhu "
        "cầu với suy luận nhân quả, tính công suất thống kê theo độ dài giai đoạn quan sát và hạch toán tài nguyên.")

    rp.H2("1.7. Đóng góp của nghiên cứu")
    rp.H3("1.7.1. Đóng góp về phương pháp dữ liệu")
    rp.PS(
        "Đồ án cho thấy một pipeline Lakehouse hoàn chỉnh cho gần sáu trăm triệu bản ghi có thể chạy trên máy tính cá nhân "
        "với khoảng 3 GB RAM, nhờ xử lý theo phân vùng, đọc theo cột và tổng hợp sớm. Các thực nghiệm hiệu năng được đo trên "
        "chính dữ liệu của đề tài, không dùng số liệu tham khảo. Cách xác định vùng xử lý từ dữ liệu, dựa vào tỷ lệ chuyến "
        "nội vùng bị thu phí, là một thủ tục có thể áp dụng lại cho các chính sách có ranh giới không trùng với ranh giới "
        "đơn vị thống kê.")
    rp.H3("1.7.2. Đóng góp về bằng chứng thực nghiệm")
    rp.PS(
        "Đồ án bổ sung cho ước lượng trung bình đã có bằng ba lớp bằng chứng: tác động lên tốc độ và thời gian chờ như thước "
        "đo trực tiếp của ùn tắc; tác động không đồng nhất theo loại luồng, khung giờ và đặc trưng chuyến đi; và hiệu ứng lan "
        "tỏa theo khoảng cách tới ranh giới. Đồ án cũng chỉ ra rằng việc chọn Manhattan phía bắc làm nhóm đối chứng dẫn đến "
        "đánh giá thấp tác động do chính các vùng này chịu ảnh hưởng gián tiếp. Với dữ liệu 2022–2025, đồ án còn cho thấy "
        "một phần lớn mức giảm số chuyến mà thiết kế một năm tìm thấy trùng với xu hướng có sẵn, trong khi tác động lên thời gian chờ, "
        "và ở mức độ thấp hơn là tốc độ, vẫn đứng vững qua các giả định xu hướng khác nhau.")
    rp.P("Về lý thuyết, đồ án xây dựng một mô hình đơn giản kết hợp cầu theo chi phí tổng quát, hàm tốc độ – lưu lượng, lan tỏa qua "
         "mạng chuyến đi và phân bổ gánh nặng, suy ra tám giả thuyết định lượng và kiểm định chúng bằng các đặc tả liều – đáp ứng thiết "
         "kế riêng. Kết quả chỉ ra nơi mô hình chuẩn giải thích tốt và nơi nó cần được mở rộng.")
    rp.H3("1.7.3. Đóng góp về tính minh bạch")
    rp.PS(
        "Toàn bộ số liệu trong báo cáo được sinh tự động từ tệp kết quả. Bộ mã nguồn gồm các bước đánh số từ 00 đến 21 có thể "
        "chạy lại từ đầu. Một lỗi ép kiểu trong chính pipeline, được phát hiện nhờ đối chứng với Spark, được báo cáo cùng cách sửa "
        "và phạm vi ảnh hưởng. Những kết quả không vững, như tác động lên giá cước, được báo cáo cùng lý do không vững thay vì bị "
        "lược bỏ.")

    rp.H2("1.8. Cấu trúc của báo cáo")
    rp.PS(
        "Ngoài phần mở đầu, báo cáo gồm chín chương. Chương 1 giới thiệu bối cảnh, vấn đề, mục tiêu và câu hỏi nghiên cứu. "
        "Chương 2 trình bày cơ sở lý thuyết về định giá ùn tắc, thị trường gọi xe, kiến trúc dữ liệu lớn và các phương pháp "
        "suy luận nhân quả, đồng thời tổng quan các nghiên cứu liên quan. Chương 3 mô tả dữ liệu, kiến trúc pipeline, quy "
        "tắc chất lượng và chiến lược nhận dạng. Chương 4 trình bày kết quả, từ hiệu năng pipeline đến các ước lượng nhân quả "
        "và phép thử độ tin cậy. Chương 5 đưa Apache Spark vào để đối chứng chéo và phân tích hiệu năng xử lý phân tán. Chương 6 "
        "đánh giá quản trị dữ liệu, quyền riêng tư và rủi ro. Chương 7 chuyển kết quả sang góc nhìn kinh doanh và chiến lược dữ "
        "liệu. Chương 8 thảo luận ý nghĩa, hàm ý quản trị và hạn chế. Chương 9 kết luận và nêu hướng nghiên cứu tiếp theo.",
        "Phần phụ lục gồm hồ sơ chi tiết theo từng vùng, bảng theo tháng và theo khung giờ, bảng hệ số đầy đủ của các nghiên "
        "cứu sự kiện, danh mục tệp kết quả, nhật ký xử lý phân tán và quản trị dữ liệu, và toàn bộ mã nguồn của pipeline.")
