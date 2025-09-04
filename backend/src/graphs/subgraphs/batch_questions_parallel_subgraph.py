from typing import TypedDict, Dict, Any, List, Annotated
from operator import add
from langgraph.graph import StateGraph, END, START 
from services.batch_questions import gen_questions_for_level_batch

class BatchState(TypedDict):
    code: str
    steps_by_level: List[Dict[str, Any]]
    n_per_level: int
    step_updates: Annotated[List[Dict[str, Any]], add]  # Use Annotated to allow concurrent updates

async def batch_level_1_node(state: BatchState) -> Dict[str, Any]:
    """Generate questions for all steps at cognitive level 1"""
    print("BATCH SUBGRAPH: Starting cognitive level 1")
    updated_steps = await gen_questions_for_level_batch(
        steps_by_level=state["steps_by_level"],
        code=state["code"],
        cognitive_level=1,
        n_per_level=state["n_per_level"]
    )
    print(f"BATCH SUBGRAPH: Cognitive level 1 completed - {len(updated_steps)} steps")
    return {"step_updates": updated_steps}

async def batch_level_2_node(state: BatchState) -> Dict[str, Any]:
    """Generate questions for all steps at cognitive level 2"""
    print("BATCH SUBGRAPH: Starting cognitive level 2")
    updated_steps = await gen_questions_for_level_batch(
        steps_by_level=state["steps_by_level"],
        code=state["code"],
        cognitive_level=2,
        n_per_level=state["n_per_level"]
    )
    print(f"BATCH SUBGRAPH: Cognitive level 2 completed - {len(updated_steps)} steps")
    return {"step_updates": updated_steps}

async def batch_level_3_node(state: BatchState) -> Dict[str, Any]:
    """Generate questions for all steps at cognitive level 3"""
    print("BATCH SUBGRAPH: Starting cognitive level 3")
    updated_steps = await gen_questions_for_level_batch(
        steps_by_level=state["steps_by_level"],
        code=state["code"],
        cognitive_level=3,
        n_per_level=state["n_per_level"]
    )
    print(f"BATCH SUBGRAPH: Cognitive level 3 completed - {len(updated_steps)} steps")
    return {"step_updates": updated_steps}

async def batch_level_4_node(state: BatchState) -> Dict[str, Any]:
    """Generate questions for all steps at cognitive level 4"""
    print("BATCH SUBGRAPH: Starting cognitive level 4")
    updated_steps = await gen_questions_for_level_batch(
        steps_by_level=state["steps_by_level"],
        code=state["code"],
        cognitive_level=4,
        n_per_level=state["n_per_level"]
    )
    print(f"BATCH SUBGRAPH: Cognitive level 4 completed - {len(updated_steps)} steps")
    return {"step_updates": updated_steps}

async def batch_level_5_node(state: BatchState) -> Dict[str, Any]:
    """Generate questions for all steps at cognitive level 5"""
    print("BATCH SUBGRAPH: Starting cognitive level 5")
    updated_steps = await gen_questions_for_level_batch(
        steps_by_level=state["steps_by_level"],
        code=state["code"],
        cognitive_level=5,
        n_per_level=state["n_per_level"]
    )
    print(f"BATCH SUBGRAPH: Cognitive level 5 completed - {len(updated_steps)} steps")
    return {"step_updates": updated_steps}

def merge_batch_results(state: BatchState) -> Dict[str, Any]:
    """Merge all the step updates from the 5 cognitive levels"""
    print("BATCH SUBGRAPH: Merging results from all cognitive levels")
    
    # Get all step updates from the state (automatically accumulated via Annotated[..., add])
    all_step_updates = state.get("step_updates", [])
    
    # Group by step number and merge questions
    by_step_number = {}
    
    for step in all_step_updates:
        step_number = step.get("step_number")
        if step_number not in by_step_number:
            by_step_number[step_number] = {
                **step,
                "questions": []
            }
        
        # Merge questions from this cognitive level
        new_questions = step.get("questions", [])
        by_step_number[step_number]["questions"].extend(new_questions)
    
    # Convert back to list sorted by step number
    merged_steps = [by_step_number[k] for k in sorted(by_step_number.keys())]
    
    total_questions = sum(len(step.get("questions", [])) for step in merged_steps)
    print(f"BATCH SUBGRAPH: Merged {total_questions} total questions across {len(merged_steps)} steps")
    
    return {"step_updates": merged_steps}

# Create the batch subgraph
batch_graph = StateGraph(BatchState)

# Add all 5 cognitive level nodes
batch_graph.add_node("level_1", batch_level_1_node)
batch_graph.add_node("level_2", batch_level_2_node)
batch_graph.add_node("level_3", batch_level_3_node)
batch_graph.add_node("level_4", batch_level_4_node)
batch_graph.add_node("level_5", batch_level_5_node)
batch_graph.add_node("merge", merge_batch_results)

# All 5 levels start from START (run in parallel)
batch_graph.add_edge(START, "level_1")
batch_graph.add_edge(START, "level_2")
batch_graph.add_edge(START, "level_3")
batch_graph.add_edge(START, "level_4")
batch_graph.add_edge(START, "level_5")

# All levels feed into the merge node
batch_graph.add_edge("level_1", "merge")
batch_graph.add_edge("level_2", "merge")
batch_graph.add_edge("level_3", "merge")
batch_graph.add_edge("level_4", "merge")
batch_graph.add_edge("level_5", "merge")

# Merge leads to END
batch_graph.add_edge("merge", END)

# Compile the subgraph
compiled_batch_graph = batch_graph.compile()