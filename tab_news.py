import streamlit as st
import feedparser
import time
import calendar
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
]

SECTION_TINTUC   = "TIN TỨC"
SECTION_DOANHNGHIEP = "DOANH NGHIỆP"

# ══════════════════════════════════════════════════════════════════════════════
# TÌM TICKER TRONG TIÊU ĐỀ
# ══════════════════════════════════════════════════════════════════════════════
_TICKER_PAT = re.compile(r'\b([A-Z0-9]{2,5})\b')
# Nhận diện nếu tiêu đề đã có sẵn dạng "XXX: ..." hoặc "XXX - ..." ở đầu câu
_LEADING_TICKER_PAT = re.compile(r'^\s*([A-Z0-9]{2,5})\s*[:\-–]\s*')

def extract_tickers(title: str) -> list:
    """Tìm tất cả mã CK xuất hiện trong tiêu đề (viết hoa)."""
    found = []
    for m in _TICKER_PAT.finditer(title.upper()):
        if m.group(1) in ALL_TICKERS:
            found.append(m.group(1))
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
    """Phân loại tin vào TIN TỨC hay DOANH NGHIỆP."""
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

def render_section(label: str, items: list):
    s = STYLES[label]
    hdr, bg, bdr = s["hdr"], s["bg"], s["border"]
    count = len(items)
    is_dn = label.startswith(SECTION_DOANHNGHIEP)

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

    # ── RENDER 2 CỘT ─────────────────────────────────────────────────────────
    if search and not filtered:
        st.warning(f'Không tìm thấy tin nào cho "{search}". Thử mã khác hoặc từ khóa khác.')
        return

    col1, col2 = st.columns(2, gap="medium")
    with col1:
        render_section(SECTION_TINTUC + label_extra, tin_tuc)
    with col2:
        render_section(SECTION_DOANHNGHIEP + label_extra, doanh_nghiep)

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
