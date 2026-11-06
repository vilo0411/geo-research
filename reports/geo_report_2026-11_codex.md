# Báo cáo GEO – Chứng khoán DSC – tháng 2026-11 – Codex CLI (tự động)

Nguồn: Codex CLI (`codex exec`), model gpt-6.1-sol. Mỗi lượt là một phiên tạm, không memory, không context dự án, tìm web live. **Đây là số đo gần đúng cho ChatGPT web, không giống hệt**: xem độ lệch ở `reports/calibration_2026-11.md`. So sánh với: không có tháng trước.

## 1. Chỉ số chính

| Chỉ số | Tháng này | Tháng trước | Thay đổi |
|---|---|---|---|
| Mention rate (lượt có nhắc tên thương hiệu) | 31% | – | – |
| Citation rate (lượt có link về website chính chủ) | 27% | – | – |
| Owned citation share (link chính chủ / tổng link, trong các lượt có nhắc tên) | 68% | – | – |
| Share of voice (lượt nhắc thương hiệu / tổng lượt nhắc mọi CTCK) | 16% | – | – |
| Tỷ lệ lượt ChatGPT có tìm web | 100% | – | – |

Tổng số lượt đo: 214

### Câu hỏi không nêu tên thương hiệu và câu hỏi có nêu tên

Câu hỏi đã chứa tên thương hiệu thì gần như luôn được nhắc tên. **Chỉ số phản ánh mức độ ChatGPT tự giới thiệu thương hiệu là ở dòng "không nêu tên".**

| Loại câu hỏi | Lượt | Mention | Δ | Citation | Δ | SoV |
|---|---|---|---|---|---|---|
| Không nêu tên thương hiệu | 148 | 1% | – | 1% | – | 0% |
| Có nêu tên thương hiệu | 66 | 100% | – | 86% | – | 93% |

## 2. Theo nhóm câu hỏi

| Nhóm | Lượt | Mention | Δ | Citation | Δ | SoV |
|---|---|---|---|---|---|---|
| 1_kien_thuc | 24 | 0% | – | 0% | – | 0% |
| 2_chon_ctck | 60 | 8% | – | 8% | – | 2% |
| 3_phi_margin | 24 | 38% | – | 38% | – | 14% |
| 4_mo_tai_khoan | 24 | 17% | – | 17% | – | 11% |
| 5_san_pham | 24 | 0% | – | 0% | – | 0% |
| 6_xac_minh | 34 | 100% | – | 74% | – | 100% |
| 7_van_hanh | 24 | 62% | – | 62% | – | 65% |

## 3. Share of voice theo CTCK

| CTCK | Lượt được nhắc | % lượt | Lần đứng đầu câu trả lời | Link trích dẫn về website |
|---|---|---|---|---|
| TCBS | 77 | 36% | 49 | 79 |
| SSI | 74 | 35% | 35 | 74 |
| Chứng khoán DSC | 67 | 31% | 67 | 106 |
| VNDIRECT | 65 | 30% | 12 | 68 |
| HSC | 20 | 9% | 5 | 17 |
| VPS | 19 | 9% | 4 | 9 |
| DNSE | 18 | 8% | 8 | 18 |
| Vietcap | 16 | 7% | 3 | 11 |
| MBS | 13 | 6% | 4 | 8 |
| Shinhan | 9 | 4% | 0 | 9 |
| VPBankS | 9 | 4% | 0 | 3 |
| KIS | 8 | 4% | 2 | 4 |
| Pinetree | 7 | 3% | 0 | 6 |
| Phú Hưng | 5 | 2% | 2 | 6 |
| Mirae Asset | 4 | 2% | 0 | 0 |

## 4. Domain được trích dẫn nhiều nhất

- **(tất cả)**: dsc.com.vn [chinh_chu] ×100, ssi.com.vn [doi_thu_ctck] ×74, help.tcbs.com.vn [doi_thu_ctck] ×50, support.vndirect.com.vn [doi_thu_ctck] ×41, tcbs.com.vn [doi_thu_ctck] ×29
- **1_kien_thuc**: ssi.com.vn [doi_thu_ctck] ×7, investor.gov [co_quan_nuoc_ngoai] ×6, support.vndirect.com.vn [doi_thu_ctck] ×5, vsdc.vn [khac] ×4, xaydungchinhsach.chinhphu.vn [co_quan_nha_nuoc] ×4
- **2_chon_ctck**: help.tcbs.com.vn [doi_thu_ctck] ×38, ssi.com.vn [doi_thu_ctck] ×37, support.vndirect.com.vn [doi_thu_ctck] ×20, vndirect.com.vn [doi_thu_ctck] ×12, shinhansec.com.vn [doi_thu_ctck] ×8
- **3_phi_margin**: dsc.com.vn [chinh_chu] ×11, ssi.com.vn [doi_thu_ctck] ×8, hsc.com.vn [doi_thu_ctck] ×7, tcbs.com.vn [doi_thu_ctck] ×6, mbs.com.vn [doi_thu_ctck] ×3
- **4_mo_tai_khoan**: dsc.com.vn [chinh_chu] ×10, ssi.com.vn [doi_thu_ctck] ×7, support.vndirect.com.vn [doi_thu_ctck] ×5, vndirect.com.vn [doi_thu_ctck] ×5, help.tcbs.com.vn [doi_thu_ctck] ×4
- **5_san_pham**: tcbs.com.vn [doi_thu_ctck] ×13, ssi.com.vn [doi_thu_ctck] ×8, support.vndirect.com.vn [doi_thu_ctck] ×8, vndirect.com.vn [doi_thu_ctck] ×7, dautu.dragoncapital.com.vn [khac] ×3
- **6_xac_minh**: dsc.com.vn [chinh_chu] ×49, vsdc.vn [khac] ×14, ssc.gov.vn [co_quan_nha_nuoc] ×5, apps.apple.com [app_store] ×4, fireant.vn [khac] ×3
- **7_van_hanh**: dsc.com.vn [chinh_chu] ×25, ssi.com.vn [doi_thu_ctck] ×7, ssc.gov.vn [co_quan_nha_nuoc] ×3, mof.gov.vn [khac] ×3, trading.dsc.com.vn [chinh_chu] ×3

