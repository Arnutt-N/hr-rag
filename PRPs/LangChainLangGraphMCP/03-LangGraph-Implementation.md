# PRP: LangGraph Implementation Guide

## 3. LangGraph Implementation

### 3.1 Core Concepts

LangGraph เป็น library สำหรับสร้าง stateful, multi-agent applications ด้วย graph structure:

- **StateGraph**: Graph ที่มี state ร่วมกัน
- **Nodes**: Functions ที่ทำงานในแต่ละขั้นตอน
- **Edges**: การเชื่อมต่อระหว่าง nodes
- **State**: ข้อมูลที่ส่งผ่านระหว่าง nodes
- **Checkpointer**: บันทึก state สำหรับ resume

### 3.2 Dependencies

```toml
[tool.poetry.dependencies]
langgraph = "^0.2.0"
```

### 3.3 Chat Workflow Graph

```
┌─────────────────────────────────────────────────────────────┐
│                    Chat Workflow Graph                      │
└─────────────────────────────────────────────────────────────┘

                    ┌─────────────┐
                    │    START    │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  classify   │
                    │   intent    │
                    └──────┬──────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
    ┌────────────┐  ┌────────────┐  ┌────────────┐
    │  greeting  │  │  question  │  │   other    │
    └──────┬─────┘  └──────┬─────┘  └──────┬─────┘
           │               │               │
           ▼               ▼               ▼
    ┌────────────┐  ┌────────────┐  ┌────────────┐
    │   reply    │  │   search   │  │  clarify   │
    │  greeting  │  │  knowledge │  │   intent   │
    └──────┬─────┘  └──────┬─────┘  └──────┬─────┘
           │               │               │
           │               ▼               │
           │        ┌────────────┐         │
           │        │  generate  │         │
           │        │   answer   │         │
           │        └──────┬─────┘         │
           │               │               │
           └───────────────┼───────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   evaluate  │
                    │   quality   │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
       ┌──────────┐ ┌──────────┐ ┌──────────┐
       │  good    │ │  medium  │ │   bad    │
       └────┬─────┘ └────┬─────┘ └────┬─────┘
            │            │            │
            ▼            ▼            ▼
       ┌──────────┐ ┌──────────┐ ┌──────────┐
       │  return  │ │  return  │ │ regenerate│
       │  answer  │ │  answer  │ │  + flag   │
       └──────────┘ └──────────┘ └──────────┘
```

### 3.4 State Definition

```python
# backend/app/services/chat_state.py
from typing import TypedDict, List, Optional, Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class ChatState(TypedDict):
    """State for chat workflow"""
    # Messages (automatically appended with add_messages)
    messages: Annotated[List[BaseMessage], add_messages]
    
    # User and session info
    user_id: int
    session_id: int
    project_id: Optional[int]
    
    # Intent classification
    intent: Optional[str]  # "greeting", "question", "other"
    
    # RAG context
    context_documents: List[dict]
    retrieved_chunks: List[str]
    
    # Answer generation
    draft_answer: Optional[str]
    final_answer: Optional[str]
    
    # Quality evaluation
    quality_score: Optional[float]  # 0.0 - 1.0
    needs_regeneration: bool
    
    # Metadata
    llm_provider: str
    token_count: int
    
    # Error handling
    error: Optional[str]
```

### 3.5 Node Functions

