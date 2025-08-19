from typing import Any, Dict

def ensure_current_question(state: Dict[str, Any]) -> None:
    if not state.get("current_question"):
        raise ValueError("No current question selected.")

def validate_answer_shape(q: Dict[str, Any], ans: Any) -> Any:
    opts = q.get("options", [])
    if not opts:
        return str(ans).strip()
    if isinstance(ans, str) and len(ans.strip()) == 1 and ans.strip().isalpha():
        idx = ord(ans.strip().upper()) - ord("A")
    elif isinstance(ans, int):
        idx = ans
    else:
        try:
            idx = next(i for i,o in enumerate(opts)
                       if str(o).strip().lower() == str(ans).strip().lower())
        except StopIteration:
            raise ValueError("Answer not in options.")
    if idx < 0 or idx >= len(opts):
        raise ValueError("Answer index out of range.")
    return idx
