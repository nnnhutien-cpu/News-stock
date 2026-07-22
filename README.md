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

## Phân loại theo ngành (tab "Doanh nghiệp theo ngành")

`ticker_universe.get_ticker_sectors()` lấy phân ngành **ICB thật** (chuẩn
quốc tế, do VCI/Vietcap cung cấp qua vnstock) cho toàn bộ ~1600+ mã trên
HOSE/HNX/UPCOM — KHÔNG dùng danh sách hardcode, vì gõ tay 1000+ mã ở quy
mô này chắc chắn sẽ có sai sót/lỗi thời. Cụ thể:

```python
from vnstock import Listing
Listing().symbols_by_industries()
```

trả về DataFrame gồm `symbol`, `icb_name1` (ngành cấp 1, rộng nhất) đến
`icb_name4` (chi tiết nhất), `organ_name`... Hệ thống dùng `icb_name3`
làm mặc định (gần với "Ngân hàng", "Bán lẻ", "Chứng khoán" — đúng độ
chi tiết người dùng thường muốn), lùi dần về các cấp khác nếu thiếu.

Cache riêng vào `sectors_cache.json` (TTL 24h, không commit vào git —
xem `.gitignore`). Khi offline/vnstock lỗi, dùng `SECTOR_FALLBACK` (~85
mã) để tab ngành không trắng hoàn toàn, nhưng đây chỉ là bản rút gọn.

**Vì sao không dùng KB / Yahoo Finance để bổ sung ngành?**
- Yahoo Finance có dữ liệu ngành (`sector`/`industry`) nhưng độ phủ mã CK
  Việt Nam trên Yahoo rất thưa (chỉ vài chục mã lớn có suffix `.VN`,
  thiếu hầu hết UPCOM/HNX), và phân ngành theo chuẩn GICS của Mỹ thay vì
  ICB — không khớp với cách thị trường VN đang dùng.
- Không tìm thấy API công khai, miễn phí, ổn định của "KB" (KB Securities
  Việt Nam) cho dữ liệu phân ngành hàng loạt qua mã.
- `vnstock` (nguồn VCI/Vietcap) là nguồn duy nhất trong 3 nguồn được nêu
  có API chính thức, miễn phí, trả về phân ngành ICB đầy đủ theo mã cho
  toàn bộ 3 sàn — nên được chọn làm nguồn chính.

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
- Các tiền tố nhãn tin nhanh của báo (VD: `TIN:`, `HOT:`, `LIVE:`) đã
  được đưa vào blacklist mặc định để tránh bị nhận nhầm thành mã CK —
  nếu phát hiện tiền tố mới tương tự gây nhiễu, thêm vào
  `DEFAULT_BLACKLIST` trong `ticker_universe.py`.
- **Quan trọng**: mỗi khi sửa `FALLBACK_ALIASES`/`FALLBACK_TICKERS`/
  `DEFAULT_BLACKLIST`, nếu máy đã từng chạy app trước đó và có file
  `tickers_cache.json` (cache 24h lấy từ vnstock), file cache đó **không**
  chứa các alias/blacklist thủ công mới thêm — nhưng không sao vì
  `get_ticker_universe_and_aliases()` luôn gọi `_merge_aliases(cached,
  FALLBACK_ALIASES)`, tức FALLBACK_ALIASES luôn được cộng thêm dù cache
  còn hạn hay không. Riêng nếu bạn *xoá bớt* hoặc *đổi tên* một mã trong
  FALLBACK_TICKERS, nên xoá `tickers_cache.json` để tránh dữ liệu cũ lẫn
  vào (`rm tickers_cache.json`).
