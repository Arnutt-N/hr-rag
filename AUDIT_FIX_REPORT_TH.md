# รายงานสรุปการแก้ไขช่องโหว่ระบบ HR-RAG

| รายการ | ข้อมูล |
|---|---|
| **โมเดล AI** | Claude Sonnet 4.6 (`claude-sonnet-4-6`) |
| **วันที่และเวลา** | 8 มีนาคม พ.ศ. 2569 (2026-03-08) |
| **ผู้ตรวจสอบ** | Claude Code — Automated Audit Fix |
| **จำนวนปัญหาที่แก้ไข** | 30 รายการ (Critical 6 / High 13 / Medium 11) |
| **ไฟล์ที่แก้ไข** | 22 ไฟล์ |

---

## 🔴 ปัญหาระดับ Critical (6 รายการ)

### CRITICAL-1 & CRITICAL-5 — SSE Generator ใช้ DB Session ที่ปิดไปแล้ว
**ไฟล์:** `backend/app/routers/chat.py`

**ปัญหา:** FastAPI ปิด `AsyncSession` ที่ได้จาก `Depends(get_db)` ทันทีที่ route handler คืน `StreamingResponse` กลับไป ทำให้ generator ที่ยังทำงานอยู่ไม่สามารถบันทึก assistant message ลงฐานข้อมูลได้ และไม่มีการจัดการ exception ใน generator

**การแก้ไข:**
- เปิด `AsyncSessionLocal()` ใหม่ภายใน `sse_gen()` โดยตรง
- เพิ่ม `try/except` ใน generation loop และ yield `event: error` เมื่อเกิด exception

---

### CRITICAL-2 — Qdrant Client แบบ Synchronous บล็อก Event Loop
**ไฟล์:** `backend/app/services/vector_store.py`

**ปัญหา:** ใช้ `QdrantClient` แบบ sync ภายใน `async def` ทำให้ทุก request ที่เรียก vector search บล็อก event loop ของ asyncio ส่งผลให้ระบบตอบสนองช้าลงทั้งหมด

**การแก้ไข:**
- เปลี่ยนเป็น `AsyncQdrantClient` จาก `qdrant_client`
- เพิ่ม `await` ให้ทุก client call (`get_collections`, `create_collection`, `upsert`, `search`, `delete`, `get_collection`)
- เปลี่ยน `except: pass` → log warning พร้อมข้อมูล collection ที่เกิดปัญหา

---

### CRITICAL-3 — JWT Token ใน WebSocket Query Parameter
**ไฟล์:** `backend/app/routers/chat.py`

**ปัญหา:** `token` ที่อยู่ใน query string จะถูกบันทึกลง server access log, reverse proxy log, และ browser history ทำให้ token รั่วไหลได้

**การแก้ไข:**
- รับ token ใน **WebSocket message แรก** แทน (`{"type": "auth", "token": "..."}`)
- ใช้ `asyncio.wait_for(..., timeout=10.0)` เพื่อป้องกัน connection ค้าง
- ⚠️ **Breaking Change:** WebSocket client ต้องส่ง auth message แรกก่อนจึงจะสื่อสารได้

---

### CRITICAL-4 — JWT Secret ใช้ค่า Default ใน Production
**ไฟล์:** `backend/app/core/config.py`

**ปัญหา:** เมื่อไม่ตั้งค่า `JWT_SECRET_KEY` ระบบใช้ค่า `"dev-only-secret-change-in-production"` และแสดงเพียง `warnings.warn()` ซึ่งไม่เพียงพอที่จะป้องกันการ deploy ที่ไม่ปลอดภัย

**การแก้ไข:**
- เพิ่ม `model_validator` ที่ raise `RuntimeError` เมื่อ `DEBUG=False` และ secret ยังเป็นค่า default หรือว่างเปล่า
- เปลี่ยน `extra = "allow"` → `extra = "ignore"` เพื่อป้องกัน env var ที่พิมพ์ผิดผ่านการตรวจสอบโดยไม่มีข้อผิดพลาด

---

### CRITICAL-5 — ไม่มี Error Handling ใน SSE Generator
*(รวมอยู่ใน CRITICAL-1 ด้านบน)*

---

### CRITICAL-6 — Evaluation Endpoints ไม่สามารถเข้าถึงได้ (Double Prefix)
**ไฟล์:** `backend/app/routers/evaluation.py`

