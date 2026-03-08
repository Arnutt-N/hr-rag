"""
Search & Chat API Router - Native FastAPI endpoints
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.vector_store_langchain import get_vector_store_service
from app.services.rag_chain import get_rag_service
from app.services.chat_graph import get_chat_graph_service

router = APIRouter(prefix="/api/v1", tags=["Search & Chat"])


# Models
class SearchRequest(BaseModel):
    query: str
    category: Optional[str] = None
    limit: int = 5


class SearchResponse(BaseModel):
    success: bool
    query: str
    total: int
    results: list


class ChatRequest(BaseModel):
    message: str
    user_id: int
    session_id: str
    project_id: Optional[int] = None
    llm_provider: str = "openai"


class ChatResponse(BaseModel):
    success: bool
    answer: str
    intent: Optional[str]
    quality_score: Optional[float]
    sources: Optional[list]


class AnswerRequest(BaseModel):
    question: str
    project_id: Optional[int] = None
    include_sources: bool = True


@router.post("/search", response_model=SearchResponse)
async def search_knowledge_base(request: SearchRequest):
    """
    ค้นหาเอกสารใน Knowledge Base
    
    Search HR knowledge base.
    
    - query: คำค้นหา (ภาษาไทยหรืออังกฤษ)
    - category: หมวดหมู่ (policy, handbook, procedure, form)
    - limit: จำนวนผลลัพธ์ (default: 5)
    """
    try:
        vector_store = get_vector_store_service()
        collection = f"hr_{request.category}" if request.category else "hr_documents"
        
        docs = await vector_store.similarity_search(
            collection_name=collection,
            query=request.query,
            k=min(request.limit, 20)
        )
        
        results = [
            {
                "content": doc.page_content[:500],
                "metadata": doc.metadata,
                "score": doc.metadata.get("score", 0)
            }
            for doc in docs
        ]
        
        return SearchResponse(
            success=True,
            query=request.query,
            total=len(results),
            results=results
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ask", response_model=ChatResponse)
async def answer_question(request: AnswerRequest):
    """
    ถามคำถามและได้คำตอบ (RAG)
    
    Ask question using RAG.
    
    - question: คำถาม
    - project_id: รหัสโปรเจกต์ (optional)
    - include_sources: แสดงแหล่งที่มา
    """
    try:
        collection = f"project_{request.project_id}" if request.project_id else "hr_documents"
        rag = get_rag_service(collection_name=collection)
        
        result = await rag.answer(
            question=request.question,
            collection_name=collection,
            return_sources=request.include_sources
        )
        
        return ChatResponse(
            success=True,
            answer=result["answer"],
            sources=result.get("sources")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    แชทผ่าน LangGraph Workflow
    
    Chat with LangGraph workflow.
    
    - message: ข้อความ
    - user_id: รหัสผู้ใช้
    - session_id: รหัสเซสชัน
    - project_id: รหัสโปรเจกต์ (optional)
    """
    try:
        graph = get_chat_graph_service()
        
        result = await graph.chat(
            message=request.message,
            user_id=request.user_id,
            session_id=request.session_id,
            project_id=request.project_id,
            llm_provider=request.llm_provider
        )
        
        return ChatResponse(
            success=True,
            answer=result.get("answer", ""),
            intent=result.get("intent"),
            quality_score=result.get("quality_score"),
            sources=result.get("sources")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories")
async def list_categories():
    """
    แสดงหมวดหมู่เอกสารทั้งหมด
    
    List all document categories.
    """
    return {
        "categories": [
            {"id": "policy", "name": "นโยบาย", "description": "นโยบายบริษัทและกฎระเบียบ"},
            {"id": "handbook", "name": "คู่มือพนักงาน", "description": "คู่มือและแนวทางการทำงาน"},
            {"id": "procedure", "name": "ขั้นตอน", "description": "ขั้นตอนและวิธีการดำเนินการ"},
            {"id": "form", "name": "แบบฟอร์ม", "description": "แบบฟอร์มและเอกสารที่เกี่ยวข้อง"},
            {"id": "benefit", "name": "สวัสดิการ", "description": "สวัสดิการและสิทธิประโยชน์"},
            {"id": "training", "name": "การอบรม", "description": "หลักสูตรและการอบรม"}
        ]
    }


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    แชทแบบ Stream (สำหรับ realtime)
    
    Chat with streaming response.
    
    **Note:** ใช้ WebSocket หรือ Server-Sent Events
    """
    # TODO: Implement streaming with WebSocket
    return {"message": "Streaming not yet implemented. Use /chat instead."}
