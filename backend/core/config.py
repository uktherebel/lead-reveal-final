import os
from typing import Optional, Dict, Any
from pydantic import Field
from pydantic_settings import BaseSettings
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # API Keys
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    qwen_api_key: Optional[str] = Field(None, env="QWEN_API_KEY")
    e2b_api_key: str = Field(..., env="E2B_API_KEY")  

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = Field(False, env="DEBUG")

    # LLM Settings
    llm_provider: str = Field("openai", env="LLM_PROVIDER")  # "openai" or "ollama"
    llm_model: str = Field("gpt-4", env="LLM_MODEL")
    llm_temperature: float = 0.3

    # Sandboxing Configuration
    sandbox_timeout: int = 30  # seconds
    sandbox_max_memory: int = 512  # MB
    enable_sandboxing: bool = True

    # Session Management
    session_timeout: int = 3600  # 1 hour
    max_concurrent_sessions: int = 100

    # Feature Flags 
    enable_orchestration: bool = False
    enable_analytics: bool = False
    enable_time_travel: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    return Settings()