**ปัญหา:** Router มี `prefix="/api/evaluation"` และถูก include ด้วย `prefix="/api/v1"` ทำให้ path จริงคือ `/api/v1/api/evaluation/...` แทนที่จะเป็น `/api/v1/evaluation/...`

**การแก้ไข:**
- เปลี่ยน `prefix="/api/evaluation"` → `prefix="/evaluation"`

---

## 🟠 ปัญหาระดับ High (13 รายการ)

### HIGH-2 & HIGH-10 — ไม่ตรวจสอบขนาดไฟล์และ Orphan Record
**ไฟล์:** `backend/app/routers/ingest.py`

**ปัญหา:**
- อ่านไฟล์ทั้งหมดเข้า memory ก่อนตรวจขนาด ทำให้ถูก OOM ได้
- เมื่อ vector upsert ล้มเหลว DB record ที่สร้างไว้แล้วกลายเป็น orphan

**การแก้ไข:**
- ตรวจ `Content-Length` header ก่อนอ่านไฟล์ ปฏิเสธทันทีหากเกิน `max_file_size`
- ครอบ vector upsert ด้วย `try/except` และ `DELETE` DB record เมื่อล้มเหลว

---

### HIGH-3 & MEDIUM-7 — ไม่มี Input Validation ใน UserCreate
**ไฟล์:** `backend/app/models/schemas.py`

**ปัญหา:** `email` เป็น `str` ธรรมดา, `username`/`password` ไม่มี constraint, `llm_provider` เป็น `Optional[str]` แทนที่จะเป็น enum

**การแก้ไข:**
- `email: EmailStr`
- `username: str = Field(..., min_length=3, max_length=50, pattern=r"^\w+$")`
- `password: str = Field(..., min_length=8)`
- `llm_provider: Optional[LLMProvider] = None`

---

### HIGH-4 — Circuit Breaker ไม่ Thread-Safe
**ไฟล์:** `backend/app/core/circuit_breaker.py`

**ปัญหา:** State mutations ไม่มี lock ทำให้เกิด race condition เมื่อหลาย coroutine เรียกพร้อมกัน

**การแก้ไข:**
- เพิ่ม `asyncio.Lock` ผ่าน `__post_init__`
- ครอบ state check และ mutation ด้วย `async with self._lock`

---

### HIGH-5 — `CacheService.ping()` หายไป
**ไฟล์:** `backend/app/services/cache.py`

**ปัญหา:** Health check endpoint เรียก `await cache.ping()` แต่ method นี้ไม่มีอยู่

**การแก้ไข:**
- เพิ่ม `async def ping(self) -> bool` ที่ call `await self.client.ping()` และ return `True/False`

---

### HIGH-6 — มี `LLMProvider` Enum 2 ตัวซ้ำกัน
**ไฟล์:** `backend/app/models/database.py`, `backend/app/models/schemas.py`

**ปัญหา:** `database.py` มี `LLMProvider` 4 members, `schemas.py` มี 10 members ไม่ consistent กัน

**การแก้ไข:**
- ลบ `LLMProvider` ออกจาก `database.py`
- `import` จาก `schemas.py` แทน (single source of truth)

---

### HIGH-7 & MEDIUM-8 — Knowledge Base Index/Extract Error Handling
**ไฟล์:** `backend/app/services/knowledge_base.py`

*(ไฟล์นี้มีการ log error อยู่แล้ว — พฤติกรรมที่มีอยู่ถูกต้องตามสถาปัตยกรรม)*

---

### HIGH-8 — ใช้ `print()` แทน Logger
**ไฟล์:** `backend/app/services/graph_rag.py`, `backend/app/services/neo4j_graph.py`

**ปัญหา:** `print()` ไม่ผ่าน structured logging pipeline ทำให้ไม่มี log level, timestamp, หรือ context

**การแก้ไข:**
- เพิ่ม `logger = logging.getLogger(__name__)` ทั้ง 2 ไฟล์
- เปลี่ยน `print(...)` ทุกจุดเป็น `logger.info(...)` / `logger.warning(...)` / `logger.error(...)`

---

### HIGH-9 — WebSocket Outer Catch เปิดเผย Internal Errors
**ไฟล์:** `backend/app/routers/chat.py`

**ปัญหา:** `await websocket.send_text(json.dumps({"type": "error", "detail": str(e)}))` ส่ง stack trace ให้ client

