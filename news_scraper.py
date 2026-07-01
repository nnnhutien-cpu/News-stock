import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import json

def fetch_rss_news(rss_url, category):
    """Cào tin tức từ RSS (nhanh, nhẹ, không bị chặn)"""
    try:
        response = requests.get(rss_url, timeout=10)
        soup = BeautifulSoup(response.content, features="xml")
        articles = soup.findAll('item')
        
        news_list = []
        for a in articles[:10]: # Lấy 10 tin mới nhất mỗi chuyên mục
            news_list.append({
                'title': a.find('title').text if a.find('title') else '',
                'link': a.find('link').text if a.find('link') else '',
                'pubDate': a.find('pubDate').text if a.find('pubDate') else '',
                'category': category
            })
        return news_list
    except Exception as e:
        print(f"Lỗi khi cào {category}: {e}")
        return []

def update_daily_news():
    print(f"Bắt đầu cào tin tức lúc: {datetime.now()}")
    
    # 1. Tin Thế giới & Vĩ mô trong nước (Dùng RSS VnExpress)
    world_news = fetch_rss_news('https://vnexpress.net/rss/the-gioi.rss', 'Thế giới')
    macro_news = fetch_rss_news('https://vnexpress.net/rss/kinh-doanh.rss', 'Kinh doanh & Vĩ mô')
    
    # 2. Tin Doanh nghiệp niêm yết (Dùng RSS CafeF chuyên trang chứng khoán)
    corporate_news = fetch_rss_news('https://cafef.vn/doc-nhanh/chung-khoan.rss', 'Doanh nghiệp')
    
    # Gộp tất cả lại
    all_news = world_news + macro_news + corporate_news
    
    # Lưu ra file JSON để Streamlit của bạn đọc lên giao diện
    with open('daily_news.json', 'w', encoding='utf-8') as f:
        json.dump(all_news, f, ensure_ascii=False, indent=4)
        
    print(f"Đã lưu thành công {len(all_news)} bản tin!")

if __name__ == "__main__":
    update_daily_news()
