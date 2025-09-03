from typing import TypedDict, Dict, Any, Annotated
from operator import add
from langgraph.graph import StateGraph, END, START 
from services.batch_questions import gen_questions_for_level_batch

class BatchState(TypedDict):
    # Input data from Send messages
    code: str
    steps_by_level: list[Dict[str, Any]]  # Steps at this cognitive level
    cognitive_level: int
    n_per_level: int
    # Output for reducer
    step_updates: Annotated[list[Dict[str, Any]], add]

async def batch_level_node(state: BatchState) -> Dict[str, Any]:
    """Generate questions for all steps at a specific cognitive level"""
    try:
        print(f"Batch node received state keys: {list(state.keys())}")
        print(f"State contents: {state}")
        
        # Validate required keys
        if "steps_by_level" not in state:
            raise KeyError(f"Missing 'steps_by_level' in state. Available keys: {list(state.keys())}")
        
        steps_by_level = state["steps_by_level"]
        code = state.get("code", "")
        cognitive_level = state.get("cognitive_level", 3)
        n_per_level = state.get("n_per_level", 1)
        
        print(f"Processing {len(steps_by_level)} steps at cognitive level {cognitive_level}")
        
        updated_steps = await gen_questions_for_level_batch(
            steps_by_level=steps_by_level,
            code=code, 
            cognitive_level=cognitive_level,
            n_per_level=n_per_level
        )
        # Return in format expected by build_assets_graph reducer
        return {"step_updates": updated_steps}
        
    except Exception as e:
        print(f"Error in batch_level_node: {e}")
        print(f"State received: {state}")
        raise e

batch_graph = StateGraph(BatchState)
batch_graph.add_node("generate", batch_level_node)
batch_graph.add_edge(START, 'generate')
batch_graph.add_edge("generate", END)
compiled_batch_graph = batch_graph.compile()