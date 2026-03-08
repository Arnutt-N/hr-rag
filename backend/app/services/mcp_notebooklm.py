"""
MCP NotebookLM Service - AI-powered document summarization and analysis
"""

from typing import Optional, Dict, Any, List
from datetime import datetime

from app.services.llm.langchain_service import get_llm_service
from app.services.vector_store_langchain import get_vector_store_service


class MCPNotebookLMService:
    """
    NotebookLM-style service for:
    - Document summarization
    - Key insights extraction
    - Q&A generation
    - Audio script generation (for podcasts)
    - Multi-document synthesis
    """
    
    def __init__(self):
        self.llm_service = get_llm_service()
        self.vector_store = get_vector_store_service()
    
    async def summarize_document(
        self,
        document_id: Optional[str] = None,
        query: Optional[str] = None,
        summary_type: str = "comprehensive",  # brief, comprehensive, bullet_points
        language: str = "thai"
    ) -> Dict[str, Any]:
        """
        Summarize document(s).
        
        Args:
            document_id: Specific document ID (optional)
            query: Search query to find relevant docs
            summary_type: Type of summary
            language: Output language
        
        Returns:
            Summary with key points
        """
        try:
            # Retrieve document content
            if document_id:
                # TODO: Get specific document
                content = "[Document content]"
            elif query:
                docs = await self.vector_store.similarity_search(
                    collection_name="hr_documents",
                    query=query,
                    k=3
                )
                content = "\n\n".join([doc.page_content for doc in docs])
            else:
                return {"success": False, "error": "Provide document_id or query"}
            
            # Build prompt based on summary type
            prompts = {
                "brief": f"""สรุปเอกสารต่อไปนี้อย่างกระชับ (3-5 ประโยค):

{content[:3000]}

สรุป:""",
                
                "comprehensive": f"""สรุปเอกสารต่อไปนี้อย่างละเอียด:

{content[:5000]}

โครงสร้างสรุป:
1. บทสรุปผู้บริหาร (Executive Summary)
2. ประเด็นสำคัญ (Key Points)
3. รายละเอียด (Details)
4. ข้อควรระวัง (Cautions)
5. บทสรุป (Conclusion)

สรุป:""",
                
                "bullet_points": f"""สรุปเอกสารต่อไปนี้เป็น bullet points:

{content[:4000]}

สรุป:
• (point 1)
• (point 2)
• (point 3)
..."""
            }
            
            prompt = prompts.get(summary_type, prompts["comprehensive"])
            
            # Generate summary
            summary = await self.llm_service.chat([
                {"role": "user", "content": prompt}
            ])
            
            return {
                "success": True,
                "summary": summary,
                "summary_type": summary_type,
                "language": language,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def extract_insights(
        self,
        query: str,
        collection_name: str = "hr_documents"
    ) -> Dict[str, Any]:
        """
        Extract key insights from documents.
        
        Args:
            query: Topic to analyze
            collection_name: Document collection
        
        Returns:
            Insights with evidence
        """
        try:
            # Retrieve relevant documents
            docs = await self.vector_store.similarity_search(
                collection_name=collection_name,
                query=query,
                k=5
            )
            
            content = "\n\n".join([doc.page_content for doc in docs])
            
            prompt = f"""วิเคราะห์และสรุป insights สำคัญจากเอกสารต่อไปนี้ เกี่ยวกับ: {query}

{content[:5000]}

โครงสร้าง:
1. Insights หลัก (3-5 ข้อ)
   - Insight: ...
   - หลักฐานจากเอกสาร: ...
   - ความสำคัญ: ...

2. แนวโน้มที่พบ (Trends)

3. ข้อควรระวัง (Watch-outs)

4. คำแนะนำ (Recommendations)

วิเคราะห์:"""
            
            insights = await self.llm_service.chat([
                {"role": "user", "content": prompt}
            ])
            
            return {
                "success": True,
                "topic": query,
                "insights": insights,
                "sources": [doc.metadata.get("source", "Unknown") for doc in docs],
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def generate_qa(
        self,
        document_content: str,
        num_questions: int = 10,
        difficulty: str = "mixed"  # easy, medium, hard, mixed
    ) -> Dict[str, Any]:
        """
        Generate Q&A from document.
        
        Args:
            document_content: Document text
            num_questions: Number of questions
            difficulty: Question difficulty
        
        Returns:
            Q&A pairs
        """
        try:
            prompt = f"""สร้างคำถาม-คำตอบจากเอกสารต่อไปนี้:

{document_content[:4000]}

จำนวนคำถาม: {num_questions} ข้อ
ระดับความยาก: {difficulty}

รูปแบบ:
Q1: [คำถาม]
A1: [คำตอบ]

Q2: [คำถาม]
A2: [คำตอบ]

..."""
            
            qa = await self.llm_service.chat([
                {"role": "user", "content": prompt}
            ])
            
            return {
                "success": True,
                "qa": qa,
                "num_questions": num_questions,
                "difficulty": difficulty
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def generate_podcast_script(
        self,
        topic: str,
        documents: List[str],
        duration_minutes: int = 10,
        style: str = "interview"  # interview, lecture, discussion
    ) -> Dict[str, Any]:
        """
        Generate podcast script from documents.
        
        Args:
            topic: Podcast topic
            documents: List of document contents
            duration_minutes: Target duration
            style: Podcast style
        
        Returns:
            Podcast script
        """
        try:
            combined_content = "\n\n".join(documents)[:5000]
            
            prompts = {
                "interview": f"""สร้างสคริปต์พอดคาสต์แบบสัมภาษณ์ เรื่อง: {topic}

ข้อมูลจากเอกสาร:
{combined_content}

โครงสร้าง ({duration_minutes} นาที):
- แนะนำ: พิธีกรแนะนำหัวข้อและแขกรับเชิญ
- เนื้อหาหลัก: สัมภาษณ์ ถาม-ตอบ สลับกัน
- สรุป: สรุปประเด็นสำคัญ

สคริปต์:
[พิธีกร]: สวัสดีครับ/ค่ะ...
[แขก]: ...""",
                
                "lecture": f"""สร้างสคริปต์บรรยาย เรื่อง: {topic}

ข้อมูล:
{combined_content}

สคริปต์ ({duration_minutes} นาที):
[ผู้บรรยาย]: ..."""
            }
            
            prompt = prompts.get(style, prompts["interview"])
            
            script = await self.llm_service.chat([
                {"role": "user", "content": prompt}
            ])
            
            return {
                "success": True,
                "topic": topic,
                "style": style,
                "duration": duration_minutes,
                "script": script
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def compare_documents(
        self,
        doc_queries: List[str],
        comparison_aspects: List[str]
    ) -> Dict[str, Any]:
        """
        Compare multiple documents.
        
        Args:
            doc_queries: Queries to find documents
            comparison_aspects: Aspects to compare
        
        Returns:
            Comparison analysis
        """
        try:
            # Retrieve documents
            documents = []
            for query in doc_queries:
                docs = await self.vector_store.similarity_search(
                    collection_name="hr_documents",
                    query=query,
                    k=2
                )
                documents.extend(docs)
            
            contents = [doc.page_content[:2000] for doc in documents]
            
            prompt = f"""เปรียบเทียบเอกสารต่อไปนี้:

{chr(10).join([f'เอกสาร {i+1}:\n{c}' for i, c in enumerate(contents)])}

ด้านที่ต้องการเปรียบเทียบ:
{chr(10).join(comparison_aspects)}

รูปแบบผลลัพธ์:
| ด้าน | เอกสาร 1 | เอกสาร 2 | ... |
|-------|----------|----------|-----|
| ... | ... | ... | ... |

ความเหมือน: ...
ความแตกต่าง: ...
ข้อแนะนำ: ..."""
            
            comparison = await self.llm_service.chat([
                {"role": "user", "content": prompt}
            ])
            
            return {
                "success": True,
                "comparison": comparison,
                "aspects": comparison_aspects,
                "num_documents": len(documents)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}


# Singleton
_notebooklm_service: Optional[MCPNotebookLMService] = None


def get_notebooklm_service() -> MCPNotebookLMService:
    """Get NotebookLM service singleton."""
    global _notebooklm_service
    if _notebooklm_service is None:
        _notebooklm_service = MCPNotebookLMService()
    return _notebooklm_service
