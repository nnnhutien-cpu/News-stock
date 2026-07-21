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
        detector = TickerDetector(get_ticker_universe(), get_blacklist(), get_company_aliases())

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
