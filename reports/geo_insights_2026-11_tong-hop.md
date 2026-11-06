# ChatGPT nói gì về Chứng khoán DSC? Phân tích tháng 11/2026

Báo cáo này dựa trên 214 lượt hỏi (60 câu hỏi, mỗi câu 3–5 lượt), chạy bằng Codex CLI ngày 06/11/2026, có tìm web. Bảng số liệu chi tiết nằm ở `geo_insights_2026-11_codex.md`. Toàn văn câu trả lời nằm ở `data/2026-11/codex/geo_answers.csv`.

> **Giới hạn cần biết trước khi đọc.** Codex là bản xấp xỉ của ChatGPT web, không giống hệt. Chưa có số đối chiếu với chatgpt.com (còn chờ 20 lượt hỏi tay). Riêng phát hiện 2 (lệnh tìm `site:`) có thể là thói quen của Codex nhiều hơn của ChatGPT web, vì vậy cần đối chiếu trước khi dùng phát hiện này để ra quyết định lớn. Mỗi câu hỏi chỉ có 3–5 lượt, nên đọc theo xu hướng, không đọc từng điểm %.

---

## Tóm tắt

1. **Khi khách chưa biết DSC, ChatGPT gần như không bao giờ giới thiệu DSC.** Trong 148 lượt hỏi chung chung, DSC chỉ được nhắc 1 lần (0,7%). TCBS được nhắc ở 77 lượt, SSI 69 lượt, VNDIRECT 65 lượt.
2. **DSC bị loại trước khi ChatGPT tìm web, không phải sau khi đọc nội dung.** 86% lệnh tìm là lệnh `site:` nhắm thẳng vào domain các CTCK mà model đã chọn sẵn. DSC chỉ nhận 1 lệnh `site:` (SSI nhận 76). Lệnh đó xuất hiện sau khi một bài kiến thức của DSC tình cờ lọt vào kết quả tìm chung. Trang của DSC chỉ lọt vào kết quả tìm ở 5/148 lượt.
3. **Khi khách hỏi đích danh DSC, website DSC làm tốt.** ChatGPT nhận đúng website, hotline và địa chỉ. Biểu phí 0,1% được trích dẫn đúng và nhất quán. Ở câu "DSC hay SSI tốt hơn?", cả 5/5 lượt đều nêu DSC có lợi thế phí.
4. **Trang trả lời đúng một câu hỏi được trích dẫn gần như mọi lần.** Trang biểu phí cổ phiếu niêm yết được trích dẫn 12/13 lần (92%). Trang giới thiệu chỉ 1/14 lần (7%). PDF và bản tiếng Anh gần như không bao giờ được trích dẫn.
5. **Lãi margin của DSC là điểm mù.** Ba lượt hỏi cho ba câu trả lời khác nhau. Một lượt nói không xác minh được, vì trang chính sách chỉ ghi lãi suất "theo công bố của DSC từng thời kỳ".
6. **Hỏi "DSC có uy tín / lừa đảo không", 9/10 lượt nhắc chuyện bị xử phạt.** Khi đi tìm bằng chứng giấy phép, ChatGPT tìm thấy ở VSDC và UBCKNN, chứ không ở website DSC. Cũng ở các nguồn đó nó gặp luôn quyết định xử phạt.
7. **Mỗi nhóm câu hỏi có một nhóm nguồn mà ChatGPT tin.**
   - Câu hỏi kiến thức: cơ quan nhà nước (HOSE, VSDC, Chính phủ) và cả investor.gov của Mỹ.
   - Câu hỏi sản phẩm: các quỹ đầu tư.
   - Câu hỏi xác minh: VSDC và UBCKNN.
   - Blog, toplist, diễn đàn và văn bản luật được đọc nhiều nhưng gần như không được trích dẫn.
8. **Trung tâm hỗ trợ của đối thủ là "máy" tạo trích dẫn.** `help.tcbs.com.vn` được chọn ở 45% số lần được đọc, còn trang chính `tcbs.com.vn` chỉ 14%. Trang dạng hỗ trợ/hướng dẫn chiếm 38% link trích dẫn về website đối thủ.

