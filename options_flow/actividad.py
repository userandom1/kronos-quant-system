"""Cambios observados entre capturas, sin inferir órdenes ejecutadas."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from zoneinfo import ZoneInfo

from .capturas import CapturaValidada


@dataclass(frozen=True)
class ActividadContrato:
    id_contrato: str
    vencimiento: str
    tipo: str
    strike: Decimal
    volumen_anterior: int | None
    volumen_actual: int | None
    incremento_volumen_estimado: int | None
    cambio_oi_reportado: int | None
    cambio_iv: Decimal | None
    prima_mid_estimativa: Decimal | None
    estado_volumen: str


@dataclass(frozen=True)
class ComparacionCapturas:
    id_anterior: str
    id_actual: str
    misma_fecha_mercado: bool
    contratos: tuple[ActividadContrato, ...]
    contratos_desaparecidos: tuple[str, ...]
    tipo_dato: str = "COMPARACION_DE_CAPTURAS_NO_OPERACIONES"


@dataclass(frozen=True)
class ActividadAgregada:
    vencimiento: str
    tipo: str
    strike: Decimal | None
    contratos_actuales: int
    contratos_comparables: int
    incremento_volumen_estimado: int | None
    prima_mid_estimativa: Decimal | None


def comparar_capturas(
    anterior: CapturaValidada, actual: CapturaValidada
) -> ComparacionCapturas:
    """Compara volumen acumulado solo en el mismo día local y con base válida."""
    a, b = anterior.metadatos, actual.metadatos
    if (
        a.subyacente != b.subyacente
        or a.proveedor != b.proveedor
        or a.divisa != b.divisa
        or a.zona_mercado != b.zona_mercado
    ):
        raise ValueError("capturas_incompatibles")
    if b.capturado_en_utc <= a.capturado_en_utc:
        raise ValueError("capturas_fuera_de_orden")
    if a.id_captura == b.id_captura:
        raise ValueError("id_captura_repetido")
    zona = ZoneInfo(a.zona_mercado)
    misma_fecha = (
        a.capturado_en_utc.astimezone(zona).date()
        == b.capturado_en_utc.astimezone(zona).date()
    )
    previos = {contrato.id_contrato: contrato for contrato in anterior.contratos}
    actuales = {contrato.id_contrato: contrato for contrato in actual.contratos}
    if len(previos) != len(anterior.contratos) or len(actuales) != len(actual.contratos):
        raise ValueError("ids_contrato_no_unicos")

    filas: list[ActividadContrato] = []
    for contrato in sorted(actual.contratos, key=lambda c: c.id_contrato):
        previo = previos.get(contrato.id_contrato)
        compatible = previo is not None and (
            previo.id_proveedor == contrato.id_proveedor
            and previo.tipo == contrato.tipo
            and previo.strike == contrato.strike
            and previo.vencimiento == contrato.vencimiento
            and previo.multiplicador == contrato.multiplicador
        )
        if previo is None:
            estado = "SIN_BASE_ANTERIOR"
        elif not compatible:
            estado = "CONTRATO_CAMBIADO"
        elif not misma_fecha:
            estado = "DIA_MERCADO_DISTINTO"
        elif previo.volumen is None or contrato.volumen is None:
            estado = "VOLUMEN_AUSENTE"
        elif contrato.volumen < previo.volumen:
            estado = "VOLUMEN_RETROCEDE"
        else:
            estado = "COMPARABLE"
        incremento = (
            contrato.volumen - previo.volumen if estado == "COMPARABLE" else None
        )
        cambio_oi = (
            contrato.open_interest - previo.open_interest
            if compatible and contrato.open_interest is not None
            and previo.open_interest is not None else None
        )
        cambio_iv = contrato.iv - previo.iv if compatible else None
        prima = (
            (contrato.bid + contrato.ask) / 2 * incremento * contrato.multiplicador
            if incremento is not None else None
        )
        filas.append(ActividadContrato(
            id_contrato=contrato.id_contrato,
            vencimiento=contrato.vencimiento.isoformat(),
            tipo=contrato.tipo,
            strike=contrato.strike,
            volumen_anterior=previo.volumen if previo is not None else None,
            volumen_actual=contrato.volumen,
            incremento_volumen_estimado=incremento,
            cambio_oi_reportado=cambio_oi,
            cambio_iv=cambio_iv,
            prima_mid_estimativa=prima,
            estado_volumen=estado,
        ))
    return ComparacionCapturas(
        id_anterior=a.id_captura,
        id_actual=b.id_captura,
        misma_fecha_mercado=misma_fecha,
        contratos=tuple(filas),
        contratos_desaparecidos=tuple(sorted(set(previos) - set(actuales))),
    )


def agregar_actividad(
    comparacion: ComparacionCapturas, *, por_strike: bool
) -> tuple[ActividadAgregada, ...]:
    """Resume cobertura y actividad por tipo y vencimiento, sin signo de orden."""
    grupos: dict[tuple[str, str, Decimal | None], list[ActividadContrato]] = {}
    for fila in comparacion.contratos:
        clave = (fila.vencimiento, fila.tipo, fila.strike if por_strike else None)
        grupos.setdefault(clave, []).append(fila)
    salida: list[ActividadAgregada] = []
    for (vencimiento, tipo, strike), filas in sorted(grupos.items()):
        comparables = [
            fila for fila in filas if fila.incremento_volumen_estimado is not None
        ]
        salida.append(ActividadAgregada(
            vencimiento=vencimiento,
            tipo=tipo,
            strike=strike,
            contratos_actuales=len(filas),
            contratos_comparables=len(comparables),
            incremento_volumen_estimado=sum(
                fila.incremento_volumen_estimado for fila in comparables
            ) if comparables else None,
            prima_mid_estimativa=sum(
                (fila.prima_mid_estimativa for fila in comparables), Decimal(0)
            ) if comparables else None,
        ))
    return tuple(salida)
