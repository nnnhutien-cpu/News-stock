import streamlit as st
import feedparser
import pandas as pd

# Cấu hình hàm lấy tin tức tự động cập nhật sau mỗi 12 tiếng
@st.cache_data(ttl=43200)
def fetch_rss_news(rss_url, limit=15):
    """Hàm cào dữ liệu từ link RSS"""
    feed = feedparser.parse(rss_url)
    news_list = []
    
    for entry in feed.entries[:limit]:
        news_list.append({
            "Tiêu đề": entry.title,
            "Link": entry.link
        })
    return pd.DataFrame(news_list)

# --- GIAO DIỆN STREAMLIT ---
st.set_page_config(page_title="Dashboard Tin Tức", layout="wide")
st.title("📰 Bảng Tin Tài Chính Hàng Ngày")
st.write("Dữ liệu tự động cập nhật liên tục từ các đầu báo lớn.")

# Chia màn hình làm 2 cột
col1, col2 = st.columns(2)

with col1:
    st.subheader("🌍 Tin Thế Giới & Vĩ Mô")
    # Lấy RSS Thế giới từ VnExpress
    url_world = "https://vnexpress.net/rss/the-gioi.rss"
    df_world = fetch_rss_news(url_world)
    
    # Hiển thị dạng bảng (bỏ cột index cho đẹp)
    st.dataframe(df_world, use_container_width=True, hide_index=True)

with col2:
    st.subheader("🏢 Tin Doanh Nghiệp Niêm Yết")
    # Lấy RSS Doanh nghiệp từ CafeF
    url_corp = "https://cafef.vn/doanh-nghiep.rss"
    df_corp = fetch_rss_news(url_corp)
    
    st.dataframe(df_corp, use_container_width=True, hide_index=True)