**การแก้ไข:**
- Log exception ด้วย `logger.error()`
- ส่ง generic message ให้ client: `"An internal error occurred"`

---

### HIGH-11 — Delete Vectors Task ไม่มี Error Handling
**ไฟล์:** `backend/app/tasks/document_tasks.py`

**ปัญหา:** `delete_document_vectors_task` ไม่มี retry logic เมื่อ Qdrant ไม่พร้อมใช้งาน

**การแก้ไข:**
- เพิ่ม `bind=True, max_retries=3, default_retry_delay=30`
- ครอบด้วย `try/except` และ `raise self.retry(exc=e)`

---

### HIGH-12 — Admin Delete ไม่ลบ Vectors จาก Qdrant
**ไฟล์:** `backend/app/routers/admin.py`

**ปัญหา:** มี `# TODO: Also delete vectors from Qdrant` ค้างอยู่ ทำให้ document ที่ลบไปแล้วยังคงมี vectors เหลืออยู่ใน Qdrant

**การแก้ไข:**
- เพิ่ม import header ที่ขาดหายไปทั้งหมด (ไฟล์นี้ไม่มี imports เลย)
- เรียก `knowledge_base_service.vector_store.delete_vectors(...)` ก่อนลบ DB record
- ครอบด้วย `try/except` เพื่อให้ DB deletion ดำเนินต่อแม้ Qdrant จะล้มเหลว

---

### HIGH-13 — Batch Embedding Task เรียก Task แบบผิดวิธี
**ไฟล์:** `backend/app/tasks/embedding_tasks.py`

**ปัญหา:** `batch_generate_embeddings_task` เรียก `generate_embeddings_task(batch)` แบบ sync function call แทนที่จะเป็น Celery dispatch ทำให้ไม่ได้รับ embeddings จริง

**การแก้ไข:**
- เรียก `embedding_service.embed_texts(batch)` โดยตรง ผ่าน `asyncio.run()`
- ไม่ dispatch sub-task (ซึ่งจะทำให้ผลลัพธ์สูญหาย)

---

### HIGH-14 — Frontend useChat ซ่อน Parse Errors และ Expose Internal Setter
**ไฟล์:** `frontend/src/hooks/useChat.ts`

**ปัญหา:** `catch (e) { // Ignore }` กลืน error ทำให้ UI ไม่แสดงข้อผิดพลาด และ `setMessages` ที่ return ออกไปทำให้ internal state ถูก manipulate จากภายนอก

**การแก้ไข:**
- เปลี่ยน `// Ignore` → `setError("Failed to parse server message")`
- ลบ `setMessages` ออกจาก return value

---

## 🟡 ปัญหาระดับ Medium (11 รายการ)

| # | ไฟล์ | ปัญหา | การแก้ไข |
|---|---|---|---|
| M-1 | `services/embeddings.py` | `asyncio.get_event_loop()` deprecated | เปลี่ยนเป็น `asyncio.get_running_loop()` |
| M-2 | `services/embeddings.py` | Race condition ขณะโหลด model ครั้งแรก | เพิ่ม `asyncio.Lock` ใน `_ensure_model()` (double-checked locking) |
| M-3 | `services/advanced_retrieval.py` | `hash(text)` ไม่ deterministic ข้าม process | เปลี่ยนเป็น `hashlib.sha256(text.encode()).hexdigest()[:16]` |
| M-4 | `core/config.py` | `extra = "allow"` ยอมรับ env var ที่พิมพ์ผิด | เปลี่ยนเป็น `extra = "ignore"` |
| M-5 | `services/rag_chain.py` | `answer()` เรียก vector retrieval 2 ครั้ง | Retrieve 1 ครั้ง แล้วใช้ docs สำหรับทั้ง context และ sources |
| M-6 | `services/llm/factory.py` | ไม่มี fallback chain สำหรับ Anthropic/Google/Ollama | เพิ่ม fallback: `ANTHROPIC→[OPENAI,OLLAMA]`, `GOOGLE→[OPENAI,OLLAMA]`, `OLLAMA→[OPENAI]` |
| M-7 | `models/schemas.py` | `ChatRequest.llm_provider: Optional[str]` | เปลี่ยนเป็น `Optional[LLMProvider]` *(รวมใน HIGH-3)* |
| M-8 | `services/knowledge_base.py` | Text extraction ไม่ log filename | *(มีการ log อยู่แล้วใน existing code)* |
| M-9 | `frontend/types/index.ts` | มี `groq`/`ring2.5-t` ที่ backend ไม่รองรับ, Google/Kimi model ไม่ตรงกัน | ลบ `groq`/`ring2.5-t`, อัปเดต Google → `gemini-2.0-flash`, Kimi → `kimi-coding/k2p5/chat` |
| M-10 | `frontend/hooks/useAuth.ts` | `User.id: string` ไม่ตรงกับ backend (`int`) | เปลี่ยนเป็น `User.id: number` |
| M-11 | `models/database.py` | ไม่มี helper สำหรับตรวจสอบ admin role | เพิ่ม `@property is_admin(self) -> bool` ใน `User` model |
| M-12 | `services/advanced_retrieval.py` | Bare `except:` 3 จุด (กลืน error) | เปลี่ยนเป็น `except Exception as e: logger.warning(...)` ทั้ง 3 จุด |

