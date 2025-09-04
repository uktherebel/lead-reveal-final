import sys
import os

# Add backend to path when running as script
if __name__ == "__main__":
    backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)

from typing import TypedDict, Dict, Any, List, Annotated, Literal
from operator import add
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from src.workers.coder import CodeWorker
from src.workers.decomposer import Decompose
from src.workers.language_detector import LanguageDetectionWorker

try:
    from .questions_subgraph import compiled_step_graph as compiled_qgen
except ImportError:
    # When running as script, use absolute import
    from questions_subgraph import compiled_step_graph as compiled_qgen

# Import batch processing function directly
from services.batch_questions import gen_questions_for_level_batch

# ---- App state for building assets
class AppState(TypedDict):
    # input
    task_description: str
    difficulty_level: Literal['beginner', 'intermediate', 'advanced']
    quick_mode: bool
    programming_language: str  # Detected programming language

    # generated assets
    code_solution: str
    validated_code: str
    steps: List[Dict[str, Any]]

    # reducer bucket
    step_updates: Annotated[List[Dict[str, Any]], add]

# ---- Nodes
def detect_language(state: AppState) -> Dict[str, Any]:
    """Detect programming language from task description"""
    if state.get("programming_language"):
        return {}  # Language already detected
    
    worker = LanguageDetectionWorker()
    result = worker.process_sync({
        "task_description": state["task_description"]
    })
    
    detected_language = result.get("programming_language", "python")
    print(f"Language detected: {detected_language}")
    
    return {"programming_language": detected_language}

def codegen(state: AppState) -> Dict[str, Any]:
    if state.get("validated_code"):
        return {}
    worker = CodeWorker()
    out = worker.process_sync({
        "task_description": state["task_description"],
        "difficulty_level": state.get("difficulty_level", "intermediate"),
        "programming_language": state.get("programming_language", "python"),
    })
    if not out or not out.get("success", True):
        # Log the error but try to continue with whatever code was generated
        error_msg = out.get("error", "Code generation failed")
        print(f"Warning: {error_msg}")
        # If there's any code at all, use it
        code = out.get("code") or out.get("validated_code") or out.get("code_solution") or ""
        if not code:
            # Last resort - generate a simple placeholder
            code = f"""# Generated solution for: {state["task_description"]}
# Note: This is a placeholder due to generation issues

def solution():
    '''
    Task: {state["task_description"]}
    
    This is a placeholder function that needs to be implemented.
    The actual implementation depends on the specific requirements.
    '''
    pass
    
# TODO: Implement the actual solution
"""
        return {"code_solution": code, "validated_code": code}
    code = out.get("code") or out.get("validated_code") or out.get("code_solution") or ""
    return {"code_solution": code, "validated_code": code}

def decompose(state: AppState) -> Dict[str, Any]:
    code = state.get("validated_code") or state.get("code_solution") or ""
    if not code:
        raise RuntimeError("No code available to decompose")
    d = Decompose()
    out = d.process_sync(code)
    steps = out.get("steps", [])
    # ensure required fields exist for questions subgraph
    for i, s in enumerate(steps, start=1):
        s.setdefault("step_number", i)
        s.setdefault("questions", [])  # Questions will be populated by the questions subgraph
    return {"steps": steps}

def map_steps(state: AppState):
    """Map steps for question generation - normal mode (per step)"""
    code = state.get("validated_code") or state.get("code_solution") or ""
    return [Send("qgen", {"step": s, "code": code, "n_per_level": 1}) for s in state.get("steps", [])]

def map_levels(state: AppState):
    """Map steps for question generation - quick mode (per cognitive level)"""
    from services.batch_questions import group_steps_by_cognitive_level
    
    code = state.get("validated_code") or state.get("code_solution") or ""
    steps = state.get("steps", [])
    
    print(f"Mapping {len(steps)} steps for batch question generation")
    
    # Group steps by cognitive level
    grouped = group_steps_by_cognitive_level(steps)
    
    print(f"Grouped steps by intrinsic_load: {[(level, len(level_steps)) for level, level_steps in grouped.items()]}")
    
    # Create Send messages for each cognitive level
    sends = []
    for level, level_steps in grouped.items():
        print(f"Creating batch for level {level} with {len(level_steps)} steps: {[s.get('step_number') for s in level_steps]}")
        sends.append(Send("batch_qgen", {
            "code": code,
            "steps_by_level": level_steps,
            "cognitive_level": level,
            "n_per_level": 1
        }))
    
    print(f"Created {len(sends)} batch sends")
    return sends

def conditional_map(state: AppState):
    """Choose mapping strategy based on quick_mode flag"""
    if state.get("quick_mode", False):
        return map_levels(state)
    else:
        return map_steps(state)

async def batch_qgen_node(state: AppState) -> Dict[str, Any]:
    """Direct batch question generation node"""
    print(f"Batch node received state with keys: {list(state.keys())}")
    
    # Extract data from the Send message
    code = state.get("code", "")
    steps_by_level = state.get("steps_by_level", [])
    cognitive_level = state.get("cognitive_level", 3)
    n_per_level = state.get("n_per_level", 1)
    
    print(f"Processing {len(steps_by_level)} steps at cognitive level {cognitive_level}")
    
    # Generate questions for this batch
    updated_steps = await gen_questions_for_level_batch(
        steps_by_level=steps_by_level,
        code=code, 
        cognitive_level=cognitive_level,
        n_per_level=n_per_level
    )
    
    # Return in format expected by reducer
    return {"step_updates": updated_steps}

def reduce_updates(state: AppState) -> Dict[str, Any]:
    by_num = {s["step_number"]: s for s in state.get("steps", [])}
    for upd in state.get("step_updates", []):
        by_num[upd["step_number"]] = upd
    merged = [by_num[k] for k in sorted(by_num.keys())]
    return {"steps": merged}

g = StateGraph(AppState)
g.add_node("detect_language", detect_language)  # Language detection first
g.add_node("codegen", codegen)
g.add_node("decompose", decompose)
g.add_node("qgen", compiled_qgen)  # Normal mode: per-step generation
g.add_node("batch_qgen", batch_qgen_node)  # Quick mode: per-level batch generation
g.add_node("reduce", reduce_updates)

g.add_edge(START, "detect_language")  # Start with language detection
g.add_edge("detect_language", "codegen")
g.add_edge("codegen", "decompose")
g.add_conditional_edges("decompose", conditional_map)  # Choose based on quick_mode
g.add_edge("qgen", "reduce")  # Both question generators feed into reducer
g.add_edge("batch_qgen", "reduce")
g.add_edge("reduce", END)

build_assets_app = g.compile()

if __name__ == "__main__": 
    task = """ 
32. Longest Valid Parentheses
Hard
Topics
premium lock icon
Companies
Given a string containing just the characters '(' and ')', return the length of the longest valid (well-formed) parentheses substring.

 

Example 1:

Input: s = "(()"
Output: 2
Explanation: The longest valid parentheses substring is "()".
Example 2:

Input: s = ")()())"
Output: 4
Explanation: The longest valid parentheses substring is "()()".
Example 3:

Input: s = ""
Output: 0
 

Constraints:

0 <= s.length <= 3 * 104
s[i] is '(', or ')'.
"""
    import asyncio
    response = asyncio.run(build_assets_app.ainvoke({
        'task_description': task
    }))