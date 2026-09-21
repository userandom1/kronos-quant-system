from pathlib import Path

import numpy as np
import pandas as pd

from motor_mercado.estudio_regimen_v1 import (
    analizar_activo,
)


RUTA_BASE = Path(__file__).resolve().parents[1]

RUTA_RESULTADOS = (
    RUTA_BASE
    / "resultados"
    / "market_regime_v1"
    / "comparador_multi_activo"
)


UNIVERSO_BASE = [
    "QQQ",
    "SPY",
    "IWM",
    "SMH",
    "XLK",
    "TLT",
    "GLD",
]


def analizar_universo(
    tickers: list[str],
) -> pd.DataFrame:
    """Analiza un conjunto de activos."""

    resultados = []

    for ticker in tickers:
        print(
            f"Analizando {ticker}..."
        )

        try:
            resultado = analizar_activo(
                ticker
            )

            resultados.append(
                resultado
            )

        except Exception as error:
            print(
                f"Error en {ticker}: {error}"
            )

    if not resultados:
        raise RuntimeError(
            "No se pudo analizar ningún activo."
        )

    return pd.DataFrame(
        resultados
    )


def normalizar_serie(
    serie: pd.Series,
) -> pd.Series:
    """Normaliza una serie mediante z-score."""

    desviacion = serie.std(
        ddof=0
    )

    if (
        desviacion == 0
        or not np.isfinite(
            desviacion
        )
    ):
        return pd.Series(
            0.0,
            index=serie.index,
        )

    return (
        serie
        - serie.mean()
    ) / desviacion


def construir_score(
    datos: pd.DataFrame,
) -> pd.DataFrame:
    """Construye un score cuantitativo relativo."""

    datos = datos.copy()

    z_ret20 = normalizar_serie(
        datos["retorno_20d"]
    )

    z_ret60 = normalizar_serie(
        datos["retorno_60d"]
    )

    z_mom20 = normalizar_serie(
        datos["momentum20"]
    )

    z_sharpe60 = normalizar_serie(
        datos["sharpe60"]
    )

    z_vol20 = normalizar_serie(
        datos["vol20"]
    )

    z_drawdown = normalizar_serie(
        datos["drawdown_actual"]
    )

    datos["score_relativo"] = (
        0.20 * z_ret20
        + 0.20 * z_ret60
        + 0.20 * z_mom20
        + 0.20 * z_sharpe60
        - 0.10 * z_vol20
        + 0.10 * z_drawdown
    )

    datos[
        "ranking"
    ] = datos[
        "score_relativo"
    ].rank(
        ascending=False,
        method="min",
    )

    return datos


def clasificar_relativo(
    datos: pd.DataFrame,
) -> pd.DataFrame:
    """Clasifica el posicionamiento relativo del universo."""

    datos = datos.copy()

    percentil = datos[
        "score_relativo"
    ].rank(
        pct=True
    )

    datos[
        "regimen_relativo"
    ] = np.select(
        [
            percentil >= 0.80,
            percentil >= 0.60,
            percentil <= 0.20,
            percentil <= 0.40,
        ],
        [
            "FUERZA_RELATIVA_ALTA",
            "FUERZA_RELATIVA",
            "DEBILIDAD_RELATIVA_ALTA",
            "DEBILIDAD_RELATIVA",
        ],
        default="NEUTRAL",
    )

    return datos


def imprimir_ranking(
    datos: pd.DataFrame,
) -> None:
    """Muestra el ranking multi-activo."""

    columnas = [
        "ranking",
        "ticker",
        "precio",
        "retorno_5d",
        "retorno_20d",
        "retorno_60d",
        "vol20",
        "sharpe60",
        "drawdown_actual",
        "score_relativo",
        "regimen_tendencia",
        "regimen_relativo",
    ]

    salida = (
        datos[
            columnas
        ]
        .sort_values(
            "ranking"
        )
        .copy()
    )

    for columna in [
        "retorno_5d",
        "retorno_20d",
        "retorno_60d",
        "vol20",
        "drawdown_actual",
    ]:
        salida[columna] = (
            salida[columna]
            * 100.0
        )

    print()
    print("=" * 130)
    print("MULTI-ASSET MARKET INTELLIGENCE V1")
    print("=" * 130)

    print(
        salida.to_string(
            index=False,
            float_format=lambda x: (
                f"{x:,.3f}"
            ),
        )
    )


def main() -> None:
    """Ejecuta el comparador multi-activo."""

    RUTA_RESULTADOS.mkdir(
        parents=True,
        exist_ok=True,
    )

    datos = analizar_universo(
        UNIVERSO_BASE
    )

    datos = construir_score(
        datos
    )

    datos = clasificar_relativo(
        datos
    )

    ruta = (
        RUTA_RESULTADOS
        / "ranking_multi_activo.csv"
    )

    datos.to_csv(
        ruta,
        index=False,
    )

    imprimir_ranking(
        datos
    )

    print()
    print(
        f"Guardado en: {ruta}"
    )


if __name__ == "__main__":
    main()