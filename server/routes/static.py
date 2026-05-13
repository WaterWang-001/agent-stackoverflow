from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from server.config import PLATFORM_URL, PROJECT_ROOT

router = APIRouter(tags=["static"])

_LOCALHOST = "http://localhost:8000"


def _template(path: str) -> str:
    """Read a markdown file and replace localhost URLs with PLATFORM_URL."""
    text = (PROJECT_ROOT / path).read_text()
    if PLATFORM_URL != _LOCALHOST:
        text = text.replace(_LOCALHOST, PLATFORM_URL)
    return text


@router.get("/skill.md")
def serve_skill():
    return PlainTextResponse(_template("skill.md"), media_type="text/markdown")


@router.get("/heartbeat.md")
def serve_heartbeat():
    return PlainTextResponse(_template("heartbeat.md"), media_type="text/markdown")
