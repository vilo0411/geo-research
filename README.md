# GEO tracker – đo ChatGPT nhắc tên và trích dẫn CTCK

Bộ công cụ đo xem ChatGPT nhắc tên (mention) và trích dẫn (citation) thương hiệu của bạn thế nào, so với các công ty chứng khoán khác. Chiến lược tổng thể nằm ở [docs/chien-luoc-geo-ctck.md](docs/chien-luoc-geo-ctck.md).

## Cách đo: 2 nguồn
| Nguồn | Cách chạy | Vai trò |
|---|---|---|
| `codex` | Tự động bằng Codex CLI, đủ 214 lượt mỗi tháng | Số đo chính, theo dõi xu hướng. **Gần đúng**, không giống hệt ChatGPT web |
| `chatgpt` | Hỏi tay trên chatgpt.com khoảng 20 lượt, rồi export | Đối chiếu: đo xem Codex lệch so với trải nghiệm thật bao nhiêu |

**Vì sao Codex không giống hệt ChatGPT web:** Codex dùng bộ model và công cụ tìm web riêng. Script đã thay system prompt lập trình bằng một prompt trợ lý chat trung tính (`config/codex_instructions.md`), nhưng không tái tạo được đúng ChatGPT web. Vì vậy mỗi tháng cần chạy `calibrate` để xem độ lệch.

**Cách cách ly mỗi lượt hỏi Codex** (để không có cache hay context lẫn vào):
- `codex exec --ephemeral`: không lưu session. Mỗi lượt là một phiên mới, không có lịch sử.
- Thư mục cấu hình Codex riêng `~/.codex-geo`: không dính AGENTS.md, skill, plugin hay memory của Codex bạn dùng để code.
- `--ignore-user-config`, `--ignore-rules`, `project_doc_max_bytes=0`, tắt shell, memories, apps, plugins.
- Mỗi lượt chạy trong một thư mục tạm trống, không thấy file nào của dự án.
- Tìm web để chế độ `live`, không dùng kết quả tìm đã lưu sẵn.
- Không dùng API key: script xóa `OPENAI_API_KEY` khỏi môi trường, chỉ dùng đăng nhập ChatGPT.

Phía OpenAI vẫn có *prompt caching*, thể hiện ở `cached_input_tokens`. Đây là bộ nhớ đệm phần prompt cố định ở đầu, chỉ để tính toán nhanh hơn. Nó không lưu câu trả lời và không làm câu trả lời giống nhau, và phía client không tắt được.

**Không tự động hóa (bot) giao diện chatgpt.com.** Điều khoản OpenAI cấm, và tài khoản có thể bị khóa.

## Cài đặt một lần
1. Cần Python 3.10 trở lên (chỉ dùng thư viện chuẩn) và Codex CLI.
2. Sửa `config/brand.json`: tên thương hiệu, alias, domain.
3. Đăng nhập Codex vào thư mục riêng, chọn "Sign in with ChatGPT":
   ```powershell
   $env:CODEX_HOME = "$HOME\.codex-geo"; codex login; Remove-Item Env:CODEX_HOME
   ```
4. Sửa `config/codex.json`:
   - `model`: chọn model gần nhất với model mặc định trên chatgpt.com.
   - `workers`: số lượt chạy song song, mặc định 3.
5. Cho tài khoản dùng để hỏi tay: vào Settings → Personalization, **tắt Memory** và **Reference chat history**, để trống Custom instructions.

## Quy trình mỗi tháng

```powershell
cd E:\project\geo-research
# 1. Codex tự hỏi 214 lượt (khoảng 40 phút với 3 luồng), rồi tự parse
python geo.py codex-run --month 2026-12
#    Nếu chạm giới hạn sử dụng của gói Plus, script dừng và giữ kết quả đã có. Chạy lại cùng lệnh để làm tiếp.
#    Chạy thử vài lượt trước:  python geo.py codex-run --month 2026-12 --only Q009 --limit 2

# 2. Lấy danh sách khoảng 20 lượt cần hỏi tay trên chatgpt.com
python geo.py checklist --month 2026-12          # -> data\2026-12\chatgpt\checklist.csv
```
3. Hỏi tay từng dòng trong `checklist.csv`:
   - Mở **New chat**, dùng model mặc định.
   - Dán đúng câu hỏi trong cột `question` rồi gửi.
   - Đổi tên chat theo cột `chat_title`, ví dụ `Q017-r1`.
   - Không dùng Temporary chat, không regenerate, không bật VPN.
