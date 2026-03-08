# PRP: HR-RAG Refactor to LangChain + LangGraph + FastMCP

## 📋 Project Requirements Proposal

เอกสารชุดนี้เป็นแผนการ refactor HR-RAG ให้ใช้งาน:
- **LangChain** - RAG pipeline และ LLM integration
- **LangGraph** - Chat workflow และ state management
- **FastMCP** - Tool server สำหรับ modular capabilities

## 📁 Documents

| # | Document | Description |
|---|----------|-------------|
| 1 | [01-Overview-and-Architecture.md](01-Overview-and-Architecture.md) | ภาพรวม architecture ปัจจุบันและที่ต้องการ |
| 2 | [02-LangChain-Integration.md](02-LangChain-Integration.md) | คู่มือ integration LangChain |
| 3 | [03-LangGraph-Implementation.md](03-LangGraph-Implementation.md) | คู่มือ implementation LangGraph |
| 4 | [04-FastMCP-Integration.md](04-FastMCP-Integration.md) | คู่มือ integration FastMCP |
| 5 | [05-Migration-Plan.md](05-Migration-Plan.md) | แผนการย้ายระบบและ timeline |
| 6 | [06-Memory-Management.md](06-Memory-Management.md) | Memory Management (Short-term, Long-term, Entity) |
| 7 | [07-Tools-and-Agents.md](07-Tools-and-Agents.md) | **🆕** Function Calling, Tool Registry, A2A, Orchestration |
| 8 | [REFERENCES.md](REFERENCES.md) | เอกสารอ้างอิงและลิงก์สำคัญ (Updated 2026-03-08) |

## 🎯 Goals

1. **Standardization**: ใช้ LangChain pattern สำหรับ RAG
2. **Maintainability**: Code ที่อ่านง่ายและ maintain ได้
3. **Extensibility**: ง่ายต่อการเพิ่ม features ใหม่
4. **Performance**: รักษา performance หรือดีกว่าเดิม

## ⏱️ Timeline

- **Total Duration**: 6 weeks
- **Start Date**: TBD
- **End Date**: TBD

## 👥 Team

- Backend Lead
- Backend Developers (2)
- DevOps
- QA

## 📊 Status

- [x] PRP Documents Created
- [x] Research Completed (2026-03-08)
- [ ] Review Completed
- [ ] Approved
- [ ] Implementation Started

---

## 🔄 Updates

### 2026-03-08: Research Update

ได้ทำการค้นคว้าเอกสารล่าสุดและอัพเดท PRP:

| Component | เวอร์ชันเดิม | เวอร์ชันใหม่ | แหล่งอ้างอิง |
|-----------|------------|-------------|--------------|
| LangChain | ^0.3.0 | ^0.3.20 | [Official Docs](https://docs.langchain.com/oss/python/langchain/quickstart) |
| LangGraph | ^0.2.0 | ^0.3.0 | [Overview](https://docs.langchain.com/oss/python/langgraph/overview) |
| FastMCP | ^0.4.0 | ^2.0.0 | [FastMCP 2.0](https://gofastmcp.com/v2/getting-started/welcome) |

**⚠️ สิ่งสำคัญ:**
- FastMCP 2.0 มี breaking changes ที่สำคัญ - ต้องอ่าน migration guide
- LangGraph 0.3.x มีฟีเจอร์ `interrupt` และ `Command` ใหม่สำหรับ human-in-the-loop
- **แนะนำให้ใช้ `uv` แทน `poetry`/`pip`** สำหรับการติดตั้ง dependencies (เร็วกว่ามาก)
- **🆕 Memory Management** เพิ่มแล้วใน `06-Memory-Management.md` - ครอบคลุม Short-term, Long-term, Entity Memory
- **🆕 Tools & Agents** เพิ่มแล้วใน `07-Tools-and-Agents.md` - Function Calling, Tool Registry, A2A, Orchestration Patterns

**Research Files:**
- `/data/Organization/ToppLab/research/LangChainLangGraphMCP/` มีเอกสารอ้างอิงจาก Tavily และ Serper

---

*Created: 2026-03-08*
*Updated: 2026-03-08*
*Author: Lita (AI Assistant)*