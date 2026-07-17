import streamlit as st
import feedparser
import time
import calendar
import io
import csv
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import re

# ══════════════════════════════════════════════════════════════════════════════
# 1500+ MÃ CK 3 SÀN — dùng để detect trong tiêu đề tin tức
# ══════════════════════════════════════════════════════════════════════════════
# Danh sách đầy đủ — bạn có thể thêm mã mới vào đây
ALL_TICKERS = set("""
A32 AAA AAM AAT ABB ABC ABR ABS ABT ACB ACC ACG ACL ACM ACS ACT ADC ADG ADP
ADS AEF AFX AGF AGG AGM AGP AGR AHA AHP AIC AIF AKC ALT ALV AMC AMD AME AMI
AMN AMP AMV ANT AOG APC APG APH APS APT ARG ART ASA ASG ASM ASP AST ATB ATC
ATG ATN ATS AVF AVM AVS AXB AXV BAB BAF BAX BBC BBH BBS BCG BCM BDB BDG BDT
BDW BFC BFI BHC BHN BHT BIC BID BKC BKG BKH BLF BLI BLN BLW BMC BMF BMG BMI
BMJ BMN BMP BMT BNA BNW BOT BPC BPH BPT BRC BRS BSB BSC BSI BSP BSR BST BT1
BTB BTC BTD BTE BTG BTH BTL BTN BTP BTS BTT BTW BTV BVB BVG BVH BVL BVN BVS
BWA BWE C21 C32 C47 C69 CAB CAD CAG CAP CAT CAV CBI CBT CCA CCB CCC CCL CCM
CCN CCP CCR CCS CCT CCY CDA CDB CDC CDH CDN CDO CDP CDR CDS CDT CDW CEE CEG
CEO CFC CFM CFV CGP CGS CHC CHN CI5 CID CIG CII CIP CJC CKD CKG CLB CLC CLH
CLM CLN CLR CLS CMC CMG CMI CMN CMT CNA CNC CNT COG COM CPA CPC CPH CPI CPW
CRC CRE CRB CS4 CSC CSM CST CTB CTC CTD CTF CTG CTI CTN CTP CTR CTS CTT CTX
CVN CVP CVT CX8 CXH CXL D11 D2D DAD DAE DAG DAH DAP DAT DBC DBT DC2 DC4 DC9
DCC DCG DCH DCI DCL DCM DCS DCT DCW DDB DDG DDV DDM DDN DDS DEL DHB DHC DHG
DHM DHN DHT DIC DID DIH DIN DKC DKP DKS DL1 DLD DLG DLR DLS DM7 DMC DNC DNA
DNH DNM DNP DPG DPM DPP DPR DPS DPT DQC DQN DQV DRC DRG DRI DRL DRR DRT DRH
DRV DSC DSN DST DTC DTE DTG DTH DTI DTK DTL DTN DTP DTT DTV DTX DUS DXG DXL
DXP DXS DXV EBA EBS ECI EFT EGL EIB ELC ELT EMG EVF EVG EVN ETC ETL ETV FBA
FBC FBI FBT FCC FCM FCN FCS FDC FDP FGL FHH FIR FIT FIE FLC FLN FMC FNF FPC
FPS FPT FRD FRT FTI FTV GAS GAW GCB GDT GDW GEE GEG GEX GFC GFF GGG GHC GIC
GIL GKM GLT GMC GMD GMT GNT GPC GPM GPN GPP GPS GRK GSM GTN GTS GTT GVR HAD
HAF HAG HAH HAM HAP HAR HAS HAT HAV HBC HBO HBS HCC HCL HCM HCS HDC HDG HDP
HEL HFT HGM HHC HHN HHR HHS HHV HID HIG HII HIM HIO HJS HKB HLA HLD HLG HLY
HMC HNA HNB HNM HNP HNR HNS HNX HPD HPG HPT HPW HQC HRC HRS HRT HSG HSL HSM
HSN HST HTC HTD HTG HTI HTL HTM HTN HTP HTR HTS HTT HTV HUB HUD HUI HUM HUT
HVG HVN HVT HWS ICF ICG ICI IFP IHL IJC ILB IME IMP IMT INC INN INT IPA IRC
IRB ITA ITD ITQ ITL ITS JVC KBC KBT KCB KDF KDH KDM KDS KGM KHB KHA KHP KHW
KII KIL KIP KKC KLF KMR KMT KNS KPF KSB KSF KSH KSK KSQ KST KTC KTS KTT KVF
LAF LAS LAX LBM LBE LCG LCD LCI LCM LCW LDG LDX LEC LHC LIC LIG LIN LIX LKW
LLM LM3 LM8 LMC LNC LNH LPB LPI LPT LRC LRG LSG LSS LTG LUT LWS MBB MBN MBR
MBS MCC MCF MCG MCH MCI MCM MCP MCS MCW MDC MDG MDN MDS MDX MEF MED MEL MHB
MHC MHD MHN MHP MHT MKP MKV MMB MMC MMH MMS MMT MPT MPC MPT MQN MRC MRM MRS
MSB MSG MSH MSI MSN MSP MSR MST MTG MTH MTS MTV MXV NAB NAF NAG NAV NAW NCC
NCT NDF NDN NDP NDW NEG NHH NHI NHL NHN NHP NHT NHW NID NIN NIP NKC NKG NKM
NLG NLS NMG NMR NMP NMT NNC NNS NOI NPM NPS NQN NRC NSC NSH NSN NTA NTC NTH
NTI NTL NTP NTR NTS NTT NTV OGC OIL OJC OMG ONE ONW OPC ORS PAC PAI PAT PAV
PAX PBC PBP PCF PCG PCH PCI PCM PCN PCS PDB PDN PDO PDR PDT PEB PEG PET PFC
PFN PGC PGD PGI PGN PGS PGT PGV PGZ PHH PHR PIA PIV PJC PJT PKC PKN PKT PLA
PLI PLX PMP PNE PNG PNJ PNP PNT PON POT PPC PPP PPR PPS PPT PRA PRE PRP PRT
PSC PSG PSH PSI PSN PSW PTC PTG PTH PTI PTK PTL PTN PTP PTV PTY PUC PVA PVB
PVC PVD PVE PVG PVI PVL PVM PVN PVO PVP PVR PVS PVT PVU PVX PXA PXI PXL PXM
PXP PXS PYN QBC QCG QHD QHL QHS QNC QNS QPH QPR QSP QST QTC QTP QTS RBC REE
RFC RGC RHC RIC RKC RLC RLF RMF RNI RNP ROS RPC RPT RSC SAB SAC SAF SAM SAP
SAV SBA SBB SBC SBD SBF SBG SBL SBM SBS SBT SBV SCC SCI SCJ SCL SCN SCV SCY
SDA SDC SDF SDG SDH SDN SDP SDT SDU SDW SEC SEP SER SFC SFF SFG SFI SFN SGC
SGD SGH SGN SGP SGR SGS SGT SHB SHE SHG SHI SHL SHN SHR SHS SHX SIC SII SIL
SIM SIT SKG SLN SMC SMN SMT SNA SNC SNG SNN SNS SOB SOD SOF SOI SOL SOM SOP
SOS SPB SPD SPH SPI SPM SPN SPP SPR SPS SPT SRC SRF SRI SRS SRT SSC SSF SSG
SSH SSI SSL SSN SSP SST STC STG STH STL STN STP STS STT STV STX SUA SUB SVC
SVD SVN SVT SVX SWC SYC SZB SZC SZE SZL SZN SZR SZV T10 T19 T90 TAC TAG TAL
TAP TAR TAS TAW TBC TBD TBG TBH TBI TBN TBR TBT TBW TCB TCH TCI TCJ TCL TCM
TCO TCR TCS TCT TCX TDC TDF TDG TDM TDN TDP TDT TDW TEB TGC TGN TGP TGR TGS
TGW THB THD THG THI THL THM THN THP THR THS THT THV THW TID TIG TIH TIN TIP
TIS TIU TIW TJS TKC TKG TKU TKW TLA TLG TLH TLN TLT TLX TMA TMB TMC TMT TNA
TNC TND TNH TNI TNM TNN TNP TNS TNT TNW TOC TOT TPC TPB TPH TPI TPN TPP TPS
TPW TRA TRC TRB TRC TRF TRI TRM TRS TRT TRV TSB TSC TST TTC TTD TTF TTH TTL
TTN TTP TTS TTW TUA TUC TVC TVB TVM TVN TVP TVS TVT TVW TWA TXM TXN UDC UDJ
UDL UEM UIG V11 V12 V21 V60 VAF VAT VBC VBD VBH VBP VBQ VBR VBS VBT VBV VCC
VCI VCM VCR VCS VCT VDB VDC VDP VDS VDT VDX VEA VEC VEF VEL VEX VFC VFR VFS
VFT VGC VGF VGI VGP VGR VGS VGT VHC VHE VHF VHG VHH VHM VHL VHN VHP VHS VHT
VMD VMI VMJ VMK VML VMM VMP VMR VMS VMT VMV VNA VNB VNC VND VNE VNG VNH VNI
VNL VNM VNN VNP VNR VNS VNT VNX VPB VPC VPD VPG VPI VPK VPL VPN VPP VPQ VPR
VPS VPX VRC VRE VRG VRP VRS VRT VRX VSB VSC VSD VSE VSF VSH VSI VSK VSL VSM
VSN VSP VSR VSS VST VSX VTA VTB VTC VTD VTE VTF VTG VTH VTI VTJ VTK VTL VTM
VTN VTP VTQ VTR VTS VTT VTV VTX VTZ VUC VUI VXB WCS WSB YBC YBM YEG
""".split())

