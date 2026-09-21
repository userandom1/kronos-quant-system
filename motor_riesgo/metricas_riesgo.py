from __future__ import annotations

import numpy as np
import pandas as pd


SESIONES_ANUALES = 252


def volatilidad_anual(
    retornos: pd.Series,
) -> float:
    """Calcula volatilidad anualizada."""

    return float(
        retornos.std(ddof=1)
        * np.sqrt(SESIONES_ANUALES)
    )


def downside_volatility(
    retornos: pd.Series,
) -> float:
    """Calcula volatilidad anualizada de retornos negativos."""

    negativos = retornos[
        retornos < 0
    ]

    if negativos.empty:
        return np.nan

    return float(
        negativos.std(ddof=1)
        * np.sqrt(SESIONES_ANUALES)
    )


def var_historico(
    retornos: pd.Series,
    confianza: float,
) -> float:
    """Calcula Value at Risk histórico diario."""

    cuantial = retornos.quantile(
        1.0 - confianza
    )

    return float(
        max(
            0.0,
            -cuantial,
        )
    )


def cvar_historico(
    retornos: pd.Series,
    confianza: float,
) -> float:
    """Calcula Expected Shortfall histórico diario."""

    limite = retornos.quantile(
        1.0 - confianza
    )

    cola = retornos[
        retornos <= limite
    ]

    if cola.empty:
        return np.nan

    return float(
        max(
            0.0,
            -cola.mean(),
        )
    )


def max_drawdown(
    retornos: pd.Series,
) -> float:
    """Calcula máximo drawdown histórico."""

    curva = (
        1.0
        + retornos
    ).cumprod()

    drawdown = (
        curva
        / curva.cummax()
        - 1.0
    )

    return float(
        drawdown.min()
    )


def beta(
    retornos: pd.Series,
    benchmark: pd.Series,
) -> float:
    """Calcula beta respecto al benchmark."""

    datos = pd.concat(
        [
            retornos.rename("portfolio"),
            benchmark.rename("benchmark"),
        ],
        axis=1,
    ).dropna()

    var_benchmark = datos[
        "benchmark"
    ].var(ddof=1)

    if var_benchmark == 0:
        return np.nan

    covarianza = datos[
        [
            "portfolio",
            "benchmark",
        ]
    ].cov().iloc[
        0,
        1,
    ]

    return float(
        covarianza
        / var_benchmark
    )


def concentracion_hhi(
    pesos: pd.Series,
) -> float:
    """Calcula índice Herfindahl-Hirschman de pesos."""

    return float(
        np.square(
            pesos
        ).sum()
    )


def numero_efectivo_activos(
    pesos: pd.Series,
) -> float:
    """Calcula número efectivo de activos."""

    hhi = concentracion_hhi(
        pesos
    )

    if hhi <= 0:
        return np.nan

    return float(
        1.0 / hhi
    )


def calcular_metricas_riesgo(
    retornos: pd.Series,
    pesos: pd.Series,
    benchmark: pd.Series,
) -> dict[str, float]:
    """Calcula las métricas principales de riesgo."""

    return {
        "volatilidad_anual": volatilidad_anual(
            retornos
        ),
        "downside_volatility": downside_volatility(
            retornos
        ),
        "var_95_1d": var_historico(
            retornos,
            0.95,
        ),
        "var_99_1d": var_historico(
            retornos,
            0.99,
        ),
        "cvar_95_1d": cvar_historico(
            retornos,
            0.95,
        ),
        "cvar_99_1d": cvar_historico(
            retornos,
            0.99,
        ),
        "max_drawdown": max_drawdown(
            retornos
        ),
        "beta_spy": beta(
            retornos,
            benchmark,
        ),
        "hhi_pesos": concentracion_hhi(
            pesos
        ),
        "numero_efectivo_activos": (
            numero_efectivo_activos(
                pesos
            )
        ),
    }