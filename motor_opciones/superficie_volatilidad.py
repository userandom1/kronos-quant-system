from dataclasses import dataclass
from math import exp

import numpy as np
import pandas as pd


# =============================================================================
# CONFIGURACIÓN
# =============================================================================


@dataclass(frozen=True)
class ConfiguracionVolatilidad:
    """Parámetros de la superficie de volatilidad implícita."""

    iv_atm_base: float = 0.20

    # Intensidad del skew de equity.
    skew_base: float = -0.35

    # Convexidad del smile.
    curvatura_base: float = 0.80

    # Límites de seguridad.
    iv_minima: float = 0.05
    iv_maxima: float = 1.50


# =============================================================================
# TERM STRUCTURE ATM
# =============================================================================


def iv_atm_por_dte(
    dte: float,
    configuracion: ConfiguracionVolatilidad,
) -> float:
    """
    Calcula la IV ATM en función del vencimiento.

    Esta primera versión utiliza una estructura paramétrica
    suave pensada para simular un mercado de equity/index.
    """

    if dte <= 0:
        raise ValueError(
            "DTE debe ser mayor que cero."
        )

    # Componente elevada de corto plazo.
    prima_corto_plazo = (
        0.06
        * exp(
            -dte / 15.0
        )
    )

    # Ligera elevación estructural en vencimientos largos.
    prima_largo_plazo = (
        0.025
        * (
            1.0
            - exp(
                -dte / 365.0
            )
        )
    )

    return (
        configuracion.iv_atm_base
        + prima_corto_plazo
        + prima_largo_plazo
    )


# =============================================================================
# SKEW
# =============================================================================


def skew_por_dte(
    dte: float,
    configuracion: ConfiguracionVolatilidad,
) -> float:
    """
    Calcula el skew según el vencimiento.

    El skew se hace más intenso en vencimientos cortos.
    """

    if dte <= 0:
        raise ValueError(
            "DTE debe ser mayor que cero."
        )

    factor_corto = (
        1.0
        + 0.80
        * exp(
            -dte / 30.0
        )
    )

    return (
        configuracion.skew_base
        * factor_corto
    )


# =============================================================================
# CURVATURA
# =============================================================================


def curvatura_por_dte(
    dte: float,
    configuracion: ConfiguracionVolatilidad,
) -> float:
    """
    Calcula la convexidad del smile según DTE.
    """

    if dte <= 0:
        raise ValueError(
            "DTE debe ser mayor que cero."
        )

    factor_corto = (
        1.0
        + 0.50
        * exp(
            -dte / 45.0
        )
    )

    return (
        configuracion.curvatura_base
        * factor_corto
    )


# =============================================================================
# SUPERFICIE IV
# =============================================================================


def volatilidad_implicita(
    log_moneyness: float,
    dte: float,
    configuracion: ConfiguracionVolatilidad,
) -> float:
    """
    Calcula IV como función de log-moneyness y DTE.

    IV(m, T) =
        IV_ATM(T)
        + skew(T) * m
        + curvatura(T) * m²
    """

    nivel_atm = iv_atm_por_dte(
        dte,
        configuracion,
    )

    skew = skew_por_dte(
        dte,
        configuracion,
    )

    curvatura = curvatura_por_dte(
        dte,
        configuracion,
    )

    iv = (
        nivel_atm
        + skew
        * log_moneyness
        + curvatura
        * log_moneyness**2
    )

    return float(
        np.clip(
            iv,
            configuracion.iv_minima,
            configuracion.iv_maxima,
        )
    )


# =============================================================================
# GENERACIÓN DE SUPERFICIE
# =============================================================================


def generar_superficie_volatilidad(
    configuracion: ConfiguracionVolatilidad,
    moneyness_min: float = 0.60,
    moneyness_max: float = 1.40,
    puntos_moneyness: int = 161,
    dtes: tuple[float, ...] = (
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
        90.0,
        120.0,
        180.0,
        270.0,
        365.0,
    ),
) -> pd.DataFrame:
    """Genera una superficie completa de IV."""

    log_min = np.log(
        moneyness_min
    )

    log_max = np.log(
        moneyness_max
    )

    eje_log_moneyness = np.linspace(
        log_min,
        log_max,
        puntos_moneyness,
    )

    filas: list[dict[str, float]] = []

    for dte in dtes:
        for log_m in eje_log_moneyness:
            moneyness = float(
                np.exp(
                    log_m
                )
            )

            iv = volatilidad_implicita(
                float(log_m),
                float(dte),
                configuracion,
            )

            filas.append(
                {
                    "dte": float(
                        dte
                    ),
                    "log_moneyness": float(
                        log_m
                    ),
                    "moneyness": moneyness,
                    "iv": iv,
                    "iv_pct": (
                        iv * 100.0
                    ),
                }
            )

    return pd.DataFrame(
        filas
    )


# =============================================================================
# RESUMEN ATM
# =============================================================================


def generar_term_structure_atm(
    configuracion: ConfiguracionVolatilidad,
    dtes: tuple[float, ...] = (
        0.25,
        0.50,
        1.0,
        2.0,
        3.0,
        5.0,
        7.0,
        14.0,
        30.0,
        60.0,
        90.0,
        180.0,
        365.0,
    ),
) -> pd.DataFrame:
    """Genera la term structure ATM."""

    filas = []

    for dte in dtes:
        iv = iv_atm_por_dte(
            dte,
            configuracion,
        )

        filas.append(
            {
                "dte": dte,
                "iv_atm": iv,
                "iv_atm_pct": (
                    iv * 100.0
                ),
            }
        )

    return pd.DataFrame(
        filas
    )