<!-- chart:hero -->

---

## Phương pháp

| Mục | Chi tiết |
|---|---|
| Bộ câu hỏi | 60 câu, chia 7 nhóm theo hành trình khách: kiến thức, chọn CTCK, phí/margin, mở tài khoản, sản phẩm, xác minh, vận hành |
| Số lượt | 214. Nhóm "chọn CTCK" 5 lượt mỗi câu, các nhóm khác 3–5 lượt |
| Cách hỏi | `codex exec`, model gpt-6.1-sol, phiên tạm (không memory, không lịch sử), tìm web live, prompt trợ lý chat trung tính |
| Nhắc tên (mention) | Tên CTCK xuất hiện trong nội dung câu trả lời, không tính link |
| Trích dẫn (citation) | Câu trả lời có link về website CTCK đó |
| Được đọc (retrieved) | Trang có trong kết quả tìm web của lượt đó |
| Câu không nêu tên / có nêu tên | 42 câu không nêu tên DSC (148 lượt). 18 câu có nêu tên DSC (66 lượt) |

## ChatGPT trả lời từng nhóm câu hỏi như thế nào

Mỗi nhóm câu hỏi được trả lời theo một "công thức" riêng: tìm ở đâu, đọc loại nguồn nào, và tin loại nguồn nào để trích dẫn. **Tỷ lệ chọn** = số trang được trích dẫn / số trang được đọc của loại nguồn đó. Tỷ lệ chọn cao nghĩa là ChatGPT tin loại nguồn này.

<!-- chart:source_mix -->

| Nhóm | Cách ChatGPT tìm | Nguồn được tin (trích dẫn) | Nguồn được đọc nhưng bị bỏ qua | DSC nên làm gì |
|---|---|---|---|---|
| 1. Kiến thức (lô lẻ, T+2, margin là gì) | 100% lệnh `site:`, 70% nhắm vào **cơ quan nhà nước** (hsx.vn, vsd.vn, hnx.vn, chinhphu.vn). 7% tìm bằng tiếng Anh | Trang hỗ trợ của CTCK lớn 49% (SSI, VNDIRECT), cơ quan nhà nước 27%, **investor.gov (SEC Mỹ) 13%** | Blog kiến thức (đọc 5%, trích dẫn 0%), văn bản luật (đọc 4%, trích dẫn 0%) | Bài kiến thức của DSC không có mặt ở nhóm này. Cần viết theo kiểu trang hỗ trợ: trả lời thẳng, dẫn nguồn HOSE/VSDC, không viết dạng blog dài |
| 2. Chọn CTCK | 84% lệnh `site:`, 90% nhắm vào website các CTCK đã chọn sẵn. Các lệnh còn lại cũng ghi sẵn tên CTCK | **Website CTCK 89%**, chủ yếu trang biểu phí và trung tâm hỗ trợ | Toplist (đọc 8%, trích dẫn 2%), diễn đàn (đọc 3%, trích dẫn 0%), ngân hàng | Phải lọt vào danh sách ứng viên trước (xem phát hiện 2). Toplist không phải nơi được trích dẫn, mà là nơi để model *biết tới* DSC |
| 3. Phí và margin | 74% lệnh `site:`. Lệnh tìm ghi sẵn danh sách, ví dụ "lãi suất margin 2026 SSI HSC TCBS VPS" | Website CTCK 69%, website DSC 18% (chỉ ở câu có nêu tên DSC) | Toplist, blog | Công bố con số margin trên HTML (phát hiện 6) |
| 4. Mở tài khoản | 76% lệnh `site:`: CTCK 56%, **cơ quan nhà nước 20%**, ngân hàng 13%. Tìm theo điều luật cụ thể (Thông tư 120/2020) | Website CTCK 60%, DSC 19%, cơ quan nhà nước 15% | **Văn bản luật: đọc 14%, trích dẫn 0%**. Ngân hàng: đọc 10%, trích dẫn 2% | ChatGPT đọc luật để kiểm chứng, nhưng trích dẫn trang hướng dẫn của CTCK đã "dịch" luật sang ngôn ngữ thường. DSC nên có trang hướng dẫn cho từng trường hợp (dưới 18 tuổi, người nước ngoài, nhiều tài khoản), ghi rõ căn cứ pháp lý |
| 5. Sản phẩm (quỹ, trái phiếu, phái sinh) | 88% lệnh `site:` | Website CTCK 81%, **quỹ đầu tư: tỷ lệ chọn 28%, cao nhất mọi nhóm** (Dragon Capital) | Toplist, blog | Câu hỏi về chứng chỉ quỹ thì ChatGPT tin công ty quản lý quỹ. DSC nên có trang sản phẩm riêng cho từng câu hỏi |
| 6. Xác minh (uy tín, giấy phép) | 55% lệnh `site:`: 79% vào dsc.com.vn, 21% vào cơ quan nhà nước | Website DSC 55%, **cơ quan nhà nước 22%** (VSDC, UBCKNN), báo chí 9% | Trang dữ liệu tài chính (đọc 11%, trích dẫn 3%) | Ghi giấy phép và mã thành viên VSDC ngay trên website (phát hiện 7) |
| 7. Vận hành (nạp/rút, lỗi app, hotline) | 84% lệnh `site:`: DSC 47%, cơ quan nhà nước 37% (với câu khiếu nại) | Website DSC 54%, website CTCK khác 26%, cơ quan nhà nước 15% | **Công ty trùng tên DSC** (dsc-medical.vn, dscvietnam.vn): đọc 4%, trích dẫn 0% | Trang hỗ trợ của DSC đang làm tốt. Tên "DSC" bị trùng nên cần ghi tên đầy đủ "Chứng khoán DSC" ở tiêu đề trang |

