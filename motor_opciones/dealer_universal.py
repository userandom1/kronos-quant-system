from __future__ import annotations

import numpy as np
import pandas as pd


def signo_dealer(
    tipo_opcion: pd.Series,
) -> np.ndarray:
    """
    Proxy estructural de posicionamiento dealer.

    CALL -> dealer short.
    PUT  -> dealer long.
    """

    tipo = (
        tipo_opcion
        .astype(str)
        .str.upper()
    )

    return np.where(
        tipo == "CALL",
        -1.0,
        1.0,
    )


def calcular_exposiciones_dealer(
    cadena: pd.DataFrame,
    spot: float,
) -> pd.DataFrame:
    """Calcula exposiciones dealer universales."""

    resultado = cadena.copy()

    oi = pd.to_numeric(
        resultado[
            "open_interest"
        ],
        errors="coerce",
    ).fillna(0)

    signo = signo_dealer(
        resultado[
            "tipo_opcion"
        ]
    )

    multiplicador = 100.0

    resultado[
        "dealer_sign"
    ] = signo

    resultado[
        "dex"
    ] = (
        signo
        * resultado["delta"]
        * oi
        * multiplicador
        * spot
    )

    resultado[
        "gex_1pct"
    ] = (
        signo
        * resultado["gamma"]
        * oi
        * multiplicador
        * spot**2
        * 0.01
    )

    resultado[
        "vega_exposure_1pt"
    ] = (
        signo
        * resultado["vega_1pt"]
        * oi
        * multiplicador
    )

    resultado[
        "vanna_exposure_1pt"
    ] = (
        signo
        * resultado["vanna_1pt"]
        * oi
        * multiplicador
        * spot
    )

    resultado[
        "charm_exposure_dia"
    ] = (
        signo
        * resultado["charm_dia"]
        * oi
        * multiplicador
        * spot
    )

    return resultado


def calcular_niveles_dealer(cadena: pd.DataFrame) -> dict[str, float | None]:
    """Walls: máximo OI agregado por strike y tipo; nodos respetan su signo."""
    if cadena.empty:
        raise ValueError("No existen contratos válidos para calcular dealer.")
    por_strike = cadena.groupby("strike")["gex_1pct"].sum()
    positivos = por_strike[por_strike > 0]
    negativos = por_strike[por_strike < 0]

    def wall(tipo: str) -> float | None:
        lado = cadena[cadena["tipo_opcion"].str.upper() == tipo]
        oi = lado.groupby("strike")["open_interest"].sum()
        return float(oi.idxmax()) if not oi.empty and oi.max() > 0 else None

    return {
        "gamma_node_positivo": float(positivos.idxmax()) if not positivos.empty else None,
        "gamma_node_negativo": float(negativos.idxmin()) if not negativos.empty else None,
        "call_wall": wall("CALL"),
        "put_wall": wall("PUT"),
    }


def resumir_dealer(
    cadena: pd.DataFrame,
) -> dict[str, float | None]:
    """Resume las exposiciones estructurales."""

    niveles = calcular_niveles_dealer(
        cadena
    )

    return {
        "net_gex_1pct": float(
            cadena[
                "gex_1pct"
            ].sum()
        ),
        "net_dex": float(
            cadena[
                "dex"
            ].sum()
        ),
        "net_vega_1pt": float(
            cadena[
                "vega_exposure_1pt"
            ].sum()
        ),
        "net_vanna_1pt": float(
            cadena[
                "vanna_exposure_1pt"
            ].sum()
        ),
        "net_charm_dia": float(
            cadena[
                "charm_exposure_dia"
            ].sum()
        ),
        **niveles,
    }