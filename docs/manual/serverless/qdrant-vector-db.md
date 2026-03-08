# คู่มือ Qdrant Vector DB

## ภาพรวม
Qdrant เป็น open-source vector similarity search engine รองรับ high-performance, production-ready workloads มีทั้ง self-hosted และ cloud

## ติดตั้ง

### Python
```bash
pip install qdrant-client
```

### Node.js
```bash
npm install @qdrant/js-client-rest
```

## วิธีใช้งาน

### วิธีที่ 1: Qdrant Cloud (แนะนำ)

**สมัคร:**
1. ไปที่ https://qdrant.to
2. Sign in ด้วย GitHub/Google
3. สร้าง "Cluster" ใหม่
4. เลือก Region: `Singapore` หรือ `US East`

**ได้ connection URL:**
```
https://your-cluster.uuid.us-east-1-0.qdrant.to
```

**API Key:**
- ได้จาก dashboard → API Keys
- ใช้สำหรับ authenticate

### วิธีที่ 2: Self-Hosted (Docker)

```bash
# Pull image
docker pull qdrant/qdrant:latest

# Run
docker run -p 6333:6333 -v ./qdrant_storage:/qdrant/storage qdrant/qdrant:latest
```

- API: http://localhost:6333
- Dashboard: http://localhost:6333/dashboard

## Python Examples

### เชื่อมต่อ
```python
# นำเข้า Qdrant client
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# เชื่อมต่อ Qdrant Cloud
client = QdrantClient(
    url="https://your-cluster.uuid.us-east-1-0.qdrant.to",
    api_key="your-api-key"
)

# หรือ เชื่อมต่อ Local
client = QdrantClient(host="localhost", port=6333)
```

### สร้าง Collection
```python
# ลบและสร้าง collection ใหม่
client.recreate_collection(
    collection_name="hr_documents",
    vectors_config=VectorParams(
        size=1536,  # OpenAI ada-002 dimension
        distance=Distance.COSINE
    )
)
```

### เพิ่ม Points
```python
# นำเข้า PointStruct สำหรับสร้าง points
from qdrant_client.models import PointStruct

# สร้าง operations สำหรับ upsert
operations = [
    PointStruct(
        id="doc1",
        vector=[0.1, 0.2, ...],  # embedding vector
        payload={
            "text": "นโยบายการลาหยุดประจำปี...",
            "type": "policy",
            "year": "2024"
        }
    ),
    PointStruct(
        id="doc2",
        vector=[0.3, 0.4, ...],
        payload={
            "text": "ขั้นตอนการเบิกค่ารักษาพยาบาล...",
            "type": "procedure"
        }
    )
]

# เพิ่ม points เข้า collection
client.upsert(
    collection_name="hr_documents",
    points=operations
)
```

### Query / Search
```python
# ค้นหาเอกสารที่คล้ายกับ query
search_results = client.search(
    collection_name="hr_documents",
    query_vector=[0.1, 0.2, ...],  # query embedding
    limit=5,
    query_filter=None,  # optional: filter by payload
    with_payload=True,
    with_vectors=False
)

# แสดงผลลัพธ์
for result in search_results:
    print(f"Score: {result.score}")
    print(f"Text: {result.payload['text']}")
```

### Filter by Payload
```python
# นำเข้า filter models
from qdrant_client.models import Filter, FieldCondition, Match

# ค้นหาพร้อม filter
results = client.search(
    collection_name="hr_documents",
    query_vector=query_embedding,
    limit=5,
    query_filter=Filter(
        must=[
            FieldCondition(
                key="type",
                match=Match(value="policy")
            )
        ]
    )
)
```

## กับ LangChain

```python
# นำเข้า LangChain components
from langchain.vectorstores import Qdrant
from langchain.embeddings import OpenAIEmbeddings

# สร้าง vectorstore จาก documents
vectorstore = Qdrant.from_documents(
    documents=docs,
    embedding=OpenAIEmbeddings(),
    host="your-cluster.uuid.us-east-1-0.qdrant.to",
    api_key="your-api-key",
    collection_name="hr_documents"
)

# ค้นหา
docs = vectorstore.similarity_search("question", k=3)
```

## Node.js Example

```javascript
// นำเข้า Qdrant client
import { QdrantClient } from '@qdrant/js-client-rest'

// สร้าง client
const client = new QdrantClient({
  url: 'https://your-cluster.uuid.us-east-1-0.qdrant.to',
  apiKey: 'your-api-key'
})

// ค้นหา
const results = await client.search('hr_documents', {
  vector: queryEmbedding,
  limit: 5,
  with_payload: true
})

console.log(results)
```

## Configuration Options

### Vector Size
- OpenAI ada-002: 1536
- text-embedding-3-small: 1536
- text-embedding-3-large: 3072

### Distance Metrics
- `COSINE` - แนะนำ (cosine similarity)
- `EUCLID` - Euclidean distance
- `DOT` - Dot product

### Indexing
Qdrant auto-index เมื่อมีการ insert ใหม่

## Pricing (Qdrant Cloud)

| Plan | Storage | Requests/month | Price |
|------|---------|-----------------|-------|
| Free | 1GB | 10K | ฟรี |
| Hobby | 10GB | 100K | $25/mo |
| Production | 100GB+ | Unlimited | $99/mo+ |

## Troubleshooting

**Authentication failed:**
- ตรวจ API key ถูกต้อง
- ดูที่ API Keys ใน dashboard

**Connection timeout:**
- ลอง region ใกล้กว่า (Singapore)
- ตรวจ firewall

**Empty results:**
- ตรวจว่า vector dimension ตรงกัน
- ลอง increase limit
- ตรวจ score threshold

**Rate limit:**
- รอสักครู่ หรือ upgrade plan

## สิ่งที่ควรรู้

### ข้อดี
- Performance สูงมาก
- รองรับ filtering ดี
- Cloud/On-prem ได้
- Rust-based → fast & memory efficient

### ข้อเสีย
- ต้อง generate embeddings เอง (ต่างจาก Chroma)
- Setup ยากกว่า Chroma เล็กน้อย
