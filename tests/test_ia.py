"""Asistente con Gemini. Gemini se reemplaza por respuestas fijas: los tests nunca llaman a la API."""
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import ia
from app.services import movimientos

client = TestClient(app)
URL = "/api/v1/ia/interpretar-movimiento"


@pytest.fixture(autouse=True)
def entorno(monkeypatch):
    monkeypatch.setattr(movimientos, "hoy", lambda: date(2026, 11, 15))
    monkeypatch.setenv("GEMINI_API_KEY", "clave-de-prueba")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)


def gemini_responde(monkeypatch, **campos):
    """Hace que Gemini devuelva esta respuesta y guarda el prompt que recibió."""
    respuesta = {"tipo": "gasto", "monto": 45000, "categoria_id": 4, "cuenta_id": 3,
                 "fecha": "2026-11-14", "descripcion": "Taxi"} | campos
    prompts = []

    def falso(prompt):
        prompts.append(prompt)
        return ia._RespuestaGemini(**respuesta)

    monkeypatch.setattr(ia, "_llamar_gemini", falso)
    return prompts


def test_frase_completa_devuelve_la_sugerencia(monkeypatch):
    prompts = gemini_responde(monkeypatch)

    r = client.post(URL, json={"texto": "ayer gasté 45.000 en taxi en efectivo"})

    assert r.status_code == 200
    assert r.json() == {"tipo": "gasto", "monto": "45000", "categoria_id": 4, "cuenta_id": 3,
                        "fecha": "2026-11-14", "descripcion": "Taxi"}
    # Gemini recibe la fecha de hoy, el catálogo y la frase.
    assert "domingo 2026-11-15" in prompts[0]
    assert "- 4: Transporte, gasto" in prompts[0] and "- 3: Efectivo" in prompts[0]
    assert prompts[0].endswith("ayer gasté 45.000 en taxi en efectivo")


@pytest.mark.parametrize(
    ("campos", "esperado"),
    [
        ({"monto": 0}, {"monto": None}),
        ({"monto": -500}, {"monto": None}),
        ({"monto": 10**13}, {"monto": None}),
        ({"categoria_id": 99}, {"categoria_id": None}),
        ({"categoria_id": 1}, {"categoria_id": None}),  # Salario es de ingresos, no de gastos
        ({"cuenta_id": 99}, {"cuenta_id": None}),
        ({"fecha": "2026-12-01"}, {"fecha": None}),  # futura
        ({"fecha": "ayer"}, {"fecha": None}),
        ({"fecha": None}, {"fecha": None}),
        ({"descripcion": "  Taxi   al\naeropuerto "}, {"descripcion": "Taxi al aeropuerto"}),
        ({"descripcion": "x" * 200}, {"descripcion": "x" * 80}),
    ],
)
def test_lo_que_no_es_valido_se_descarta(monkeypatch, campos, esperado):
    gemini_responde(monkeypatch, **campos)

    sugerido = client.post(URL, json={"texto": "taxi"}).json()

    for campo, valor in esperado.items():
        assert sugerido[campo] == valor


def test_ingreso(monkeypatch):
    gemini_responde(monkeypatch, tipo="ingreso", monto=3200000, categoria_id=1, cuenta_id=1,
                    descripcion="Salario")

    sugerido = client.post(URL, json={"texto": "me pagaron el sueldo"}).json()

    assert sugerido["tipo"] == "ingreso" and sugerido["categoria_id"] == 1 and sugerido["monto"] == "3200000"


@pytest.mark.parametrize("cuerpo", [{}, {"texto": ""}, {"texto": "   "}, {"texto": 5}, [1, 2], None])
def test_texto_vacio_o_invalido(monkeypatch, cuerpo):
    gemini_responde(monkeypatch)

    r = client.post(URL, json=cuerpo)

    assert r.status_code == 422
    assert r.json()["errores"]["texto"] == "Escribe qué gastaste o recibiste."


def test_texto_demasiado_largo(monkeypatch):
    gemini_responde(monkeypatch)

    r = client.post(URL, json={"texto": "a" * 301})

    assert r.status_code == 422
    assert r.json()["errores"]["texto"] == "Máximo 300 caracteres."


def test_sin_clave_responde_503_sin_llamar_a_gemini(monkeypatch):
    prompts = gemini_responde(monkeypatch)
    monkeypatch.delenv("GEMINI_API_KEY")

    r = client.post(URL, json={"texto": "taxi"})

    assert r.status_code == 503
    assert r.json()["errores"]["general"] == "El asistente no está configurado."
    assert prompts == []


def test_si_gemini_falla_responde_503(monkeypatch):
    def falla(prompt):
        raise ia.ErrorIA("El asistente no respondió. Llena el formulario o inténtalo de nuevo.")

    monkeypatch.setattr(ia, "_llamar_gemini", falla)

    r = client.post(URL, json={"texto": "taxi"})

    assert r.status_code == 503
    assert "no respondió" in r.json()["errores"]["general"]


def test_errores_del_sdk_se_convierten_en_error_ia(monkeypatch):
    class ClienteRoto:
        class models:
            @staticmethod
            def generate_content(**_):
                raise ConnectionError("sin red")

    monkeypatch.setattr(ia, "_cliente", lambda api_key: ClienteRoto)

    with pytest.raises(ia.ErrorIA):
        ia._llamar_gemini("taxi")


def test_el_asistente_aparece_en_el_dialogo_solo_con_clave(monkeypatch):
    assert "data-ia-texto" in client.get("/resumen").text

    monkeypatch.delenv("GEMINI_API_KEY")
    assert "data-ia-texto" not in client.get("/resumen").text


def test_el_menu_del_asistente_aparece_en_el_resumen_solo_con_clave(monkeypatch):
    html = client.get("/resumen").text
    assert "data-asistente-abrir" in html and "js/asistente.js" in html

    monkeypatch.delenv("GEMINI_API_KEY")
    html = client.get("/resumen").text
    assert "data-asistente-abrir" not in html and "js/asistente.js" not in html
