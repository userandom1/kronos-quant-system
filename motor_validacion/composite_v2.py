from __future__ import annotations

import pandas as pd

from motor_validacion.historico_senales import (
    construir_features,
    zscore_cross_sectional,
)


def construir_senales_v2(
    precios: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    """Construye las señales candidatas para Composite V2."""

    features = construir_features(
        precios
    )

    momentum = (
        0.50
        * zscore_cross_sectional(
            features["momentum20"]
        )
        + 0.50
        * zscore_cross_sectional(
            features["momentum60"]
        )
    )

    tendencia = (
        0.40
        * zscore_cross_sectional(
            features["distancia_ma20"]
        )
        + 0.30
        * zscore_cross_sectional(
            features["distancia_ma50"]
        )
        + 0.30
        * zscore_cross_sectional(
            features["distancia_ma200"]
        )
    )

    rendimiento = (
        0.40
        * zscore_cross_sectional(
            features["retorno_20d"]
        )
        + 0.60
        * zscore_cross_sectional(
            features["retorno_60d"]
        )
    )

    sharpe = zscore_cross_sectional(
        features["sharpe60"]
    )

    riesgo = (
        -0.50
        * zscore_cross_sectional(
            features["vol20"]
        )
        + 0.50
        * zscore_cross_sectional(
            features["drawdown"]
        )
    )

    relativo = (
        0.20
        * zscore_cross_sectional(
            features["retorno_20d"]
        )
        + 0.20
        * zscore_cross_sectional(
            features["retorno_60d"]
        )
        + 0.20
        * zscore_cross_sectional(
            features["momentum20"]
        )
        + 0.20
        * zscore_cross_sectional(
            features["sharpe60"]
        )
        - 0.10
        * zscore_cross_sectional(
            features["vol20"]
        )
        + 0.10
        * zscore_cross_sectional(
            features["drawdown"]
        )
    )

    relativo = zscore_cross_sectional(
        relativo
    )

    composite_v1 = (
        0.20 * tendencia
        + 0.20 * momentum
        + 0.15 * rendimiento
        + 0.15 * sharpe
        + 0.10 * riesgo
        + 0.10 * relativo
    )

    composite_v2_20d = (
        0.30 * tendencia
        + 0.30 * momentum
        + 0.25 * relativo
        + 0.15 * sharpe
    )

    composite_v2_60d = (
        0.45 * tendencia
        + 0.30 * momentum
        + 0.25 * relativo
    )

    senales = {
        "COMPOSITE_V1": composite_v1,
        "COMPOSITE_V2_20D": composite_v2_20d,
        "COMPOSITE_V2_60D": composite_v2_60d,
        "TENDENCIA": tendencia,
        "MOMENTUM": momentum,
    }

    return {
        nombre: senal.shift(1)
        for nombre, senal in senales.items()
    }