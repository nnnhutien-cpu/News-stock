import streamlit as st
import feedparser
from concurrent.futures import ThreadPoolExecutor, as_completed

# ══════════════════════════════════════════════════════════════════════════════
# RSS SOURCES — Chỉ lấy tin chứng khoán, tài chính, doanh nghiệp niêm yết
# Ưu tiên: CafeF > Vietstock > Tinnhanhchungkhoan > VnEconomy > VietnamBiz
# ══════════════════════════════════════════════════════════════════════════════
RSS_SOURCES = {
    "TIN TỨC": {
        "CafeF – Chứng khoán":         "https://cafef.vn/chung-khoan.rss",
        "CafeF – Tài chính ngân hàng":  "https://cafef.vn/tai-chinh-ngan-hang.rss",
        "CafeF – Vĩ mô đầu tư":        "https://cafef.vn/vi-mo-dau-tu.rss",
        "Vietstock – Chứng khoán":      "https://vietstock.vn/rss/chung-khoan.rss",
        "Vietstock – Tài chính":        "https://vietstock.vn/rss/tai-chinh.rss",
        "VnEconomy – Chứng khoán":      "https://vneconomy.vn/rss/chung-khoan.rss",
        "VnEconomy – Tài chính":        "https://vneconomy.vn/rss/tai-chinh.rss",
        "Tinnhanhchungkhoan – CK":      "https://www.tinnhanhchungkhoan.vn/rss/chung-khoan-1.rss",
        "VietnamBiz – Chứng khoán":     "https://vietnambiz.vn/chung-khoan.rss",
        "VnExpress – Chứng khoán":      "https://vnexpress.net/rss/kinh-doanh/chung-khoan.rss",
    },
    "DOANH NGHIỆP": {
        "CafeF – Doanh nghiệp":             "https://cafef.vn/doanh-nghiep.rss",
        "Vietstock – Doanh nghiệp":         "https://vietstock.vn/rss/doanh-nghiep.rss",
        "Tinnhanhchungkhoan – Doanh nghiệp":"https://www.tinnhanhchungkhoan.vn/rss/doanh-nghiep-2.rss",
        "VietnamBiz – Doanh nghiệp":        "https://vietnambiz.vn/doanh-nghiep.rss",
        "VnEconomy – Doanh nghiệp":         "https://vneconomy.vn/rss/doanh-nghiep.rss",
        "VnExpress – Kinh doanh":           "https://vnexpress.net/rss/kinh-doanh.rss",
    },
}

# ══════════════════════════════════════════════════════════════════════════════
# BỘ LỌC NỘI DUNG — Chỉ giữ tin CK / tài chính / DN niêm yết
# ══════════════════════════════════════════════════════════════════════════════
INCLUDE_KW = [
    "vnindex","vn-index","hnx","upcom","vn30","chứng khoán","cổ phiếu","cổ phần",
    "nhà đầu tư","thanh khoản","khối ngoại","mua ròng","bán ròng","giao dịch",
    "tăng điểm","giảm điểm","hồi phục","điều chỉnh","vốn hóa","room ngoại",
    "lãi suất","tỷ giá","tín dụng","trái phiếu","ngân hàng","lạm phát",
    "kqkd","kết quả kinh doanh","doanh thu","lợi nhuận","eps","pe","pb",
    "cổ tức","phát hành","esop","đại hội cổ đông","đhcđ","niêm yết",
    "bctc","báo cáo tài chính","quý","năm tài chính","hose","hnx",
    "margin","ký quỹ","đòn bẩy","fed","tăng vốn","phát hành thêm",
]

EXCLUDE_KW = [
    "bóng đá","thể thao","giải trí","sao việt","âm nhạc","phim","hoa hậu",
    "thời tiết","du lịch","ẩm thực","sức khỏe","y tế","giáo dục","tội phạm",
    "tai nạn","pháp luật","xã hội","thế giới showbiz",
]

def is_relevant(title: str) -> bool:
    t = title.lower()
    if any(kw in t for kw in EXCLUDE_KW):
        return False
    # Nguồn đã là chuyên trang CK nên fallback = True khi không khớp exclude
    return True

