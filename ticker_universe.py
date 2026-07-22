"""
ticker_universe.py
------------------
Quản lý "vũ trụ" mã chứng khoán hợp lệ trên 3 sàn HOSE, HNX, UPCOM —
VÀ tên công ty tương ứng (để nhận diện tin tức chỉ nhắc tên, không nhắc
mã, ví dụ "Viglacera bổ nhiệm..." -> mã VGC).

Đây là thành phần CỐT LÕI để nhận diện đúng tin tức doanh nghiệp: một
token 3 chữ cái viết hoa trong tiêu đề tin tức (VD: "HPG", "VNM", "SSI")
chỉ được coi là một MÃ CHỨNG KHOÁN nếu nó nằm trong danh sách mã đang
niêm yết/giao dịch thật sự — chứ không phải cứ 3 chữ hoa là nhận (để
tránh nhầm với các từ viết tắt như GDP, CEO, FDI, CPI, IMF, WTO...).
Đồng thời, tên công ty (VD: "Viglacera", "Hoà Phát", "Vinamilk"...) cũng
được ánh xạ về mã, vì phần lớn tin tức doanh nghiệp viết theo TÊN chứ
không viết mã trong tiêu đề.

Chiến lược lấy dữ liệu (ưu tiên theo thứ tự):
1. Cache cục bộ (tickers_cache.json) nếu còn hạn (mặc định 24h) -> nhanh,
   không phụ thuộc mạng.
2. Gọi thư viện `vnstock` (nguồn dữ liệu chính thức, cập nhật hằng ngày,
   có cả tên đầy đủ + tên viết tắt của từng mã) -> ghi đè cache.
3. Nếu cả hai cách trên đều lỗi (mất mạng, đổi API...), dùng danh sách
   tĩnh dự phòng (FALLBACK_TICKERS / FALLBACK_ALIASES) để ứng dụng vẫn
   chạy được, không bị crash — chỉ là độ phủ mã/tên sẽ ít hơn.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Set

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
    "PTB": "HOSE", "TRA": "HOSE", "THI": "HOSE", "OIL": "HOSE", "VGC": "HOSE",
    "VCG": "HOSE", "HVN": "HOSE", "HDG": "HOSE", "DPG": "HOSE", "DBC": "HOSE",
    "BMP": "HOSE", "BWE": "HOSE", "NT2": "HOSE", "GEG": "HOSE", "BHN": "HOSE",
    "HTN": "HOSE",
    # HNX
    "SHS": "HNX", "PVS": "HNX", "PVI": "HNX", "VCS": "HNX", "CEO": "HNX",
    "IDC": "HNX", "TNG": "HNX", "NTP": "HNX", "L14": "HNX", "MBS": "HNX",
    "BAB": "HNX", "DTD": "HNX", "PVC": "HNX", "TVC": "HNX", "VGS": "HNX",
    # UPCOM
    "BSR": "UPCOM", "VGT": "UPCOM", "ACV": "UPCOM", "VEA": "UPCOM", "QNS": "UPCOM",
    "MSR": "UPCOM", "MCH": "UPCOM", "SIP": "UPCOM", "VGI": "UPCOM", "DVN": "UPCOM",
    "FOX": "UPCOM", "VTP": "UPCOM", "DMX": "UPCOM", "PGB": "UPCOM",
}

# Tên công ty (viết thường, không phân biệt hoa/thường khi so khớp) hay
# xuất hiện trong tiêu đề THAY VÌ mã CK. Danh sách này là bộ dự phòng khi
# offline / vnstock không trả về organ_name; khi online, hệ thống ưu tiên
# gộp thêm tên lấy trực tiếp từ vnstock để phủ được ~1600+ mã.
FALLBACK_ALIASES: Dict[str, List[str]] = {
    "VGC": ["Viglacera"],
    "HPG": ["Hòa Phát", "Hoà Phát", "Tập đoàn Hòa Phát"],
    "VNM": ["Vinamilk"],
    "VIC": ["Vingroup"],
    "VHM": ["Vinhomes"],
    "VRE": ["Vincom Retail"],
    "MSN": ["Masan", "Tập đoàn Masan"],
    "TCB": ["Techcombank"],
    "VCB": ["Vietcombank"],
    "BID": ["BIDV"],
    "CTG": ["VietinBank", "Vietinbank"],
    "MBB": ["MB Bank", "MBBank", "Ngân hàng MB"],
    "STB": ["Sacombank"],
    "EIB": ["Eximbank"],
    "OCB": ["OCB", "Ngân hàng Phương Đông"],
    "VND": ["VNDirect"],
    "HCM": ["Chứng khoán TP.HCM", "HSC"],
    "VJC": ["Vietjet", "Vietjet Air"],
    "HVN": ["Vietnam Airlines"],
    "NVL": ["Novaland"],
    "DXG": ["Đất Xanh", "Tập đoàn Đất Xanh"],
    "KDH": ["Khang Điền"],
    "NLG": ["Nam Long"],
    "PDR": ["Phát Đạt"],
    "GAS": ["PV GAS", "PVGAS"],
    "PLX": ["Petrolimex"],
    "MWG": ["Thế Giới Di Động", "Thế giới Di động"],
    "PNJ": ["PNJ", "Vàng bạc đá quý Phú Nhuận"],
    "VCG": ["Vinaconex"],
    "HSG": ["Hoa Sen", "Tập đoàn Hoa Sen"],
    "NKG": ["Nam Kim", "Thép Nam Kim"],
    "SAB": ["Sabeco"],
    "BHN": ["Habeco"],
    "GVR": ["Tập đoàn Cao su Việt Nam", "Cao su Việt Nam"],
    "BCM": ["Becamex"],
    "KBC": ["Kinh Bắc", "Đô thị Kinh Bắc"],
    "IDC": ["Idico"],
    "VCS": ["Vicostone"],
    "BVH": ["Bảo Việt", "Tập đoàn Bảo Việt"],
    "POW": ["PV Power"],
    "PVD": ["PV Drilling"],
    "PVT": ["PV Trans", "PVTrans"],
    "DCM": ["Đạm Cà Mau"],
    "DPM": ["Đạm Phú Mỹ"],
    "DGC": ["Hoá chất Đức Giang", "Hóa chất Đức Giang"],
    "FPT": ["FPT", "Tập đoàn FPT"],
    "SSI": ["Chứng khoán SSI"],
    "ACB": ["ACB", "Ngân hàng Á Châu"],
    "HDB": ["HDBank"],
    "TPB": ["TPBank"],
    "VPB": ["VPBank"],
    "SHB": ["SHB", "Ngân hàng SHB"],
    "LPB": ["LPBank", "Ngân hàng Bưu điện Liên Việt"],
    "BSR": ["Lọc hoá dầu Bình Sơn", "Lọc hóa dầu Bình Sơn", "BSR"],
    "ACV": ["ACV", "Tổng công ty Cảng hàng không"],
    "VEA": ["VEAM"],
    "QNS": ["Đường Quảng Ngãi"],
    "MSR": ["Masan High-Tech Materials"],
    "MCH": ["Masan Consumer"],
    "VGI": ["Viettel Global"],
    "VTP": ["Viettel Post"],
    "FOX": ["FPT Telecom"],
    "GEX": ["Gelex", "Tập đoàn Gelex"],
    "REE": ["REE", "Cơ điện lạnh REE"],
    "CII": ["Hạ tầng Kỹ thuật TP.HCM", "CII"],
    "HAG": ["Hoàng Anh Gia Lai", "HAGL"],
    "HNG": ["HAGL Agrico"],
    "ANV": ["Nam Việt", "Thuỷ sản Nam Việt", "Thủy sản Nam Việt"],
    "VHC": ["Vĩnh Hoàn"],
    "GMD": ["Gemadept"],
    "DIG": ["DIC Corp", "DIC Group"],
    "FRT": ["FPT Retail"],
    "DGW": ["Digiworld"],
    "PTB": ["Phú Tài"],
    "TRA": ["Traphaco"],
    "PGB": ["PGBank", "PG Bank", "Ngân hàng Xăng dầu Petrolimex"],
    "HTN": ["Hưng Thịnh Incons"],
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
    # Các tiền tố nhãn tin nhanh rất hay gặp ở đầu tiêu đề CafeF/Vietstock
    # (VD: "TIN: Xe VF 2 mang tin vui...", "TIN: Địa ốc Kido..."), dễ bị
    # nhận nhầm thành mã CK vì đúng 3 chữ hoa đứng độc lập ở đầu câu.
    "TIN", "HOT", "LIVE", "NEW",
}
# Ghi chú: một vài mã trong FALLBACK_TICKERS (VD: CEO, VND, HCM) là MÃ THẬT
# (CEO = C.E.O Group trên HNX, VND = Chứng khoán VNDirect, HCM = Chứng khoán
# TP.HCM - HSC) nên KHÔNG bị đưa vào blacklist mặc định — chấp nhận một tỷ lệ
# nhầm lẫn nhỏ khi các từ này xuất hiện với nghĩa khác (VD "TP.HCM"), vì phân
# biệt ngữ nghĩa 100% cần NLP/NER phức tạp hơn nhiều so với danh sách loại trừ
# tĩnh. Người dùng có thể tự thêm mã vào blacklist qua tham số extra_blacklist.


def _load_cache() -> Optional[dict]:
    if not os.path.exists(CACHE_PATH):
        return None
    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if time.time() - data.get("_fetched_at", 0) > CACHE_TTL_SECONDS:
            return None
        return data
    except Exception:
        return None


def _load_cache_ignore_ttl() -> Optional[dict]:
    if not os.path.exists(CACHE_PATH):
        return None
    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _save_cache(tickers: Dict[str, str], aliases: Dict[str, List[str]]) -> None:
    try:
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(
                {"_fetched_at": time.time(), "tickers": tickers, "aliases": aliases},
                f,
                ensure_ascii=False,
            )
    except Exception:
        pass  # cache là tối ưu hoá, lỗi ghi file không nên làm sập app


def _fetch_from_vnstock() -> Optional[tuple[Dict[str, str], Dict[str, List[str]]]]:
    """Lấy danh sách mã CK + tên công ty đầy đủ từ thư viện vnstock.

    Trả về (tickers, aliases) hoặc None nếu thất bại (không có mạng, đổi
    API, chưa cài vnstock...). Import được đặt trong hàm để toàn bộ module
    không bắt buộc phải có vnstock mới chạy được (graceful degrade).
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
        name_cols = [
            c for c in df.columns
            if any(k in c.lower() for k in ("organname", "organ_name", "shortname", "short_name", "companyname"))
        ]
        if ticker_col is None:
            return None

        tickers: Dict[str, str] = {}
        aliases: Dict[str, List[str]] = {}
        for _, row in df.iterrows():
            t = str(row[ticker_col]).strip().upper()
            if not t or len(t) > 4 or not t.isalpha():
                continue
            exch = str(row[exchange_col]).strip().upper() if exchange_col else "UNKNOWN"
            tickers[t] = exch
            names = []
            for nc in name_cols:
                val = row.get(nc)
                if val and isinstance(val, str) and val.strip():
                    names.append(val.strip())
            if names:
                aliases[t] = names
        return (tickers, aliases) if tickers else None
    except Exception:
        return None


