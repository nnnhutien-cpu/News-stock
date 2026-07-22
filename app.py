"""
app.py
------
Giao diện Streamlit chính. Chạy bằng:  streamlit run app.py

Bố cục:
- Ô tìm kiếm theo mã CK hoặc từ khoá (áp dụng cho cả 2 tab).
- TAB 1 "Tổng quan": 3 cột TIN TỨC / DOANH NGHIỆP / THẾ GIỚI + khu vực
  "Mã CK được nhắc đến hôm nay" (click để lọc).
- TAB 2 "Doanh nghiệp theo ngành": các tin có gắn mã CK, nhóm theo ngành
  (Ngân hàng, Chứng khoán, Bất động sản, Bán lẻ...) lấy từ phân ngành ICB
  thật của vnstock — xem ticker_universe.get_ticker_sectors().
- Nút tải CSV toàn bộ tin đã cào (đã gắn nhãn mã CK + ngành).
- Khu vực debug trạng thái từng nguồn RSS.
"""

from __future__ import annotations

import io

import pandas as pd
import streamlit as st

from news_fetcher import (
    collect_tickers_today,
    fetch_all_news,
    group_by_category,
    group_by_sector,
)
from ticker_detector import TickerDetector
from ticker_universe import (
    get_blacklist,
    get_company_aliases,
    get_ticker_sectors,
    get_ticker_universe,
)

st.set_page_config(page_title="Tin tức Chứng khoán VN", layout="wide")


@st.cache_resource(ttl=24 * 3600)
def load_detector() -> TickerDetector:
    universe = get_ticker_universe()
    return TickerDetector(universe, get_blacklist(), get_company_aliases())


@st.cache_data(ttl=24 * 3600)
def load_sector_map():
    return get_ticker_sectors()


@st.cache_data(ttl=900)  # 15 phút, giống chu kỳ cập nhật của bản cũ
def load_news(_detector: TickerDetector, _sector_map: dict):
    items, fetch_stats = fetch_all_news(detector=_detector, sector_map=_sector_map, verbose=True)
    return items, fetch_stats


def render_news_list(items, max_rows: int = 60):
    for it in items[:max_rows]:
        tag = f" `{'/'.join(it.tickers)}`" if it.tickers else ""
        st.markdown(
            f"- [{it.title}]({it.link}){tag}  \n  <small>{it.source} · {it.published}</small>",
            unsafe_allow_html=True,
        )


