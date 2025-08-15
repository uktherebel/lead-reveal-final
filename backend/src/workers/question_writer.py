import logging
from typing import Dict, Any, List, Optional
from langchain_core.prompts import ChatPromptTemplate
from src.workers.base_worker import BaseWorker
from src.prompts import questions_prompt
from state.schemas import Question
import json
import re

logger = logging.getLogger(__name__)

class QuestionWriter(BaseWorker):

    def _setup(self):
        self.question_prompt = questions_prompt
        logger.info("QuestionWriter initialized")

        self.model = self.llm.with_structured_output(Question)


    async def generate_question(self,
                               code: str,
                               explanation: str,
                               title: str = "Code Step",
                               difficulty: str = "intermediate") -> Dict[str, Any]:
        """Generate a Socratic question for a code step"""

        try:
            chain = self.question_prompt | self.llm
            response = await chain.ainvoke({
                "title": title,
                "code": code,
                "explanation": explanation,
                "difficulty": difficulty
            })

        except Exception as e:
            logger.error(f"Question generation failed: {e}")
            return self._create_fallback_question(code, explanation)

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process method for BaseWorker compatibility"""

        code = input_data.get("code", "")
        explanation = input_data.get("explanation", "")
        title = input_data.get("title", "Code Step")
        difficulty = input_data.get("difficulty", "intermediate")

        question = await self.generate_question(code, explanation, title, difficulty)

        return {
            "success": True,
            "question_data": question,
            "worker": "question_writer"
        }
