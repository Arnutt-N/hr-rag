"""
MCP Research Service - Research and document creation
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
import json

from app.services.llm.langchain_service import get_llm_service
from app.services.vector_store_langchain import get_vector_store_service


class MCPResearchService:
    """
    Research service for:
    - Literature review
    - Research synthesis
    - Report generation
    - Citation management
    - Evidence-based recommendations
    """
    
    def __init__(self):
        self.llm_service = get_llm_service()
        self.vector_store = get_vector_store_service()
    
    async def research_topic(
        self,
        topic: str,
        research_questions: List[str],
        sources: Optional[List[str]] = None,
        max_sources: int = 10
    ) -> Dict[str, Any]:
        """
        Conduct research on a topic.
        
        Args:
            topic: Research topic
            research_questions: Questions to answer
            sources: Specific sources to use (optional)
            max_sources: Maximum sources to retrieve
        
        Returns:
            Research findings
        """
        try:
            # Retrieve relevant documents
            docs = await self.vector_store.similarity_search(
                collection_name="hr_documents",
                query=topic,
                k=max_sources
            )
            
            # Compile evidence
            evidence = []
            for doc in docs:
                evidence.append({
                    "content": doc.page_content[:500],
                    "source": doc.metadata.get("source", "Unknown"),
                    "title": doc.metadata.get("title", "Untitled"),
                    "relevance_score": doc.metadata.get("score", 0)
                })
            
            # Build research prompt
            prompt = f"""วิจัยหัวข้อ: {topic}

คำถามวิจัย:
{chr(10).join([f'{i+1}. {q}' for i, q in enumerate(research_questions)])}

หลักฐานจากเอกสาร:
{chr(10).join([f'[{e["source"]}] {e["content"]}' for e in evidence[:5]])}

โครงสร้างรายงานวิจัย:
1. บทคัดย่อ (Abstract)
2. คำถามวิจัย (Research Questions)
3. วิธีการ (Methodology)
4. ผลการวิจัย (Findings) - ตอบแต่ละคำถาม
5. การวิเคราะห์ (Analysis)
6. ข้อจำกัด (Limitations)
7. ข้อเสนอแนะ (Recommendations)
8. บรรณานุกรม (References)

