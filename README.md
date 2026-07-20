# News-stock — Tin tức Chứng khoán Việt Nam

Ứng dụng Streamlit cào tin tức tài chính/chứng khoán từ nhiều nguồn
(CafeF, Vietstock, VnEconomy, VietnamBiz, VnExpress, Tin nhanh chứng
khoán) và **nhận diện chính xác mã chứng khoán** (HOSE/HNX/UPCOM) được
nhắc đến trong từng tin, để lọc/nhóm tin theo mã.

## Vấn đề của bản cũ

Bản trước (`news_scraper.py` + `tab_news.py`) chỉ cào RSS và nhóm tin
theo **chuyên mục của nguồn** (feed nào thì bỏ vào box đó), **không hề
kiểm tra** xem tiêu đề có thực sự nhắc tới một mã CK hợp lệ hay không.
Hệ quả: không lọc được tin theo mã, và nếu có thử nhận diện bằng regex
"3 chữ hoa" đơn thuần thì sẽ dính rất nhiều false positive (GDP, CPI,
CEO, TP.HCM...).

## Kiến trúc mới

```
ticker_universe.py   -> Lấy & cache danh sách mã CK thật (HOSE/HNX/UPCOM)
                         từ vnstock (24h/lần), có fallback tĩnh khi mất mạng.
ticker_detector.py    -> Regex + whitelist + blacklist + luật ngữ cảnh,
                         nhận diện mã CK trong tiêu đề/mô tả/URL bài báo.
news_fetcher.py       -> Cào nhiều RSS, khử trùng lặp, gắn nhãn mã CK,
                         phân loại lại TIN TỨC / DOANH NGHIỆP / THẾ GIỚI.
app.py                -> Giao diện Streamlit: 3 cột tin, ô tìm kiếm,
                         khu vực "mã CK hôm nay" (click để lọc), tải CSV.
test_ticker_detector.py -> Bộ test độc lập (không cần mạng) cho detector.
news_sources.py       -> (giữ nguyên) cẩm nang nguồn dữ liệu, hiển thị dạng tab riêng.
```

## Cách nhận diện mã CK hoạt động

1. Chỉ xét token 3-4 chữ **IN HOA liên tục**, đứng độc lập (word boundary).
2. Token phải nằm trong **whitelist mã CK thật** (không tự suy đoán).
3. Loại các từ viết tắt phổ biến hay trùng (GDP, CPI, FDI, IMF...).
4. Loại các cụm ngữ cảnh địa danh dễ nhầm, ví dụ "TP.HCM" (dù "HCM" là
   mã CK thật của Chứng khoán HSC).
5. Ưu tiên/đánh dấu độ tin cậy cao khi mã xuất hiện ngay sau "mã",
   "cổ phiếu", trong ngoặc đơn, hoặc trong slug URL
   (`cafef.vn/du-lieu/hose/hpg-...`, `finance.vietstock.vn/HPG/tin-tuc.htm`).

## Chạy thử

```bash
pip install -r requirements.txt
streamlit run app.py
```

Kiểm thử nhanh logic nhận diện (không cần mạng):

```bash
python test_ticker_detector.py
```

## Giới hạn đã biết

- Danh sách mã CK phụ thuộc `vnstock` khi có mạng; khi offline sẽ dùng
  danh sách tĩnh rút gọn (không đầy đủ ~1600+ mã).
- Một số mã trùng với từ viết tắt thông dụng (VD: `CEO`, `VND`, `HCM`)
  không thể phân biệt 100% bằng regex — cần NLP/NER để xử lý triệt để
  hơn nếu muốn độ chính xác cao hơn nữa.
