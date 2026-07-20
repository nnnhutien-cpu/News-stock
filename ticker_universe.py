"""
ticker_universe.py
------------------
Quản lý "vũ trụ" mã chứng khoán hợp lệ trên 3 sàn HOSE, HNX, UPCOM.

Đây là thành phần CỐT LÕI để nhận diện đúng tin tức doanh nghiệp: một
token 3 chữ cái viết hoa trong tiêu đề tin tức (VD: "HPG", "VNM", "SSI")
chỉ được coi là một MÃ CHỨNG KHOÁN nếu nó nằm trong danh sách mã đang
niêm yết/giao dịch thật sự — chứ không phải cứ 3 chữ hoa là nhận (để
tránh nhầm với các từ viết tắt như GDP, CEO, FDI, CPI, IMF, WTO...).

Chiến lược lấy dữ liệu (ưu tiên theo thứ tự):
1. Cache cục bộ (tickers_cache.json) nếu còn hạn (mặc định 24h) -> nhanh,
   không phụ thuộc mạng.
2. Gọi thư viện `vnstock` (nguồn dữ liệu chính thức, cập nhật hằng ngày,
   có gắn nhãn sàn HOSE/HNX/UPCOM cho từng mã) -> ghi đè cache.
3. Nếu cả hai cách trên đều lỗi (mất mạng, đổi API...), dùng danh sách
   tĩnh dự phòng (FALLBACK_TICKERS) để ứng dụng vẫn chạy được, không bị
   crash — chỉ là độ phủ mã sẽ ít hơn.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Dict, Optional, Set

CACHE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tickers_cache.json")
CACHE_TTL_SECONDS = 24 * 3600  # 24 giờ


@dataclass
class TickerInfo:
    ticker: str
    exchange: str  # "HOSE" | "HNX" | "UPCOM"
    company_name: str = ""


# ---------------------------------------------------------------------------
# Danh sách dự phòng khi không có mạng / vnstock lỗi.
# Đây KHÔNG phải danh sách đầy đủ (~1600+ mã) mà chỉ là các mã phổ biến
# nhất (VN30 + một số mã lớn HNX/UPCOM) để hệ thống không "tê liệt" khi
# offline. Danh sách đầy đủ luôn được ưu tiên lấy từ vnstock ở trên.
# ---------------------------------------------------------------------------
FALLBACK_TICKERS: Dict[str, str] = {
    # HOSE - nhóm VN30 & vốn hoá lớn
    "ACB": "HOSE", "BCM": "HOSE", "BID": "HOSE", "BVH": "HOSE", "CTG": "HOSE",
    "FPT": "HOSE", "GAS": "HOSE", "GVR": "HOSE", "HDB": "HOSE", "HPG": "HOSE",
    "MBB": "HOSE", "MSN": "HOSE", "MWG": "HOSE", "PLX": "HOSE", "POW": "HOSE",
    "SAB": "HOSE", "SHB": "HOSE", "SSB": "HOSE", "SSI": "HOSE", "STB": "HOSE",
    "TCB": "HOSE", "TPB": "HOSE", "VCB": "HOSE", "VHM": "HOSE", "VIB": "HOSE",
    "VIC": "HOSE", "VJC": "HOSE", "VNM": "HOSE", "VPB": "HOSE", "VRE": "HOSE",
    "HAX": "HOSE", "DGC": "HOSE", "DPM": "HOSE", "DCM": "HOSE", "GEX": "HOSE",
    "KBC": "HOSE", "KDH": "HOSE", "NLG": "HOSE", "NVL": "HOSE", "PDR": "HOSE",
    "PNJ": "HOSE", "REE": "HOSE", "VND": "HOSE", "HCM": "HOSE", "VCI": "HOSE",
    "DXG": "HOSE", "HSG": "HOSE", "NKG": "HOSE", "GMD": "HOSE", "PVD": "HOSE",
    "PVT": "HOSE", "DIG": "HOSE", "VOS": "HOSE", "HAG": "HOSE", "HNG": "HOSE",
    "ANV": "HOSE", "VHC": "HOSE", "PC1": "HOSE", "CII": "HOSE", "EIB": "HOSE",
    "OCB": "HOSE", "LPB": "HOSE", "SAM": "HOSE", "FRT": "HOSE", "DGW": "HOSE",
    "PTB": "HOSE", "TRA": "HOSE", "THI": "HOSE", "OIL": "HOSE",
    # HNX
    "SHS": "HNX", "PVS": "HNX", "PVI": "HNX", "VCS": "HNX", "CEO": "HNX",
    "IDC": "HNX", "TNG": "HNX", "NTP": "HNX", "L14": "HNX", "MBS": "HNX",
    "BAB": "HNX", "DTD": "HNX", "PVC": "HNX", "TVC": "HNX", "VGS": "HNX",
    # UPCOM
    "BSR": "UPCOM", "VGT": "UPCOM", "ACV": "UPCOM", "VEA": "UPCOM", "QNS": "UPCOM",
    "MSR": "UPCOM", "MCH": "UPCOM", "SIP": "UPCOM", "VGI": "UPCOM", "DVN": "UPCOM",
    "FOX": "UPCOM", "VTP": "UPCOM", "KBC": "UPCOM", "DMX": "UPCOM",
}

# Các token 3 chữ cái hay bị nhầm là mã CK nhưng thực chất là từ viết tắt
# thông dụng (địa danh, tổ chức, thuật ngữ vĩ mô...). Danh sách này dùng để
# LOẠI TRỪ ngay cả khi trùng ngẫu nhiên với một mã có thật, trừ khi người
# dùng chủ động bỏ nó ra khỏi blacklist vì biết ngữ cảnh của mình.
DEFAULT_BLACKLIST: Set[str] = {
    "GDP", "CPI", "FDI", "IMF", "WTO", "ADB", "FED", "ECB", "SEC", "EU", "UN",
    "USD", "EUR", "GBP", "JPY", "CNY",
    "TP", "UBND", "HDND", "QH", "CP", "TT", "BTC", "NHNN",
    "WHO", "ILO", "NATO", "OPEC", "ASEAN", "APEC",
    "CFO", "CTO", "HR", "PR", "KOL", "SEO", "API",
    "ATM", "POS", "QR", "SMS", "OTP", "KYC", "ESG",
}
# Ghi chú: một vài mã trong FALLBACK_TICKERS (VD: CEO, VND, HCM) là MÃ THẬT
# (CEO = C.E.O Group trên HNX, VND = Chứng khoán VNDirect, HCM = Chứng khoán
# TP.HCM - HSC) nên KHÔNG bị đưa vào blacklist mặc định — chấp nhận một tỷ lệ
# nhầm lẫn nhỏ khi các từ này xuất hiện với nghĩa khác (VD "TP.HCM"), vì phân
# biệt ngữ nghĩa 100% cần NLP/NER phức tạp hơn nhiều so với danh sách loại trừ
# tĩnh. Người dùng có thể tự thêm mã vào blacklist qua tham số extra_blacklist.


def _load_cache() -> Optional[Dict[str, str]]:
    if not os.path.exists(CACHE_PATH):
        return None
    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if time.time() - data.get("_fetched_at", 0) > CACHE_TTL_SECONDS:
            return None
        return data.get("tickers")
    except Exception:
        return None


def _save_cache(tickers: Dict[str, str]) -> None:
    try:
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump({"_fetched_at": time.time(), "tickers": tickers}, f, ensure_ascii=False)
    except Exception:
        pass  # cache là tối ưu hoá, lỗi ghi file không nên làm sập app


def _fetch_from_vnstock() -> Optional[Dict[str, str]]:
    """Lấy danh sách mã CK đầy đủ + sàn niêm yết từ thư viện vnstock.

    Trả về dict {ticker: exchange} hoặc None nếu thất bại (không có mạng,
    đổi API, chưa cài vnstock...). Import được đặt trong hàm để toàn bộ
    module không bắt buộc phải có vnstock mới chạy được (graceful degrade).
    """
    try:
        from vnstock import Listing  # vnstock >= 3.x
        listing = Listing()
        df = listing.all_symbols()  # DataFrame: ticker, organ_name, ...
        # Một số phiên bản vnstock trả cột khác nhau -> dò tên cột linh hoạt
        ticker_col = next((c for c in df.columns if c.lower() in ("ticker", "symbol")), None)
        exchange_col = next(
            (c for c in df.columns if "exchange" in c.lower() or "group" in c.lower() or "comgroup" in c.lower()),
            None,
        )
        if ticker_col is None:
            return None
        result: Dict[str, str] = {}
        for _, row in df.iterrows():
            t = str(row[ticker_col]).strip().upper()
            if not t or len(t) > 4 or not t.isalpha():
                continue
            exch = str(row[exchange_col]).strip().upper() if exchange_col else "UNKNOWN"
            result[t] = exch
        return result or None
    except Exception:
        return None


def get_ticker_universe(force_refresh: bool = False) -> Dict[str, str]:
    """Trả về dict {MÃ: SÀN} đầy đủ nhất có thể, dùng cache 24h.

    Đây là hàm nên được gọi từ các module khác (news_fetcher, app...).
    """
    if not force_refresh:
        cached = _load_cache()
        if cached:
            return cached

    fresh = _fetch_from_vnstock()
    if fresh:
        _save_cache(fresh)
        return fresh

    # Không lấy được dữ liệu mới -> thử cache cũ (dù đã hết hạn) trước khi
    # phải quay về danh sách tĩnh, vì cache cũ vẫn đúng hơn danh sách rút gọn.
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("tickers"):
                return data["tickers"]
        except Exception:
            pass

    return dict(FALLBACK_TICKERS)


def get_blacklist() -> Set[str]:
    return set(DEFAULT_BLACKLIST)
