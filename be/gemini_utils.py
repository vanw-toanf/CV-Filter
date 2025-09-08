import os
import google.generativeai as genai
from dotenv import load_dotenv
import json

load_dotenv()

# Cấu hình API key
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY not found in .env file")
genai.configure(api_key=api_key)

# Chọn model
model = genai.GenerativeModel('gemini-2.5-flash')

def extract_cv_info_with_gemini(cv_text: str) -> dict:
    """
    Bóc tách thông tin CV bằng Gemini.
    Nếu một trường thông tin không tìm thấy, giá trị của nó sẽ là None.
    """
    ALL_EXPECTED_FIELDS = [
        "ho_ten", "email", "so_dien_thoai", "dia_chi",
        "hoc_van", "kinh_nghiem", "ky_nang", "so_nam_kinh_nghiem"
    ]

    final_data = {field: None for field in ALL_EXPECTED_FIELDS}
    
    # Cập nhật prompt để yêu cầu Gemini bỏ qua trường nếu không tìm thấy
    prompt = f"""
    Bạn là một trợ lý nhân sự AI chuyên nghiệp. Hãy đọc nội dung CV sau và bóc tách các thông tin thành một cấu trúc JSON duy nhất.
    Nếu không tìm thấy thông tin cho một trường nào đó, hãy bỏ qua trường đó trong file JSON trả về.
    Chỉ trả về đối tượng JSON, không giải thích gì thêm.
    
    Các trường thông tin cần bóc tách:
    - ho_ten: Họ và tên đầy đủ.
    - email: Địa chỉ email.
    - so_dien_thoai: Số điện thoại.
    - dia_chi: Địa chỉ.
    - hoc_van: Một danh sách các mục học vấn (ten_truong, chuyen_nganh, thoi_gian).
    - kinh_nghiem: Một danh sách kinh nghiệm làm việc (ten_cong_ty, chuc_vu, thoi_gian, mo_ta).
    - ky_nang: Một danh sách các kỹ năng chính.
    - so_nam_kinh_nghiem: Ước tính tổng số năm kinh nghiệm làm việc (chỉ trả về một con số, ví dụ: 3.5). Nếu không có kinh nghiệm, trả về 0.

    Nội dung CV:
    ---
    {cv_text}
    ---
    """
    
    try:
        response = model.generate_content(prompt)
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "").strip()
        gemini_data = json.loads(cleaned_response)

        final_data.update(gemini_data)
        
        # Đảm bảo trường số năm kinh nghiệm luôn là một con số để dễ truy vấn
        if final_data.get("so_nam_kinh_nghiem") is None:
            final_data["so_nam_kinh_nghiem"] = 0.0

        return final_data
    except (json.JSONDecodeError, Exception) as e:
        print(f"Error parsing Gemini response or processing CV: {e}")
        return final_data


def analyze_search_query_with_gemini(search_text: str) -> dict:
    """Phân tích yêu cầu tìm kiếm của người dùng bằng Gemini."""
    prompt = f"""
    Phân tích yêu cầu tuyển dụng sau đây và trích xuất các tiêu chí thành một cấu trúc JSON.
    Chỉ trả về đối tượng JSON. Các trường có thể có:
    - chuc_danh (string)
    - so_nam_kinh_nghiem_toi_thieu (number)
    - ky_nang_bat_buoc (list of strings)

    Yêu cầu: "{search_text}"
    """
    try:
        response = model.generate_content(prompt)
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned_response)
    except (json.JSONDecodeError, Exception) as e:
        print(f"Error parsing search query: {e}")
        return {}