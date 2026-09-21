from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf


RUTA_BASE = Path(__file__).resolve().parents[1]

RUTA_RESULTADOS = (
    RUTA_BASE
    / "resultados"
    / "regimen_mercado_v2"
)

ACTIVOS = [
    "SPY",
    "QQQ",
    "IWM",
    "RSP",
    "XLK",
    "SMH",
    "TLT",
    "SHY",
    "GLD",
    "HYG",
    "LQD",
    "^VIX",
]

ACTIVOS_RIESGO = [
    "SPY",
    "QQQ",
    "IWM",
    "RSP",
    "XLK",
    "SMH",
]

SESIONES_ANUALES = 252


def descargar_precios(
    periodo: str = "5y",
) -> pd.DataFrame:
    """Descarga precios diarios del universo macro."""

    datos = yf.download(
        ACTIVOS,
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

    return (
        precios
        .sort_index()
        .ffill()
        .dropna()
    )


def retorno(
    serie: pd.Series,
    sesiones: int,
) -> float:
    """Calcula retorno simple."""

    return float(
        serie.iloc[-1]
        / serie.iloc[-1 - sesiones]
        - 1.0
    )


def signo(
    valor: float,
    umbral: float = 0.0,
) -> float:
    """Transforma una variable en señal -1/0/+1."""

    if valor > umbral:
        return 1.0

    if valor < -umbral:
        return -1.0

    return 0.0


def analizar_tendencia(
    precios: pd.DataFrame,
) -> dict:
    """Evalúa la tendencia agregada de activos de riesgo."""

    puntuaciones = []

    for ticker in ACTIVOS_RIESGO:
        serie = precios[
            ticker
        ]

        ma50 = (
            serie
            .rolling(50)
            .mean()
            .iloc[-1]
        )

        ma200 = (
            serie
            .rolling(200)
            .mean()
            .iloc[-1]
        )

        precio = serie.iloc[-1]

        corto = signo(
            precio / ma50 - 1.0
        )

        largo = signo(
            ma50 / ma200 - 1.0
        )

        puntuaciones.append(
            0.50 * corto
            + 0.50 * largo
        )

    score = float(
        np.mean(
            puntuaciones
        )
    )

    if score >= 0.50:
        estado = "ALCISTA"

    elif score <= -0.50:
        estado = "BAJISTA"

    else:
        estado = "MIXTO"

    return {
        "score": score,
        "estado": estado,
    }


def analizar_volatilidad(
    precios: pd.DataFrame,
) -> dict:
    """Evalúa VIX y volatilidad realizada."""

    vix = float(
        precios[
            "^VIX"
        ].iloc[-1]
    )

    retornos_spy = (
        precios["SPY"]
        .pct_change()
    )

    vol20 = (
        retornos_spy
        .tail(20)
        .std(ddof=1)
        * np.sqrt(
            SESIONES_ANUALES
        )
    )

    vol60 = (
        retornos_spy
        .tail(60)
        .std(ddof=1)
        * np.sqrt(
            SESIONES_ANUALES
        )
    )

    ratio = (
        vol20 / vol60
        if vol60 > 0
        else np.nan
    )

    if vix < 18:
        score_vix = 1.0

    elif vix > 25:
        score_vix = -1.0

    else:
        score_vix = 0.0

    if ratio < 0.90:
        score_realizada = 1.0

    elif ratio > 1.20:
        score_realizada = -1.0

    else:
        score_realizada = 0.0

    score = (
        0.70 * score_vix
        + 0.30 * score_realizada
    )

    if score >= 0.50:
        estado = "BAJA"

    elif score <= -0.50:
        estado = "ALTA"

    else:
        estado = "NORMAL"

    return {
        "score": score,
        "estado": estado,
        "vix": vix,
        "vol20": vol20,
        "vol60": vol60,
    }


def analizar_credito(
    precios: pd.DataFrame,
) -> dict:
    """Usa HYG/LQD como proxy de apetito por riesgo crediticio."""

    ratio = (
        precios["HYG"]
        / precios["LQD"]
    )

    r20 = retorno(
        ratio,
        20,
    )

    r60 = retorno(
        ratio,
        60,
    )

    score = (
        0.60 * signo(
            r20,
            0.01,
        )
        + 0.40 * signo(
            r60,
            0.02,
        )
    )

    if score >= 0.50:
        estado = "RISK_ON"

    elif score <= -0.50:
        estado = "RISK_OFF"

    else:
        estado = "NEUTRAL"

    return {
        "score": score,
        "estado": estado,
        "hyg_lqd_20d": r20,
        "hyg_lqd_60d": r60,
    }


def analizar_tipos(
    precios: pd.DataFrame,
) -> dict:
    """Usa TLT/SHY como proxy de dirección de tipos."""

    ratio = (
        precios["TLT"]
        / precios["SHY"]
    )

    r20 = retorno(
        ratio,
        20,
    )

    r60 = retorno(
        ratio,
        60,
    )

    score = (
        0.60 * signo(
            r20,
            0.01,
        )
        + 0.40 * signo(
            r60,
            0.02,
        )
    )

    if score >= 0.50:
        estado = "TIPOS_DESCENDIENDO"

    elif score <= -0.50:
        estado = "TIPOS_SUBIENDO"

    else:
        estado = "MIXTO"

    return {
        "score": score,
        "estado": estado,
        "tlt_shy_20d": r20,
        "tlt_shy_60d": r60,
    }


def analizar_cross_asset(
    precios: pd.DataFrame,
) -> dict:
    """Evalúa liderazgo entre equity, bonos y oro."""

    spy20 = retorno(
        precios["SPY"],
        20,
    )

    tlt20 = retorno(
        precios["TLT"],
        20,
    )

    gld20 = retorno(
        precios["GLD"],
        20,
    )

    if (
        spy20 > 0
        and spy20 > tlt20
        and spy20 > gld20
    ):
        score = 1.0
        estado = "RISK_ON"

    elif (
        spy20 < 0
        and (
            tlt20 > spy20
            or gld20 > spy20
        )
    ):
        score = -1.0
        estado = "DEFENSIVO"

    else:
        score = 0.0
        estado = "MIXTO"

    return {
        "score": score,
        "estado": estado,
        "spy20": spy20,
        "tlt20": tlt20,
        "gld20": gld20,
    }


def analizar_correlacion(
    precios: pd.DataFrame,
) -> dict:
    """Calcula correlación media entre activos de riesgo."""

    retornos = (
        precios[
            ACTIVOS_RIESGO
        ]
        .pct_change()
        .tail(60)
        .dropna()
    )

    matriz = retornos.corr()

    valores = (
        matriz
        .where(
            np.triu(
                np.ones(
                    matriz.shape
                ),
                k=1,
            ).astype(bool)
        )
        .stack()
    )

    correlacion_media = float(
        valores.mean()
    )

    if correlacion_media >= 0.80:
        estado = "ALTA"

    elif correlacion_media <= 0.50:
        estado = "BAJA"

    else:
        estado = "NORMAL"

    return {
        "score": 0.0,
        "estado": estado,
        "correlacion_media": (
            correlacion_media
        ),
    }


def analizar_breadth(
    precios: pd.DataFrame,
) -> dict:
    """Evalúa breadth mediante RSP/SPY e IWM/SPY."""

    rsp_spy = (
        precios["RSP"]
        / precios["SPY"]
    )

    iwm_spy = (
        precios["IWM"]
        / precios["SPY"]
    )

    rsp20 = retorno(
        rsp_spy,
        20,
    )

    iwm20 = retorno(
        iwm_spy,
        20,
    )

    media = (
        rsp20 + iwm20
    ) / 2.0

    score = signo(
        media,
        0.01,
    )

    if score > 0:
        estado = "AMPLIA"

    elif score < 0:
        estado = "ESTRECHA"

    else:
        estado = "NEUTRAL"

    return {
        "score": score,
        "estado": estado,
        "rsp_spy_20d": rsp20,
        "iwm_spy_20d": iwm20,
    }


def calcular_regimen_global(
    componentes: dict,
) -> dict:
    """Construye el régimen agregado."""

    score = (
        0.30
        * componentes[
            "tendencia"
        ]["score"]
        + 0.20
        * componentes[
            "volatilidad"
        ]["score"]
        + 0.15
        * componentes[
            "credito"
        ]["score"]
        + 0.10
        * componentes[
            "tipos"
        ]["score"]
        + 0.10
        * componentes[
            "cross_asset"
        ]["score"]
        + 0.15
        * componentes[
            "breadth"
        ]["score"]
    )

    if score >= 0.50:
        estado = "RISK_ON_FUERTE"

    elif score >= 0.20:
        estado = "RISK_ON"

    elif score <= -0.50:
        estado = "RISK_OFF_FUERTE"

    elif score <= -0.20:
        estado = "RISK_OFF"

    else:
        estado = "NEUTRAL_MIXTO"

    return {
        "score": float(score),
        "estado": estado,
    }


def ejecutar_analisis() -> tuple[
    dict,
    pd.DataFrame,
]:
    """Ejecuta el Market Regime V2 completo."""

    precios = descargar_precios()

    componentes = {
        "tendencia": analizar_tendencia(
            precios
        ),
        "volatilidad": analizar_volatilidad(
            precios
        ),
        "credito": analizar_credito(
            precios
        ),
        "tipos": analizar_tipos(
            precios
        ),
        "cross_asset": analizar_cross_asset(
            precios
        ),
        "correlacion": analizar_correlacion(
            precios
        ),
        "breadth": analizar_breadth(
            precios
        ),
    }

    global_regime = calcular_regimen_global(
        componentes
    )

    componentes[
        "global"
    ] = global_regime

    filas = []

    for nombre, datos in componentes.items():
        fila = {
            "componente": nombre,
            "score": datos.get(
                "score"
            ),
            "estado": datos.get(
                "estado"
            ),
        }

        for clave, valor in datos.items():
            if clave not in {
                "score",
                "estado",
            }:
                fila[
                    clave
                ] = valor

        filas.append(
            fila
        )

    detalle = pd.DataFrame(
        filas
    )

    return (
        componentes,
        detalle,
    )