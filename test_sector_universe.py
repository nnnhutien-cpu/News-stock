"""
Kiểm thử ticker_universe.get_ticker_sectors():
  1) Nhánh fallback khi KHÔNG có mạng/vnstock (dùng SECTOR_FALLBACK).
  2) Nhánh parse dữ liệu thật từ vnstock — mô phỏng bằng DataFrame giả lập
     đúng cấu trúc cột mà Listing().symbols_by_industries() trả về
     (symbol, icb_name1..4, organ_name), KHÔNG cần mạng.

Chạy: python test_sector_universe.py
"""

import sys
import types

import pandas as pd

import ticker_universe as tu


def test_fallback_offline():
    tu._save_sector_cache  # đảm bảo import không lỗi
    # Xoá cache nếu có để chắc chắn đi vào nhánh fetch (sẽ lỗi vì không có
    # mạng/vnstock trong môi trường test) -> phải rơi về SECTOR_FALLBACK.
    import os
    if os.path.exists(tu.SECTOR_CACHE_PATH):
        os.remove(tu.SECTOR_CACHE_PATH)

    sectors = tu.get_ticker_sectors(force_refresh=True)
    assert sectors, "get_ticker_sectors() không được trả về rỗng"
    assert sectors.get("HPG", {}).get("sector") == "Thép", sectors.get("HPG")
    assert sectors.get("VCB", {}).get("sector") == "Ngân hàng", sectors.get("VCB")
    print("[OK] Fallback offline hoạt động đúng (HPG -> Thép, VCB -> Ngân hàng)")


def test_parse_mock_vnstock_dataframe():
    """Giả lập vnstock trả về DataFrame đúng cấu trúc cột thật (đã xác minh
    qua tài liệu vnstock: symbol, icb_name1..4, organ_name) để kiểm tra hàm
    _fetch_sectors_from_vnstock() parse đúng mà không cần mạng thật."""
    mock_df = pd.DataFrame(
        [
            {
                "symbol": "VCB",
                "icb_name1": "Tài chính",
                "icb_name2": "Ngân hàng",
                "icb_name3": "Ngân hàng",
                "icb_name4": "Ngân hàng",
                "organ_name": "Ngân hàng TMCP Ngoại thương Việt Nam",
            },
            {
                "symbol": "HPG",
                "icb_name1": "Nguyên vật liệu",
                "icb_name2": "Tài nguyên cơ bản",
                "icb_name3": "Thép",
                "icb_name4": "Thép",
                "organ_name": "CTCP Tập đoàn Hòa Phát",
            },
            {
                # Mã rác/quỹ có thể lẫn trong dữ liệu thật -> phải bị loại
                # vì độ dài > 4 hoặc không phải toàn chữ cái.
                "symbol": "E1VFVN30",
                "icb_name1": "", "icb_name2": "", "icb_name3": "", "icb_name4": "",
                "organ_name": "Quỹ ETF VN30",
            },
        ]
    )

    class FakeListing:
        def symbols_by_industries(self):
            return mock_df

    # "Cấy" module vnstock giả vào sys.modules để _fetch_sectors_from_vnstock()
    # (vốn làm `from vnstock import Listing`) lấy được bản giả lập này, không
    # cần cài/gọi thật vnstock qua mạng.
    fake_module = types.ModuleType("vnstock")
    fake_module.Listing = FakeListing
    sys.modules["vnstock"] = fake_module

    result = tu._fetch_sectors_from_vnstock()
    assert result is not None, "Phải parse được DataFrame giả lập"
    assert result["VCB"]["sector"] == "Ngân hàng", result["VCB"]
    assert result["HPG"]["sector"] == "Thép", result["HPG"]
    assert "E1VFVN30" not in result, "Mã quỹ ETF (không phải mã 3-4 chữ cái) phải bị loại"
    assert result["HPG"]["organ_name"] == "CTCP Tập đoàn Hòa Phát"
    print("[OK] Parse DataFrame giả lập từ vnstock đúng cấu trúc, đúng logic loại mã rác")

    del sys.modules["vnstock"]


def test_map_to_grouped_sector_edge_cases():
    """Kiểm tra riêng hàm map_to_grouped_sector() với các ca dễ gán nhầm."""
    # Ca mơ hồ: tên ICB tiện ích gộp chứa cả "dầu khí" lẫn "điện" -> phải
    # về nhóm Điện - Tiện ích, KHÔNG phải Dầu khí.
    assert tu.map_to_grouped_sector(["Điện, nước & xăng dầu khí đốt"]) == "Điện - Tiện ích"
    # Công ty dầu khí thuần, không có "điện" -> đúng là Dầu khí.
    assert tu.map_to_grouped_sector(["Dầu khí", "Dầu khí"]) == "Dầu khí"
    # Ngân hàng phải thắng dù ICB cấp 1 ghi là "Tài chính" chung chung.
    assert tu.map_to_grouped_sector(["Tài chính", "Ngân hàng", "Ngân hàng"]) == "Ngân hàng"
    # Không khớp từ khoá nào -> "Khác".
    assert tu.map_to_grouped_sector(["Giải trí đại chúng"]) == "Khác"
    print("[OK] map_to_grouped_sector() xử lý đúng các ca mơ hồ (điện/dầu khí, ngân hàng/tài chính)")


if __name__ == "__main__":
    test_fallback_offline()
    test_parse_mock_vnstock_dataframe()
    test_map_to_grouped_sector_edge_cases()
    print("\n=> TẤT CẢ TEST get_ticker_sectors() PASS")
