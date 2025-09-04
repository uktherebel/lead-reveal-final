from typing import Dict, Any, List
from src.workers.mega_batch_worker import MegaBatchQuestionWorker


async def gen_all_questions_mega_batch(
    steps: List[Dict[str, Any]], 
    code: str,
    n_per_level: int = 1
) -> List[Dict[str, Any]]:
    """
    Generate ALL questions for ALL steps at ALL cognitive levels in ONE single LLM call.
    This is the ultimate batch mode - 1 LLM call generates everything.
    
    Args:
        steps: List of all steps
        code: The complete code solution
        n_per_level: Number of questions per cognitive level per step
    
    Returns:
        List of steps with all questions populated
    """
    print(f"MEGA BATCH: Processing {len(steps)} steps across ALL 5 cognitive levels in ONE call")
    
    if not steps:
        print("No steps provided for mega batch processing")
        return []
    
    # Initialize the mega batch worker
    mega_worker = MegaBatchQuestionWorker()
    
    try:
        # Single mega LLM call to generate ALL questions for ALL steps at ALL cognitive levels
        result = await mega_worker.process_mega_batch(
            steps=steps,
            code=code,
            n_per_level=n_per_level
        )
        
        if not result.get("success"):
            print(f"Mega batch generation failed: {result.get('error', 'Unknown error')}")
            return []
        
        final_steps = result.get("steps", [])
        total_questions = result.get("total_questions", 0)
        
        print(f"MEGA BATCH completed: {total_questions} total questions across {len(final_steps)} steps in ONE call")
        return final_steps
        
    except Exception as e:
        print(f"Mega batch processing failed: {e}")
        # Fallback: return steps unchanged rather than failing completely
        return steps