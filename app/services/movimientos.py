"""Movimientos: listar con filtros, crear, editar y eliminar.

Por ahora guarda todo en memoria del proceso (se pierde al reiniciar el servidor). Cada mes se
siembra con datos de prueba la primera vez que se pide, así cualquier mes tiene datos y los
tests con meses fijos dan siempre las mismas cifras. En el mes en curso solo se siembran los
días que ya pasaron.

TODO(backend): reemplazar el almacén por consultas filtradas por usuario_id. Las firmas, los
modelos de app/schemas/movimientos.py y las reglas de _validar() se mantienen.
"""
import unicodedata
from datetime import date
from decimal import Decimal

from app.schemas.movimientos import (
    CategoriaRef,
    CuentaRef,
    FiltrosMovimientos,
    ListaMovimientos,
    Movimiento,
    MovimientoEntrada,
)

MAX_DESCRIPCION = 80
# Tope del monto: 12 dígitos enteros, los mismos que acepta el campo del diálogo. Sin tope, un
# monto como 1E+30 no cabe en la precisión de Decimal y rompe el formato de toda la pantalla.
MAX_MONTO = Decimal("1000000000000")

# TODO(backend): cuentas y categorías del usuario (las categorías por defecto tienen usuario_id null).
_CUENTAS = [CuentaRef(id=1, nombre="Cuenta de ahorros"), CuentaRef(id=2, nombre="Billetera digital"),
            CuentaRef(id=3, nombre="Efectivo")]
_CATEGORIAS = [
    CategoriaRef(id=1, nombre="Salario", tipo="ingreso"),
    CategoriaRef(id=2, nombre="Otros ingresos", tipo="ingreso"),
    CategoriaRef(id=3, nombre="Mercado", tipo="gasto"),
    CategoriaRef(id=4, nombre="Transporte", tipo="gasto"),
    CategoriaRef(id=5, nombre="Arriendo", tipo="gasto"),
    CategoriaRef(id=6, nombre="Ocio", tipo="gasto"),
    CategoriaRef(id=7, nombre="Otros gastos", tipo="gasto"),
]

# Plantilla de cada mes: (día, descripción, categoría, cuenta, tipo, monto).
_PLANTILLA = [
    (31, "Salario", "Salario", "Cuenta de ahorros", "ingreso", "3200000"),
    (30, "Supermercado", "Mercado", "Billetera digital", "gasto", "184300"),
    (28, "Taxi", "Transporte", "Efectivo", "gasto", "62000"),
    (25, "Arriendo", "Arriendo", "Cuenta de ahorros", "gasto", "1100000"),
    (22, "Cine", "Ocio", "Billetera digital", "gasto", "48000"),
    (18, "Cena", "Ocio", "Cuenta de ahorros", "gasto", "132000"),
    (15, "Plaza de mercado", "Mercado", "Efectivo", "gasto", "200000"),
    (10, "Recarga tarjeta de transporte", "Transporte", "Billetera digital", "gasto", "148000"),
]

_movimientos: dict[int, Movimiento] = {}
_meses_sembrados: set[tuple[int, int]] = set()
_siguiente_id = 1


class ErrorValidacion(Exception):
    def __init__(self, errores: dict[str, str]):
        super().__init__(errores)
        self.errores = errores


class NoEncontrado(Exception):
    pass


def hoy() -> date:
    return date.today()


def reiniciar() -> None:
    """Vacía el almacén. Solo para tests."""
    global _siguiente_id
    _movimientos.clear()
    _meses_sembrados.clear()
    _siguiente_id = 1


def _nuevo_id() -> int:
    global _siguiente_id
    _siguiente_id += 1
    return _siguiente_id - 1


