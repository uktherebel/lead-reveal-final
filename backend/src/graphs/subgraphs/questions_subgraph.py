from typing import TypedDict, Dict, Any
from langgraph.graph import StateGraph, END, START 
from services.questions import gen_all_levels_for_step

class StepState(TypedDict):
    code: str
    step: Dict[str, Any]
    n_per_level: int
    step_updates: list[Dict[str, Any]]  # Add this field

async def per_step_node(state: StepState) -> Dict[str, Any]:
    updated = await gen_all_levels_for_step(
        step=state["step"], code=state["code"], n_per_level=state["n_per_level"]
    )
    # Return in format expected by build_assets_graph reducer
    return {"step_updates": [updated]}

step_graph = StateGraph(StepState)
step_graph.add_node("generate", per_step_node)
step_graph.add_edge(START, 'generate')
step_graph.add_edge("generate", END)
compiled_step_graph = step_graph.compile()