รายงานวิจัย:"""
            
            research_report = await self.llm_service.chat([
                {"role": "user", "content": prompt}
            ])
            
            return {
                "success": True,
                "topic": topic,
                "research_questions": research_questions,
                "report": research_report,
                "sources_used": len(evidence),
                "evidence": evidence,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def literature_review(
        self,
        topic: str,
        time_range: Optional[str] = None,  # e.g., "2020-2024"
        focus_areas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate literature review.
        
        Args:
            topic: Review topic
            time_range: Time period
            focus_areas: Specific areas to focus on
        
        Returns:
            Literature review
        """
        try:
            # Retrieve documents
            docs = await self.vector_store.similarity_search(
                collection_name="hr_documents",
                query=topic,
                k=15
            )
            
            contents = [doc.page_content[:800] for doc in docs]
            
            focus_text = ""
            if focus_areas:
                focus_text = f"\nเน้นด้าน: {', '.join(focus_areas)}"
            
            time_text = f"\nช่วงเวลา: {time_range}" if time_range else ""
            
            prompt = f"""เขียน Literature Review หัวข้อ: {topic}{time_text}{focus_text}

เอกสารที่เกี่ยวข้อง:
{chr(10).join([f'{i+1}. {c}' for i, c in enumerate(contents[:10])])}

โครงสร้าง Literature Review:
1. บทนำ (Introduction)
   - ความสำคัญของหัวข้อ
   - ขอบเขตการรีวิว

2. ทฤษฎีและงานวิจัยที่เกี่ยวข้อง (Theoretical Framework)

3. การวิเคราะห์เอกสาร (Analysis)
   - แนวคิดหลักที่พบ
   - ช่องโหว่ในงานวิจัย (Research Gaps)
   - แนวโน้ม (Trends)

4. สรุป (Conclusion)
   - ประเด็นสำคัญ
   - ข้อเสนอแนะสำหรับการวิจัยต่อไป

5. บรรณานุกรม (References)

Literature Review:"""
            
            review = await self.llm_service.chat([
                {"role": "user", "content": prompt}
            ])
            
            return {
                "success": True,
                "topic": topic,
                "time_range": time_range,
                "focus_areas": focus_areas,
                "review": review,
                "documents_reviewed": len(docs),
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def evidence_synthesis(
        self,
        claim: str,
        evidence_queries: List[str]
    ) -> Dict[str, Any]:
        """
        Synthesize evidence for a claim.
        
        Args:
            claim: Claim to evaluate
            evidence_queries: Queries to find evidence
        
        Returns:
            Evidence synthesis
        """
        try:
            # Gather evidence
            all_evidence = []
            for query in evidence_queries:
                docs = await self.vector_store.similarity_search(
                    collection_name="hr_documents",
                    query=query,
                    k=3
                )
                for doc in docs:
                    all_evidence.append({
                        "content": doc.page_content[:400],
                        "source": doc.metadata.get("source", "Unknown"),
                        "query": query
                    })
            
            prompt = f"""วิเคราะห์ข้อความอ้างอิงต่อไปนี้:

ข้อความ: "{claim}"

หลักฐานที่พบ:
{chr(10).join([f'[{e["source"]}] {e["content"]}' for e in all_evidence])}

โครงสร้างการวิเคราะห์:
1. สรุปข้อความ (Claim Summary)

2. หลักฐานสนับสนุน (Supporting Evidence)
   - รายการพร้อมแหล่งที่มา

3. หลักฐานคัดค้าน (Contradicting Evidence)
   - รายการพร้อมแหล่งที่มา

4. ความน่าเชื่อถือ (Credibility Assessment)
   - จุดแข็งของข้อความ
   - ข้อจำกัด/จุดอ่อน

5. ข้อสรุป (Conclusion)
   - ข้อความมีหลักฐานสนับสนุนหรือไม่
   - ระดับความมั่นใจ (สูง/ปานกลาง/ต่ำ)

6. ข้อเสนอแนะ (Recommendations)

การวิเคราะห์:"""
            
            analysis = await self.llm_service.chat([
                {"role": "user", "content": prompt}
            ])
            
            return {
                "success": True,
                "claim": claim,
                "analysis": analysis,
                "evidence_count": len(all_evidence),
                "sources": list(set(e["source"] for e in all_evidence))
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def generate_research_proposal(
        self,
        title: str,
        background: str,
        objectives: List[str],
        methodology_approach: str
    ) -> Dict[str, Any]:
        """
        Generate research proposal.
        
        Args:
            title: Research title
            background: Background/context
            objectives: Research objectives
            methodology_approach: Methodology approach
        
        Returns:
            Research proposal
        """
        try:
            # Search for related research
            related_docs = await self.vector_store.similarity_search(
                collection_name="hr_documents",
                query=title,
                k=5
            )
            
            related_research = "\n".join([
                f"- {doc.metadata.get('title', 'Untitled')}: {doc.page_content[:200]}"
                for doc in related_docs
            ])
            
            prompt = f"""เขียนโครงร่างการวิจัย (Research Proposal)

ชื่อเรื่อง: {title}

ที่มาและความสำคัญ:
{background}

วัตถุประสงค์:
{chr(10).join([f'{i+1}. {o}' for i, o in enumerate(objectives)])}

แนวทางวิธีวิจัย: {methodology_approach}

งานวิจัยที่เกี่ยวข้อง:
{related_research}

โครงสร้าง Proposal:
1. ชื่อเรื่อง (Title)
2. บทคัดย่อ (Abstract) - 250 คำ
3. บทนำ (Introduction)
   - ที่มาและความสำคัญ
   - วัตถุประสงค์
   - ขอบเขต
   - คำจำกัดความ

4. ทบทวนวรรณกรรม (Literature Review)
   - ทฤษฎีที่เกี่ยวข้อง
   - งานวิจัยที่เกี่ยวข้อง
   - ช่องโหว่วิจัย (Research Gap)

5. กรอบแนวคิด (Conceptual Framework)

6. วิธีการวิจัย (Methodology)
   - การออกแบบวิจัย
   - ประชากรและตัวอย่าง
   - เครื่องมือเก็บรวบรวมข้อมูล
   - การวิเคราะห์ข้อมูล

7. กำหนดการ (Timeline)

8. งบประมาณ (Budget) - โดยประมาณ

9. บรรณานุกรม (References)

10. ภาคผนวก (Appendices)

Proposal:"""
            
            proposal = await self.llm_service.chat([
                {"role": "user", "content": prompt}
            ])
            
            return {
                "success": True,
                "title": title,
                "proposal": proposal,
                "objectives": objectives,
                "methodology": methodology_approach,
                "related_research_count": len(related_docs),
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}


# Singleton
_research_service: Optional[MCPResearchService] = None


def get_research_service() -> MCPResearchService:
    """Get research service singleton."""
    global _research_service
    if _research_service is None:
        _research_service = MCPResearchService()
    return _research_service
