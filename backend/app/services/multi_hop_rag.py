"""
Multi-hop Retrieval - Answer complex questions requiring multiple steps
"""

from typing import List, Dict, Any, Optional
import json

from langchain_core.documents import Document
from app.services.llm.langchain_service import get_llm_service
from app.services.advanced_retrieval import get_advanced_retrieval_service


class MultiHopRetrievalService:
    """
    Multi-hop retrieval for complex questions.
    
    Example:
    Question: "นโยบายลาของพนักงานฝ่ายไอทีที่ทำงานมา 2 ปี"
    
    Hop 1: Find general leave policy
    Hop 2: Find IT department specific rules
    Hop 3: Find seniority-based benefits
    Final: Combine all information
    """
    
    def __init__(self, max_hops: int = 3):
        self.max_hops = max_hops
        self.llm_service = get_llm_service()
        self.retrieval_service = get_advanced_retrieval_service()
    
    async def retrieve_multi_hop(
        self,
        query: str,
        collection_name: str,
        k_per_hop: int = 3
    ) -> Dict[str, Any]:
        """
        Perform multi-hop retrieval.
        
        Args:
            query: Complex question
            collection_name: Vector collection
            k_per_hop: Documents per hop
        
        Returns:
            Combined results from multiple hops
        """
        # Step 1: Decompose query into sub-questions
        sub_questions = await self._decompose_query(query)
        
        # Step 2: Retrieve for each sub-question
        all_results = []
        context = ""
        
        for i, sub_q in enumerate(sub_questions[:self.max_hops]):
            # Retrieve with context from previous hops
            results = await self._retrieve_with_context(
                query=sub_q,
                collection_name=collection_name,
                context=context,
                k=k_per_hop
            )
            
            all_results.append({
                'hop': i + 1,
                'question': sub_q,
                'results': results
            })
            
            # Update context for next hop
            context += f"\n\n[Hop {i+1}: {sub_q}]\n"
            for r in results:
                context += r['document'].page_content[:300] + "\n"
        
        # Step 3: Synthesize final answer
        final_answer = await self._synthesize_answer(query, all_results)
        
        return {
            'success': True,
            'original_query': query,
            'sub_questions': sub_questions,
            'hops': all_results,
            'final_answer': final_answer,
            'total_hops': len(all_results)
        }
    
    async def _decompose_query(self, query: str) -> List[str]:
        """Decompose complex query into sub-questions."""
        prompt = f"""แยกคำถามซับซ้อนออกเป็นคำถามย่อย:

คำถามหลัก: {query}

แยกเป็น 2-3 คำถามย่อยที่ต้องหาคำตอบ:
1."""
        
        try:
            response = await self.llm_service.chat([
                {"role": "user", "content": prompt}
            ])
            
            # Parse sub-questions
            lines = [line.strip() for line in response.split('\n') if line.strip()]
            sub_questions = []
            
            for line in lines:
                # Remove numbering
                clean = line.lstrip('0123456789. ')
                if clean and len(clean) > 10:
                    sub_questions.append(clean)
            
            # Add original if no decomposition
            if not sub_questions:
                sub_questions = [query]
            
            return sub_questions[:self.max_hops]
            
        except Exception as e:
            return [query]
    
    async def _retrieve_with_context(
        self,
        query: str,
        collection_name: str,
        context: str,
        k: int
    ) -> List[Dict[str, Any]]:
        """Retrieve documents with context from previous hops."""
        # Enhance query with context
        enhanced_query = f"{query}\n\nContext: {context[:500]}"
        
        # Use advanced retrieval
        results = await self.retrieval_service.hybrid_search(
            query=enhanced_query,
            collection_name=collection_name,
            k=k
        )
        
        return results
    
    async def _synthesize_answer(
        self,
        original_query: str,
        hops: List[Dict[str, Any]]
    ) -> str:
        """Synthesize final answer from all hops."""
        # Build context from all hops
        context_parts = []
        for hop in hops:
            context_parts.append(f"\n[{hop['question']}]")
            for r in hop['results'][:2]:  # Top 2 per hop
                context_parts.append(r['document'].page_content[:400])
        
        context = "\n".join(context_parts)
        
        prompt = f"""สร้างคำตอบจากข้อมูลที่หามา:

คำถาม: {original_query}

ข้อมูลที่พบ:
{context}

คำตอบ:"""
        
        try:
            answer = await self.llm_service.chat([
                {"role": "user", "content": prompt}
            ])
            return answer
        except:
            return "ไม่สามารถสร้างคำตอบได้"


