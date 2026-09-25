from __future__ import annotations

import numpy as np
import pandas as pd


def preparar_snapshot(
    datos: pd.DataFrame,
) -> pd.DataFrame:
    """Prepara un snapshot para comparación."""

    resultado = datos.copy()

    resultado[
        "contract_symbol"
    ] = resultado[
        "contract_symbol"
    ].astype(str)

    numericas = [
        "volumen",
        "open_interest",
        "bid",
        "ask",
        "ultimo",
        "iv",
    ]

    for columna in numericas:
        resultado[
            columna
        ] = pd.to_numeric(
            resultado[
                columna
            ],
            errors="coerce",
        ).fillna(0)

    return resultado


def comparar_snapshots(
    anterior: pd.DataFrame,
    actual: pd.DataFrame,
) -> pd.DataFrame:
    """Compara dos snapshots de opciones."""

    anterior = preparar_snapshot(
        anterior
    )

    actual = preparar_snapshot(
        actual
    )

    columnas_previas = [
        "contract_symbol",
        "volumen",
        "open_interest",
        "iv",
    ]

    previo = anterior[
        columnas_previas
    ].rename(
        columns={
            "volumen": "volumen_previo",
            "open_interest": "oi_previo",
            "iv": "iv_previa",
        }
    )

    resultado = actual.merge(
        previo,
        on="contract_symbol",
        how="left",
    )

    resultado[
        "volumen_previo"
    ] = resultado[
        "volumen_previo"
    ].fillna(0)

    resultado[
        "oi_previo"
    ] = resultado[
        "oi_previo"
    ].fillna(0)

    resultado[
        "iv_previa"
    ] = resultado[
        "iv_previa"
    ].fillna(
        resultado[
            "iv"
        ]
    )

    resultado[
        "delta_volumen"
    ] = np.maximum(
        resultado[
            "volumen"
        ]
        - resultado[
            "volumen_previo"
        ],
        0,
    )

    resultado[
        "delta_oi"
    ] = (
        resultado[
            "open_interest"
        ]
        - resultado[
            "oi_previo"
        ]
    )

    resultado[
        "delta_iv"
    ] = (
        resultado[
            "iv"
        ]
        - resultado[
            "iv_previa"
        ]
    )

    resultado[
        "mid"
    ] = (
        resultado[
            "bid"
        ]
        + resultado[
            "ask"
        ]
    ) / 2.0

    resultado[
        "premium_nuevo"
    ] = (
        resultado[
            "mid"
        ]
        * resultado[
            "delta_volumen"
        ]
        * 100.0
    )

    tolerancia = np.maximum(
        resultado[
            "ask"
        ]
        - resultado[
            "bid"
        ],
        0.01,
    ) * 0.20

    resultado[
        "ejecucion_proxy"
    ] = np.select(
        [
            resultado[
                "ultimo"
            ]
            >= (
                resultado[
                    "ask"
                ]
                - tolerancia
            ),
            resultado[
                "ultimo"
            ]
            <= (
                resultado[
                    "bid"
                ]
                + tolerancia
            ),
        ],
        [
            "BUY",
            "SELL",
        ],
        default="MID",
    )

    return resultado


def resumir_flow(
    flujo: pd.DataFrame,
) -> dict[str, float | str]:
    """Resume el flow direccional estimado."""

    premium_alcista = 0.0
    premium_bajista = 0.0

    for _, fila in flujo.iterrows():
        premium = float(
            fila[
                "premium_nuevo"
            ]
        )

        tipo = str(
            fila[
                "tipo_opcion"
            ]
        ).upper()

        ejecucion = str(
            fila[
                "ejecucion_proxy"
            ]
        ).upper()

        if tipo == "CALL":
            if ejecucion == "BUY":
                premium_alcista += premium

            elif ejecucion == "SELL":
                premium_bajista += premium

        elif tipo == "PUT":
            if ejecucion == "BUY":
                premium_bajista += premium

            elif ejecucion == "SELL":
                premium_alcista += premium

    total = (
        premium_alcista
        + premium_bajista
    )

    balance = (
        (
            premium_alcista
            - premium_bajista
        )
        / total
        if total > 0
        else 0.0
    )

    if balance >= 0.25:
        estado = "ALCISTA"

    elif balance <= -0.25:
        estado = "BAJISTA"

    else:
        estado = "MIXTO"

    return {
        "premium_alcista": premium_alcista,
        "premium_bajista": premium_bajista,
        "balance": balance,
        "estado": estado,
        "nuevo_volumen": float(
            flujo[
                "delta_volumen"
            ].sum()
        ),
        "delta_oi": float(
            flujo[
                "delta_oi"
            ].sum()
        ),
    }