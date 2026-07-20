"""
ticker_detector.py
-------------------
Nhận diện mã chứng khoán (3-4 chữ cái, HOSE/HNX/UPCOM) được nhắc đến
trong một bài báo, dựa trên: tiêu đề, mô tả (nếu có) và URL bài viết.

Nguyên tắc để tránh nhận nhầm (đây là điểm khác biệt so với bản cũ, vốn
không hề kiểm tra tính hợp lệ của token — dẫn tới việc mọi cụm 3 chữ hoa
kiểu "TP.HCM", "GDP", "CEO"... đều có thể bị coi là mã CK sai lệch):

1. CHỈ xét các token viết hoa liên tục 3-4 ký tự, đứng độc lập (word
   boundary) — không cắt giữa từ, không dính vào chữ thường.
2. Token đó PHẢI nằm trong "vũ trụ mã CK" thật (whitelist lấy từ
   ticker_universe.get_ticker_universe()) — không tự suy diễn.
3. Token đó KHÔNG được nằm trong blacklist các từ viết tắt phổ biến dễ
   trùng (GDP, CPI, FDI, IMF, CEO*, ATM...) — *trừ phi bản thân nó thật
   sự là một mã CK hợp lệ và không nằm trong blacklist mặc định.
4. Ưu tiên các dấu hiệu ngữ cảnh mạnh làm tăng độ tin cậy (không bắt
   buộc, chỉ dùng để xếp hạng/nổi bật): đứng ngay sau "mã", "cổ phiếu",
   "CTCP", trong ngoặc đơn "(XXX)", hoặc xuất hiện trong slug URL dạng
   .../hose/xxx-ten-cong-ty.chn hay /XXX/tin-tuc.htm.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Set
from urllib.parse import urlparse

# Token ứng viên: đúng 3 hoặc 4 chữ cái IN HOA liên tiếp, có ranh giới từ
# rõ ràng ở hai đầu (không phải một phần của từ dài hơn / có dấu).
_CANDIDATE_RE = re.compile(r"(?<![A-Za-zÀ-ỹ0-9])[A-Z]{3,4}(?![A-Za-zÀ-ỹ0-9])")

# Các mẫu ngữ cảnh cho biết token phía sau/trong ngoặc nhiều khả năng là
# mã CK thật (dùng để tính "confidence", không dùng để lọc cứng).
_STRONG_CONTEXT_RE = re.compile(
    r"(?:mã\s+(?:CK|cổ phiếu)?\s*[:\-]?\s*|cổ phiếu\s+|CTCP\s+.*?\(|\()\s*([A-Z]{3,4})\b",
    re.UNICODE,
)

# Regex bắt mã từ slug URL kiểu cafef.vn/du-lieu/hose/hpg-... hoặc
# finance.vietstock.vn/HPG/tin-tuc.htm
_URL_TICKER_RE = re.compile(r"/(?:hose|hnx|upcom)/([a-zA-Z]{3,4})-", re.IGNORECASE)
_URL_TICKER_RE2 = re.compile(r"/([A-Za-z]{3,4})/(?:tin-tuc|tai-tai-lieu)", re.IGNORECASE)

# Một số cụm địa danh/tổ chức viết tắt rất phổ biến trong báo chí VN mà
# 3 chữ cuối vô tình trùng với một mã CK có thật (VD: "TP.HCM" trùng mã
# HCM của Chứng khoán TP.HCM - HSC). Nếu token đứng NGAY sau các tiền tố
# này thì loại trừ, vì xác suất đây là địa danh cao hơn nhiều so với mã CK.
_LOCATION_PREFIX_RE = re.compile(r"(?:TP\.?|T\.P\.?)\s*$", re.IGNORECASE)


@dataclass
class DetectedTicker:
    ticker: str
    exchange: str
    confidence: str = "normal"  # "high" nếu khớp ngữ cảnh mạnh hoặc từ URL


@dataclass
class TickerMatchResult:
    tickers: List[DetectedTicker] = field(default_factory=list)

    @property
    def codes(self) -> List[str]:
        return [t.ticker for t in self.tickers]

    def __bool__(self) -> bool:
        return bool(self.tickers)


class TickerDetector:
    """Bọc whitelist + blacklist lại thành một detector tái sử dụng được,
    tránh phải truyền dict đi khắp nơi và cho phép nạp lại khi cache mã CK
    được refresh (gọi `refresh()`).
    """

    def __init__(self, universe: Dict[str, str], blacklist: Set[str] | None = None):
        self._universe = {k.upper(): v for k, v in universe.items()}
        self._blacklist = {b.upper() for b in (blacklist or set())}

    def refresh(self, universe: Dict[str, str], blacklist: Set[str] | None = None) -> None:
        self._universe = {k.upper(): v for k, v in universe.items()}
        if blacklist is not None:
            self._blacklist = {b.upper() for b in blacklist}

    def _is_valid_ticker(self, token: str) -> bool:
        token = token.upper()
        return token in self._universe and token not in self._blacklist

    @staticmethod
    def _preceded_by_location_prefix(text: str, match_start: int) -> bool:
        """True nếu ngay trước token là tiền tố kiểu 'TP.' / 'Tp.'
        (VD: 'TP.HCM') -> nên loại trừ vì đây là địa danh, không phải mã CK."""
        prefix = text[max(0, match_start - 6):match_start]
        return bool(_LOCATION_PREFIX_RE.search(prefix))

    def detect(self, title: str, description: str = "", link: str = "") -> TickerMatchResult:
        found: Dict[str, DetectedTicker] = {}

        # 1) Ngữ cảnh mạnh trước (title + description), gán confidence cao
        text_for_context = f"{title}\n{description}"
        for m in _STRONG_CONTEXT_RE.finditer(text_for_context):
            token = m.group(1).upper()
            if self._is_valid_ticker(token) and token not in found:
                found[token] = DetectedTicker(token, self._universe[token], confidence="high")

        # 2) Toàn bộ token ứng viên trong tiêu đề (nguồn tin cậy nhất vì
        #    tiêu đề luôn liên quan trực tiếp tới nội dung chính bài báo)
        for m in _CANDIDATE_RE.finditer(title):
            token = m.group(0).upper()
            if self._preceded_by_location_prefix(title, m.start()):
                continue
            if self._is_valid_ticker(token) and token not in found:
                found[token] = DetectedTicker(token, self._universe[token], confidence="normal")

        # 3) Token ứng viên trong mô tả/tóm tắt (độ tin cậy thấp hơn một
        #    chút vì mô tả có thể nhắc tới mã liên quan chứ không phải mã
        #    chính của bài, nhưng vẫn hữu ích để không bỏ sót)
        if description:
            for m in _CANDIDATE_RE.finditer(description):
                token = m.group(0).upper()
                if self._preceded_by_location_prefix(description, m.start()):
                    continue
                if self._is_valid_ticker(token) and token not in found:
                    found[token] = DetectedTicker(token, self._universe[token], confidence="normal")

        # 4) Trích từ slug URL (rất đáng tin vì đây là cách CafeF/Vietstock
        #    tự gắn mã cho bài viết)
        if link:
            path = urlparse(link).path
            for rx in (_URL_TICKER_RE, _URL_TICKER_RE2):
                m = rx.search(path)
                if m:
                    token = m.group(1).upper()
                    if self._is_valid_ticker(token):
                        found[token] = DetectedTicker(token, self._universe[token], confidence="high")

        return TickerMatchResult(tickers=list(found.values()))
