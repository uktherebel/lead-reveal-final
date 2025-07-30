import logging 
from typing import Dict, Any 
from src.state.schemas import LearningState
from src.workers.coder import Coder
from datetime import datetime
from src.workers.decomposer import Decomposer

logger = logging.getLogger(__name__)

def generate_code_node(state: LearningState) -> Dict[str, any]: 
  task = state['task_description']
  logger.info(f"Generating code for the task: {task}")
  try: 
    coder = Coder()
    code = coder.generate_code(task)
    return {
      'code_solution': code, 
      'messages': state['messages'] + [{
        'type': 'code_generated', 
        'content': code, 
        'timestamp': datetime.now().isoformat()
      }]
    }

  except Exception as e: 
    logger.error(f"Error generating code: {e}")
    return {
      "error": str(e), 
      'messages': state['messages'] + [{
        'type': 'error', 
        'content': f"Failed to generate code: {str(e)}",
        'timestamp': datetime.now().isoformat(),
      }]
    }

def decompose_code_node(state: LearningState) -> Dict[str, any]: 
  decomposer = Decomposer()
  logger.info('Decomposing code into steps')
  code = state.get('code_solution', "")

  if not code: 
     state['messages'].append({
            "type": "error",
            "content": "No code to decompose",
            "timestamp": 'now',
        })
     return state 
  
  try:
    steps = decomposer.generate_steps(code)['steps']
    state['steps'] = steps,
    state['current_step'] = 0
    state['total_steps'] = len(steps)

    cognitive_loads = [step.get('cognitive_load', 3) for step in steps]
    avg_difficulty = sum(cognitive_loads) / len(cognitive_loads) if cognitive_loads else 3


    state['messages'].append({
        'type': 'steps_created', 
        'content': f"Created {len(steps)} learning steps", 
        "details": {
            "total_steps": len(steps),
            "average_difficulty": round(avg_difficulty, 1),
            "difficulty_range": f"{min(cognitive_loads)}-{max(cognitive_loads)}"
        },
      })
  
  except Exception as e: 
    print(f'Error creating steps: {str(e)}')
    state['messages'].append({
      'type': 'error', 
      'content': f'Failed to generate learning steps: {str(e)}',
      'timestamp': 'now'
    }) 
  return state 

def finalise_node(state: LearningState) -> Dict[str, any]: 
  logger.info("Finalising learning session")
  summary = {
    'task': state['task_description'], 
    'technique': state['technique'], 
    'code_length': len(state.get("code_solution", "")),
    "steps_created": state.get("total_steps", 0)
  }

  return {
        "completed": True,
        "completed_at": datetime.now().isoformat(),
        "messages": state['messages'] + [
          {
            'type': 'session_complete', 
            'content': 'Learning session completed', 
            'summary': summary, 
            'timestamp': datetime.now().isoformat()
          }
        ]
  }