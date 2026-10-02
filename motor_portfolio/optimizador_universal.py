from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import minimize


def pesos_equal_weight(
    retornos: pd.DataFrame,
) -> pd.Series:
    """Construye portfolio equiponderado."""

    validar_optimizacion(retornos, None)
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

    validar_optimizacion(retornos, None)
    volatilidades = retornos.std(
        ddof=1
    )

    if (volatilidades <= 0).any():
        raise ValueError("Inverse Vol requiere volatilidades positivas.")

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
    max_peso: float | None = None,
) -> pd.Series:
    """Optimiza cartera long-only de mínima varianza."""

    max_peso = validar_optimizacion(retornos, max_peso)
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
    max_peso: float | None = None,
) -> pd.Series:
    """Optimiza señal esperada frente a riesgo."""

    if not np.isfinite(lambda_riesgo) or lambda_riesgo <= 0:
        raise ValueError("lambda_riesgo debe ser positivo y finito.")
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

    max_peso = validar_optimizacion(retornos, max_peso)
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

def validar_optimizacion(retornos: pd.DataFrame, max_peso: float | None) -> float:
    """Valida datos y factibilidad antes de invocar el optimizador."""
    n = retornos.shape[1]
    if n == 0 or len(retornos) < 2 or retornos.columns.has_duplicates:
        raise ValueError("Se requieren activos únicos y al menos dos observaciones.")
    if not np.isfinite(retornos.to_numpy(dtype=float)).all():
        raise ValueError("Los retornos contienen valores no finitos.")
    limite = max(0.35, 1.0 / n) if max_peso is None else max_peso
    if not np.isfinite(limite) or not 0 < limite <= 1:
        raise ValueError("max_peso debe estar entre 0 y 1.")
    if n * limite < 1.0 - 1e-10:
        raise ValueError(f"Límite inviable: {n} activos × {limite:.2%} < 100%.")
    return float(limite)
