import asyncio
import logging
import uuid
from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from pydantic import Field, BaseModel

from src.prompts.level_batch_prompt import get_batch_prompt_for_level
from src.state.schemas import Question
from src.workers.base_worker import BaseWorker

logger = logging.getLogger(__name__)

# Semaphore to control concurrency and avoid rate limits
BATCH_SEM = asyncio.Semaphore(5)  # Allow up to 5 concurrent batch calls

class StepQuestions(BaseModel):
    step_number: int = Field(..., description="The step number")
    questions: List[Question] = Field(default_factory=list, description="Questions for this step")

class BatchQuestionsOut(BaseModel):
    questions_by_step: List[StepQuestions] = Field(default_factory=list, description="Questions organized by step")

class BatchQuestionWorker(BaseWorker):
    """Worker that generates questions for ALL steps at a specific cognitive level in ONE call"""
    
    def _setup(self):
        self.model = self.llm.with_structured_output(BatchQuestionsOut, method="function_calling")
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Implementation of abstract process method - delegates to process_batch_level"""
        return await self.process_batch_level(**input_data)
    
    def _format_steps_info(self, steps: List[Dict[str, Any]]) -> str:
        """Format steps info for the prompt"""
        steps_text = ""
        for step in steps:
            steps_text += f"""
Step {step['step_number']}:
- Code snippet: {step['code_snippet']}
- Concept: {step['concept']}
- Explanation: {step['explanation']}
- Intrinsic load: {step.get('intrinsic_load', 3)}

"""
        return steps_text.strip()
    
    async def process_batch_level(self,
                                  *,
                                  steps: List[Dict[str, Any]],
                                  code: str, 
                                  cognitive_level: int,
                                  n_per_level: int = 1) -> Dict[str, Any]:
        """Generate questions for ALL steps at a specific cognitive level in a single call"""
        
        try:
            prompt = get_batch_prompt_for_level(cognitive_level)
            steps_info = self._format_steps_info(steps)
            
            formatted_prompt = prompt.format_messages(
                code=code,
                steps_info=steps_info,
                n_per_step=n_per_level
            )
            
            # Use semaphore to control concurrency
            async with BATCH_SEM:
                response: BatchQuestionsOut = await self.execute_with_retry(
                    lambda: self.model.ainvoke(formatted_prompt)
                )
                # Add delay to avoid rate limiting (like in normal mode)
                await asyncio.sleep(0.5)
            
            # Convert to the expected format and assign IDs and cognitive loads
            questions_by_step = {}
            for step_questions in response.questions_by_step:
                questions = []
                for q in step_questions.questions:
                    question_dict = q.model_dump()
                    question_dict['id'] = str(uuid.uuid4())
                    question_dict['cognitive_load'] = cognitive_level
                    questions.append(question_dict)
                
                questions_by_step[step_questions.step_number] = questions
            
            return {
                'success': True,
                'questions_by_step': questions_by_step,
                'total_questions': sum(len(qs) for qs in questions_by_step.values())
            }
            
        except Exception as e:
            logger.error(f"Batch question generation failed for level {cognitive_level}: {e}")
            return await self.handle_error(e, {
                "cognitive_level": cognitive_level,
                "num_steps": len(steps),
                "n_per_level": n_per_level
            })