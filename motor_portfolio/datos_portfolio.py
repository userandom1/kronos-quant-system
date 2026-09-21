from pathlib import Path

import pandas as pd
import yfinance as yf


RUTA_BASE = Path(__file__).resolve().parents[1]

RUTA_RESULTADOS = (
    RUTA_BASE
    / "resultados"
    / "portfolio_engine"
    / "v1"
)

UNIVERSO_PORTFOLIO = [
    "QQQ",
    "SPY",
    "IWM",
    "SMH",
    "XLK",
    "TLT",
    "GLD",
]


def descargar_precios(
    tickers: list[str],
    periodo: str = "5y",
) -> pd.DataFrame:
    """Descarga precios ajustados para el universo."""

    datos = yf.download(
        tickers,
        period=periodo,
        interval="1d",
        auto_adjust=True,
        progress=False,
    )

    if datos.empty:
        raise RuntimeError(
            "No se han obtenido datos."
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
        .dropna(
            how="all"
        )
        .ffill()
        .dropna()
    )

    return precios


def calcular_retornos(
    precios: pd.DataFrame,
) -> pd.DataFrame:
    """Calcula retornos simples diarios."""

    retornos = (
        precios
        .pct_change()
        .dropna()
    )

    return retornos


def guardar_datos(
    precios: pd.DataFrame,
    retornos: pd.DataFrame,
) -> None:
    """Guarda precios y retornos."""

    RUTA_RESULTADOS.mkdir(
        parents=True,
        exist_ok=True,
    )

    precios.to_csv(
        RUTA_RESULTADOS
        / "precios.csv"
    )

    retornos.to_csv(
        RUTA_RESULTADOS
        / "retornos.csv"
    )