```python
# backend/app/services/chat_nodes.py
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI

class ChatNodes:
    """Node functions for chat workflow"""
    
    def __init__(self, llm_service):
        self.llm = llm_service.llm
        self.rag_service = RAGChainService(llm_service)
    
    async def classify_intent(self, state: ChatState) -> ChatState:
        """Classify user intent"""
        last_message = state["messages"][-1].content
        
        prompt = f"""Classify the user intent:
User: {last_message}

Intent (greeting/question/other):"""
        
        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        intent = response.content.strip().lower()
        
        # Normalize intent
        if "greeting" in intent or "สวัสดี" in last_message:
            intent = "greeting"
        elif "question" in intent or "?" in last_message:
            intent = "question"
        else:
            intent = "other"
        
        state["intent"] = intent
        return state
    
    async def handle_greeting(self, state: ChatState) -> ChatState:
        """Handle greeting intent"""
        greetings = [
            "สวัสดีค่ะ! มีอะไรให้ช่วยเหลือเกี่ยวกับนโยบาย HR ไหมคะ?",
            "ยินดีต้อนรับค่ะ! ถามได้เลยนะคะ",
            "สวัสดีค่ะ วันนี้ต้องการค้นหาข้อมูลอะไรคะ?"
        ]
        
        import random
        response = random.choice(greetings)
        
        state["final_answer"] = response
        state["messages"].append(AIMessage(content=response))
        return state
    
    async def search_knowledge(self, state: ChatState) -> ChatState:
        """Search knowledge base"""
        last_message = state["messages"][-1].content
        project_id = state.get("project_id")
        
        # Determine collection name
        collection_name = f"project_{project_id}" if project_id else "knowledge_base"
        
        # Search
        result = await self.rag_service.answer(last_message, collection_name)
        
        state["draft_answer"] = result["answer"]
        state["context_documents"] = result["sources"]
        state["retrieved_chunks"] = [s["content"] for s in result["sources"]]
        
        return state
    
    async def generate_answer(self, state: ChatState) -> ChatState:
        """Generate final answer"""
        # If we already have draft from RAG, use it
        if state.get("draft_answer"):
            state["final_answer"] = state["draft_answer"]
        else:
            # Fallback to direct LLM
            messages = state["messages"]
            response = await self.llm.ainvoke(messages)
            state["final_answer"] = response.content
        
        state["messages"].append(AIMessage(content=state["final_answer"]))
        return state
    
    async def clarify_intent(self, state: ChatState) -> ChatState:
        """Ask for clarification"""
        response = "ขอโทษค่ะ ไม่เข้าใจคำถาม กรุณาถามใหม่หรือให้รายละเอียดเพิ่มเติมได้ไหมคะ?"
        state["final_answer"] = response
        state["messages"].append(AIMessage(content=response))
        return state
    
    async def evaluate_quality(self, state: ChatState) -> ChatState:
        """Evaluate answer quality"""
        answer = state.get("final_answer", "")
        context = state.get("retrieved_chunks", [])
        
        if not context:
            # No context, assume medium quality
            state["quality_score"] = 0.6
            return state
        
        # Simple heuristic evaluation
        score = 0.7  # Base score
        
        # Check if answer uses context
        context_text = " ".join(context)
        overlap = sum(1 for word in answer.split() if word in context_text)
        if overlap > 5:
            score += 0.2
        
        # Check answer length
        if len(answer) > 50:
            score += 0.1
        
        state["quality_score"] = min(score, 1.0)
        state["needs_regeneration"] = score < 0.6
        
        return state
    
    async def regenerate_answer(self, state: ChatState) -> ChatState:
        """Regenerate with better prompting"""
        last_message = state["messages"][-2].content  # User message
        context = "\n".join(state.get("retrieved_chunks", []))
        
        prompt = f"""Based on the following context, provide a detailed answer:

Context:
{context}

Question: {last_message}

Please provide a comprehensive answer in Thai:"""
        
        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        state["final_answer"] = response.content
        
        # Update last message
        state["messages"][-1] = AIMessage(content=state["final_answer"])
        return state
```

### 3.6 Graph Construction

```python
# backend/app/services/chat_graph.py
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.redis import RedisSaver

class ChatGraphService:
    """Chat workflow using LangGraph"""
    
    def __init__(self, llm_service, redis_url: str):
        self.nodes = ChatNodes(llm_service)
        self.checkpointer = RedisSaver(redis_url)
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """Build the chat workflow graph"""
        # Initialize graph
        workflow = StateGraph(ChatState)
        
        # Add nodes
        workflow.add_node("classify", self.nodes.classify_intent)
        workflow.add_node("greeting", self.nodes.handle_greeting)
        workflow.add_node("search", self.nodes.search_knowledge)
        workflow.add_node("generate", self.nodes.generate_answer)
        workflow.add_node("clarify", self.nodes.clarify_intent)
        workflow.add_node("evaluate", self.nodes.evaluate_quality)
        workflow.add_node("regenerate", self.nodes.regenerate_answer)
        
        # Add edges
        workflow.set_entry_point("classify")
        
        # Conditional edges from classify
        workflow.add_conditional_edges(
            "classify",
            self._route_by_intent,
            {
                "greeting": "greeting",
                "question": "search",
                "other": "clarify"
            }
        )
        
        # Greeting -> END
        workflow.add_edge("greeting", END)
        
        # Search -> Generate
        workflow.add_edge("search", "generate")
        
        # Generate -> Evaluate
        workflow.add_edge("generate", "evaluate")
        
        # Clarify -> END
        workflow.add_edge("clarify", END)
        
        # Evaluate -> conditional
        workflow.add_conditional_edges(
            "evaluate",
            self._route_by_quality,
            {
                "good": END,
                "regenerate": "regenerate"
            }
        )
        
        # Regenerate -> END
        workflow.add_edge("regenerate", END)
        
        # Compile with checkpointer
        return workflow.compile(checkpointer=self.checkpointer)
    
    def _route_by_intent(self, state: ChatState) -> str:
        """Route based on intent"""
        return state.get("intent", "other")
    
    def _route_by_quality(self, state: ChatState) -> str:
        """Route based on quality score"""
        if state.get("needs_regeneration"):
            return "regenerate"
        return "good"
    
    async def chat(
        self,
        message: str,
        user_id: int,
        session_id: int,
        project_id: Optional[int] = None,
        thread_id: Optional[str] = None
    ) -> dict:
        """Process chat message through graph"""
        
        # Initial state
        initial_state = ChatState(
            messages=[HumanMessage(content=message)],
            user_id=user_id,
            session_id=session_id,
            project_id=project_id,
            intent=None,
            context_documents=[],
            retrieved_chunks=[],
            draft_answer=None,
            final_answer=None,
            quality_score=None,
            needs_regeneration=False,
            llm_provider="openai",
            token_count=0,
            error=None
        )
        
        # Config with thread_id for persistence
        config = {
            "configurable": {"thread_id": thread_id or str(session_id)}
        }
        
        # Run graph
        result = await self.graph.ainvoke(initial_state, config)
        
        return {
            "answer": result.get("final_answer"),
            "sources": result.get("context_documents", []),
            "quality_score": result.get("quality_score"),
            "intent": result.get("intent"),
            "thread_id": config["configurable"]["thread_id"]
        }
```

