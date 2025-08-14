from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from dotenv import load_dotenv
from typing import List, Dict, Any 
from src.prompts.decomposition_prompt import decomposition_prompt
from base_worker import BaseWorker
from prompts.decomposition_prompt import decomposition_prompt
from pydantic import Field, BaseModel
from state.schemas import LearningState, LearningPhase

load_dotenv()

class Decompose(BaseWorker): 
  def _setup(self): 
      self.decomposition_prompt = decomposition_prompt

      class Step(BaseModel): 
        step_number: int = Field(..., description='The number of the step, increment by 1')
        code_snippet: str = Field(..., description='The exact code for this step')
        explanation: str = Field(..., description="What does this step entail? What's the justification for having this step?")
        concept: str = Field(..., description='What are the concepts involved for this particular step?')
        cognitive_load: int = Field(..., description="Cognitive load 1-5, where 1=easy, 5=complex", ge=1, le=5)

      class StepsSchema(BaseModel): 
         steps: List[Step] = Field(
            ..., 
            description="List of ordered steps; each step must include step_number, code, explanation, concept, and cognitive_load."
         )
      
      self.model = self.llm.with_structured_output(StepsSchema)

  async def process(self, code_solution: str):
     prompt = decomposition_prompt.format_prompt(code=code_solution)
     steps = self.model.invoke(prompt)
     return {
        
     }
     
     
      
     
   
   

if __name__ == "__main__": 
  pass 