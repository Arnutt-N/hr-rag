"""
FastMCP Server - MCP server for HR-RAG tools
"""

from typing import Optional, List, Dict, Any
import json
from datetime import datetime

from fastmcp import FastMCP

from app.core.config import settings


# Create MCP server
mcp = FastMCP(
    "hr-rag-server",
    description="HR-RAG MCP Server - AI-powered HR Knowledge Assistant"
)


# ============================================
# TOOLS
# ============================================

@mcp.tool()
async def search_knowledge_base(
    query: str,
    category: Optional[str] = None,
    limit: int = 5
) -> str:
    """
    Search the HR knowledge base for relevant documents.
    
    Args:
        query: Search query in Thai or English
        category: Optional category filter (policy, handbook, procedure, form)
        limit: Maximum number of results (default: 5, max: 20)
    
    Returns:
        JSON string with search results
    """
    from app.services.vector_store_langchain import get_vector_store_service
    
    try:
        # Determine collection
        collection = f"hr_{category}" if category else "hr_documents"
        
        # Search
        vector_store = get_vector_store_service()
        docs = await vector_store.similarity_search(
            collection_name=collection,
            query=query,
            k=min(limit, 20)
        )
        
        # Format results
        results = [
            {
                "content": doc.page_content[:500],
                "metadata": doc.metadata,
                "score": doc.metadata.get("score", 0)
            }
            for doc in docs
        ]
        
        return json.dumps({
            "success": True,
            "query": query,
            "category": category,
            "total": len(results),
            "results": results
        }, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, ensure_ascii=False)


@mcp.tool()
async def answer_question(
    question: str,
    project_id: Optional[int] = None,
    include_sources: bool = True
) -> str:
    """
    Answer a question using RAG (Retrieval-Augmented Generation).
    
    Args:
        question: Question in Thai or English
        project_id: Optional project ID for project-specific knowledge
        include_sources: Include source documents in response
    
    Returns:
        JSON string with answer and optional sources
    """
    from app.services.rag_chain import get_rag_service
    
    try:
        # Get RAG service
        collection = f"project_{project_id}" if project_id else "hr_documents"
        rag = get_rag_service(collection_name=collection)
        
        # Answer
        result = await rag.answer(
            question=question,
            collection_name=collection,
            return_sources=include_sources
        )
        
        return json.dumps({
            "success": True,
            "answer": result["answer"],
            "sources": result.get("sources", []) if include_sources else []
        }, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, ensure_ascii=False)


@mcp.tool()
async def chat(
    message: str,
    user_id: int,
    session_id: str,
    project_id: Optional[int] = None
) -> str:
    """
    Send a chat message through the LangGraph workflow.
    
    Args:
        message: User message
        user_id: User ID
        session_id: Session ID for conversation continuity
        project_id: Optional project ID
    
    Returns:
        JSON string with response and metadata
    """
    from app.services.chat_graph import get_chat_graph_service
    
    try:
        # Get chat graph
        graph = get_chat_graph_service()
        
        # Process message
        result = await graph.chat(
            message=message,
            user_id=user_id,
            session_id=session_id,
            project_id=project_id
        )
        
        return json.dumps({
            "success": True,
            "answer": result.get("answer", ""),
            "intent": result.get("intent"),
            "quality_score": result.get("quality_score"),
            "thread_id": result.get("thread_id"),
            "sources": result.get("sources", [])
        }, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, ensure_ascii=False)


@mcp.tool()
async def list_categories() -> str:
    """
    List all knowledge base categories.
    
    Returns:
        JSON string with list of categories
    """
    categories = [
        {"id": "policy", "name": "นโยบาย", "description": "นโยบายบริษัทและกฎระเบียบ"},
        {"id": "handbook", "name": "คู่มือพนักงาน", "description": "คู่มือและแนวทางการทำงาน"},
        {"id": "procedure", "name": "ขั้นตอน", "description": "ขั้นตอนและวิธีการดำเนินการ"},
        {"id": "form", "name": "แบบฟอร์ม", "description": "แบบฟอร์มและเอกสารที่เกี่ยวข้อง"},
        {"id": "benefit", "name": "สวัสดิการ", "description": "สวัสดิการและสิทธิประโยชน์"},
        {"id": "training", "name": "การอบรม", "description": "หลักสูตรและการอบรม"},
    ]
    
    return json.dumps({
        "success": True,
        "categories": categories
    }, ensure_ascii=False)


@mcp.tool()
async def get_user_info(user_id: int) -> str:
    """
    Get user profile information (admin only).
    
    Args:
        user_id: User ID to lookup
    
    Returns:
        JSON string with user details
    """
    # TODO: Implement actual user lookup from database
    # This is a placeholder implementation
    
    return json.dumps({
        "success": True,
        "user": {
            "id": user_id,
            "username": f"user_{user_id}",
            "department": "Engineering",
            "role": "Employee"
        }
    }, ensure_ascii=False)


