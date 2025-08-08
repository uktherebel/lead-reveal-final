from langgraph.graph import StateGraph
from langgraph.graph import END, START
from typing import Dict, Any 
import logging 
from state.schemas import LearningState
from utils.logging_setup import logger
from node_functions import (
  generate_code_node, 
  decompose_code_node, 
  finalise_node
)

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