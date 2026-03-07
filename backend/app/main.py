"""HR-RAG Backend - FastAPI entry

Routers:
- /auth
- /projects
- /ingest
- /search
- /chat (SSE + WS)
- /llm
- /evaluation (RAG Evaluation)
- /admin (Admin Panel)

Run:
  uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.models.database import init_db

from app.routers import auth, projects, ingest, chat, llm, search, evaluation, admin

settings = get_settings()

app = FastAPI(title=settings.app_name, debug=settings.debug)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    # For dev: create tables if not exist
    # In prod: replace with Alembic migrations.
    await init_db()


@app.get("/health")
async def health():
    return {"status": "ok"}


# Routers
app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(ingest.router)
app.include_router(search.router)
app.include_router(chat.router)
app.include_router(llm.router)
app.include_router(evaluation.router)
app.include_router(admin.router)