# ══════════════════════════════════════════════════════════════════════════════
# CẤU HÌNH THỜI GIAN LỌC TIN
# ══════════════════════════════════════════════════════════════════════════════
MAX_AGE_DAYS = 2  # chỉ giữ tin trong vòng 2 ngày gần nhất

# ══════════════════════════════════════════════════════════════════════════════
# RSS — Tất cả chuyên mục có thể chứa tin DN niêm yết
# ══════════════════════════════════════════════════════════════════════════════
RSS_FEEDS = [
    # CafeF
    ("CafeF", "https://cafef.vn/chung-khoan.rss"),
    ("CafeF", "https://cafef.vn/doanh-nghiep.rss"),
    ("CafeF", "https://cafef.vn/tai-chinh-ngan-hang.rss"),
    ("CafeF", "https://cafef.vn/vi-mo-dau-tu.rss"),
    ("CafeF", "https://cafef.vn/bat-dong-san.rss"),
    ("CafeF", "https://cafef.vn/thi-truong.rss"),
    # Vietstock
    ("Vietstock", "https://vietstock.vn/rss/chung-khoan.rss"),
    ("Vietstock", "https://vietstock.vn/rss/doanh-nghiep.rss"),
    ("Vietstock", "https://vietstock.vn/rss/tai-chinh.rss"),
    ("Vietstock", "https://vietstock.vn/rss/bat-dong-san.rss"),
    # Tinnhanhchungkhoan
    ("TNCK", "https://www.tinnhanhchungkhoan.vn/rss/chung-khoan-1.rss"),
    ("TNCK", "https://www.tinnhanhchungkhoan.vn/rss/doanh-nghiep-2.rss"),
    ("TNCK", "https://www.tinnhanhchungkhoan.vn/rss/ngan-hang-3.rss"),
    # VnEconomy
    ("VnEconomy", "https://vneconomy.vn/rss/chung-khoan.rss"),
    ("VnEconomy", "https://vneconomy.vn/rss/doanh-nghiep.rss"),
    ("VnEconomy", "https://vneconomy.vn/rss/tai-chinh.rss"),
    # VietnamBiz
    ("VietnamBiz", "https://vietnambiz.vn/chung-khoan.rss"),
    ("VietnamBiz", "https://vietnambiz.vn/doanh-nghiep.rss"),
    ("VietnamBiz", "https://vietnambiz.vn/ngan-hang.rss"),
    # VnExpress
    ("VnExpress", "https://vnexpress.net/rss/kinh-doanh/chung-khoan.rss"),
    ("VnExpress", "https://vnexpress.net/rss/kinh-doanh.rss"),
    # Thế giới / quốc tế — CHỈ dùng nguồn tài chính quốc tế, bỏ VnExpress the-gioi (lẫn bóng đá/xã hội)
    ("CafeF", "https://cafef.vn/tai-chinh-quoc-te.rss"),
    ("Vietstock", "https://vietstock.vn/rss/the-gioi.rss"),
    ("VnEconomy", "https://vneconomy.vn/rss/the-gioi.rss"),
]

