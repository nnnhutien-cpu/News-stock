import streamlit as st
import feedparser

# 1. CẬP NHẬT KHO NGUỒN TÌM KIẾM THEO ĐÚNG TIÊU CHÍ ƯU TIÊN CỦA BẠN
RSS_SOURCES = {
    "THẾ GIỚI": [
        "https://cafef.vn/tai-chinh-quoc-te.rss",
        "https://vietstock.vn/rss/the-gioi.rss",
        "https://vneconomy.vn/rss/the-gioi.rss",
        "https://vnexpress.net/rss/the-gioi.rss"
    ],
    "TRONG NƯỚC": [
        "https://cafef.vn/vi-mo-dau-tu.rss",
        "https://vietstock.vn/rss/vi-mo.rss",
        "https://vneconomy.vn/rss/tai-chinh.rss",
        "https://vnexpress.net/rss/kinh-doanh.rss" # Bổ sung tin vĩ mô, CPI, lãi suất nhanh
    ],
    "DOANH NGHIỆP": [
        "https://cafef.vn/doanh-nghiep.rss",
        "https://vietstock.vn/rss/doanh-nghiep.rss",
        "https://www.tinnhanhchungkhoan.vn/rss/doanh-nghiep-2.rss" # Nguồn ưu tiên số 1 về ĐHCĐ & Phát hành
    ]
}

@st.cache_data(ttl=900)  # Giảm xuống 15 phút/lần để cập nhật tin sốt dẻo nhanh nhất
def fetch_and_group_news(limit_per_category=20):  # Tăng lượng cào ban đầu lên để bộ lọc filter không bị thiếu tin
    """Hàm cào dữ liệu thô từ hệ thống cổng báo lớn"""
    grouped_news = {"THẾ GIỚI": [], "TRONG NƯỚC": [], "DOANH NGHIỆP": []}
    
    for category, urls in RSS_SOURCES.items():
        for url in urls:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries:
                    title = entry.title.strip()
                    link = entry.link
                    # Lọc trùng lặp bài viết chia sẻ chéo giữa các báo
                    if not any(title == item['title'] for item in grouped_news[category]):
                        grouped_news[category].append({"title": title, "link": link})
            except Exception:
                continue
                
        # Giữ lại danh sách thô nhiều tin để phục vụ tính năng tìm kiếm động
        grouped_news[category] = grouped_news[category]
