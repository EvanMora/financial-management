"""Lo que comparten los servicios: los errores que la API traduce a respuestas y la comparación
de textos sin tildes ni mayúsculas."""
import unicodedata


class ErrorValidacion(Exception):
    """Errores por campo: {campo: mensaje}. La API responde 422 con {"errores": ...}."""

    def __init__(self, errores: dict[str, str]):
        super().__init__(errores)
        self.errores = errores


class NoEncontrado(Exception):
    pass


class NoPermitido(Exception):
    """Existe, pero el usuario no lo puede cambiar (p. ej. una categoría predeterminada)."""


def normalizar(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in sin_tildes if not unicodedata.combining(c)).casefold()
