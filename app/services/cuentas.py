"""Cuentas: dinero (ahorros, corriente, billetera, efectivo) y tarjetas de crédito.

Saldos (ver docs/superpowers/specs/2026-11-02-cuentas-design.md):
- Dinero: inicial + ingresos − gastos, contando solo movimientos con fecha >= creada_en.
- Tarjeta: la deuda es inicial + gastos − ingresos (un ingreso a una tarjeta es una devolución).
  Disponible = cupo − deuda.
- Editar el "saldo de hoy" ajusta inicial en la diferencia: no es un movimiento.

Reglas: nombre obligatorio, de hasta MAX_NOMBRE caracteres y único entre las cuentas de la persona
(sin tildes ni mayúsculas); una cuenta con movimientos no pasa de dinero a tarjeta ni al revés;
eliminarla con movimientos exige pasarlos a otra cuenta del mismo grupo, y si no hay otra, no se
elimina. Nunca se borran movimientos.

El usuario demo empieza con las tres cuentas que usa la plantilla de services/movimientos.py y una
tarjeta. Se crean el primer día del mes anterior a hoy(), así solo cuentan uno o dos meses de la
plantilla y ninguna queda en negativo.

Por ahora todo vive en memoria del proceso. TODO(backend): tabla Cuenta con usuario_id; los saldos
salen de SUMs sobre movimientos con fecha >= creada_en. Las firmas y los modelos se mantienen.

services/movimientos.py importa este módulo. Las funciones de aquí que necesitan los movimientos
lo importan adentro para no formar un ciclo (igual que services/categorias.py).
"""
from calendar import monthrange
from datetime import date
from decimal import Decimal

from app.schemas.cuentas import Cuenta, CuentaConSaldo, CuentaEntrada, PanelCuentas
from app.schemas.movimientos import CuentaRef, Movimiento
from app.services.comun import ErrorValidacion, NoEncontrado, normalizar

MAX_NOMBRE = 40
MAX_CUENTAS = 30  # por usuario

# TODO(backend): quitar cuando exista el registro de usuarios; hoy solo el demo tiene cuentas de prueba.
DEMO_USUARIO_ID = 1
# (id, nombre, tipo, icono, tono, inicial, cupo, dia_pago)
_DEMO = [
    (1, "Cuenta de ahorros", "ahorros", "banco", "azul", "1644400", None, None),
    (2, "Billetera digital", "billetera", "celular", "ciruela", "1053300", None, None),
    (3, "Efectivo", "efectivo", "billetes", "cafe", "707500", None, None),
    (4, "Tarjeta de crédito", "tarjeta", "tarjeta", "violeta", "840000", "3000000", 15),
]
# Nombres que usa la plantilla de movimientos → id de la cuenta demo.
_PLANTILLA = {"Cuenta de ahorros": 1, "Billetera digital": 2, "Efectivo": 3}
_PRIMER_ID = 100

_cuentas: dict[int, tuple[int, Cuenta]] = {}  # id → (usuario_id, cuenta)
_demo_creado = False
_siguiente_id = _PRIMER_ID


def reiniciar() -> None:
    """Vuelve al estado inicial (el demo se crea de nuevo al pedirlo). Solo para tests."""
    global _demo_creado, _siguiente_id
    _cuentas.clear()
    _demo_creado = False
    _siguiente_id = _PRIMER_ID


def es_tarjeta(tipo: str) -> bool:
    return tipo == "tarjeta"


def ref(c: Cuenta) -> CuentaRef:
    """La forma que llevan los movimientos."""
    return CuentaRef(id=c.id, nombre=c.nombre)


def _hoy() -> date:
    from app.services import movimientos
    return movimientos.hoy()


def _mes_anterior(d: date) -> date:
    return date(d.year - 1, 12, 1) if d.month == 1 else date(d.year, d.month - 1, 1)


def _crear_demo() -> None:
    global _demo_creado
    if _demo_creado:
        return
    _demo_creado = True
    creada_en = _mes_anterior(_hoy())
    for id, nombre, tipo, icono, tono, inicial, cupo, dia_pago in _DEMO:
        _cuentas[id] = (DEMO_USUARIO_ID, Cuenta(
            id=id, nombre=nombre, tipo=tipo, icono=icono, tono=tono, creada_en=creada_en,
            inicial=Decimal(inicial), cupo=Decimal(cupo) if cupo else None, dia_pago=dia_pago))