# ══════════════════════════════════════════════════════════════════════════════
# TICKER HIGHLIGHT — Bôi đậm mã CP ở đầu tiêu đề
# ══════════════════════════════════════════════════════════════════════════════
TICKERS = {
    "VCB","TCB","BID","CTG","MBB","VPB","ACB","SHB","LPB","HDB","MSB","OCB","TPB","VIB","STB",
    "VHM","VIC","VRE","NVL","DIG","KDH","PDR","BCM","CEO","DXG","HDG","NLG",
    "VNM","SAB","MCH","MSN","KDC","MWG","FRT","DGW","PNJ",
    "GAS","PLX","PVD","PVS","BSR","OIL","PVC","PGD",
    "HPG","HSG","NKG","TLH","VGS","SMC","TNA","POM",
    "FPT","CMG","VGI","ELC",
    "VJC","HVN","ACV","SCS","NCT",
    "REE","GEX","PC1","SZC","BCG","HDC","LCG","HHV",
    "SSI","VND","HCM","VCI","BSI","MBS","ORS","VDS","AGR","CTS","FTS","SHS","TVS","TVB",
    "VBB","AIC","GIL","CC1","HSM","IDC","GMD","VSC","HAH",
    "DBC","HAG","HNG","BAF","PAN","LSS","SBT","QNS",
    "DPM","DCM","BFC","CSV",
    "VGT","TNG","MSH","GMC","TCM","STK",
    "VHC","ANV","CMX","IDI","FMC",
    "BWE","DNP","NBB","VTP","EIB","EVF",
}

def highlight_ticker(title: str) -> str:
    if not title:
        return title
    first = title.split()[0].rstrip(":- ").upper()
    if first in TICKERS:
        rest = title[len(first):]
        return f'<b style="color:#0d3b8e">{first}</b>{rest}'
    return title

# ══════════════════════════════════════════════════════════════════════════════
# FETCH
# ══════════════════════════════════════════════════════════════════════════════
def _fetch_one(url: str):
    try:
        feed = feedparser.parse(url)
        out = []
        for e in feed.entries:
            title = getattr(e, "title", "").strip()
            link  = getattr(e, "link",  "").strip()
            if title and link and is_relevant(title):
                out.append({"title": title, "link": link})
        return out
    except Exception:
        return []

@st.cache_data(ttl=900, show_spinner=False)
def fetch_all_news():
    grouped = {cat: [] for cat in RSS_SOURCES}
    with ThreadPoolExecutor(max_workers=10) as ex:
        futures = {
            ex.submit(_fetch_one, url): cat
            for cat, sources in RSS_SOURCES.items()
            for url in sources.values()
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

# ══════════════════════════════════════════════════════════════════════════════
# RENDER
# ══════════════════════════════════════════════════════════════════════════════
STYLES = {
    "TIN TỨC":      {"hdr": "#D46B08", "bg": "#FFF7E6", "border": "#FFD591"},
    "DOANH NGHIỆP": {"hdr": "#1D4ED8", "bg": "#EFF6FF", "border": "#BFDBFE"},
}

def news_section(label: str, items: list, limit: int = 15):
    s = STYLES.get(label, {"hdr": "#333", "bg": "#fff", "border": "#ddd"})
    hdr, bg, bdr = s["hdr"], s["bg"], s["border"]

    st.markdown(
        f'''<div style="background:{hdr};color:#fff;font-weight:700;font-size:13px;
        padding:7px 14px;border-radius:5px 5px 0 0;letter-spacing:.5px">{label}</div>''',
        unsafe_allow_html=True,
    )

    if not items:
        st.markdown(
            f'''<div style="border:1px solid {bdr};border-top:none;background:{bg};
            border-radius:0 0 5px 5px;padding:12px 14px;color:#888;font-size:13px">
            Không có tin tức.</div>''',
            unsafe_allow_html=True,
        )
        return

    rows = ""
    for item in items[:limit]:
        display = highlight_ticker(item["title"])
        rows += (
            f'<li style="margin-bottom:7px;line-height:1.45">' +
            f'<a href="{item["link"]}" target="_blank"' +
            f' style="text-decoration:none;color:#1a1a1a;font-size:13px">{display}</a></li>'
        )

    st.markdown(
        f'''<div style="border:1px solid {bdr};border-top:none;background:{bg};
        border-radius:0 0 5px 5px;padding:10px 14px 14px">
        <ul style="margin:0;padding-left:18px">{rows}</ul></div>''',
        unsafe_allow_html=True,
    )

# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════
def render_tab_news():
    col_title, col_btn = st.columns([5, 1])
    with col_title:
        st.markdown("#### 📰 Tin tức Chứng khoán & Doanh nghiệp niêm yết")
    with col_btn:
        if st.button("🔄 Làm mới", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    st.caption(
        "Nguồn: CafeF · Vietstock · Tinnhanhchungkhoan · VnEconomy · "
        "VietnamBiz · VnExpress — Cập nhật mỗi 15 phút"
    )

    with st.spinner("Đang tải tin tức..."):
        grouped = fetch_all_news()

    col1, col2 = st.columns(2, gap="medium")
    with col1:
        news_section("TIN TỨC", grouped.get("TIN TỨC", []), limit=15)
    with col2:
        news_section("DOANH NGHIỆP", grouped.get("DOANH NGHIỆP", []), limit=15)


if __name__ == "__main__":
    st.set_page_config(page_title="Tin tức CK", layout="wide")
    render_tab_news()
