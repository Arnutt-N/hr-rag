# คู่มือ Chroma Vector DB

## ภาพรวม
Chroma เป็น open-source vector database สำหรับ AI applications มีทั้งแบบ local (in-memory) และ client-server

## ติดตั้ง

### Python
```bash
pip install chromadb
```

### Node.js
```bash
npm install chromadb
```

## การใช้งาน

### 1. Local Mode (ไม่ต้อง deploy server)

```python
# นำเข้า Chroma client
import chromadb
from chromadb.config import Settings

# In-memory database (ข้อมูลจะหายเมื่อปิด program)
client = chromadb.Client()

# หรือ persistent (เก็บไว้ใน disk)
client = chromadb.PersistentClient(path="./chroma_data")
```

### 2. Client-Server Mode

**Run Server:**
```bash
# Pull Docker image ล่าสุด
docker pull chromadb/chroma:latest

# Run server บน port 8000
docker run -p 8000:8000 chromadb/chroma
```

**เชื่อมต่อจาก Client:**
```python
# นำเข้า Chroma
import chromadb

# เชื่อมต่อไปยัง server
client = chromadb.HttpClient(host="localhost", port=8000)
```

## การสร้าง Collection

```python
# สร้าง collection ใหม่
collection = client.create_collection(
    name="hr_documents",
    metadata={"description": "HR documents for RAG"}
)

# หรือ get existing collection
collection = client.get_collection("hr_documents")

# ลบ collection
client.delete_collection("hr_documents")
```

## เพิ่ม Documents

```python
# เพิ่ม documents เข้า collection
collection.add(
    documents=[
        "นโยบายการลาหยุดประจำปี...",
        "ขั้นตอนการขอเบิกค่ารักษาพยาบาล...",
        "ระเบียบการจ่ายโบนัส..."
    ],
    ids=["doc1", "doc2", "doc3"],
    metadatas=[
        {"type": "policy", "year": "2024"},
        {"type": "procedure", "year": "2024"},
        {"type": "policy", "year": "2023"}
    ]
)
```

**หมายเหตุ:** Chroma จะ auto-generate embeddings ด้วย all-MiniLM-L6-v2 ถ้าไม่ได้ใส่ embeddings เอง

## Query

```python
# ค้นหาเอกสารที่คล้ายกับ query
results = collection.query(
    query_texts=["การลาหยุดทำอย่างไร"],
    n_results=3
)

# ดูผลลัพธ์
print(results["documents"][0])
print(results["distances"][0])
print(results["metadatas"][0])
```

## กับ LangChain

```python
# นำเข้า LangChain components
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings

# สร้าง vectorstore จาก documents
vectorstore = Chroma.from_documents(
    documents=docs,
    embedding=OpenAIEmbeddings(),
    persist_directory="./chroma_data"
)

# ค้นหา
docs = vectorstore.similarity_search("question", k=3)
```

## กับ Node.js

```javascript
// นำเข้า Chroma client
import { ChromaClient } from 'chromadb'

// สร้าง client เชื่อมต่อ server
const client = new ChromaClient({ path: 'http://localhost:8000' })

// สร้างหรือดึง collection
const collection = await client.getOrCreateCollection({ name: 'hr_docs' })

// เพิ่ม documents
await collection.add({
  documents: ['เอกสาร HR...'],
  ids: ['doc1']
})

// ค้นหา
const results = await collection.query({
  queryTexts: ['คำถาม'],
  nResults: 3
})
```

## Configuration

### Chroma Server Config
```python
# เชื่อมต่อด้วย API key
client = chromadb.HttpClient(
    host="localhost",
    port=8000,
    ssl=False,
    headers={"x-api-key": "your-api-key"}
)
```

### Embedding Function
```python
# นำเข้า sentence transformer สำหรับ Thai
from chromadb.embeddings import SentenceTransformerEmbeddingFunction

# ใช้ embedding function ที่รองรับภาษาไทย
ef = SentenceTransformerEmbeddingFunction("paraphrase-multilingual-MiniLM-L12-v2")

collection = client.create_collection(
    name="hr_th",
    embedding_function=ef
)
```

## สิ่งที่ควรรู้

### Limitations
- ไม่รองรับ real-time update ดีนัก
- เหมาะกับ small-medium scale
- ควรใช้ cloud service สำหรับ production

### Cloud Services
- **Chroma Cloud** (เริ่มต้นมี free tier): https://trychroma.com
- **Deploy บน Railway/Render** ด้วย Docker

## Troubleshooting

**Connection refused:**
- ตรวจว่า server ทำงานอยู่ `docker ps`
- ลอง restart: `docker restart <container_id>`

**Embedding error:**
- ตรวจว่า install sentence-transformers แล้ว

**Empty results:**
- ลองเพิ่ม documents ก่อน query
- ตรวจ collection name ถูกต้อง