def listar(usuario_id: int) -> list[Cuenta]:
    """En el orden en que se crearon."""
    # TODO(backend): SELECT ... WHERE usuario_id = :usuario_id ORDER BY id.
    if usuario_id == DEMO_USUARIO_ID:
        _crear_demo()
    return [c for dueno, c in _cuentas.values() if dueno == usuario_id]


def obtener(usuario_id: int, id: int) -> Cuenta | None:
    return next((c for c in listar(usuario_id) if c.id == id), None)


def ref_plantilla(nombre: str) -> CuentaRef | None:
    """La cuenta demo que usa una fila de la plantilla de movimientos, con su nombre actual.
    None si la persona la eliminó: esa fila no se siembra."""
    cuenta = obtener(DEMO_USUARIO_ID, _PLANTILLA[nombre])
    return ref(cuenta) if cuenta else None


def proxima_fecha_pago(dia_pago: int, hoy: date) -> date:
    """La próxima vez que llega dia_pago (hoy cuenta). En meses más cortos, su último día."""
    def en_mes(anio: int, mes: int) -> date:
        return date(anio, mes, min(dia_pago, monthrange(anio, mes)[1]))

    fecha = en_mes(hoy.year, hoy.month)
    if fecha >= hoy:
        return fecha
    return en_mes(hoy.year + 1, 1) if hoy.month == 12 else en_mes(hoy.year, hoy.month + 1)


# ---------- Saldos ----------

def _efecto(c: Cuenta, m: Movimiento) -> Decimal:
    """Cuánto cambia un movimiento el saldo (dinero) o la deuda (tarjeta) de la cuenta c."""
    suma = m.monto if m.tipo == "ingreso" else -m.monto
    return -suma if es_tarjeta(c.tipo) else suma


def _saldos(usuario_id: int, lista: list[Cuenta]) -> dict[int, Decimal]:
    from app.services import movimientos
    if not lista:
        return {}
    movs = movimientos.desde(usuario_id, min(c.creada_en for c in lista))
    saldos = {c.id: c.inicial for c in lista}
    por_id = {c.id: c for c in lista}
    for m in movs:
        c = por_id.get(m.cuenta.id)
        if c and m.fecha >= c.creada_en:
            saldos[c.id] += _efecto(c, m)
    return saldos


def _usos(usuario_id: int, c: Cuenta) -> int:
    from app.services import movimientos
    movimientos.desde(usuario_id, c.creada_en)  # siembra los meses que importan antes de contar
    return movimientos.usos_por_cuenta(usuario_id).get(c.id, 0)


def panel(usuario_id: int) -> PanelCuentas:
    from app.services import movimientos
    lista = listar(usuario_id)
    saldos = _saldos(usuario_id, lista)
    usos = movimientos.usos_por_cuenta(usuario_id)  # _saldos ya sembró desde la cuenta más vieja
    hoy = _hoy()
    dinero, tarjetas = [], []
    for c in lista:
        saldo = saldos[c.id]
        if es_tarjeta(c.tipo):
            fecha = proxima_fecha_pago(c.dia_pago, hoy)
            tarjetas.append(CuentaConSaldo(cuenta=c, saldo=saldo, disponible=c.cupo - saldo, fecha_limite=fecha,
                                           dias_para_pagar=(fecha - hoy).days, usos=usos.get(c.id, 0)))
        else:
            dinero.append(CuentaConSaldo(cuenta=c, saldo=saldo, disponible=None, fecha_limite=None,
                                         dias_para_pagar=None, usos=usos.get(c.id, 0)))
    tarjetas.sort(key=lambda t: (t.fecha_limite, t.cuenta.nombre))
    tienes = sum((c.saldo for c in dinero), Decimal(0))
    debes = sum((t.saldo for t in tarjetas), Decimal(0))
    return PanelCuentas(dinero=dinero, tarjetas=tarjetas, tienes=tienes, debes=debes, te_queda=tienes - debes)


# ---------- Crear, editar y eliminar ----------

