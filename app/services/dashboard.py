"""Datos de la pantalla de Resumen.

Por ahora devuelve datos de prueba que cuadran entre sí (los mismos de la vista previa del
login). TODO(backend): reemplazar el cuerpo de obtener_resumen() por las consultas reales
filtradas por usuario_id; la firma y el modelo de respuesta se mantienen.
"""
from datetime import date
from decimal import Decimal

from app.schemas.dashboard import CuentaSaldo, GastoCategoria, MovimientoReciente, ResumenDashboard

CANTIDAD_RECIENTES = 4

_CUENTAS = [
    ("Cuenta de ahorros", "Banco", "3612400"),
    ("Billetera digital", "Billetera", "525000"),
    ("Efectivo", "Efectivo", "245500"),
]

# (día, descripción, categoría, cuenta, tipo, monto)
_MOVIMIENTOS = [
    (31, "Salario", "Salario", "Cuenta de ahorros", "ingreso", "3200000"),
    (30, "Supermercado", "Mercado", "Billetera digital", "gasto", "184300"),
    (28, "Taxi", "Transporte", "Efectivo", "gasto", "62000"),
    (25, "Arriendo", "Arriendo", "Cuenta de ahorros", "gasto", "1100000"),
    (22, "Cine", "Ocio", "Billetera digital", "gasto", "48000"),
    (18, "Cena", "Ocio", "Cuenta de ahorros", "gasto", "132000"),
    (15, "Plaza de mercado", "Mercado", "Efectivo", "gasto", "200000"),
    (10, "Recarga tarjeta de transporte", "Transporte", "Billetera digital", "gasto", "148000"),
]


def _ultimo_dia(anio: int, mes: int) -> int:
    siguiente = date(anio + mes // 12, mes % 12 + 1, 1)
    return (siguiente - date(anio, mes, 1)).days


def obtener_resumen(usuario_id: int, anio: int, mes: int) -> ResumenDashboard:
    ultimo = _ultimo_dia(anio, mes)
    movimientos = [
        MovimientoReciente(
            fecha=date(anio, mes, min(dia, ultimo)),
            descripcion=descripcion,
            categoria=categoria,
            cuenta=cuenta,
            tipo=tipo,
            monto=Decimal(monto),
        )
        for dia, descripcion, categoria, cuenta, tipo, monto in _MOVIMIENTOS
    ]

    gastos: dict[str, Decimal] = {}
    for m in movimientos:
        if m.tipo == "gasto":
            gastos[m.categoria] = gastos.get(m.categoria, Decimal(0)) + m.monto

    cuentas = [CuentaSaldo(nombre=n, tipo=t, saldo=Decimal(s)) for n, t, s in _CUENTAS]

    return ResumenDashboard(
        anio=anio,
        mes=mes,
        saldo_total=sum((c.saldo for c in cuentas), Decimal(0)),
        cuentas=cuentas,
        ingresos_mes=sum((m.monto for m in movimientos if m.tipo == "ingreso"), Decimal(0)),
        gastos_mes=sum(gastos.values(), Decimal(0)),
        gastos_por_categoria=[
            GastoCategoria(categoria=c, total=t) for c, t in sorted(gastos.items(), key=lambda par: par[1], reverse=True)
        ],
        movimientos_recientes=sorted(movimientos, key=lambda m: m.fecha, reverse=True)[:CANTIDAD_RECIENTES],
    )
