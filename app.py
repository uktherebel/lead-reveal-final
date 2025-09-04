import runpy
import sys
from pathlib import Path

if __name__ == "__main__":
    # Add backend directory to Python path so imports work correctly
    backend_path = str(Path(__file__).parent / "backend")
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)
    
    target = Path(__file__).parent / "frontend" / "ui_app.py"
    runpy.run_path(str(target), run_name="__main__")
