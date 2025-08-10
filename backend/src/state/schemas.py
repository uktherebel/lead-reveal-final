from typing import TypedDict, List, Optional, Dict, Any, Literal
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator

class LearningPhase(Enum):
    INITIALIZATION = "initialization"
    CODE_GENERATION = "code_generation"
    VALIDATION = "validation"
    DECOMPOSITION = "decomposition"
    QUESTIONING = "questioning"
    EVALUATION = "evaluation"
    COMPLETION = "completion"

class StepDetail(BaseModel): 
    step_number: int 
    code_snippet: str 
    explanation: str 
    concept: str 
    cognitive_load: int = Field(ge=1, le=5)
    questions: List[Dict[str, Any]] = []
    reveral: bool = False 

    @field_validator('cognitive_load')
    @classmethod
    def validate_cognitive_load(cls, v):
        """Ensures cognitive load is within learning theory bounds"""
        if not 1 <= v <= 5:
            raise ValueError('Cognitive load must be between 1 and 5')
        return v 

class LearningState(TypedDict): 
  """
    State schema for learning system.
  """
  # Identification
  session_id: str
  user_id = Optional[str]

  # Task config
  task_description: str 
  difficulty_level: Literal['beginner', 'intermediate', 'advanced']

  # Learning content
  code_solution: str
  validated_code: Optional[str]
  validation_results: Optional[Dict[str, Any]]

  # Steps 
  steps: List[StepDetail]
  current_step: int 
  total_steps: int 
  current_phase: LearningPhase

  # Q&A tracking
  current_question: Optional[Dict[str, Any]]
  user_answers: List[Dict[str, any]]
  answer_attempts: int 
  hints_used: int

  # Performance matrics 
  score: int 
  accuracy_rate: float 
  average_response_time: float 
  learning_velocity: float # steps / min 

  # Session management  
  messages: List[Dict[str, Any]]
  completed: bool
  can_resume: bool
  error: Optional[str]

  # Timestamps 
  started_at: str
  updated_at: str 
  completed_at: Optional[str]

  # Advanced features
  checkpoint_data: Dict['str', Any]
  analytics_data: Dict['str', Any]
  sandbox_results = List[Dict[str, Any]]

def create_initial_state(task: str, technique: str) -> LearningState: 
     """
    Factory function to create a new learning state.

    args:
        task: What the user wants to learn
        technique: Which learning technique to use

    returns:
        Dictionary of state updates (merged with existing state)
    """
     return {
         'task_description': task, 
         'technique': technique, 
         'session_id': f"session_{datetime.now().timestamp()}",
         'current_step': 0,
         'total_steps': 0, 
         'code_solution': "", 
         "steps": [],
         "messages": [],
         "completed": False,
         "started_at": datetime.now().isoformat(),
         "completed_at": None,
         "error": None
     }

    