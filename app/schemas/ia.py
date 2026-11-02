"""Contrato del asistente que completa el diálogo "Nuevo movimiento" a partir de una frase.

El usuario escribe algo como "ayer gasté 45.000 en taxi con efectivo"; Gemini lo interpreta y la
API devuelve un MovimientoSugerido. Es solo una sugerencia: el diálogo la muestra en el
formulario y el usuario la revisa y guarda como siempre (POST /api/v1/movimientos).
"""
from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from app.schemas.movimientos import Tipo

MAX_TEXTO = 300


class InterpretarEntrada(BaseModel):
    texto: str


class MovimientoSugerido(BaseModel):
    """Lo que se pudo entender. Cada campo que no se entendió (o no es válido) llega en null y el
    diálogo lo deja como estaba."""
    tipo: Tipo
    monto: Decimal | None = None
    categoria_id: int | None = None
    cuenta_id: int | None = None
    fecha: date | None = None
    descripcion: str = ""
