from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from dotenv import load_dotenv
from typing import List, Dict, Any 
from src.prompts.decomposition_prompt import decomposition_prompt
from base_worker import BaseWorker
from prompts.decomposition_prompt import decomposition_prompt
from pydantic import Field, BaseModel
from state.schemas import LearningState, LearningPhase, StepDetail
import logging

logger = logging.getLogger(__name__)

load_dotenv()

class Decompose(BaseWorker): 
  def _setup(self): 
      self.decomposition_prompt = decomposition_prompt
      logger.info("Decomposer initialized")

      class Step(StepDetail):
         questions: List[str] = Field(..., description='Set to []')

      class StepsSchema(BaseModel): 
         steps: List[Step] = Field(
            ..., 
            description="List of ordered steps; each step must include step_number, code, explanation, concept, cognitive_load, questions, reveal."
         
         )
      
      self.model = self.llm.with_structured_output(StepsSchema)

  async def process(self, code_solution: str):
     prompt = decomposition_prompt.format_prompt(code=code_solution)
     result = self.model.ainvoke(prompt)
     return {
        'steps': result.steps
     }
   
if __name__ == "__main__": 
  pass 