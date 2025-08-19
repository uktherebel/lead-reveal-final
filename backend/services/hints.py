from typing import Dict, Any, Optional
from src.workers.hint_worker import HintWorker


def _decide_tier(hints_used: int, last_correct: Optional[bool], rt_z: float) -> int:
    tier = 1 if hints_used == 0 else (2 if hints_used == 1 else 3)
    if last_correct is False and hints_used > 0: tier = max(tier, 2)
    if rt_z > 0.8: tier = max(tier, 2)
    return min(tier, 3)

async def request_dynamic_hint(state: Dict[str, Any]) -> Dict[str, Any]:
    cq = state.get("current_question") or {}
    if not cq: return {"messages": [{"type":"hint","content":"No active question."}]}

    # last user answer (if any) for this question
    last = None
    for a in reversed(state.get("user_answers", [])):
        if a.get("question_id") == cq.get("question_id"):
            last = a
            break
    last_answer = (last or {}).get("user_answer")
    last_correct = (last or {}).get("correct")

    rs = state.get("rolling_stats", {}) or {}
    rt_z = float((rs.get("median_rt", 30.0) - 30.0) / 10.0)

    tier = _decide_tier(state.get("hints_used", 0), last_correct, rt_z)

    # build context for LLM
    ctx = {
        "code_snippet": _safe(state, "steps", state.get("current_step", 0), "code_snippet"),
        "concept": _safe(state, "steps", state.get("current_step", 0), "concept"),
        "explanation": _safe(state, "steps", state.get("current_step", 0), "explanation"),
        "question": cq.get("question",""),
        "options": cq.get("options", []),
        "last_answer": last_answer,
        "hints_used": state.get("hints_used", 0),
        "rt_z": rt_z,
        "tier": tier,
    }

    # generate (on-demand)
    worker = HintWorker()
    res = await worker.process(ctx)
    if not res.get("success"):
        # fallback: template
        fallback = "Check the variable names and the control flow around the focus of this step."
        hint = fallback
    else:
        hint = res["hint"]

    used = state.get("hints_used", 0) + 1
    return {
        "hints_used": used,
        "messages": [{"type": "hint", "tier": tier, "content": hint}],
    }

def _safe(state: Dict[str, Any], key: str, idx: int, sub: str) -> str:
    try:
        return str(((state.get(key) or [])[idx] or {}).get(sub) or "")
    except Exception:
        return ""