SECTION_TINTUC       = "TIN TỨC"
SECTION_DOANHNGHIEP  = "DOANH NGHIỆP"
SECTION_THEGIOI      = "THẾ GIỚI"

# ══════════════════════════════════════════════════════════════════════════════
# NHẬN DIỆN TIN THẾ GIỚI (ngoài Việt Nam)
# ══════════════════════════════════════════════════════════════════════════════
# Cụm từ/tên nước ghép — an toàn để so khớp dạng chuỗi con (không nhầm với từ tiếng Việt khác)
_WORLD_LOOSE_PHRASES = [
    "trung quốc", "nhật bản", "hàn quốc", "triều tiên", "ukraine", "ukraina",
    "ấn độ", "indonesia", "thái lan", "singapore", "malaysia", "philippines",
    "campuchia", "myanmar", "canada", "brazil", "mexico", "argentina",
    "ả rập", "uae", "dubai", "qatar", "thổ nhĩ kỳ", "israel", "iran", "iraq",
    "ai cập", "nam phi", "châu âu", "châu á", "châu phi", "eurozone",
    "wall street", "phố wall", "nasdaq", "dow jones", "s&p 500", "s&p500",
    "đài loan", "hong kong", "hồng kông", "kospi", "nikkei", "shanghai",
    "fed", "ecb", "opec", "imf", " wb ", "wto", "g7", "g20",
    "quốc tế", "toàn cầu", "thế giới", "nước ngoài",
]
# Tên nước ngắn/dễ nhầm — chỉ khớp khi viết hoa đúng như tên riêng trong tiêu đề gốc
_WORLD_STRICT_PAT = re.compile(r'\b(Mỹ|Nga|Đức|Pháp|Úc|Lào)\b')
# Các cụm tiếng Việt chứa "mỹ"/"đức"... nhưng KHÔNG phải tên nước (mỹ phẩm, thẩm mỹ, Mỹ Đình...)
_WORLD_FALSE_FRIENDS = re.compile(
    r'\b(thẩm|hoàn|tuyệt|duy)\s+mỹ\b|'
    r'\bmỹ\s+(phẩm|thuật|nghệ|vị|mãn|nhân|danh|tục|cảm|ý|đình|tho|hào|đức|xuyên|lồng|hạnh|hưng|quan|dung)\b|'
    r'\bđạo\s+đức\b|\bcông\s+đức\b|\bân\s+đức\b|\bphẩm\s+đức\b',
    re.IGNORECASE,
)

