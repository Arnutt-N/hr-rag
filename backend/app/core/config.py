"""
HR-RAG Backend - Core Configuration
FastAPI configuration with environment variables
"""

import os
import warnings
from pydantic_settings import BaseSettings
from pydantic import model_validator
from typing import Optional, List
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # App
    app_name: str = "HR-RAG Backend"
    debug: bool = False
    
    # Database (PostgreSQL - Docker)
    # ⚠️ CRITICAL: ต้องตั้งค่าใน .env ก่อน run production!
    # Use SQLAlchemy async driver: postgresql+asyncpg
    database_url: str = ""  # อ่านจาก DATABASE_URL env
    
    # JWT Settings
    # ⚠️ CRITICAL: ต้องตั้งค่าใน .env ก่อน run production!
    jwt_secret_key: str = ""  # อ่านจาก JWT_SECRET_KEY env
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60 * 24  # 24 hours
    
    # Vector Database (Qdrant - Free, self-hosted)
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "hr_documents"
    
    # Embedding Model (Thai support)
    embedding_model: str = "BAAI/bge-m3"
    embedding_device: str = "cpu"  # or "cuda"
    embedding_batch_size: int = 32
    
    # LLM Providers - อ่านจาก environment variables
    # ใส่ API key ที่ได้จาก provider ต่างๆ ลงใน .env
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""
    
    # Ollama (Local models)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    
    # New LLM Providers - Kimi (Moonshot AI)
    kimi_api_key: str = ""
    kimi_base_url: str = "https://api.moonshot.cn/v1"
    
    # New LLM Providers - GLM (Zhipu AI)
    glm_api_key: str = ""
    glm_base_url: str = "https://open.bigmodel.cn/api/paas/v4"
    
    # New LLM Providers - MiniMax
    minimax_api_key: str = ""
    minimax_base_url: str = "https://api.minimax.chat/v1"
    
    # New LLM Providers - Qwen (Alibaba)
    qwen_api_key: str = ""
    qwen_base_url: str = "https://dashscope.aliyuncs.com/api/v1"
    
    # New LLM Providers - DeepSeek
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    
    # Custom LLM provider (OpenAI-compatible)
    custom_api_key: str = ""
    custom_base_url: str = "https://api.openai.com/v1"
    custom_model: str = "gpt-4o-mini"
    
    # Rate limiting (requests per minute per provider)
    rate_limit_per_provider: int = 60
    
    # LLM Connection Pool Settings
    llm_timeout: float = 60.0
    llm_max_retries: int = 2
    llm_max_connections: int = 100
    llm_keepalive_connections: int = 20
    
    # Default LLM provider
    default_llm_provider: str = "openai"  # openai, anthropic, google, ollama, kimi, glm, minimax, qwen, deepseek, custom
    
    # File Upload
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_extensions: list = [".pdf", ".doc", ".docx", ".txt"]
    
    # CORS - รองรับหลาย domain โดยคั่นด้วย comma
    # ตัวอย่าง: "https://example.com,http://localhost:3000"
    cors_origins_str: str = ""  # อ่าน string จาก env แล้วค่อย parse
    
    # Redis Cache
    redis_url: str = "redis://localhost:6379"
    cache_ttl_seconds: int = 3600  # 1 hour default
    chat_cache_ttl_seconds: int = 300  # 5 minutes for chat
    
    class Config:
        env_file = ".env"
        extra = "allow"
    
    @model_validator(mode="after")
    def validate_and_set_settings(self):
        """
        Task 1.1: Validate JWT Secret - ถ้าไม่มีค่าใน env ให้ใช้ dev default
        Task 1.2: Parse CORS Origins จาก comma-separated string
        Task 1.3: API Keys อ่านจาก env แล้ว (pydantic ทำเอง) แต่ต้อง ensure ไม่มี hardcoded
        Task 1.4: Validate DATABASE_URL
        """
        
        # Task 1.4: Database URL validation
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            self.database_url = db_url
        elif not self.database_url:
            # Dev default for Docker
            self.database_url = "postgresql+asyncpg://postgres:postgres@postgres:5432/hr_rag"
            warnings.warn(
                "⚠️ DATABASE_URL ไม่ได้ตั้งค่า! ใช้ค่า default สำหรับ development\n"
                "สำหรับ production: ตั้งค่าใน .env",
                UserWarning
            )
        
        # Task 1.1: JWT Secret validation
        jwt_secret = os.getenv("JWT_SECRET_KEY")
        if jwt_secret:
            self.jwt_secret_key = jwt_secret
        elif not self.jwt_secret_key or self.jwt_secret_key == "":
            # ใช้ค่า default ใน dev mode แต่ warning
            warnings.warn(
                "⚠️ JWT_SECRET_KEY ไม่ได้ตั้งค่า! กรุณาตั้งค่าใน .env สำหรับ production\n"
                "สร้าง secret: openssl rand -hex 64",
                UserWarning
            )
            self.jwt_secret_key = "dev-only-secret-change-in-production"
        
        # Task 1.2: CORS Origins - parse comma-separated list
        cors_env = os.getenv("CORS_ORIGINS", "")
        if cors_env:
            # แยกด้วย comma และ strip whitespace
            self.cors_origins_str = cors_env
        elif not self.cors_origins_str:
            # Default เป็น localhost ถ้าไม่ได้ตั้งค่า
            self.cors_origins_str = "http://localhost:3000,http://127.0.0.1:3000"
        
        return self
    
    @property
    def cors_origins(self) -> List[str]:
        """Property สำหรับ get CORS origins เป็น list"""
        if isinstance(self.cors_origins_str, list):
            return self.cors_origins_str
        return [origin.strip() for origin in self.cors_origins_str.split(",") if origin.strip()]


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
