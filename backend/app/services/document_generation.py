"""
Document Generation Service - Generate new documents from existing content
"""

from typing import Optional, List, Dict, Any
from datetime import datetime

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.services.llm.langchain_service import get_llm_service
from app.services.vector_store_langchain import get_vector_store_service


class DocumentGenerationService:
    """
    Generate new documents based on:
    - Existing documents in knowledge base
    - User requirements
    - Templates
    """
    
    def __init__(self):
        self.llm_service = get_llm_service()
        self.vector_store = get_vector_store_service()
    
    async def generate_document(
        self,
        doc_type: str,  # "policy", "procedure", "memo", "announcement"
        topic: str,
        requirements: List[str],
        reference_docs: Optional[List[str]] = None,
        collection_name: str = "hr_documents"
    ) -> Dict[str, Any]:
        """
        Generate a new document.
        
        Args:
            doc_type: Type of document to generate
            topic: Document topic/title
            requirements: List of requirements/content points
            reference_docs: Optional list of reference document IDs
            collection_name: Vector store collection
        
        Returns:
            Generated document with metadata
        """
        # 1. Retrieve relevant context
        context = await self._get_context(topic, collection_name)
        
        # 2. Build prompt based on doc type
        prompt = self._build_generation_prompt(doc_type, topic, requirements, context)
        
        # 3. Generate with LLM
        response = await self.llm_service.chat([
            {"role": "user", "content": prompt}
        ], temperature=0.7)
        
        return {
            "title": topic,
            "type": doc_type,
            "content": response,
            "generated_at": datetime.utcnow().isoformat(),
            "references_used": context.get("sources", [])
        }
    
    async def _get_context(self, topic: str, collection_name: str) -> Dict[str, Any]:
        """Get relevant context from knowledge base."""
        docs = await self.vector_store.similarity_search(
            collection_name=collection_name,
            query=topic,
            k=5
        )
        
        context_text = "\n\n".join([doc.page_content for doc in docs])
        
        return {
            "text": context_text,
            "sources": [doc.metadata.get("source", "Unknown") for doc in docs]
        }
    
    def _build_generation_prompt(
        self,
        doc_type: str,
        topic: str,
        requirements: List[str],
        context: Dict[str, Any]
    ) -> str:
        """Build generation prompt."""
        
        templates = {
            "policy": """สร้างนโยบาย HR ต่อไปนี้:

**หัวข้อ:** {topic}

**ข้อกำหนด:**
{requirements}

**เอกสารอ้างอิง:**
{context}

**โครงสร้างนโยบาย:**
1. วัตถุประสงค์
2. ขอบเขตการบังคับใช้
3. รายละเอียดนโยบาย
4. ขั้นตอนการดำเนินการ
5. ผู้รับผิดชอบ

**เนื้อหานโยบาย (ภาษาไทย):**""",

            "procedure": """สร้างขั้นตอนการปฏิบัติงานต่อไปนี้:

**หัวข้อ:** {topic}

**ข้อกำหนด:**
{requirements}

**เอกสารอ้างอิง:**
{context}

**โครงสร้าง:**
1. วัตถุประสงค์
2. ขอบเขต
3. คำนิยาม
4. ขั้นตอนการดำเนินการ (แยกเป็นขั้นตอนย่อย)
5. แบบฟอร์มที่เกี่ยวข้อง
6. ผู้รับผิดชอบ

**เนื้อหา (ภาษาไทย):**""",

            "memo": """สร้างบันทึกข้อความ (Memo) ต่อไปนี้:

**เรื่อง:** {topic}

**รายละเอียด:**
{requirements}

**เอกสารอ้างอิง:**
{context}

**โครงสร้าง:**
- ส่วนราชการ
- ที่
- วันที่
- เรื่อง
- เรียน
- เนื้อหา
- ลงชื่อ

**เนื้อหา (ภาษาไทย):**""",

            "announcement": """สร้างประกาศบริษัทต่อไปนี้:

**หัวข้อ:** {topic}

**รายละเอียด:**
{requirements}

**เอกสารอ้างอิง:**
{context}

**โครงสร้าง:**
- หัวเรื่อง
- วันที่
- เนื้อหาประกาศ
- ผู้มีอำนาจลงนาม
- วันที่มีผลบังคับใช้

**เนื้อหา (ภาษาไทย):**"""
        }
        
        template = templates.get(doc_type, templates["policy"])
        
        return template.format(
            topic=topic,
            requirements="\n".join(f"- {r}" for r in requirements),
            context=context["text"][:2000]  # Limit context
        )


# Singleton
_doc_gen_service: Optional[DocumentGenerationService] = None


def get_document_generation_service() -> DocumentGenerationService:
    """Get document generation service singleton."""
    global _doc_gen_service
    if _doc_gen_service is None:
        _doc_gen_service = DocumentGenerationService()
    return _doc_gen_service
