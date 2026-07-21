"""
check_feeds.py
---------------
Script chẩn đoán độc lập (không cần Streamlit) — in ra trạng thái từng
nguồn RSS: OK (kèm số bài lấy được) hoặc LỖI (kèm lý do cụ thể: HTTP 403,
timeout, XML hỏng, 0 bài...).

Dùng khi nghi ngờ một nguồn (VD: Vietstock, VietnamBiz) không lên tin:
chạy script này để biết CHÍNH XÁC nguyên nhân, thay vì đoán mò.

Chạy: python check_feeds.py

Có thể thêm bước này vào workflow GitHub Actions (auto_news.yml) trước
bước cào tin chính, để mỗi lần chạy đều ghi log rõ ràng nguồn nào đang
gặp vấn đề:

    - name: Kiểm tra trạng thái nguồn RSS
      run: python check_feeds.py
"""

from __future__ import annotations

from news_fetcher import RSS_SOURCES, _fetch_one_feed


def main() -> int:
    print("Đang kiểm tra từng nguồn RSS...\n")
    total = 0
    ok_count = 0
    failures = []

    for category, sources in RSS_SOURCES.items():
        print(f"=== {category} ===")
        for source_name, url in sources.items():
            total += 1
            _, status = _fetch_one_feed(url)
            status.source_name = source_name
            if status.ok:
                ok_count += 1
                print(f"  [OK]   {source_name:30s} {status.entry_count:3d} bài")
            else:
                failures.append(status)
                print(f"  [LỖI]  {source_name:30s} {status.error}")
        print()

    print(f"Tổng kết: {ok_count}/{total} nguồn OK.\n")

    if failures:
        print("Chi tiết các nguồn lỗi:")
        for s in failures:
            print(f"  - {s.source_name}: {s.error}")
            print(f"    URL: {s.url}")
        print(
            "\nGợi ý: lỗi 'HTTP 403' hoặc '0 bài viết' thường do trang đặt sau\n"
            "Cloudflare/WAF chặn IP của máy chủ chạy script (đặc biệt là IP dùng\n"
            "chung của GitHub Actions — rất hay bị các trang VN chặn vì bị lạm\n"
            "dụng bởi bot khác). Trang vẫn mở bình thường trên trình duyệt cá\n"
            "nhân của bạn không có nghĩa là script cũng truy cập được.\n"
            "Cách xử lý: (1) thử lại vào giờ khác xem có phải chặn tạm thời,\n"
            "(2) cân nhắc dùng self-hosted runner với IP dân dụng thay vì\n"
            "GitHub-hosted runner, (3) hoặc dùng dịch vụ proxy/RSS-to-RSS\n"
            "trung gian (VD: rss-bridge) để đổi IP nguồn request."
        )
        return 1

    print("Tất cả nguồn đều hoạt động tốt.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
