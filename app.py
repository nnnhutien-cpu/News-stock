import streamlit as st
from tab_news import render_tab_news
from news_sources import render_tab_sources

st.set_page_config(
    page_title="Tin tức Chứng khoán VN · 3 Sàn",
    page_icon="📰",
    layout="wide",
)

tab1, tab2 = st.tabs(["📰 Tin tức", "📚 Nguồn dữ liệu"])

with tab1:
    render_tab_news()

with tab2:
    render_tab_sources()
