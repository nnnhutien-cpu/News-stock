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
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List

import feedparser

from ticker_detector import TickerDetector
from ticker_universe import get_blacklist, get_ticker_universe

# {category: {source_name: rss_url}}
RSS_SOURCES: Dict[str, Dict[str, str]] = {
    "THẾ GIỚI": {
        "CafeF": "https://cafef.vn/tai-chinh-quoc-te.rss",
        "Vietstock": "https://vietstock.vn/rss/the-gioi.rss",
        "VnEconomy": "https://vneconomy.vn/rss/the-gioi.rss",
        "VnExpress": "https://vnexpress.net/rss/the-gioi.rss",
    },
    "TIN TỨC": {  # tin vĩ mô, thị trường chung trong nước
        "CafeF": "https://cafef.vn/vi-mo-dau-tu.rss",
        "Vietstock": "https://vietstock.vn/rss/vi-mo.rss",
        "VnEconomy": "https://vneconomy.vn/rss/tai-chinh.rss",
        "VnExpress": "https://vnexpress.net/rss/kinh-doanh.rss",
        "VietnamBiz": "https://vietnambiz.vn/rss/tai-chinh.rss",
    },
    "DOANH NGHIỆP": {
        "CafeF": "https://cafef.vn/doanh-nghiep.rss",
        "Vietstock": "https://vietstock.vn/rss/doanh-nghiep.rss",
        "TNCK": "https://www.tinnhanhchungkhoan.vn/rss/doanh-nghiep-2.rss",
        "VietnamBiz": "https://vietnambiz.vn/rss/doanh-nghiep.rss",
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


def _fetch_one_feed(url: str, timeout: int = 10):
    try:
        return feedparser.parse(url, request_headers={"User-Agent": "Mozilla/5.0"})
    except Exception:
        return None


def fetch_all_news(
    limit_per_feed: int = 25,
    detector: TickerDetector | None = None,
) -> List[NewsItem]:
    """Cào toàn bộ nguồn RSS, chuẩn hoá, gắn mã CK và khử trùng lặp.

    Args:
        limit_per_feed: số tin mới nhất lấy mỗi feed (feed nào cũng có
            thể chứa hàng chục tin, chỉ cần đủ để không sót tin quan trọng).
        detector: truyền vào từ ngoài để tái sử dụng universe đã cache;
            nếu None sẽ tự khởi tạo (gọi get_ticker_universe()).
    """
    if detector is None:
        detector = TickerDetector(get_ticker_universe(), get_blacklist())

    seen_titles: set[str] = set()
    all_items: List[NewsItem] = []

    for category, sources in RSS_SOURCES.items():
        for source_name, url in sources.items():
            feed = _fetch_one_feed(url)
            if not feed or not getattr(feed, "entries", None):
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

    return all_items


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