Pattern giống nghiên cứu nha khoa: **câu hỏi kiến thức đi qua nguồn chính thống**, gồm cơ quan nhà nước Việt Nam và cả nguồn quốc tế. Ở bài quangsilic là AAO và NHS, ở đây là investor.gov của SEC Mỹ. Website doanh nghiệp chỉ được trích dẫn khi trang được viết như một trang hỗ trợ, không phải bài blog.

---

## Phát hiện 1: Với câu hỏi chung chung, DSC vắng mặt

<!-- chart:named -->

| CTCK | Số lượt được nhắc (trên 148 lượt không nêu tên) |
|---|---|
| TCBS | 77 |
| SSI | 69 |
| VNDIRECT | 65 |
| HSC | 20 |
| VPS | 19 |
| DNSE | 18 |
| Vietcap | 16 |
| **DSC** | **1** (câu Q031 "Người dưới 18 tuổi có mở được tài khoản không?", qua một bài kiến thức) |

Danh sách CTCK được nhắc rất ổn định giữa các lượt:

| Câu hỏi | CTCK được nhắc (số lượt / 5 lượt) |
|---|---|
| Q009 Nên mở tài khoản chứng khoán ở công ty nào? | SSI 5, TCBS 5, VNDIRECT 4 |
| **Q017 Mở tài khoản ở Hà Nội nên chọn công ty nào?** | SSI 5, TCBS 5, VNDIRECT 5. **DSC đặt hội sở ở Hà Nội nhưng 0/5** |
| Q011 App chứng khoán nào tốt cho người mới? | TCBS 5, VNDIRECT 5, SSI 2 |
| Q014 Sinh viên nên mở tài khoản ở đâu? | SSI 5, TCBS 5 |
| Q012 Top CTCK uy tín nhất | VPS 5, TCBS 5, SSI 5, Vietcap 4, VPBankS 4, MBS 4 |

<!-- chart:heatmap -->

Câu trả lời của ChatGPT cho nhóm câu hỏi này không ngẫu nhiên. Đó là một danh sách đóng gồm 3–6 tên, lặp lại gần như y hệt giữa các lượt. Muốn được nhắc tên thì DSC phải lọt vào danh sách này.

## Phát hiện 2: DSC bị loại từ bước chọn ứng viên, trước khi tìm web

