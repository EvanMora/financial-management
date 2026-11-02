"""API del asistente con Gemini. La usa el diálogo "Nuevo movimiento" para completar el formulario
a partir de una frase. Mismo formato de errores que la API de movimientos: {"errores": {campo: mensaje}}.
422: frase vacía o larga · 429: pasó el límite de consultas (con Retry-After) · 503: Gemini no disponible."""
from typing import Any

from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse

from app.schemas.ia import MAX_TEXTO, MovimientoSugerido
from app.services import ia as servicio
from app.web.sesion import USUARIO_DEMO

router = APIRouter(prefix="/api/v1/ia", tags=["ia"])


def _errores(status: int, errores: dict[str, str]) -> JSONResponse:
    return JSONResponse(status_code=status, content={"errores": errores})


@router.post("/interpretar-movimiento", response_model=MovimientoSugerido)
def interpretar_movimiento(cuerpo: Any = Body(None)):
    texto = cuerpo.get("texto") if isinstance(cuerpo, dict) else None
    if not isinstance(texto, str) or not texto.strip():
        return _errores(422, {"texto": "Escribe qué gastaste o recibiste."})
    if len(texto) > MAX_TEXTO:
        return _errores(422, {"texto": f"Máximo {MAX_TEXTO} caracteres."})
    if not servicio.configurado():
        return _errores(503, {"general": "El asistente no está configurado."})
    try:
        return servicio.interpretar(USUARIO_DEMO["id"], texto)
    except servicio.LimiteExcedido as error:
        respuesta = _errores(429, {"general": str(error)})
        respuesta.headers["Retry-After"] = str(error.segundos)
        return respuesta
    except servicio.ErrorIA as error:
        return _errores(503, {"general": str(error)})
