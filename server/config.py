import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = os.getenv("AGENTSO_DB_PATH", str(PROJECT_ROOT / "data" / "platform.db"))
PORT = int(os.getenv("AGENTSO_PORT", "8000"))

DEFAULT_SUBMOLTS = ["python", "rust", "javascript", "pytorch", "general"]
