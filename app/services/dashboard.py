"""Datos de la pantalla de Resumen.

Ingresos, gastos, categorías y recientes salen de services/movimientos.py, así el Resumen y la
sección Movimientos siempre muestran las mismas cifras. Los saldos de las cuentas siguen siendo
de prueba. TODO(backend): calcular cada saldo como saldo inicial + ingresos − gastos (ver
docs/alcance.md); la firma y el modelo de respuesta se mantienen.
"""
from decimal import Decimal

from app.schemas.dashboard import CuentaSaldo, GastoCategoria, ResumenDashboard
from app.services import movimientos

CANTIDAD_RECIENTES = 4

_CUENTAS = [
    ("Cuenta de ahorros", "Banco", "3612400"),
    ("Billetera digital", "Billetera", "525000"),
    ("Efectivo", "Efectivo", "245500"),
]


def obtener_resumen(usuario_id: int, anio: int, mes: int) -> ResumenDashboard:
    lista = movimientos.listar(usuario_id, anio, mes)

    gastos: dict[str, Decimal] = {}
    for m in lista.movimientos:
        if m.tipo == "gasto":
            gastos[m.categoria.nombre] = gastos.get(m.categoria.nombre, Decimal(0)) + m.monto

    cuentas = [CuentaSaldo(nombre=n, tipo=t, saldo=Decimal(s)) for n, t, s in _CUENTAS]

    return ResumenDashboard(
        anio=anio,
        mes=mes,
        saldo_total=sum((c.saldo for c in cuentas), Decimal(0)),
        cuentas=cuentas,
        ingresos_mes=lista.ingresos,
        gastos_mes=lista.gastos,
        gastos_por_categoria=[
            GastoCategoria(categoria=c, total=t) for c, t in sorted(gastos.items(), key=lambda par: par[1], reverse=True)
        ],
        movimientos_recientes=lista.movimientos[:CANTIDAD_RECIENTES],
    )
