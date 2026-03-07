"""
HR-RAG Backend - Database
SQLAlchemy async engine/session + ORM models for TiDB Cloud (MySQL)

Note: TiDB Cloud is MySQL-compatible; use `mysql+aiomysql://...` for async.
"""

from datetime import datetime
import enum
from typing import AsyncGenerator

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean,
    ForeignKey, Enum, JSON
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.config import get_settings

settings = get_settings()

Base = declarative_base()

# Async DB engine/session
engine = create_async_engine(settings.database_url, pool_pre_ping=True, future=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    """Create tables (dev convenience). In prod, prefer migrations."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    MEMBER = "member"
    USER = "user"


class LLMProvider(str, enum.Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OLLAMA = "ollama"


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    
    # Role & Status
    role = Column(Enum(UserRole), default=UserRole.USER)
    is_member = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Preferences
    preferred_llm_provider = Column(Enum(LLMProvider), default=LLMProvider.OPENAI)
    preferred_embedding_model = Column(String(100), default="BAAI/bge-m3")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")


class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Owner
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Project settings
    is_public = Column(Boolean, default=False)
    settings = Column(JSON, default=dict)  # LLM config, embedding config, etc.
    
    # Vector collection name (isolated per project)
    vector_collection = Column(String(100), unique=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owner = relationship("User", back_populates="projects")
    documents = relationship("Document", back_populates="project", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="project", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_type = Column(String(50))  # pdf, doc, docx, txt
    
    # Content
    content = Column(Text)  # Extracted text
    file_size = Column(Integer)  # bytes
    page_count = Column(Integer, nullable=True)
    
    # Project relationship
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    
    # Vector DB reference
    vector_ids = Column(JSON, default=list)  # List of vector IDs in Qdrant
    
    # Processing status
    is_indexed = Column(Boolean, default=False)
    chunk_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="documents")


class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), default="New Chat")
    
    # Relationships
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    project = relationship("Project", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    
    # Message content
    role = Column(String(20), nullable=False)  # user, assistant
    content = Column(Text, nullable=False)
    
    # Optional: for RAG context
    context_docs = Column(JSON, default=list)  # Source documents used
    token_count = Column(Integer, nullable=True)
    
    # LLM provider used
    llm_provider = Column(String(50), nullable=True)
    llm_model = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")
