from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from motor_validacion.composite_v2 import (
    construir_senales_v2,
)
from motor_validacion.historico_senales import (
    UNIVERSO,
    descargar_precios,
)


RUTA_BASE = Path(__file__).resolve().parents[1]

RUTA_RESULTADOS = (
    RUTA_BASE
    / "resultados"
    / "senales_v2"
)


def clasificar_senal(
    valor: float,
) -> str:
    """Clasifica una señal cuantitativa."""

    if not np.isfinite(valor):
        return "NO_DISPONIBLE"

    if valor >= 1.0:
        return "FORTALEZA_ALTA"

    if valor >= 0.35:
        return "FORTALEZA"

    if valor <= -1.0:
        return "DEBILIDAD_ALTA"

    if valor <= -0.35:
        return "DEBILIDAD"

    return "NEUTRAL"


def construir_senales_actuales(
    precios: pd.DataFrame,
) -> pd.DataFrame:
    """Construye las señales oficiales V2 actuales."""

    senales = construir_senales_v2(
        precios
    )

    momentum = senales[
        "MOMENTUM"
    ]

    composite_60d = senales[
        "COMPOSITE_V2_60D"
    ]

    fecha = precios.index[-1]

    filas = []

    for ticker in precios.columns:
        signal_20d = float(
            momentum.loc[
                fecha,
                ticker,
            ]
        )

        signal_60d = float(
            composite_60d.loc[
                fecha,
                ticker,
            ]
        )

        filas.append(
            {
                "fecha": fecha,
                "ticker": ticker,
                "signal_20d": signal_20d,
                "signal_60d": signal_60d,
                "estado_20d": clasificar_senal(
                    signal_20d
                ),
                "estado_60d": clasificar_senal(
                    signal_60d
                ),
            }
        )

    return pd.DataFrame(
        filas
    )


def añadir_ranking(
    datos: pd.DataFrame,
) -> pd.DataFrame:
    """Añade rankings relativos por horizonte."""

    datos = datos.copy()

    datos[
        "ranking_20d"
    ] = datos[
        "signal_20d"
    ].rank(
        ascending=False,
        method="min",
    )

    datos[
        "ranking_60d"
    ] = datos[
        "signal_60d"
    ].rank(
        ascending=False,
        method="min",
    )

    return datos


def imprimir_resultados(
    datos: pd.DataFrame,
) -> None:
    """Muestra las señales oficiales."""

    salida = datos[
        [
            "ticker",
            "signal_20d",
            "ranking_20d",
            "estado_20d",
            "signal_60d",
            "ranking_60d",
            "estado_60d",
        ]
    ].sort_values(
        "ranking_60d"
    )

    print()
    print("=" * 105)
    print(
        "SEÑALES OFICIALES V2"
    )
    print("=" * 105)

    print(
        salida.to_string(
            index=False,
            float_format=lambda x: (
                f"{x:,.4f}"
            ),
        )
    )


def main() -> None:
    """Genera las señales oficiales V2."""

    RUTA_RESULTADOS.mkdir(
        parents=True,
        exist_ok=True,
    )

    print(
        "Descargando histórico..."
    )

    precios = descargar_precios(
        UNIVERSO,
        periodo="10y",
    )

    print(
        "Construyendo señales V2..."
    )

    datos = construir_senales_actuales(
        precios
    )

    datos = añadir_ranking(
        datos
    )

    ruta = (
        RUTA_RESULTADOS
        / "senales_v2.csv"
    )

    datos.to_csv(
        ruta,
        index=False,
    )

    imprimir_resultados(
        datos
    )

    print()
    print(
        f"Guardado en: {ruta}"
    )


if __name__ == "__main__":
    main()