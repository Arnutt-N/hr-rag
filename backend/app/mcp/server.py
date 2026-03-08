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


@mcp.tool()
async def generate_document(
    doc_type: str,
    topic: str,
    requirements: List[str],
    reference_category: Optional[str] = None
) -> str:
    """
    สร้างเอกสาร HR ใหม่จากข้อมูลที่มีและความต้องการ
    
    Generate a new HR document based on existing knowledge and requirements.
    
    Args:
        doc_type: ประเภทเอกสาร (policy=นโยบาย, procedure=ขั้นตอน, memo=บันทึก, 
                 announcement=ประกาศ, email=อีเมล, form=แบบฟอร์ม)
        topic: หัวข้อ/ชื่อเรื่องเอกสาร
        requirements: รายการข้อกำหนด/รายละเอียดที่ต้องมี
        reference_category: หมวดหมู่เอกสารอ้างอิง (optional)
    
    Returns:
        JSON string with generated document
    
    Examples:
        doc_type="policy", topic="นโยบาย Work From Home"
        doc_type="procedure", topic="ขั้นตอนการลางาน"
        doc_type="memo", topic="บันทึกข้อความ เรื่อง ประชุมพนักงาน"
    """
    from app.services.document_generation import get_document_generation_service
    
    try:
        # Get generation service
        gen_service = get_document_generation_service()
        
        # Generate document
        result = await gen_service.generate_document(
            doc_type=doc_type,
            topic=topic,
            requirements=requirements,
            collection_name=f"hr_{reference_category}" if reference_category else "hr_documents"
        )
        
        return json.dumps({
            "success": True,
            "message": "สร้างเอกสารสำเร็จ",
            "document": result
        }, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "message": "เกิดข้อผิดพลาดในการสร้างเอกสาร"
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
# OCR TOOLS (Thai-optimized)
# ============================================

@mcp.tool()
async def ocr_extract_text(
    file_path: str,
    language: str = "tha+eng",
    enhance_resolution: bool = True
) -> str:
    """
    แปลงเอกสาร/รูปภาพเป็นข้อความ (OCR) - รองรับภาษาไทย
    
    Extract text from document/image with Thai language support.
    
    Args:
        file_path: พาธไฟล์ (PDF, PNG, JPG)
        language: ภาษา (tha+eng, tha, eng)
        enhance_resolution: ปรับปรุงความละเอียด
    
    Returns:
        JSON with extracted text
    """
    from app.services.mcp_ocr import get_ocr_service
    
    try:
        ocr_service = get_ocr_service()
        result = await ocr_service.extract_text(
            file_path=file_path,
            language=language,
            enhance_resolution=enhance_resolution
        )
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)


@mcp.tool()
async def ocr_batch_process(
    file_paths: List[str],
    language: str = "tha+eng"
) -> str:
    """
    ประมวลผล OCR หลายไฟล์พร้อมกัน
    
    Batch OCR processing for multiple files.
    
    Args:
        file_paths: รายการพาธไฟล์
        language: ภาษา
    
    Returns:
        JSON with batch results
    """
    from app.services.mcp_ocr import get_ocr_service
    
    try:
        ocr_service = get_ocr_service()
        result = await ocr_service.batch_process(file_paths, language)
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)


# ============================================
# NOTEBOOKLM TOOLS
# ============================================

@mcp.tool()
async def notebook_summarize(
    query: str,
    summary_type: str = "comprehensive",
    language: str = "thai"
) -> str:
    """
    สรุปเอกสารแบบ NotebookLM
    
    Summarize documents like NotebookLM.
    
    Args:
        query: หัวข้อ/คำค้นหา
        summary_type: ประเภทสรุป (brief, comprehensive, bullet_points)
        language: ภาษาผลลัพธ์
    
    Returns:
        JSON with summary
    """
    from app.services.mcp_notebooklm import get_notebooklm_service
    
    try:
        service = get_notebooklm_service()
        result = await service.summarize_document(
            query=query,
            summary_type=summary_type,
            language=language
        )
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)


@mcp.tool()
async def notebook_insights(
    query: str
) -> str:
    """
    ดึง insights สำคัญจากเอกสาร
    
    Extract key insights from documents.
    
    Args:
        query: หัวข้อที่ต้องการวิเคราะห์
    
    Returns:
        JSON with insights
    """
    from app.services.mcp_notebooklm import get_notebooklm_service
    
    try:
        service = get_notebooklm_service()
        result = await service.extract_insights(query=query)
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)