def main():
    detector = load_detector()
    sector_map = load_sector_map()
    items, fetch_stats = load_news(detector, sector_map)
    grouped = group_by_category(items)
    ticker_counts = collect_tickers_today(items)
    sector_groups = group_by_sector(items)

    total_count = len(items)
    n_tickers = len(ticker_counts)

    st.markdown(
        f"**{total_count} tin** (trong 2 ngày gần nhất) · **{n_tickers} mã được nhắc đến** · "
        f"Nguồn: CafeF · Vietstock · TNCK · VnEconomy · VietnamBiz · VnExpress · Cập nhật 15 phút/lần"
    )

    query = st.text_input(
        "🔍 Tìm theo mã CK hoặc từ khoá",
        placeholder="VD: HPG hoặc cổ tức hoặc ngân hàng",
    )

    selected_ticker = st.session_state.get("selected_ticker")
    if selected_ticker:
        st.info(f"Đang lọc theo mã **{selected_ticker}** — bấm 'Bỏ lọc' để xem lại tất cả.")
        if st.button("❌ Bỏ lọc"):
            st.session_state["selected_ticker"] = None
            st.rerun()

    def matches_filter(item) -> bool:
        if selected_ticker and selected_ticker not in item.tickers:
            return False
        if query:
            q = query.strip().lower()
            in_title = q in item.title.lower()
            in_ticker = any(q == t.lower() for t in item.tickers)
            if not (in_title or in_ticker):
                return False
        return True

    tab_overview, tab_sector = st.tabs(["📰 Tổng quan", "🏢 Doanh nghiệp theo ngành"])

    # ------------------------------------------------------------ TAB 1
    with tab_overview:
        cols = st.columns(3)
        col_titles = ["TIN TỨC", "DOANH NGHIỆP", "THẾ GIỚI"]
        col_colors = ["#f2a341", "#3b3bdb", "#1f9d55"]

        for col, cat, color in zip(cols, col_titles, col_colors):
            with col:
                filtered = [it for it in grouped.get(cat, []) if matches_filter(it)]
                st.markdown(
                    f"<div style='background:{color};color:white;padding:6px 10px;"
                    f"border-radius:4px;font-weight:600;'>{cat} ({len(filtered)} tin)</div>",
                    unsafe_allow_html=True,
                )
                render_news_list(filtered)

        st.divider()
        st.markdown("#### 🏷️ Mã CK được nhắc đến hôm nay — click để lọc")
        if ticker_counts:
            tickers_list = list(ticker_counts.items())
            per_row = 10
            for i in range(0, len(tickers_list), per_row):
                row = tickers_list[i : i + per_row]
                btn_cols = st.columns(len(row))
                for c, (tk, cnt) in zip(btn_cols, row):
                    with c:
                        if st.button(f"{tk} ({cnt})", key=f"tk_{tk}"):
                            st.session_state["selected_ticker"] = tk
                            st.rerun()
        else:
            st.caption("Chưa nhận diện được mã CK nào trong đợt cào tin gần nhất.")

    # ------------------------------------------------------------ TAB 2
    with tab_sector:
        st.caption(
            "Chỉ gồm tin đã nhận diện được mã CK (HOSE/HNX/UPCOM), nhóm theo "
            "ngành ICB lấy từ vnstock (cache 24h). Ngành của 1 tin lấy theo "
            "mã ĐẦU TIÊN nhận diện được trong tiêu đề."
        )
        if not sector_groups:
            st.info("Chưa có tin doanh nghiệp nào trong đợt cào gần nhất.")
        else:
            sector_names = list(sector_groups.keys())
            sector_tabs = st.tabs([f"{s} ({len(sector_groups[s])})" for s in sector_names])
            for tab, sector in zip(sector_tabs, sector_names):
                with tab:
                    filtered = [it for it in sector_groups[sector] if matches_filter(it)]
                    if not filtered:
                        st.caption("Không có tin khớp bộ lọc hiện tại.")
                    render_news_list(filtered, max_rows=80)

    # ------------------------------------------------------------ Chung
    df = pd.DataFrame([it.as_dict() for it in items])
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False, encoding="utf-8-sig")
    st.download_button(
        "⬇️ Tải CSV",
        data=csv_buffer.getvalue().encode("utf-8-sig"),
        file_name="tin_tuc_chung_khoan.csv",
        mime="text/csv",
    )

    # Khu vực debug: hiển thị trạng thái fetch từng nguồn RSS ngay trên UI,
    # để thấy CHÍNH XÁC nguồn nào lỗi (403 do chặn bot, timeout, XML hỏng...)
    # thay vì chỉ thấy "thiếu tin Vietstock/VietnamBiz" mà không rõ vì sao.
    n_ok = sum(1 for s in fetch_stats if s.ok)
    with st.expander(f"🔧 Trạng thái nguồn tin ({n_ok}/{len(fetch_stats)} nguồn OK)"):
        status_df = pd.DataFrame(
            [
                {
                    "Nguồn": s.source_name,
                    "Trạng thái": "✅ OK" if s.ok else "❌ Lỗi",
                    "Số bài": s.entry_count,
                    "Ghi chú": s.error,
                    "URL": s.url,
                }
                for s in fetch_stats
            ]
        )
        st.dataframe(status_df, use_container_width=True, hide_index=True)
        if n_ok < len(fetch_stats):
            st.caption(
                "Nguồn báo lỗi 403/0 bài thường do trang đặt sau Cloudflare/WAF "
                "chặn IP của máy chủ chạy ứng dụng (kể cả khi vẫn mở được bằng "
                "trình duyệt cá nhân). Xem README mục 'Khi Vietstock/VietnamBiz "
                "không lấy được tin' để biết cách xử lý."
            )


if __name__ == "__main__":
    main()
