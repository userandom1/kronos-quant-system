import numpy as np
import pandas as pd

from skfolio import RiskMeasure
from skfolio.optimization import (
    MeanRisk,
    ObjectiveFunction,
)


def pesos_equal_weight(
    retornos: pd.DataFrame,
) -> pd.Series:
    """Construye una cartera equiponderada."""

    n = len(
        retornos.columns
    )

    pesos = np.repeat(
        1.0 / n,
        n,
    )

    return pd.Series(
        pesos,
        index=retornos.columns,
        name="Equal Weight",
    )


def pesos_inverse_volatility(
    retornos: pd.DataFrame,
) -> pd.Series:
    """Construye pesos inversamente proporcionales a volatilidad."""

    volatilidad = retornos.std(
        ddof=1
    )

    inversa = (
        1.0
        / volatilidad
    )

    pesos = (
        inversa
        / inversa.sum()
    )

    return pesos.rename(
        "Inverse Volatility"
    )


def pesos_minimum_variance(
    retornos: pd.DataFrame,
) -> pd.Series:
    """Optimiza cartera de mínima varianza."""

    modelo = MeanRisk(
        objective_function=(
            ObjectiveFunction.MINIMIZE_RISK
        ),
        risk_measure=(
            RiskMeasure.VARIANCE
        ),
        min_weights=0.0,
        max_weights=1.0,
    )

    modelo.fit(
        retornos
    )

    pesos = pd.Series(
        modelo.weights_,
        index=retornos.columns,
        name="Minimum Variance",
    )

    return pesos


def pesos_maximum_sharpe(
    retornos: pd.DataFrame,
) -> pd.Series:
    """Optimiza una cartera de máximo ratio Sharpe."""

    modelo = MeanRisk(
        objective_function=(
            ObjectiveFunction.MAXIMIZE_RATIO
        ),
        risk_measure=(
            RiskMeasure.STANDARD_DEVIATION
        ),
        min_weights=0.0,
        max_weights=1.0,
    )

    modelo.fit(
        retornos
    )

    pesos = pd.Series(
        modelo.weights_,
        index=retornos.columns,
        name="Maximum Sharpe",
    )

    return pesos


def construir_tabla_pesos(
    retornos: pd.DataFrame,
) -> pd.DataFrame:
    """Construye tabla comparativa de pesos."""

    carteras = [
        pesos_equal_weight(
            retornos
        ),
        pesos_inverse_volatility(
            retornos
        ),
        pesos_minimum_variance(
            retornos
        ),
        pesos_maximum_sharpe(
            retornos
        ),
    ]

    return pd.concat(
        carteras,
        axis=1,
    )