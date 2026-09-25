from __future__ import annotations

import numpy as np
import pandas as pd


def seleccionar_mejor_modelo(
    benchmark: pd.DataFrame,
) -> str:
    """Selecciona modelo usando error y dirección."""

    datos = benchmark.copy()

    datos = datos[
        np.isfinite(
            datos[
                "rmse_retorno"
            ]
        )
    ].copy()

    if datos.empty:
        raise RuntimeError(
            "No existen modelos válidos."
        )

    datos = datos.sort_values(
        by=[
            "rmse_retorno",
            "direccion_acertada",
        ],
        ascending=[
            True,
            False,
        ],
    )

    return str(
        datos.iloc[
            0
        ][
            "modelo"
        ]
    )


def calcular_pesos_modelos(
    benchmark: pd.DataFrame,
) -> dict[str, float]:
    """Calcula pesos por inversa del RMSE."""

    datos = benchmark.copy()

    datos = datos[
        np.isfinite(
            datos[
                "rmse_retorno"
            ]
        )
        & (
            datos[
                "rmse_retorno"
            ]
            > 0
        )
    ].copy()

    if datos.empty:
        raise RuntimeError(
            "No pueden calcularse pesos."
        )

    inverso = (
        1.0
        / datos[
            "rmse_retorno"
        ]
    )

    pesos = (
        inverso
        / inverso.sum()
    )

    return {
        str(modelo): float(
            peso
        )
        for modelo, peso in zip(
            datos[
                "modelo"
            ],
            pesos,
            strict=True,
        )
    }