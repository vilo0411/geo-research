# Chiến lược GEO cho công ty chứng khoán (CTCK)

Áp dụng phương pháp "reverse engineering" của bài quangsilic.com/geo-nha-khoa: đo trước, sửa sau. Hai chỉ số đo:
- **Mention**: ChatGPT có nhắc tên thương hiệu trong câu trả lời không.
- **Citation**: link nguồn có dẫn về website của thương hiệu không.

> `{BRAND}` = thương hiệu của bạn. Cấu hình tên, alias, domain và đối thủ trong `config/brand.json` và `config/entities.csv`.

---

## 1. Bảy nhóm câu hỏi theo hành trình khách

Bộ đầy đủ có 60 câu trong `config/prompts.csv`. Cột cuối bảng là giả thuyết, phải kiểm chứng bằng dữ liệu tháng đầu chứ không áp nguyên từ ngành nha khoa.

| Nhóm | Khách đang ở đâu | Giả thuyết |
|---|---|---|
| 1_kien_thuc | Tìm hiểu chứng khoán, margin, T+2 | Nguồn là báo hoặc trang kiến thức, ít nhắc tên CTCK. Blog kiến thức không phải đường vào chính |
| 2_chon_ctck | "Nên mở tài khoản ở đâu", "phí thấp nhất", "app cho người mới" | Toplist và báo chi phối. Đây là nhóm **có giá trị nhất** để được nhắc tên |
| 3_phi_margin | Phí giao dịch, lãi margin, phí lưu ký | Trang biểu phí HTML có con số và ngày hiệu lực sẽ được trích dẫn |
| 4_mo_tai_khoan | Giấy tờ, thời gian, đối tượng đặc biệt | Trang hướng dẫn cụ thể thắng |
| 5_san_pham | Trái phiếu, chứng chỉ quỹ, phái sinh, chứng quyền | Trang trả lời từng câu hỏi sản phẩm |
| 6_xac_minh | "{BRAND} có uy tín / lừa đảo không", website chính thức | Rủi ro thương hiệu. Kiểm tra độ chính xác hằng tháng |
| 7_van_hanh | Nạp/rút tiền, lỗi app, hotline | Trang hỗ trợ, liên hệ và Google Business Profile |

## 2. Các trang cần làm tốt (theo thứ tự ưu tiên)

Trong nghiên cứu nha khoa, trang **liên hệ (61%)**, **giới thiệu (38%)** và **trả góp (34%)** được trích dẫn nhiều hơn hẳn blog (13%). Điểm chung là thông tin thực tế, dễ kiểm chứng. Với CTCK, các trang tương đương là:

1. **Biểu phí và lãi suất margin**
   - Một URL riêng, bảng HTML (không dùng PDF hay ảnh), có ngày hiệu lực.
   - 2–3 câu trả lời thẳng ở đầu trang, ví dụ: "Phí giao dịch cổ phiếu tại {BRAND} là X%, lãi margin từ Y%/năm, áp dụng từ dd/mm/yyyy."
   - Link sang trang danh mục margin và trang mở tài khoản.
2. **Danh mục cổ phiếu được margin**: dạng HTML, có ngày cập nhật.
3. **Hướng dẫn mở tài khoản online**
   - Các bước, giấy tờ, thời gian kích hoạt.
   - Trường hợp đặc biệt: người nước ngoài, người dưới 18 tuổi, mở qua app ngân hàng.
4. **Về chúng tôi / pháp lý**
   - Tên pháp lý đầy đủ, số giấy phép thành lập và hoạt động do UBCKNN cấp, vốn điều lệ, cổ đông lớn.
   - Tư cách thành viên HOSE, HNX, VSDC.
   - Đây là tín hiệu "xác minh" mà ChatGPT tự đi tìm. Trong ví dụ nha khoa, Otis được trích dẫn nhờ số giấy phép ở footer.
5. **Liên hệ, chi nhánh, phòng giao dịch**
   - Địa chỉ có số nhà, giờ làm việc, hotline.
   - Mỗi chi nhánh có một trang riêng và một Google Business Profile khớp với website.
   - Footer liệt kê toàn bộ chi nhánh.
6. **Trang sản phẩm**: mỗi câu hỏi phổ biến có một trang trả lời riêng, mở đầu bằng câu trả lời thẳng.
7. **Trang so sánh có số liệu thật**, ví dụ "{BRAND} so với mặt bằng phí thị trường". Bắt buộc qua compliance duyệt.

Không thêm FAQ hay schema chỉ vì "tốt cho AI". Nghiên cứu gốc không thấy chúng đi kèm tỷ lệ trích dẫn cao hơn. Nếu website đã có thì cứ giữ.

