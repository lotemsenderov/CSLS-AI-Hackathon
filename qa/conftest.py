import sys
from pathlib import Path

# Only backend/ goes on sys.path: backend/app.py and frontend/app.py share a
# module name, and frontend/app.py imports gradio (not always installed) at
# module scope. Tests that need frontend logic load it directly by file path
# instead — see qa/unit/test_frontend_logic.py.
ROOT = Path(__file__).parent.parent
p = str(ROOT / "backend")
if p not in sys.path:
    sys.path.insert(0, p)