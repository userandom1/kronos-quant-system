from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf


RUTA_BASE = Path(__file__).resolve().parents[1]

RUTA_RESULTADOS = (
    RUTA_BASE
    / "resultados"
    / "market_regime_v1"
)

SESIONES_ANUALES = 252


BENCHMARKS = {
    "QQQ": "SPY",
    "QQQM": "SPY",
    "QQQJ": "QQQ",
    "QQQI": "QQQ",
    "QQQY": "QQQ",
    "QYLD": "QQQ",
    "JEPQ": "QQQ",
    "QLD": "QQQ",
    "TQQQ": "QQQ",
    "PSQ": "QQQ",
    "QID": "QQQ",
    "SQQQ": "QQQ",
    "SMH": "QQQ",
    "SOXX": "QQQ",
    "XLK": "SPY",
    "IWM": "SPY",
    "DIA": "SPY",
    "SPY": "SPY",
    "TLT": "SPY",
    "GLD": "SPY",
}


def obtener_ticker() -> str:
    """
    Obtiene el ticker desde línea de comandos.

    Si no existe argumento, mantiene el modo interactivo.
    """

    if len(sys.argv) >= 2:
        entrada = sys.argv[1].strip()

    else:
        entrada = input(
            "Ticker: "
        ).strip()

    if not entrada:
        raise ValueError(
            "El ticker no puede estar vacío."
        )

    return entrada.upper()


def obtener_benchmark(
    ticker: str,
) -> str:
    """Devuelve el benchmark correspondiente."""

    return BENCHMARKS.get(
        ticker.upper(),
        "SPY",
    )


def descargar_precios(
    ticker: str,
    benchmark: str,
    periodo: str = "5y",
) -> pd.DataFrame:
    """Descarga precios ajustados del activo y benchmark."""

    ticker = ticker.upper()
    benchmark = benchmark.upper()

    if ticker == benchmark:
        tickers_descarga = [
            ticker
        ]

    else:
        tickers_descarga = [
            ticker,
            benchmark,
        ]

    datos = yf.download(
        tickers_descarga,
        period=periodo,
        interval="1d",
        auto_adjust=True,
        progress=False,
        threads=True,
    )

    if datos.empty:
        raise RuntimeError(
            "No se han podido descargar datos."
        )

    if isinstance(
        datos.columns,
        pd.MultiIndex,
    ):
        cierre = datos[
            "Close"
        ].copy()

    else:
        if "Close" not in datos.columns:
            raise KeyError(
                "La descarga no contiene columna Close."
            )

        cierre = datos[
            ["Close"]
        ].copy()

        cierre.columns = [
            ticker
        ]

    if isinstance(
        cierre,
        pd.Series,
    ):
        cierre = cierre.to_frame(
            name=ticker
        )

    if ticker not in cierre.columns:
        if len(
            cierre.columns
        ) == 1:
            cierre.columns = [
                ticker
            ]

        else:
            raise KeyError(
                f"No se encontraron precios para {ticker}."
            )

    if ticker == benchmark:
        cierre = cierre[
            [ticker]
        ].copy()

    else:
        if benchmark not in cierre.columns:
            raise KeyError(
                f"No se encontraron precios para "
                f"el benchmark {benchmark}."
            )

        cierre = cierre[
            [
                ticker,
                benchmark,
            ]
        ].copy()

    cierre = (
        cierre
        .sort_index()
        .ffill()
        .dropna()
    )

    if len(cierre) < 220:
        raise RuntimeError(
            "No existe histórico suficiente "
            "para calcular el régimen."
        )

    return cierre


def retorno_periodo(
    precios: pd.Series,
    sesiones: int,
) -> float:
    """Calcula retorno simple en N sesiones."""

    if len(precios) <= sesiones:
        return np.nan

    return float(
        precios.iloc[-1]
        / precios.iloc[
            -1 - sesiones
        ]
        - 1.0
    )


def volatilidad_anualizada(
    retornos: pd.Series,
    ventana: int,
) -> float:
    """Calcula volatilidad histórica anualizada."""

    muestra = (
        retornos
        .dropna()
        .tail(
            ventana
        )
    )

    if len(muestra) < 2:
        return np.nan

    return float(
        muestra.std(
            ddof=1
        )
        * np.sqrt(
            SESIONES_ANUALES
        )
    )


def sharpe_anualizado(
    retornos: pd.Series,
    ventana: int,
) -> float:
    """
    Calcula Sharpe anualizado.

    En V1 se asume tasa libre de riesgo igual a cero.
    """

    muestra = (
        retornos
        .dropna()
        .tail(
            ventana
        )
    )

    if len(muestra) < 2:
        return np.nan

    desviacion = muestra.std(
        ddof=1
    )

    if (
        not np.isfinite(
            desviacion
        )
        or desviacion <= 0
    ):
        return np.nan

    return float(
        muestra.mean()
        / desviacion
        * np.sqrt(
            SESIONES_ANUALES
        )
    )


