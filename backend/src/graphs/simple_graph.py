from langgraph.graph import StateGraph
from langgraph.graph import END, START
from typing import Dict, Any 
import logging 

from src.state.schemas import LearningState
from src.graphs.nodes import (
  generate_code_node, 
  decompose_code_node, 
  finalise_node
)

logger = logging.getLogger(__name__)

def should_continue(state: LearningState) -> str: 
  if state.get('code_solution') and not state.get('error'):
    return 'decompose_code'
  else:
    return 'finalise'

def create_simple_graph(): 
  workflow = StateGraph(LearningState)

  workflow.add_node('generate_code', generate_code_node)
  workflow.add_node('decompose_code', decompose_code_node)
  workflow.add_node('finalise', finalise_node)

  workflow.add_edge(START, 'generate_code')
  workflow.add_conditional_edges(
    'generate_code', 
    should_continue
  )
  workflow.add_edge('decompose_code', 'finalise')
  workflow.add_edge('finalise', END)

  return workflow.compile()