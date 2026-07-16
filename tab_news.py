import streamlit as st
import feedparser

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
    # Trả về danh sách (List) thay vì DataFrame để dễ dàng làm link click
    return news_list

# --- GIAO DIỆN STREAMLIT CHÍNH ---
st.set_page_config(page_title="Dashboard Tin Tức", layout="wide")

st.title("📰 Bảng Tin Tài Chính Hàng Ngày")
st.write("Dữ liệu tự động cập nhật liên tục từ các đầu báo lớn - **Click trực tiếp vào tiêu đề để đọc báo.**")
st.divider()

# Chia màn hình làm 2 cột
col1, col2 = st.columns(2)

with col1:
    st.subheader("🌍 Tin Thế Giới & Vĩ Mô")
    # Lấy RSS Thế giới từ VnExpress
    url_world = "https://vnexpress.net/rss/the-gioi.rss"
    world_news = fetch_rss_news(url_world)
    
    # Hiển thị dạng danh sách Link Click
    if world_news:
        for item in world_news:
            st.markdown(f"🔗 **[{item['Tiêu đề']}]({item['Link']})**")
            st.write("") # Tạo khoảng trắng nhỏ giữa các dòng

with col2:
    st.subheader("🏢 Tin Doanh Nghiệp Niêm Yết")
    # Lấy RSS Doanh nghiệp từ CafeF
    url_corp = "https://cafef.vn/doanh-nghiep.rss"
    corp_news = fetch_rss_news(url_corp)
    
    # Hiển thị dạng danh sách Link Click
    if corp_news:
        for item in corp_news:
            st.markdown(f"📈 **[{item['Tiêu đề']}]({item['Link']})**")
            st.write("") # Tạo khoảng trắng nhỏ giữa các dòng