def get_ticker_universe(force_refresh: bool = False) -> Dict[str, str]:
    """Trả về dict {MÃ: SÀN} đầy đủ nhất có thể, dùng cache 24h.

    Đây là hàm nên được gọi từ các module khác (news_fetcher, app...).
    """
    tickers, _ = get_ticker_universe_and_aliases(force_refresh=force_refresh)
    return tickers


def get_company_aliases(force_refresh: bool = False) -> Dict[str, List[str]]:
    """Trả về dict {MÃ: [tên gọi khác nhau của công ty]}."""
    _, aliases = get_ticker_universe_and_aliases(force_refresh=force_refresh)
    return aliases


def get_ticker_universe_and_aliases(
    force_refresh: bool = False,
) -> "tuple[Dict[str, str], Dict[str, List[str]]]":
    """Nguồn sự thật duy nhất: lấy đồng thời mã + tên, luôn merge thêm
    FALLBACK_ALIASES (danh sách tên curate thủ công) vào bất kể online hay
    offline, vì tên viết tắt/thân mật ("Hòa Phát", "Viglacera"...) thường
    chính xác hơn organ_name đầy đủ mà vnstock trả về.
    """
    if not force_refresh:
        cached = _load_cache()
        if cached:
            tickers = cached.get("tickers", {})
            aliases = _merge_aliases(cached.get("aliases", {}), FALLBACK_ALIASES)
            if tickers:
                return tickers, aliases

    fresh = _fetch_from_vnstock()
    if fresh:
        tickers, aliases = fresh
        _save_cache(tickers, aliases)
        return tickers, _merge_aliases(aliases, FALLBACK_ALIASES)

    # Không lấy được dữ liệu mới -> thử cache cũ (dù đã hết hạn) trước khi
    # phải quay về danh sách tĩnh, vì cache cũ vẫn đúng hơn danh sách rút gọn.
    stale = _load_cache_ignore_ttl()
    if stale and stale.get("tickers"):
        return stale["tickers"], _merge_aliases(stale.get("aliases", {}), FALLBACK_ALIASES)

    return dict(FALLBACK_TICKERS), dict(FALLBACK_ALIASES)


