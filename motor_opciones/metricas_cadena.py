from __future__ import annotations

import numpy as np
import pandas as pd


def sumar_seguro(
    serie: pd.Series,
) -> float:
    """Suma una serie numérica ignorando valores inválidos."""

    valores = pd.to_numeric(
        serie,
        errors="coerce",
    )

    return float(
        valores.fillna(0).sum()
    )


def media_ponderada(
    valores: pd.Series,
    pesos: pd.Series,
) -> float:
    """Calcula una media ponderada defensiva."""

    valores = pd.to_numeric(
        valores,
        errors="coerce",
    )

    pesos = pd.to_numeric(
        pesos,
        errors="coerce",
    ).fillna(0)

    mascara = (
        valores.notna()
        & pesos.notna()
        & (pesos > 0)
    )

    if not mascara.any():
        return np.nan

    return float(
        np.average(
            valores[mascara],
            weights=pesos[mascara],
        )
    )


def resumir_cadena(
    cadena: pd.DataFrame,
) -> dict[str, float | int]:
    """Calcula métricas agregadas de la cadena."""

    calls = cadena[
        cadena["tipo_opcion"] == "CALL"
    ]

    puts = cadena[
        cadena["tipo_opcion"] == "PUT"
    ]

    volumen_calls = sumar_seguro(
        calls["volumen"]
    )

    volumen_puts = sumar_seguro(
        puts["volumen"]
    )

    oi_calls = sumar_seguro(
        calls["open_interest"]
    )

    oi_puts = sumar_seguro(
        puts["open_interest"]
    )

    premium_calls = sumar_seguro(
        calls["premium_proxy"]
    )

    premium_puts = sumar_seguro(
        puts["premium_proxy"]
    )

    put_call_volumen = (
        volumen_puts / volumen_calls
        if volumen_calls > 0
        else np.nan
    )

    put_call_oi = (
        oi_puts / oi_calls
        if oi_calls > 0
        else np.nan
    )

    return {
        "contratos": int(
            len(cadena)
        ),
        "calls": int(
            len(calls)
        ),
        "puts": int(
            len(puts)
        ),
        "volumen_total": int(
            volumen_calls
            + volumen_puts
        ),
        "volumen_calls": int(
            volumen_calls
        ),
        "volumen_puts": int(
            volumen_puts
        ),
        "oi_total": int(
            oi_calls
            + oi_puts
        ),
        "oi_calls": int(
            oi_calls
        ),
        "oi_puts": int(
            oi_puts
        ),
        "put_call_volumen": float(
            put_call_volumen
        ),
        "put_call_oi": float(
            put_call_oi
        ),
        "premium_calls": premium_calls,
        "premium_puts": premium_puts,
        "premium_total": (
            premium_calls
            + premium_puts
        ),
        "iv_media_calls": media_ponderada(
            calls["iv"],
            calls["open_interest"],
        ),
        "iv_media_puts": media_ponderada(
            puts["iv"],
            puts["open_interest"],
        ),
    }