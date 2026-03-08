

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, EmailStr

class SearchRequest(BaseModel):
    query: str
    project_id: Optional[int] = None
    top_k: int = Field(default=5, ge=1, le=20)  # Configurable, max 20


class SearchResult(BaseModel):
    text: str
    score: float
    document_id: int
    filename: str


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    cached: bool = False  # Whether result was served from cache


# ==================== ADMIN / AUDIT SCHEMAS ====================

class SystemLogLevel(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"


class SystemLogCreate(BaseModel):
    level: SystemLogLevel = SystemLogLevel.INFO
    message: str = Field(..., min_length=1, max_length=5000)
    source: Optional[str] = Field(default=None, max_length=255)
    user_id: Optional[int] = None
    ip_address: Optional[str] = Field(default=None, max_length=64)
    user_agent: Optional[str] = Field(default=None, max_length=512)
    details: Optional[dict] = None


class SystemLogResponse(BaseModel):
    id: int
    timestamp: datetime
    level: SystemLogLevel
    message: str
    source: Optional[str]
    user_id: Optional[int]
    ip_address: Optional[str]
    user_agent: Optional[str]
    details: Optional[dict]

    class Config:
        from_attributes = True


class LoginAttemptCreate(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    success: bool
    ip_address: Optional[str] = Field(default=None, max_length=64)
    user_agent: Optional[str] = Field(default=None, max_length=512)
    failure_reason: Optional[str] = Field(default=None, max_length=255)


class LoginAttemptResponse(BaseModel):
    id: int
    username: str
    success: bool
    ip_address: Optional[str]
    user_agent: Optional[str]
    failure_reason: Optional[str]
    timestamp: datetime

    class Config:
        from_attributes = True


# ==================== LLM PROVIDER ENUM ====================

class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OLLAMA = "ollama"
    KIMI = "kimi"
    GLM = "glm"
    MINIMAX = "minimax"
    QWEN = "qwen"
    DEEPSEEK = "deepseek"
    CUSTOM = "custom"


# ==================== AUTH SCHEMAS ====================

class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^\w+$")
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: Optional[str]
    is_member: bool
    is_active: bool

    class Config:
        from_attributes = True


# ==================== CHAT SCHEMAS ====================

class ChatRequest(BaseModel):
    message: str
    project_id: int
    session_id: Optional[int] = None
    stream: bool = False
    llm_provider: Optional[LLMProvider] = None
