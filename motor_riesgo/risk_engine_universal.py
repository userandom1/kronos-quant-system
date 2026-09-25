from __future__ import annotations

import numpy as np
import pandas as pd


def retornos_portfolio(
    retornos: pd.DataFrame,
    pesos: pd.Series,
) -> pd.Series:
    """Calcula retornos históricos del portfolio."""

    pesos = pesos.reindex(
        retornos.columns
    ).fillna(
        0.0
    )

    return (
        retornos
        @ pesos
    ).rename(
        "portfolio"
    )


def volatilidad_anual(
    retornos: pd.Series,
    factor_anual: int,
) -> float:
    """Calcula volatilidad anualizada."""

    return float(
        retornos.std(
            ddof=1
        )
        * np.sqrt(
            factor_anual
        )
    )


def var_historico(
    retornos: pd.Series,
    confianza: float = 0.95,
) -> float:
    """Calcula VaR histórico diario."""

    cuantile = np.quantile(
        retornos,
        1.0 - confianza,
    )

    return float(
        -cuantile
    )


def cvar_historico(
    retornos: pd.Series,
    confianza: float = 0.95,
) -> float:
    """Calcula CVaR histórico diario."""

    limite = np.quantile(
        retornos,
        1.0 - confianza,
    )

    cola = retornos[
        retornos <= limite
    ]

    if cola.empty:
        return np.nan

    return float(
        -cola.mean()
    )


def max_drawdown(
    retornos: pd.Series,
) -> float:
    """Calcula máximo drawdown."""

    curva = (
        1.0
        + retornos
    ).cumprod()

    maximos = curva.cummax()

    drawdown = (
        curva
        / maximos
        - 1.0
    )

    return float(
        drawdown.min()
    )


def hhi(
    pesos: pd.Series,
) -> float:
    """Calcula concentración Herfindahl-Hirschman."""

    return float(
        np.sum(
            pesos**2
        )
    )


def activos_efectivos(
    pesos: pd.Series,
) -> float:
    """Calcula número efectivo de activos."""

    valor_hhi = hhi(
        pesos
    )

    if valor_hhi <= 0:
        return np.nan

    return float(
        1.0
        / valor_hhi
    )


def contribucion_riesgo(
    retornos: pd.DataFrame,
    pesos: pd.Series,
) -> pd.Series:
    """Calcula contribución porcentual a varianza."""

    pesos = pesos.reindex(
        retornos.columns
    ).fillna(
        0.0
    )

    covarianza = retornos.cov()

    w = pesos.to_numpy()

    cov = covarianza.to_numpy()

    varianza = float(
        w.T
        @ cov
        @ w
    )

    if varianza <= 0:
        return pd.Series(
            0.0,
            index=retornos.columns,
        )

    marginal = (
        cov
        @ w
    )

    contribucion = (
        w
        * marginal
        / varianza
    )

    return pd.Series(
        contribucion,
        index=retornos.columns,
        name="contribucion_riesgo",
    )


def analizar_riesgo(
    retornos: pd.DataFrame,
    pesos: pd.Series,
    factor_anual: int,
) -> dict[str, object]:
    """Ejecuta Risk Engine Universal."""

    rp = retornos_portfolio(
        retornos,
        pesos,
    )

    contribuciones = contribucion_riesgo(
        retornos,
        pesos,
    )

    return {
        "volatilidad_anual": volatilidad_anual(
            rp,
            factor_anual,
        ),
        "var_95": var_historico(
            rp,
            0.95,
        ),
        "var_99": var_historico(
            rp,
            0.99,
        ),
        "cvar_95": cvar_historico(
            rp,
            0.95,
        ),
        "cvar_99": cvar_historico(
            rp,
            0.99,
        ),
        "max_drawdown": max_drawdown(
            rp
        ),
        "hhi": hhi(
            pesos
        ),
        "activos_efectivos": (
            activos_efectivos(
                pesos
            )
        ),
        "contribucion_riesgo": (
            contribuciones
        ),
    }