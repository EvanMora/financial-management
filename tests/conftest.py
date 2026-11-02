import pytest

from app.services import movimientos


@pytest.fixture(autouse=True)
def _almacen_de_movimientos_limpio():
    """Cada test arranca con el almacén en memoria vacío (se vuelve a sembrar al pedir un mes)."""
    movimientos.reiniciar()
    yield
    movimientos.reiniciar()
