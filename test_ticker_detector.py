"""
Kiểm thử nhanh ticker_detector.py mà KHÔNG cần gọi mạng / vnstock:
dùng một universe giả lập nhỏ để xác nhận logic lọc true-positive /
false-positive hoạt động đúng như thiết kế.

Chạy: python test_ticker_detector.py
"""

from ticker_detector import TickerDetector

FAKE_UNIVERSE = {
    "HPG": "HOSE", "VNM": "HOSE", "SSI": "HOSE", "FPT": "HOSE",
    "CEO": "HNX", "VND": "HOSE", "HCM": "HOSE", "TRA": "HOSE",
}
BLACKLIST = {"GDP", "CPI", "FDI", "IMF", "TP"}

detector = TickerDetector(FAKE_UNIVERSE, BLACKLIST)

cases = [
    # (tiêu đề, mô tả, link, mã kỳ vọng nhận diện được)
    ("Hòa Phát (HPG) báo lãi quý 2 tăng mạnh", "", "", {"HPG"}),
    ("GDP quý 2 tăng 6,8%, lạm phát CPI trong tầm kiểm soát", "", "", set()),
    ("Cổ phiếu VNM và SSI cùng bật tăng trần phiên hôm nay", "", "", {"VNM", "SSI"}),
    ("Sự xuất hiện của Tổng thống Donald Trump tại trận chung kết World Cup", "", "", set()),
    ("Tăng tốc thi công cao tốc Bến Lức - Long Thành nối TP.HCM với Đồng Nai", "", "", set()),
    ("FPT ký hợp đồng AI Factory trị giá lớn với đối tác Nhật Bản", "", "", {"FPT"}),
    (
        "Cập nhật giá cổ phiếu",
        "",
        "https://cafef.vn/du-lieu/hose/hpg-tap-doan-hoa-phat.chn",
        {"HPG"},
    ),
]

all_ok = True
for title, desc, link, expected in cases:
    result = set(detector.detect(title, desc, link).codes)
    ok = result == expected
    all_ok &= ok
    status = "OK " if ok else "FAIL"
    print(f"[{status}] '{title}' -> nhận diện: {result} (kỳ vọng: {expected})")

print("\n=> TẤT CẢ TEST PASS" if all_ok else "\n=> CÓ TEST FAIL, xem log ở trên")
