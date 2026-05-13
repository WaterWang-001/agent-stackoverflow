from fastapi import APIRouter
from fastapi.responses import FileResponse

from server.config import PROJECT_ROOT

router = APIRouter(tags=["static"])


@router.get("/skill.md")
def serve_skill():
    return FileResponse(PROJECT_ROOT / "skill.md", media_type="text/markdown")


@router.get("/heartbeat.md")
def serve_heartbeat():
    return FileResponse(PROJECT_ROOT / "heartbeat.md", media_type="text/markdown")
