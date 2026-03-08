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
- [ ] Review Completed
- [ ] Approved
- [ ] Implementation Started

---

*Created: 2026-03-08*
*Author: Lita (AI Assistant)*