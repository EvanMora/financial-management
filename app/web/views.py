"""Rutas que devuelven HTML renderizado con Jinja2."""
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlencode

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.schemas.movimientos import FiltrosMovimientos
from app.services import categorias as categorias_servicio
from app.services import cuentas as cuentas_servicio
from app.services import ia as ia_servicio
from app.services import movimientos as movimientos_servicio
from app.services.dashboard import obtener_resumen
from app.web import formato
from app.web.presentacion import datos_pago, vista_categorias, vista_cuentas, vista_movimientos, vista_resumen
from app.web.preview import build_preview
from app.web.sesion import USUARIO_DEMO

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



def _grupos_cuentas(usuario_id: int) -> list[tuple[str, list]]:
    """Las cuentas para los <select>, en <optgroup> "Dinero" y "Tarjetas" (sin grupos vacíos)."""
    lista = cuentas_servicio.listar(usuario_id)
    grupos = [("Dinero", [cuentas_servicio.ref(c) for c in lista if not cuentas_servicio.es_tarjeta(c.tipo)]),
              ("Tarjetas", [cuentas_servicio.ref(c) for c in lista if cuentas_servicio.es_tarjeta(c.tipo)])]
    return [(nombre, refs) for nombre, refs in grupos if refs]


def _contexto_app(request: Request, seccion: str) -> dict:
    _, categorias = movimientos_servicio.catalogo(USUARIO_DEMO["id"])
    return {
        "seccion": seccion,
        "secciones": SECCIONES,
        "proximamente": PROXIMAMENTE,
        "usuario": USUARIO_DEMO,
        "barra_contraida": request.cookies.get(COOKIE_BARRA) == "1",
        # Para el diálogo "Nuevo movimiento", que está en todas las secciones.
        "grupos_cuentas": _grupos_cuentas(USUARIO_DEMO["id"]),
        "catalogo_categorias": categorias,
        "hoy_iso": movimientos_servicio.hoy().isoformat(),
        # El asistente con Gemini solo aparece si hay GEMINI_API_KEY.
        "ia_disponible": ia_servicio.configurado(),
    }


def _periodo(anio: int | None, mes: int | None) -> tuple[int, int]:
    """Mes pedido, o el actual si no se pide ninguno. No deja ir a meses futuros. Usa la fecha de
    la app (movimientos.hoy), como el resto de las cuentas."""
    hoy = movimientos_servicio.hoy()
    if anio is None or mes is None:
        return hoy.year, hoy.month
    return min((anio, mes), (hoy.year, hoy.month))


def _navegacion_mes(anio: int, mes: int) -> dict:
    hoy = movimientos_servicio.hoy()
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


def _entero(valor: str | None) -> int | None:
    """Número de la URL, o None. No usa str.isdigit(): acepta "²" y luego int() falla."""
    return int(valor) if valor and re.fullmatch(r"[0-9]{1,9}", valor) else None


def _id_valido(valor: str | None, validos: set[int]) -> int | None:
    """Un id de la URL solo cuenta si es un número que existe en el catálogo; si no, se ignora."""
    numero = _entero(valor)
    return numero if numero in validos else None


def _filtros(tipo: str | None, cuenta: str | None, categoria: str | None, q: str | None) -> FiltrosMovimientos:
    cuentas, categorias = movimientos_servicio.catalogo(USUARIO_DEMO["id"])
    texto = (q or "").strip()[:80]
    return FiltrosMovimientos(
        tipo=tipo if tipo in ("ingreso", "gasto") else None,
        cuenta_id=_id_valido(cuenta, {c.id for c in cuentas}),
        categoria_id=_id_valido(categoria, {c.id for c in categorias}),
        q=texto or None,
    )


def _consulta(f: FiltrosMovimientos) -> str:
    """Los filtros activos como parámetros de URL, para que el selector de mes los conserve."""
    pares = {"tipo": f.tipo, "cuenta": f.cuenta_id, "categoria": f.categoria_id, "q": f.q}
    return urlencode({k: v for k, v in pares.items() if v})


@router.get("/movimientos", response_class=HTMLResponse)
def movimientos(
    request: Request,
    anio: int | None = Query(None, ge=2000, le=2100),
    mes: int | None = Query(None, ge=1, le=12),
    tipo: str | None = None,
    cuenta: str | None = None,
    categoria: str | None = None,
    q: str | None = None,
    nuevo: str | None = None,
    guardado: str | None = None,
):
    anio, mes = _periodo(anio, mes)
    filtros = _filtros(tipo, cuenta, categoria, q)
    lista = movimientos_servicio.listar(USUARIO_DEMO["id"], anio, mes, filtros)
    pagos = cuentas_servicio.pagos_del_mes(USUARIO_DEMO["id"], anio, mes, filtros)
    _, categorias = movimientos_servicio.catalogo(USUARIO_DEMO["id"])
    context = _contexto_app(request, "movimientos") | {
        "lista": lista,
        "vista": vista_movimientos(lista, pagos),
        "pago": datos_pago(cuentas_servicio.panel(USUARIO_DEMO["id"])),
        "periodo": _navegacion_mes(anio, mes),
        "consulta": _consulta(filtros),
        "categorias": categorias,
        "abrir_dialogo": nuevo == "1",
        "guardado": _entero(guardado),
    }
    return templates.TemplateResponse(request, "app/movimientos.html", context)


@router.get("/cuentas", response_class=HTMLResponse)
def cuentas(request: Request, guardado: str | None = None):
    panel = cuentas_servicio.panel(USUARIO_DEMO["id"])
    context = _contexto_app(request, "cuentas") | {
        "panel": panel,
        "vista": vista_cuentas(panel),
        "pago": datos_pago(panel),
        "guardado": _entero(guardado),
    }
    return templates.TemplateResponse(request, "app/cuentas.html", context)


@router.get("/categorias", response_class=HTMLResponse)
def categorias(
    request: Request,
    anio: int | None = Query(None, ge=2000, le=2100),
    mes: int | None = Query(None, ge=1, le=12),
    guardado: str | None = None,
):
    anio, mes = _periodo(anio, mes)
    datos = categorias_servicio.del_mes(USUARIO_DEMO["id"], anio, mes)
    context = _contexto_app(request, "categorias") | {
        "datos": datos,
        "vista": vista_categorias(datos),
        "periodo": _navegacion_mes(anio, mes),
        "guardado": _entero(guardado),
    }
    return templates.TemplateResponse(request, "app/categorias.html", context)