def _merge_aliases(
    primary: Dict[str, List[str]], extra: Dict[str, List[str]]
) -> Dict[str, List[str]]:
    merged: Dict[str, List[str]] = {k: list(v) for k, v in primary.items()}
    for ticker, names in extra.items():
        existing = merged.setdefault(ticker, [])
        for n in names:
            if n not in existing:
                existing.append(n)
    return merged


SECTOR_CACHE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sectors_cache.json")

# ---------------------------------------------------------------------------
# Bảng ngành dự phòng (~85 mã) khi KHÔNG có mạng / vnstock lỗi. Đây KHÔNG
# phải danh sách đầy đủ ~1600+ mã — nguồn đầy đủ & chính xác luôn là API
# phân ngành ICB thật của vnstock (get_ticker_sectors() bên dưới), lấy từ
# VCI (Vietcap) qua vnstock.Listing().symbols_by_industries(). Bảng này chỉ
# để app không "trắng ngành" khi mất mạng hoàn toàn.
# ---------------------------------------------------------------------------
SECTOR_FALLBACK: Dict[str, str] = {
    # Ngân hàng
    "ACB": "Ngân hàng", "BID": "Ngân hàng", "CTG": "Ngân hàng", "EIB": "Ngân hàng",
    "HDB": "Ngân hàng", "LPB": "Ngân hàng", "MBB": "Ngân hàng", "OCB": "Ngân hàng",
    "PGB": "Ngân hàng", "SHB": "Ngân hàng", "SSB": "Ngân hàng", "STB": "Ngân hàng",
    "TCB": "Ngân hàng", "TPB": "Ngân hàng", "VCB": "Ngân hàng", "VIB": "Ngân hàng",
    "VPB": "Ngân hàng",
    # Chứng khoán
    "SSI": "Chứng khoán", "VND": "Chứng khoán", "HCM": "Chứng khoán", "VCI": "Chứng khoán",
    "MBS": "Chứng khoán", "SHS": "Chứng khoán", "VIX": "Chứng khoán",
    # Bất động sản
    "VIC": "Bất động sản", "VHM": "Bất động sản", "VRE": "Bất động sản", "NVL": "Bất động sản",
    "DXG": "Bất động sản", "KDH": "Bất động sản", "NLG": "Bất động sản", "PDR": "Bất động sản",
    "DIG": "Bất động sản", "KBC": "Bất động sản", "IDC": "Bất động sản", "HDG": "Bất động sản",
    "CII": "Bất động sản", "BCM": "Bất động sản",
    # Bán lẻ
    "MWG": "Bán lẻ", "PNJ": "Bán lẻ", "FRT": "Bán lẻ", "DGW": "Bán lẻ",
    # Thép
    "HPG": "Thép", "HSG": "Thép", "NKG": "Thép",
    # Dầu khí
    "GAS": "Dầu khí", "PLX": "Dầu khí", "PVD": "Dầu khí", "PVT": "Dầu khí",
    "PVS": "Dầu khí", "BSR": "Dầu khí",
    # Hoá chất
    "DGC": "Hoá chất", "DPM": "Hoá chất", "DCM": "Hoá chất",
    # Hàng không - Logistics
    "VJC": "Hàng không - Logistics", "HVN": "Hàng không - Logistics",
    "GMD": "Hàng không - Logistics", "ACV": "Hàng không - Logistics",
    # Thực phẩm - Đồ uống
    "VNM": "Thực phẩm - Đồ uống", "SAB": "Thực phẩm - Đồ uống", "BHN": "Thực phẩm - Đồ uống",
    "MSN": "Thực phẩm - Đồ uống", "QNS": "Thực phẩm - Đồ uống", "VHC": "Thực phẩm - Đồ uống",
    "ANV": "Thực phẩm - Đồ uống",
    # Xây dựng - VLXD
    "VGC": "Xây dựng - VLXD", "VCG": "Xây dựng - VLXD", "BMP": "Xây dựng - VLXD",
    "HTN": "Xây dựng - VLXD", "PTB": "Xây dựng - VLXD",
    # Công nghệ - Viễn thông
    "FPT": "Công nghệ - Viễn thông", "FOX": "Công nghệ - Viễn thông",
    "VGI": "Công nghệ - Viễn thông", "VTP": "Công nghệ - Viễn thông",
    # Điện - Tiện ích
    "POW": "Điện - Tiện ích", "NT2": "Điện - Tiện ích", "GEG": "Điện - Tiện ích",
    "BWE": "Điện - Tiện ích", "PC1": "Điện - Tiện ích",
    # Bảo hiểm
    "BVH": "Bảo hiểm",
    # Cao su - Nông nghiệp
    "GVR": "Cao su - Nông nghiệp", "HAG": "Cao su - Nông nghiệp",
    "HNG": "Cao su - Nông nghiệp", "DBC": "Cao su - Nông nghiệp",
}


