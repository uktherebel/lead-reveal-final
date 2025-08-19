from typing import Dict, Any, Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

async def upsert_session(db: AsyncSession, state: Dict[str, Any]) -> None:
    q = text("""
        INSERT INTO sessions (session_id, user_id, technique, difficulty, current_step, phase,
                              score, accuracy_rate, hints_used, bandit, rolling_stats, state)
        VALUES (:sid, :uid, :technique, :difficulty, :current_step, :phase,
                :score, :accuracy_rate, :hints_used, CAST(:bandit AS JSONB),
                CAST(:rolling_stats AS JSONB), CAST(:state AS JSONB))
        ON CONFLICT (session_id) DO UPDATE SET
            updated_at = NOW(),
            technique = EXCLUDED.technique,
            difficulty = EXCLUDED.difficulty,
            current_step = EXCLUDED.current_step,
            phase = EXCLUDED.phase,
            score = EXCLUDED.score,
            accuracy_rate = EXCLUDED.accuracy_rate,
            hints_used = EXCLUDED.hints_used,
            bandit = EXCLUDED.bandit,
            rolling_stats = EXCLUDED.rolling_stats,
            state = EXCLUDED.state;
    """)
    await db.execute(q, {
        "sid": state["session_id"],
        "uid": state.get("user_id"),
        "technique": state.get("technique"),
        "difficulty": state.get("difficulty_level"),
        "current_step": state.get("current_step"),
        "phase": str(state.get("current_phase")),
        "score": state.get("score"),
        "accuracy_rate": state.get("accuracy_rate"),
        "hints_used": state.get("hints_used"),
        "bandit": state.get("bandit"),
        "rolling_stats": state.get("rolling_stats"),
        "state": state,
    })

async def load_session(db: AsyncSession, session_id: str) -> Optional[Dict[str, Any]]:
    q = text("SELECT state FROM sessions WHERE session_id=:sid")
    res = await db.execute(q, {"sid": session_id})
    row = res.first()
    return row[0] if row else None

async def append_answer(db: AsyncSession, session_id: str, record: Dict[str, Any]) -> None:
    q = text("""
        INSERT INTO answers (session_id, question_id, step_number, user_answer,
                             correct, rt_seconds, revealed)
        VALUES (:sid, :qid, :step, CAST(:ans AS JSONB), :correct, :rt, :rev)
    """)
    await db.execute(q, {
        "sid": session_id,
        "qid": record.get("question_id"),
        "step": record.get("step_number"),
        "ans": record.get("user_answer"),
        "correct": record.get("correct"),
        "rt": record.get("rt"),
        "rev": record.get("revealed", False),
    })

async def save_checkpoint_db(db: AsyncSession, session_id: str, tag: str, snapshot: Dict[str, Any]) -> None:
    q = text("""
        INSERT INTO checkpoints (session_id, tag, snapshot)
        VALUES (:sid, :tag, CAST(:snap AS JSONB))
    """)
    await db.execute(q, {"sid": session_id, "tag": tag, "snap": snapshot})
