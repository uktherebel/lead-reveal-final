from typing import Dict, Any
from services.persistence import save_state
from services.validators import ensure_current_question, validate_answer_shape
from services.eval import is_correct, score_delta
from services.hints import request_dynamic_hint
from services.bandit_lints import LinTS
from services.adapt_context import context_x
from services.adapt_reward import reward
from services.db import get_session
from services.postgres_db import upsert_session, append_answer, save_checkpoint_db 
from core.config import settings
from services.cache import cache_set

def choose_next_question(state: Dict[str, Any]) -> Dict[str, Any]:
    steps = state.get("steps", [])
    i = state.get("current_step", 0)
    if i >= len(steps): return {"completed": True}

    step = steps[i]
    if not state.get("bandit"):
        state["bandit"] = LinTS(n_arms=5, d=6).to_dict()

    bandit = LinTS.from_dict(state["bandit"])
    arm = bandit.choose(context_x(state))   # 0..4
    load = arm + 1

    qs = step.get("questions", [])
    cand = next((q for q in qs if not q.get("answered") and q.get("cognitive_load")==load), None)
    if not cand:
        cand = next((q for q in qs if not q.get("answered")), None)
        if not cand:
            return {"current_step": i+1, "current_question": None}

    cq = {
        "step_number": step["step_number"],
        "question_id": cand.get("id"),
        "question": cand["question"],
        "options": cand.get("options", []),
        "correct_answer": cand.get("correct_answer"),
        "cognitive_load": cand.get("cognitive_load", 1),
        "hint": cand.get("hint"),
    }
    return {"current_question": cq, "next_load_idx": arm, "bandit": bandit.to_dict()}

async def hint_node(state: Dict[str, Any]) -> Dict[str, Any]:
    if not state.get("current_question"):
        return {"messages": [{"type":"hint","content":"No active question."}]}
    return await request_dynamic_hint(state)


async def persist_all(state: Dict[str, Any], record: Dict[str, Any], checkpoint: bool = True):
    # cache (short-term)
    if settings.redis_url:
        await cache_set(state["session_id"], state, url=settings.redis_url)

    # postgres (long-term)
    async for db in get_session():
        await append_answer(db, state["session_id"], record)
        await upsert_session(db, state)
        if checkpoint:
            await save_checkpoint_db(db, state["session_id"], "post_eval", state)
        await db.commit()

async def submit_and_evaluate(state: Dict[str, Any], user_answer, rt_seconds: float, revealed: bool=False) -> Dict[str, Any]:
    ensure_current_question(state)
    cq = state["current_question"]

    ans = validate_answer_shape(cq, user_answer)
    user_val = cq["options"][ans] if isinstance(ans, int) and cq.get("options") else ans

    correct = is_correct(user_val, cq["correct_answer"])
    i = state.get("current_step", 0)
    for q in state["steps"][i]["questions"]:
        if q.get("id") == cq["question_id"]:
            q["answered"] = True
            q["correct"] = correct
            break

    delta = score_delta(correct)
    score = state.get("score", 0) + delta
    total = len(state.get("user_answers", [])) + 1
    corrects = sum(1 for a in state.get("user_answers", []) if a.get("correct")) + (1 if correct else 0)
    acc = corrects / total

    bandit = LinTS.from_dict(state["bandit"])
    r = reward(correct, state.get("hints_used", 0), revealed, float(rt_seconds))
    bandit.update(state["next_load_idx"], context_x(state), r)

    record = {
        "step_number": cq["step_number"],
        "question_id": cq["question_id"],
        "user_answer": user_val,
        "correct": correct,
        "rt": rt_seconds,
        "revealed": revealed,
    }

    out = {
        "score": score,
        "accuracy_rate": acc,
        "user_answers": [record],
        "bandit": bandit.to_dict(),
    }
    out.update(out)
    await persist_all(state, record, checkpoint=True)
    return out