Phễu hiển thị của từng CTCK trên 148 lượt không nêu tên:

<!-- chart:funnel -->

| CTCK | Nhận lệnh `site:` | Được đọc | Được trích dẫn | Được nhắc tên |
|---|---|---|---|---|
| SSI | 76 | 86 | 60 | 69 |
| TCBS | 67 | 82 | 71 | 77 |
| VNDIRECT | 55 | 75 | 57 | 65 |
| VPS | 28 | 41 | 9 | 19 |
| DNSE | 22 | 31 | 13 | 18 |
| Phú Hưng | 0 | 33 | 6 | 5 |
| **DSC** | **1** | **5** | **1** | **1** |

- **Có 487/566 lệnh tìm (86%) là dạng `site:ssi.com.vn …`.** Nghĩa là model quyết định cân nhắc CTCK nào *từ kiến thức sẵn có*, rồi mới vào website của chính các CTCK đó để lấy số liệu. Website một CTCK làm tốt đến đâu cũng không giúp gì nếu CTCK đó không có trong danh sách ban đầu.
- **Ngay cả các lệnh tìm không dùng `site:` cũng đã ghi sẵn tên CTCK**, ví dụ "phí giao dịch chứng khoán VPS SSI MBS 2026" hay "lãi suất margin 2026 SSI HSC TCBS VPS".
- **Rất ít lệnh tìm thật sự mở**, tức là ChatGPT tìm mà chưa có tên CTCK trong đầu. Những lệnh này đều nhắm vào **bảng xếp hạng**: "thị phần môi giới HOSE quý 3 2026", "công ty chứng khoán uy tín 2026 Vietnam Report top 10", và trang toplist `reviewchungkhoan.com` (xuất hiện trong kết quả tìm ở 66 lượt).
- So sánh với Phú Hưng: trang của Phú Hưng *được đọc* ở 33 lượt, vì xếp hạng tốt khi ChatGPT tìm chung chung, nhưng chỉ được nhắc tên 5 lần. Xếp hạng tìm kiếm tốt không đủ để được nhắc tên.

Link trích dẫn trong nhóm câu hỏi chọn CTCK trỏ thẳng về website các CTCK: 89%, trong khi báo chí và toplist chỉ chiếm 8%. Điều này khác ngành nha khoa, nơi các trang trung gian giữ vai trò lớn. Với CTCK, nguồn bên ngoài có tác dụng chủ yếu ở bước *đưa tên vào danh sách ứng viên*, không ở bước được trích dẫn.

<!-- chart:destination -->

**Ý nghĩa:** với nhóm câu hỏi chọn CTCK, vấn đề của DSC không nằm ở SEO on-page. Vấn đề là model không "biết" DSC là một lựa chọn khi khách hỏi về phí, app, người mới hay Hà Nội. Đây đúng là "chiều 2" trong file chiến lược: thông tin dạng "muốn X thì chọn DSC" phải xuất hiện ở các nguồn bên ngoài mà model học và tìm. Trước hết là các bảng xếp hạng thị phần, giải thưởng uy tín và bài toplist so sánh CTCK.

## Phát hiện 3: Khi được hỏi đích danh, DSC có lập luận tốt mà không được dùng ở câu hỏi chung

- **Q020 "DSC hay SSI tốt hơn?"**: cả 5/5 lượt kết luận DSC có lợi thế phí khi tự giao dịch: 0,1% với tài khoản do khối Tư vấn số quản lý, so với 0,15% của SSI khi giao dịch online.
- **Q023 và Q025 về phí của DSC**: các lượt đều nêu đúng 0,1% và 0,15–0,3%, kèm ngày hiệu lực 20/08/2025, trích dẫn trang biểu phí chính thức.
- **Q050 website chính thức, Q056 hotline và địa chỉ**: đúng ở mọi lượt.

Nhưng ở câu hỏi chung **Q010 "CTCK nào phí giao dịch thấp nhất?"**, danh sách là DNSE, Shinhan và TCBS (5/5 lượt), đều là các công ty miễn hoặc gần miễn phí. Mức 0,1% của DSC không thắng được nhóm miễn phí. Nó chỉ là lợi thế khi so với các CTCK lớn như SSI và VNDIRECT.