# ── Từ khóa phi tài chính — nếu có trong tiêu đề thì BỎ QUA (bóng đá, giải trí...) ──
_NON_FINANCE_KEYWORDS = [
    # Thể thao
    "bóng đá", "world cup", "euro ", "champions league", "premier league",
    "la liga", "serie a", "bundesliga", "cup ", " cúp ", "vô địch", "huy chương",
    "olympic", "seagames", "sea games", "asian games", "ngoại hạng anh",
    "câu lạc bộ", " clb ", "bàn thắng", "bàn thua", "thủ môn", "tiền đạo",
    "huấn luyện viên", "hlv ", "cầu thủ", "trọng tài", "penalty",
    "f1 ", "tennis", "golf ", "bơi lội", "điền kinh", "boxing", "võ",
    # Giải trí / văn hóa
    "phim ", "ca sĩ", "diễn viên", "hoa hậu", "sao ", "nghệ sĩ",
    "âm nhạc", "concert", "show ", "album", "mv ", "gameshow",
    # Chính trị thuần túy (không liên quan thị trường)
    "bầu cử", "nghị viện", "tổng thống", "thủ tướng", "ngoại giao",
    # Thiên tai / tai nạn (không liên quan thị trường)
    "động đất", "sóng thần", "lũ lụt", "cháy rừng", "tai nạn",
]

# ── Từ khóa tài chính quốc tế — nếu có thì GIỮ LẠI ──
_WORLD_FINANCE_KEYWORDS = [
    "kinh tế", "tài chính", "ngân hàng", "lãi suất", "lạm phát", "gdp",
    "chứng khoán", "cổ phiếu", "thị trường", "đầu tư", "quỹ", "trái phiếu",
    "tỷ giá", "ngoại tệ", "usd", "eur", "dầu", "vàng", "hàng hóa",
    "thương mại", "xuất khẩu", "nhập khẩu", "thuế quan", "tariff",
    "fed", "ecb", "imf", "world bank", "opec", "nasdaq", "dow jones",
    "s&p", "nikkei", "kospi", "shanghai", "hang seng",
    "wall street", "phố wall", "tăng trưởng", "suy thoái", "khủng hoảng",
    "doanh nghiệp", "công ty", "tập đoàn", "m&a", "ipo", "niêm yết",
    "cổ phần", "vốn", "doanh thu", "lợi nhuận",
]

