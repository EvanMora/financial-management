"""Contrato entre la pantalla de Resumen y el backend.

La plantilla solo conoce estos modelos. Mientras no existan las tablas, services/dashboard.py
devuelve datos de prueba con esta misma forma; cuando estén, se cambian las consultas y la
pantalla no se toca.

Todo el dinero va en Decimal (nunca float) y sin formato: el formato lo pone la plantilla.
"""
from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel


class CuentaSaldo(BaseModel):
    nombre: str
    tipo: str
    saldo: Decimal


class GastoCategoria(BaseModel):
    categoria: str
    total: Decimal


class MovimientoReciente(BaseModel):
    fecha: date
    descripcion: str
    categoria: str
    cuenta: str
    tipo: Literal["ingreso", "gasto"]
    monto: Decimal  # siempre positivo; el tipo dice si suma o resta


class ResumenDashboard(BaseModel):
    anio: int
    mes: int
    saldo_total: Decimal                            # suma del saldo de todas las cuentas
    cuentas: list[CuentaSaldo]
    ingresos_mes: Decimal
    gastos_mes: Decimal
    gastos_por_categoria: list[GastoCategoria]      # solo gastos del mes, de mayor a menor
    movimientos_recientes: list[MovimientoReciente]  # los últimos del mes, del más nuevo al más viejo
