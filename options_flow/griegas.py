"""Delta y Gamma Black-Scholes-Merton por contrato validado."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from .capturas import CapturaValidada, Contrato


SEGUNDOS_ANO = 365.0 * 24.0 * 60.0 * 60.0


@dataclass(frozen=True)
class SupuestosGriegas:
    tasa_anual: float
    dividendo_anual: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.tasa_anual) or not math.isfinite(self.dividendo_anual):
            raise ValueError("tasa_y_dividendo_deben_ser_finitos")


@dataclass(frozen=True)
class ResultadoGriegas:
    id_captura: str
    id_contrato: str
    tipo: str
    vencimiento: str
    spot: float
    strike: float
    volatilidad: float
    multiplicador: int
    tasa_anual: float
    dividendo_anual: float
    delta: float
    gamma: float
    tiempo_anos: float
    precision_tiempo: str
    modelo: str = "BLACK_SCHOLES_MERTON_EUROPEO"


@dataclass(frozen=True)
class OmitidoGriegas:
    id_contrato: str
    motivo: str


def tiempo_hasta_vencimiento(
    contrato: Contrato, captura_utc: datetime, zona_mercado: str
) -> tuple[float, str]:
    """Usa hora exacta si existe; para fechas futuras, días de mercado."""
    impedimento = contrato.impedimento_griegas(captura_utc, zona_mercado)
    if impedimento is not None:
        raise ValueError(impedimento)
    if contrato.expiracion_utc is not None:
        segundos = (contrato.expiracion_utc - captura_utc).total_seconds()
        return segundos / SEGUNDOS_ANO, "HORA_EXACTA"
    fecha_captura = captura_utc.astimezone(ZoneInfo(zona_mercado)).date()
    dias = (contrato.vencimiento - fecha_captura).days
    return dias / 365.0, "DIAS_CALENDARIO"


def delta_gamma(
    *, spot: float, strike: float, volatilidad: float, tiempo_anos: float,
    tipo: str, tasa_anual: float, dividendo_anual: float,
) -> tuple[float, float]:
    """Devuelve Delta por unidad y Gamma por unidad de precio del subyacente."""
    valores = (spot, strike, volatilidad, tiempo_anos, tasa_anual, dividendo_anual)
    if not all(math.isfinite(x) for x in valores):
        raise ValueError("parametros_no_finitos")
    if spot <= 0 or strike <= 0 or volatilidad <= 0 or tiempo_anos <= 0:
        raise ValueError("parametros_no_positivos")
    if tipo not in {"CALL", "PUT"}:
        raise ValueError("tipo_invalido")
    raiz = math.sqrt(tiempo_anos)
    d1 = (math.log(spot / strike) + (
        tasa_anual - dividendo_anual + 0.5 * volatilidad**2
    ) * tiempo_anos) / (volatilidad * raiz)
    cdf = 0.5 * math.erfc(-d1 / math.sqrt(2.0))
    pdf = math.exp(-0.5 * d1**2) / math.sqrt(2.0 * math.pi)
    descuento = math.exp(-dividendo_anual * tiempo_anos)
    delta = descuento * (cdf if tipo == "CALL" else cdf - 1.0)
    gamma = descuento * pdf / (spot * volatilidad * raiz)
    if not math.isfinite(delta) or not math.isfinite(gamma):
        raise ValueError("resultado_no_finito")
    return delta, gamma


def calcular_griegas_captura(
    captura: CapturaValidada, supuestos: SupuestosGriegas
) -> tuple[tuple[ResultadoGriegas, ...], tuple[OmitidoGriegas, ...]]:
    """Calcula por contrato sin convertir rechazos de calidad en observaciones."""
    resultados: list[ResultadoGriegas] = []
    omitidos: list[OmitidoGriegas] = []
    for contrato in captura.contratos:
        try:
            tiempo, precision = tiempo_hasta_vencimiento(
                contrato, captura.metadatos.capturado_en_utc,
                captura.metadatos.zona_mercado,
            )
            delta, gamma = delta_gamma(
                spot=float(captura.metadatos.spot),
                strike=float(contrato.strike),
                volatilidad=float(contrato.iv),
                tiempo_anos=tiempo,
                tipo=contrato.tipo,
                tasa_anual=supuestos.tasa_anual,
                dividendo_anual=supuestos.dividendo_anual,
            )
        except (OverflowError, ValueError) as error:
            omitidos.append(OmitidoGriegas(contrato.id_contrato, str(error)))
            continue
        resultados.append(ResultadoGriegas(
            id_captura=captura.metadatos.id_captura,
            id_contrato=contrato.id_contrato,
            tipo=contrato.tipo,
            vencimiento=contrato.vencimiento.isoformat(),
            spot=float(captura.metadatos.spot),
            strike=float(contrato.strike),
            volatilidad=float(contrato.iv),
            multiplicador=contrato.multiplicador,
            tasa_anual=supuestos.tasa_anual,
            dividendo_anual=supuestos.dividendo_anual,
            delta=delta,
            gamma=gamma,
            tiempo_anos=tiempo,
            precision_tiempo=precision,
        ))
    return tuple(resultados), tuple(omitidos)
