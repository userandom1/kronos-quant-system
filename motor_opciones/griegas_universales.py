from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import norm


DIAS_ANO = 365.0


def calcular_delta(
    spot: float,
    strike: np.ndarray,
    tiempo: np.ndarray,
    volatilidad: np.ndarray,
    tipo: np.ndarray,
    tipo_interes: float,
    dividendo: float,
) -> np.ndarray:
    """Calcula Delta Black-Scholes."""

    raiz_t = np.sqrt(tiempo)

    d1 = (
        np.log(spot / strike)
        + (
            tipo_interes
            - dividendo
            + 0.5 * volatilidad**2
        )
        * tiempo
    ) / (
        volatilidad
        * raiz_t
    )

    descuento_dividendo = np.exp(
        -dividendo * tiempo
    )

    delta_call = (
        descuento_dividendo
        * norm.cdf(d1)
    )

    delta_put = (
        descuento_dividendo
        * (
            norm.cdf(d1)
            - 1.0
        )
    )

    return np.where(
        tipo == "CALL",
        delta_call,
        delta_put,
    )


def aplicar_griegas(
    cadena: pd.DataFrame,
    spot: float,
    tipo_interes: float = 0.04,
    dividendo: float = 0.01,
) -> pd.DataFrame:
    """Calcula Greeks universales sobre una cadena."""

    resultado = cadena.copy()

    resultado["strike"] = pd.to_numeric(
        resultado["strike"],
        errors="coerce",
    )

    resultado["iv"] = pd.to_numeric(
        resultado["iv"],
        errors="coerce",
    )

    resultado["dte"] = pd.to_numeric(
        resultado["dte"],
        errors="coerce",
    )

    resultado = resultado[
        (resultado["strike"] > 0)
        & (resultado["iv"] > 0)
        & (resultado["dte"] >= 0)
    ].copy()

    strike = resultado[
        "strike"
    ].to_numpy(
        dtype=float
    )

    volatilidad = resultado[
        "iv"
    ].to_numpy(
        dtype=float
    )

    tiempo = np.maximum(
        resultado[
            "dte"
        ].to_numpy(
            dtype=float
        )
        / DIAS_ANO,
        1.0 / DIAS_ANO,
    )

    tipo = resultado[
        "tipo_opcion"
    ].astype(str).str.upper().to_numpy()

    raiz_t = np.sqrt(
        tiempo
    )

    d1 = (
        np.log(
            spot / strike
        )
        + (
            tipo_interes
            - dividendo
            + 0.5
            * volatilidad**2
        )
        * tiempo
    ) / (
        volatilidad
        * raiz_t
    )

    d2 = (
        d1
        - volatilidad
        * raiz_t
    )

    descuento_r = np.exp(
        -tipo_interes
        * tiempo
    )

    descuento_q = np.exp(
        -dividendo
        * tiempo
    )

    pdf_d1 = norm.pdf(
        d1
    )

    delta = calcular_delta(
        spot=spot,
        strike=strike,
        tiempo=tiempo,
        volatilidad=volatilidad,
        tipo=tipo,
        tipo_interes=tipo_interes,
        dividendo=dividendo,
    )

    gamma = (
        descuento_q
        * pdf_d1
        / (
            spot
            * volatilidad
            * raiz_t
        )
    )

    # Vega expresada para un cambio de 1 punto de IV.
    vega_1pt = (
        spot
        * descuento_q
        * pdf_d1
        * raiz_t
        / 100.0
    )

    theta_call = (
        -spot
        * descuento_q
        * pdf_d1
        * volatilidad
        / (
            2.0
            * raiz_t
        )
        - tipo_interes
        * strike
        * descuento_r
        * norm.cdf(d2)
        + dividendo
        * spot
        * descuento_q
        * norm.cdf(d1)
    )

    theta_put = (
        -spot
        * descuento_q
        * pdf_d1
        * volatilidad
        / (
            2.0
            * raiz_t
        )
        + tipo_interes
        * strike
        * descuento_r
        * norm.cdf(-d2)
        - dividendo
        * spot
        * descuento_q
        * norm.cdf(-d1)
    )

    theta_dia = (
        np.where(
            tipo == "CALL",
            theta_call,
            theta_put,
        )
        / DIAS_ANO
    )

    # Vanna aproximada mediante shock central de +/-1 punto de IV.
    shock_iv = 0.01

    vol_mas = (
        volatilidad
        + shock_iv
    )

    vol_menos = np.maximum(
        volatilidad
        - shock_iv,
        0.0001,
    )

    delta_vol_mas = calcular_delta(
        spot,
        strike,
        tiempo,
        vol_mas,
        tipo,
        tipo_interes,
        dividendo,
    )

    delta_vol_menos = calcular_delta(
        spot,
        strike,
        tiempo,
        vol_menos,
        tipo,
        tipo_interes,
        dividendo,
    )

    vanna_1pt = (
        delta_vol_mas
        - delta_vol_menos
    ) / 2.0

    # Charm: cambio estimado de Delta tras un día.
    tiempo_manana = np.maximum(
        tiempo
        - 1.0 / DIAS_ANO,
        1.0 / (
            DIAS_ANO
            * 24.0
        ),
    )

    delta_manana = calcular_delta(
        spot,
        strike,
        tiempo_manana,
        volatilidad,
        tipo,
        tipo_interes,
        dividendo,
    )

    charm_dia = (
        delta_manana
        - delta
    )

    resultado[
        "delta"
    ] = delta

    resultado[
        "gamma"
    ] = gamma

    resultado[
        "theta_dia"
    ] = theta_dia

    resultado[
        "vega_1pt"
    ] = vega_1pt

    resultado[
        "vanna_1pt"
    ] = vanna_1pt

    resultado[
        "charm_dia"
    ] = charm_dia

    return resultado