def calcular_drawdown_actual(
    precios: pd.Series,
) -> float:
    """Calcula drawdown actual frente al máximo histórico."""

    maximo = precios.cummax()

    drawdown = (
        precios
        / maximo
        - 1.0
    )

    return float(
        drawdown.iloc[-1]
    )


def calcular_beta_correlacion(
    retornos_activo: pd.Series,
    retornos_benchmark: pd.Series,
    ventana: int = 60,
) -> tuple[float, float]:
    """Calcula beta y correlación frente al benchmark."""

    datos = pd.concat(
        [
            retornos_activo.rename(
                "activo"
            ),
            retornos_benchmark.rename(
                "benchmark"
            ),
        ],
        axis=1,
    ).dropna()

    datos = datos.tail(
        ventana
    )

    if len(datos) < 2:
        return (
            np.nan,
            np.nan,
        )

    var_benchmark = datos[
        "benchmark"
    ].var(
        ddof=1
    )

    if (
        not np.isfinite(
            var_benchmark
        )
        or var_benchmark <= 0
    ):
        beta = np.nan

    else:
        covarianza = datos[
            [
                "activo",
                "benchmark",
            ]
        ].cov().iloc[
            0,
            1
        ]

        beta = float(
            covarianza
            / var_benchmark
        )

    correlacion = float(
        datos[
            "activo"
        ].corr(
            datos[
                "benchmark"
            ]
        )
    )

    return (
        beta,
        correlacion,
    )


def clasificar_tendencia(
    precio: float,
    ma20: float,
    ma50: float,
    ma200: float,
) -> str:
    """Clasifica el régimen de tendencia."""

    if (
        precio > ma20
        and ma20 > ma50
        and ma50 > ma200
    ):
        return "ALCISTA_FUERTE"

    if (
        precio > ma50
        and precio > ma200
    ):
        return "ALCISTA"

    if (
        precio < ma20
        and ma20 < ma50
        and ma50 < ma200
    ):
        return "BAJISTA_FUERTE"

    if (
        precio < ma50
        and precio < ma200
    ):
        return "BAJISTA"

    return "MIXTO"


def clasificar_momentum(
    momentum20: float,
    momentum60: float,
) -> str:
    """Clasifica el momentum."""

    if (
        momentum20 > 0
        and momentum60 > 0
    ):
        return "POSITIVO"

    if (
        momentum20 < 0
        and momentum60 < 0
    ):
        return "NEGATIVO"

    return "MIXTO"


def clasificar_volatilidad(
    vol20: float,
    vol60: float,
) -> str:
    """Clasifica el régimen de volatilidad."""

    if (
        not np.isfinite(
            vol20
        )
        or not np.isfinite(
            vol60
        )
        or vol60 <= 0
    ):
        return "DESCONOCIDO"

    ratio = (
        vol20
        / vol60
    )

    if ratio >= 1.25:
        return "EXPANSION"

    if ratio <= 0.80:
        return "CONTRACCION"

    return "NORMAL"


def analizar_regimen(
    ticker: str,
    benchmark: str,
    precios: pd.DataFrame,
) -> pd.DataFrame:
    """Construye todas las métricas de Market Regime V1."""

    ticker = ticker.upper()
    benchmark = benchmark.upper()

    serie = precios[
        ticker
    ].copy()

    retornos = serie.pct_change()

    if ticker == benchmark:
        serie_benchmark = serie.copy()
        retornos_benchmark = retornos.copy()

    else:
        serie_benchmark = precios[
            benchmark
        ].copy()

        retornos_benchmark = (
            serie_benchmark
            .pct_change()
        )

    precio = float(
        serie.iloc[-1]
    )

    ma20 = float(
        serie
        .rolling(
            20
        )
        .mean()
        .iloc[-1]
    )

    ma50 = float(
        serie
        .rolling(
            50
        )
        .mean()
        .iloc[-1]
    )

    ma200 = float(
        serie
        .rolling(
            200
        )
        .mean()
        .iloc[-1]
    )

    retorno_1d = retorno_periodo(
        serie,
        1,
    )

    retorno_5d = retorno_periodo(
        serie,
        5,
    )

    retorno_20d = retorno_periodo(
        serie,
        20,
    )

    retorno_60d = retorno_periodo(
        serie,
        60,
    )

    momentum20 = retorno_20d
    momentum60 = retorno_60d

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

    drawdown_actual = (
        calcular_drawdown_actual(
            serie
        )
    )

    beta60, correlacion60 = (
        calcular_beta_correlacion(
            retornos,
            retornos_benchmark,
            ventana=60,
        )
    )

    regimen_tendencia = (
        clasificar_tendencia(
            precio,
            ma20,
            ma50,
            ma200,
        )
    )

    regimen_momentum = (
        clasificar_momentum(
            momentum20,
            momentum60,
        )
    )

    regimen_volatilidad = (
        clasificar_volatilidad(
            vol20,
            vol60,
        )
    )

    resultado = pd.DataFrame(
        [
            {
                "ticker": ticker,
                "benchmark": benchmark,
                "fecha": precios.index[
                    -1
                ].strftime(
                    "%Y-%m-%d"
                ),
                "precio": precio,

                "ma20": ma20,
                "ma50": ma50,
                "ma200": ma200,

                "retorno_1d": retorno_1d,
                "retorno_5d": retorno_5d,
                "retorno_20d": retorno_20d,
                "retorno_60d": retorno_60d,

                "momentum20": momentum20,
                "momentum60": momentum60,

                # Nombres históricos usados por otros módulos.
                "vol20": vol20,
                "vol60": vol60,

                # Alias descriptivos para compatibilidad nueva.
                "volatilidad20": vol20,
                "volatilidad60": vol60,

                "sharpe20": sharpe20,
                "sharpe60": sharpe60,

                "drawdown_actual": (
                    drawdown_actual
                ),

                "beta60": beta60,
                "correlacion60": (
                    correlacion60
                ),

                "regimen_tendencia": (
                    regimen_tendencia
                ),
                "regimen_momentum": (
                    regimen_momentum
                ),
                "regimen_volatilidad": (
                    regimen_volatilidad
                ),
            }
        ]
    )

    return resultado


