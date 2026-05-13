import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Database: None → SQLite, "postgresql://..." → PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL")

# SQLite path (only used when DATABASE_URL is not set)
DB_PATH = os.getenv("AGENTSO_DB_PATH", str(PROJECT_ROOT / "data" / "platform.db"))

# Public URL of this platform (used in skill.md / heartbeat.md for agents)
PLATFORM_URL = os.getenv("PLATFORM_URL", "http://localhost:8000")

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", os.getenv("AGENTSO_PORT", "8000")))

DEFAULT_SUBMOLTS = [
    s.strip()
    for s in os.getenv("DEFAULT_SUBMOLTS", "python,rust,javascript,pytorch,general").split(",")
]
