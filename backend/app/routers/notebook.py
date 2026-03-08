"""
Notebook API Router - Native FastAPI endpoints for NotebookLM features
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.mcp_notebooklm import get_notebooklm_service

router = APIRouter(prefix="/notebook", tags=["Notebook"])


# Models
class SummarizeRequest(BaseModel):
    query: str
    summary_type: str = "comprehensive"  # brief, comprehensive, bullet_points
    language: str = "thai"


class InsightsRequest(BaseModel):
    query: str


class QARequest(BaseModel):
    document_content: str
    num_questions: int = 10
    difficulty: str = "mixed"


class PodcastRequest(BaseModel):
    topic: str
    documents: List[str]
    duration_minutes: int = 10
    style: str = "interview"  # interview, lecture


@router.post("/summarize")
async def notebook_summarize(request: SummarizeRequest):
    """
    สรุปเอกสาร (NotebookLM Style)
    
    Summarize documents.
    
    - query: หัวข้อ/คำค้นหา
    - summary_type: ประเภทสรุป (brief, comprehensive, bullet_points)
    - language: ภาษา (thai, english)
    """
    try:
        service = get_notebooklm_service()
        result = await service.summarize_document(
            query=request.query,
            summary_type=request.summary_type,
            language=request.language
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/insights")
async def notebook_insights(request: InsightsRequest):
    """
    ดึง Insights สำคัญจากเอกสาร
    
    Extract key insights.
    
    - query: หัวข้อที่ต้องการวิเคราะห์
    """
    try:
        service = get_notebooklm_service()
        result = await service.extract_insights(query=request.query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-qa")
async def notebook_generate_qa(request: QARequest):
    """
    สร้างคำถาม-คำตอบจากเอกสาร
    
    Generate Q&A from document.
    
    - document_content: เนื้อหาเอกสาร
    - num_questions: จำนวนคำถาม
    - difficulty: ระดับความยาก (easy, medium, hard, mixed)
    """
    try:
        service = get_notebooklm_service()
        result = await service.generate_qa(
            document_content=request.document_content,
            num_questions=request.num_questions,
            difficulty=request.difficulty
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/podcast-script")
async def notebook_podcast_script(request: PodcastRequest):
    """
    สร้างสคริปต์พอดคาสต์
    
    Generate podcast script.
    
    - topic: หัวข้อพอดคาสต์
    - documents: รายการเนื้อหาเอกสาร
    - duration_minutes: ความยาว (นาที)
    - style: สไตล์ (interview, lecture)
    """
    try:
        service = get_notebooklm_service()
        result = await service.generate_podcast_script(
            topic=request.topic,
            documents=request.documents,
            duration_minutes=request.duration_minutes,
            style=request.style
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare")
async def notebook_compare(
    doc_queries: List[str],
    comparison_aspects: List[str]
):
    """
    เปรียบเทียบหลายเอกสาร
    
    Compare multiple documents.
    
    - doc_queries: คำค้นหาสำหรับแต่ละเอกสาร
    - comparison_aspects: ด้านที่ต้องการเปรียบเทียบ
    """
    try:
        service = get_notebooklm_service()
        result = await service.compare_documents(
            doc_queries=doc_queries,
            comparison_aspects=comparison_aspects
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
