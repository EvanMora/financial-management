import pytest

from app.services import categorias, cuentas, ia, movimientos


@pytest.fixture(autouse=True)
def _almacen_de_movimientos_limpio():
    """Cada test arranca con el almacén en memoria vacío (se vuelve a sembrar al pedir un mes) y
    sin categorías propias, sin consultas al asistente contadas para el límite de uso ni análisis
    guardados."""
    movimientos.reiniciar()
    categorias.reiniciar()
    cuentas.reiniciar()
    ia.reiniciar_limite()
    ia.reiniciar_cache_analisis()
    yield
    movimientos.reiniciar()
    categorias.reiniciar()
    cuentas.reiniciar()
    ia.reiniciar_limite()
    ia.reiniciar_cache_analisis()
