from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel
import uuid

from firebase import db, bucket
from gemini_utils import extract_cv_info_with_gemini, analyze_search_query_with_gemini
from utils import convert_file_to_text

app = FastAPI(title="CV Filtering API with Gemini")

class SearchQuery(BaseModel):
    text: str

class CandidateSelection(BaseModel):
    candidate_id: str # Dùng email hoặc ID của document

@app.post("/upload_cv/", status_code=201)
async def upload_cv(file: UploadFile = File(...)):
    if not file.content_type in ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
        raise HTTPException(status_code=400, detail="Chỉ chấp nhận file PDF và DOCX.")

    file_content = await file.read()

    # 1. Chuyển file sang text
    cv_text = convert_file_to_text(file_content, file.content_type)
    if not cv_text:
        raise HTTPException(status_code=400, detail="Không thể đọc nội dung từ file.")
        
    # 2. Bóc tách thông tin bằng Gemini
    extracted_data = extract_cv_info_with_gemini(cv_text)
    if not extracted_data or not extracted_data.get("email"):
        raise HTTPException(status_code=500, detail="Gemini không thể bóc tách thông tin hoặc thiếu email.")
        
    # 3. Thêm các trường do hệ thống quản lý
    file_name = f"cvs/{uuid.uuid4()}_{file.filename}"
    blob = bucket.blob(file_name)
    blob.upload_from_string(file_content, content_type=file.content_type)
    blob.make_public()

    extracted_data['cv_url'] = blob.public_url
    extracted_data['da_duoc_chon'] = False # <-- Thêm trạng thái mặc định
    extracted_data['raw_text'] = cv_text[:1500] # Lưu một phần text để tìm kiếm ngữ nghĩa sau này

    # 4. Lưu vào Firestore, dùng email làm ID document
    candidate_id = extracted_data["email"]
    doc_ref = db.collection('candidates').document(candidate_id)
    doc_ref.set(extracted_data)

    return {"message": f"CV của ứng viên {extracted_data.get('ho_ten')} đã được xử lý!", "candidate_id": candidate_id}


@app.post("/search_candidates/")
async def search_candidates(query: SearchQuery):
    search_criteria = analyze_search_query_with_gemini(query.text)
    
    candidates_ref = db.collection('candidates')
    
    # <-- Luôn lọc các CV chưa được chọn
    query_builder = candidates_ref.where('da_duoc_chon', '==', False)
    
    # Xây dựng truy vấn dựa trên tiêu chí
    if search_criteria.get("so_nam_kinh_nghiem_toi_thieu"):
        query_builder = query_builder.where('so_nam_kinh_nghiem', '>=', float(search_criteria["so_nam_kinh_nghiem_toi_thieu"]))
    
    if search_criteria.get("ky_nang_bat_buoc"):
        for skill in search_criteria["ky_nang_bat_buoc"]:
            query_builder = query_builder.where('ky_nang', 'array_contains', skill)

    docs = query_builder.stream()
    results = []
    for doc in docs:
        res = doc.to_dict()
        res['id'] = doc.id # Gửi kèm ID để frontend xử lý
        results.append(res)
    
    return {"results": results}


@app.post("/mark_as_selected/")
async def mark_as_selected(selection: CandidateSelection):
    """Đánh dấu một ứng viên là đã được chọn."""
    candidate_id = selection.candidate_id
    doc_ref = db.collection('candidates').document(candidate_id)
    
    if not doc_ref.get().exists:
        raise HTTPException(status_code=404, detail="Không tìm thấy ứng viên.")
    
    doc_ref.update({'da_duoc_chon': True})
    
    return {"message": f"Ứng viên {candidate_id} đã được đánh dấu là đã chọn."}