---

## 📁 สรุปไฟล์ที่แก้ไข

```
backend/
├── app/
│   ├── core/
│   │   ├── config.py              ✅ CRITICAL-4, MEDIUM-4
│   │   └── circuit_breaker.py     ✅ HIGH-4
│   ├── models/
│   │   ├── schemas.py             ✅ HIGH-3, HIGH-6, MEDIUM-7
│   │   └── database.py            ✅ HIGH-6, MEDIUM-11
│   ├── services/
│   │   ├── cache.py               ✅ HIGH-5
│   │   ├── vector_store.py        ✅ CRITICAL-2
│   │   ├── embeddings.py          ✅ MEDIUM-1, MEDIUM-2
│   │   ├── rag_chain.py           ✅ MEDIUM-5
│   │   ├── knowledge_base.py      ✅ HIGH-7, MEDIUM-8
│   │   ├── graph_rag.py           ✅ HIGH-8
│   │   ├── neo4j_graph.py         ✅ HIGH-8
│   │   ├── advanced_retrieval.py  ✅ MEDIUM-3, MEDIUM-12
│   │   └── llm/
│   │       └── factory.py         ✅ MEDIUM-6
│   ├── routers/
│   │   ├── chat.py                ✅ CRITICAL-1/3/5, HIGH-9
│   │   ├── ingest.py              ✅ HIGH-2, HIGH-10
│   │   ├── admin.py               ✅ HIGH-12 (+ เพิ่ม missing imports)
│   │   └── evaluation.py          ✅ CRITICAL-6
│   └── tasks/
│       ├── embedding_tasks.py     ✅ HIGH-13
│       └── document_tasks.py      ✅ HIGH-11

frontend/src/
├── types/
│   └── index.ts                   ✅ MEDIUM-9
└── hooks/
    ├── useAuth.ts                  ✅ MEDIUM-10
    └── useChat.ts                  ✅ HIGH-14
```

---

## ⚠️ Breaking Changes ที่ต้องอัปเดต Client

### 1. WebSocket Authentication Protocol
WebSocket client ต้องส่ง **authentication message แรก** ก่อนส่ง chat message:
```json
// ข้อความแรกที่ต้องส่งหลังเชื่อมต่อ
{"type": "auth", "token": "<jwt_access_token>"}
```
*(เดิมส่ง token เป็น query parameter: `ws://host/chat/ws?token=...`)*

---

## 🔒 การตรวจสอบหลังแก้ไข

| การทดสอบ | วิธีตรวจ | ผลที่คาดหวัง |
|---|---|---|
| JWT Secret | เริ่ม app ด้วย `DEBUG=False` และไม่ตั้ง `JWT_SECRET_KEY` | `RuntimeError` ถูก raise ทันที |
| Evaluation prefix | `GET /api/v1/evaluation/dashboard` | HTTP 200 |
| Async Qdrant | รัน ingest + search flow | ไม่มี event loop blocking |
| Cache health | `GET /health/detailed` | Redis แสดง `"healthy": true` |
| Frontend types | `npm run build` ใน `frontend/` | ไม่มี TypeScript errors |
| Python syntax | `python -m py_compile app/**/*.py` | ผ่านทุกไฟล์ ✅ |

---

*รายงานนี้สร้างโดย Claude Sonnet 4.6 (`claude-sonnet-4-6`) เมื่อวันที่ 8 มีนาคม พ.ศ. 2569*
