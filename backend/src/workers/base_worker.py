from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import asyncio
import logging
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from core.config import get_settings

logger = logging.getLogger(__name__)

class BaseWorker(ABC):
    """
    Abstract base class for all workers.
    """

    def __init__(self):
        settings = get_settings()

        # Initialise LLM based on configuration
        if settings.llm_provider == "openai":
            self.llm = ChatOpenAI(
                model=settings.llm_model,
                temperature=settings.llm_temperature,
                api_key=settings.openai_api_key
            )
        else:
            self.llm = ChatOllama(
                model=settings.llm_model,
                temperature=settings.llm_temperature
            )

        self.settings = settings
        self._setup()

    @abstractmethod
    def _setup(self):
        """Initialize worker-specific components"""
        pass

    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main processing method - must be implemented by subclasses"""
        pass

    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input before processing.
        """
        return input_data is not None

    async def handle_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Centralised error handling.
        """
        logger.error(f"{self.__class__.__name__} error: {error}", extra=context)
        return {
            'success': False,
            'error': str(error),
            'worker': self.__class__.__name__,
            'context': context
        }

    async def execute_with_retry(
        self,
        func,
        max_retries: int = 3,
        backoff: float = 1.0
    ):
        """
        Retry logic with exponential backoff.
        """
        for attempt in range(max_retries):
            try:
                return await func()
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                wait_time = backoff * (2 ** attempt)
                logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time}s")
                await asyncio.sleep(wait_time)
