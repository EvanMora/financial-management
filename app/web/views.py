"""Rutas que devuelven HTML renderizado con Jinja2."""
from datetime import date
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.web.preview import build_preview

APP_DIR = Path(__file__).resolve().parent.parent

templates = Jinja2Templates(directory=APP_DIR / "templates")
# Nombre provisional: el equipo aún no lo define (ver docs/alcance.md, decisiones pendientes).
templates.env.globals["app_name"] = "Mis Finanzas"

router = APIRouter(include_in_schema=False)


@router.get("/login", response_class=HTMLResponse)
def login(request: Request):
    context = {"year": date.today().year, "preview": build_preview()}
    return templates.TemplateResponse(request, "login.html", context)
