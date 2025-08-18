import logging
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from pydantic import Field, BaseModel
from src.prompts.question_prompt import (
    cognitive_load_1_prompt, 
    cognitive_load_2_prompt, 
    cognitive_load_3_prompt, 
    cognitive_load_4_prompt, 
    cognitive_load_5_prompt
)
from src.state.schemas import Question
from src.workers.base_worker import BaseWorker


logger = logging.getLogger(__name__)

class QuestionsOut(BaseModel):
    items: list[Question] = Field(default_factory=list)

class BaseQuestionWorker(BaseWorker):
    """Base class for cognitive load question workers"""
    
    def _setup(self):
        self.model = self.llm.with_structured_output(QuestionsOut, method="function_calling")
        
    def get_prompt_template(self) -> ChatPromptTemplate:
        raise NotImplementedError
    
    async def process(self, 
                        *,
                        code: str, 
                        step_number: int,
                        code_snippet: str,
                        concept: str, 
                        explanation: str, 
                        n: int, 
                        level: int) -> Dict[str, Any]:
        """Generate a question at this cognitive load level"""
        
        try:
            prompt = self.get_prompt_template()
            formatted_prompt = prompt.format_messages(
                code=code, 
                step_number=step_number, 
                code_snippet=code_snippet, 
                concept=concept, 
                explanation=explanation,
                n=n, 
            )
            response: QuestionsOut = await self.execute_with_retry(
                lambda: self.model.ainvoke(formatted_prompt)
            )
            return {
                'success': True, 
                'questions': [q.model_dump() for q in response.items]
            }
        except Exception as e:
            return await self.handle_error(e, {"step_number": step_number})


        
class CognitiveLoad1Worker(BaseQuestionWorker):  
    def get_prompt_template(self): return cognitive_load_1_prompt
class CognitiveLoad2Worker(BaseQuestionWorker):  
    def get_prompt_template(self): return cognitive_load_2_prompt
class CognitiveLoad3Worker(BaseQuestionWorker): 
    def get_prompt_template(self): return cognitive_load_3_prompt
class CognitiveLoad4Worker(BaseQuestionWorker):  
    def get_prompt_template(self): return cognitive_load_4_prompt
class CognitiveLoad5Worker(BaseQuestionWorker):  
    def get_prompt_template(self): return cognitive_load_5_prompt


WORKERS = {
    1: CognitiveLoad1Worker, 
    2: CognitiveLoad2Worker, 
    3: CognitiveLoad3Worker, 
    4: CognitiveLoad4Worker,
    5: CognitiveLoad5Worker,
}