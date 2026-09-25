from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from motor_mercado.regimen_universal import (
    analizar_regimen_universal,
)


RUTA_BASE = Path(__file__).resolve().parents[1]

RUTA_RESULTADOS = (
    RUTA_BASE
    / "resultados"
    / "market_regime_v2"
    / "comparador_universal"
)


def normalizar_serie(
    serie: pd.Series,
) -> pd.Series:
    """Normaliza una serie mediante z-score."""

    serie = pd.to_numeric(
        serie,
        errors="coerce",
    )

    media = serie.mean()

    desviacion = serie.std(
        ddof=0
    )

    if (
        not np.isfinite(desviacion)
        or desviacion == 0
    ):
        return pd.Series(
            0.0,
            index=serie.index,
            dtype=float,
        )

    return (
        serie
        - media
    ) / desviacion


def analizar_universo(
    simbolos: list[str],
) -> pd.DataFrame:
    """Analiza todos los activos solicitados."""

    resultados: list[
        dict[str, object]
    ] = []

    errores: list[
        tuple[str, str]
    ] = []

    for simbolo in simbolos:
        simbolo = simbolo.strip().upper()

        if not simbolo:
            continue

        print(
            f"Analizando {simbolo}..."
        )

        try:
            resultado = (
                analizar_regimen_universal(
                    simbolo
                )
            )

            resultado.pop(
                "componentes_regimen",
                None,
            )

            resultados.append(
                resultado
            )

        except Exception as error:
            errores.append(
                (
                    simbolo,
                    str(error),
                )
            )

            print(
                f"  ERROR: {error}"
            )

    if not resultados:
        raise RuntimeError(
            "No se pudo analizar ningún activo."
        )

    datos = pd.DataFrame(
        resultados
    )

    if errores:
        print()
        print(
            "Activos con error:"
        )

        for simbolo, error in errores:
            print(
                f"  {simbolo}: {error}"
            )

    return datos


def construir_score_relativo(
    datos: pd.DataFrame,
) -> pd.DataFrame:
    """Construye el ranking cuantitativo relativo."""

    resultado = datos.copy()

    variables = [
        "score_regimen",
        "retorno_20d",
        "retorno_60d",
        "sharpe60",
        "vol20",
        "drawdown_actual",
    ]

    for variable in variables:
        if variable not in resultado.columns:
            resultado[
                variable
            ] = np.nan

    z_regimen = normalizar_serie(
        resultado[
            "score_regimen"
        ]
    )

    z_ret20 = normalizar_serie(
        resultado[
            "retorno_20d"
        ]
    )

    z_ret60 = normalizar_serie(
        resultado[
            "retorno_60d"
        ]
    )

    z_sharpe60 = normalizar_serie(
        resultado[
            "sharpe60"
        ]
    )

    z_vol20 = normalizar_serie(
        resultado[
            "vol20"
        ]
    )

    z_drawdown = normalizar_serie(
        resultado[
            "drawdown_actual"
        ]
    )

    resultado[
        "score_relativo"
    ] = (
        0.30 * z_regimen
        + 0.15 * z_ret20
        + 0.20 * z_ret60
        + 0.15 * z_sharpe60
        - 0.10 * z_vol20
        + 0.10 * z_drawdown
    )

    resultado[
        "ranking"
    ] = (
        resultado[
            "score_relativo"
        ]
        .rank(
            ascending=False,
            method="min",
        )
        .astype(int)
    )

    return resultado


def clasificar_fuerza_relativa(
    datos: pd.DataFrame,
) -> pd.DataFrame:
    """Clasifica los activos según su posición relativa."""

    resultado = datos.copy()

    percentil = (
        resultado[
            "score_relativo"
        ]
        .rank(
            pct=True
        )
    )

    resultado[
        "fuerza_relativa"
    ] = np.select(
        [
            percentil >= 0.80,
            percentil >= 0.60,
            percentil <= 0.20,
            percentil <= 0.40,
        ],
        [
            "MUY_FUERTE",
            "FUERTE",
            "MUY_DEBIL",
            "DEBIL",
        ],
        default="NEUTRAL",
    )

    return resultado


def ordenar_resultados(
    datos: pd.DataFrame,
) -> pd.DataFrame:
    """Ordena los resultados por ranking."""

    columnas_preferidas = [
        "ranking",
        "simbolo",
        "clase",
        "mercado",
        "benchmark",
        "precio",
        "regimen_global",
        "score_regimen",
        "confianza_regimen",
        "score_relativo",
        "fuerza_relativa",
        "retorno_20d",
        "retorno_60d",
        "vol20",
        "vol60",
        "sharpe20",
        "sharpe60",
        "drawdown_actual",
        "beta60",
        "correlacion60",
        "fecha",
    ]

    columnas_existentes = [
        columna
        for columna in columnas_preferidas
        if columna in datos.columns
    ]

    otras_columnas = [
        columna
        for columna in datos.columns
        if columna
        not in columnas_existentes
    ]

    resultado = datos[
        columnas_existentes
        + otras_columnas
    ].copy()

    return resultado.sort_values(
        by="ranking",
        ascending=True,
    ).reset_index(
        drop=True
    )


def guardar_resultados(
    datos: pd.DataFrame,
) -> tuple[Path, Path]:
    """Guarda resultados actualizados e históricos."""

    RUTA_RESULTADOS.mkdir(
        parents=True,
        exist_ok=True,
    )

    ruta_actual = (
        RUTA_RESULTADOS
        / "ranking_actual.csv"
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    ruta_historica = (
        RUTA_RESULTADOS
        / f"ranking_{timestamp}.csv"
    )

    datos.to_csv(
        ruta_actual,
        index=False,
    )

    datos.to_csv(
        ruta_historica,
        index=False,
    )

    return (
        ruta_actual,
        ruta_historica,
    )


def imprimir_ranking(
    datos: pd.DataFrame,
) -> None:
    """Muestra el ranking resumido en terminal."""

    print()
    print(
        "=" * 110
    )
    print(
        "COMPARADOR MULTI-ACTIVO UNIVERSAL"
    )
    print(
        "=" * 110
    )

    for _, fila in datos.iterrows():
        print(
            f"{int(fila['ranking']):>2}. "
            f"{fila['simbolo']:<12} | "
            f"{fila['clase']:<10} | "
            f"{fila['regimen_global']:<17} | "
            f"Reg: {fila['score_regimen']:+.3f} | "
            f"Rel: {fila['score_relativo']:+.3f} | "
            f"{fila['fuerza_relativa']:<10} | "
            f"20D: {fila['retorno_20d'] * 100:+6.2f}% | "
            f"60D: {fila['retorno_60d'] * 100:+6.2f}%"
        )


def main() -> None:
    """Ejecuta el comparador universal."""

    if len(sys.argv) < 2:
        raise SystemExit(
            "Uso: python -m "
            "motor_mercado.comparador_universal "
            "ACTIVO1 ACTIVO2 ..."
        )

    simbolos = sys.argv[
        1:
    ]

    datos = analizar_universo(
        simbolos
    )

    datos = construir_score_relativo(
        datos
    )

    datos = clasificar_fuerza_relativa(
        datos
    )

    datos = ordenar_resultados(
        datos
    )

    imprimir_ranking(
        datos
    )

    ruta_actual, ruta_historica = (
        guardar_resultados(
            datos
        )
    )

    print()
    print(
        f"Ranking actual : {ruta_actual}"
    )

    print(
        f"Histórico      : {ruta_historica}"
    )


if __name__ == "__main__":
    main()