def is_world_news(title: str) -> bool:
    """Tin liên quan ngoài Việt Nam (quốc gia/khu vực/tổ chức nước ngoài) -> tính là THẾ GIỚI."""
    working = _WORLD_FALSE_FRIENDS.sub(' ', title)
    t = f" {working.lower()} "
    if any(kw in t for kw in _WORLD_LOOSE_PHRASES):
        return True
    if _WORLD_STRICT_PAT.search(working):
        return True
    return False

def is_finance_relevant_world_news(title: str) -> bool:
    """
    Với tin THẾ GIỚI: kiểm tra thêm xem có liên quan tài chính/kinh tế không.
    Loại bỏ tin bóng đá, giải trí, thiên tai thuần túy.
    Logic: GIỮ nếu có từ tài chính, BỎ nếu chỉ có từ phi tài chính.
    """
    t = title.lower()
    # Nếu có từ khóa phi tài chính rõ ràng -> loại
    if any(kw in t for kw in _NON_FINANCE_KEYWORDS):
        return False
    # Nếu có từ khóa tài chính -> giữ
    if any(kw in t for kw in _WORLD_FINANCE_KEYWORDS):
        return True
    # Mặc định giữ lại (để không mất tin tài chính chưa liệt kê)
    return True

# ══════════════════════════════════════════════════════════════════════════════
# TÌM TICKER TRONG TIÊU ĐỀ
# ══════════════════════════════════════════════════════════════════════════════
_TICKER_PAT = re.compile(r'\b([A-Z0-9]{2,5})\b')
# Nhận diện nếu tiêu đề đã có sẵn dạng "XXX: ..." hoặc "XXX - ..." ở đầu câu
_LEADING_TICKER_PAT = re.compile(r'^\s*([A-Z0-9]{2,5})\s*[:\-–]\s*')

# ── Loại trừ ticker nhầm với địa danh / từ viết tắt phổ biến ──────────────
# Map: ticker → danh sách pattern (lowercase) trong tiêu đề gốc mà nếu match => KHÔNG phải ticker
_TICKER_FALSE_POSITIVE: dict[str, list[str]] = {
    # HCM = TP. Hồ Chí Minh (địa danh), KHÔNG phải Chứng khoán HCM (HSC)
    # Chỉ loại khi có prefix địa danh rõ ràng, KHÔNG loại khi đứng độc lập (dạng mã CK)
    "HCM": ["tp.hcm", "tp hcm", "tphcm", "thành phố hồ chí minh", "hồ chí minh",
            "tại hcm", "ở hcm", "về hcm", "đến hcm", "từ hcm",
            "thị trường hcm", "sở giao dịch hcm"],
    # HN = Hà Nội (địa danh)
    "HN":  ["hà nội", "tp hà nội", "tại hà nội", "ở hà nội", " hn ", "tại hn"],
    # DN = Doanh nghiệp (viết tắt phổ biến)
    "DN":  ["doanh nghiệp", " dn ", "các dn", "nhiều dn", "nhóm dn"],
    # BT = Bình Thuận / Bình Thạnh
    "BT":  ["bình thuận", "bình thạnh", "tỉnh bt"],
    # CT = Công ty (rất phổ biến)
    "CT":  [" ct ", "công ty", "các ct"],
    # NT = Nha Trang / Ninh Thuận
    "NT":  ["nha trang", "ninh thuận"],
    # ND = Nam Định
    "ND":  ["nam định"],
    # BD = Bình Dương
    "BD":  ["bình dương"],
    # LA = Long An
    "LA":  ["long an"],
    # AG = An Giang (có thể nhầm với mã AG)
    # AG là mã hợp lệ, nhưng cần cẩn thận khi đứng cạnh "an giang"
    "AG":  ["tỉnh an giang", "tại an giang"],
}

# Pattern phát hiện "TP.HCM", "TP HCM", "TPHCM" trong title đã upper
_TPHCM_PAT = re.compile(r'\bTP\.?HCM\b|T\.P\.HCM|TPHCM', re.IGNORECASE)

def _is_false_positive_ticker(ticker: str, title_original: str) -> bool:
    """
    Kiểm tra xem ticker có phải nhầm lẫn với địa danh/từ viết tắt không.
    title_original: tiêu đề gốc (chưa upper).
    """
    patterns = _TICKER_FALSE_POSITIVE.get(ticker)
    if not patterns:
        return False
    t_lower = title_original.lower()
    return any(p in t_lower for p in patterns)