4. Vào Settings → Data controls → Export data. Giải nén `conversations.json` vào `exports\2026-12\`, rồi chạy:
   ```powershell
   python geo.py parse exports\2026-12\conversations.json --month 2026-12
   python geo.py calibrate --month 2026-12          # -> reports\calibration_2026-12.md
   python geo.py report --month 2026-12             # -> reports\geo_report_2026-12_codex.md
   python geo.py insights --month 2026-12           # -> reports\geo_insights_2026-12_codex.md
   ```
   - `insights` tính các bảng phân tích theo kiểu quangsilic:
     - Phễu "nhận lệnh `site:` → được đọc → được trích dẫn → được nhắc tên" của từng CTCK.
     - Danh sách CTCK được nhắc theo từng câu hỏi.
     - Link trích dẫn trỏ về đâu theo nhóm câu hỏi.
     - Trang của thương hiệu được đọc so với được trích dẫn.
     - Tỷ lệ trích dẫn theo định dạng trang: PDF, bản `/en/`, HTML.
     - Con số về thương hiệu có nhất quán giữa các lượt không.
     - Rủi ro danh tiếng.
   - Dựa trên các bảng đó, viết bản tổng hợp insight, ví dụ `reports\geo_insights_2026-11_tong-hop.md`.
   - Xuất PDF kèm biểu đồ: `python report_pdf.py --month 2026-12`.
     - Script đọc file `*_tong-hop.md` và chèn biểu đồ vào chỗ có đánh dấu `<!-- chart:named|heatmap|funnel|destination|brand_pages|format|hero -->`.
     - Ảnh PNG của từng biểu đồ lưu ở `reports\charts_<tháng>\`.
     - Script này cần `matplotlib` và `reportlab`. Riêng `geo.py` vẫn chỉ dùng thư viện chuẩn.
5. Đối thủ mới: mở `data\2026-12\codex\entity_candidates.csv`. File này liệt kê các tên hoặc domain giống CTCK nhưng chưa có trong `config\entities.csv`. Thêm những tên đúng là CTCK vào `entities.csv`, rồi chạy lại `parse` và `report`.
6. Duyệt độ chính xác trong `review\accuracy_2026-12_codex.csv`:
   - Cột `is_accurate`: điền `dung` hoặc `sai`.
   - Cột `wrong_fact`: ghi thông tin bị sai.
   - Cột `source_of_error`: ghi domain gây sai.

   Đối chiếu với câu trả lời trong `data\2026-12\codex\geo_answers.csv`. Duyệt xong thì chạy lại `report`.

Lần đầu export ChatGPT: chạy `python geo.py inspect exports\...\conversations.json` để kiểm tra các trường dữ liệu có trong file, vì OpenAI không công bố định dạng file này.

## Các chỉ số trong báo cáo
| Chỉ số | Cách tính |
|---|---|
| Mention rate | Số lượt có tên thương hiệu trong câu trả lời / tổng số lượt |
| Citation rate | Số lượt có ít nhất 1 link về domain chính chủ / tổng số lượt |
| Owned citation share | Trong các lượt có nhắc tên thương hiệu: số link về domain chính chủ / tổng số link |
| Share of voice | Số lượt nhắc thương hiệu / tổng số lượt nhắc mọi CTCK |
| Loại trang được đọc và được trích dẫn | Loại trang nào trên website CTCK được chọn làm nguồn |

## File
- `exports\<tháng>\codex\Qxxx-rN.json`: output gốc của từng lượt Codex. Có trường `ok`; các lượt lỗi sẽ được chạy lại.
- `data\<tháng>\<codex|chatgpt>\`:
  - `geo_runs.csv`, `geo_mentions.csv`, `geo_citations.csv`, `geo_retrieved.csv`, `geo_queries.csv`, `geo_answers.csv`
  - `entity_candidates.csv`: ứng viên đối thủ mới.
- `reports\`: `geo_report_<tháng>_<nguồn>.md` và `calibration_<tháng>.md`.

## Kiểm thử
```powershell
$env:GEO_WORKDIR = "$env:TEMP\geo-test"; python geo.py parse tests\fixture_conversations.json; python geo.py report --source chatgpt; Remove-Item Env:GEO_WORKDIR
```
`tests/fixture_conversations.json` là dữ liệu **giả lập** export ChatGPT, không phải export thật.
