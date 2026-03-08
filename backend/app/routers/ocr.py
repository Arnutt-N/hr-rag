"""
OCR API Router - Native FastAPI endpoints for OCR
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from app.services.mcp_ocr import get_ocr_service

router = APIRouter(prefix="/ocr", tags=["OCR"])


# Models
class OCRRequest(BaseModel):
    file_path: str
    language: str = "tha+eng"
    enhance_resolution: bool = True


class OCRBatchRequest(BaseModel):
    file_paths: List[str]
    language: str = "tha+eng"


@router.post("/extract")
async def extract_text(
    file_path: str = Form(...),
    language: str = Form("tha+eng"),
    enhance_resolution: bool = Form(True)
):
    """
    แปลงเอกสาร/รูปภาพเป็นข้อความ (OCR)
    
    Extract text from document/image.
    
    **รองรับไฟล์:** PDF, PNG, JPG, TIFF, BMP
    **ภาษา:** tha+eng, tha, eng
    """
    try:
        service = get_ocr_service()
        result = await service.extract_text(
            file_path=file_path,
            language=language,
            enhance_resolution=enhance_resolution
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload-and-extract")
async def upload_and_extract(
    file: UploadFile = File(...),
    language: str = Form("tha+eng")
):
    """
    อัพโหลดไฟล์และแปลงเป็นข้อความ
    
    Upload file and extract text.
    """
    try:
        # Save uploaded file
        import tempfile
        import os
        
        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        # Extract text
        service = get_ocr_service()
        result = await service.extract_text(
            file_path=tmp_path,
            language=language
        )
        
        # Clean up
        os.unlink(tmp_path)
        
        result["filename"] = file.filename
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch")
async def batch_extract(request: OCRBatchRequest):
    """
    ประมวลผล OCR หลายไฟล์พร้อมกัน
    
    Batch OCR processing.
    """
    try:
        service = get_ocr_service()
        result = await service.batch_process(
            file_paths=request.file_paths,
            language=request.language
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/languages")
async def get_supported_languages():
    """
    แสดงภาษาที่รองรับ
    
    List supported OCR languages.
    """
    return {
        "languages": [
            {"code": "tha+eng", "name": "ไทย + อังกฤษ", "description": "ภาษาไทยและอังกฤษ"},
            {"code": "tha", "name": "ไทย", "description": "ภาษาไทยอย่างเดียว"},
            {"code": "eng", "name": "อังกฤษ", "description": "ภาษาอังกฤษอย่างเดียว"}
        ]
    }


@router.post("/validate-thai")
async def validate_thai_text(text: str = Form(...)):
    """
    ตรวจสอบคุณภาพข้อความภาษาไทย
    
    Validate Thai text quality.
    """
    try:
        service = get_ocr_service()
        result = service.validate_thai_text(text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
