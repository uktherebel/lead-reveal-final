import os
from typing import Optional, Dict, Any
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # API Keys
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    qwen_api_key: Optional[str] = Field(None, env="QWEN_API_KEY")
    e2b_api_key: Optional[str] = Field(None, env="E2B_API_KEY")

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = Field(False, env="DEBUG")
    
    @field_validator('debug', mode='before')
    @classmethod
    def parse_debug(cls, v):
        """Convert string values to boolean for debug field"""
        if isinstance(v, str):
            return v.lower() in ('true', '1', 'yes', 'on')
        return bool(v) if v is not None else False

    # LLM Settings
    llm_provider: str = Field("openai", env="LLM_PROVIDER")
    llm_model: str = Field("gpt-4o-mini", env="LLM_MODEL")  # gpt-4o-mini supports structured outputs
    llm_temperature: float = 0.3

    # Sandboxing Configuration
    sandbox_timeout: int = 30  # seconds
    sandbox_max_memory: int = 512  # MB
    enable_sandboxing: bool = True

    # Database Configuration
    database_url: str = Field("postgresql+asyncpg://postgres:password@localhost:5433/learningdb", env="DATABASE_URL")
    redis_url: Optional[str] = Field(None, env="REDIS_URL")

    # Session Management
    session_timeout: int = 3600  # 1 hour
    max_concurrent_sessions: int = 100

    # Feature Flags 
    enable_orchestration: bool = False
    enable_analytics: bool = False
    enable_time_travel: bool = False
    
    @field_validator('enable_sandboxing', 'enable_orchestration', 'enable_analytics', 'enable_time_travel', mode='before')
    @classmethod
    def parse_boolean_flags(cls, v):
        """Convert string values to boolean for feature flags"""
        if isinstance(v, str):
            return v.lower() in ('true', '1', 'yes', 'on')
        return bool(v) if v is not None else False

    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()




