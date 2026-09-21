from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf


RUTA_BASE = Path(__file__).resolve().parents[1]

RUTA_RESULTADOS = (
    RUTA_BASE
    / "resultados"
    / "validacion"
    / "v1"
)

UNIVERSO = [
    "QQQ",
    "SPY",
    "IWM",
    "SMH",
    "XLK",
    "TLT",
    "GLD",
]

SESIONES_ANUALES = 252


def descargar_precios(
    tickers: list[str],
    periodo: str = "10y",
) -> pd.DataFrame:
    """Descarga precios ajustados diarios."""

    datos = yf.download(
        tickers,
        period=periodo,
        interval="1d",
        auto_adjust=True,
        progress=False,
    )

    if datos.empty:
        raise RuntimeError(
            "No se han obtenido datos históricos."
        )

    if isinstance(
        datos.columns,
        pd.MultiIndex,
    ):
        precios = datos["Close"].copy()
    else:
        precios = datos[
            ["Close"]
        ].copy()

        precios.columns = [
            tickers[0]
        ]

    precios = (
        precios
        .sort_index()
        .ffill()
        .dropna()
    )

    return precios


def zscore_cross_sectional(
    datos: pd.DataFrame,
) -> pd.DataFrame:
    """Calcula z-score transversal por fecha."""

    media = datos.mean(
        axis=1
    )

    desviacion = datos.std(
        axis=1,
        ddof=0,
    ).replace(
        0.0,
        np.nan,
    )

    return (
        datos.sub(
            media,
            axis=0,
        )
        .div(
            desviacion,
            axis=0,
        )
        .fillna(0.0)
    )


def construir_features(
    precios: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    """Construye las señales históricas sin look-ahead."""

    retornos = precios.pct_change()

    retorno_20d = (
        precios
        / precios.shift(20)
        - 1.0
    )

    retorno_60d = (
        precios
        / precios.shift(60)
        - 1.0
    )

    ma20 = (
        precios
        .rolling(20)
        .mean()
    )

    ma50 = (
        precios
        .rolling(50)
        .mean()
    )

    ma200 = (
        precios
        .rolling(200)
        .mean()
    )

    distancia_ma20 = (
        precios
        / ma20
        - 1.0
    )

    distancia_ma50 = (
        precios
        / ma50
        - 1.0
    )

    distancia_ma200 = (
        precios
        / ma200
        - 1.0
    )

    vol20 = (
        retornos
        .rolling(20)
        .std(
            ddof=1
        )
        * np.sqrt(
            SESIONES_ANUALES
        )
    )

    media60 = (
        retornos
        .rolling(60)
        .mean()
    )

    vol60_diaria = (
        retornos
        .rolling(60)
        .std(
            ddof=1
        )
    )

    sharpe60 = (
        media60
        / vol60_diaria
        * np.sqrt(
            SESIONES_ANUALES
        )
    )

    maximo_acumulado = (
        precios.cummax()
    )

    drawdown = (
        precios
        / maximo_acumulado
        - 1.0
    )

    return {
        "retorno_20d": retorno_20d,
        "retorno_60d": retorno_60d,
        "momentum20": retorno_20d,
        "momentum60": retorno_60d,
        "distancia_ma20": distancia_ma20,
        "distancia_ma50": distancia_ma50,
        "distancia_ma200": distancia_ma200,
        "vol20": vol20,
        "sharpe60": sharpe60,
        "drawdown": drawdown,
    }


def construir_composite_historico(
    precios: pd.DataFrame,
) -> pd.DataFrame:
    """Reconstruye históricamente el Composite Signal."""

    features = construir_features(
        precios
    )

    z_momentum = (
        0.50
        * zscore_cross_sectional(
            features["momentum20"]
        )
        + 0.50
        * zscore_cross_sectional(
            features["momentum60"]
        )
    )

    z_tendencia = (
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

    z_rendimiento = (
        0.40
        * zscore_cross_sectional(
            features["retorno_20d"]
        )
        + 0.60
        * zscore_cross_sectional(
            features["retorno_60d"]
        )
    )

    z_sharpe = (
        zscore_cross_sectional(
            features["sharpe60"]
        )
    )

    z_riesgo = (
        -0.50
        * zscore_cross_sectional(
            features["vol20"]
        )
        + 0.50
        * zscore_cross_sectional(
            features["drawdown"]
        )
    )

    score_relativo = (
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

    z_relativo = (
        zscore_cross_sectional(
            score_relativo
        )
    )

    composite = (
        0.20 * z_tendencia
        + 0.20 * z_momentum
        + 0.15 * z_rendimiento
        + 0.15 * z_sharpe
        + 0.10 * z_riesgo
        + 0.10 * z_relativo
    )

    composite = composite.shift(1)

    return composite


def guardar_historico(
    precios: pd.DataFrame,
    composite: pd.DataFrame,
) -> None:
    """Guarda precios y señales históricas."""

    RUTA_RESULTADOS.mkdir(
        parents=True,
        exist_ok=True,
    )

    precios.to_csv(
        RUTA_RESULTADOS
        / "precios_historicos.csv"
    )

    composite.to_csv(
        RUTA_RESULTADOS
        / "composite_historico.csv"
    )