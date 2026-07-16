import streamlit as st

# 1. Đóng gói toàn bộ nội dung của bạn vào một biến văn bản
HUONG_DAN_CONTENT = """# Nguồn tin tức chứng khoán VN — URL & cách filter

## Mục lục
1. CafeF
2. Vietstock
3. VietnamBiz
4. VSA (Hiệp hội Thép)
5. Báo chính thống
6. Trang DN chính thức

---

### 1. CafeF
Dùng cho: Tin tức công ty + thị trường (nhanh nhất, phong phú nhất)
- Trang cổ phiếu: `cafef.vn/du-lieu/hose/[mã]-ten-cong-ty.chn`
- Tin tức công ty: `cafef.vn/[tên-dn]-[mã].chn (tag)`
- Lịch cổ tức: `cafef.vn/lich-chot-quyen-co-tuc-...`

💡 **Tips:**
- Tốc độ cập nhật nhanh nhất VN (15-30 phút sau sự kiện).
- Có nhiều góc nhìn (phân tích kỹ thuật + cơ bản + tin vỉa).
- Search query: `"[tên DN] [chủ đề] tháng [m] năm [y] site:cafef.vn"`

---

### 2. Vietstock
Dùng cho: Tin tức + công bố thông tin chính thức
- Trang cổ phiếu: `finance.vietstock.vn/[MÃ]-ten-cong-ty.htm`
- Tin tức: `finance.vietstock.vn/[MÃ]/tin-tuc.htm`
- Báo cáo phân tích PDF: `finance.vietstock.vn/[MÃ]/tai-tai-lieu.htm`

💡 **Tips:**
- Tab "Tin tức" filter theo mã CP — chính xác.
- PDF báo cáo công ty CK (BSC, VCBS, SHS...) — giá trị cao cho phân tích.

---

### 3. VietnamBiz
Dùng cho: Tin ngành + dữ liệu vĩ mô
- URL: `vietnambiz.vn`

💡 **Tips:**
- Tin tức ngành thép/dầu khí/BĐS cập nhật nhanh.
- Thường có số liệu định lượng (giá, sản lượng, tỷ lệ).

---

### 4. VSA — Hiệp hội Thép VN
Dùng cho (chỉ ngành thép): Giá HRC, sản lượng, xuất nhập khẩu
- URL: `vsa.com.vn`

💡 **Tips:**
- Giá HRC bình quân hàng tháng — benchmark chính.
- Sản lượng thép cả nước theo tháng/năm.

---

### 5. Báo chính thống
| Báo | URL | Đặc thù |
|---|---|---|
| VnExpress | vnexpress.net | Tin KQKD nhanh, góc nhìn tổng quan |
| Tuổi Trẻ | tuoitre.vn | Tin giao dịch khối ngoại, block trade |
| Thời báo Tài chính VN | thoibaotaichinhvietnam.vn | Tin khối ngoại, vĩ mô |
| Thị trường Tài chính Tiền tệ | thitruongtaichinhtiente.vn | Tin sản lượng, giao dịch nội bộ CĐ |
| Báo Mới | baomoi.com | Aggregate tổng hợp |
| Tạp chí Công Thương | tapchicongthuong.vn | Tin dự án, sản xuất |

---

### 6. Trang DN chính thức
Dùng cho: Thông tin chính thức 100% (công bố thông tin, BCTC)
- Trang tin tức DN: `[domain-dn]/tin-tuc`
- Trang QHCD: `[domain-dn]/quan-he-co-dong`
- Thông báo HOSE: `hose.com.vn/#/home/disclosure/[mã]`
*(Ví dụ: HPG → hoaphat.com.vn/tin-tuc, hoaphat.com.vn/quan-he-co-dong)*

---

### 🎯 Tóm tắt ưu tiên theo loại tin
| Loại tin cần | Nguồn ưu tiên #1 | Nguồn phụ |
|---|---|---|
| KQKD quý/năm | VnExpress + Trang DN | CafeF |
| Sản lượng/kinh doanh | Thị trường Tài chính | CafeF |
| Dự án/công suất mới | Tạp chí Công Thương | VietnamBiz |
| Giá ngành (thép, dầu) | VSA + VietnamBiz | Asemconnect |
| Khối ngoại/block trade | Tuổi Trẻ + Thời báo Tài chính | CafeF |
| Cổ tức/phát hành CP | CafeF + VSD | HOSE Disclosure |
| Vĩ mô (lãi suất, CPI) | VnExpress | Thời báo Tài chính |
"""

# --- GIAO DIỆN STREAMLIT ---
st.subheader("📚 Cẩm nang Nguồn dữ liệu & Cách lấy tin")

# Hiển thị cho người dùng đọc lướt trên web
with st.expander("👁️ Bấm để xem trực tiếp Cẩm nang", expanded=False):
    st.markdown(HUONG_DAN_CONTENT)

# Cung cấp nút Download
st.download_button(
    label="📥 Tải về Bí kíp Nguồn tin (.md)",
    data=HUONG_DAN_CONTENT,
    file_name="cam_nang_nguon_tin_CK_VN.md",
    mime="text/markdown"
)
