import logging 
from typing import Dict, Any 
from src.state.schemas import LearningState
from src.langchain.llm_config import create_code_chain, decomposition_chain
from datetime import datetime

logger = logging.getLogger(__name__)

def generate_code_node(state: LearningState) -> Dict[str, any]: 
  task = state['task_description']
  logger.info(f"Generating code for the task: {task}")
  try: 
    code = create_code_chain(task)
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
  logger.info('Decomposing code into steps')
  code = state.get('code_solution')

  if not code: 
     return {
            "error": "No code to decompose",
            "steps": []
        }
  steps = decomposition_chain(code)['steps']
  return {
    'steps': steps,
    'total_steps': len(steps), 
    'messages': state['messages'] + [{
      'type': 'steps_created', 
      'content': f"Created {len(steps)} learning steps", 
      'timestamp': datetime.now().isoformat()
    }]
  }

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