def extract_tickers(title: str) -> list:
    """
    Tìm tất cả mã CK xuất hiện trong tiêu đề (viết hoa).
    Lọc false positive: HCM trong 'TP.HCM', DN trong 'doanh nghiệp', v.v.
    """
    found = []
    title_upper = title.upper()
    for m in _TICKER_PAT.finditer(title_upper):
        tk = m.group(1)
        if tk not in ALL_TICKERS:
            continue
        # Kiểm tra ngữ cảnh false positive
        if _is_false_positive_ticker(tk, title):
            continue
        found.append(tk)
    return list(dict.fromkeys(found))  # dedup, giữ thứ tự

def highlight_tickers(title: str) -> str:
    """Bôi đậm xanh tất cả ticker trong tiêu đề."""
    def replace(m):
        tk = m.group(1)
        if tk in ALL_TICKERS:
            return f'<b style="color:#0d3b8e">{tk}</b>'
        return m.group(0)
    return _TICKER_PAT.sub(replace, title)

def format_doanhnghiep_line(title: str, tickers: list) -> str:
    """
    Format tin DOANH NGHIỆP theo dạng 'MÃ: nội dung'.
    - Nếu tiêu đề đã có sẵn dạng 'XXX: ...' với XXX là mã hợp lệ -> giữ nguyên, chỉ bôi đậm mã.
    - Nếu chưa có -> gắn mã đầu tiên tìm được làm tiền tố 'MÃ: nội dung'.
    - Nếu không tìm được mã nào -> trả về tiêu đề bôi đậm mã (nếu có) như cũ.
    """
    m = _LEADING_TICKER_PAT.match(title)
    if m and m.group(1) in ALL_TICKERS:
        rest = title[m.end():].strip()
        return f'<b style="color:#0d3b8e">{m.group(1)}</b>: {highlight_tickers(rest)}'

    if tickers:
        primary = tickers[0]
        return f'<b style="color:#0d3b8e">{primary}</b>: {highlight_tickers(title)}'

    return highlight_tickers(title)

def classify(source: str, title: str):
    """
    Phân loại tin vào THẾ GIỚI, DOANH NGHIỆP, hay TIN TỨC (trong nước).
    Tin THẾ GIỚI phi tài chính (bóng đá, giải trí...) sẽ bị loại bỏ (trả None).
    """
    if is_world_news(title):
        if is_finance_relevant_world_news(title):
            return SECTION_THEGIOI
        return None  # Bỏ qua tin thế giới phi tài chính

    t = title.lower()
    dn_kw = [
        "kqkd","kết quả kinh doanh","doanh thu","lợi nhuận","cổ tức",
        "phát hành","đại hội cổ đông","đhcđ","niêm yết","hủy niêm yết",
        "bctc","báo cáo tài chính","esop","tăng vốn","mua lại cổ phiếu",
        "ban lãnh đạo","hội đồng quản trị","tổng giám đốc","ceo",
        "quý i","quý ii","quý iii","quý iv","6 tháng","9 tháng",
    ]
    if any(kw in t for kw in dn_kw) or bool(extract_tickers(title)):
        return SECTION_DOANHNGHIEP
    return SECTION_TINTUC

# ══════════════════════════════════════════════════════════════════════════════
# NGÀY GIỜ XUẤT BẢN
# ══════════════════════════════════════════════════════════════════════════════
def _parse_pubdate(entry):
    """Trả về datetime (UTC) từ entry RSS, hoặc None nếu không đọc được."""
    for field in ("published_parsed", "updated_parsed"):
        struct = getattr(entry, field, None)
        if struct:
            try:
                return datetime.utcfromtimestamp(calendar.timegm(struct))
            except Exception:
                continue
    return None

# ══════════════════════════════════════════════════════════════════════════════
# FETCH
# ══════════════════════════════════════════════════════════════════════════════
def _fetch_one(source_name: str, url: str):
    try:
        feed = feedparser.parse(url)
        out = []
        for e in feed.entries:
            title = getattr(e, "title", "").strip()
            link  = getattr(e, "link",  "").strip()
            if title and link:
                tickers = extract_tickers(title)
                cat = classify(source_name, title)
                if cat is None:
                    continue  # Bỏ qua tin phi tài chính (bóng đá, giải trí...)
                pub_dt = _parse_pubdate(e)
                out.append({
                    "title":   title,
                    "link":    link,
                    "source":  source_name,
                    "tickers": tickers,
                    "cat":     cat,
                    "pub_dt":  pub_dt,
                })
        return out
    except Exception:
        return []

