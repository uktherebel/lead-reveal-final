import sys
import os

# Add the backend directory to Python path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from langgraph.graph import StateGraph, END, START
from src.state.schemas import LearningState
from nodes import (
    generate_validated_code_node,
    decompose_validated_code_node,
)
from edges import (
    should_continue_after_generation,
    should_continue_after_decomposition
)
from typing import Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def create_enhanced_graph():
    """
    Create the enhanced learning graph with validation.
    """
    workflow = StateGraph(LearningState)

    # Add nodes
    workflow.add_node('generate_code', generate_validated_code_node)
    workflow.add_node('decompose', decompose_validated_code_node)
    workflow.add_node('finalize', finalize_node)

    # Add edges
    workflow.add_edge(START, 'generate_code')
    workflow.add_conditional_edges(
        'generate_code',
        should_continue_after_generation,
        {
            'decompose': 'decompose',
            'handle_error': 'finalize',
            'validate': 'generate_code',  # Retry with validation
            'retry_generation': 'generate_code'
        }
    )
    workflow.add_conditional_edges(
        'decompose',
        should_continue_after_decomposition,
        {
            'start_questioning': 'finalize',  
            'handle_error': 'finalize',
            'finalize': 'finalize'
        }
    )
    workflow.add_edge('finalize', END)

    return workflow.compile()

def finalize_node(state: LearningState) -> Dict[str, Any]:
    """
    Finalise the learning session.
    """
    from src.state.schemas import LearningPhase

    summary = {
        'task': state['task_description'],
        'technique': state['technique'],
        'code_generated': bool(state.get('code_solution')),
        'code_validated': bool(state.get('validated_code')),
        'steps_created': state.get('total_steps', 0),
        'duration': calculate_duration(state['started_at']),
        'final_phase': state.get('current_phase', LearningPhase.INITIALIZATION).value
    }

    return {
        'completed': True,
        'completed_at': datetime.now().isoformat(),
        'current_phase': LearningPhase.COMPLETION,
        'messages': state['messages'] + [{
            'type': 'session_complete',
            'content': 'Learning session completed',
            'summary': summary,
            'timestamp': datetime.now().isoformat()
        }],
        'updated_at': datetime.now().isoformat()
    }

def calculate_duration(start_time: str) -> float:
    """Calculate session duration in minutes"""
    from datetime import datetime
    start = datetime.fromisoformat(start_time)
    end = datetime.now()
    return (end - start).total_seconds() / 60