def _ultimo_dia(anio: int, mes: int) -> int:
    siguiente = date(anio + mes // 12, mes % 12 + 1, 1)
    return (siguiente - date(anio, mes, 1)).days


def _por_nombre(lista, nombre):
    return next(x for x in lista if x.nombre == nombre)


def _sembrar(anio: int, mes: int) -> None:
    if (anio, mes) in _meses_sembrados:
        return
    _meses_sembrados.add((anio, mes))
    ultimo = _ultimo_dia(anio, mes)
    limite = hoy()
    # De la más vieja a la más nueva, para que los ids crezcan con la fecha.
    for dia, descripcion, categoria, cuenta, tipo, monto in reversed(_PLANTILLA):
        fecha = date(anio, mes, min(dia, ultimo))
        if fecha > limite:
            continue
        nuevo = Movimiento(id=_nuevo_id(), fecha=fecha, descripcion=descripcion,
                           categoria=_por_nombre(_CATEGORIAS, categoria),
                           cuenta=_por_nombre(_CUENTAS, cuenta), tipo=tipo, monto=Decimal(monto))
        _movimientos[nuevo.id] = nuevo


def _normalizar(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in sin_tildes if not unicodedata.combining(c)).casefold()


def _coincide(m: Movimiento, f: FiltrosMovimientos, buscar: str) -> bool:
    if f.tipo and m.tipo != f.tipo:
        return False
    if f.cuenta_id and m.cuenta.id != f.cuenta_id:
        return False
    if f.categoria_id and m.categoria.id != f.categoria_id:
        return False
    if buscar and buscar not in _normalizar(m.descripcion) and buscar not in _normalizar(m.categoria.nombre):
        return False
    return True


def catalogo(usuario_id: int) -> tuple[list[CuentaRef], list[CategoriaRef]]:
    # TODO(backend): cuentas y categorías de usuario_id.
    return list(_CUENTAS), list(_CATEGORIAS)


def listar(usuario_id: int, anio: int, mes: int, filtros: FiltrosMovimientos | None = None) -> ListaMovimientos:
    # TODO(backend): SELECT de los movimientos de usuario_id en el mes, con los filtros.
    filtros = filtros or FiltrosMovimientos()
    _sembrar(anio, mes)
    buscar = _normalizar((filtros.q or "").strip())
    encontrados = sorted(
        (m for m in _movimientos.values()
         if m.fecha.year == anio and m.fecha.month == mes and _coincide(m, filtros, buscar)),
        key=lambda m: (m.fecha, m.id),
        reverse=True,
    )
    return ListaMovimientos(
        anio=anio,
        mes=mes,
        filtros=filtros,
        movimientos=encontrados,
        ingresos=sum((m.monto for m in encontrados if m.tipo == "ingreso"), Decimal(0)),
        gastos=sum((m.monto for m in encontrados if m.tipo == "gasto"), Decimal(0)),
    )


def obtener(usuario_id: int, id: int) -> Movimiento | None:
    # TODO(backend): SELECT por id y usuario_id.
    return _movimientos.get(id)


def _normalizar_monto(monto: Decimal) -> Decimal:
    """Sin exponente ("1E+5" → 100000) y con a lo sumo 2 decimales."""
    return monto.quantize(Decimal(1)) if monto == monto.to_integral_value() else monto.quantize(Decimal("0.01"))


def _validar(entrada: MovimientoEntrada) -> tuple[CategoriaRef, CuentaRef, str]:
    errores: dict[str, str] = {}
    if not entrada.monto.is_finite() or entrada.monto <= 0:
        errores["monto"] = "Escribe un monto mayor que 0."
    elif entrada.monto >= MAX_MONTO:
        errores["monto"] = "El monto es demasiado grande."
    categoria = next((c for c in _CATEGORIAS if c.id == entrada.categoria_id), None)
    if categoria is None:
        errores["categoria_id"] = "Elige una categoría."
    elif categoria.tipo != entrada.tipo:
        errores["categoria_id"] = f"Esa categoría es de {'ingresos' if categoria.tipo == 'ingreso' else 'gastos'}."
    cuenta = next((c for c in _CUENTAS if c.id == entrada.cuenta_id), None)
    if cuenta is None:
        errores["cuenta_id"] = "Elige una cuenta."
    if entrada.fecha > hoy():
        errores["fecha"] = "La fecha no puede ser futura."
    descripcion = entrada.descripcion.strip()
    if len(descripcion) > MAX_DESCRIPCION:
        errores["descripcion"] = f"Máximo {MAX_DESCRIPCION} caracteres."
    if errores:
        raise ErrorValidacion(errores)
    return categoria, cuenta, descripcion


def _guardar(id: int, entrada: MovimientoEntrada) -> Movimiento:
    categoria, cuenta, descripcion = _validar(entrada)
    # Sembrar el mes de destino antes de guardar, para que una siembra posterior no lo pise.
    _sembrar(entrada.fecha.year, entrada.fecha.month)
    movimiento = Movimiento(id=id, fecha=entrada.fecha, descripcion=descripcion, categoria=categoria,
                            cuenta=cuenta, tipo=entrada.tipo, monto=_normalizar_monto(entrada.monto))
    _movimientos[id] = movimiento
    return movimiento


def crear(usuario_id: int, entrada: MovimientoEntrada) -> Movimiento:
    # TODO(backend): INSERT con usuario_id.
    _validar(entrada)
    _sembrar(entrada.fecha.year, entrada.fecha.month)  # antes del id, para que el nuevo sea el mayor
    return _guardar(_nuevo_id(), entrada)


def actualizar(usuario_id: int, id: int, entrada: MovimientoEntrada) -> Movimiento:
    # TODO(backend): UPDATE por id y usuario_id.
    if id not in _movimientos:
        raise NoEncontrado(id)
    return _guardar(id, entrada)


def eliminar(usuario_id: int, id: int) -> None:
    # TODO(backend): DELETE por id y usuario_id.
    if _movimientos.pop(id, None) is None:
        raise NoEncontrado(id)
