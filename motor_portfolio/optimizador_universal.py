from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import minimize


def pesos_equal_weight(
    retornos: pd.DataFrame,
) -> pd.Series:
    """Construye portfolio equiponderado."""

    n = retornos.shape[1]

    pesos = np.repeat(
        1.0 / n,
        n,
    )

    return pd.Series(
        pesos,
        index=retornos.columns,
        name="peso",
    )


def pesos_inverse_vol(
    retornos: pd.DataFrame,
) -> pd.Series:
    """Construye pesos inversos a volatilidad."""

    volatilidades = retornos.std(
        ddof=1
    )

    inversas = (
        1.0
        / volatilidades.replace(
            0,
            np.nan,
        )
    )

    pesos = (
        inversas
        / inversas.sum()
    )

    return pesos.rename(
        "peso"
    )


def pesos_min_varianza(
    retornos: pd.DataFrame,
    max_peso: float = 0.35,
) -> pd.Series:
    """Optimiza cartera long-only de mínima varianza."""

    covarianza = retornos.cov().to_numpy()

    activos = list(
        retornos.columns
    )

    n = len(
        activos
    )

    inicial = np.repeat(
        1.0 / n,
        n,
    )

    def objetivo(
        pesos: np.ndarray,
    ) -> float:
        return float(
            pesos.T
            @ covarianza
            @ pesos
        )

    restricciones = [
        {
            "type": "eq",
            "fun": lambda pesos: (
                np.sum(
                    pesos
                )
                - 1.0
            ),
        }
    ]

    limites = [
        (
            0.0,
            max_peso,
        )
        for _ in activos
    ]

    resultado = minimize(
        objetivo,
        inicial,
        method="SLSQP",
        bounds=limites,
        constraints=restricciones,
    )

    if not resultado.success:
        raise RuntimeError(
            f"Optimización fallida: "
            f"{resultado.message}"
        )

    return pd.Series(
        resultado.x,
        index=activos,
        name="peso",
    )


def pesos_signal_tilted(
    retornos: pd.DataFrame,
    senales: pd.Series,
    lambda_riesgo: float = 3.0,
    max_peso: float = 0.35,
) -> pd.Series:
    """Optimiza señal esperada frente a riesgo."""

    activos = list(
        retornos.columns
    )

    senales = (
        senales
        .reindex(
            activos
        )
        .fillna(0.0)
    )

    covarianza = retornos.cov().to_numpy()

    alpha = senales.to_numpy(
        dtype=float
    )

    n = len(
        activos
    )

    inicial = np.repeat(
        1.0 / n,
        n,
    )

    def objetivo(
        pesos: np.ndarray,
    ) -> float:
        retorno_signal = (
            alpha
            @ pesos
        )

        riesgo = (
            pesos.T
            @ covarianza
            @ pesos
        )

        return float(
            -retorno_signal
            + lambda_riesgo
            * riesgo
        )

    restricciones = [
        {
            "type": "eq",
            "fun": lambda pesos: (
                np.sum(
                    pesos
                )
                - 1.0
            ),
        }
    ]

    limites = [
        (
            0.0,
            max_peso,
        )
        for _ in activos
    ]

    resultado = minimize(
        objetivo,
        inicial,
        method="SLSQP",
        bounds=limites,
        constraints=restricciones,
    )

    if not resultado.success:
        raise RuntimeError(
            f"Optimización fallida: "
            f"{resultado.message}"
        )

    return pd.Series(
        resultado.x,
        index=activos,
        name="peso",
    )