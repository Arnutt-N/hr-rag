

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

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
