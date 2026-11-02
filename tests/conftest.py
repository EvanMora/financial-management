import pytest

from app.services import ia, movimientos


@pytest.fixture(autouse=True)
def _almacen_de_movimientos_limpio():
    """Cada test arranca con el almacén en memoria vacío (se vuelve a sembrar al pedir un mes) y
    sin consultas al asistente contadas para el límite de uso ni análisis guardados."""
    movimientos.reiniciar()
    ia.reiniciar_limite()
    ia.reiniciar_cache_analisis()
    yield
    movimientos.reiniciar()
    ia.reiniciar_limite()
    ia.reiniciar_cache_analisis()
