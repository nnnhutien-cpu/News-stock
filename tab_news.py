import streamlit as st
import feedparser
from concurrent.futures import ThreadPoolExecutor, as_completed

# ── RSS SOURCES ──────────────────────────────────────────────────────────────
RSS_SOURCES = {
    "TIN TỨC": [
        "https://cafef.vn/tai-chinh-quoc-te.rss",
        "https://cafef.vn/vi-mo-dau-tu.rss",
        "https://vietstock.vn/rss/vi-mo.rss",
        "https://vneconomy.vn/rss/tai-chinh.rss",
        "https://vnexpress.net/rss/kinh-doanh.rss",
    ],
    "DOANH NGHIỆP": [
        "https://cafef.vn/doanh-nghiep.rss",
        "https://vietstock.vn/rss/doanh-nghiep.rss",
        "https://www.tinnhanhchungkhoan.vn/rss/doanh-nghiep-2.rss",
    ],
}

# Danh sách ticker phổ biến để bôi đậm trong tiêu đề
TICKERS = [
    "VCB","TCB","BID","CTG","MBB","VPB","ACB","SHB","LPB","HDB",
    "VHM","VIC","VNM","SAB","GAS","PLX","MSN","MWG","HPG","HSG",
    "NKG","SSI","VND","HCM","VCI","FPT","CMG","VGI","DGW","PNJ",
    "VJC","HVN","ACV","REE","GEX","KDC","DBC","HAG","AGR","DPM",
    "PVD","PVS","BSR","OIL","GIL","AIC","VBB","CC1","HSM","VBB",
]

# ── DATA FETCHING ─────────────────────────────────────────────────────────────
def _fetch_one(url):
    try:
        feed = feedparser.parse(url)
        items = []
        for e in feed.entries:
            title = getattr(e, "title", "").strip()
            link  = getattr(e, "link",  "").strip()
            if title and link:
                items.append({"title": title, "link": link})
        return items
    except Exception:
        return []

@st.cache_data(ttl=900, show_spinner=False)
def fetch_all_news():
    grouped = {cat: [] for cat in RSS_SOURCES}
    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {
            ex.submit(_fetch_one, url): cat
            for cat, urls in RSS_SOURCES.items()
            for url in urls
        }
        for fut in as_completed(futures):
            cat   = futures[fut]
            items = fut.result()
            seen  = {i["title"] for i in grouped[cat]}
            for item in items:
                if item["title"] not in seen:
                    grouped[cat].append(item)
                    seen.add(item["title"])
    return grouped

# ── HELPERS ───────────────────────────────────────────────────────────────────
def highlight_ticker(title: str) -> str:
    """Bôi đậm ticker nếu xuất hiện ở đầu tiêu đề (dạng 'VBB: ...')"""
    for tk in TICKERS:
        if title.upper().startswith(tk + ":") or title.upper().startswith(tk + " "):
            rest = title[len(tk):]
            return f"**{tk}**{rest}"
    return title

def news_section(label: str, color: str, items: list, limit: int = 12):
    """Render một khối tin tức styled giống ảnh."""
    # Header màu
    st.markdown(
        f"""
        <div style="
            background-color:{color};
            color:white;
            font-weight:700;
            font-size:14px;
            padding:6px 12px;
            border-radius:4px 4px 0 0;
            letter-spacing:0.5px;
        ">{label}</div>
        """,
        unsafe_allow_html=True,
    )

    # Body
    if not items:
        st.markdown(
            "<div style='padding:10px;color:#888;font-size:13px;'>Không có tin tức.</div>",
            unsafe_allow_html=True,
        )
        return

    bullets_html = ""
    for item in items[:limit]:
        title = item["title"]
        link  = item["link"]
        # Tìm ticker để bôi đậm
        ticker_bold = ""
        rest_title  = title
        for tk in TICKERS:
            if title.upper().startswith(tk + ":") or title.upper().startswith(tk + " "):
                ticker_bold = tk
                rest_title  = title[len(tk):]
                break

        if ticker_bold:
            display = f'<b style="color:#1a1a1a">{ticker_bold}</b>{rest_title}'
        else:
            display = title

        bullets_html += f"""
        <li style="margin-bottom:6px;line-height:1.4;">
            <a href="{link}" target="_blank"
               style="text-decoration:none;color:#1a1a1a;font-size:13px;">
               {display}
            </a>
        </li>
        """

    st.markdown(
        f"""
        <div style="
            border:1px solid {color};
            border-top:none;
            border-radius:0 0 4px 4px;
            padding:10px 14px;
            background:#fff;
        ">
        <ul style="margin:0;padding-left:18px;list-style-type:disc;">
            {bullets_html}
        </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── MAIN TAB FUNCTION ─────────────────────────────────────────────────────────
def render_tab_news():
    st.markdown("#### 📰 Tin tức thị trường")

    col_refresh, col_time = st.columns([1, 3])
    with col_refresh:
        if st.button("🔄 Làm mới tin"):
            st.cache_data.clear()

    with st.spinner("Đang tải tin tức..."):
        grouped = fetch_all_news()

    tin_tuc      = grouped.get("TIN TỨC", [])
    doanh_nghiep = grouped.get("DOANH NGHIỆP", [])

    col1, col2 = st.columns(2)

    with col1:
        news_section("TIN TỨC", "#E07B1A", tin_tuc, limit=12)

    with col2:
        news_section("DOANH NGHIỆP", "#1F5FAD", doanh_nghiep, limit=12)


# ── STANDALONE RUN ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    st.set_page_config(page_title="Tin tức CK", layout="wide")
    render_tab_news()
