import streamlit as st
import feedparser

# 1. KHAI BÁO KHO NGUỒN RSS CỦA CÁC BÁO LỚN
RSS_SOURCES = {
    "THẾ GIỚI": [
        "https://cafef.vn/tai-chinh-quoc-te.rss",
        "https://vietstock.vn/rss/the-gioi.rss",
        "https://vneconomy.vn/rss/the-gioi.rss"
    ],
    "TRONG NƯỚC": [
        "https://cafef.vn/vi-mo-dau-tu.rss",
        "https://vietstock.vn/rss/vi-mo.rss",
        "https://vneconomy.vn/rss/tai-chinh.rss"
    ],
    "DOANH NGHIỆP": [
        "https://cafef.vn/doanh-nghiep.rss",
        "https://vietstock.vn/rss/doanh-nghiep.rss",
        "https://www.tinnhanhchungkhoan.vn/rss/doanh-nghiep-2.rss"
    ]
}

@st.cache_data(ttl=1800)  # Cập nhật 30 phút/lần
def fetch_and_group_news(limit_per_category=5):
    """Hàm cào tin từ nhiều nguồn và gom nhóm"""
    grouped_news = {"THẾ GIỚI": [], "TRONG NƯỚC": [], "DOANH NGHIỆP": []}
    
    for category, urls in RSS_SOURCES.items():
        for url in urls:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries:
                    title = entry.title.strip()
                    link = entry.link
                    # Lọc trùng lặp tiêu đề bài viết
                    if not any(title == item['title'] for item in grouped_news[category]):
                        grouped_news[category].append({"title": title, "link": link})
            except Exception:
                continue
                
        # Giới hạn số lượng bài viết mới nhất mỗi chuyên mục
        grouped_news[category] = grouped_news[category][:limit_per_category]
        
    return grouped_news

def render_news_tab():
    """Hàm render giao diện Tab Tin Tức đa năng"""
    st.title("📰 HỆ THỐNG TỔNG HỢP & XUẤT BẢN TIN TỨC")
    st.caption("Nguồn dữ liệu tự động quét từ: CafeF, Vietstock, VnEconomy, Tinnhanhchungkhoan")
    st.divider()

    # Cào dữ liệu bài viết mới nhất
    news_data = fetch_and_group_news(limit_per_category=5)

    # TẠO 2 SUB-TAB BÊN TRONG: 1 ĐỂ ĐỌC GẮN LINK, 1 ĐỂ COPY VĂN BẢN THUẦN
    sub_tab_view, sub_tab_copy = st.tabs(["🌐 Giao diện Đọc Online", "📋 Bản tin Copy nhanh (Zalo/Telegram)"])

    # --- SUB-TAB 1: GIAO DIỆN ĐỌC ONLINE (BẤM ĐƯỢC LINK) ---
    with sub_tab_view:
        st.subheader("🌍 THẾ GIỚI")
        for item in news_data["THẾ GIỚI"]:
            st.markdown(f"🔗 **[{item['title']}]({item['link']})**")
        st.write("")

        st.subheader("🇻🇳 TRONG NƯỚC")
        for item in news_data["TRONG NƯỚC"]:
            st.markdown(f"📌 **[{item['title']}]({item['link']})**")
        st.write("")

        st.subheader("🏢 DOANH NGHIỆP")
        for item in news_data["DOANH NGHIỆP"]:
            st.markdown(f"📈 **[{item['title']}]({item['link']})**")

    # --- SUB-TAB 2: BẢN TIN CHỈ CÓ CHỮ THUẦN (DỄ COPY ĐI CHAT) ---
    with sub_tab_copy:
        st.subheader("📋 Định dạng văn bản thuần túy")
        st.write("💡 Mẹo: Rê chuột vào góc trên bên phải khung chữ dưới đây, bấm nút **Copy** (biểu tượng 2 tờ giấy) là xong!")

        # Khởi tạo chuỗi văn bản theo đúng cấu trúc yêu cầu
        raw_text = ""
        
        # Thêm chuyên mục THẾ GIỚI
        raw_text += "THẾ GIỚI\n\n"
        for item in news_data["THẾ GIỚI"]:
            raw_text += f"{item['title']}\n"
        raw_text += "\n"

        # Thêm chuyên mục TRONG NƯỚC
        raw_text += "TRONG NƯỚC\n\n"
        for item in news_data["TRONG NƯỚC"]:
            raw_text += f"{item['title']}\n"
        raw_text += "\n"

        # Thêm chuyên mục DOANH NGHIỆP
        raw_text += "DOANH NGHIỆP\n\n"
        for item in news_data["DOANH NGHIỆP"]:
            raw_text += f"{item['title']}\n"
        
        # Hiển thị vào vùng text chuyên dụng (st.text_area)
        st.text_area(
            label="Khung nội dung bản tin nhanh",
            value=raw_text,
            height=450,
            key="news_raw_text_area",
            label_visibility="collapsed" # Ẩn label đi cho đẹp
        )

        # Thêm nút Download file .txt
        st.download_button(
            label="📥 Tải về file Bản tin (.txt)",
            data=raw_text,
            file_name="ban_tin_tai_chinh.txt",
            mime="text/plain"
        )
