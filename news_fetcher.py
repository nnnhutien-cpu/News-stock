"""
news_fetcher.py
----------------
Thay thế cho news_scraper.py + phần cào dữ liệu trong tab_news.py bản cũ.

Điểm khác biệt chính so với bản cũ:
- Gộp nhiều nguồn (CafeF, Vietstock, VnEconomy, VietnamBiz, VnExpress,
  Tin nhanh chứng khoán) thay vì rải rác 2 nơi.
- Mỗi tin được gắn thêm:
    * `source`      : tên nguồn (CafeF, Vietstock, ...)
    * `tickers`      : danh sách mã CK hợp lệ được nhận diện (list[str])
    * `category`     : "TIN TỨC" | "DOANH NGHIỆP" | "THẾ GIỚI"
  Việc phân loại DOANH NGHIỆP không còn dựa 100% vào "tin này lấy từ RSS
  chuyên trang doanh nghiệp" như bản cũ (dễ sót vì một tin ở box Vĩ mô
  vẫn có thể là tin công ty), mà dựa vào: (a) nguồn RSS gốc, HOẶC (b) có
  ít nhất 1 mã CK hợp lệ được nhận diện trong tiêu đề -> gộp vào DOANH
  NGHIỆP luôn cho chính xác.
- Loại trùng lặp theo tiêu đề đã chuẩn hoá (bỏ khoảng trắng thừa, không
  phân biệt hoa/thường) để không đếm 2 lần khi nhiều báo đăng cùng 1 tin.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

import feedparser
import requests

from ticker_detector import TickerDetector
from ticker_universe import get_blacklist, get_company_aliases, get_ticker_universe

# {category: {source_name: rss_url}}
# LƯU Ý: toàn bộ URL dưới đây đã được xác minh trực tiếp từ trang "RSS Feeds"
# chính thức của từng báo (cafef.vn/rss.chn, vietstock.vn/rss, vneconomy.vn/rss.html)
# — không phải URL đoán theo mẫu như bản trước, nên tránh được tình trạng feed
# 404/rỗng do sai slug.
RSS_SOURCES: Dict[str, Dict[str, str]] = {
    "THẾ GIỚI": {
        # Đây là nhóm quan trọng nhất để bắt các tin kiểu "Phố Wall nhuốm sắc
        # đỏ, Dow Jones giảm hơn 300 điểm" — trước đây chỉ có 1 nguồn (CafeF)
        # nên rất dễ bỏ sót nếu CafeF chưa kịp đăng hoặc đăng ở mục khác.
        "CafeF": "https://cafef.vn/tai-chinh-quoc-te.rss",
        "Vietstock (CK thế giới)": "https://vietstock.vn/773/the-gioi/chung-khoan-the-gioi.rss",
        "Vietstock (TC quốc tế)": "https://vietstock.vn/772/the-gioi/tai-chinh-quoc-te.rss",
        "VnEconomy": "https://vneconomy.vn/kinh-te-the-gioi.rss",
        "VnExpress": "https://vnexpress.net/rss/kinh-doanh.rss",  # có mục con quốc tế trong nội dung
    },
    "TIN TỨC": {  # tin vĩ mô, thị trường chung trong nước
        "CafeF (vĩ mô)": "https://cafef.vn/vi-mo-dau-tu.rss",
        "CafeF (TT chứng khoán)": "https://cafef.vn/thi-truong-chung-khoan.rss",
        "Vietstock (vĩ mô)": "https://vietstock.vn/761/kinh-te/vi-mo.rss",
        "Vietstock (cổ phiếu)": "https://vietstock.vn/830/chung-khoan/co-phieu.rss",
        "VnEconomy (chứng khoán)": "https://vneconomy.vn/chung-khoan.rss",
        "VnEconomy (tài chính)": "https://vneconomy.vn/tai-chinh.rss",
        "VietnamBiz (tài chính)": "https://vietnambiz.vn/tai-chinh.rss",
        "VietnamBiz (chứng khoán)": "https://vietnambiz.vn/chung-khoan.rss",
    },
    "DOANH NGHIỆP": {
        "CafeF": "https://cafef.vn/doanh-nghiep.rss",
        "Vietstock (HĐ kinh doanh)": "https://vietstock.vn/737/doanh-nghiep/hoat-dong-kinh-doanh.rss",
        "Vietstock (cổ tức)": "https://vietstock.vn/738/doanh-nghiep/co-tuc.rss",
        "Vietstock (tăng vốn - M&A)": "https://vietstock.vn/764/doanh-nghiep/tang-von-m-a.rss",
        "TNCK": "https://www.tinnhanhchungkhoan.vn/rss/doanh-nghiep-2.rss",
        "VietnamBiz": "https://vietnambiz.vn/doanh-nghiep.rss",
    },
}


@dataclass
class NewsItem:
    title: str
    link: str
    source: str
    category: str
    published: str = ""
    description: str = ""
    tickers: List[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "Tiêu đề": self.title,
            "Link": self.link,
            "Nguồn": self.source,
            "Chuyên mục": self.category,
            "Thời gian": self.published,
            "Mã CK": ", ".join(self.tickers) if self.tickers else "",
        }


def _normalize_title(title: str) -> str:
    return re.sub(r"\s+", " ", title).strip().lower()


# Nhiều báo (đặc biệt Vietstock, VietnamBiz) đặt sau Cloudflare / WAF và có
# thể chặn im lặng (403, hoặc trả về trang chặn thay vì XML) nếu request
# "trông giống bot": không có Accept-Language, User-Agent quá đơn giản kiểu
# "Mozilla/5.0" trần trụi, hoặc dùng bộ tải HTTP mặc định của feedparser
# (urllib) vốn có fingerprint rất dễ bị nhận diện. Vì vậy ở đây ta:
#  1) Tự fetch bằng `requests` với header đầy đủ giống trình duyệt thật.
#  2) Đưa bytes đã tải về cho feedparser.parse() phân tích (thay vì để
#     feedparser tự đi tải URL).
#  3) KHÔNG nuốt lỗi im lặng — log rõ nguyên nhân (status code, exception)
#     để chạy trên GitHub Actions vẫn thấy được trong log tại sao 1 nguồn
#     không có tin, thay vì cứ trống bí ẩn.
_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/xml, text/xml, */*;q=0.8",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.google.com/",
}


@dataclass
class FetchStatus:
    source_name: str
    url: str
    ok: bool
    entry_count: int = 0
    error: str = ""


def _fetch_one_feed(url: str, timeout: int = 12) -> "tuple[Optional[object], FetchStatus]":
    status = FetchStatus(source_name="", url=url, ok=False)
    try:
        resp = requests.get(url, headers=_BROWSER_HEADERS, timeout=timeout)
        if resp.status_code != 200:
            status.error = f"HTTP {resp.status_code}"
            return None, status
        parsed = feedparser.parse(resp.content)
        if getattr(parsed, "bozo", 0) and not getattr(parsed, "entries", None):
            # bozo=1 nghĩa là XML lỗi cú pháp; nếu vẫn có entries thì feed
            # vẫn dùng được (nhiều RSS VN có XML hơi lỗi chuẩn nhưng đọc
            # được bình thường), chỉ coi là lỗi thật khi KHÔNG có entries.
            status.error = f"XML lỗi (bozo): {getattr(parsed, 'bozo_exception', '')}"
            return None, status
        entries = getattr(parsed, "entries", []) or []
        if not entries:
            status.error = "Feed hợp lệ nhưng 0 bài viết (có thể bị chặn/trả trang chặn)"
            return None, status
        status.ok = True
        status.entry_count = len(entries)
        return parsed, status
    except requests.exceptions.SSLError as e:
        status.error = f"Lỗi SSL: {e}"
    except requests.exceptions.Timeout:
        status.error = f"Timeout sau {timeout}s"
    except requests.exceptions.ConnectionError as e:
        status.error = f"Lỗi kết nối: {e}"
    except Exception as e:  # noqa: BLE001 - muốn bắt hết để không crash cả pipeline
        status.error = f"Lỗi không xác định: {e}"
    return None, status


def fetch_all_news(
    limit_per_feed: int = 25,
    detector: TickerDetector | None = None,
    verbose: bool = True,
) -> "tuple[List[NewsItem], List[FetchStatus]]":
    """Cào toàn bộ nguồn RSS, chuẩn hoá, gắn mã CK và khử trùng lặp.

    Args:
        limit_per_feed: số tin mới nhất lấy mỗi feed (feed nào cũng có
            thể chứa hàng chục tin, chỉ cần đủ để không sót tin quan trọng).
        detector: truyền vào từ ngoài để tái sử dụng universe đã cache;
            nếu None sẽ tự khởi tạo (gọi get_ticker_universe()).
        verbose: in log từng nguồn ra stdout (hiện được trong log của
            GitHub Actions) — bật mặc định vì im lặng bỏ qua lỗi chính là
            lý do gây khó chẩn đoán trước đây.

    Returns:
        (danh sách tin, danh sách trạng thái fetch từng nguồn) — trạng
        thái này giúp biết CHÍNH XÁC nguồn nào lỗi và vì sao, thay vì chỉ
        thấy "không có tin Vietstock/VietnamBiz" mà không rõ nguyên nhân.
    """
    if detector is None:
        detector = TickerDetector(get_ticker_universe(), get_blacklist(), get_company_aliases())

    seen_titles: set[str] = set()
    all_items: List[NewsItem] = []
    fetch_stats: List[FetchStatus] = []

    for category, sources in RSS_SOURCES.items():
        for source_name, url in sources.items():
            feed, status = _fetch_one_feed(url)
            status.source_name = source_name
            fetch_stats.append(status)

            if verbose:
                if status.ok:
                    print(f"[OK]   {source_name:30s} {status.entry_count:3d} bài  ({url})", file=sys.stderr)
                else:
                    print(f"[LỖI]  {source_name:30s} {status.error}  ({url})", file=sys.stderr)

            if not status.ok or not feed:
                continue

            for entry in feed.entries[:limit_per_feed]:
                title = getattr(entry, "title", "").strip()
                link = getattr(entry, "link", "").strip()
                if not title or not link:
                    continue
                key = _normalize_title(title)
                if key in seen_titles:
                    continue
                seen_titles.add(key)

                description = getattr(entry, "summary", "") or getattr(entry, "description", "")
                published = getattr(entry, "published", "") or getattr(entry, "updated", "")

                match = detector.detect(title=title, description=description, link=link)
                tickers = match.codes

                # Một tin có mã CK hợp lệ trong tiêu đề luôn được coi là
                # tin DOANH NGHIỆP, bất kể nó được cào từ feed chuyên mục
                # nào (vĩ mô, thị trường chung...) — đây chính là phần sửa
                # lỗi phân loại chính mà bạn yêu cầu.
                final_category = "DOANH NGHIỆP" if tickers else category

                all_items.append(
                    NewsItem(
                        title=title,
                        link=link,
                        source=source_name,
                        category=final_category,
                        published=published,
                        description=description,
                        tickers=tickers,
                    )
                )

    if verbose:
        n_ok = sum(1 for s in fetch_stats if s.ok)
        print(f"\n=> {n_ok}/{len(fetch_stats)} nguồn fetch thành công, {len(all_items)} tin sau khi khử trùng lặp.", file=sys.stderr)

    return all_items, fetch_stats


def group_by_category(items: List[NewsItem]) -> Dict[str, List[NewsItem]]:
    grouped: Dict[str, List[NewsItem]] = {"TIN TỨC": [], "DOANH NGHIỆP": [], "THẾ GIỚI": []}
    for item in items:
        grouped.setdefault(item.category, []).append(item)
    return grouped


def collect_tickers_today(items: List[NewsItem]) -> Dict[str, int]:
    """Đếm số tin theo mã CK, phục vụ khu vực 'Mã CK được nhắc đến hôm nay'."""
    counts: Dict[str, int] = {}
    for item in items:
        for t in item.tickers:
            counts[t] = counts.get(t, 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: kv[1], reverse=True))