class SelfRAGService:
    """
    Self-RAG: Retrieval with self-reflection and correction.
    
    The system evaluates its own retrieval and generation,
    and iteratively improves until confident.
    """
    
    def __init__(self, max_iterations: int = 3, confidence_threshold: float = 0.8):
        self.max_iterations = max_iterations
        self.confidence_threshold = confidence_threshold
        self.llm_service = get_llm_service()
        self.retrieval_service = get_advanced_retrieval_service()
    
    async def retrieve_and_generate(
        self,
        query: str,
        collection_name: str
    ) -> Dict[str, Any]:
        """
        Self-RAG with iterative improvement.
        """
        iteration = 0
        best_result = None
        best_score = 0
        
        while iteration < self.max_iterations:
            iteration += 1
            
            # Step 1: Retrieve
            retrieved = await self.retrieval_service.hybrid_search(
                query=query,
                collection_name=collection_name,
                k=5
            )
            
            # Step 2: Generate answer
            context = "\n\n".join([r['document'].page_content[:500] for r in retrieved[:3]])
            answer = await self._generate_answer(query, context)
            
            # Step 3: Self-evaluate
            evaluation = await self._evaluate_answer(query, answer, context)
            
            # Step 4: Check if good enough
            if evaluation['confidence'] >= self.confidence_threshold:
                return {
                    'success': True,
                    'answer': answer,
                    'confidence': evaluation['confidence'],
                    'iterations': iteration,
                    'retrieved_documents': retrieved,
                    'evaluation': evaluation
                }
            
            # Save best result
            if evaluation['confidence'] > best_score:
                best_score = evaluation['confidence']
                best_result = {
                    'answer': answer,
                    'confidence': evaluation['confidence'],
                    'retrieved_documents': retrieved,
                    'evaluation': evaluation
                }
            
            # Step 5: Improve if needed
            if iteration < self.max_iterations:
                query = await self._improve_query(query, evaluation)
        
        # Return best result after max iterations
        if best_result:
            return {
                'success': True,
                'answer': best_result['answer'],
                'confidence': best_result['confidence'],
                'iterations': iteration,
                'retrieved_documents': best_result['retrieved_documents'],
                'evaluation': best_result['evaluation'],
                'note': 'Max iterations reached'
            }
        
        return {'success': False, 'error': 'Could not generate confident answer'}
    
    async def _generate_answer(self, query: str, context: str) -> str:
        """Generate answer from context."""
        prompt = f"""ตอบคำถามจากข้อมูล:

ข้อมูล: {context}

คำถาม: {query}

คำตอบ:"""
        
        return await self.llm_service.chat([
            {"role": "user", "content": prompt}
        ])
    
    async def _evaluate_answer(
        self,
        query: str,
        answer: str,
        context: str
    ) -> Dict[str, Any]:
        """Self-evaluate answer quality."""
        prompt = f"""ประเมินคุณภาพคำตอบ (0-10):

คำถาม: {query}
คำตอบ: {answer}
ข้อมูลอ้างอิง: {context[:500]}

ประเมิน:
1. ความถูกต้อง (0-10):
2. ความสมบูรณ์ (0-10):
3. ความเกี่ยวข้อง (0-10):

คะแนนรวม (0-10):"""
        
        try:
            response = await self.llm_service.chat([
                {"role": "user", "content": prompt}
            ])
            
            # Extract score
            import re
            numbers = re.findall(r'\d+', response)
            if numbers:
                score = int(numbers[-1])  # Last number
                score = min(10, max(0, score)) / 10
            else:
                score = 0.5
            
            return {
                'confidence': score,
                'assessment': response
            }
        except:
            return {'confidence': 0.5, 'assessment': 'Evaluation failed'}
    
    async def _improve_query(self, query: str, evaluation: Dict) -> str:
        """Improve query based on evaluation."""
        prompt = f"""ปรับปรุงคำถามให้ชัดเจนขึ้น:

คำถามเดิม: {query}
ปัญหา: {evaluation.get('assessment', 'ไม่แน่ใจ')}

คำถามที่ปรับปรุง:"""
        
        try:
            improved = await self.llm_service.chat([
                {"role": "user", "content": prompt}
            ])
            return improved.strip() if improved.strip() else query
        except:
            return query


# Singleton
_multi_hop: Optional[MultiHopRetrievalService] = None
_self_rag: Optional[SelfRAGService] = None


def get_multi_hop_service() -> MultiHopRetrievalService:
    """Get multi-hop service singleton."""
    global _multi_hop
    if _multi_hop is None:
        _multi_hop = MultiHopRetrievalService()
    return _multi_hop


def get_self_rag_service() -> SelfRAGService:
    """Get self-RAG service singleton."""
    global _self_rag
    if _self_rag is None:
        _self_rag = SelfRAGService()
    return _self_rag
