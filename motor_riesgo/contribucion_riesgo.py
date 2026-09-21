from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import norm


SESIONES_ANUALES = 252


def calcular_contribucion_riesgo(
    retornos: pd.DataFrame,
    pesos: pd.Series,
) -> pd.DataFrame:
    """Calcula contribución marginal y total a volatilidad."""

    pesos = pesos.reindex(
        retornos.columns
    ).fillna(0.0)

    covarianza_diaria = (
        retornos.cov()
    )

    covarianza_anual = (
        covarianza_diaria
        * SESIONES_ANUALES
    )

    vector_pesos = pesos.to_numpy(
        dtype=float
    )

    matriz = covarianza_anual.to_numpy(
        dtype=float
    )

    varianza_portfolio = float(
        vector_pesos
        @ matriz
        @ vector_pesos
    )

    volatilidad_portfolio = np.sqrt(
        varianza_portfolio
    )

    sigma_w = (
        matriz
        @ vector_pesos
    )

    marginal_risk = (
        sigma_w
        / volatilidad_portfolio
    )

    component_risk = (
        vector_pesos
        * marginal_risk
    )

    contribucion_pct = (
        component_risk
        / volatilidad_portfolio
    )

    resultado = pd.DataFrame(
        {
            "ticker": retornos.columns,
            "peso": vector_pesos,
            "marginal_risk": marginal_risk,
            "component_risk": component_risk,
            "contribucion_riesgo_pct": contribucion_pct,
        }
    )

    return resultado.sort_values(
        "contribucion_riesgo_pct",
        ascending=False,
    )


def calcular_component_var(
    retornos: pd.DataFrame,
    pesos: pd.Series,
    confianza: float = 0.95,
) -> pd.DataFrame:
    """Calcula Component VaR paramétrico diario."""

    pesos = pesos.reindex(
        retornos.columns
    ).fillna(0.0)

    covarianza = retornos.cov()

    vector_pesos = pesos.to_numpy(
        dtype=float
    )

    matriz = covarianza.to_numpy(
        dtype=float
    )

    volatilidad_portfolio = np.sqrt(
        vector_pesos
        @ matriz
        @ vector_pesos
    )

    z = norm.ppf(
        confianza
    )

    marginal_var = (
        z
        * (
            matriz
            @ vector_pesos
        )
        / volatilidad_portfolio
    )

    component_var = (
        vector_pesos
        * marginal_var
    )

    total_var = component_var.sum()

    porcentaje = np.where(
        total_var != 0,
        component_var / total_var,
        np.nan,
    )

    resultado = pd.DataFrame(
        {
            "ticker": retornos.columns,
            "peso": vector_pesos,
            "marginal_var_1d": marginal_var,
            "component_var_1d": component_var,
            "component_var_pct": porcentaje,
        }
    )

    return resultado.sort_values(
        "component_var_1d",
        ascending=False,
    )