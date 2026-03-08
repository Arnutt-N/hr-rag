# PRP: LangChain Integration Guide

## 2. LangChain Integration

### 2.1 Core Concepts

LangChain เป็น framework สำหรับสร้าง applications ที่ใช้ LLM โดยมี components หลัก:

- **Models**: Interface สำหรับ LLM (OpenAI, Anthropic, etc.)
- **Prompts**: Template สำหรับสร้าง prompts
- **Chains**: Sequence ของ calls (LLM, tools, data)
- **Document Loaders**: โหลดเอกสารจากหลาย sources
- **Text Splitters**: แบ่งเอกสารเป็น chunks
- **Embeddings**: แปลง text เป็น vectors
- **Vector Stores**: เก็บและค้นหา vectors
- **Retrievers**: ดึงข้อมูลที่เกี่ยวข้อง

### 2.2 Dependencies

```toml
# pyproject.toml
[tool.poetry.dependencies]
langchain = "^0.3.0"
langchain-community = "^0.3.0"
langchain-openai = "^0.2.0"
langchain-anthropic = "^0.2.0"
langchain-qdrant = "^0.2.0"
langchain-redis = "^0.1.0"

# Document loaders
pypdf = "^5.0.0"
python-docx = "^1.1.0"
unstructured = "^0.16.0"

# Embeddings
sentence-transformers = "^3.0.0"
```

### 2.3 LLM Service Refactor

#### Current Implementation
```python
# Current: backend/app/services/llm/openai.py
class OpenAIService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
    
    async def chat(self, messages: List[dict], **kwargs) -> str:
        response = await self.client.chat.completions.create(
            model="gpt-4",
            messages=messages
        )
        return response.choices[0].message.content
```

#### New Implementation with LangChain
```python
# New: backend/app/services/llm/langchain_service.py
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

class LangChainLLMService:
    def __init__(self, provider: str = "openai"):
        self.provider = provider
        self.llm = self._get_llm(provider)
    
    def _get_llm(self, provider: str):
        providers = {
            "openai": ChatOpenAI(
                model="gpt-4",
                temperature=0.7,
                api_key=settings.openai_api_key
            ),
            "anthropic": ChatAnthropic(
                model="claude-3-sonnet-20240229",
                temperature=0.7,
                api_key=settings.anthropic_api_key
            ),
            "kimi": ChatOpenAI(
                model="kimi-k2.5",
                base_url="https://api.moonshot.cn/v1",
                api_key=settings.kimi_api_key
            ),
            # Add more providers...
        }
        return providers.get(provider)
    
    async def chat(self, messages: List[dict], **kwargs) -> str:
        # Convert to LangChain message format
        lc_messages = []
        for msg in messages:
            if msg["role"] == "user":
                lc_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                lc_messages.append(AIMessage(content=msg["content"]))
            elif msg["role"] == "system":
                lc_messages.append(SystemMessage(content=msg["content"]))
        
        response = await self.llm.ainvoke(lc_messages)
        return response.content
```

### 2.4 Document Loaders

```python
# backend/app/services/document_loaders.py
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    UnstructuredFileLoader
)
from langchain_core.documents import Document

class DocumentLoaderService:
    """Load documents using LangChain loaders"""
    
    def __init__(self):
        self.loaders = {
            "pdf": PyPDFLoader,
            "docx": Docx2txtLoader,
            "txt": TextLoader,
            "md": TextLoader,
        }
    
    async def load(self, file_path: str, file_type: str) -> List[Document]:
        """Load document and return LangChain Document objects"""
        loader_class = self.loaders.get(file_type, UnstructuredFileLoader)
        loader = loader_class(file_path)
        
        # Load with async support
        documents = await loader.aload()
        
        # Add metadata
        for doc in documents:
            doc.metadata.update({
                "source": file_path,
                "file_type": file_type,
                "loaded_at": datetime.utcnow().isoformat()
            })
        
        return documents
```

### 2.5 Text Splitters

```python
# backend/app/services/text_splitters.py
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    TokenTextSplitter,
    MarkdownTextSplitter
)

class TextSplitterService:
    """Split documents into chunks"""
    
    def __init__(self, strategy: str = "recursive"):
        self.splitters = {
            "recursive": RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=50,
                separators=["\n\n", "\n", ".", " ", ""]
            ),
            "token": TokenTextSplitter(
                chunk_size=500,
                chunk_overlap=50
            ),
            "markdown": MarkdownTextSplitter(
                chunk_size=500,
                chunk_overlap=50
            )
        }
        self.splitter = self.splitters.get(strategy, self.splitters["recursive"])
    
    def split(self, documents: List[Document]) -> List[Document]:
        """Split documents into chunks"""
        return self.splitter.split_documents(documents)
```

### 2.6 Embeddings

