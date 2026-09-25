from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from motor_mercado.regimen_universal import (
    analizar_regimen_universal,
)
from motor_portfolio.datos_universales import (
    calcular_retornos,
    descargar_precios_universo,
    sesiones_anuales,
)
from motor_portfolio.optimizador_universal import (
    pesos_equal_weight,
    pesos_inverse_vol,
    pesos_min_varianza,
    pesos_signal_tilted,
)


@dataclass(slots=True)
class ResultadoPortfolio:
    """Resultado del Portfolio Engine Universal."""

    simbolos: list[str]
    precios: pd.DataFrame
    retornos: pd.DataFrame
    pesos: pd.DataFrame
    factor_anual: int


def construir_senales(
    simbolos: list[str],
) -> pd.Series:
    """Utiliza Market Regime como señal transversal."""

    valores: dict[str, float] = {}

    for simbolo in simbolos:
        resultado = (
            analizar_regimen_universal(
                simbolo
            )
        )

        valores[
            simbolo
        ] = float(
            resultado[
                "score_regimen"
            ]
        )

    return pd.Series(
        valores,
        name="signal",
    )


def ejecutar_portfolio_universal(
    simbolos: list[str],
    max_peso: float = 0.35,
) -> ResultadoPortfolio:
    """Ejecuta los principales portfolios universales."""

    precios = descargar_precios_universo(
        simbolos
    )

    retornos = calcular_retornos(
        precios
    )

    senales = construir_senales(
        simbolos
    )

    pesos = pd.concat(
        {
            "EQUAL_WEIGHT": pesos_equal_weight(
                retornos
            ),
            "INVERSE_VOL": pesos_inverse_vol(
                retornos
            ),
            "MIN_VARIANCE": pesos_min_varianza(
                retornos,
                max_peso=max_peso,
            ),
            "SIGNAL_TILTED": pesos_signal_tilted(
                retornos,
                senales,
                max_peso=max_peso,
            ),
        },
        axis=1,
    )

    return ResultadoPortfolio(
        simbolos=simbolos,
        precios=precios,
        retornos=retornos,
        pesos=pesos,
        factor_anual=sesiones_anuales(
            simbolos
        ),
    )