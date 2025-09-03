import asyncio, uuid
from typing import Dict, Any, List
from src.workers.question_workers_registry import WORKERS
# A semaphore is a concurrency primitive that allows a limit on the number of threads that can acquire a lock protecting a critical section.
SEM = asyncio.Semaphore(20)  # Serial processing to avoid any rate limits

def diagnosis(steps: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Fast diagnostics for question data.

    - Ensures each question has an `id` and `cognitive_load` (1-5).
    - Returns a compact summary to help debug navigation issues.
    Mutates input only to fill missing fields (single pass, O(n)).
    """
    steps = steps or []
    total_q = 0
    unanswered = 0
    missing_ids = 0
    missing_loads = 0
    per_load: Dict[int, int] = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

    for step in steps:
        qs = step.get("questions", [])
        total_q += len(qs)
        default_level = step.get("intrinsic_load")
        if not isinstance(default_level, int) or not (1 <= default_level <= 5):
            default_level = 1

        for q in qs:
            if not q.get("id"):
                q["id"] = str(uuid.uuid4())
                missing_ids += 1
            lvl = q.get("cognitive_load")
            if not isinstance(lvl, int) or not (1 <= lvl <= 5):
                lvl = default_level
                q["cognitive_load"] = lvl
                missing_loads += 1
            per_load[lvl] = per_load.get(lvl, 0) + 1
            if not q.get("answered"):
                unanswered += 1

    return {
        "steps": len(steps),
        "questions": total_q,
        "unanswered": unanswered,
        "missing_ids_fixed": missing_ids,
        "missing_loads_fixed": missing_loads,
        "per_load": per_load,
    }
async def gen_all_levels_for_step(step: Dict[str, Any], code: str,
                                  n_per_level=1, levels=(1,2,3,4,5), target_level=None) -> Dict[str, Any]:
    """
      Params: 
        - step: Takes in a single step 
        - code: Takes in the whole code generated for context 
        - n_per_level: Number of questions to generate per level 
        - levels: The cognitive levels at which to generate questions
    """
    async def run(L: int):
        worker = WORKERS[L]
        async with SEM:
            res = await worker.process(
                code=code, step_number=step["step_number"],
                code_snippet=step["code_snippet"], concept=step["concept"],
                explanation=step["explanation"], n=n_per_level, level=L
            )
            # Adding delay to avoid rate limiting
            await asyncio.sleep(0.5)
        if not res.get("success"): 
            print(f"Question generation failed for step {step['step_number']} level {L}: {res.get('error', 'Unknown error')}")
            return []
        print(f"Question generation succeeded for step {step['step_number']} level {L}: {len(res.get('questions', []))} questions")
        qs = res["questions"]
        for item in qs:
            item["cognitive_load"] = L
            item.setdefault("id", str(uuid.uuid4()))
        return qs

    # Use target_level if provided, otherwise use all levels
    target_levels = [target_level] if target_level else levels
    
    # this is telling python to run all coroutines at concurrently 
    packs = await asyncio.gather(*[run(L) for L in target_levels], return_exceptions=True)
    merged: List[Dict[str, Any]] = []
    for p in packs:
        if isinstance(p, list): 
            merged.extend(p)
    step = {**step, "questions": step.get("questions", []) + merged}
    return step
