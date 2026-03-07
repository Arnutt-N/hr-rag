"""
HR-RAG Backend - Core Configuration
FastAPI configuration with environment variables
"""

from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # App
    app_name: str = "HR-RAG Backend"
    debug: bool = False
    
    # Database (TiDB Cloud - MySQL compatible)
    # Use SQLAlchemy async driver: mysql+aiomysql
    database_url: str = "mysql+aiomysql://user:password@host:4000/hr_rag"
    
    # JWT Settings
    jwt_secret_key: str = "your-secret-key-change-in-production"
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
    
    # LLM Providers
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    
    # Ollama (Local models)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    
    # New LLM Providers - Kimi (Moonshot AI)
    kimi_api_key: Optional[str] = None
    kimi_base_url: str = "https://api.moonshot.cn/v1"
    
    # New LLM Providers - GLM (Zhipu AI)
    glm_api_key: Optional[str] = None
    glm_base_url: str = "https://open.bigmodel.cn/api/paas/v4"
    
    # New LLM Providers - MiniMax
    minimax_api_key: Optional[str] = None
    minimax_base_url: str = "https://api.minimax.chat/v1"
    
    # New LLM Providers - Qwen (Alibaba)
    qwen_api_key: Optional[str] = None
    qwen_base_url: str = "https://dashscope.aliyuncs.com/api/v1"
    
    # New LLM Providers - DeepSeek
    deepseek_api_key: Optional[str] = None
    deepseek_base_url: str = "https://api.deepseek.com"
    
    # Custom LLM provider (OpenAI-compatible)
    custom_api_key: Optional[str] = None
    custom_base_url: str = "https://api.openai.com/v1"
    custom_model: str = "gpt-4o-mini"
    
    # Rate limiting (requests per minute per provider)
    rate_limit_per_provider: int = 60
    
    # Default LLM provider
    default_llm_provider: str = "openai"  # openai, anthropic, google, ollama, kimi, glm, minimax, qwen, deepseek, custom
    
    # File Upload
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_extensions: list = [".pdf", ".doc", ".docx", ".txt"]
    
    # CORS
    cors_origins: list = ["*"]
    
    class Config:
        env_file = ".env"
        extra = "allow"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