## 5. Loại nguồn được trích dẫn theo nhóm câu hỏi

| Nhóm | app_store | bao_chi | blog_kien_thuc | chinh_chu | co_quan_nha_nuoc | co_quan_nuoc_ngoai | doi_thu_ctck | du_lieu_tai_chinh | khac | toplist |
|---|---|---|---|---|---|---|---|---|---|---|
| 1_kien_thuc | 0% | 0% | 0% | 0% | 18% | 13% | 49% | 0% | 20% | 0% |
| 2_chon_ctck | 0% | 2% | 1% | 3% | 0% | 0% | 89% | 1% | 4% | 2% |
| 3_phi_margin | 0% | 0% | 2% | 18% | 3% | 0% | 68% | 0% | 6% | 3% |
| 4_mo_tai_khoan | 0% | 0% | 0% | 19% | 10% | 0% | 60% | 0% | 12% | 0% |
| 5_san_pham | 0% | 0% | 0% | 0% | 4% | 0% | 81% | 0% | 14% | 0% |
| 6_xac_minh | 7% | 4% | 0% | 55% | 7% | 0% | 2% | 0% | 25% | 0% |
| 7_van_hanh | 0% | 0% | 0% | 54% | 9% | 0% | 24% | 0% | 13% | 0% |

## 6. Loại trang trên website CTCK: được đọc so với được trích dẫn

| Loại trang | Xuất hiện | Được trích dẫn | Tỷ lệ |
|---|---|---|---|
| khac | 1045 | 132 | 13% |
| bieu_phi | 408 | 117 | 29% |
| blog | 302 | 48 | 16% |
| mo_tai_khoan | 164 | 30 | 18% |
| margin | 162 | 39 | 24% |
| san_pham | 144 | 28 | 19% |
| trang_chu | 80 | 21 | 26% |
| lien_he | 41 | 16 | 39% |
| gioi_thieu | 34 | 4 | 12% |

## 7. Trang của thương hiệu được trích dẫn

- https://dsc.com.vn/bieu-phi ×15
- https://dsc.com.vn/bieu-phi/bieu-phi-giao-dich-chung-khoan-niem-yet ×12
- https://dsc.com.vn/ ×12
- https://dsc.com.vn/dich-vu/chinh-sach-dich-vu-giao-dich-ky-quy ×11
- https://dsc.com.vn/huong-dan ×7
- https://dsc.com.vn/dich-vu/mo-tai-khoan ×5
- https://dsc.com.vn/huong-dan/mo-tai-khoan-chung-khoan ×4
- https://dsc.com.vn/mo-tai-khoan ×3
- https://dsc.com.vn/tin-tuc/dsc-dai-hoi-2026 ×3
- https://dsc.com.vn/huong-dan/huong-dan-tai-app-dsc-trading-ios-va-android ×3

## 8. Lệnh tìm (query fan-out) ChatGPT dùng nhiều nhất

- `https://dsc.com.vn/bieu-phi` ×7
- `site.hsx.vn lô lẻ 1 99 cổ phiếu lô chẵn 100` ×5
- `https://539770798-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2f-mj0-9tzhtqir6mnymqv%2fuploads%2flcd1rw5s2a2vblt7c9gb%2fbieu%20phi%20dv_2026.03.png?alt=media&token=dcfba3a8-e854-4167-a6d7-d659ac3541c7` ×5
- `site.tcbs.com.vn lãi suất margin 2026` ×5
- `site.vps.com.vn biểu phí giao dịch chứng khoán cơ sở 2026` ×5
- `site.vndirect.com.vn biểu phí giao dịch chứng khoán cơ sở` ×4
- `site.tcbs.com.vn phí giao dịch cổ phiếu 0.03%` ×4
- `site.vps.com.vn biểu phí giao dịch chứng khoán cơ sở` ×4
- `https://www.ssi.com.vn/khach-hang-ca-nhan/bieu-phi/bieu-gia-dich-vu-giao-dich-chu-dong` ×4
- `site.dnse.com.vn "0,027%" "0,045%"` ×4

## 9. Kiểm tra độ chính xác

Cần duyệt: 58 lượt | đã duyệt: 0 | sai thông tin: 0 (file `review/accuracy_2026-11_codex.csv`).


## 10. Độ đầy đủ dữ liệu

Đã đo 214/214 lượt theo kế hoạch. Câu trả lời dao động giữa các lượt, nên chênh dưới 10 điểm % giữa hai tháng chưa đủ để kết luận.

