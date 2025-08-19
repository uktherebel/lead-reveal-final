# scripts/smoke_graph.py
import asyncio
import os
os.environ.setdefault("LANGCHAIN_DEBUG", "false")

from src.graphs.subgraphs.questions_subgraph import compiled_step_graph  # sanity import
from src.graphs.subgraphs.build_assets_graph import build_assets_app     # adjust path/name if needed

STATE = {
    "task_description": "Write a BFS over adjacency list, return levels from a source node.",
    "difficulty_level": "intermediate",
    "code_solution": "",
    "validated_code": "",
    "steps": [],
    "step_updates": [],
}

async def main():
    # Test with shorter timeout and more specific task
    import asyncio
    try:
        # Set a shorter timeout
        out = await asyncio.wait_for(
            build_assets_app.ainvoke(STATE), 
            timeout=180.0  # 3 minute timeout
        )
        code = out.get("validated_code") or out.get("code_solution") or ""
        steps = out.get("steps", [])
        assert code, "no code"
        assert steps, "no steps"
        
        # Debug: show which steps have questions and sample questions
        for i, s in enumerate(steps):
            q_count = len(s.get("questions", []))
            print(f"Step {i+1}: {q_count} questions")
            if q_count > 0:
                for q in s["questions"][:2]:  # Show first 2 questions
                    print(f"  L{q.get('cognitive_load', '?')} - {q.get('question', 'No question text')[:80]}...")
        
        steps_with_questions = [s for s in steps if "questions" in s and s["questions"]]
        print(f"✓ graph produced code: {len(code)} chars")
        print(f"✓ steps: {len(steps)} total, {len(steps_with_questions)} with questions")
        
        if steps_with_questions:
            print("✓ questions per step:", [len(s["questions"]) for s in steps_with_questions])
            total_questions = sum(len(s["questions"]) for s in steps_with_questions)
            print(f"✓ total questions generated: {total_questions}")
        else:
            print("⚠️ No steps have questions generated")
            
    except asyncio.TimeoutError:
        print("⚠️ Graph execution timed out after 60 seconds")
        print("This suggests the questions generation is taking too long")
    except Exception as e:
        print(f"⚠️ Graph execution failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
