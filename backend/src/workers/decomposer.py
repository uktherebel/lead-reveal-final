import logging
from typing import List

from dotenv import load_dotenv
from pydantic import Field, BaseModel

from src.prompts.decomposition_prompt import decomposition_prompt
from src.state.schemas import StepDetail
from src.workers.base_worker import BaseWorker

logger = logging.getLogger(__name__)

load_dotenv()

class Decompose(BaseWorker): 
  def _setup(self): 
      self.decomposition_prompt = decomposition_prompt
      logger.info("Decomposer initialised")

      class Step(StepDetail):
         questions: List[str] = Field(..., description='Set to []')

      class StepsSchema(BaseModel): 
         steps: List[Step] = Field(
            ..., 
            description="List of ordered steps; each step must include step_number, code, explanation, concept, cognitive_load, questions, reveal."
         
         )
      
      self.model = self.llm.with_structured_output(StepsSchema, method="function_calling")


  async def process(self, code_solution: str):
     prompt = decomposition_prompt.format_prompt(code=code_solution)
     result = await self.model.ainvoke(prompt)
     return {
        'steps': result.model_dump().get('steps')
     }
  
  def process_sync(self, code_solution: str) -> dict:
      import asyncio
      return asyncio.run(self.process(code_solution))   
  

if __name__ == "__main__": 
  pass 