## 3. Nguồn bên thứ ba và nội dung "chiều 2"

- **Chiều 1** ("{BRAND} là công ty chứng khoán…") thì website nào cũng có. **Chiều 2** ("muốn margin lãi thấp, nhiều người chọn {BRAND} vì…") thường do người khác viết. Đây là thứ giúp ChatGPT nghĩ đến bạn khi khách hỏi chung chung (Reversal Curse).
- Các kênh tạo chiều 2:
  - Toplist và bài so sánh CTCK trên báo (CafeF, Vietstock, VnExpress…).
  - Review trên App Store và Google Play.
  - Video hướng dẫn trên YouTube.
  - Chuyên gia của bạn được trích ý kiến trên báo.
  - Thảo luận thật trên F319 và các nhóm Facebook.
- **Đa dạng nguồn và cách thể hiện**: kết hợp PR, toplist, video, hướng dẫn, review. Đăng một thông cáo y hệt lên 10 báo không giúp được nhiều.
- **Đồng bộ thông tin**: tên, giấy phép, phí, hotline phải giống nhau ở mọi nơi. Hằng tháng rà các bài "top CTCK" có nhắc {BRAND} để phát hiện số phí cũ hoặc sai. Mục 9 trong báo cáo tháng chỉ ra nguồn gây sai.
- **Không làm**: review giả, tài khoản ảo trên diễn đàn, nội dung AI viết hàng loạt, site vệ tinh. Trong nghiên cứu nha khoa, Reddit được trích dẫn đúng 1 lần dù xuất hiện rất nhiều trong kết quả tìm.

## 4. Checklist kỹ thuật (giao đội web)

1. robots.txt, Cloudflare và WAF **không chặn** `OAI-SearchBot` và `ChatGPT-User`. Chặn hay mở `GPTBot` (bot thu thập dữ liệu huấn luyện) là quyết định kinh doanh.
2. Phí, margin, giờ, địa chỉ, giấy phép phải có trong HTML gốc, không chỉ hiện sau khi chạy JavaScript, không nằm trong ảnh hay PDF.
3. Canonical đúng cho URL có tham số.
4. Schema `Organization` / `FinancialService` có `legalName`, `alternateName` (tên viết tắt, tên app) và `sameAs` (fanpage, YouTube, trang app store, trang UBCKNN).
5. Nếu ChatGPT đoán sai tên miền (xem câu Q050): sở hữu các tên miền dễ nhầm và chuyển hướng 301.
6. Trang đã xóa vĩnh viễn trả mã 410. Rà lại URL cũ của biểu phí để ChatGPT không trích dẫn số liệu lỗi thời.

## 5. Tuân thủ (YMYL tài chính)

- Không cam kết lợi nhuận, không khuyến nghị mã cổ phiếu trong nội dung SEO/GEO.
- Mọi số phí và lãi đều ghi ngày hiệu lực.
- Nội dung so sánh với đối thủ, PR và toplist phải qua pháp chế và compliance.
- Nhóm 6_xac_minh ("lừa đảo", "uy tín") là kênh cảnh báo sớm khủng hoảng truyền thông. Theo dõi riêng nhóm này.

## 6. Roadmap 90 ngày

| Giai đoạn | Việc chính | Kết quả |
|---|---|---|
| Ngày 0–30 | Pilot 5 chat để xác minh file export. Điền `brand.json` và `entities.csv`. Đo baseline đủ 214 lượt. Audit trang 1–5 ở mục 2. Gửi checklist kỹ thuật. | Báo cáo baseline. Danh sách trang thiếu. Danh sách thông tin sai |
| Ngày 31–60 | Làm hoặc sửa trang biểu phí/margin, mở tài khoản, pháp lý, liên hệ/chi nhánh. Chuẩn hóa Google Business Profile và hồ sơ bên ngoài. Đo tháng 2. | Citation rate nhóm 3, 4, 7 tăng |
| Ngày 61–90 | Trang trả lời từng câu hỏi sản phẩm. Kế hoạch nội dung chiều 2 (PR, toplist, video, review). Đo tháng 3. | Mention rate và SoV nhóm 2 tăng |
| Sau 90 ngày | Đo và báo cáo hằng tháng. Điều chỉnh bộ câu hỏi theo GSC. | |

Lưu ý khi đọc số: mỗi tháng chỉ có khoảng 214 lượt và ChatGPT dao động nhiều giữa các lượt. Chênh lệch dưới 10 điểm % giữa hai tháng chưa đủ để kết luận. Nên nhìn xu hướng qua nhiều tháng và khi gộp theo nhóm câu hỏi.