**Ý nghĩa:** thông điệp "chiều 2" phù hợp cho DSC không phải "phí thấp nhất". Thông điệp phù hợp là so với nhóm CTCK lớn, ví dụ "phí tự giao dịch 0,1%, thấp hơn mức 0,15% của các CTCK top đầu". Mọi nội dung so sánh phải qua compliance.

## Phát hiện 4: Trang trả lời đúng một câu hỏi được trích dẫn, trang tổng hợp thì không

Các trang DSC trong các lượt hỏi có nêu tên:

<!-- chart:brand_pages -->

| Trang DSC | Được đọc | Được trích dẫn | Tỷ lệ |
|---|---|---|---|
| /bieu-phi/bieu-phi-giao-dich-chung-khoan-niem-yet | 13 | 12 | **92%** |
| /bieu-phi | 20 | 15 | 75% |
| /dich-vu/chinh-sach-dich-vu-giao-dich-ky-quy | 22 | 11 | 50% |
| / (trang chủ) | 29 | 12 | 41% |
| /dich-vu/mo-tai-khoan | 13 | 5 | 38% |
| /huong-dan (trang tổng hợp hướng dẫn) | 25 | 7 | 28% |
| **/gioi-thieu** | 14 | 1 | **7%** |
| /tin-tuc/bieu-phi-dsc | 10 | 0 | 0% |

Kết quả này khớp với nghiên cứu nha khoa: trang trả lời một câu hỏi cụ thể, có con số và ngày hiệu lực, được trích dẫn nhiều hơn hẳn trang tổng hợp hay trang tin.

## Phát hiện 5: PDF và bản tiếng Anh chiếm suất đọc nhưng không được trích dẫn

Trên toàn bộ website các CTCK (DSC và đối thủ):

<!-- chart:format -->

| Định dạng | Được đọc | Được trích dẫn | Tỷ lệ |
|---|---|---|---|
| HTML tiếng Việt | 1.645 | 407 | 25% |
| PDF | 612 | 22 | **4%** |
| Bản tiếng Anh (/en/) | 123 | 6 | **5%** |

Riêng DSC, các trang sau được đọc nhiều mà gần như không được trích dẫn:
- `/en/bieu-phi`: đọc 23 lần, trích dẫn 0 lần. ChatGPT tìm bằng tiếng Việt nhưng nhận về bản tiếng Anh.
- `/en/dich-vu/chinh-sach-dich-vu-giao-dich-ky-quy`: đọc 11 lần, trích dẫn 0 lần.
- Tài liệu họp ĐHĐCĐ 2024 và 2025 dạng PDF: đọc 22, 17 và 7 lần, trích dẫn tổng cộng 2 lần.
- **`Chinh-sach-margin.pdf` năm 2023**: đọc 11 lần, trích dẫn 0 lần. Đây là tài liệu cũ nhưng vẫn được index và vẫn được đọc.

Mỗi lượt tìm chỉ đọc được một số trang có hạn. Khi bản tiếng Anh hay PDF cũ chiếm chỗ, trang tiếng Việt đúng sẽ mất cơ hội được chọn.

## Phát hiện 6: Lãi margin và thời gian nạp tiền không nhất quán

| Câu hỏi | Lượt 1 | Lượt 2 | Lượt 3 |
|---|---|---|---|
| Q024 Lãi margin DSC? | 13,5%/năm, lấy từ **báo Thương Gia** | "Chưa xác minh được": trang chính thức chỉ ghi "theo công bố của DSC từng thời kỳ" | 10–13,5%/năm |
| Q053 Nạp tiền mất bao lâu? | Realtime | 1–10 phút | 1–10 phút |

Khi trang chính thức không có con số, ChatGPT sẽ lấy từ báo, hoặc trả lời rằng không biết. Câu hỏi về margin quan trọng vì nó nằm trong nhóm câu hỏi so sánh lãi margin, nơi DNSE, KIS và TCBS đang được nhắc tên.

