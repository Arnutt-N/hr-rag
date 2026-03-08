"""
Document Generation API Router - Native FastAPI endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from app.services.document_generation import get_document_generation_service

router = APIRouter(prefix="/documents", tags=["Document Generation"])


# Models
class GenerateDocumentRequest(BaseModel):
    doc_type: str  # policy, procedure, memo, announcement, email, form
    topic: str
    requirements: List[str]
    reference_category: Optional[str] = None


class DocumentResponse(BaseModel):
    success: bool
    title: str
    content: str
    doc_type: str


@router.post("/generate", response_model=DocumentResponse)
async def generate_document(request: GenerateDocumentRequest):
    """
    สร้างเอกสาร HR ใหม่
    
    Generate new HR document.
    
    **ประเภทเอกสารที่รองรับ:**
    - `policy` - นโยบาย
    - `procedure` - ขั้นตอนการปฏิบัติงาน
    - `memo` - บันทึกข้อความ
    - `announcement` - ประกาศ
    - `email` - อีเมลทางการ
    - `form` - แบบฟอร์ม
    """
    try:
        service = get_document_generation_service()
        
        result = await service.generate_document(
            doc_type=request.doc_type,
            topic=request.topic,
            requirements=request.requirements,
            collection_name=f"hr_{request.reference_category}" if request.reference_category else "hr_documents"
        )
        
        return DocumentResponse(
            success=True,
            title=result["title"],
            content=result["content"],
            doc_type=request.doc_type
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/batch")
async def generate_documents_batch(requests: List[GenerateDocumentRequest]):
    """
    สร้างเอกสารหลายฉบับพร้อมกัน
    
    Generate multiple documents.
    """
    results = []
    for request in requests:
        try:
            service = get_document_generation_service()
            result = await service.generate_document(
                doc_type=request.doc_type,
                topic=request.topic,
                requirements=request.requirements
            )
            results.append({
                "success": True,
                "title": result["title"],
                "doc_type": request.doc_type
            })
        except Exception as e:
            results.append({
                "success": False,
                "error": str(e),
                "topic": request.topic
            })
    
    return {
        "total": len(requests),
        "successful": sum(1 for r in results if r.get("success")),
        "results": results
    }


@router.get("/types")
async def get_document_types():
    """
    แสดงประเภทเอกสารที่รองรับ
    
    List supported document types.
    """
    return {
        "types": [
            {"id": "policy", "name": "นโยบาย", "description": "นโยบายบริษัท"},
            {"id": "procedure", "name": "ขั้นตอน", "description": "ขั้นตอนการปฏิบัติงาน"},
            {"id": "memo", "name": "บันทึกข้อความ", "description": "บันทึกข้อความภายใน"},
            {"id": "announcement", "name": "ประกาศ", "description": "ประกาศบริษัท"},
            {"id": "email", "name": "อีเมล", "description": "อีเมลทางการ"},
            {"id": "form", "name": "แบบฟอร์ม", "description": "แบบฟอร์มกรอกข้อมูล"}
        ]
    }
