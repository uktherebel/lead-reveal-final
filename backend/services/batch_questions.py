import asyncio
from typing import Dict, Any, List
from services.questions import gen_all_levels_for_step


async def gen_questions_for_level_batch(
    steps_by_level: List[Dict[str, Any]], 
    code: str, 
    cognitive_level: int,
    n_per_level: int = 1
) -> List[Dict[str, Any]]:
    """
    Generate questions for all steps at a specific cognitive level in batch.
    
    Args:
        steps_by_level: List of steps that have this cognitive level
        code: The complete code solution
        cognitive_level: The cognitive load level (1-5)
        n_per_level: Number of questions per level per step
    
    Returns:
        List of updated steps with questions populated
    """
    print(f"Batch processing cognitive level {cognitive_level} with {len(steps_by_level)} steps")
    
    # For now, we'll still generate per step but concurrently for this level
    # This reduces the number of sequential calls
    
    tasks = []
    for step in steps_by_level:
        print(f"  Adding step {step.get('step_number')} to batch")
        # Generate questions for all levels for each step
        # The batching is by grouping steps that have the same intrinsic_load together
        task = gen_all_levels_for_step(
            step=step, 
            code=code, 
            n_per_level=n_per_level
            # Don't use target_level - generate for all levels per step
        )
        tasks.append(task)
    
    # Run all steps for this level concurrently
    try:
        updated_steps = await asyncio.gather(*tasks, return_exceptions=True)
        successful_steps = []
        for i, result in enumerate(updated_steps):
            if isinstance(result, Exception):
                print(f"  Step {steps_by_level[i].get('step_number')} failed: {result}")
            else:
                successful_steps.append(result)
        print(f"Batch level {cognitive_level} completed: {len(successful_steps)}/{len(steps_by_level)} steps successful")
        return successful_steps
    except Exception as e:
        print(f"Batch processing failed for level {cognitive_level}: {e}")
        return []


def group_steps_by_cognitive_level(steps: List[Dict[str, Any]]) -> Dict[int, List[Dict[str, Any]]]:
    """
    Group steps by their intrinsic_load (cognitive level).
    
    Args:
        steps: List of decomposed steps
    
    Returns:
        Dictionary mapping cognitive level -> list of steps at that level
    """
    grouped = {}
    for step in steps:
        level = step.get("intrinsic_load", 3)  # Default to level 3
        if level not in grouped:
            grouped[level] = []
        grouped[level].append(step)
    
    return grouped