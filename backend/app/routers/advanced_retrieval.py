"""
Advanced Retrieval API Router - Multi-hop, Self-RAG, and more
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.multi_hop_rag import get_multi_hop_service, get_self_rag_service
from app.services.thai_chunking import ThaiSemanticChunker, QueryClassifier
from app.services.human_in_the_loop import get_human_in_the_loop_service

router = APIRouter(prefix="/advanced", tags=["Advanced Retrieval"])


# Models
class MultiHopRequest(BaseModel):
    query: str
    collection_name: str = "hr_documents"
    max_hops: int = 3


class SelfRAGRequest(BaseModel):
    query: str
    collection_name: str = "hr_documents"


class FeedbackRequest(BaseModel):
    query_id: str
    query: str
    answer: str
    rating: int  # 1-5
    feedback_type: str  # correct, partial, incorrect, hallucination
    user_comment: Optional[str] = None


@router.post("/multi-hop")
async def multi_hop_retrieve(request: MultiHopRequest):
    """
    Multi-hop retrieval for complex questions
    
    ค้นหาหลายขั้นตอนสำหรับคำถามซับซ้อน
    """
    try:
        service = get_multi_hop_service()
        result = await service.retrieve_multi_hop(
            query=request.query,
            collection_name=request.collection_name,
            k_per_hop=3
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/self-rag")
async def self_rag_retrieve(request: SelfRAGRequest):
    """
    Self-RAG with iterative improvement
    
    ค้นหาพร้อมประเมินตัวเองและปรับปรุง
    """
    try:
        service = get_self_rag_service()
        result = await service.retrieve_and_generate(
            query=request.query,
            collection_name=request.collection_name
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/classify-query")
async def classify_query(query: str):
    """
    Classify query type
    
    แยกประเภทคำถามเพื่อเลือกกลยุทธ์ที่เหมาะสม
    """
    try:
        classifier = QueryClassifier()
        classification = classifier.classify(query)
        strategy = classifier.get_retrieval_strategy(classification['type'])
        
        return {
            'query': query,
            'classification': classification,
            'recommended_strategy': strategy
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback")
async def submit_feedback(request: FeedbackRequest):
    """
    Submit user feedback
    
    ส่ง feedback เพื่อปรับปรุงระบบ
    """
    try:
        service = get_human_in_the_loop_service()
        result = service.submit_feedback(
            query_id=request.query_id,
            query=request.query,
            answer=request.answer,
            rating=request.rating,
            feedback_type=request.feedback_type,
            user_comment=request.user_comment
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feedback/stats")
async def get_feedback_stats(days: int = 30):
    """
    Get feedback statistics
    
    ดูสถิติ feedback
    """
    try:
        service = get_human_in_the_loop_service()
        stats = service.get_feedback_stats(days)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feedback/improvements")
async def get_improvement_suggestions():
    """
    Get queries needing improvement
    
    ดูคำถามที่ต้องปรับปรุง
    """
    try:
        service = get_human_in_the_loop_service()
        queries = service.get_queries_needing_improvement()
        return {
            'queries_needing_improvement': queries
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
