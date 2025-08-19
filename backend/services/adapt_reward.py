def reward(correct: bool, hints_used: int, revealed: bool, rt: float, target_rt=30.0) -> float:
    base = 1.0 if correct else 0.0
    hint_pen = 0.25 * min(2, int(hints_used))
    rev_pen  = 0.5 if revealed else 0.0
    time_pen = max(0.0, min(1.0, (rt - target_rt)/target_rt)) * 0.3
    return max(0.0, min(1.0, base - hint_pen - rev_pen - time_pen))
