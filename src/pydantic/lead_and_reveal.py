from pydantic import BaseModel
from typing import List

class PlanItem(BaseModel): 
   subgoal: str
   line: str
   question: str
   followup: str

class PlanResponse(BaseModel): 
   plan: List[PlanItem]

class LeadAndRevealRequest(BaseModel):
    code_solution: str
    answer: str = None

class LeadAndRevealResponse(BaseModel):
    question: str
    evaluation: str = None
