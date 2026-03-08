# PRP: Migration Plan and Timeline

## 5. Migration Plan

### 5.1 Overview

การย้ายระบบ HR-RAG ไปใช้ LangChain + LangGraph + FastMCP แบ่งเป็น 5 phases:

| Phase | Duration | Focus |
|-------|----------|-------|
| 1 | Week 1 | Preparation |
| 2 | Week 2-3 | LangChain Integration |
| 3 | Week 3-4 | LangGraph Workflow |
| 4 | Week 4-5 | FastMCP Server |
| 5 | Week 5-6 | Testing & Deployment |

### 5.2 Phase 1: Preparation (Week 1)

#### Day 1-2: Environment Setup
- [ ] Create feature branch: `feature/langchain-refactor`
- [ ] Update `pyproject.toml` with new dependencies
- [ ] Setup development environment
- [ ] Run existing tests to establish baseline

```toml
# Add to pyproject.toml
[tool.poetry.dependencies]
langchain = "^0.3.0"
langchain-community = "^0.3.0"
langchain-openai = "^0.2.0"
langchain-anthropic = "^0.2.0"
langchain-qdrant = "^0.2.0"
langgraph = "^0.2.0"
fastmcp = "^0.4.0"
mcp = "^1.0.0"
```

#### Day 3-4: Architecture Review
- [ ] Review current codebase
- [ ] Identify integration points
- [ ] Document breaking changes
- [ ] Create rollback plan

#### Day 5: Team Alignment
- [ ] Share PRP documents with team
- [ ] Assign tasks
- [ ] Setup daily standup

**Deliverables:**
- Feature branch ready
- Updated dependencies
- Architecture decision records (ADRs)

### 5.3 Phase 2: LangChain Integration (Week 2-3)

#### Week 2: Core Services

**Day 1-2: LLM Service**
```python
# Create: backend/app/services/llm/langchain_service.py
# - LangChainLLMService class
# - Support multiple providers
# - Async support
```
- [ ] Implement `LangChainLLMService`
- [ ] Add provider factory
- [ ] Write unit tests

**Day 3-4: Document Processing**
```python
# Create: backend/app/services/document_loaders.py
# Create: backend/app/services/text_splitters.py
```
- [ ] Implement document loaders
- [ ] Implement text splitters
- [ ] Test with sample documents

**Day 5: Embeddings & Vector Store**
```python
# Create: backend/app/services/embeddings_langchain.py
# Create: backend/app/services/vector_store_langchain.py
```
- [ ] Implement embeddings service
- [ ] Implement vector store service
- [ ] Test Qdrant integration

#### Week 3: RAG Pipeline

**Day 1-2: RAG Chain**
```python
# Create: backend/app/services/rag_chain.py
```
- [ ] Implement RAGChainService
- [ ] Add retrievers
- [ ] Test end-to-end

**Day 3-4: Integration**
- [ ] Replace existing LLM calls
- [ ] Update document upload flow
- [ ] Update search endpoints

**Day 5: Testing**
- [ ] Unit tests: ≥80% coverage
- [ ] Integration tests
- [ ] Performance benchmarks

**Deliverables:**
- All LangChain services implemented
- Tests passing
- Performance baseline

### 5.4 Phase 3: LangGraph Workflow (Week 3-4)

#### Week 3: Graph Implementation

**Day 1-2: State Management**
```python
# Create: backend/app/services/chat_state.py
# Create: backend/app/services/chat_nodes.py
```
- [ ] Define ChatState
- [ ] Implement node functions
- [ ] Add type hints

**Day 3-4: Graph Construction**
```python
# Create: backend/app/services/chat_graph.py
```
- [ ] Build StateGraph
- [ ] Add conditional edges
- [ ] Setup Redis checkpointer

**Day 5: Integration**
- [ ] Replace chat endpoints
- [ ] Add streaming support
- [ ] Test workflows

#### Week 4: Advanced Features

**Day 1-2: Human-in-the-Loop**
- [ ] Implement interrupt points
- [ ] Add resume functionality
- [ ] Test edge cases

**Day 3-4: Multi-Agent (Optional)**
- [ ] Implement multi-agent graph
- [ ] Add agent routing
- [ ] Test complex workflows

**Day 5: Testing**
- [ ] Graph unit tests
- [ ] Integration tests
- [ ] Load testing

**Deliverables:**
- LangGraph workflow working
- State persistence
- All chat features migrated

