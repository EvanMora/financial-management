"""Convierte los contratos en lo que necesitan las plantillas: porcentajes, alturas y anchos de
las gráficas del Resumen, y los días agrupados de Movimientos. Aquí no se consulta nada; solo se
hacen cuentas de presentación."""
from decimal import Decimal
from itertools import groupby

from app.schemas.dashboard import ResumenDashboard
from app.schemas.movimientos import ListaMovimientos, Movimiento

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


def _neto(movimientos: list[Movimiento]) -> Decimal:
    return sum((m.monto if m.tipo == "ingreso" else -m.monto for m in movimientos), Decimal(0))


def datos_edicion(m: Movimiento) -> dict:
    """Lo que necesita el diálogo para abrir un movimiento en modo edición (va en data-movimiento)."""
    return {
        "id": m.id,
        "tipo": m.tipo,
        "monto": format(m.monto, "f"),  # nunca con exponente: el JS lee los dígitos
        "categoria_id": m.categoria.id,
        "cuenta_id": m.cuenta.id,
        "fecha": m.fecha.isoformat(),
        "descripcion": m.descripcion,
        "nombre": m.descripcion or m.categoria.nombre,
    }


def vista_movimientos(lista: ListaMovimientos) -> dict:
    f = lista.filtros
    dias = []
    for fecha, grupo in groupby(lista.movimientos, key=lambda m: m.fecha):
        movimientos = list(grupo)
        dias.append({
            "fecha": fecha,
            "neto": _neto(movimientos),
            "filas": [{"m": m, "datos": datos_edicion(m)} for m in movimientos],
        })
    return {
        "dias": dias,
        "balance": lista.ingresos - lista.gastos,
        "hay_filtros": bool(f.tipo or f.cuenta_id or f.categoria_id or (f.q or "").strip()),
    }
