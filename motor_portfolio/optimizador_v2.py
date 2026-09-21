from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from motor_portfolio.optimizador_v1 import (
    pesos_maximum_sharpe,
    pesos_minimum_variance,
)


def alinear_alpha(
    alpha: pd.Series,
    columnas: pd.Index,
) -> pd.Series:
    """Alinea el alpha con el universo de retornos."""

    alpha = alpha.reindex(
        columnas
    )

    if alpha.isna().any():
        faltantes = alpha[
            alpha.isna()
        ].index.tolist()

        raise ValueError(
            "Faltan señales para: "
            f"{faltantes}"
        )

    return alpha


def pesos_signal_tilted(
    retornos: pd.DataFrame,
    alpha: pd.Series,
    aversion_riesgo: float = 3.0,
    peso_maximo: float = 0.35,
) -> pd.Series:
    """
    Optimiza una cartera long-only usando señal y riesgo.

    Objetivo:
        maximizar alpha'w - lambda * w'Cov*w
    """

    columnas = retornos.columns

    alpha = alinear_alpha(
        alpha,
        columnas,
    )

    covarianza = (
        retornos.cov()
        * 252.0
    )

    vector_alpha = alpha.to_numpy(
        dtype=float
    )

    matriz_cov = covarianza.to_numpy(
        dtype=float
    )

    n_activos = len(
        columnas
    )

    inicial = np.repeat(
        1.0 / n_activos,
        n_activos,
    )

    limites = [
        (
            0.0,
            peso_maximo,
        )
        for _ in range(
            n_activos
        )
    ]

    restricciones = [
        {
            "type": "eq",
            "fun": lambda w: (
                np.sum(w) - 1.0
            ),
        }
    ]

    def objetivo(
        pesos: np.ndarray,
    ) -> float:
        """Función objetivo señal-riesgo."""

        retorno_senal = (
            vector_alpha
            @ pesos
        )

        varianza = (
            pesos
            @ matriz_cov
            @ pesos
        )

        utilidad = (
            retorno_senal
            - aversion_riesgo
            * varianza
        )

        return -float(
            utilidad
        )

    resultado = minimize(
        objetivo,
        inicial,
        method="SLSQP",
        bounds=limites,
        constraints=restricciones,
        options={
            "maxiter": 2000,
            "ftol": 1e-12,
        },
    )

    if not resultado.success:
        raise RuntimeError(
            "Falló la optimización Signal Tilted: "
            f"{resultado.message}"
        )

    pesos = pd.Series(
        resultado.x,
        index=columnas,
        name="Signal Tilted V2",
    )

    return pesos


def construir_carteras_v2(
    retornos: pd.DataFrame,
    alpha: pd.Series,
) -> pd.DataFrame:
    """Construye las carteras principales V2."""

    minimo_riesgo = (
        pesos_minimum_variance(
            retornos
        )
    )

    max_sharpe = (
        pesos_maximum_sharpe(
            retornos
        )
    )

    signal_tilted = (
        pesos_signal_tilted(
            retornos=retornos,
            alpha=alpha,
            aversion_riesgo=3.0,
            peso_maximo=0.35,
        )
    )

    return pd.concat(
        [
            minimo_riesgo,
            max_sharpe,
            signal_tilted,
        ],
        axis=1,
    )