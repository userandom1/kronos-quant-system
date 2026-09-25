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


def calcular_niveles_dealer(
    cadena: pd.DataFrame,
) -> dict[str, float]:
    """Calcula nodos principales por strike."""

    por_strike = (
        cadena
        .groupby(
            "strike",
            as_index=False,
        )
        .agg(
            gex_1pct=(
                "gex_1pct",
                "sum",
            ),
            dex=(
                "dex",
                "sum",
            ),
            open_interest=(
                "open_interest",
                "sum",
            ),
        )
    )

    positivo = por_strike.loc[
        por_strike[
            "gex_1pct"
        ].idxmax()
    ]

    negativo = por_strike.loc[
        por_strike[
            "gex_1pct"
        ].idxmin()
    ]

    calls = cadena[
        cadena[
            "tipo_opcion"
        ] == "CALL"
    ]

    puts = cadena[
        cadena[
            "tipo_opcion"
        ] == "PUT"
    ]

    call_wall = float(
        calls.loc[
            calls[
                "open_interest"
            ].idxmax(),
            "strike",
        ]
    )

    put_wall = float(
        puts.loc[
            puts[
                "open_interest"
            ].idxmax(),
            "strike",
        ]
    )

    return {
        "gamma_node_positivo": float(
            positivo["strike"]
        ),
        "gamma_node_negativo": float(
            negativo["strike"]
        ),
        "call_wall": call_wall,
        "put_wall": put_wall,
    }


def resumir_dealer(
    cadena: pd.DataFrame,
) -> dict[str, float]:
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