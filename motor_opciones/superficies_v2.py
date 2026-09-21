from dataclasses import dataclass
from math import exp, log

import numpy as np
import pandas as pd

from motor_opciones.griegas import (
    ParametrosOpcion,
    delta,
    delta_decay_por_dia,
    gamma,
    theta_por_dia,
    vanna_por_punto,
    vega_por_punto,
)


# =============================================================================
# DEFINICIÓN DE GREEKS
# =============================================================================

FUNCIONES_GRIEGAS = {
    "delta": delta,
    "gamma": gamma,
    "theta": theta_por_dia,
    "vega": vega_por_punto,
    "vanna": vanna_por_punto,
    "delta_decay": delta_decay_por_dia,
}


NOMBRES_GRIEGAS = {
    "delta": "Delta",
    "gamma": "Gamma",
    "theta": "Theta diario",
    "vega": "Vega por punto de IV",
    "vanna": "Vanna por punto de IV",
    "delta_decay": "Delta Decay diario",
}


# =============================================================================
# CONFIGURACIÓN GENERAL
# =============================================================================


@dataclass(frozen=True)
class ConfiguracionMercado:
    """Parámetros comunes del laboratorio de Greeks."""

    spot: float = 100.0
    tipo_interes: float = 0.04
    dividendo: float = 0.01
    volatilidad_base: float = 0.20

    volatilidades: tuple[float, ...] = (
        0.10,
        0.20,
        0.30,
        0.50,
        0.80,
    )


@dataclass(frozen=True)
class PerfilGriega:
    """Rango de estudio específico para cada Greek."""

    moneyness_min: float
    moneyness_max: float
    puntos_moneyness: int
    dte: tuple[float, ...]
    dte_cortes: tuple[float, ...]
    dte_comparacion_iv: float


# =============================================================================
# DTE NO LINEAL
# =============================================================================


DTE_CORTO = (
    0.25,
    0.50,
    1.0,
    2.0,
    3.0,
    5.0,
    7.0,
    10.0,
    14.0,
    21.0,
    30.0,
    45.0,
    60.0,
)

DTE_MEDIO = DTE_CORTO + (
    90.0,
    120.0,
    180.0,
    270.0,
    365.0,
)

DTE_LARGO = (
    1.0,
    2.0,
    3.0,
    5.0,
    7.0,
    10.0,
    14.0,
    21.0,
    30.0,
    45.0,
    60.0,
    90.0,
    120.0,
    180.0,
    270.0,
    365.0,
    540.0,
    730.0,
)


PERFILES_GRIEGAS = {
    "delta": PerfilGriega(
        moneyness_min=0.60,
        moneyness_max=1.40,
        puntos_moneyness=161,
        dte=DTE_MEDIO,
        dte_cortes=(
            1.0,
            7.0,
            30.0,
            90.0,
            365.0,
        ),
        dte_comparacion_iv=30.0,
    ),
    "gamma": PerfilGriega(
        moneyness_min=0.90,
        moneyness_max=1.10,
        puntos_moneyness=161,
        dte=DTE_CORTO,
        dte_cortes=(
            0.25,
            1.0,
            3.0,
            7.0,
            30.0,
            60.0,
        ),
        dte_comparacion_iv=7.0,
    ),
    "theta": PerfilGriega(
        moneyness_min=0.80,
        moneyness_max=1.20,
        puntos_moneyness=161,
        dte=DTE_CORTO + (90.0,),
        dte_cortes=(
            0.25,
            1.0,
            7.0,
            30.0,
            90.0,
        ),
        dte_comparacion_iv=7.0,
    ),
    "vega": PerfilGriega(
        moneyness_min=0.70,
        moneyness_max=1.30,
        puntos_moneyness=161,
        dte=DTE_LARGO,
        dte_cortes=(
            7.0,
            30.0,
            90.0,
            365.0,
            730.0,
        ),
        dte_comparacion_iv=90.0,
    ),
    "vanna": PerfilGriega(
        moneyness_min=0.75,
        moneyness_max=1.25,
        puntos_moneyness=161,
        dte=DTE_MEDIO,
        dte_cortes=(
            1.0,
            7.0,
            30.0,
            90.0,
            365.0,
        ),
        dte_comparacion_iv=30.0,
    ),
    "delta_decay": PerfilGriega(
        moneyness_min=0.85,
        moneyness_max=1.15,
        puntos_moneyness=161,
        dte=DTE_CORTO,
        dte_cortes=(
            0.25,
            1.0,
            3.0,
            7.0,
            30.0,
            60.0,
        ),
        dte_comparacion_iv=7.0,
    ),
}


# =============================================================================
# EJES
# =============================================================================


def crear_log_moneyness(
    perfil: PerfilGriega,
) -> np.ndarray:
    """
    Crea un eje uniforme de log-moneyness.

    log-moneyness = ln(K / S)
    ATM = 0.
    """

    minimo = log(
        perfil.moneyness_min
    )

    maximo = log(
        perfil.moneyness_max
    )

    return np.linspace(
        minimo,
        maximo,
        perfil.puntos_moneyness,
    )


# =============================================================================
# CÁLCULO INDIVIDUAL
# =============================================================================


