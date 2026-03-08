# HR-RAG Codebase Audit Report

> **วันที่ตรวจสอบ:** 8 มีนาคม 2026
> **โมเดลที่ใช้วิเคราะห์:** Claude Opus 4.6 (`claude-opus-4-6`) + Claude Sonnet 4.6 (`claude-sonnet-4-6`)
> **Agent ที่ใช้:**
> - Code Reviewer Agent (Sonnet 4.6) — ตรวจสอบโค้ดทั่วไป, ความปลอดภัย, async/await
> - Silent Failure Hunter Agent (Sonnet 4.6) — ค้นหา error ที่ถูกกลืน, error handling ที่ไม่เพียงพอ
> - Type Design Analyzer Agent (Sonnet 4.6) — วิเคราะห์คุณภาพ type system, schema, invariant
> - Main Orchestrator (Opus 4.6) — ประสานงาน, ตรวจสอบ infrastructure, สรุปผล
> **จำนวนปัญหาที่พบ:** 35 รายการ (Critical 6, High 13, Medium 11, Infrastructure 5)

---

## สารบัญ

- [สรุปผลการตรวจสอบ](#สรุปผลการตรวจสอบ)
- [ปัญหาระดับ CRITICAL](#ปัญหาระดับ-critical)
- [ปัญหาระดับ HIGH](#ปัญหาระดับ-high)
- [ปัญหาระดับ MEDIUM](#ปัญหาระดับ-medium)
- [ปัญหา Infrastructure](#ปัญหา-infrastructure)
- [สิ่งที่ทำได้ดี](#สิ่งที่ทำได้ดี)
- [ลำดับความสำคัญในการแก้ไข](#ลำดับความสำคัญในการแก้ไข)

---

## สรุปผลการตรวจสอบ

ระบบ HR-RAG มีปัญหาที่ต้องแก้ไขก่อนนำขึ้น production จำนวน **35 รายการ** แบ่งตามความรุนแรง:

| ระดับ | จำนวน | คำอธิบาย |
|-------|--------|----------|
| CRITICAL | 6 | ต้องแก้ไขทันที — ระบบจะล่มหรือมีช่องโหว่ด้านความปลอดภัย |
| HIGH | 13 | ควรแก้ไขก่อน merge — ส่งผลต่อ data integrity และ user experience |
| MEDIUM | 11 | แก้ไขใน sprint ถัดไป — ปัญหา type safety และ code quality |
| Infrastructure | 5 | ปัญหา config/deployment ที่ต้องแก้ก่อนนำขึ้น production |

### กลุ่มปัญหาหลัก 3 กลุ่ม

1. **Chat/SSE/WebSocket ไม่แสดง error ให้ผู้ใช้** (Issue 1, 5, 7, 17) — ฟีเจอร์หลักของระบบ (แชท) จะหยุดทำงานเงียบ ๆ โดยผู้ใช้ไม่รู้สาเหตุ
2. **Vector data ไม่ถูกลบ (orphaned data)** (Issue 9, 18, 19) — ทุกครั้งที่ลบ project/document จะเหลือ vector ค้างใน Qdrant ทำให้ storage โตไม่หยุดและผลค้นหาเก่าปนเข้ามา
3. **Async/Sync ไม่ตรงกัน** (Issue 2, 12, 20, 21) — Qdrant client เป็น synchronous ทำให้ event loop ถูก block, circuit breaker ไม่ thread-safe, deprecated API

---

## ปัญหาระดับ CRITICAL

### CRITICAL-1: DB Session ถูกปิดก่อนที่ SSE Generator จะ commit

| รายละเอียด | |
|---|---|
| **ไฟล์** | `backend/app/routers/chat.py:91-108` |
| **ความมั่นใจ** | 95% |
| **ผลกระทบ** | ข้อความ assistant จะไม่ถูกบันทึกลง database ในทุก streaming response |

**ปัญหา:** ฟังก์ชัน `sse_gen()` (async generator) จับ `db` session จาก FastAPI dependency injection แต่ FastAPI จะปิด session ทันทีที่ฟังก์ชัน `chat()` return ในขณะที่ generator ยังทำงานอยู่ ทำให้ `db.commit()` ภายใน generator ทำงานกับ session ที่ปิดไปแล้ว

**โค้ดปัจจุบัน:**
```python
@router.post("", response_class=StreamingResponse)
async def chat(..., db: AsyncSession = Depends(get_db)):
    ...
    async def sse_gen() -> AsyncGenerator[str, None]:
        ...
        # db ถูกปิดแล้วตรงนี้ — FastAPI ปิดเมื่อ chat() return
        db.add(assistant_msg)
        await db.commit()  # FAIL หรือไม่ทำงาน
    return StreamingResponse(sse_gen(), ...)
```

**วิธีแก้ไข:** เปิด session ใหม่ภายใน generator
```python
async def sse_gen() -> AsyncGenerator[str, None]:
    collected = []
    async for chunk in llm.generate_response(prompt, provider=provider, stream=True):
        collected.append(chunk)
        yield f"data: {json.dumps({'content': chunk})}\n\n"
    full = "".join(collected)
    async with AsyncSessionLocal() as gen_db:
        assistant_msg = ChatMessage(...)
        gen_db.add(assistant_msg)
        await gen_db.commit()
    yield f"data: {json.dumps({'done': True, 'session_id': session.id})}\n\n"
```

---

### CRITICAL-2: Qdrant Client เป็น Synchronous — Block Event Loop

| รายละเอียด | |
|---|---|
| **ไฟล์** | `backend/app/services/vector_store.py:23` |
| **ความมั่นใจ** | 100% |
| **ผลกระทบ** | ทุก request ที่เกี่ยวกับ vector search/upsert จะ block event loop ทั้งหมด |

**ปัญหา:** ทุก method ใน `VectorStore` ถูกประกาศเป็น `async` แต่ใช้ `QdrantClient` (synchronous) จริง ๆ ทำให้ทุก operation block event loop ทำให้ throughput ต่ำมากภายใต้ concurrent load

**โค้ดปัจจุบัน:**
```python
self.client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
# ทุก call ด้านล่างนี้ block event loop:
collections = self.client.get_collections().collections
self.client.upsert(collection_name=collection_name, points=points)
results = self.client.search(...)
```

**วิธีแก้ไข:**
```python
from qdrant_client import AsyncQdrantClient

self.client = AsyncQdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
# แล้วใช้ await ทุก call:
collections = await self.client.get_collections()
await self.client.upsert(...)
results = await self.client.search(...)
```

---

### CRITICAL-3: JWT Token ถูกส่งผ่าน WebSocket Query Parameter

| รายละเอียด | |
|---|---|
| **ไฟล์** | `backend/app/routers/chat.py:140` |
| **ความมั่นใจ** | 100% |
| **ผลกระทบ** | Token ถูกบันทึกใน Nginx access log, browser history, load balancer log |

**ปัญหา:** `token = websocket.query_params.get("token")` — query parameter จะถูก log โดย proxy, load balancer, และ browser history ทุกตัว เป็นช่องโหว่ด้านความปลอดภัยร้ายแรง

**วิธีแก้ไข:** รับ token จาก message แรกหลัง connection:
```python
# รับ auth จาก message แรก
raw = await asyncio.wait_for(websocket.receive_text(), timeout=5.0)
auth_msg = json.loads(raw)
token = auth_msg.get("token")
```

---

### CRITICAL-4: JWT Secret ใช้ค่า Default ใน Production โดยไม่ Error

| รายละเอียด | |
|---|---|
| **ไฟล์** | `backend/app/core/config.py:134-139` |
| **ความมั่นใจ** | 100% |
| **ผลกระทบ** | ใครก็ตามสามารถปลอม JWT token ได้ถ้า production ลืมตั้ง JWT_SECRET_KEY |

**ปัญหา:** เมื่อ `JWT_SECRET_KEY` ไม่ได้ตั้งค่า ระบบใช้ `"dev-only-secret-change-in-production"` พร้อม `warnings.warn()` ซึ่งจะไม่แสดงใน container ที่ suppress warnings

**วิธีแก้ไข:**
```python
if not self.jwt_secret_key:
    if not self.debug:
        raise RuntimeError(
            "JWT_SECRET_KEY ต้องตั้งค่าใน production. "
            "สร้างด้วย: openssl rand -hex 64"
        )
    self.jwt_secret_key = "dev-only-secret-change-in-production"
```

---

### CRITICAL-5: SSE Generator ไม่มี Error Handling — ผู้ใช้เห็น Response ตัดกลางคัน

| รายละเอียด | |
|---|---|
| **ไฟล์** | `backend/app/routers/chat.py:91-108` |
| **ความมั่นใจ** | 100% |
| **ผลกระทบ** | LLM error, rate limit, หรือ DB error ระหว่าง stream จะทำให้ response หยุดกลางคันโดยไม่มี error message |

**ปัญหา:** ไม่มี try/except ใน `sse_gen()` ถ้า LLM API เกิด error กลางทาง ผู้ใช้จะเห็น response ที่ถูกตัดและ event `done: true` จะไม่ถูกส่ง

**วิธีแก้ไข:**
```python
async def sse_gen() -> AsyncGenerator[str, None]:
    collected = []
    try:
        async for chunk in llm.generate_response(prompt, provider=provider, stream=True):
            collected.append(chunk)
            yield f"data: {json.dumps({'content': chunk})}\n\n"
    except Exception as e:
        logger.error("sse_generation_failed", session_id=session.id, error=str(e))
        yield f"data: {json.dumps({'error': True, 'detail': 'เกิดข้อผิดพลาด กรุณาลองใหม่'})}\n\n"
        return
    # ... commit logic ...
```

---

### CRITICAL-6: Evaluation Router มี URL Prefix ซ้ำซ้อน — ทุก Endpoint ใช้งานไม่ได้

| รายละเอียด | |
|---|---|
| **ไฟล์** | `backend/app/routers/evaluation.py:21` |
| **ความมั่นใจ** | 100% |
| **ผลกระทบ** | ทุก evaluation endpoint เข้าถึงไม่ได้ (404) |

**ปัญหา:** Router ใช้ `prefix="/api/evaluation"` แล้ว `main.py` เพิ่ม `/api/v1` อีก ทำให้ path เป็น `/api/v1/api/evaluation/...`

**วิธีแก้ไข:**
```python
# เปลี่ยนจาก:
router = APIRouter(prefix="/api/evaluation", tags=["evaluation"])
# เป็น:
router = APIRouter(prefix="/evaluation", tags=["evaluation"])
```

---

## ปัญหาระดับ HIGH

### HIGH-1: Vector Store `delete_collection` กลืน Exception ทั้งหมด

| รายละเอียด | |
|---|---|
| **ไฟล์** | `backend/app/services/vector_store.py:60-63` |
| **ผลกระทบ** | ลบ project แล้ว vector ค้างใน Qdrant — storage โตไม่หยุด, ผลค้นหาเก่าปนเข้ามา |

```python
# ปัจจุบัน — กลืนทุก error
except Exception:
    pass  # Ignore if doesn't exist
```

**วิธีแก้ไข:** แยก "not found" error ออกจาก error อื่น ๆ แล้ว re-raise กรณีที่ไม่ใช่ "not found"

---

### HIGH-2: ไม่มีการจำกัดขนาดไฟล์ก่อนอ่านเข้า Memory

| รายละเอียด | |
|---|---|
| **ไฟล์** | `backend/app/routers/ingest.py:20-33` |
| **ผลกระทบ** | ผู้ใช้ที่ authenticated สามารถอัปโหลดไฟล์ขนาดใหญ่ทำให้เกิด OOM crash |

**วิธีแก้ไข:** เพิ่ม size check ก่อนอ่านไฟล์:
```python
contents = await file.read(settings.max_file_size + 1)
if len(contents) > settings.max_file_size:
    raise HTTPException(status_code=413, detail="ไฟล์มีขนาดใหญ่เกินไป")
await file.seek(0)
```

---

### HIGH-3: ไม่มี Input Validation บน `UserCreate`

| รายละเอียด | |
|---|---|
| **ไฟล์** | `backend/app/models/schemas.py` |
| **ผลกระทบ** | รับ email/username/password ทุกค่าโดยไม่ตรวจสอบ format |

```python
# ปัจจุบัน — ไม่มี validation
class UserCreate(BaseModel):
    email: str           # ไม่มี EmailStr
    username: str        # ไม่มี length limit
    password: str        # ไม่มี min length

# วิธีแก้ไข:
class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9_.-]+$')
    password: str = Field(..., min_length=8, max_length=128)
    full_name: Optional[str] = Field(default=None, max_length=255)
```

---

### HIGH-4: Circuit Breaker ไม่ Thread/Coroutine Safe

| รายละเอียด | |
|---|---|
| **ไฟล์** | `backend/app/core/circuit_breaker.py:79-83` |
| **ผลกระทบ** | Concurrent coroutine สามารถ corrupt state ของ circuit breaker ได้ |

**วิธีแก้ไข:** ใช้ `asyncio.Lock` ป้องกัน state transitions

---

### HIGH-5: `/health/detailed` เรียก method `cache.ping()` ที่ไม่มีอยู่จริง

| รายละเอียด | |
|---|---|
| **ไฟล์** | `backend/app/main.py:134` |
| **ผลกระทบ** | Health endpoint รายงาน Redis เป็น "error" เสมอ แม้ Redis ทำงานปกติ — ข้อมูล monitoring ผิดทั้งหมด |

**วิธีแก้ไข:** เพิ่ม method `ping()` ใน `CacheService` หรือเปลี่ยนเป็น `await cache.client.ping()`

---

### HIGH-6: `LLMProvider` Enum มี 2 version ที่ไม่ตรงกัน

| รายละเอียด | |
|---|---|
| **ไฟล์** | `database.py:47-51` (4 members) vs `schemas.py:126-136` (10 members) |
| **ผลกระทบ** | บันทึก provider เช่น `KIMI` ลง DB จะเกิด runtime error เพราะ column enum มีแค่ 4 ค่า |

**วิธีแก้ไข:** สร้าง enum ตัวเดียวใน `app/models/enums.py` แล้ว import ใช้ทั้ง 2 ไฟล์

---

### HIGH-7: Knowledge Base `index_document` ข้าม chunk ที่ fail เงียบ ๆ

| รายละเอียด | |
|---|---|
| **ไฟล์** | `backend/app/services/knowledge_base.py:183-185` |
| **ผลกระทบ** | Document ถูก mark เป็น `is_indexed=True` แม้มีแค่ 1 จาก 100 chunk ที่สำเร็จ — ผู้ใช้ค้นหาได้ผลลัพธ์ไม่ครบ |

**วิธีแก้ไข:** เพิ่ม status `"partial"` และแจ้งจำนวน chunk ที่ fail ใน response

---

### HIGH-8: `graph_rag.py` + `neo4j_graph.py` ใช้ `print()` แทน logger (10+ ที่)

| รายละเอียด | |
|---|---|
| **ไฟล์** | `backend/app/services/graph_rag.py`, `neo4j_graph.py` |
| **ผลกระทบ** | Error ไม่ถูกจับโดย log aggregation — ไม่สามารถ monitor Neo4j ใน production ได้ |

**วิธีแก้ไข:** เปลี่ยน `print()` เป็น `logger.error()`/`logger.info()` พร้อม structured fields

---

### HIGH-9: WebSocket Outer Catch ส่ง `str(e)` ให้ client และปิด connection ทั้งหมด

| รายละเอียด | |
|---|---|
| **ไฟล์** | `backend/app/routers/chat.py:216-221` |
| **ผลกระทบ** | Error จาก message เดียวทำให้ WS connection ทั้งหมดตาย + อาจเปิดเผย internal details |

**วิธีแก้ไข:** ย้าย try/except เข้าไปใน `while True` loop และส่ง sanitized error message + `continue`

---

### HIGH-10: Ingest Router ไม่จัดการ Vector Upsert Failure

| รายละเอียด | |
|---|---|
| **ไฟล์** | `backend/app/routers/ingest.py:57-70` |
| **ผลกระทบ** | Document record ถูก commit ก่อน vector upsert — ถ้า Qdrant ล่ม จะเกิด orphaned records |

**วิธีแก้ไข:** ถ้า upsert fail ให้ลบ document record ออกและ return 503

---

### HIGH-11: Admin `delete_knowledge_document` ไม่ลบ vector จาก Qdrant

| รายละเอียด | |
|---|---|
| **ไฟล์** | `backend/app/routers/admin.py:389-390` |
| **ผลกระทบ** | `# TODO: Also delete vectors from Qdrant` — vector ไม่ถูกลบเมื่อลบ document |

---

### HIGH-12: Frontend Chat Error ไม่แสดงให้ผู้ใช้เห็น

| รายละเอียด | |
|---|---|
| **ไฟล์** | `frontend/src/app/page.tsx:93-101` |
| **ผลกระทบ** | `catch (e) { // Ignore }` — ผู้ใช้เห็น spinner หยุดและ message ว่างเปล่า |

**วิธีแก้ไข:** แสดง error message ใน chat UI

---

### HIGH-13: `batch_generate_embeddings_task` เรียก Celery task เป็น function ธรรมดา

| รายละเอียด | |
|---|---|
| **ไฟล์** | `backend/app/tasks/embedding_tasks.py:55` |
| **ผลกระทบ** | task ไม่ผ่าน worker + return value ไม่มี key `"embeddings"` ทำให้ได้ผลลัพธ์ว่างเสมอ |

---

## ปัญหาระดับ MEDIUM

| # | ไฟล์ | ปัญหา |
|---|------|-------|
| 1 | `embeddings.py:47` | `asyncio.get_event_loop()` deprecated ใน Python 3.10+ — ใช้ `get_running_loop()` แทน |
| 2 | `embeddings.py:28-31` | Lazy model loading ไม่ coroutine-safe บน cold start (race condition) |
| 3 | `advanced_retrieval.py:336` | `hash()` สำหรับ doc dedup ไม่ deterministic ข้าม process restart |
| 4 | `config.py:102-104` | `extra = "allow"` ทำให้ env var ที่พิมพ์ผิดถูกรับเงียบ ๆ |
| 5 | `rag_chain.py:144-165` | ดึง vector 2 ครั้งต่อ `answer()` call (duplicate retrieval) |
| 6 | `chat_state.py:66` | `quality_evaluation` ไม่ได้ถูกกำหนดค่าใน `create_initial_state` — จะเกิด `KeyError` |
| 7 | `factory.py:68-76` | `FALLBACK_CHAIN` ไม่มี entry สำหรับ `ANTHROPIC`, `GOOGLE`, `OLLAMA` |
| 8 | `llm.py:76-100` | `/llm/custom/config` รับ API key และเก็บใน global state — member คนไหนก็เปลี่ยน LLM provider ที่ใช้ร่วมกันได้ |
| 9 | `knowledge_base.py:86-90` | Text extraction fail แล้วสร้าง document ที่ `content=None` เงียบ ๆ |
| 10 | `frontend types` | `User.id`/`Project.id` typed เป็น `string` แต่ backend return `number`; frontend มี `groq` ที่ backend ไม่มี |
| 11 | `database.py:64-65` | `role` + `is_member` ซ้ำซ้อน สร้าง invalid state space |

---

## ปัญหา Infrastructure

| # | ไฟล์ | ปัญหา | ความรุนแรง |
|---|------|-------|-----------|
| 1 | `docker-compose.yml:44-46` | `NEXT_PUBLIC_API_URL=http://localhost:8000` — ใช้งานไม่ได้ใน production | HIGH |
| 2 | `docker-compose.yml:87` | `SECRET_KEY=${SECRET_KEY}` ถูกส่งแต่ backend ไม่ใช้ (ใช้ `JWT_SECRET_KEY`) | MEDIUM |
| 3 | `.env.example:14` | `DATABASE_URL` ใช้ `mysql+pymysql://` แต่ docker-compose ใช้ `postgresql+asyncpg://` — ขัดแย้งกัน | HIGH |
| 4 | `nginx.conf:92-110` | Qdrant และ Neo4j browser ถูกเปิดผ่าน reverse proxy — `allow`/`deny` ถูก comment ออก ทำให้ database เข้าถึงได้จากภายนอก | CRITICAL |
| 5 | `docker-compose.yml:107` | Backend ใช้ `--reload` flag ใน Docker — เป็น development flag ที่ไม่ควรอยู่ใน production | MEDIUM |

---

## สิ่งที่ทำได้ดี

ต่อไปนี้คือ pattern ที่ทำได้ดีและควรเป็นตัวอย่างสำหรับส่วนอื่น:

- **`cache.py`** — ทุก method มี try/except, log พร้อม key context, graceful degradation เมื่อ Redis ไม่พร้อม
- **`file_processor.py`** — ใช้ magic number validation ป้องกัน file spoofing; `.doc` path มี error message ที่ชัดเจนและ actionable
- **`auth.py`** — Login failure log ที่ `warning` พร้อม `reason` field; มี rate limiting ทั้ง register และ login; password strength validation มี message ภาษาไทย
- **`chat.py` WebSocket auth** — Token validation failure ส่ง close code 4401 พร้อม log reason
- **`search.py`** — Sanitize query input ก่อนใช้งาน; log project-not-found ที่ `warning` พร้อม user context
- **`circuit_breaker.py`** — State transitions ถูก log ที่ `info`, failures ที่ `warning`; ใช้ structured logging ตลอด
- **`document_tasks.py:47-51`** — `process_document_task` log error แล้ว retry ผ่าน `self.retry(exc=e)` — Celery retry pattern ที่ถูกต้อง
- **`main.py`** — Rate limit handler return 429 พร้อม `Retry-After` header และ log IP + path

---

## ลำดับความสำคัญในการแก้ไข

### ทำทันที (ก่อนนำขึ้น production)

| ลำดับ | Issue | เหตุผล |
|-------|-------|--------|
| 1 | CRITICAL-1 | SSE session lifecycle — ข้อมูลแชทจะไม่ถูกบันทึก |
| 2 | CRITICAL-2 | Qdrant synchronous client — throughput ต่ำมาก |
| 3 | CRITICAL-4 | JWT secret fallback — ช่องโหว่ authentication |
| 4 | CRITICAL-6 | Evaluation prefix ซ้ำ — ทุก endpoint 404 |
| 5 | CRITICAL-5 | SSE error handling — ผู้ใช้เห็น response ตัดกลางคัน |
| 6 | Infra-4 | Nginx เปิด Qdrant/Neo4j สู่ภายนอก |

### ทำก่อน merge

| ลำดับ | Issue | เหตุผล |
|-------|-------|--------|
| 7 | CRITICAL-3 | Token ใน query parameter |
| 8 | HIGH-1 | Vector data ค้างเมื่อลบ project |
| 9 | HIGH-2 | File size ไม่ถูกจำกัด |
| 10 | HIGH-3 | UserCreate ไม่มี validation |
| 11 | HIGH-5 | Health endpoint รายงานผิด |
| 12 | HIGH-12 | Frontend ไม่แสดง error |
| 13 | HIGH-6 | LLMProvider enum ไม่ตรงกัน |

### ทำใน sprint ถัดไป

ปัญหา MEDIUM ทั้งหมด + HIGH ที่เหลือ

---

> **หมายเหตุ:** รายงานนี้สร้างโดย Claude Code โดยใช้ Claude Opus 4.6 เป็นตัวประสาน และ Claude Sonnet 4.6 เป็น agent ย่อย 3 ตัวทำงานคู่ขนาน ผลลัพธ์ถูกตรวจสอบซ้ำ (deduplicated) และจัดลำดับความสำคัญแล้ว