## Phát hiện 7: Câu hỏi xác minh dẫn ChatGPT đến quyết định xử phạt

| Câu hỏi | Số lượt nhắc xử phạt, thanh tra hoặc vi phạm |
|---|---|
| Q045 DSC có uy tín không? | 5/5 |
| Q046 DSC có lừa đảo không? | 4/5 |
| Q049 DSC có được UBCK cấp phép không? | 1/3 |

Các nội dung được nhắc: phạt 55 triệu đồng (tháng 2/2026) vì công bố thông tin chậm; phạt gần 700 triệu đồng (tháng 9/2025); kết luận thanh tra ngày 08/08/2025. Nguồn bên ngoài được trích dẫn nhiều nhất là vsdc.vn (9 lần) và ssc.gov.vn (5 lần).

Chuỗi xảy ra như sau:
1. Khách hỏi về uy tín.
2. ChatGPT đi tìm bằng chứng giấy phép.
3. Nó tìm thấy ở VSDC, hoặc ngay trong văn bản kết luận thanh tra của UBCKNN. Câu Q049 lượt 1 lấy số giấy phép từ chính kết luận thanh tra.
4. Cùng lúc, nó đọc được quyết định xử phạt.

Trang `/gioi-thieu` của DSC được đọc 14 lần nhưng chỉ được trích dẫn 1 lần.

Giọng điệu của các câu trả lời vẫn cân bằng, ví dụ "xử phạt hành chính không đồng nghĩa với lừa đảo". Đây là thông tin công khai, đúng sự thật, không thể và không nên tìm cách che giấu.

**Ý nghĩa:** việc nên làm là giúp ChatGPT tìm thấy bằng chứng giấy phép ngay trên website DSC, và đưa thông tin khắc phục một cách minh bạch.

## Phát hiện 8: Trung tâm hỗ trợ của đối thủ được trích dẫn gấp ba trang chính

<!-- chart:helpcenter -->

| Website | Được đọc | Được trích dẫn | Tỷ lệ chọn |
|---|---|---|---|
| help.tcbs.com.vn (trung tâm hỗ trợ TCBS) | 110 | 50 | **45%** |
| support.vndirect.com.vn (trung tâm hỗ trợ VNDIRECT) | 177 | 41 | 23% |
| ssi.com.vn | 263 | 74 | 28% |
| tcbs.com.vn (trang chính) | 208 | 29 | 14% |
| vndirect.com.vn (trang chính) | 158 | 26 | 16% |

Trang dạng hỗ trợ/hướng dẫn (help, support, FAQ, /huong-dan) chiếm **126/331 link trích dẫn về website đối thủ (38%)**. Mỗi trang này trả lời đúng một câu hỏi: "Biểu phí dịch vụ chứng khoán", "Phí giao dịch cơ sở theo gói". Chúng có bảng số liệu và được cập nhật thường xuyên.

Tính chung toàn bộ các trang `/huong-dan/*`, DSC chỉ đạt tỷ lệ chọn **21% (27/128)**. Mức này bằng nửa help.tcbs và còn thấp hơn trang chính của SSI. Trang `/huong-dan` của DSC là một trang tổng hợp: được đọc 25 lần, trích dẫn 7 lần.

---

## Việc nên làm, gắn với từng phát hiện

