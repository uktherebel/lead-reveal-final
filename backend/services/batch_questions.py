import asyncio
from typing import Dict, Any, List
from src.workers.batch_question_worker import BatchQuestionWorker


async def gen_questions_for_level_batch(
    steps_by_level: List[Dict[str, Any]], 
    code: str, 
    cognitive_level: int,
    n_per_level: int = 1
) -> List[Dict[str, Any]]:
    """
    Generate questions for all steps at a specific cognitive level in batch.
    This is the TRUE batch mode - ONE LLM call generates questions for ALL steps at the specified level.
    
    Args:
        steps_by_level: List of steps that have this cognitive level
        code: The complete code solution
        cognitive_level: The cognitive load level (1-5)
        n_per_level: Number of questions per level per step
    
    Returns:
        List of updated steps with questions populated
    """
    print(f"TRUE BATCH processing cognitive level {cognitive_level} with {len(steps_by_level)} steps")
    
    if not steps_by_level:
        print("No steps provided for batch processing")
        return []
    
    # Initialize the batch worker
    batch_worker = BatchQuestionWorker()
    
    try:
        # Single LLM call to generate questions for ALL steps at this cognitive level
        result = await batch_worker.process_batch_level(
            steps=steps_by_level,
            code=code,
            cognitive_level=cognitive_level,
            n_per_level=n_per_level
        )
        
        if not result.get("success"):
            print(f"Batch generation failed: {result.get('error', 'Unknown error')}")
            return []
        
        questions_by_step = result.get("questions_by_step", {})
        print(f"Batch generated {result.get('total_questions', 0)} questions across {len(questions_by_step)} steps")
        
        # Update each step with its generated questions
        updated_steps = []
        for step in steps_by_level:
            step_number = step.get("step_number")
            step_questions = questions_by_step.get(step_number, [])
            
            # Add the new questions to existing ones
            existing_questions = step.get("questions", [])
            updated_step = {
                **step,
                "questions": existing_questions + step_questions
            }
            updated_steps.append(updated_step)
            print(f"  Step {step_number}: added {len(step_questions)} questions at level {cognitive_level}")
        
        print(f"TRUE BATCH level {cognitive_level} completed: {len(updated_steps)} steps updated")
        return updated_steps
        
    except Exception as e:
        print(f"Batch processing failed for level {cognitive_level}: {e}")
        # Fallback: return steps unchanged rather than failing completely
        return steps_by_level


async def gen_questions_super_batch(
    steps: List[Dict[str, Any]], 
    code: str,
    n_per_level: int = 1,
    levels: List[int] = [1, 2, 3, 4, 5]
) -> List[Dict[str, Any]]:
    """
    Generate questions for all steps across all cognitive levels in true batch mode.
    This uses 5 LLM calls (one per cognitive level) instead of N*5 calls (per step per level).
    
    Args:
        steps: List of all steps
        code: The complete code solution
        n_per_level: Number of questions per level per step
        levels: List of cognitive levels to generate questions for
    
    Returns:
        List of updated steps with all questions populated
    """
    print(f"SUPER BATCH processing {len(steps)} steps across {len(levels)} cognitive levels")
    
    if not steps:
        print("No steps provided for super batch processing")
        return []
    
    # Start with a copy of the original steps
    updated_steps = [dict(step) for step in steps]
    
    # Ensure all steps have questions list initialized
    for step in updated_steps:
        if "questions" not in step:
            step["questions"] = []
    
    # Process all cognitive levels in parallel for maximum efficiency
    print(f"Processing {len(levels)} cognitive levels in parallel for all {len(updated_steps)} steps")
    
    async def process_level(level: int):
        print(f"  Starting cognitive level {level} batch processing")
        return await gen_questions_for_level_batch(
            steps_by_level=updated_steps,
            code=code,
            cognitive_level=level,
            n_per_level=n_per_level
        )
    
    # Run all cognitive levels concurrently
    level_results = await asyncio.gather(*[process_level(level) for level in levels], return_exceptions=True)
    
    # Merge results from all levels
    for level_idx, level_result in enumerate(level_results):
        level = levels[level_idx]
        if isinstance(level_result, Exception):
            print(f"  Cognitive level {level} failed: {level_result}")
            continue
        
        if level_result:
            print(f"  Cognitive level {level} completed with {len(level_result)} steps")
            # Merge questions from this level into existing steps
            step_map = {step.get("step_number"): step for step in level_result}
            
            for i, step in enumerate(updated_steps):
                step_number = step.get("step_number")
                if step_number in step_map:
                    # Merge questions instead of overwriting the entire step
                    new_questions = step_map[step_number].get("questions", [])
                    existing_questions = step.get("questions", [])
                    updated_steps[i] = {
                        **step,  # Keep all existing step data
                        "questions": existing_questions + new_questions  # Merge questions
                    }
                    print(f"    Step {step_number}: merged {len(new_questions)} questions from level {level}")
    
    total_questions = sum(len(step.get("questions", [])) for step in updated_steps)
    print(f"SUPER BATCH completed: {total_questions} total questions across {len(updated_steps)} steps")
    
    return updated_steps