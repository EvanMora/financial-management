"""Página de Movimientos: lista por día, totales, filtros en la URL y estados vacíos."""
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import movimientos as servicio

client = TestClient(app)


@pytest.fixture(autouse=True)
def hoy_fijo(monkeypatch):
    monkeypatch.setattr(servicio, "hoy", lambda: date(2026, 11, 1))


def lista_html(url: str) -> str:
    """Solo la parte de la lista, para no confundir montos con los de los totales."""
    html = client.get(url).text
    return html.split('data-lista', 1)[1]


def test_lista_agrupada_y_totales():
    html = client.get("/movimientos?anio=2026&mes=10").text

    assert "Sábado 31 de octubre" in html
    assert "Viernes 30 de octubre" in html
    assert "+$3.200.000" in html
    assert "−$1.874.300" in html
    assert "+$1.325.700" in html  # balance
    assert "Mercado · Billetera digital" in html
    assert "Según los filtros" not in html
    assert "Quitar filtros" not in html


def test_filtros_en_la_url_y_quitar_filtros():
    html = client.get("/movimientos?anio=2026&mes=10&tipo=gasto").text

    assert "+$3.200.000" not in lista_html("/movimientos?anio=2026&mes=10&tipo=gasto")
    assert "Según los filtros" in html
    assert 'href="/movimientos?anio=2026&amp;mes=10">Quitar filtros' in html
    assert 'value="gasto" checked' in html


def test_selector_de_mes_conserva_filtros():
    html = client.get("/movimientos?anio=2026&mes=10&tipo=gasto&q=taxi").text

    assert 'href="/movimientos?anio=2026&amp;mes=9&amp;tipo=gasto&amp;q=taxi"' in html


def test_parametros_invalidos_se_ignoran():
    r = client.get("/movimientos?anio=2026&mes=10&cuenta=abc&tipo=x&categoria=999")

    assert r.status_code == 200
    assert "Según los filtros" not in r.text


@pytest.mark.parametrize("consulta", ["cuenta=%C2%B2", "categoria=%C2%B9", "guardado=%C2%B2",
                                      "guardado=" + "9" * 5000, "cuenta=" + "1" * 5000])
def test_parametros_que_parecen_numeros_no_rompen_la_pagina(consulta):
    r = client.get(f"/movimientos?anio=2026&mes=10&{consulta}")

    assert r.status_code == 200
    assert "Según los filtros" not in r.text


def test_estado_vacio_del_mes():
    html = client.get("/movimientos?anio=2026&mes=11").text

    assert "No hay movimientos en noviembre" in html
    assert "Registrar un movimiento" in html


def test_filtros_sin_resultados():
    html = client.get("/movimientos?anio=2026&mes=10&q=zzz").text

    assert "Ningún movimiento coincide con los filtros" in html


def test_fila_lleva_sus_datos_para_editar():
    html = client.get("/movimientos?anio=2026&mes=10&q=taxi").text

    assert "data-movimiento=" in html
    assert "&#34;descripcion&#34;: &#34;Taxi&#34;" in html or '"descripcion": "Taxi"' in html


def test_nuevo_abre_dialogo_y_guardado_resalta():
    assert "data-abrir-dialogo" in client.get("/movimientos?nuevo=1").text
    assert "data-abrir-dialogo" not in client.get("/movimientos").text
    assert 'data-guardado="5"' in client.get("/movimientos?anio=2026&mes=10&guardado=5").text


def test_monto_con_exponente_se_ofrece_sin_exponente_para_editar():
    client.post("/api/v1/movimientos", json={"tipo": "gasto", "monto": "1e5", "categoria_id": 3, "cuenta_id": 1,
                                             "fecha": "2026-10-20", "descripcion": "Exponente"})
    html = client.get("/movimientos?anio=2026&mes=10&q=exponente").text

    assert "&#34;monto&#34;: &#34;100000&#34;" in html or '"monto": "100000"' in html
