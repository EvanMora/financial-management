"""Convierte el contrato del Resumen en lo que necesita la plantilla: porcentajes, alturas y
anchos de las gráficas. Aquí no se consulta nada; solo se hacen cuentas de presentación."""
from app.schemas.dashboard import ResumenDashboard

ALTURA_CAPSULA = 200  # px de la cápsula más alta en "Ingresos vs. gastos"


def _pct(parte, total) -> float:
    return float(parte / total * 100) if total else 0.0


def vista_resumen(resumen: ResumenDashboard) -> dict:
    mayor_mes = max(resumen.ingresos_mes, resumen.gastos_mes)
    mayor_categoria = resumen.gastos_por_categoria[0].total if resumen.gastos_por_categoria else 0

    return {
        "queda": resumen.ingresos_mes - resumen.gastos_mes,
        "pct_gastado": _pct(resumen.gastos_mes, resumen.ingresos_mes),
        "altura_ingresos": round(_pct(resumen.ingresos_mes, mayor_mes) / 100 * ALTURA_CAPSULA),
        "altura_gastos": round(_pct(resumen.gastos_mes, mayor_mes) / 100 * ALTURA_CAPSULA),
        "categorias": [
            {
                "nombre": g.categoria,
                "total": g.total,
                "pct": _pct(g.total, resumen.gastos_mes),
                "ancho": round(_pct(g.total, mayor_categoria), 1),
                "mayor": i == 0,
            }
            for i, g in enumerate(resumen.gastos_por_categoria)
        ],
    }
