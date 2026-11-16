"""Agregados transparentes de Delta y Gamma por open interest informado."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from math import fsum

from .capturas import CapturaValidada
from .griegas import ResultadoGriegas


@dataclass(frozen=True)
class AgregadoGriegas:
    vencimiento: date
    tipo: str
    strike: float | None
    contratos_con_griegas: int
    contratos_con_oi: int
    oi_conocido: int | None
    delta_oi_unidades: float | None
    gamma_oi_unidades_por_precio: float | None
    supuesto: str = "CADA_CONTRATO_ABIERTO_LARGO"


@dataclass(frozen=True)
class EscenarioDealer:
    vencimiento: date
    strike: float | None
    contratos_con_griegas: int
    contratos_con_oi: int
    delta_oi_unidades: float | None
    gamma_oi_unidades_por_precio: float | None
    convencion: str = "HIPOTESIS_CALLS_CORTAS_PUTS_LARGAS"


def agregar_griegas(
    captura: CapturaValidada,
    griegas: tuple[ResultadoGriegas, ...],
    *,
    por_strike: bool,
) -> tuple[AgregadoGriegas, ...]:
    """Suma Greeks ponderados por OI; nunca infiere posiciones dealer."""
    por_id = {fila.id_contrato: fila for fila in captura.contratos}
    if len(por_id) != len(captura.contratos):
        raise ValueError("ids_contrato_no_unicos")
    grupos: dict[tuple[date, str, float | None], list[tuple[ResultadoGriegas, int | None]]] = {}
    usados: set[str] = set()
    for resultado in griegas:
        if resultado.id_contrato in usados:
            raise ValueError("griegas_duplicadas")
        usados.add(resultado.id_contrato)
        contrato = por_id.get(resultado.id_contrato)
        if contrato is None or resultado.id_captura != captura.metadatos.id_captura:
            raise ValueError("griegas_no_corresponden_a_captura")
        if (
            resultado.tipo != contrato.tipo
            or resultado.vencimiento != contrato.vencimiento.isoformat()
            or resultado.strike != float(contrato.strike)
            or resultado.multiplicador != contrato.multiplicador
        ):
            raise ValueError("griegas_no_corresponden_a_contrato")
        clave = (
            contrato.vencimiento,
            contrato.tipo,
            float(contrato.strike) if por_strike else None,
        )
        grupos.setdefault(clave, []).append((resultado, contrato.open_interest))

    salida: list[AgregadoGriegas] = []
    for (vencimiento, tipo, strike), filas in sorted(grupos.items()):
        con_oi = [(g, oi) for g, oi in filas if oi is not None]
        salida.append(AgregadoGriegas(
            vencimiento=vencimiento,
            tipo=tipo,
            strike=strike,
            contratos_con_griegas=len(filas),
            contratos_con_oi=len(con_oi),
            oi_conocido=sum(oi for _, oi in con_oi) if con_oi else None,
            delta_oi_unidades=fsum(
                g.delta * oi * g.multiplicador for g, oi in con_oi
            ) if con_oi else None,
            gamma_oi_unidades_por_precio=fsum(
                g.gamma * oi * g.multiplicador for g, oi in con_oi
            ) if con_oi else None,
        ))
    return tuple(salida)


def escenario_dealer(
    agregados: tuple[AgregadoGriegas, ...]
) -> tuple[EscenarioDealer, ...]:
    """Escenario optativo; no representa posiciones observadas de dealers."""
    grupos: dict[tuple[date, float | None], list[AgregadoGriegas]] = {}
    for fila in agregados:
        if fila.tipo not in {"CALL", "PUT"}:
            raise ValueError("tipo_invalido_para_escenario")
        grupos.setdefault((fila.vencimiento, fila.strike), []).append(fila)
    salida: list[EscenarioDealer] = []
    for (vencimiento, strike), filas in sorted(grupos.items()):
        conocidas = [f for f in filas if f.contratos_con_oi]
        salida.append(EscenarioDealer(
            vencimiento=vencimiento,
            strike=strike,
            contratos_con_griegas=sum(f.contratos_con_griegas for f in filas),
            contratos_con_oi=sum(f.contratos_con_oi for f in filas),
            delta_oi_unidades=fsum(
                (-1 if f.tipo == "CALL" else 1) * f.delta_oi_unidades
                for f in conocidas
            ) if conocidas else None,
            gamma_oi_unidades_por_precio=fsum(
                (-1 if f.tipo == "CALL" else 1) * f.gamma_oi_unidades_por_precio
                for f in conocidas
            ) if conocidas else None,
        ))
    return tuple(salida)
