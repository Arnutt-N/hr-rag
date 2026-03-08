"""
Chat Nodes - Node functions for LangGraph workflow
"""

from typing import Optional, Dict, Any
import random
import time

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.services.chat_state import ChatState
from app.services.llm.langchain_service import get_llm_service
from app.services.rag_chain import get_rag_service


class ChatNodes:
    """
    Node functions for chat workflow graph.
    
    Each node takes a state and returns an updated state.
    """
    
    def __init__(
        self,
        llm_provider: str = "openai",
        collection_name: str = "hr_documents"
    ):
        """
        Initialize chat nodes.
        
        Args:
            llm_provider: LLM provider name
            collection_name: Vector store collection
        """
        self.llm_service = get_llm_service(llm_provider)
        self.rag_service = get_rag_service(collection_name)
        self.collection_name = collection_name
    
    # ============================================
    # Memory Nodes
    # ============================================
    
    async def load_memory(self, state: ChatState) -> ChatState:
        """
        Load memory context from various sources.
        
        Args:
            state: Current state
        
        Returns:
            State with memory loaded
        """
        # TODO: Implement actual memory loading in Phase 3
        # For now, set empty context
        
        state["short_term_context"] = []
        state["entity_context"] = ""
        state["relevant_memories"] = []
        
        return state
    
    async def save_memory(self, state: ChatState) -> ChatState:
        """
        Save conversation to memory after response.
        
        Args:
            state: Current state
        
        Returns:
            State (unchanged, memory saved as side effect)
        """
        # TODO: Implement actual memory saving in Phase 3
        
        return state
    
    # ============================================
    # Intent Classification
    # ============================================
    
    async def classify_intent(self, state: ChatState) -> ChatState:
        """
        Classify user intent from message.
        
        Args:
            state: Current state
        
        Returns:
            State with intent classified
        """
        last_message = state["messages"][-1].content
        
        # Simple rule-based classification (can be enhanced with LLM)
        intent = self._classify_intent_rules(last_message)
        
        state["intent"] = intent
        state["intent_confidence"] = 0.9 if intent != "other" else 0.5
        
        return state
    
    def _classify_intent_rules(self, message: str) -> str:
        """
        Classify intent using simple rules.
        
        Args:
            message: User message
        
        Returns:
            Intent string
        """
        message_lower = message.lower()
        
        # Greeting patterns
        greetings = ["สวัสดี", "hello", "hi", "หวัดดี", "เฮลโล"]
        if any(g in message_lower for g in greetings):
            return "greeting"
        
        # Question patterns
        if "?" in message or any(word in message_lower for word in ["ไหม", "มั้ย", "อย่างไร", "อะไร", "ที่ไหน", "เมื่อไหร่", "how", "what", "where", "when", "why"]):
            return "question"
        
        # Complaint patterns
        complaints = ["ไม่พอใจ", "ร้องเรียน", "ปัญหา", "ไม่ได้", "แย่", "complaint"]
        if any(c in message_lower for c in complaints):
            return "complaint"
        
        # Chitchat patterns
        chitchat = ["ขอบคุณ", "thank", "ดีใจ", "เย้", "โอเค", "ok"]
        if any(c in message_lower for c in chitchat):
            return "chitchat"
        
        return "question"  # Default to question for HR assistant
    
    # ============================================
    # Response Nodes
    # ============================================
    
    async def handle_greeting(self, state: ChatState) -> ChatState:
        """
        Handle greeting intent.
        
        Args:
            state: Current state
        
        Returns:
            State with greeting response
        """
        greetings = [
            "สวัสดีค่ะ! 👋 ลิตาพร้อมช่วยเหลือเรื่อง HR แล้วค่ะ มีอะไรให้ช่วยไหมคะ?",
            "ยินดีต้อนรับค่ะ! 🌟 ถามเรื่องนโยบาย HR ได้เลยนะคะ",
            "สวัสดีค่ะ! วันนี้ต้องการค้นหาข้อมูลอะไรคะ?",
        ]
        
        response = random.choice(greetings)
        
        state["final_answer"] = response
        state["messages"].append(AIMessage(content=response))
        state["quality_score"] = 1.0
        state["needs_regeneration"] = False
        
        return state
    
    async def handle_chitchat(self, state: ChatState) -> ChatState:
        """
        Handle chitchat intent.
        
        Args:
            state: Current state
        
        Returns:
            State with chitchat response
        """
        responses = [
            "ยินดีค่ะ! มีอะไรให้ช่วยเพิ่มเติมไหมคะ?",
            "ขอบคุณค่ะ! หากมีคำถามเพิ่มเติมถามได้เลยนะคะ",
            "ดีใจที่ได้ช่วยค่ะ! 😊",
        ]
        
        response = random.choice(responses)
        
        state["final_answer"] = response
        state["messages"].append(AIMessage(content=response))
        state["quality_score"] = 1.0
        state["needs_regeneration"] = False
        
        return state
    
    async def handle_complaint(self, state: ChatState) -> ChatState:
        """
        Handle complaint intent.
        
        Args:
            state: Current state
        
        Returns:
            State with complaint response
        """
        last_message = state["messages"][-1].content
        
        response = f"""ขอบคุณที่แจ้งปัญหามาค่ะ เราเข้าใจว่าท่านมีความไม่พอใจ

เพื่อให้เราช่วยเหลือได้ดียิ่งขึ้น กรุณาแจ้ง:
1. รายละเอียดปัญหาที่พบ
2. แผนก/หน่วยงานที่เกี่ยวข้อง
3. ช่องทางที่ท่านต้องการให้ติดต่อกลับ

หรือติดต่อ HR โดยตรงที่:
- อีเมล: hr@company.com
- โทร: 02-xxx-xxxx ต่อ 1234"""

        state["final_answer"] = response
        state["messages"].append(AIMessage(content=response))
        state["quality_score"] = 0.8
        state["needs_regeneration"] = False
        
        return state
    
    # ============================================
    # RAG Nodes
    # ============================================
    
    async def retrieve_documents(self, state: ChatState) -> ChatState:
        """
        Retrieve relevant documents from vector store.
        
        Args:
            state: Current state
        
        Returns:
            State with retrieved documents
        """
        last_message = state["messages"][-1].content
        project_id = state.get("project_id")
        
        # Determine collection
        collection = f"project_{project_id}" if project_id else self.collection_name
        
        try:
            # Retrieve documents
            result = await self.rag_service.answer(
                question=last_message,
                collection_name=collection,
                k=5,
                return_sources=True
            )
            
            state["retrieved_documents"] = result.get("sources", [])
            state["retrieved_chunks"] = [s["content"] for s in result.get("sources", [])]
            state["draft_answer"] = result.get("answer")
            
            # Calculate average retrieval score
            state["retrieval_score"] = 0.7  # Default score
            
        except Exception as e:
            state["error"] = f"Retrieval error: {str(e)}"
            state["retrieved_documents"] = []
            state["retrieved_chunks"] = []
            state["draft_answer"] = None
            state["retrieval_score"] = 0.0
        
        return state
    
    async def generate_answer(self, state: ChatState) -> ChatState:
        """
        Generate final answer from retrieved context.
        
        Args:
            state: Current state
        
        Returns:
            State with generated answer
        """
        # Use draft answer from RAG if available
        if state.get("draft_answer"):
            state["final_answer"] = state["draft_answer"]
        else:
            # Fallback to direct LLM call
            last_message = state["messages"][-1].content
            
            try:
                response = await self.llm_service.chat([
                    {"role": "system", "content": "คุณเป็นผู้ช่วย HR ที่ตอบคำถามอย่างเป็นประโยชน์"},
                    {"role": "user", "content": last_message}
                ])
                
                state["final_answer"] = response
                state["fallback_used"] = True
                
            except Exception as e:
                state["error"] = f"Generation error: {str(e)}"
                state["final_answer"] = "ขออภัยค่ะ เกิดข้อผิดพลาดในการประมวลผล กรุณาลองใหม่อีกครั้งค่ะ"
        
        # Add to messages
        if state.get("final_answer"):
            state["messages"].append(AIMessage(content=state["final_answer"]))
        
        return state
    
    # ============================================
    # Quality Evaluation
    # ============================================
    
    async def evaluate_quality(self, state: ChatState) -> ChatState:
        """
        Evaluate answer quality.
        
        Args:
            state: Current state
        
        Returns:
            State with quality score
        """
        answer = state.get("final_answer", "")
        context = state.get("retrieved_chunks", [])
        
        # Simple heuristic evaluation
        score = self._calculate_quality_score(answer, context)
        
        state["quality_score"] = score
        state["needs_regeneration"] = score < 0.6
        state["quality_feedback"] = self._get_quality_feedback(score)
        
        return state
    
    def _calculate_quality_score(self, answer: str, context: list) -> float:
        """
        Calculate quality score based on heuristics.
        
        Args:
            answer: Generated answer
            context: Retrieved context
        
        Returns:
            Quality score (0.0 - 1.0)
        """
        if not answer:
            return 0.0
        
        score = 0.7  # Base score
        
        # Check answer length
        if len(answer) > 50:
            score += 0.1
        if len(answer) > 100:
            score += 0.05
        
        # Check if answer uses context
        if context:
            context_text = " ".join(context)
            overlap = sum(1 for word in answer.split() if word in context_text)
            if overlap > 5:
                score += 0.1
        
        # Check for Thai response
        thai_chars = sum(1 for c in answer if ord(c) >= 0x0E00 and ord(c) <= 0x0E7F)
        if thai_chars > len(answer) * 0.3:
            score += 0.05
        
        return min(score, 1.0)
    
    def _get_quality_feedback(self, score: float) -> str:
        """
        Get feedback based on quality score.
        
        Args:
            score: Quality score
        
        Returns:
            Feedback string
        """
        if score >= 0.9:
            return "Excellent quality"
        elif score >= 0.7:
            return "Good quality"
        elif score >= 0.5:
            return "Acceptable quality, could be improved"
        else:
            return "Poor quality, regeneration recommended"
    
    async def regenerate_answer(self, state: ChatState) -> ChatState:
        """
        Regenerate answer with better prompting.
        
        Args:
            state: Current state
        
        Returns:
            State with regenerated answer
        """
        # Get original question
        user_messages = [m for m in state["messages"] if isinstance(m, HumanMessage)]
        if not user_messages:
            return state
        
        last_user_message = user_messages[-1].content
        context = state.get("retrieved_chunks", [])
        
        # Better prompt with explicit context
        prompt = f"""Based on the following documents, provide a detailed and accurate answer in Thai:

**เอกสารอ้างอิง:**
{chr(10).join(context) if context else 'ไม่มีเอกสารอ้างอิง'}

**คำถาม:** {last_user_message}

**คำตอบ:**"""
        
        try:
            response = await self.llm_service.chat([
                {"role": "user", "content": prompt}
            ])
            
            state["final_answer"] = response
            state["retry_count"] = state.get("retry_count", 0) + 1
            
            # Update last AI message
            if state["messages"] and isinstance(state["messages"][-1], AIMessage):
                state["messages"][-1] = AIMessage(content=response)
            
        except Exception as e:
            state["error"] = f"Regeneration error: {str(e)}"
        
        return state
