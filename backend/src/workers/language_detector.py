from typing import Dict, Any
import logging
from src.workers.base_worker import BaseWorker
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)

class LanguageDetectionWorker(BaseWorker):
    """
    Worker that detects programming language from task description using LLM.
    """

    def _setup(self):
        """Initialize language detection prompt"""
        self.detection_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a programming language detection expert. Analyze the task description and determine which programming language is most appropriate.

DETECTION RULES:
1. Look for explicit language mentions (e.g., "write a Python function", "C++ program", "Java class", "Dart", "Go", "Rust")
2. Consider algorithm/data structure contexts (often Python/C++)
3. Web development contexts (JavaScript/HTML/CSS)
4. Mobile app contexts (Swift/Kotlin/Dart/Flutter)
5. Database contexts (SQL)
6. System programming contexts (C/C++/Rust/Go)
7. If no clear indicators, default to "python" for general programming tasks

CRITICAL: Return ONLY the language name in lowercase (e.g., "python", "cpp", "java", "dart", "go", "rust", etc.) - no explanations or additional text."""),
            ("human", "Task description: {task}\n\nDetected language:")
        ])

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect programming language from task description.
        """
        task_description = input_data.get('task_description', '')
        
        try:
            logger.info(f"Detecting language for task: {task_description[:100]}...")
            
            chain = self.detection_prompt | self.llm
            response = await chain.ainvoke({
                'task': task_description
            })
            
            detected_language = response.content.strip().lower()
            
            # Basic validation - ensure it's a reasonable programming language name
            if not detected_language or len(detected_language) > 20 or ' ' in detected_language:
                logger.warning(f"Invalid language detection '{detected_language}', defaulting to Python")
                detected_language = 'python'
            
            logger.info(f"Detected language: {detected_language}")
            
            return {
                'success': True,
                'programming_language': detected_language,
                'task_description': task_description
            }
            
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'programming_language': 'python',  # Fallback to Python
                'task_description': task_description
            }

    def process_sync(self, input_data: dict) -> dict:
        import asyncio
        return asyncio.run(self.process(input_data))