from typing import TypedDict, Dict, Any
from langgraph.graph import StateGraph, END, START 
from services.batch_questions import gen_questions_for_level_batch

class BatchState(TypedDict):
    code: str
    steps_by_level: list[Dict[str, Any]]  # Steps at this cognitive level
    cognitive_level: int
    n_per_level: int
    step_updates: list[Dict[str, Any]]  # For output

async def batch_level_node(state: BatchState) -> Dict[str, Any]:
    """Generate questions for all steps at a specific cognitive level"""
    updated_steps = await gen_questions_for_level_batch(
        steps_by_level=state["steps_by_level"],
        code=state["code"], 
        cognitive_level=state["cognitive_level"],
        n_per_level=state["n_per_level"]
    )
    # Return in format expected by build_assets_graph reducer
    return {"step_updates": updated_steps}

batch_graph = StateGraph(BatchState)
batch_graph.add_node("generate", batch_level_node)
batch_graph.add_edge(START, 'generate')
batch_graph.add_edge("generate", END)
compiled_batch_graph = batch_graph.compile()