@mcp.tool()
async def index_document(
    content: str,
    title: str,
    category: str,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Index a new document into the knowledge base.
    
    Args:
        content: Document content
        title: Document title
        category: Document category
        metadata: Optional additional metadata
    
    Returns:
        JSON string with indexing result
    """
    from langchain_core.documents import Document
    from app.services.vector_store_langchain import get_vector_store_service
    from app.services.text_splitters import get_splitter
    
    try:
        # Create document
        doc = Document(
            page_content=content,
            metadata={
                "title": title,
                "category": category,
                "indexed_at": datetime.utcnow().isoformat(),
                **(metadata or {})
            }
        )
        
        # Split document
        splitter = get_splitter(thai_optimized=True)
        chunks = splitter.split_documents([doc])
        
        # Index to vector store
        vector_store = get_vector_store_service()
        ids = await vector_store.add_documents(
            collection_name=f"hr_{category}",
            documents=chunks
        )
        
        return json.dumps({
            "success": True,
            "document_id": ids[0] if ids else None,
            "chunks_created": len(chunks),
            "title": title,
            "category": category
        }, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, ensure_ascii=False)


# ============================================
# RESOURCES
# ============================================

@mcp.resource("docs://policies")
async def get_all_policies() -> str:
    """Get all HR policies as a resource."""
    # TODO: Implement actual policy retrieval
    return json.dumps({
        "policies": [
            {"id": "POL-001", "title": "นโยบายการลางาน"},
            {"id": "POL-002", "title": "นโยบายการทำงานล่วงเวลา"},
            {"id": "POL-003", "title": "นโยบายสวัสดิการ"},
        ]
    }, ensure_ascii=False)


@mcp.resource("docs://handbook")
async def get_employee_handbook() -> str:
    """Get employee handbook content."""
    # TODO: Implement actual handbook retrieval
    return """# คู่มือพนักงาน

## บทที่ 1: ข้อมูลทั่วไป
บริษัทมีนโยบายให้ความสำคัญกับพนักงานทุกคน...

## บทที่ 2: สวัสดิการ
พนักงานมีสิทธิ์ได้รับสวัสดิการต่างๆ ได้แก่...
"""


@mcp.resource("stats://usage")
async def get_usage_stats() -> str:
    """Get current usage statistics."""
    # TODO: Implement actual stats retrieval
    return json.dumps({
        "total_queries": 1523,
        "total_users": 45,
        "total_documents": 128,
        "last_updated": datetime.utcnow().isoformat()
    }, ensure_ascii=False)


# ============================================
# PROMPTS
# ============================================

@mcp.prompt()
def hr_assistant_prompt() -> str:
    """Default prompt for HR assistant."""
    return """คุณเป็นผู้ช่วย HR สำหรับบริษัทไทย

**หน้าที่:**
- ตอบคำถามเกี่ยวกับนโยบายและกฎระเบียบ
- ให้ข้อมูลสวัสดิการและสิทธิประโยชน์
- ช่วยเหลือเรื่องการลางานและการทำงาน

**แนวทาง:**
- ตอบเป็นภาษาไทย
- ใช้ข้อมูลจากเอกสารที่ให้เท่านั้น
- สุภาพและเป็นมิตร
- หากไม่แน่ใจ ให้แนะนำติดต่อ HR โดยตรง"""


@mcp.prompt()
def policy_expert_prompt(topic: str) -> str:
    """Prompt for policy expert mode."""
    return f"""คุณเป็นผู้เชี่ยวชาญด้านนโยบาย HR โดยเฉพาะเรื่อง: {topic}

**หน้าที่:**
- ให้ข้อมูลเฉพาะทางเกี่ยวกับ {topic}
- อ้างอิงเอกสารอย่างชัดเจน
- ให้คำแนะนำที่ปฏิบัติได้จริง

**หัวข้อ:** {topic}"""


@mcp.prompt()
def complaint_handler_prompt() -> str:
    """Prompt for handling complaints."""
    return """คุณเป็นเจ้าหน้าที่รับเรื่องร้องเรียน

**แนวทาง:**
- รับฟังอย่างใส่ใจ
- ไม่ตัดสินหรือโต้แย้ง
- บันทึกรายละเอียดให้ครบถ้วน
- แนะนำช่องทางการติดต่อที่เหมาะสม
- รักษาความลับของผู้ร้องเรียน"""


# ============================================
# SERVER STARTUP
# ============================================

def main():
    """Run MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