def analizar_activo(
    ticker: str,
) -> dict:
    """
    Analiza un activo y devuelve un único registro.

    Mantiene compatibilidad con
    comparador_multi_activo.py.
    """

    ticker = ticker.strip().upper()

    if not ticker:
        raise ValueError(
            "El ticker no puede estar vacío."
        )

    benchmark = obtener_benchmark(
        ticker
    )

    precios = descargar_precios(
        ticker=ticker,
        benchmark=benchmark,
        periodo="5y",
    )

    resultado = analizar_regimen(
        ticker=ticker,
        benchmark=benchmark,
        precios=precios,
    )

    return resultado.iloc[
        0
    ].to_dict()


def guardar_resultado(
    ticker: str,
    resultado: pd.DataFrame,
) -> Path:
    """Guarda Market Regime V1."""

    ruta_ticker = (
        RUTA_RESULTADOS
        / ticker
    )

    ruta_ticker.mkdir(
        parents=True,
        exist_ok=True,
    )

    archivo = (
        ruta_ticker
        / "market_regime_v1.csv"
    )

    resultado.to_csv(
        archivo,
        index=False,
    )

    return archivo


def imprimir_resultado(
    resultado: pd.DataFrame,
) -> None:
    """Muestra un resumen en terminal."""

    fila = resultado.iloc[
        0
    ]

    print()

    print(
        "=" * 85
    )

    print(
        "MARKET REGIME V1"
    )

    print(
        "=" * 85
    )

    print(
        f"Ticker              : "
        f"{fila['ticker']}"
    )

    print(
        f"Benchmark           : "
        f"{fila['benchmark']}"
    )

    print(
        f"Precio              : "
        f"{fila['precio']:,.2f}"
    )

    print(
        f"Tendencia           : "
        f"{fila['regimen_tendencia']}"
    )

    print(
        f"Momentum            : "
        f"{fila['regimen_momentum']}"
    )

    print(
        f"Volatilidad         : "
        f"{fila['regimen_volatilidad']}"
    )

    print(
        f"Retorno 20D         : "
        f"{fila['retorno_20d'] * 100:+.2f}%"
    )

    print(
        f"Retorno 60D         : "
        f"{fila['retorno_60d'] * 100:+.2f}%"
    )

    print(
        f"Volatilidad 20D     : "
        f"{fila['vol20'] * 100:.2f}%"
    )

    print(
        f"Volatilidad 60D     : "
        f"{fila['vol60'] * 100:.2f}%"
    )

    print(
        f"Sharpe 20D          : "
        f"{fila['sharpe20']:.3f}"
    )

    print(
        f"Sharpe 60D          : "
        f"{fila['sharpe60']:.3f}"
    )

    print(
        f"Drawdown actual     : "
        f"{fila['drawdown_actual'] * 100:.2f}%"
    )

    print(
        f"Beta 60D            : "
        f"{fila['beta60']:.3f}"
    )

    print(
        f"Correlación 60D     : "
        f"{fila['correlacion60']:.3f}"
    )


def main() -> None:
    """Ejecuta Market Regime V1."""

    ticker = obtener_ticker()

    benchmark = obtener_benchmark(
        ticker
    )

    print(
        f"Analizando {ticker} "
        f"vs {benchmark}..."
    )

    precios = descargar_precios(
        ticker=ticker,
        benchmark=benchmark,
        periodo="5y",
    )

    resultado = analizar_regimen(
        ticker=ticker,
        benchmark=benchmark,
        precios=precios,
    )

    archivo = guardar_resultado(
        ticker,
        resultado,
    )

    imprimir_resultado(
        resultado
    )

    print()

    print(
        f"Resultado guardado: "
        f"{archivo}"
    )


if __name__ == "__main__":
    main()