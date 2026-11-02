"""Rutas que devuelven HTML renderizado con Jinja2."""
from datetime import date
from pathlib import Path

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.services.dashboard import obtener_resumen
from app.web import formato
from app.web.presentacion import vista_resumen
from app.web.preview import build_preview

APP_DIR = Path(__file__).resolve().parent.parent

templates = Jinja2Templates(directory=APP_DIR / "templates")
# Nombre provisional: el equipo aún no lo define (ver docs/alcance.md, decisiones pendientes).
templates.env.globals["app_name"] = "Mis Finanzas"
formato.registrar(templates.env)

router = APIRouter(include_in_schema=False)

# Cookie que recuerda la barra lateral contraída; la escribe static/js/app-shell.js.
COOKIE_BARRA = "barra_contraida"

# Secciones de la barra lateral: (ruta, nombre, ícono). El orden es el de la barra.
SECCIONES = [
    ("resumen", "Resumen", "resumen"),
    ("movimientos", "Movimientos", "movimientos"),
    ("cuentas", "Cuentas", "cuentas"),
    ("categorias", "Categorías", "categorias"),
]
PROXIMAMENTE = [("Presupuestos", "presupuestos"), ("Metas", "metas")]

# TODO(backend): cambiar por el usuario de la sesión cuando exista el login real.
USUARIO_DEMO = {"id": 1, "nombre": "Laura Martínez", "correo": "laura@correo.com", "iniciales": "LM"}


def _contexto_app(request: Request, seccion: str) -> dict:
    return {
        "seccion": seccion,
        "secciones": SECCIONES,
        "proximamente": PROXIMAMENTE,
        "usuario": USUARIO_DEMO,
        "barra_contraida": request.cookies.get(COOKIE_BARRA) == "1",
    }


def _periodo(anio: int | None, mes: int | None) -> tuple[int, int]:
    """Mes pedido, o el actual si no se pide ninguno. No deja ir a meses futuros."""
    hoy = date.today()
    if anio is None or mes is None:
        return hoy.year, hoy.month
    return min((anio, mes), (hoy.year, hoy.month))


def _navegacion_mes(anio: int, mes: int) -> dict:
    hoy = date.today()
    anterior = (anio - 1, 12) if mes == 1 else (anio, mes - 1)
    siguiente = (anio + 1, 1) if mes == 12 else (anio, mes + 1)
    return {
        "anio": anio,
        "mes": mes,
        "anterior": anterior,
        "siguiente": siguiente if siguiente <= (hoy.year, hoy.month) else None,
    }


@router.get("/login", response_class=HTMLResponse)
def login(request: Request):
    context = {"year": date.today().year, "preview": build_preview()}
    return templates.TemplateResponse(request, "login.html", context)


@router.get("/resumen", response_class=HTMLResponse)
def resumen(
    request: Request,
    anio: int | None = Query(None, ge=2000, le=2100),
    mes: int | None = Query(None, ge=1, le=12),
):
    anio, mes = _periodo(anio, mes)
    datos = obtener_resumen(USUARIO_DEMO["id"], anio, mes)
    context = _contexto_app(request, "resumen") | {
        "resumen": datos,
        "vista": vista_resumen(datos),
        "periodo": _navegacion_mes(anio, mes),
    }
    return templates.TemplateResponse(request, "app/resumen.html", context)


def _seccion_pendiente(request: Request, seccion: str, nombre: str, texto: str):
    context = _contexto_app(request, seccion) | {"titulo": nombre, "texto": texto}
    return templates.TemplateResponse(request, "app/pendiente.html", context)


@router.get("/movimientos", response_class=HTMLResponse)
def movimientos(request: Request):
    return _seccion_pendiente(request, "movimientos", "Movimientos",
                              "Aquí vas a ver y filtrar todos tus ingresos y gastos, agrupados por día.")


@router.get("/cuentas", response_class=HTMLResponse)
def cuentas(request: Request):
    return _seccion_pendiente(request, "cuentas", "Cuentas",
                              "Aquí vas a ver el saldo de cada cuenta: banco, billetera digital y efectivo.")


@router.get("/categorias", response_class=HTMLResponse)
def categorias(request: Request):
    return _seccion_pendiente(request, "categorias", "Categorías",
                              "Aquí vas a organizar las categorías de tus ingresos y gastos.")