def _validar(usuario_id: int, e: CuentaEntrada, actual: Cuenta | None) -> str:
    """Devuelve el nombre limpio o lanza ErrorValidacion."""
    from app.services.movimientos import MAX_MONTO
    errores: dict[str, str] = {}
    tarjeta = es_tarjeta(e.tipo)

    nombre = " ".join(e.nombre.split())
    if not nombre:
        errores["nombre"] = "Escribe un nombre."
    elif len(nombre) > MAX_NOMBRE:
        errores["nombre"] = f"Máximo {MAX_NOMBRE} caracteres."
    elif any(normalizar(c.nombre) == normalizar(nombre)
             for c in listar(usuario_id) if actual is None or c.id != actual.id):
        errores["nombre"] = "Ya tienes una cuenta con ese nombre."

    if not e.saldo.is_finite() or e.saldo < 0:
        errores["saldo"] = "Escribe una deuda de 0 o más." if tarjeta else "Escribe un saldo de 0 o más."
    elif e.saldo >= MAX_MONTO:
        errores["saldo"] = "El monto es demasiado grande."

    if tarjeta:
        if e.cupo is None or not e.cupo.is_finite() or e.cupo <= 0:
            errores["cupo"] = "Escribe un cupo mayor que 0."
        elif e.cupo >= MAX_MONTO:
            errores["cupo"] = "El monto es demasiado grande."
        if e.dia_pago is None or not 1 <= e.dia_pago <= 31:
            errores["dia_pago"] = "Elige un día entre 1 y 31."

    if actual is None and len(listar(usuario_id)) >= MAX_CUENTAS:
        errores["general"] = f"Llegaste al máximo de {MAX_CUENTAS} cuentas."
    if actual is not None and es_tarjeta(actual.tipo) != tarjeta and _usos(usuario_id, actual):
        errores["tipo"] = "Ya tiene movimientos: no puede pasar de dinero a tarjeta ni al revés."
    if errores:
        raise ErrorValidacion(errores)
    return nombre


def _datos(e: CuentaEntrada, nombre: str) -> dict:
    tarjeta = es_tarjeta(e.tipo)
    return {"nombre": nombre, "tipo": e.tipo, "icono": e.icono, "tono": e.tono,
            "cupo": e.cupo if tarjeta else None, "dia_pago": e.dia_pago if tarjeta else None}


def crear(usuario_id: int, e: CuentaEntrada) -> Cuenta:
    # TODO(backend): INSERT con usuario_id.
    global _siguiente_id
    nombre = _validar(usuario_id, e, None)
    cuenta = Cuenta(id=_siguiente_id, creada_en=_hoy(), inicial=e.saldo, **_datos(e, nombre))
    _siguiente_id += 1
    _cuentas[cuenta.id] = (usuario_id, cuenta)
    return cuenta


def actualizar(usuario_id: int, id: int, e: CuentaEntrada) -> Cuenta:
    # TODO(backend): UPDATE por id y usuario_id.
    from app.services import movimientos
    actual = obtener(usuario_id, id)
    if actual is None:
        raise NoEncontrado(id)
    nombre = _validar(usuario_id, e, actual)
    if es_tarjeta(actual.tipo) != es_tarjeta(e.tipo):
        inicial = e.saldo  # sin movimientos (lo validó _validar): el saldo de hoy es el punto de partida
    else:
        inicial = actual.inicial + e.saldo - _saldos(usuario_id, [actual])[id]
    cuenta = actual.model_copy(update=_datos(e, nombre) | {"inicial": inicial})
    _cuentas[id] = (usuario_id, cuenta)
    movimientos.cambiar_cuenta(usuario_id, id, ref(cuenta))  # los movimientos llevan el nombre
    return cuenta


def eliminar(usuario_id: int, id: int, mover_a: int | None = None) -> None:
    """Si la cuenta tiene movimientos, mover_a es la cuenta (del mismo grupo) que los recibe."""
    # TODO(backend): UPDATE de movimientos y DELETE, en una transacción.
    from app.services import movimientos
    cuenta = obtener(usuario_id, id)
    if cuenta is None:
        raise NoEncontrado(id)
    usos = _usos(usuario_id, cuenta)
    if usos:
        tarjeta = es_tarjeta(cuenta.tipo)
        otras = [c for c in listar(usuario_id) if c.id != id and es_tarjeta(c.tipo) == tarjeta]
        destino = obtener(usuario_id, mover_a) if mover_a is not None else None
        if not otras:
            unica = "tu única tarjeta" if tarjeta else "tu única cuenta de dinero"
            raise ErrorValidacion({"mover_a": f"Es {unica}. Crea otra para pasarle sus movimientos antes de eliminarla."})
        if mover_a is None:
            plural = "1 movimiento" if usos == 1 else f"{usos} movimientos"
            raise ErrorValidacion({"mover_a": f"Tiene {plural}. Elige a qué cuenta pasarlos."})
        if destino is None or destino.id == id:
            raise ErrorValidacion({"mover_a": "Elige otra cuenta."})
        if es_tarjeta(destino.tipo) != tarjeta:
            raise ErrorValidacion({"mover_a": "Elige una tarjeta." if tarjeta else "Elige una cuenta de dinero."})
        movimientos.cambiar_cuenta(usuario_id, id, ref(destino))
    del _cuentas[id]
