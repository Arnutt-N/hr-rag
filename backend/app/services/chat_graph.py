"""
Chat Graph - LangGraph workflow for HR-RAG chat
"""

from typing import Optional, Literal
import asyncio

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.services.chat_state import ChatState, create_initial_state
from app.services.chat_nodes import ChatNodes


class ChatGraphService:
    """
    Chat workflow using LangGraph.
    
    Implements a multi-step chat flow:
    1. Load memory context
    2. Classify intent
    3. Route to appropriate handler
    4. Retrieve documents (for questions)
    5. Generate answer
    6. Evaluate quality
    7. Regenerate if needed
    8. Save memory
    """
    
    def __init__(
        self,
        llm_provider: str = "openai",
        collection_name: str = "hr_documents",
        use_checkpointer: bool = True
    ):
        """
        Initialize chat graph service.
        
        Args:
            llm_provider: LLM provider name
            collection_name: Vector store collection
            use_checkpointer: Enable state persistence
        """
        self.nodes = ChatNodes(llm_provider, collection_name)
        self.use_checkpointer = use_checkpointer
        self.checkpointer = MemorySaver() if use_checkpointer else None
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """
        Build the chat workflow graph.
        
        Returns:
            Compiled LangGraph graph
        """
        # Create workflow
        workflow = StateGraph(ChatState)
        
        # ============================================
        # Add Nodes
        # ============================================
        
        workflow.add_node("load_memory", self.nodes.load_memory)
        workflow.add_node("classify_intent", self.nodes.classify_intent)
        workflow.add_node("handle_greeting", self.nodes.handle_greeting)
        workflow.add_node("handle_chitchat", self.nodes.handle_chitchat)
        workflow.add_node("handle_complaint", self.nodes.handle_complaint)
        workflow.add_node("retrieve_documents", self.nodes.retrieve_documents)
        workflow.add_node("generate_answer", self.nodes.generate_answer)
        workflow.add_node("evaluate_quality", self.nodes.evaluate_quality)
        workflow.add_node("regenerate_answer", self.nodes.regenerate_answer)
        workflow.add_node("save_memory", self.nodes.save_memory)
        
        # ============================================
        # Set Entry Point
        # ============================================
        
        workflow.set_entry_point("load_memory")
        
        # ============================================
        # Add Edges
        # ============================================
        
        # load_memory -> classify_intent
        workflow.add_edge("load_memory", "classify_intent")
        
        # classify_intent -> conditional routing
        workflow.add_conditional_edges(
            "classify_intent",
            self._route_by_intent,
            {
                "greeting": "handle_greeting",
                "chitchat": "handle_chitchat",
                "complaint": "handle_complaint",
                "question": "retrieve_documents",
            }
        )
        
        # Intent handlers -> save_memory -> END
        workflow.add_edge("handle_greeting", "save_memory")
        workflow.add_edge("handle_chitchat", "save_memory")
        workflow.add_edge("handle_complaint", "save_memory")
        
        # RAG flow
        workflow.add_edge("retrieve_documents", "generate_answer")
        workflow.add_edge("generate_answer", "evaluate_quality")
        
        # Quality evaluation -> conditional
        workflow.add_conditional_edges(
            "evaluate_quality",
            self._route_by_quality,
            {
                "good": "save_memory",
                "regenerate": "regenerate_answer"
            }
        )
        
        # Regenerate -> save_memory
        workflow.add_edge("regenerate_answer", "save_memory")
        
        # save_memory -> END
        workflow.add_edge("save_memory", END)
        
        # ============================================
        # Compile Graph
        # ============================================
        
        return workflow.compile(
            checkpointer=self.checkpointer,
            interrupt_before=None,  # No human-in-the-loop by default
            interrupt_after=None
        )
    
    def _route_by_intent(self, state: ChatState) -> str:
        """
        Route based on classified intent.
        
        Args:
            state: Current state
        
        Returns:
            Next node name
        """
        return state.get("intent", "question")
    
    def _route_by_quality(self, state: ChatState) -> str:
        """
        Route based on quality score.
        
        Args:
            state: Current state
        
        Returns:
            Next node name
        """
        if state.get("needs_regeneration", False) and state.get("retry_count", 0) < 2:
            return "regenerate"
        return "good"
    
    async def chat(
        self,
        message: str,
        user_id: int,
        session_id: str,
        project_id: Optional[int] = None,
        thread_id: Optional[str] = None,
        llm_provider: str = "openai"
    ) -> dict:
        """
        Process chat message through graph.
        
        Args:
            message: User message
            user_id: User ID
            session_id: Session ID
            project_id: Optional project ID
            thread_id: Thread ID for persistence
            llm_provider: LLM provider
        
        Returns:
            Response dict with answer and metadata
        """
        import time
        start_time = time.time()
        
        # Create initial state
        initial_state = create_initial_state(
            message=message,
            user_id=user_id,
            session_id=session_id,
            project_id=project_id,
            llm_provider=llm_provider
        )
        
        # Config for persistence
        config = {
            "configurable": {
                "thread_id": thread_id or session_id
            }
        }
        
        try:
            # Run graph
            result = await self.graph.ainvoke(initial_state, config)
            
            # Calculate processing time
            processing_time_ms = (time.time() - start_time) * 1000
            
            # Build response
            return {
                "answer": result.get("final_answer", ""),
                "sources": result.get("retrieved_documents", []),
                "intent": result.get("intent"),
                "quality_score": result.get("quality_score"),
                "thread_id": config["configurable"]["thread_id"],
                "processing_time_ms": processing_time_ms,
                "metadata": {
                    "retrieval_score": result.get("retrieval_score"),
                    "retry_count": result.get("retry_count", 0),
                    "fallback_used": result.get("fallback_used", False)
                }
            }
            
        except Exception as e:
            # Error response
            return {
                "answer": "ขออภัยค่ะ เกิดข้อผิดพลาดในการประมวลผล กรุณาลองใหม่อีกครั้งค่ะ",
                "error": str(e),
                "thread_id": config["configurable"]["thread_id"]
            }
    
    async def chat_stream(
        self,
        message: str,
        user_id: int,
        session_id: str,
        project_id: Optional[int] = None,
        thread_id: Optional[str] = None,
        llm_provider: str = "openai"
    ):
        """
        Stream chat response events.
        
        Args:
            message: User message
            user_id: User ID
            session_id: Session ID
            project_id: Optional project ID
            thread_id: Thread ID
            llm_provider: LLM provider
        
        Yields:
            Event dicts
        """
        # Create initial state
        initial_state = create_initial_state(
            message=message,
            user_id=user_id,
            session_id=session_id,
            project_id=project_id,
            llm_provider=llm_provider
        )
        
        # Config
        config = {
            "configurable": {
                "thread_id": thread_id or session_id
            }
        }
        
        # Stream events
        async for event in self.graph.astream_events(initial_state, config):
            yield event
    
    def get_graph_image(self) -> Optional[str]:
        """
        Get graph visualization as ASCII art.
        
        Returns:
            ASCII art string or None
        """
        try:
            from langgraph.graph import StateGraph
            return str(self.graph.get_graph())
        except:
            return None


# ============================================
# Singleton Instance
# ============================================

_chat_graph_service: Optional[ChatGraphService] = None


def get_chat_graph_service(
    llm_provider: str = "openai",
    collection_name: str = "hr_documents"
) -> ChatGraphService:
    """
    Get or create chat graph service singleton.
    
    Args:
        llm_provider: LLM provider name
        collection_name: Vector store collection
    
    Returns:
        ChatGraphService instance
    """
    global _chat_graph_service
    
    if _chat_graph_service is None:
        _chat_graph_service = ChatGraphService(
            llm_provider=llm_provider,
            collection_name=collection_name
        )
    
    return _chat_graph_service
