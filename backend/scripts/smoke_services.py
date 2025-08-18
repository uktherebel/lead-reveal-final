import asyncio
import os
import sys

# Add backend to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("LANGCHAIN_DEBUG", "false")

from src.workers.coder import CodeWorker
from src.workers.decomposer import Decompose
from services.questions import gen_all_levels_for_step

TASK = "Write a BFS over adjacency list, return distance (levels) from a source node."

async def main():
    # 1) Code
    code_out = await CodeWorker().process({
        "task_description": TASK, "difficulty_level": "intermediate"
    })
    assert code_out.get("success", True), code_out
    code = code_out.get("validated_code") or code_out.get("code") or ""
    print("✓ code generated:", len(code), "chars")

    # 2) Decompose
    steps_out = await Decompose().process(code)
    steps = steps_out.get("steps", [])
    assert steps, "no steps"
    print("✓ steps:", len(steps))

    # 3) Questions for step 1
    step0 = steps[0]
    step0.setdefault("step_number", 1)
    step0.setdefault("questions", [])
    updated = await gen_all_levels_for_step(step0, code, n_per_level=1)
    print("✓ questions in step 1:", len(updated.get("questions", [])))
    for q in updated.get("questions", []):
        print(f"  L{q.get('cognitive_load')} - {q['question'][:80]}")

if __name__ == "__main__":
    asyncio.run(main())
