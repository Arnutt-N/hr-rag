# คู่มือการรันระบบ HR-RAG แบบโลคอล (Development)

คู่มือนี้จะแนะนำขั้นตอนการเตรียม环境และรันระบบ HR-RAG บนเครื่องโลคอลเพื่อการพัฒนาและทดสอบ

---

## 📋 สารบัญ

1. [สิ่งที่ต้องมี](#1-สิ่งที่ต้องมี-prerequisites)
2. [เตรียม Backend](#2-เตรียม-backend)
3. [เตรียม Database Services](#3-เตรียม-database-services)
4. [เตรียม Frontend](#4-เตรียม-frontend)
5. [รันและทดสอบ](#5-รันและทดสอบ)
6. [แก้ไขปัญหาที่พบบ่อย](#6-แก้ไขปัญหาที่พบบ่อย)

---

## 1. สิ่งที่ต้องมี (Prerequisites)

### Software ที่ต้องติดตั้ง

| Software | เวอร์ชัน | เว็บไซต์ |
|----------|---------|----------|
| Python | 3.10+ | https://www.python.org/downloads/ |
| Node.js | 18+ | https://nodejs.org/ |
| Docker Desktop | ล่าสุด | https://www.docker.com/products/docker-desktop/ |

### ตรวจสอบการติดตั้ง

```bash
python --version
node --version
npm --version
docker --version
docker compose version
```

---

## 2. เตรียม Backend

### 2.1 สร้าง Virtual Environment

```bash
cd D:\genAI\hr-rag\backend

# สร้าง virtual environment
python -m venv venv
py -3.12 -m venv venv

# Activate (PowerShell)
venv\Scripts\Activate.ps1

# Activate (CMD)
venv\Scripts\activate
```

### 2.2 ติดตั้ง Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 2.3 สร้างไฟล์ .env

> ⚠️ **สำคัญ:** โปรเจกต์นี้ไม่มีไฟล์ `.env.example` ต้องสร้างไฟล์ `.env` เอง

สร้างไฟล์ `backend/.env` ด้วยเนื้อหาต่อไปนี้:

```env
# ===========================================
# HR-RAG Development Environment Configuration
# ===========================================

# --- Debug & Security ---
DEBUG=True
JWT_SECRET_KEY=dev-secret-key-change-this-in-production
CORS_ORIGINS=http://localhost:3000,http://localhost:8000,http://127.0.0.1:3000

# --- PostgreSQL ---
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/hr_rag
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=hr_rag
POSTGRES_PASSWORD=postgres

# --- Qdrant (Vector DB) ---
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_API_KEY=

# --- Neo4j (Graph DB) ---
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=neo4j_password
NEO4J_DATABASE=neo4j

# --- Redis (Cache) ---
REDIS_URL=redis://localhost:6379/0

# --- LLM Providers (เลือกอย่างน้อย 1 ตัว) ---

# Option 1: OpenAI
OPENAI_API_KEY=sk-your-openai-api-key-here
DEFAULT_LLM_PROVIDER=openai

# Option 2: Anthropic (Claude)
# ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key-here
# DEFAULT_LLM_PROVIDER=anthropic

# Option 3: Google (Gemini)
# GOOGLE_API_KEY=your-google-api-key-here
# DEFAULT_LLM_PROVIDER=google

# Option 4: Ollama (Local - Free)
# OLLAMA_BASE_URL=http://localhost:11434
# DEFAULT_LLM_PROVIDER=ollama

# --- Embedding Model ---
EMBEDDING_MODEL=BAAI/bge-m3
EMBEDDING_DEVICE=cpu

# --- Application Settings ---
MAX_FILE_SIZE=10485760
CACHE_TTL=3600
CELERY_TIMEZONE=Asia/Bangkok

# --- Observability (Optional) ---
OTEL_EXPORTER_OTLP_ENDPOINT=
PROMETHEUS_ENABLED=False
```

---

## 3. เตรียม Database Services

### 3.1 รัน Infrastructure ด้วย Docker

```bash
cd D:\genAI\hr-rag

# รันเฉพาะ database services (ไม่รัน backend/frontend)
docker-compose up -d postgres qdrant neo4j redis

# ตรวจสอบสถานะ
docker-compose ps
```

### 3.2 ตรวจสอบ Services

```bash
# ดู logs ของแต่ละ service
docker-compose logs postgres
docker-compose logs qdrant
docker-compose logs neo4j
docker-compose logs redis
```

### 3.3 เข้าถึง Admin UIs

| Service | URL | Username | Password |
|---------|-----|----------|----------|
| Qdrant | http://localhost:6333 | - | - |
| Neo4j Browser | http://localhost:7474 | neo4j | neo4j_password |
| Redis | localhost:6379 | - | - |

---

## 4. เตรียม Frontend

### 4.1 ติดตั้ง Dependencies

```bash
cd D:\genAI\hr-rag\frontend

npm install
```

### 4.2 สร้างไฟล์ .env.local (ถ้าจำเป็น)

สร้างไฟล์ `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

---

## 5. รันและทดสอบ

### 5.1 รัน Backend Server

```bash
cd D:\genAI\hr-rag\backend

# Activate virtual environment (ถ้ายังไม่ได้ activate)
.venv\Scripts\activate

# รัน server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5.2 รัน Frontend Development Server

เปิด terminal ใหม่:

```bash
cd D:\genAI\hr-rag\frontend

npm run dev
```

### 5.3 รัน Celery Workers (Optional)

เปิด terminal ใหม่:

```bash
cd D:\genAI\hr-rag\backend
.venv\Scripts\activate

# Worker สำหรับ background tasks
celery -A app.core.celery_app worker --loglevel=info

# Beat สำหรับ periodic tasks (terminal อีกอัน)
celery -A app.core.celery_app beat --loglevel=info
```

---

## 6. เข้าถึงระบบ

| Service | URL | คำอธิบาย |
|---------|-----|----------|
| Frontend | http://localhost:3000 | Next.js Web App |
| Backend API | http://localhost:8000 | FastAPI Server |
| API Docs (Swagger) | http://localhost:8000/docs | Interactive API Documentation |
| API Docs (ReDoc) | http://localhost:8000/redoc | Alternative API Documentation |
| Health Check | http://localhost:8000/health | Basic health status |
| Health Detailed | http://localhost:8000/health/detailed | Detailed service status |

---

## 7. การทดสอบ

### 7.1 ทดสอบ Backend

```bash
cd D:\genAI\hr-rag\backend
.venv\Scripts\activate

# รันทุก test
pytest

# รันพร้อม coverage
pytest --cov=app

# รันแบบ verbose
pytest -v

# รันเฉพาะไฟล์
pytest tests/test_file.py

# รันเฉพาะ function
pytest tests/test_file.py::test_function_name
```

### 7.2 ทดสอบ Frontend

```bash
cd D:\genAI\hr-rag\frontend

# Lint check
npm run lint

# Type check
npm run type-check

# Build test
npm run build
```

### 7.3 ทดสอบ API ด้วย cURL

```bash
# Health check
curl http://localhost:8000/health

# Detailed health check
curl http://localhost:8000/health/detailed

# Register new user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123","username":"testuser"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
```

---

## 8. คำสั่งที่เป็นประโยชน์

### Docker Commands

```bash
# ดู logs ของทุก service
docker-compose logs -f

# ดู logs ของ service เดียว
docker-compose logs -f backend

# Restart service
docker-compose restart postgres

# หยุดทุก service
docker-compose down

# หยุดและลบ volumes (⚠️ ข้อมูลจะหาย)
docker-compose down -v

# ดู resource usage
docker stats

# สร้าง image ใหม่
docker-compose build backend
```

### Backend Commands

```bash
# Database migrations
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1
alembic history
alembic current

# Type checking
mypy app/

# Format code
black app/
isort app/
```

### Frontend Commands

```bash
# Development
npm run dev

# Build production
npm run build

# Start production server
npm start

# Lint
npm run lint
```

---

## 9. แก้ไขปัญหาที่พบบ่อย

### ❌ Port ถูกใช้แล้ว

**อาการ:** `Error: Address already in use`

**วิธีแก้:**
```bash
# Windows - หา process ที่ใช้ port
netstat -ano | findstr :8000

# ฆ่า process (แทนที่ PID ด้วยเลขที่ได้)
taskkill /PID <PID> /F

# หรือเปลี่ยน port ใน .env และ docker-compose.yml
```

### ❌ ModuleNotFoundError

**อาการ:** `ModuleNotFoundError: No module named 'xxx'`

**วิธีแก้:**
```bash
cd backend
.venv\Scripts\activate
pip install -r requirements.txt --upgrade
```

### ❌ Docker Container ไม่ขึ้น

**อาการ:** Container status = Exited

**วิธีแก้:**
```bash
# ดู logs
docker-compose logs <service_name>

# ลบ container และสร้างใหม่
docker-compose rm -f <service_name>
docker-compose up -d <service_name>
```

### ❌ Database Connection Failed

**อาการ:** `could not connect to server`

**วิธีแก้:**
1. ตรวจสอบว่า PostgreSQL container ขึ้นแล้ว
   ```bash
   docker-compose ps postgres
   ```
2. ตรวจสอบ `DATABASE_URL` ใน `.env`
3. ลอง restart container
   ```bash
   docker-compose restart postgres
   ```

### ❌ JWT Secret Error

**อาการ:** `RuntimeError: JWT_SECRET_KEY is not set`

**วิธีแก้:**
- ตรวจสอบว่า `JWT_SECRET_KEY` ใน `.env` มีการตั้งค่า
- ตรวจสอบว่า `DEBUG=True` สำหรับ development

### ❌ npm install ล้มเหลว

**อาการ:** `npm ERR! code ENOENT` หรือ `npm ERR! ERESOLVE`

**วิธีแก้:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

---

## 10. โครงสร้างไฟล์ที่สร้าง

```
D:\genAI\hr-rag\
├── backend/
│   ├── .venv/                 # Virtual environment (สร้างเอง)
│   ├── .env                   # Environment variables (สร้างเอง)
│   ├── app/
│   │   ├── main.py            # FastAPI entry point
│   │   ├── core/              # Config, logging, circuit breaker
│   │   ├── models/            # SQLAlchemy models, Pydantic schemas
│   │   ├── routers/           # API endpoints
│   │   ├── services/          # Business logic
│   │   └── tasks/             # Celery tasks
│   └── tests/                 # Test files
│
├── frontend/
│   ├── node_modules/          # Dependencies (สร้างเอง)
│   ├── .env.local             # Environment variables (สร้างเอง)
│   ├── src/
│   │   ├── app/               # Next.js pages
│   │   ├── components/        # React components
│   │   ├── hooks/             # Custom hooks
│   │   └── types/             # TypeScript types
│   └── package.json
│
└── docs/
    └── manual/
        └── rundev/
            └── GUIDE.md       # คู่มือนี้
```

---

## 11. Next Steps

หลังจากระบบรันได้แล้ว แนะนำให้:

1. **ทดสอบ API** - เข้า http://localhost:8000/docs
2. **Register User** - สร้าง user ใหม่ผ่าน API หรือ frontend
3. **Upload Document** - ทดลอง upload HR document
4. **ทดสอบ Chat** - ถามคำถามเกี่ยวกับ documents
5. **ดู Logs** - ตรวจสอบ logs เพื่อเข้าใจ flow

---

## 📚 เอกสารอ้างอิงเพิ่มเติม

- [README.md](../../README.md) — ภาพรวมโปรเจกต์
- [deployment.md](../deployment.md) — Production deployment
- [security.md](../security.md) — Security features
- [api-reference.md](../api-reference.md) — API documentation
- [CLAUDE.md](../../CLAUDE.md) — Project structure & commands

---

*คู่มือนี้ปรับปรุงล่าสุด: 8 มีนาคม 2569 (2026-03-08)*