@mcp.tool()
async def notebook_generate_qa(
    document_content: str,
    num_questions: int = 10
) -> str:
    """
    สร้างคำถาม-คำตอบจากเอกสาร
    
    Generate Q&A from document.
    
    Args:
        document_content: เนื้อหาเอกสาร
        num_questions: จำนวนคำถาม
    
    Returns:
        JSON with Q&A
    """
    from app.services.mcp_notebooklm import get_notebooklm_service
    
    try:
        service = get_notebooklm_service()
        result = await service.generate_qa(
            document_content=document_content,
            num_questions=num_questions
        )
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)


@mcp.tool()
async def notebook_podcast_script(
    topic: str,
    documents: List[str],
    duration_minutes: int = 10
) -> str:
    """
    สร้างสคริปต์พอดคาสต์จากเอกสาร
    
    Generate podcast script from documents.
    
    Args:
        topic: หัวข้อพอดคาสต์
        documents: รายการเนื้อหาเอกสาร
        duration_minutes: ความยาวเป้าหมาย (นาที)
    
    Returns:
        JSON with podcast script
    """
    from app.services.mcp_notebooklm import get_notebooklm_service
    
    try:
        service = get_notebooklm_service()
        result = await service.generate_podcast_script(
            topic=topic,
            documents=documents,
            duration_minutes=duration_minutes
        )
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)


# ============================================
# RESEARCH TOOLS
# ============================================

@mcp.tool()
async def research_topic(
    topic: str,
    research_questions: List[str],
    max_sources: int = 10
) -> str:
    """
    วิจัยหัวข้อพร้อมสรุปผล
    
    Conduct research on a topic with full report.
    
    Args:
        topic: หัวข้อวิจัย
        research_questions: คำถามวิจัย
        max_sources: จำนวนแหล่งข้อมูลสูงสุด
    
    Returns:
        JSON with research report
    """
    from app.services.mcp_research import get_research_service
    
    try:
        service = get_research_service()
        result = await service.research_topic(
            topic=topic,
            research_questions=research_questions,
            max_sources=max_sources
        )
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)


@mcp.tool()
async def research_literature_review(
    topic: str,
    time_range: Optional[str] = None,
    focus_areas: Optional[List[str]] = None
) -> str:
    """
    สร้าง Literature Review
    
    Generate literature review.
    
    Args:
        topic: หัวข้อรีวิว
        time_range: ช่วงเวลา (เช่น "2020-2024")
        focus_areas: ด้านที่เน้น
    
    Returns:
        JSON with literature review
    """
    from app.services.mcp_research import get_research_service
    
    try:
        service = get_research_service()
        result = await service.literature_review(
            topic=topic,
            time_range=time_range,
            focus_areas=focus_areas
        )
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)


@mcp.tool()
async def research_evidence_analysis(
    claim: str,
    evidence_queries: List[str]
) -> str:
    """
    วิเคราะห์หลักฐานสนับสนุนหรือคัดค้านข้อความ
    
    Analyze evidence for or against a claim.
    
    Args:
        claim: ข้อความที่ต้องการตรวจสอบ
        evidence_queries: คำค้นหาหลักฐาน
    
    Returns:
        JSON with evidence analysis
    """
    from app.services.mcp_research import get_research_service
    
    try:
        service = get_research_service()
        result = await service.evidence_synthesis(
            claim=claim,
            evidence_queries=evidence_queries
        )
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)


@mcp.tool()
async def research_proposal(
    title: str,
    background: str,
    objectives: List[str],
    methodology_approach: str
) -> str:
    """
    สร้างโครงร่างการวิจัย (Research Proposal)
    
    Generate research proposal.
    
    Args:
        title: ชื่อเรื่อง
        background: ที่มาและความสำคัญ
        objectives: วัตถุประสงค์
        methodology_approach: แนวทางวิธีวิจัย
    
    Returns:
        JSON with research proposal
    """
    from app.services.mcp_research import get_research_service
    
    try:
        service = get_research_service()
        result = await service.generate_research_proposal(
            title=title,
            background=background,
            objectives=objectives,
            methodology_approach=methodology_approach
        )
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)


# ============================================
# SKILL MANAGEMENT TOOLS
# ============================================

