from typing import Any

def _norm(x: Any) -> str:
    s = str(x).strip().lower()
    return s.replace("’","'").replace("“",'"').replace("”",'"')

def is_correct(user, correct) -> bool:
    return _norm(user) == _norm(correct)

def score_delta(correct: bool) -> int:
    return 10 if correct else 0
