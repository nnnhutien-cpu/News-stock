"""
app.py
------
Giao diện Streamlit chính. Chạy bằng:  streamlit run app.py

Bố cục phỏng theo dashboard tham khảo:
- Ô tìm kiếm theo mã CK hoặc từ khoá.
- 3 cột: TIN TỨC / DOANH NGHIỆP / THẾ GIỚI.
- Khu vực "Mã CK được nhắc đến hôm nay" — click 1 mã để lọc toàn trang.
- Nút tải CSV toàn bộ tin đã cào (đã gắn nhãn mã CK).
"""

from __future__ import annotations

import io

import pandas as pd
import streamlit as st

from news_fetcher import collect_tickers_today, fetch_all_news, group_by_category
from ticker_detector import TickerDetector
from ticker_universe import get_blacklist, get_ticker_universe

st.set_page_config(page_title="Tin tức Chứng khoán VN", layout="wide")


@st.cache_resource(ttl=24 * 3600)
def load_detector() -> TickerDetector:
    universe = get_ticker_universe()
    return TickerDetector(universe, get_blacklist())


@st.cache_data(ttl=900)  # 15 phút, giống chu kỳ cập nhật của bản cũ
def load_news(_detector: TickerDetector):
    items = fetch_all_news(detector=_detector)
    return items


def main():
    detector = load_detector()
    items = load_news(detector)
    grouped = group_by_category(items)
    ticker_counts = collect_tickers_today(items)

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
            for it in filtered[:60]:
                tag = f" `{'/'.join(it.tickers)}`" if it.tickers else ""
                st.markdown(f"- [{it.title}]({it.link}){tag}  \n  <small>{it.source} · {it.published}</small>",
                            unsafe_allow_html=True)

    st.divider()
    st.markdown("#### 🏷️ Mã CK được nhắc đến hôm nay — click để lọc")
    if ticker_counts:
        # Hiển thị dạng nút bấm để click lọc, chia thành hàng ~10 nút/dòng
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

    # Nút tải CSV toàn bộ (không áp dụng filter, để người dùng có dữ liệu gốc đầy đủ)
    df = pd.DataFrame([it.as_dict() for it in items])
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False, encoding="utf-8-sig")
    st.download_button(
        "⬇️ Tải CSV",
        data=csv_buffer.getvalue().encode("utf-8-sig"),
        file_name="tin_tuc_chung_khoan.csv",
        mime="text/csv",
    )


if __name__ == "__main__":
    main()
