from pydantic import BaseModel, ConfigDict
# --- Pydantic Models ---
class ChatRequest(BaseModel): 
   prompt: str 

# class TokenScore(BaseModel):
#     token: str
#    #  confidence: float

class ChatResponse(BaseModel):
    explanation: str
   #  token_scores: List[TokenScore]
   #  trust_score: float
    model_config = ConfigDict(populate_by_name=True) 