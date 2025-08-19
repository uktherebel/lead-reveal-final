import numpy as np
from typing import Dict, Any

def context_x(state: Dict[str, Any]) -> np.ndarray:
    r = state.get("rolling_stats", {})
    acc = float(r.get("acc", 0.5))
    rt  = float(r.get("median_rt", 30.0))
    hint_rate   = float(r.get("hint_rate", 0.2))
    reveal_rate = float(r.get("reveal_rate", 0.0))
    step_norm   = float(r.get("step_norm", 0.5))
    rt_z = (rt - 30.0) / 10.0
    return np.array([1.0, acc, rt_z, hint_rate, reveal_rate, step_norm], dtype=float)
