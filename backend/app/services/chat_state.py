"""
Chat State - State definition for LangGraph workflow
"""

from typing import TypedDict, List, Optional, Annotated, Any, Dict
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph.message import add_messages


class ChatState(TypedDict):
    """
    State for chat workflow.
    
    All fields are passed between nodes in the graph.
    """
    
    # ============================================
    # Messages (Core conversation)
    # ============================================
    # Automatically appends new messages with add_messages reducer
    messages: Annotated[List[BaseMessage], add_messages]
    
    # ============================================
    # User & Session Info
    # ============================================
    user_id: int
    session_id: str
    project_id: Optional[int]
    thread_id: Optional[str]
    
    # ============================================
    # Memory Context
    # ============================================
    short_term_context: Optional[List[BaseMessage]]  # From Redis
    long_term_summary: Optional[str]                  # From DB
    entity_context: Optional[str]                     # User entities
    relevant_memories: Optional[List[Dict]]           # Vector search
    
    # ============================================
    # Intent Classification
    # ============================================
    intent: Optional[str]  # "greeting", "question", "chitchat", "complaint", "other"
    intent_confidence: Optional[float]
    
    # ============================================
    # RAG Context
    # ============================================
    retrieved_documents: Optional[List[Dict]]
    retrieved_chunks: Optional[List[str]]
    retrieval_score: Optional[float]
    
    # ============================================
    # Answer Generation
    # ============================================
    draft_answer: Optional[str]
    final_answer: Optional[str]  # Alias for compatibility
    answer_confidence: Optional[float]
    
    # ============================================
    # Quality Evaluation
    # ============================================
    quality_score: Optional[float]  # 0.0 - 1.0
    quality_feedback: Optional[str]
    needs_regeneration: bool
    quality_evaluation: Optional[Dict]  # Detailed evaluation result
    
    # ============================================
    # Tool Calls
    # ============================================
    tool_calls: Optional[List[Dict[str, Any]]]
    tool_results: Optional[List[Dict[str, Any]]]
    
    # ============================================
    # Metadata
    # ============================================
    llm_provider: str
    model_name: Optional[str]
    token_count: int
    processing_time_ms: Optional[float]
    
    # ============================================
    # Error Handling
    # ============================================
    error: Optional[str]
    retry_count: int
    fallback_used: bool


class AgentState(TypedDict):
    """
    State for multi-agent workflow.
    
    Used when multiple agents collaborate on complex tasks.
    """
    
    # Messages
    messages: Annotated[List[BaseMessage], add_messages]
    
    # Agent routing
    current_agent: str
    next_agent: Optional[str]
    agent_history: List[str]
    
    # Task tracking
    task_id: str
    task_type: str
    task_status: str  # "pending", "in_progress", "completed", "failed"
    
    # Agent-specific data
    research_data: Optional[Dict[str, Any]]
    draft_content: Optional[str]
    review_result: Optional[Dict[str, Any]]
    
    # Final output
    final_output: Optional[Any]
    
    # Metadata
    created_at: str
    updated_at: str
    metadata: Dict[str, Any]


def create_initial_state(
    message: str,
    user_id: int,
    session_id: str,
    project_id: Optional[int] = None,
    llm_provider: str = "openai"
) -> ChatState:
    """
    Create initial chat state.
    
    Args:
        message: User's message
        user_id: User ID
        session_id: Session ID
        project_id: Optional project ID
        llm_provider: LLM provider name
    
    Returns:
        Initial ChatState dict
    """
    from datetime import datetime
    
    return ChatState(
        # Messages
        messages=[HumanMessage(content=message)],
        
        # User & Session
        user_id=user_id,
        session_id=session_id,
        project_id=project_id,
        thread_id=session_id,
        
        # Memory (empty initially)
        short_term_context=None,
        long_term_summary=None,
        entity_context=None,
        relevant_memories=None,
        
        # Intent (to be classified)
        intent=None,
        intent_confidence=None,
        
        # RAG (to be retrieved)
        retrieved_documents=None,
        retrieved_chunks=None,
        retrieval_score=None,
        
        # Answer (to be generated)
        draft_answer=None,
        final_answer=None,
        answer_confidence=None,
        
        # Quality (to be evaluated)
        quality_score=None,
        quality_feedback=None,
        needs_regeneration=False,
        
        # Tools
        tool_calls=None,
        tool_results=None,
        
        # Metadata
        llm_provider=llm_provider,
        model_name=None,
        token_count=0,
        processing_time_ms=None,
        
        # Error
        error=None,
        retry_count=0,
        fallback_used=False,
    )
