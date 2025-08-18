import asyncio, uuid
from typing import Dict, Any, List
from workers.question_workers_registry import WORKERS
# A semaphore is a concurrency primitive that allows a limit on the number of threads that can acquire a lock protecting a critical section.
SEM = asyncio.Semaphore(6)

async def gen_all_levels_for_step(step: Dict[str, Any], code: str,
                                  n_per_level=1, levels=(1,2,3,4,5)) -> Dict[str, Any]:
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
        if not res.get("success"): 
            return []
        qs = res["questions"]
        for item in qs:
            item["cognitive_load"] = L
            item.setdefault("id", str(uuid.uuid4()))
        return qs

    # this is telling python to run all coroutines at concurrently 
    packs = await asyncio.gather(*[run(L) for L in levels], return_exceptions=True)
    merged: List[Dict[str, Any]] = []
    for p in packs:
        if isinstance(p, list): 
            merged.extend(p)
    step = {**step, "questions": step.get("questions", []) + merged}
    return step
