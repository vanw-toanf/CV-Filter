import streamlit as st
import requests

BACKEND_URL = "http://127.0.0.1:8000"

st.set_page_config(layout="wide", page_title="Hệ thống Lọc CV (Gemini)")
st.title("🤖 Hệ thống Lọc CV Thông minh (Gemini Ver.)")

# --- Chức năng "Chọn ứng viên" ---
def select_candidate(candidate_id):
    try:
        response = requests.post(f"{BACKEND_URL}/mark_as_selected/", json={"candidate_id": candidate_id})
        if response.status_code == 200:
            st.toast(f"✅ Đã chọn ứng viên {candidate_id}!", icon="🎉")
        else:
            st.error(f"Lỗi khi chọn ứng viên: {response.text}")
    except requests.exceptions.ConnectionError:
        st.error("Lỗi kết nối backend.")

# --- Giao diện ---
col1, col2 = st.columns(2)

with col1:
    st.header("1. Tải lên CV")
    uploaded_file = st.file_uploader("Chọn file CV (PDF hoặc DOCX)", type=["pdf", "docx"])
    
    if uploaded_file:
        if st.button("Xử lý CV"):
            with st.spinner('Gemini đang đọc CV...'):
                files = {'file': (uploaded_file.name, uploaded_file, uploaded_file.type)}
                try:
                    response = requests.post(f"{BACKEND_URL}/upload_cv/", files=files)
                    if response.status_code == 201:
                        st.success(response.json().get("message"))
                    else:
                        st.error(f"Lỗi từ server: {response.json().get('detail')}")
                except requests.exceptions.ConnectionError:
                    st.error("Không thể kết nối đến backend. Hãy đảm bảo nó đang chạy.")

with col2:
    st.header("2. Tìm kiếm ứng viên")
    search_query = st.text_area("Nhập yêu cầu của bạn:", height=100, placeholder="Ví dụ: tìm data engineer có trên 2 năm kinh nghiệm, biết AWS và Python")

    if st.button("Tìm kiếm ứng viên"):
        if not search_query:
            st.warning("Vui lòng nhập yêu cầu.")
        else:
            with st.spinner('Đang tìm kiếm trong database...'):
                payload = {"text": search_query}
                try:
                    response = requests.post(f"{BACKEND_URL}/search_candidates/", json=payload)
                    if response.status_code == 200:
                        results = response.json().get("results", [])
                        st.session_state['search_results'] = results # Lưu kết quả vào session
                    else:
                        st.error(f"Lỗi từ server: {response.json().get('detail')}")
                except requests.exceptions.ConnectionError:
                    st.error("Lỗi kết nối backend.")

# Hiển thị kết quả tìm kiếm
if 'search_results' in st.session_state:
    results = st.session_state['search_results']
    st.subheader(f"🔍 Tìm thấy {len(results)} ứng viên phù hợp:")
    
    if not results:
        st.info("Không có ứng viên nào khớp với tiêu chí của bạn.")
    
    for candidate in results:
        candidate_id = candidate.get('id')
        with st.container(border=True):
            st.subheader(candidate.get('ho_ten', 'N/A'))
            
            c1, c2 = st.columns([3, 1])
            with c1:
                st.write(f"**Email:** `{candidate.get('email', 'N/A')}`")
                st.write(f"**Kinh nghiệm:** {candidate.get('so_nam_kinh_nghiem', 'N/A')} năm")
                skills = candidate.get('ky_nang', [])
                if skills:
                    st.markdown("**Kỹ năng:** " + " ".join(f"`{s}`" for s in skills))
            
            with c2:
                st.link_button("📄 Xem CV gốc", candidate.get('cv_url', '#'), use_container_width=True)
                if st.button("✅ Chọn ứng viên này", key=f"select_{candidate_id}", use_container_width=True):
                    select_candidate(candidate_id)
                    # Xóa ứng viên khỏi danh sách hiển thị ngay lập tức
                    st.session_state['search_results'] = [c for c in st.session_state['search_results'] if c.get('id') != candidate_id]
                    st.rerun() # Tải lại trang để cập nhật giao diện