def _load_sector_cache() -> Optional[dict]:
    if not os.path.exists(SECTOR_CACHE_PATH):
        return None
    try:
        with open(SECTOR_CACHE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if time.time() - data.get("_fetched_at", 0) > CACHE_TTL_SECONDS:
            return None
        return data.get("sectors")
    except Exception:
        return None


def _save_sector_cache(sectors: Dict[str, dict]) -> None:
    try:
        with open(SECTOR_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump({"_fetched_at": time.time(), "sectors": sectors}, f, ensure_ascii=False)
    except Exception:
        pass


def _fetch_sectors_from_vnstock() -> Optional[Dict[str, dict]]:
    """Lấy phân ngành ICB đầy đủ (~1600+ mã) từ vnstock (nguồn VCI/Vietcap).

    API xác nhận tồn tại trong vnstock >= 3.x:
        from vnstock import Listing
        Listing().symbols_by_industries()
    trả về DataFrame với các cột symbol, icb_name1..4 (Ngành cấp 1 rộng nhất
    -> cấp 4 chi tiết nhất theo chuẩn ICB), icb_code1..4, organ_name...

    Trả về dict {ticker: {"sector": <icb_name3, fallback 2/4/1>,
                            "sector_l1": ..., "sector_l4": ..., "organ_name": ...}}
    hoặc None nếu lỗi (không có mạng, đổi API, chưa cài vnstock...).
    """
    try:
        from vnstock import Listing  # vnstock >= 3.x

        listing = Listing()
        df = listing.symbols_by_industries()

        cols = {c.lower(): c for c in df.columns}
        ticker_col = cols.get("symbol") or cols.get("ticker")
        if ticker_col is None:
            return None

        # icb_name3 (Sector - mức trung bình, gần với "Ngân hàng", "Bán lẻ",
        # "Chứng khoán"...) là lựa chọn mặc định hợp lý nhất cho việc gom
        # nhóm hiển thị; nếu thiếu thì lùi dần về các cấp còn lại.
        level_priority = ["icb_name3", "icb_name2", "icb_name4", "icb_name1"]
        level_cols = [cols[lv] for lv in level_priority if lv in cols]
        if not level_cols:
            return None

        organ_col = cols.get("organ_name") or cols.get("organname")

        result: Dict[str, dict] = {}
        for _, row in df.iterrows():
            t = str(row[ticker_col]).strip().upper()
            if not t or len(t) > 4 or not t.isalpha():
                continue
            sector = ""
            for lc in level_cols:
                val = row.get(lc)
                if val and isinstance(val, str) and val.strip():
                    sector = val.strip()
                    break
            entry = {"sector": sector or "Chưa phân loại"}
            for lv in ("icb_name1", "icb_name2", "icb_name3", "icb_name4"):
                if lv in cols:
                    v = row.get(cols[lv])
                    if v and isinstance(v, str):
                        entry[lv] = v.strip()
            if organ_col:
                v = row.get(organ_col)
                if v and isinstance(v, str) and v.strip():
                    entry["organ_name"] = v.strip()
            result[t] = entry
        return result or None
    except Exception:
        return None


def get_ticker_sectors(force_refresh: bool = False) -> Dict[str, dict]:
    """Trả về dict {MÃ: {"sector": <tên ngành>, ...}} đầy đủ nhất có thể.

    Ưu tiên: cache 24h -> gọi vnstock trực tiếp -> cache cũ (hết hạn nhưng
    vẫn còn) -> SECTOR_FALLBACK (~85 mã) khi mọi cách trên đều thất bại.
    """
    if not force_refresh:
        cached = _load_sector_cache()
        if cached:
            return cached

    fresh = _fetch_sectors_from_vnstock()
    if fresh:
        _save_sector_cache(fresh)
        return fresh

    try:
        with open(SECTOR_CACHE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if data.get("sectors"):
            return data["sectors"]
    except Exception:
        pass

    return {t: {"sector": s} for t, s in SECTOR_FALLBACK.items()}


def get_blacklist() -> Set[str]:
    return set(DEFAULT_BLACKLIST)
