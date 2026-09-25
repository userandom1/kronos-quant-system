from __future__ import annotations

import numpy as np
import pandas as pd

from core.activos import Activo
from core.datos import obtener_proveedor
from motor_mercado.metricas_mercado import (
    beta_correlacion,
    clasificar_momentum,
    clasificar_tendencia,
    clasificar_volatilidad,
    drawdown_actual,
    retorno_periodo,
    sharpe_anualizado,
    volatilidad_anualizada,
)


def analizar_activo_universal(
    activo: Activo,
    periodo: str = "5y",
) -> dict[str, object]:
    """Analiza cualquier activo mediante el esquema universal."""

    proveedor = obtener_proveedor(
        activo.proveedor
    )

    datos = proveedor.obtener_historico(
        activo=activo,
        periodo=periodo,
        intervalo="1d",
    )

    cierre = datos[
        "close"
    ].dropna()

    if len(cierre) < 200:
        raise RuntimeError(
            f"Histórico insuficiente para "
            f"{activo.simbolo}."
        )

    retornos = cierre.pct_change()

    precio = float(
        cierre.iloc[-1]
    )

    ma20 = float(
        cierre.rolling(20)
        .mean()
        .iloc[-1]
    )

    ma50 = float(
        cierre.rolling(50)
        .mean()
        .iloc[-1]
    )

    ma200 = float(
        cierre.rolling(200)
        .mean()
        .iloc[-1]
    )

    retorno_20d = retorno_periodo(
        cierre,
        20,
    )

    retorno_60d = retorno_periodo(
        cierre,
        60,
    )

    vol20 = volatilidad_anualizada(
        retornos,
        20,
    )

    vol60 = volatilidad_anualizada(
        retornos,
        60,
    )

    sharpe20 = sharpe_anualizado(
        retornos,
        20,
    )

    sharpe60 = sharpe_anualizado(
        retornos,
        60,
    )

    dd_actual = drawdown_actual(
        cierre
    )

    beta60 = np.nan
    correlacion60 = np.nan

    if (
        activo.benchmark
        and activo.benchmark
        != activo.simbolo
    ):
        try:
            from core.activos import (
                resolver_activo,
            )

            benchmark = resolver_activo(
                activo.benchmark
            )

            datos_benchmark = (
                proveedor.obtener_historico(
                    activo=benchmark,
                    periodo=periodo,
                    intervalo="1d",
                )
            )

            retornos_benchmark = (
                datos_benchmark[
                    "close"
                ]
                .dropna()
                .pct_change()
            )

            beta60, correlacion60 = (
                beta_correlacion(
                    retornos,
                    retornos_benchmark,
                    ventana=60,
                )
            )

        except Exception:
            pass

    return {
        "simbolo": activo.simbolo,
        "clase": activo.clase.value,
        "mercado": activo.mercado,
        "divisa": activo.divisa,
        "benchmark": activo.benchmark,
        "proveedor": activo.proveedor,
        "fecha": datos.index[
            -1
        ],
        "precio": precio,
        "ma20": ma20,
        "ma50": ma50,
        "ma200": ma200,
        "retorno_20d": retorno_20d,
        "retorno_60d": retorno_60d,
        "vol20": vol20,
        "vol60": vol60,
        "sharpe20": sharpe20,
        "sharpe60": sharpe60,
        "drawdown_actual": dd_actual,
        "beta60": beta60,
        "correlacion60": correlacion60,
        "regimen_tendencia": (
            clasificar_tendencia(
                precio,
                ma20,
                ma50,
                ma200,
            )
        ),
        "regimen_momentum": (
            clasificar_momentum(
                retorno_20d,
                retorno_60d,
            )
        ),
        "regimen_volatilidad": (
            clasificar_volatilidad(
                vol20,
                vol60,
            )
        ),
    }


def resultado_a_dataframe(
    resultado: dict[str, object],
) -> pd.DataFrame:
    """Convierte un resultado en DataFrame."""

    return pd.DataFrame(
        [resultado]
    )