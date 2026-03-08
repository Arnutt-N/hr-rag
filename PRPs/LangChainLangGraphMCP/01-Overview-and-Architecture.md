# PRP: HR-RAG Refactor to LangChain + LangGraph + FastMCP

## 1. Overview and Architecture

### 1.1 Current Architecture

HR-RAG ปัจจุบันใช้สถาปัตยกรรมแบบตรง:

```
┌─────────────────────────────────────────────────────────────┐
│                    Current HR-RAG Architecture              │
└─────────────────────────────────────────────────────────────┘

Frontend (Next.js) 
        │
        ▼
FastAPI Backend
        │
        ├──► Direct LLM API Calls (OpenAI, Anthropic, etc.)
        │
        ├──► Qdrant (Vector DB) - direct client
        │
        ├──► TiDB Cloud (SQL DB) - SQLAlchemy
        │
        └──► Redis (Cache)
```

**ข้อดีของปัจจุบัน:**
- เรียบง่าย ควบคุมได้เต็มที่
- ไม่มี abstraction layer ที่ซับซ้อน
- Performance ดี (ไม่มี overhead จาก framework)

**ข้อเสียของปัจจุบัน:**
- ยากต่อการขยาย (adding new LLM providers)
- ไม่มี standard pattern สำหรับ RAG
- จัดการ state ของ conversation ยาก
- ไม่มี modular tool system

### 1.2 Proposed Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              Proposed HR-RAG Architecture                   │
└─────────────────────────────────────────────────────────────┘

Frontend (Next.js)
        │
        ▼
FastAPI Backend
        │
        ├──► LangGraph Workflow Engine
        │         │
        │         ├──► LangChain RAG Chain
        │         │         ├──► Document Loaders
        │         │         ├──► Text Splitters
        │         │         ├──► Embeddings
        │         │         └──► Vector Store (Qdrant)
        │         │
        │         ├──► LLM Models (via LangChain)
        │         │         ├──► OpenAI
        │         │         ├──► Anthropic
        │         │         └──► etc.
        │         │
        │         └──► State Management (Redis)
        │
        ├──► FastMCP Server
        │         ├──► Tool: search_documents
        │         ├──► Tool: query_knowledge_base
        │         ├──► Tool: user_management
        │         └──► Tool: analytics
        │
        ├──► TiDB Cloud (SQL DB)
        │
        └──► Redis (Cache + State)
```

### 1.3 Why LangChain + LangGraph + FastMCP?

#### LangChain
- **Standardized RAG Pattern**: มี built-in RAG chain ที่ tested และ optimized
- **Document Loaders**: รองรับหลาย format (PDF, DOCX, TXT, etc.) โดยไม่ต้องเขียนเอง
- **Text Splitters**: มีหลาย strategy (Recursive, Token, etc.)
- **Embeddings**: Unified interface สำหรับหลาย providers
- **Vector Stores**: รองรับ Qdrant, Chroma, Pinecone, etc.
- **Retrievers**: Multi-query, contextual compression, etc.

#### LangGraph
- **State Management**: จัดการ state ของ conversation ได้ดี
- **Workflow as Graph**: แสดง chat flow เป็น graph ที่เข้าใจง่าย
- **Conditional Routing**: สามารถ route ไปตามเงื่อนไขได้
- **Human-in-the-loop**: รองรับการ interrupt และ resume
- **Persistence**: State persistence กับ Redis/Checkpoint

#### FastMCP
- **Tool Standardization**: มาตรฐานเดียวสำหรับ exposing tools
- **Modularity**: แยก tools ออกเป็น独立 modules
- **Security**: Built-in security model
- **Interoperability**: ใช้กับหลาย clients ได้

### 1.4 Key Components

| Component | Technology | Responsibility |
|-----------|------------|----------------|
| API Layer | FastAPI | HTTP endpoints, auth, validation |
| Workflow Engine | LangGraph | Chat flow, state management |
| RAG Pipeline | LangChain | Document processing, retrieval |
| Tool Server | FastMCP | Expose tools to LLM |
| Vector DB | Qdrant | Document embeddings |
| SQL DB | TiDB Cloud | User data, metadata |
| Cache | Redis | Session, cache, state |

### 1.5 Migration Strategy

**Phase 1: Preparation** (Week 1)
- Setup development environment
- Add dependencies (langchain, langgraph, mcp)
- Create feature branch

**Phase 2: LangChain Integration** (Week 2-3)
- Refactor LLM services
- Implement document loaders
- Setup embeddings
- Migrate vector store to LangChain interface

**Phase 3: LangGraph Workflow** (Week 3-4)
- Design chat workflow graph
- Implement state management
- Migrate chat endpoints

**Phase 4: FastMCP Server** (Week 4-5)
- Setup MCP server
- Expose existing tools
- Integrate with LangGraph

**Phase 5: Testing & Deployment** (Week 5-6)
- Unit tests
- Integration tests
- Performance tests
- Deploy to staging
- Deploy to production

### 1.6 Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Performance degradation | High | Benchmark ก่อน/หลัง, optimize chain |
| Breaking changes | High | Feature flags, gradual rollout |
| Learning curve | Medium | Training, documentation |
| Dependency bloat | Medium | Use only necessary components |

### 1.7 Success Criteria

- [ ] All existing features work
- [ ] Response time ≤ 120% of current
- [ ] Code coverage ≥ 80%
- [ ] Documentation complete
- [ ] Zero downtime migration

---

*Next: [02-LangChain-Integration.md](02-LangChain-Integration.md)*