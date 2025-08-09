from typing import TypedDict, List, Optional, Dict, Any 
from datetime import datetime 

class LearningState(TypedDict): 
  """
    State schema for learning system.
  """
  task_description: str 
  technique: str 

  session_id: Optional[str]

  # Working statee
  current_step: int 
  total_steps: int 
  code_solution: str 
  steps: List[Dict[str, Any]] 

  # output 
  messages: List[Dict[str, Any]]
  completed: bool

  # metadata 
  started_at: Optional[str]
  completed_at: Optional[str]
  error: Optional[str]

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

    