import json, os, tempfile
from typing import Dict, Any

def _path(session_id: str) -> str:
    os.makedirs("data", exist_ok=True)
    return os.path.join("data", f"{session_id}.json")

def save_state(state: Dict[str, Any]) -> Dict[str, Any]:
    path = _path(state["session_id"])
    tmp = tempfile.NamedTemporaryFile(delete=False, dir=os.path.dirname(path))
    with open(tmp.name, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2, default=str)
    os.replace(tmp.name, path)
    return {"_persisted_path": path}

def load_state(session_id: str) -> Dict[str, Any]:
    path = _path(session_id)
    if not os.path.exists(path): return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
