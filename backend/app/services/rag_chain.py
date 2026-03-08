"""
RAG Chain Service - Retrieval-Augmented Generation using LangChain
"""

from typing import List, Optional, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document

from app.services.llm.langchain_service import LangChainLLMService, get_llm_service
from app.services.vector_store_langchain import get_vector_store_service


# Thai HR Assistant Prompt
HR_RAG_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """คุณเป็นผู้ช่วย HR ที่ตอบคำถามจากเอกสารอย่างแม่นยำและเป็นประโยชน์

**คำแนะนำ:**
1. ตอบคำถามโดยอ้างอิงจากเอกสารที่ให้มาเท่านั้น
2. หากไม่พบข้อมูล ให้บอกว่าไม่พบข้อมูลในเอกสาร
3. ตอบเป็นภาษาไทยที่สุภาพและเข้าใจง่าย
4. หากจำเป็น ให้อ้างอิงหมายเลขเอกสารหรือหัวข้อ

**เอกสารอ้างอิง:**
{context}

**คำถาม:** {question}

**คำตอบ:**"""),
])


class RAGChainService:
    """
    RAG (Retrieval-Augmented Generation) service using LangChain.
    Combines document retrieval with LLM generation.
    """
    
    def __init__(
        self,
        llm_service: Optional[LangChainLLMService] = None,
        collection_name: str = "hr_documents"
    ):
        """
        Initialize RAG chain service.
        
        Args:
            llm_service: LLM service instance
            collection_name: Default collection for retrieval
        """
        self.llm_service = llm_service or get_llm_service()
        self.collection_name = collection_name
        self.vector_store = get_vector_store_service()
        self._chains: Dict[str, Any] = {}
    
    def _format_docs(self, docs: List[Document]) -> str:
        """
        Format documents for context.
        
        Args:
            docs: List of documents
        
        Returns:
            Formatted context string
        """
        formatted = []
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get("source", "Unknown")
            title = doc.metadata.get("title", "")
            content = doc.page_content
            
            header = f"[{i}]"
            if title:
                header += f" {title}"
            if source:
                header += f" (จาก: {source})"
            
            formatted.append(f"{header}\n{content}")
        
        return "\n\n---\n\n".join(formatted)
    
    def create_chain(
        self,
        collection_name: Optional[str] = None,
        k: int = 5,
        prompt_template: Optional[ChatPromptTemplate] = None
    ):
        """
        Create RAG chain.
        
        Args:
            collection_name: Collection to retrieve from
            k: Number of documents to retrieve
            prompt_template: Custom prompt template
        
        Returns:
            LangChain chain
        """
        collection = collection_name or self.collection_name
        prompt = prompt_template or HR_RAG_PROMPT
        
        # Get retriever
        vector_store = self.vector_store.get_vector_store(collection)
        retriever = vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": k}
        )
        
        # Build chain
        chain = (
            {
                "context": retriever | self._format_docs,
                "question": RunnablePassthrough()
            }
            | prompt
            | self.llm_service.llm
            | StrOutputParser()
        )
        
        return chain
    
    async def answer(
        self,
        question: str,
        collection_name: Optional[str] = None,
        k: int = 5,
        return_sources: bool = True
    ) -> Dict[str, Any]:
        """
        Answer question using RAG. Retrieves documents once and reuses them for
        both the LLM context and the returned sources (avoids a duplicate retrieval).

        Args:
            question: User question
            collection_name: Collection to search
            k: Number of documents to retrieve
            return_sources: Include source documents in response

        Returns:
            Answer with optional sources
        """
        collection = collection_name or self.collection_name

        # Single retrieval
        vector_store = self.vector_store.get_vector_store(collection)
        retriever = vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": k}
        )
        docs = await retriever.aget_relevant_documents(question)
        context = self._format_docs(docs)

        # Build answer from already-retrieved context
        answer_chain = (
            HR_RAG_PROMPT
            | self.llm_service.llm
            | StrOutputParser()
        )
        answer_text = await answer_chain.ainvoke({"context": context, "question": question})

        result: Dict[str, Any] = {"answer": answer_text}

        if return_sources:
            result["sources"] = [
                {
                    "content": doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content,
                    "metadata": doc.metadata
                }
                for doc in docs
            ]

        return result
    
    async def answer_with_history(
        self,
        question: str,
        chat_history: List[Dict[str, str]],
        collection_name: Optional[str] = None,
        k: int = 5
    ) -> Dict[str, Any]:
        """
        Answer question with chat history context.
        
        Args:
            question: User question
            chat_history: Previous messages
            collection_name: Collection to search
            k: Number of documents to retrieve
        
        Returns:
            Answer with sources
        """
        from langchain_core.messages import HumanMessage, AIMessage
        
        collection = collection_name or self.collection_name
        
        # Get retriever
        vector_store = self.vector_store.get_vector_store(collection)
        retriever = vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": k}
        )
        
        # Create contextualize question prompt
        contextualize_prompt = ChatPromptTemplate.from_messages([
            ("system", "Given the chat history and the latest user question, reformulate the question to be standalone."),
            ("human", "Chat history:\n{chat_history}\n\nQuestion: {question}")
        ])
        
        # Create answer prompt with history
        answer_prompt = ChatPromptTemplate.from_messages([
            ("system", """คุณเป็นผู้ช่วย HR ที่ตอบคำถามจากเอกสาร

**เอกสารอ้างอิง:**
{context}

**ประวัติการสนทนา:**
{chat_history}"""),
            ("human", "{question}")
        ])
        
        # Format history
        history_text = "\n".join([
            f"{'ผู้ใช้' if msg['role'] == 'user' else 'ผู้ช่วย'}: {msg['content']}"
            for msg in chat_history[-10:]  # Last 10 messages
        ])
        
        # Get documents
        docs = await retriever.aget_relevant_documents(question)
        context = self._format_docs(docs)
        
        # Build messages
        messages = answer_prompt.format_messages(
            context=context,
            chat_history=history_text,
            question=question
        )
        
        # Get answer
        response = await self.llm_service.llm.ainvoke(messages)
        
        return {
            "answer": response.content,
            "sources": [
                {
                    "content": doc.page_content[:200],
                    "metadata": doc.metadata
                }
                for doc in docs
            ]
        }


# Singleton instance
_rag_service: Optional[RAGChainService] = None


def get_rag_service(collection_name: str = "hr_documents") -> RAGChainService:
    """
    Get or create RAG service singleton.
    
    Args:
        collection_name: Default collection name
    
    Returns:
        RAGChainService instance
    """
    global _rag_service
    
    if _rag_service is None:
        _rag_service = RAGChainService(collection_name=collection_name)
    
    return _rag_service