```python
# backend/app/services/embeddings_langchain.py
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings

class LangChainEmbeddingService:
    """Embeddings using LangChain"""
    
    def __init__(self, provider: str = "openai"):
        self.provider = provider
        self.embeddings = self._get_embeddings(provider)
    
    def _get_embeddings(self, provider: str):
        if provider == "openai":
            return OpenAIEmbeddings(
                model="text-embedding-3-small",
                api_key=settings.openai_api_key
            )
        elif provider == "huggingface":
            return HuggingFaceEmbeddings(
                model_name="BAAI/bge-m3"  # Thai multilingual
            )
        # Add more providers...
    
    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple documents"""
        return await self.embeddings.aembed_documents(texts)
    
    async def embed_query(self, text: str) -> List[float]:
        """Embed a single query"""
        return await self.embeddings.aembed_query(text)
```

### 2.7 Vector Store (Qdrant)

```python
# backend/app/services/vector_store_langchain.py
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

class LangChainVectorStoreService:
    """Vector store using LangChain Qdrant integration"""
    
    def __init__(self):
        self.client = QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port
        )
        self.embeddings = LangChainEmbeddingService()
    
    def get_vector_store(self, collection_name: str):
        """Get LangChain vector store instance"""
        return QdrantVectorStore(
            client=self.client,
            collection_name=collection_name,
            embedding=self.embeddings.embeddings
        )
    
    async def add_documents(
        self, 
        collection_name: str, 
        documents: List[Document]
    ) -> List[str]:
        """Add documents to vector store"""
        vector_store = self.get_vector_store(collection_name)
        return await vector_store.aadd_documents(documents)
    
    async def similarity_search(
        self,
        collection_name: str,
        query: str,
        k: int = 5,
        filter_dict: Optional[dict] = None
    ) -> List[Document]:
        """Search similar documents"""
        vector_store = self.get_vector_store(collection_name)
        return await vector_store.asimilarity_search(
            query=query,
            k=k,
            filter=filter_dict
        )
```

### 2.8 RAG Chain

```python
# backend/app/services/rag_chain.py
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

class RAGChainService:
    """RAG chain for question answering"""
    
    def __init__(self, llm_service: LangChainLLMService):
        self.llm = llm_service.llm
        self.vector_store = LangChainVectorStoreService()
        self.prompt = self._create_prompt()
    
    def _create_prompt(self):
        template = """คุณเป็นผู้ช่วย HR ที่ตอบคำถามจากเอกสารต่อไปนี้:

Context:
{context}

คำถาม: {question}

คำตอบ:"""
        return ChatPromptTemplate.from_template(template)
    
    def create_chain(self, collection_name: str):
        """Create RAG chain"""
        # Retriever
        vector_store = self.vector_store.get_vector_store(collection_name)
        retriever = vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 5}
        )
        
        # Chain
        chain = (
            {
                "context": retriever | self._format_docs,
                "question": RunnablePassthrough()
            }
            | self.prompt
            | self.llm
            | StrOutputParser()
        )
        
        return chain
    
    def _format_docs(self, docs: List[Document]) -> str:
        """Format documents for context"""
        return "\n\n".join(doc.page_content for doc in docs)
    
    async def answer(self, question: str, collection_name: str) -> dict:
        """Answer question using RAG"""
        chain = self.create_chain(collection_name)
        
        # Get answer
        answer = await chain.ainvoke(question)
        
        # Get source documents
        vector_store = self.vector_store.get_vector_store(collection_name)
        sources = await vector_store.asimilarity_search(question, k=5)
        
        return {
            "answer": answer,
            "sources": [
                {
                    "content": doc.page_content[:200],
                    "metadata": doc.metadata
                }
                for doc in sources
            ]
        }
```

### 2.9 Migration Steps

1. **Add Dependencies**
   ```bash
   poetry add langchain langchain-community langchain-openai langchain-qdrant
   ```

2. **Create New Services**
   - `langchain_service.py` - LLM wrapper
   - `document_loaders.py` - Document loading
   - `text_splitters.py` - Text splitting
   - `embeddings_langchain.py` - Embeddings
   - `vector_store_langchain.py` - Vector store
   - `rag_chain.py` - RAG pipeline

3. **Refactor Existing Code**
   - Replace direct API calls with LangChain
   - Update document processing flow
   - Migrate vector operations

4. **Testing**
   - Unit tests for each service
   - Integration tests for RAG chain
   - Performance benchmarks

### 2.10 Code Example: Full RAG Pipeline

```python
# Example usage
async def process_document(file_path: str, collection_name: str):
    # 1. Load document
    loader = DocumentLoaderService()
    documents = await loader.load(file_path, "pdf")
    
    # 2. Split into chunks
    splitter = TextSplitterService(strategy="recursive")
    chunks = splitter.split(documents)
    
    # 3. Add to vector store
    vector_store = LangChainVectorStoreService()
    vector_ids = await vector_store.add_documents(collection_name, chunks)
    
    return vector_ids

async def ask_question(question: str, collection_name: str):
    # 4. Create RAG chain
    llm_service = LangChainLLMService(provider="openai")
    rag = RAGChainService(llm_service)
    
    # 5. Get answer
    result = await rag.answer(question, collection_name)
    return result
```

---

*Next: [03-LangGraph-Implementation.md](03-LangGraph-Implementation.md)*