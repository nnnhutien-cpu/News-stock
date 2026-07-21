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

Có 2 tầng nhận diện, chạy song song:

**A. Theo mã (token viết hoa)**
1. Chỉ xét token 3-4 chữ **IN HOA liên tục**, đứng độc lập (word boundary).
2. Token phải nằm trong **whitelist mã CK thật** (không tự suy đoán).
3. Loại các từ viết tắt phổ biến hay trùng (GDP, CPI, FDI, IMF...).
4. Loại các cụm ngữ cảnh địa danh dễ nhầm, ví dụ "TP.HCM" (dù "HCM" là
   mã CK thật của Chứng khoán HSC).
5. Ưu tiên/đánh dấu độ tin cậy cao khi mã xuất hiện ngay sau "mã",
   "cổ phiếu", trong ngoặc đơn, hoặc trong slug URL
   (`cafef.vn/du-lieu/hose/hpg-...`, `finance.vietstock.vn/HPG/tin-tuc.htm`).

**B. Theo tên công ty** *(quan trọng — vì phần lớn tin doanh nghiệp viết
theo tên, không viết mã, ví dụ "Viglacera bổ nhiệm thêm một Phó Tổng
giám đốc" không hề có chữ "VGC")*
1. Bảng ánh xạ tên -> mã lấy từ `vnstock` (organ_name/organ_short_name)
   khi online, luôn merge thêm `FALLBACK_ALIASES` (tên gọi tắt/thân mật
   curate thủ công: "Viglacera", "Hòa Phát", "Vinamilk"...).
2. So khớp cụm từ trọn vẹn, không phân biệt hoa/thường, có ranh giới từ
   (không cắt giữa từ) trong tiêu đề + mô tả bài viết.
3. Vì tên công ty là danh từ riêng khá đặc thù nên không cần đối chiếu
   blacklist ở bước này.

## Chạy thử

```bash
pip install -r requirements.txt
streamlit run app.py
```

Kiểm thử nhanh logic nhận diện (không cần mạng):

```bash
python test_ticker_detector.py
```

## Nguồn RSS

Toàn bộ URL RSS trong `news_fetcher.py` đã được xác minh trực tiếp từ
trang "RSS Feeds" chính thức của từng báo (`cafef.vn/rss.chn`,
`vietstock.vn/rss`, `vneconomy.vn/rss.html`) — không phải suy đoán theo
mẫu URL, để tránh feed 404/rỗng do sai slug. Mục **THẾ GIỚI** được mở
rộng từ 1 nguồn lên 5 nguồn (CafeF, 2 feed của Vietstock, VnEconomy,
VnExpress) để không bỏ sót các tin như "Phố Wall nhuốm sắc đỏ, Dow Jones
giảm hơn 300 điểm".

## Khi Vietstock/VietnamBiz không lấy được tin

Nếu chạy `check_feeds.py` (hoặc xem khu vực "🔧 Trạng thái nguồn tin" trong
app) mà thấy một nguồn báo lỗi:

```bash
python check_feeds.py
```

- **`HTTP 403` hoặc `0 bài viết`**: nhiều khả năng trang đặt sau
  Cloudflare/WAF và chặn IP của máy chủ đang chạy script — phổ biến với
  IP dùng chung của GitHub-hosted runner (rất hay bị các trang tin VN
  chặn vì bị bot khác lạm dụng cùng dải IP). Trang vẫn mở bình thường
  trên trình duyệt cá nhân **không** có nghĩa là server cũng truy cập
  được — đây là 2 network path hoàn toàn khác nhau.
  - Cách xử lý: (1) thử chạy lại sau vài giờ xem có phải chặn tạm thời;
    (2) cân nhắc dùng self-hosted runner (máy cá nhân/VPS có IP dân dụng)
    thay vì GitHub-hosted runner; (3) hoặc dùng dịch vụ proxy/RSS-bridge
    trung gian để đổi IP nguồn request.
- **`Timeout`**: mạng chậm hoặc trang đang quá tải — thường tự khỏi ở lần
  chạy sau, không cần sửa gì.
- **`Lỗi SSL`**: chứng chỉ trang tạm thời có vấn đề, hoặc runner thiếu
  CA certificates cập nhật.
- **`XML lỗi (bozo)`**: trang trả về nội dung không phải RSS hợp lệ (có
  thể là trang lỗi/trang chặn dạng HTML thay vì XML) — thường đi kèm
  nguyên nhân là bị chặn ở tầng trên, không phải lỗi code.

`_fetch_one_feed()` trong `news_fetcher.py` đã được viết để KHÔNG nuốt
lỗi im lặng: mọi lần chạy `fetch_all_news()` đều in log `[OK]`/`[LỖI]`
kèm lý do cụ thể ra stderr — log này hiện đầy đủ trong tab Actions của
GitHub khi chạy qua workflow.

## Giới hạn đã biết

- Danh sách mã CK phụ thuộc `vnstock` khi có mạng; khi offline sẽ dùng
  danh sách tĩnh rút gọn (không đầy đủ ~1600+ mã).
- Một số mã trùng với từ viết tắt thông dụng (VD: `CEO`, `VND`, `HCM`)
  không thể phân biệt 100% bằng regex — cần NLP/NER để xử lý triệt để
  hơn nếu muốn độ chính xác cao hơn nữa.
