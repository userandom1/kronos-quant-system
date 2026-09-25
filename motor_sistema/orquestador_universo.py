from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from motor_mercado.comparador_universal import (
    analizar_universo,
    clasificar_fuerza_relativa,
    construir_score_relativo,
    ordenar_resultados,
)
from motor_portfolio.portfolio_universal import (
    ResultadoPortfolio,
    ejecutar_portfolio_universal,
)
from motor_riesgo.risk_engine_universal import (
    analizar_riesgo,
)


@dataclass(slots=True)
class ResultadoUniverso:
    """Resultado agregado de un universo."""

    simbolos: list[str]
    ranking: pd.DataFrame
    portfolio: ResultadoPortfolio
    riesgo: dict[str, object]


def analizar_universo_completo(
    simbolos: list[str],
) -> ResultadoUniverso:
    """Ejecuta Market + Portfolio + Risk."""

    ranking = analizar_universo(
        simbolos
    )

    ranking = construir_score_relativo(
        ranking
    )

    ranking = clasificar_fuerza_relativa(
        ranking
    )

    ranking = ordenar_resultados(
        ranking
    )

    portfolio = ejecutar_portfolio_universal(
        simbolos
    )

    pesos = portfolio.pesos[
        "SIGNAL_TILTED"
    ]

    riesgo = analizar_riesgo(
        retornos=portfolio.retornos,
        pesos=pesos,
        factor_anual=portfolio.factor_anual,
    )

    return ResultadoUniverso(
        simbolos=simbolos,
        ranking=ranking,
        portfolio=portfolio,
        riesgo=riesgo,
    )