### 3.7 Human-in-the-Loop

```python
# backend/app/services/chat_graph.py (continued)

async def request_human_review(self, state: ChatState) -> ChatState:
    """Pause for human review"""
    state["waiting_for_human"] = True
    return state

# In graph construction:
workflow.add_node("human_review", self.request_human_review)

# Interrupt before human_review
workflow.add_edge("evaluate", "human_review")
workflow.add_edge("human_review", END)

# Usage with interrupt:
result = await self.graph.ainvoke(
    initial_state,
    config,
    interrupt_before=["human_review"]
)

# Resume later:
result = await self.graph.ainvoke(
    None,  # Continue from last state
    config
)
```

### 3.8 Multi-Agent Workflow

```python
# backend/app/services/multi_agent_graph.py
from typing import Literal

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    next_agent: Literal["researcher", "writer", "reviewer", "end"]
    research_notes: str
    draft: str
    feedback: str

class MultiAgentService:
    """Multi-agent workflow for complex tasks"""
    
    def __init__(self):
        self.researcher = ChatOpenAI(model="gpt-4")
        self.writer = ChatOpenAI(model="gpt-4")
        self.reviewer = ChatOpenAI(model="gpt-4")
    
    async def research_node(self, state: AgentState) -> AgentState:
        """Research agent - search for information"""
        query = state["messages"][-1].content
        
        # Search knowledge base
        results = await search_knowledge_base(query)
        
        state["research_notes"] = format_results(results)
        state["next_agent"] = "writer"
        return state
    
    async def writer_node(self, state: AgentState) -> AgentState:
        """Writer agent - draft response"""
        prompt = f"""Based on these research notes:
{state['research_notes']}

Draft a comprehensive answer:"""
        
        response = await self.writer.ainvoke([HumanMessage(content=prompt)])
        state["draft"] = response.content
        state["next_agent"] = "reviewer"
        return state
    
    async def reviewer_node(self, state: AgentState) -> AgentState:
        """Reviewer agent - check quality"""
        prompt = f"""Review this draft:
{state['draft']}

Is it good enough? (yes/no)"""
        
        response = await self.reviewer.ainvoke([HumanMessage(content=prompt)])
        
        if "yes" in response.content.lower():
            state["next_agent"] = "end"
            state["messages"].append(AIMessage(content=state["draft"]))
        else:
            state["next_agent"] = "writer"
            state["feedback"] = response.content
        
        return state
    
    def build_graph(self):
        """Build multi-agent graph"""
        workflow = StateGraph(AgentState)
        
        workflow.add_node("researcher", self.research_node)
        workflow.add_node("writer", self.writer_node)
        workflow.add_node("reviewer", self.reviewer_node)
        
        workflow.set_entry_point("researcher")
        
        # Dynamic routing
        workflow.add_conditional_edges(
            "researcher",
            lambda s: s["next_agent"],
            {"writer": "writer"}
        )
        workflow.add_conditional_edges(
            "writer",
            lambda s: s["next_agent"],
            {"reviewer": "reviewer"}
        )
        workflow.add_conditional_edges(
            "reviewer",
            lambda s: s["next_agent"],
            {"writer": "writer", "end": END}
        )
        
        return workflow.compile()
```

### 3.9 Migration Steps

1. **Install LangGraph**
   ```bash
   poetry add langgraph
   ```

2. **Create State Models**
   - Define `ChatState` TypedDict
   - Define message types

3. **Implement Node Functions**
   - Create `ChatNodes` class
   - Implement each node

4. **Build Graph**
   - Define workflow
   - Add conditional edges
   - Compile with checkpointer

5. **Replace Chat Endpoints**
   - Update `/chat` endpoint
   - Add streaming support

6. **Add Persistence**
   - Setup Redis checkpointer
   - Test resume functionality

### 3.10 Benefits

- **Visibility**: Graph structure แสดง workflow ชัดเจน
- **Debugging**: ตรวจสอบ state ในแต่ละ step ได้
- **Flexibility**: ง่ายต่อการเพิ่ม/ลบ nodes
- **Persistence**: Resume conversation ได้
- **Human-in-the-loop**: รองรับการ interrupt

---

*Next: [04-FastMCP-Integration.md](04-FastMCP-Integration.md)*