from __future__ import annotations

import numpy as np
import pandas as pd


SESIONES_ANUALES = 252


def retorno_periodo(
    precios: pd.Series,
    sesiones: int,
) -> float:
    """Calcula el retorno simple de un periodo."""

    if len(precios) <= sesiones:
        return np.nan

    return float(
        precios.iloc[-1]
        / precios.iloc[-1 - sesiones]
        - 1.0
    )


def volatilidad_anualizada(
    retornos: pd.Series,
    ventana: int,
) -> float:
    """Calcula la volatilidad anualizada."""

    muestra = retornos.dropna().tail(
        ventana
    )

    if len(muestra) < 2:
        return np.nan

    return float(
        muestra.std(ddof=1)
        * np.sqrt(
            SESIONES_ANUALES
        )
    )


def sharpe_anualizado(
    retornos: pd.Series,
    ventana: int,
) -> float:
    """Calcula Sharpe anualizado con rf igual a cero."""

    muestra = retornos.dropna().tail(
        ventana
    )

    if len(muestra) < 2:
        return np.nan

    desviacion = muestra.std(
        ddof=1
    )

    if (
        not np.isfinite(
            desviacion
        )
        or desviacion <= 0
    ):
        return np.nan

    return float(
        muestra.mean()
        / desviacion
        * np.sqrt(
            SESIONES_ANUALES
        )
    )


def drawdown_actual(
    precios: pd.Series,
) -> float:
    """Calcula el drawdown actual."""

    maximos = precios.cummax()

    drawdown = (
        precios
        / maximos
        - 1.0
    )

    return float(
        drawdown.iloc[-1]
    )


def beta_correlacion(
    retornos_activo: pd.Series,
    retornos_benchmark: pd.Series,
    ventana: int = 60,
) -> tuple[float, float]:
    """Calcula beta y correlación."""

    datos = pd.concat(
        [
            retornos_activo.rename(
                "activo"
            ),
            retornos_benchmark.rename(
                "benchmark"
            ),
        ],
        axis=1,
    ).dropna()

    datos = datos.tail(
        ventana
    )

    if len(datos) < 2:
        return np.nan, np.nan

    var_benchmark = datos[
        "benchmark"
    ].var(
        ddof=1
    )

    if (
        not np.isfinite(
            var_benchmark
        )
        or var_benchmark <= 0
    ):
        beta = np.nan

    else:
        covarianza = datos[
            [
                "activo",
                "benchmark",
            ]
        ].cov().iloc[
            0,
            1
        ]

        beta = float(
            covarianza
            / var_benchmark
        )

    correlacion = float(
        datos[
            "activo"
        ].corr(
            datos[
                "benchmark"
            ]
        )
    )

    return beta, correlacion


def clasificar_tendencia(
    precio: float,
    ma20: float,
    ma50: float,
    ma200: float,
) -> str:
    """Clasifica el régimen de tendencia."""

    if (
        precio > ma20
        and ma20 > ma50
        and ma50 > ma200
    ):
        return "ALCISTA_FUERTE"

    if (
        precio > ma50
        and precio > ma200
    ):
        return "ALCISTA"

    if (
        precio < ma20
        and ma20 < ma50
        and ma50 < ma200
    ):
        return "BAJISTA_FUERTE"

    if (
        precio < ma50
        and precio < ma200
    ):
        return "BAJISTA"

    return "MIXTO"


def clasificar_momentum(
    retorno_20d: float,
    retorno_60d: float,
) -> str:
    """Clasifica el momentum."""

    if (
        retorno_20d > 0
        and retorno_60d > 0
    ):
        return "POSITIVO"

    if (
        retorno_20d < 0
        and retorno_60d < 0
    ):
        return "NEGATIVO"

    return "MIXTO"


def clasificar_volatilidad(
    vol20: float,
    vol60: float,
) -> str:
    """Clasifica el régimen de volatilidad."""

    if (
        not np.isfinite(vol20)
        or not np.isfinite(vol60)
        or vol60 <= 0
    ):
        return "DESCONOCIDO"

    ratio = vol20 / vol60

    if ratio >= 1.25:
        return "EXPANSION"

    if ratio <= 0.80:
        return "CONTRACCION"

    return "NORMAL"