| # | Việc | Dựa trên | Chỉ số theo dõi tháng sau |
|---|---|---|---|
| 1 | **Đưa DSC vào các nguồn xếp hạng mà ChatGPT tìm khi chưa có tên CTCK**: thị phần môi giới, Vietnam Report và các bảng xếp hạng uy tín, giải thưởng, toplist so sánh CTCK (có `reviewchungkhoan.com`). Cần thông tin đúng và qua compliance | PH 2 | Số lượt DSC nhận lệnh `site:` và được nhắc tên ở câu hỏi không nêu tên (hiện 1 và 1/148) |
| 2 | **Nội dung "chiều 2" theo đúng nhu cầu khách**: "phí tự giao dịch 0,1%", "CTCK ở Hà Nội", "app cho người mới", qua báo chí, video và review | PH 1, 3 | Q009–Q019, đặc biệt Q017 Hà Nội (hiện 0/5) |
| 3 | **Công bố lãi margin bằng con số trên trang HTML** `/dich-vu/chinh-sach-dich-vu-giao-dich-ky-quy`, có ngày hiệu lực. Không chỉ ghi "theo công bố từng thời kỳ" | PH 6 | Q024: 3/3 lượt cùng một con số, trích dẫn dsc.com.vn |
| 4 | **Rút PDF margin năm 2023 khỏi index** (trả mã 410 hoặc thêm noindex). Rà các PDF biểu phí và chính sách cũ khác | PH 5 | PDF cũ không còn xuất hiện trong mục "được đọc" |
| 5 | **Kiểm tra hreflang và canonical giữa bản `/en/` và bản tiếng Việt** của biểu phí, margin và hướng dẫn | PH 5 | `/en/bieu-phi` không còn chiếm chỗ ở câu hỏi tiếng Việt |
| 6 | **Trang giới thiệu và footer ghi rõ**: số giấy phép 29/UBCK-GPHĐKD và ngày cấp, giấy phép điều chỉnh mới nhất, mã thành viên VSDC 024, tên pháp lý, tên cũ "Chứng khoán Đà Nẵng" | PH 7 | Tỷ lệ trích dẫn `/gioi-thieu` (hiện 1/14). Câu Q049 trích dẫn dsc.com.vn thay vì kết luận thanh tra |
| 7 | **Trang công bố thông tin hoặc quan hệ cổ đông**: nêu minh bạch các quyết định xử phạt và việc đã khắc phục (pháp chế duyệt nội dung) | PH 7 | Q045/Q046: câu trả lời có trích dẫn trang khắc phục của DSC |
| 8 | **Thống nhất thông tin nạp và rút tiền** giữa các trang hướng dẫn: realtime hay 1–10 phút | PH 6 | Q053: các lượt trả lời giống nhau |
| 9 | **Tách các trang hướng dẫn tổng hợp thành từng trang một câu hỏi**, mở đầu bằng câu trả lời thẳng | PH 4 | Tỷ lệ trích dẫn `/huong-dan` (hiện 28%) so với các trang con |
| 10 | **Xây trung tâm hỗ trợ theo kiểu help.tcbs**: mỗi câu hỏi một URL, tiêu đề là câu hỏi, câu trả lời thẳng ở đầu, có bảng số và ngày cập nhật | PH 8, nhóm 1, 4 | Tỷ lệ chọn các trang `/huong-dan/*` của DSC (hiện 21%) |
| 11 | **Bài kiến thức viết như trang hỗ trợ**, dẫn nguồn HOSE/VSDC/UBCKNN. Bỏ dạng blog dài | Nhóm 1 | DSC xuất hiện ở nhóm kiến thức (hiện 0 link) |
| 12 | **Ghi tên đầy đủ "Chứng khoán DSC"** ở tiêu đề và mô tả trang hỗ trợ, để không bị lẫn với các công ty trùng tên | Nhóm 7 | Trang trùng tên không còn chiếm suất đọc |

## Cần kiểm chứng

- **Nội dung thật của các trang DSC.** Tôi chưa xem trực tiếp `/gioi-thieu`, trang margin và `/en/bieu-phi`. Lần phân tích này không truy cập được website từ máy chạy phân tích. Các khuyến nghị 3, 5, 6 dựa trên câu trả lời của ChatGPT và số liệu đọc/trích dẫn. Cần mở trang thật để xác nhận.
- **Đối chiếu với ChatGPT web**: hỏi tay 20 lượt theo `data/2026-11/chatgpt/checklist.csv`, rồi chạy `python geo.py calibrate --month 2026-11`. Cần xem đặc biệt ChatGPT web có dùng lệnh `site:` nhiều như Codex không (phát hiện 2).
- **Duyệt độ chính xác** 58 lượt trong `review/accuracy_2026-11_codex.csv`. Ưu tiên các con số về margin, phí và xử phạt.
