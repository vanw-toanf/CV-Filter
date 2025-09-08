import pdfplumber
from docx import Document
import io

def convert_file_to_text(file_content: bytes, content_type: str) -> str:
    """Chuyển đổi nội dung file (bytes) sang text."""
    full_text = ""
    if content_type == "application/pdf":
        with pdfplumber.open(io.BytesIO(file_content)) as pdf:
            for page in pdf.pages:
                full_text += page.extract_text() + "\n"
    elif content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = Document(io.BytesIO(file_content))
        for para in doc.paragraphs:
            full_text += para.text + "\n"
    return full_text