@st.cache_data(ttl=900, show_spinner=False)
def fetch_all_news():
    all_items = []
    seen_titles = set()
    with ThreadPoolExecutor(max_workers=12) as ex:
        futures = {ex.submit(_fetch_one, src, url): (src, url) for src, url in RSS_FEEDS}
        for fut in as_completed(futures):
            for item in fut.result():
                if item["title"] not in seen_titles:
                    all_items.append(item)
                    seen_titles.add(item["title"])

    # ── Lọc tin không quá MAX_AGE_DAYS ngày ──
    # Tin không xác định được ngày xuất bản sẽ bị loại để đảm bảo đúng tiêu chí "không quá 2 ngày"
    cutoff = datetime.utcnow() - timedelta(days=MAX_AGE_DAYS)
    all_items = [it for it in all_items if it["pub_dt"] and it["pub_dt"] >= cutoff]

    # ── Sắp xếp mới nhất → cũ nhất ──
    all_items.sort(key=lambda it: it["pub_dt"], reverse=True)

    return all_items

# ══════════════════════════════════════════════════════════════════════════════
# RENDER
# ══════════════════════════════════════════════════════════════════════════════
STYLES = {
    SECTION_TINTUC:      {"hdr": "#D46B08", "bg": "#FFF7E6", "border": "#FFD591"},
    SECTION_DOANHNGHIEP: {"hdr": "#1D4ED8", "bg": "#EFF6FF", "border": "#BFDBFE"},
    SECTION_THEGIOI:     {"hdr": "#059669", "bg": "#ECFDF5", "border": "#A7F3D0"},
}

def _time_badge(pub_dt):
    if not pub_dt:
        return ""
    now = datetime.utcnow()
    delta = now - pub_dt
    if delta < timedelta(hours=24):
        label = pub_dt.strftime("%H:%M")
    else:
        label = pub_dt.strftime("%H:%M %d/%m")
    return (
        f'<span style="font-size:10px;color:#aaa;margin-left:5px">{label}</span>'
    )

def render_section(label: str, items: list, section_key: str = None):
    section_key = section_key or label
    s = STYLES[section_key]
    hdr, bg, bdr = s["hdr"], s["bg"], s["border"]
    count = len(items)
    is_dn = section_key == SECTION_DOANHNGHIEP

    st.markdown(
        f'<div style="background:{hdr};color:#fff;font-weight:700;font-size:13px;'
        f'padding:7px 14px;border-radius:5px 5px 0 0;letter-spacing:.5px">'
        f'{label} <span style="font-weight:400;font-size:11px;opacity:.85">({count} tin)</span></div>',
        unsafe_allow_html=True,
    )

    if not items:
        st.markdown(
            f'<div style="border:1px solid {bdr};border-top:none;background:{bg};'
            f'border-radius:0 0 5px 5px;padding:12px 14px;color:#888;font-size:13px">'
            f'Không có tin tức.</div>',
            unsafe_allow_html=True,
        )
        return

    rows = ""
    for item in items:
        if is_dn:
            display = format_doanhnghiep_line(item["title"], item["tickers"])
        else:
            display = highlight_tickers(item["title"])

        src_badge = (
            f'<span style="font-size:10px;color:#888;margin-left:5px;'
            f'background:#f0f0f0;padding:1px 5px;border-radius:3px">'
            f'{item["source"]}</span>'
        )
        time_badge = _time_badge(item.get("pub_dt"))
        rows += (
            f'<li style="margin-bottom:8px;line-height:1.45">'
            f'<a href="{item["link"]}" target="_blank" '
            f'style="text-decoration:none;color:#1a1a1a;font-size:13px">{display}</a>'
            f'{src_badge}{time_badge}</li>'
        )

    st.markdown(
        f'<div style="border:1px solid {bdr};border-top:none;background:{bg};'
        f'border-radius:0 0 5px 5px;padding:10px 14px 14px;max-height:520px;overflow-y:auto">'
        f'<ul style="margin:0;padding-left:18px">{rows}</ul></div>',
        unsafe_allow_html=True,
    )

