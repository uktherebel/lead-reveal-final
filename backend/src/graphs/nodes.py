import logging
import sys
import os
from typing import Dict, Any
from datetime import datetime

# Add the backend directory to Python path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from src.state.schemas import LearningState, LearningPhase
from src.workers.validated_worker import ValidatedSolutionWorker
from src.workers.decomposer import Decomposer

logger = logging.getLogger(__name__)

async def generate_validated_code_node(state: LearningState) -> Dict[str, Any]:
    """
    Generate and validate code solution.
    """
    logger.info(f"Generating validated code for: {state['task_description']}")

    try:
        # Update phase
        state['current_phase'] = LearningPhase.CODE_GENERATION

        # Use validated worker
        worker = ValidatedSolutionWorker()
        result = await worker.process({
            'task_description': state['task_description'],
            'difficulty_level': state['difficulty_level']
        })

        if result['success']:
            # Update state with validated code
            return {
                'code_solution': result['code'],
                'validated_code': result['code'],
                'validation_results': result.get('validation'),
                'sandbox_results': [result.get('validation', {})],
                'current_phase': LearningPhase.VALIDATION,
                'messages': state['messages'] + [{
                    'type': 'code_validated',
                    'content': 'Code generated and validated successfully',
                    'timestamp': datetime.now().isoformat(),
                    'validation': result.get('validation')
                }],
                'updated_at': datetime.now().isoformat()
            }
        else:
            return {
                'error': result.get('error', 'Code generation failed'),
                'messages': state['messages'] + [{
                    'type': 'error',
                    'content': f"Generation failed: {result.get('error')}",
                    'timestamp': datetime.now().isoformat()
                }],
                'updated_at': datetime.now().isoformat()
            }

    except Exception as e:
        logger.error(f"Node error: {e}")
        return {
            'error': str(e),
            'messages': state['messages'] + [{
                'type': 'error',
                'content': str(e),
                'timestamp': datetime.now().isoformat()
            }],
            'updated_at': datetime.now().isoformat()
        }

async def decompose_validated_code_node(state: LearningState) -> Dict[str, Any]:
    """
    Decompose validated code into learning steps.
    """
    logger.info("Decomposing validated code into learning steps")

    code = state.get('validated_code') or state.get('code_solution')
    if not code:
        return {
            'error': 'No code to decompose',
            'messages': state['messages'] + [{
                'type': 'error',
                'content': 'No validated code available',
                'timestamp': datetime.now().isoformat()
            }]
        }

    try:
        state['current_phase'] = LearningPhase.DECOMPOSITION

        decomposer = Decomposer()
        result = decomposer.generate_steps(code)
        steps = result.get('steps', [])

        # Calculate cognitive load distribution
        cognitive_loads = [step.get('cognitive_load', 3) for step in steps]
        avg_load = sum(cognitive_loads) / len(cognitive_loads) if cognitive_loads else 3

        return {
            'steps': steps,
            'current_step': 0,
            'total_steps': len(steps),
            'current_phase': LearningPhase.QUESTIONING,
            'analytics_data': {
                'average_cognitive_load': avg_load,
                'max_cognitive_load': max(cognitive_loads) if cognitive_loads else 0,
                'min_cognitive_load': min(cognitive_loads) if cognitive_loads else 0
            },
            'messages': state['messages'] + [{
                'type': 'decomposition_complete',
                'content': f'Created {len(steps)} learning steps',
                'details': {
                    'total_steps': len(steps),
                    'average_difficulty': round(avg_load, 1)
                },
                'timestamp': datetime.now().isoformat()
            }],
            'updated_at': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Decomposition error: {e}")
        return {
            'error': str(e),
            'messages': state['messages'] + [{
                'type': 'error',
                'content': f'Decomposition failed: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }]
        }

