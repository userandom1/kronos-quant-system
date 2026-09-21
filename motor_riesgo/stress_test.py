from __future__ import annotations

import pandas as pd


ESCENARIOS = {
    "RISK_OFF": {
        "QQQ": -0.15,
        "SPY": -0.12,
        "IWM": -0.18,
        "SMH": -0.20,
        "XLK": -0.15,
        "TLT": 0.08,
        "GLD": 0.05,
    },
    "TECH_CRASH": {
        "QQQ": -0.20,
        "SPY": -0.10,
        "IWM": -0.12,
        "SMH": -0.28,
        "XLK": -0.22,
        "TLT": 0.05,
        "GLD": 0.03,
    },
    "RATES_UP": {
        "QQQ": -0.10,
        "SPY": -0.07,
        "IWM": -0.09,
        "SMH": -0.12,
        "XLK": -0.10,
        "TLT": -0.12,
        "GLD": -0.05,
    },
    "INFLATION_SHOCK": {
        "QQQ": -0.08,
        "SPY": -0.06,
        "IWM": -0.07,
        "SMH": -0.10,
        "XLK": -0.08,
        "TLT": -0.10,
        "GLD": 0.08,
    },
    "LIQUIDITY_CRISIS": {
        "QQQ": -0.18,
        "SPY": -0.16,
        "IWM": -0.23,
        "SMH": -0.22,
        "XLK": -0.18,
        "TLT": -0.05,
        "GLD": -0.04,
    },
}


def ejecutar_stress_tests(
    pesos: pd.Series,
) -> pd.DataFrame:
    """Aplica shocks deterministas a la cartera."""

    filas = []

    for nombre, shocks in ESCENARIOS.items():
        retorno_portfolio = 0.0

        detalle = {}

        for ticker, peso in pesos.items():
            shock = shocks.get(
                ticker,
                0.0,
            )

            contribucion = (
                peso
                * shock
            )

            retorno_portfolio += (
                contribucion
            )

            detalle[
                f"shock_{ticker}"
            ] = shock

        filas.append(
            {
                "escenario": nombre,
                "impacto_portfolio": retorno_portfolio,
                **detalle,
            }
        )

    return pd.DataFrame(
        filas
    ).sort_values(
        "impacto_portfolio"
    )


def stress_historico(
    retornos_portfolio: pd.Series,
) -> pd.DataFrame:
    """Busca peores movimientos históricos acumulados."""

    filas = []

    for horizonte in [
        1,
        5,
        20,
    ]:
        retorno_acumulado = (
            (
                1.0
                + retornos_portfolio
            )
            .rolling(
                horizonte
            )
            .apply(
                lambda x: x.prod(),
                raw=True,
            )
            - 1.0
        )

        peor_fecha = (
            retorno_acumulado.idxmin()
        )

        filas.append(
            {
                "horizonte_dias": horizonte,
                "peor_retorno": (
                    retorno_acumulado.min()
                ),
                "fecha_fin": peor_fecha,
            }
        )

    return pd.DataFrame(
        filas
    )