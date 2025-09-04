import logging
import os
import json
from typing import List

from dotenv import load_dotenv
from pydantic import Field, BaseModel

from src.prompts.decomposition_prompt import decomposition_prompt
from src.prompts.decomposition_refine_prompt import decomposition_refine_prompt
from src.state.schemas import StepDetail
from src.workers.base_worker import BaseWorker

logger = logging.getLogger(__name__)

load_dotenv()

class Decompose(BaseWorker): 
  def _setup(self): 
      self.decomposition_prompt = decomposition_prompt
      logger.info("Decomposer initialised")

      # Create a step schema without the questions field for decomposition
      class Step(BaseModel):
         step_number: int = Field(..., description='The number of the step, increment by 1')
         code_snippet: str = Field(..., description='The exact code for this step')
         explanation: str = Field(..., description="What does this step entail? What's the justification for having this step?")
         concept: str = Field(..., description='What are the concepts involved for this particular step?')
         reveal: bool = Field(default=False)
         intrinsic_load: int = Field(default=3, ge=1, le=5)

      class StepsSchema(BaseModel): 
         steps: List[Step] = Field(
            ..., 
            description="List of ordered steps; each step must include step_number, code_snippet, explanation, concept, intrinsic_load."
         
         )
      
      self.model = self.llm.with_structured_output(StepsSchema, method="function_calling")


  async def process(self, code_solution: str):
     strategy = os.getenv("DECOMP_STRATEGY", "ts_llm").lower()
     if strategy in ("ast_llm", "ts_llm"):
         try:
             if strategy == "ts_llm":
                 from services.ts_slicing import build_steps_from_code
             else:
                 from services.ast_slicing import build_steps_from_code
             skeleton = build_steps_from_code(code_solution)
             if skeleton:
                 refine_prompt = decomposition_refine_prompt.format_prompt(
                     code=code_solution,
                     steps_json=json.dumps(skeleton, ensure_ascii=False)
                 )
                 result = await self.model.ainvoke(refine_prompt)
                 return {'steps': result.model_dump().get('steps')}
         except Exception as e:
             logger.warning(f"AST+LLM failed, fallback to LLM-only: {e}")

     # Fallback: original LLM-only decomposition
     prompt = self.decomposition_prompt.format_prompt(code=code_solution)
     result = await self.model.ainvoke(prompt)
     return {'steps': result.model_dump().get('steps')}
  
  def process_sync(self, code_solution: str) -> dict:
      import asyncio
      return asyncio.run(self.process(code_solution))   
  

if __name__ == "__main__": 
  pass 
