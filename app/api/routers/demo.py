from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["demo"])

_demo_path = Path(__file__).resolve().parents[2] / "frontend" / "index.html"


@router.get("/demo", response_class=HTMLResponse)
def demo_page() -> str:
    return _demo_path.read_text(encoding="utf-8")
