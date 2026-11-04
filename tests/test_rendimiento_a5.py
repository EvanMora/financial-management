"""A5: cambiar de mes no anima la View Transition; cambiar de sección sí."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _head(ruta: str) -> str:
    html = client.get(ruta).text
    return html[: html.index("</head>")]


def test_el_salto_de_la_transicion_va_en_linea_en_el_head():
    # pagereveal se dispara antes del primer pintado: un oyente en un script defer llega tarde.
    for ruta in ("/resumen", "/movimientos", "/presupuestos"):
        head = _head(ruta)
        assert 'addEventListener("pagereveal"' in head, ruta
        assert 'addEventListener("pageswap"' in head, ruta
        assert "skipTransition()" in head, ruta


def test_solo_se_ignoran_anio_y_mes():
    head = _head("/resumen")
    assert 'searchParams.delete("anio")' in head
    assert 'searchParams.delete("mes")' in head
    assert "x.pathname !== y.pathname" in head


def test_la_transicion_entre_secciones_sigue_activa():
    css = client.get("/static/css/app.css").text
    assert "navigation: auto" in css