### 5.5 Phase 4: FastMCP Server (Week 4-5)

#### Week 4: MCP Server

**Day 1-2: Server Setup**
```python
# Create: backend/app/mcp/server.py
```
- [ ] Create FastMCP server
- [ ] Add lifespan management
- [ ] Setup authentication

**Day 3-4: Tools Implementation**
- [ ] `search_knowledge_base`
- [ ] `get_document_by_id`
- [ ] `list_categories`
- [ ] `get_user_info`
- [ ] `get_analytics_summary`

**Day 5: Resources & Prompts**
- [ ] Add MCP resources
- [ ] Create prompts
- [ ] Test server

#### Week 5: Integration

**Day 1-2: MCP Client**
```python
# Create: backend/app/services/mcp_client.py
```
- [ ] Create MCP client service
- [ ] Integrate with LangChain
- [ ] Test tool calling

**Day 3-4: LangGraph + MCP**
- [ ] Add MCP tools to graph
- [ ] Test agent with tools
- [ ] Optimize performance

**Day 5: Testing**
- [ ] MCP server tests
- [ ] Integration tests
- [ ] Security tests

**Deliverables:**
- MCP server running
- Tools exposed
- Client integration working

### 5.6 Phase 5: Testing & Deployment (Week 5-6)

#### Week 5: Testing

**Day 1-2: Unit Tests**
- [ ] All services: ≥80% coverage
- [ ] Edge cases
- [ ] Error handling

**Day 3-4: Integration Tests**
- [ ] End-to-end workflows
- [ ] API contract tests
- [ ] Performance tests

**Day 5: Security Audit**
- [ ] Dependency check
- [ ] Vulnerability scan
- [ ] Penetration testing

#### Week 6: Deployment

**Day 1-2: Staging**
- [ ] Deploy to staging
- [ ] Run smoke tests
- [ ] Monitor metrics

**Day 3-4: Production**
- [ ] Blue-green deployment
- [ ] Gradual traffic shift
- [ ] Monitor errors

**Day 5: Post-Deployment**
- [ ] Monitor for 24 hours
- [ ] Collect feedback
- [ ] Document issues

**Deliverables:**
- Production deployment
- Monitoring dashboards
- Incident response plan

### 5.7 Resource Requirements

#### Personnel
| Role | Count | Duration |
|------|-------|----------|
| Backend Lead | 1 | Full duration |
| Backend Dev | 2 | Phase 2-5 |
| DevOps | 1 | Phase 5 |
| QA | 1 | Phase 3-5 |

#### Infrastructure
- Staging environment
- Feature flags system
- Monitoring (Prometheus/Grafana)
- Log aggregation

### 5.8 Risk Management

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Performance regression | Medium | High | Benchmark before/after, optimize |
| Breaking changes | Medium | High | Feature flags, gradual rollout |
| Dependency conflicts | Low | Medium | Pin versions, test thoroughly |
| Learning curve | Medium | Low | Training, pair programming |
| Scope creep | High | Medium | Strict sprint planning |

### 5.9 Rollback Strategy

1. **Feature Flags**: สามารถ disable features ได้ทันที
2. **Blue-Green Deployment**: Switch traffic กลับได้ใน 5 นาที
3. **Database**: No breaking schema changes
4. **Monitoring**: Alerts สำหรับ error rate > 1%

### 5.10 Success Criteria

- [ ] All existing features work
- [ ] Response time ≤ 120% of baseline
- [ ] Error rate < 0.1%
- [ ] Code coverage ≥ 80%
- [ ] Documentation complete
- [ ] Zero downtime deployment
- [ ] Team trained on new stack

### 5.11 Timeline Summary

```
Week 1:  [====] Preparation
Week 2:  [========] LangChain Core
Week 3:  [========] LangChain RAG + LangGraph Start
Week 4:  [========] LangGraph + MCP Start
Week 5:  [========] MCP + Testing
Week 6:  [========] Testing + Deployment
```

### 5.12 Checklist

#### Pre-Migration
- [ ] Backup database
- [ ] Document current state
- [ ] Notify stakeholders
- [ ] Schedule maintenance window

#### During Migration
- [ ] Monitor error rates
- [ ] Check response times
- [ ] Validate data integrity
- [ ] Keep rollback ready

#### Post-Migration
- [ ] Run full test suite
- [ ] Update documentation
- [ ] Train team
- [ ] Collect feedback

---

**End of PRP Documents**

*For questions or updates, contact the development team.*