# ══════════════════════════════════════════════════════════════════════════════
# XUẤT FILE CSV
# ══════════════════════════════════════════════════════════════════════════════
def build_csv(items: list) -> bytes:
    """Xuất danh sách tin ra CSV (mở tốt bằng Excel, có BOM UTF-8)."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Danh mục", "Mã CK", "Nội dung", "Nguồn", "Thời gian", "Link"])
    for it in items:
        tickers_str = ", ".join(it["tickers"])
        pub_dt = it.get("pub_dt")
        time_str = pub_dt.strftime("%Y-%m-%d %H:%M") if pub_dt else ""
        writer.writerow([it["cat"], tickers_str, it["title"], it["source"], time_str, it["link"]])
    # BOM để Excel nhận đúng UTF-8 tiếng Việt
    return ("\ufeff" + buf.getvalue()).encode("utf-8")

# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
def render_tab_news():
    # Header + refresh
    c1, c2 = st.columns([5, 1])
    with c1:
        st.markdown("#### 📰 Tin tức Chứng khoán · 3 Sàn")
    with c2:
        if st.button("🔄 Làm mới", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    # Load data
    with st.spinner("Đang tải tin từ 6 nguồn..."):
        all_news = fetch_all_news()

    total = len(all_news)
    all_tickers_found = sorted(set(tk for item in all_news for tk in item["tickers"]))

    st.caption(
        f"📊 {total} tin (trong {MAX_AGE_DAYS} ngày gần nhất) · {len(all_tickers_found)} mã được nhắc đến · "
        f"Nguồn: CafeF · Vietstock · TNCK · VnEconomy · VietnamBiz · VnExpress · "
        f"Cập nhật 15 phút/lần · Mới nhất → cũ nhất"
    )

    # ── SEARCH BOX ────────────────────────────────────────────────────────────
    search = st.text_input(
        "🔍 Tìm theo mã CK hoặc từ khóa",
        placeholder="VD: HPG   hoặc   cổ tức   hoặc   ngân hàng",
    ).strip().upper()

    # Filter
    if search:
        filtered = [
            item for item in all_news
            if search in item["title"].upper()
            or search in item["tickers"]
        ]
        label_extra = f' — kết quả cho "{search}"'
    else:
        filtered = all_news
        label_extra = ""

    tin_tuc      = [i for i in filtered if i["cat"] == SECTION_TINTUC]
    doanh_nghiep = [i for i in filtered if i["cat"] == SECTION_DOANHNGHIEP]
    the_gioi     = [i for i in filtered if i["cat"] == SECTION_THEGIOI]

    # ── NÚT TẢI VỀ ────────────────────────────────────────────────────────────
    dl_col1, dl_col2 = st.columns([5, 1])
    with dl_col2:
        st.download_button(
            "⬇️ Tải CSV",
            data=build_csv(filtered),
            file_name=f"tin_ck_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True,
            help="Tải về danh sách tin đang hiển thị (đã áp dụng bộ lọc tìm kiếm nếu có).",
        )

    # ── RENDER 3 CỘT ─────────────────────────────────────────────────────────
    if search and not filtered:
        st.warning(f'Không tìm thấy tin nào cho "{search}". Thử mã khác hoặc từ khóa khác.')
        return

    col1, col2, col3 = st.columns(3, gap="medium")
    with col1:
        render_section(SECTION_TINTUC + label_extra, tin_tuc, section_key=SECTION_TINTUC)
    with col2:
        render_section(SECTION_DOANHNGHIEP + label_extra, doanh_nghiep, section_key=SECTION_DOANHNGHIEP)
    with col3:
        render_section(SECTION_THEGIOI + label_extra, the_gioi, section_key=SECTION_THEGIOI)


    # ── TICKER CLOUD (khi chưa search) ───────────────────────────────────────
    if not search and all_tickers_found:
        st.markdown("---")
        st.markdown("**🏷️ Mã CK được nhắc đến hôm nay — click để lọc:**")
        cols = st.columns(10)
        for i, tk in enumerate(all_tickers_found[:50]):
            with cols[i % 10]:
                if st.button(tk, key=f"tk_{tk}", use_container_width=True):
                    st.session_state["_search_ticker"] = tk
                    st.rerun()

    # Xử lý click ticker cloud
    if "_search_ticker" in st.session_state:
        st.session_state["search_input"] = st.session_state.pop("_search_ticker")


if __name__ == "__main__":
    st.set_page_config(page_title="News CK 3 Sàn", layout="wide")
    render_tab_news()
