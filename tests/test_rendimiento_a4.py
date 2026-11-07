"""Regresión A4: la animación de entrada no debe esconder el contenido ni alargarse."""

import re
from pathlib import Path

CSS = Path(__file__).resolve().parent.parent / "app" / "static" / "css"


def _bloque(texto: str, cabecera: str) -> str:
    inicio = texto.index(cabecera)
    return texto[inicio : texto.index("\n}", inicio)]


def test_view_in_no_anima_la_opacidad():
    # Con opacidad 0 el contenido no se ve y Chrome lo descarta como LCP.
    assert "opacity" not in _bloque((CSS / "app.css").read_text(), "@keyframes view-in")


def test_barras_crecen_sin_espera_y_en_400ms_o_menos():
    resumen = (CSS / "resumen.css").read_text()
    for nombre in ("grow-y", "grow-x"):
        declaracion = re.search(rf"animation: {nombre} (\d+)ms [^;]*;", resumen)
        assert declaracion, nombre
        assert int(declaracion.group(1)) <= 400
        # Un segundo tiempo en la declaración sería un retraso.
        assert len(re.findall(r"\d+ms", declaracion.group(0))) == 1

    relleno = _bloque((CSS / "presupuesto-barra.css").read_text(), ".pres-pista__relleno {")
    assert "pista-in 400ms" in relleno
    assert "200ms" not in relleno


def _ms(valor: str) -> float:
    return float(valor[:-2]) if valor.endswith("ms") else float(valor[:-1]) * 1000


def test_el_cambio_de_seccion_no_superpone_las_dos_paginas():
    """Los bloques ya no arrancan con opacidad 0, así que la captura nueva tiene que entrar
    cuando la vieja terminó de salir. Si no, se ven restos de la página anterior encima."""
    app_css = (CSS / "app.css").read_text()
    vieja = _bloque(app_css, "::view-transition-old(contenido) {")
    nueva = _bloque(app_css, "::view-transition-new(contenido) {")
    salida = re.search(r"vt-fuera\s+(\d+m?s)", vieja)
    entrada = re.search(r"vt-dentro\s+\d+m?s\s+\S+(?:\([^)]*\))?\s+(\d+m?s)", nueva)
    assert salida and entrada, "faltan las animaciones vt-fuera / vt-dentro"
    assert _ms(entrada.group(1)) >= _ms(salida.group(1))
    assert "opacity: 0" in _bloque(app_css, "@keyframes vt-dentro {")