@mcp.tool()
async def skill_create(
    name: str,
    description: str,
    author: str,
    template: str = "basic",
    tags: Optional[List[str]] = None,
    dependencies: Optional[List[str]] = None
) -> str:
    """
    สร้าง Skill ใหม่จาก Template
    
    Create a new skill from template.
    
    Args:
        name: ชื่อ Skill
        description: คำอธิบาย
        author: ผู้สร้าง
        template: Template (basic, api, mcp, agent)
        tags: แท็ก
        dependencies: Dependencies ที่ต้องการ
    
    Returns:
        JSON with created skill info
    """
    from app.services.skill_manager import get_skill_registry
    
    try:
        registry = get_skill_registry()
        skill_path = registry.create_skill(
            name=name,
            description=description,
            author=author,
            template=template,
            tags=tags or [],
            dependencies=dependencies or []
        )
        
        return json.dumps({
            "success": True,
            "message": f"สร้าง Skill '{name}' สำเร็จ",
            "skill_path": skill_path,
            "template": template
        }, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "message": "เกิดข้อผิดพลาดในการสร้าง Skill"
        }, ensure_ascii=False)


@mcp.tool()
async def skill_import(skill_path: str) -> str:
    """
    Import Skill จาก Path
    
    Import skill from directory path.
    
    Args:
        skill_path: พาธไปยังโฟลเดอร์ Skill
    
    Returns:
        JSON with import result
    """
    from app.services.skill_manager import get_skill_registry
    
    try:
        registry = get_skill_registry()
        skill = registry.import_skill(skill_path)
        
        return json.dumps({
            "success": True,
            "message": f"Import Skill '{skill.metadata.name}' สำเร็จ",
            "skill_id": skill.metadata.name.lower().replace(" ", "_"),
            "functions": list(skill.functions.keys())
        }, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "message": "เกิดข้อผิดพลาดในการ Import Skill"
        }, ensure_ascii=False)


@mcp.tool()
async def skill_use(
    skill_id: str,
    function_name: str = "main",
    parameters: Optional[Dict[str, Any]] = None
) -> str:
    """
    ใช้งาน Skill
    
    Execute a skill function.
    
    Args:
        skill_id: ID ของ Skill
        function_name: ชื่อฟังก์ชัน (default: main)
        parameters: พารามิเตอร์สำหรับฟังก์ชัน
    
    Returns:
        JSON with execution result
    """
    from app.services.skill_manager import get_skill_registry
    
    try:
        registry = get_skill_registry()
        result = registry.use_skill(
            skill_id=skill_id,
            function_name=function_name,
            **(parameters or {})
        )
        
        return json.dumps({
            "success": True,
            "skill_id": skill_id,
            "function": function_name,
            "result": result
        }, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "message": f"เกิดข้อผิดพลาดในการใช้ Skill '{skill_id}'"
        }, ensure_ascii=False)


@mcp.tool()
async def skill_list() -> str:
    """
    แสดงรายการ Skills ทั้งหมด
    
    List all registered skills.
    
    Returns:
        JSON with skills list
    """
    from app.services.skill_manager import get_skill_registry
    
    try:
        registry = get_skill_registry()
        skills = registry.list_skills()
        
        return json.dumps({
            "success": True,
            "total_skills": len(skills),
            "skills": skills
        }, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, ensure_ascii=False)


@mcp.tool()
async def skill_toggle(skill_id: str, enable: bool = True) -> str:
    """
    เปิด/ปิด Skill
    
    Enable or disable a skill.
    
    Args:
        skill_id: ID ของ Skill
        enable: True=เปิด, False=ปิด
    
    Returns:
        JSON with result
    """
    from app.services.skill_manager import get_skill_registry
    
    try:
        registry = get_skill_registry()
        
        if enable:
            registry.enable_skill(skill_id)
            message = f"เปิดใช้งาน Skill '{skill_id}' แล้ว"
        else:
            registry.disable_skill(skill_id)
            message = f"ปิดใช้งาน Skill '{skill_id}' แล้ว"
        
        return json.dumps({
            "success": True,
            "message": message,
            "skill_id": skill_id,
            "enabled": enable
        }, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, ensure_ascii=False)


@mcp.tool()
async def skill_delete(skill_id: str) -> str:
    """
    ลบ Skill
    
    Delete a skill from registry.
    
    Args:
        skill_id: ID ของ Skill
    
    Returns:
        JSON with result
    """
    from app.services.skill_manager import get_skill_registry
    
    try:
        registry = get_skill_registry()
        registry.delete_skill(skill_id)
        
        return json.dumps({
            "success": True,
            "message": f"ลบ Skill '{skill_id}' แล้ว",
            "skill_id": skill_id
        }, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
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