def calcular_valor_griega(
    nombre_griega: str,
    tipo_opcion: str,
    log_moneyness: float,
    dte: float,
    volatilidad: float,
    mercado: ConfiguracionMercado,
) -> float:
    """Calcula una Greek para un único punto del espacio."""

    if nombre_griega not in FUNCIONES_GRIEGAS:
        raise ValueError(
            f"Greek no soportada: {nombre_griega}"
        )

    if tipo_opcion not in {
        "call",
        "put",
    }:
        raise ValueError(
            "El tipo de opción debe ser 'call' o 'put'."
        )

    ratio = exp(
        log_moneyness
    )

    strike = (
        mercado.spot
        * ratio
    )

    parametros = ParametrosOpcion(
        spot=mercado.spot,
        strike=strike,
        tiempo=dte / 365.0,
        volatilidad=volatilidad,
        tipo_interes=mercado.tipo_interes,
        dividendo=mercado.dividendo,
        tipo=tipo_opcion,
    )

    funcion = FUNCIONES_GRIEGAS[
        nombre_griega
    ]

    return float(
        funcion(
            parametros
        )
    )


# =============================================================================
# SUPERFICIE
# =============================================================================


def calcular_superficie(
    nombre_griega: str,
    tipo_opcion: str,
    mercado: ConfiguracionMercado,
    volatilidad: float | None = None,
) -> pd.DataFrame:
    """Calcula la superficie completa log-moneyness x DTE."""

    perfil = PERFILES_GRIEGAS[
        nombre_griega
    ]

    iv = (
        mercado.volatilidad_base
        if volatilidad is None
        else volatilidad
    )

    eje_log_moneyness = (
        crear_log_moneyness(
            perfil
        )
    )

    filas: list[dict] = []

    for dte in perfil.dte:
        for log_m in eje_log_moneyness:
            ratio = exp(
                float(log_m)
            )

            valor = calcular_valor_griega(
                nombre_griega=nombre_griega,
                tipo_opcion=tipo_opcion,
                log_moneyness=float(log_m),
                dte=float(dte),
                volatilidad=float(iv),
                mercado=mercado,
            )

            filas.append(
                {
                    "tipo_opcion": tipo_opcion,
                    "griega": nombre_griega,
                    "volatilidad": iv,
                    "log_moneyness": float(
                        log_m
                    ),
                    "moneyness": ratio,
                    "strike": (
                        mercado.spot
                        * ratio
                    ),
                    "dte": float(
                        dte
                    ),
                    "valor": valor,
                }
            )

    return pd.DataFrame(
        filas
    )


# =============================================================================
# CORTE POR DTE
# =============================================================================


def calcular_cortes_dte(
    nombre_griega: str,
    tipo_opcion: str,
    mercado: ConfiguracionMercado,
) -> pd.DataFrame:
    """Calcula curvas Greek vs log-moneyness para varios DTE."""

    perfil = PERFILES_GRIEGAS[
        nombre_griega
    ]

    eje_log_moneyness = crear_log_moneyness(
        perfil
    )

    filas: list[dict] = []

    for dte in perfil.dte_cortes:
        for log_m in eje_log_moneyness:
            valor = calcular_valor_griega(
                nombre_griega,
                tipo_opcion,
                float(log_m),
                dte,
                mercado.volatilidad_base,
                mercado,
            )

            filas.append(
                {
                    "dte": dte,
                    "log_moneyness": float(
                        log_m
                    ),
                    "moneyness": exp(
                        float(log_m)
                    ),
                    "valor": valor,
                }
            )

    return pd.DataFrame(
        filas
    )


# =============================================================================
# ATM VS DTE PARA VARIOS REGÍMENES DE IV
# =============================================================================


def calcular_atm_por_dte_e_iv(
    nombre_griega: str,
    tipo_opcion: str,
    mercado: ConfiguracionMercado,
) -> pd.DataFrame:
    """Calcula la Greek ATM para cada DTE y régimen de IV."""

    perfil = PERFILES_GRIEGAS[
        nombre_griega
    ]

    filas: list[dict] = []

    for volatilidad in mercado.volatilidades:
        for dte in perfil.dte:
            valor = calcular_valor_griega(
                nombre_griega,
                tipo_opcion,
                0.0,
                dte,
                volatilidad,
                mercado,
            )

            filas.append(
                {
                    "volatilidad": volatilidad,
                    "dte": dte,
                    "valor": valor,
                }
            )

    return pd.DataFrame(
        filas
    )


# =============================================================================
# COMPARACIÓN DE IV EN UN DTE FIJO
# =============================================================================


def calcular_comparacion_iv(
    nombre_griega: str,
    tipo_opcion: str,
    mercado: ConfiguracionMercado,
) -> pd.DataFrame:
    """
    Compara la forma de una Greek para diferentes IV
    manteniendo fijo el DTE.
    """

    perfil = PERFILES_GRIEGAS[
        nombre_griega
    ]

    eje_log_moneyness = crear_log_moneyness(
        perfil
    )

    dte = perfil.dte_comparacion_iv

    filas: list[dict] = []

    for volatilidad in mercado.volatilidades:
        for log_m in eje_log_moneyness:
            valor = calcular_valor_griega(
                nombre_griega,
                tipo_opcion,
                float(log_m),
                dte,
                volatilidad,
                mercado,
            )

            filas.append(
                {
                    "volatilidad": volatilidad,
                    "dte": dte,
                    "log_moneyness": float(
                        log_m
                    ),
                    "moneyness": exp(
                        float(log_m)
                    ),
                    "valor": valor,
                }
            )

    return pd.DataFrame(
        filas
    )