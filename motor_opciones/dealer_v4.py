from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from motor_opciones.griegas import (
    ParametrosOpcion,
    delta,
    delta_decay_por_dia,
    gamma,
    vanna_por_punto,
)


RUTA_BASE = Path(__file__).resolve().parents[1]

RUTA_CADENA = (
    RUTA_BASE
    / "resultados"
    / "dealer_engine"
    / "QQQ"
    / "cadena_filtrada.csv"
)

RUTA_FLOW = (
    RUTA_BASE
    / "resultados"
    / "options_flow"
    / "QQQ"
    / "v2"
    / "options_flow_v2_contratos.csv"
)

RUTA_RESULTADOS = (
    RUTA_BASE
    / "resultados"
    / "dealer_engine"
    / "QQQ"
    / "v4"
)

MULTIPLICADOR = 100.0

TIPO_INTERES = 0.04
DIVIDENDO = 0.01

SHOCKS_SPOT_PCT = np.arange(
    -3.0,
    3.01,
    0.25,
)


def signo_dealer_estructural(
    tipo: str,
) -> float:
    """Convención proxy estructural basada en tipo de opción."""

    if tipo == "call":
        return -1.0

    return 1.0


def cargar_cadena() -> pd.DataFrame:
    """Carga la cadena estructural filtrada."""

    if not RUTA_CADENA.exists():
        raise FileNotFoundError(
            f"No existe: {RUTA_CADENA}"
        )

    datos = pd.read_csv(
        RUTA_CADENA
    )

    return datos


def cargar_flow() -> pd.DataFrame:
    """Carga Options Flow V2."""

    if not RUTA_FLOW.exists():
        raise FileNotFoundError(
            f"No existe: {RUTA_FLOW}"
        )

    return pd.read_csv(
        RUTA_FLOW
    )


def calcular_estado_estructural(
    cadena: pd.DataFrame,
    spot: float,
) -> dict[str, float]:
    """Recalcula exposiciones estructurales a un spot concreto."""

    gex = 0.0
    dex = 0.0
    vanna = 0.0
    charm = 0.0

    for fila in cadena.itertuples():

        dte = float(
            fila.dte
        )

        if dte <= 0:
            continue

        oi = float(
            fila.openInterest
        )

        if oi <= 0:
            continue

        iv = float(
            fila.impliedVolatility
        )

        if not np.isfinite(iv) or iv <= 0:
            continue

        parametros = ParametrosOpcion(
            spot=spot,
            strike=float(
                fila.strike
            ),
            tiempo=dte / 365.0,
            volatilidad=iv,
            tipo_interes=TIPO_INTERES,
            dividendo=DIVIDENDO,
            tipo=fila.tipo,
        )

        signo = signo_dealer_estructural(
            fila.tipo
        )

        delta_val = delta(
            parametros
        )

        gamma_val = gamma(
            parametros
        )

        vanna_val = vanna_por_punto(
            parametros
        )

        charm_val = delta_decay_por_dia(
            parametros
        )

        dex += (
            signo
            * delta_val
            * oi
            * MULTIPLICADOR
            * spot
        )

        gex += (
            signo
            * gamma_val
            * oi
            * MULTIPLICADOR
            * spot**2
            * 0.01
        )

        vanna += (
            signo
            * vanna_val
            * oi
            * MULTIPLICADOR
            * spot
        )

        charm += (
            signo
            * charm_val
            * oi
            * MULTIPLICADOR
            * spot
        )

    return {
        "spot": spot,
        "gex_estructural": gex,
        "dex_estructural": dex,
        "vanna_estructural": vanna,
        "charm_estructural": charm,
    }


def construir_perfil_estructural(
    cadena: pd.DataFrame,
) -> pd.DataFrame:
    """Construye perfil estructural por shocks de spot."""

    spot_base = float(
        cadena["spot"].iloc[0]
    )

    filas = []

    for shock in SHOCKS_SPOT_PCT:

        spot = (
            spot_base
            * (
                1.0
                + shock / 100.0
            )
        )

        estado = calcular_estado_estructural(
            cadena,
            spot,
        )

        estado[
            "shock_spot_pct"
        ] = shock

        filas.append(
            estado
        )

    return pd.DataFrame(
        filas
    )


def interpolar_flip(
    perfil: pd.DataFrame,
) -> float | None:
    """Busca el primer cruce de GEX estructural por cero."""

    datos = perfil.sort_values(
        "spot"
    )

    x = datos[
        "spot"
    ].to_numpy()

    y = datos[
        "gex_estructural"
    ].to_numpy()

    for i in range(
        len(datos) - 1
    ):

        if y[i] == 0:
            return float(
                x[i]
            )

        if (
            y[i] * y[i + 1]
            < 0
        ):
            peso = (
                -y[i]
                / (
                    y[i + 1]
                    - y[i]
                )
            )

            return float(
                x[i]
                + peso
                * (
                    x[i + 1]
                    - x[i]
                )
            )

    return None


def calcular_flow_dealer(
    flow: pd.DataFrame,
) -> pd.DataFrame:
    """
    Construye proxy dinámico dealer.

    Se interpreta como actividad, no como posicionamiento real confirmado.
    """

    datos = flow.copy()

    datos[
        "signo_flow_dealer"
    ] = -datos[
        "sesgo_numerico"
    ].fillna(0.0)

    datos[
        "delta_flow_proxy"
    ] = (
        datos[
            "signo_flow_dealer"
        ]
        * datos[
            "delta_t1"
        ].abs()
        * datos[
            "nuevo_volumen"
        ]
        * MULTIPLICADOR
        * datos[
            "spot_t1"
        ]
    )

    datos[
        "gamma_flow_proxy"
    ] = (
        datos[
            "signo_flow_dealer"
        ]
        * datos[
            "gamma_t1"
        ].abs()
        * datos[
            "nuevo_volumen"
        ]
        * MULTIPLICADOR
        * datos[
            "spot_t1"
        ] ** 2
        * 0.01
    )

    datos[
        "vanna_flow_proxy"
    ] = (
        datos[
            "signo_flow_dealer"
        ]
        * datos[
            "vanna_t1"
        ]
        * datos[
            "nuevo_volumen"
        ]
        * MULTIPLICADOR
        * datos[
            "spot_t1"
        ]
    )

    datos[
        "charm_flow_proxy"
    ] = (
        datos[
            "signo_flow_dealer"
        ]
        * datos[
            "delta_decay_t1"
        ]
        * datos[
            "nuevo_volumen"
        ]
        * MULTIPLICADOR
        * datos[
            "spot_t1"
        ]
    )

    return datos


def agregar_flow_por_strike(
    datos: pd.DataFrame,
) -> pd.DataFrame:
    """Agrega presión dinámica por strike."""

    return (
        datos.groupby(
            "strike_t1",
            as_index=False,
        )
        .agg(
            nuevo_volumen=(
                "nuevo_volumen",
                "sum",
            ),
            premium_nuevo=(
                "nuevo_premium_proxy",
                "sum",
            ),
            delta_flow=(
                "delta_flow_proxy",
                "sum",
            ),
            gamma_flow=(
                "gamma_flow_proxy",
                "sum",
            ),
            vanna_flow=(
                "vanna_flow_proxy",
                "sum",
            ),
            charm_flow=(
                "charm_flow_proxy",
                "sum",
            ),
        )
        .sort_values(
            "premium_nuevo",
            ascending=False,
        )
    )


def calcular_niveles(
    cadena: pd.DataFrame,
    flow_strike: pd.DataFrame,
) -> dict[str, float | None]:
    """Obtiene principales niveles estructurales y dinámicos."""

    cadena = cadena.copy()

    cadena[
        "signo_dealer"
    ] = cadena[
        "tipo"
    ].map(
        {
            "call": -1.0,
            "put": 1.0,
        }
    )

    cadena[
        "gex_contrato"
    ] = (
        cadena[
            "signo_dealer"
        ]
        * cadena[
            "gamma"
        ]
        * cadena[
            "openInterest"
        ]
        * MULTIPLICADOR
        * cadena[
            "spot"
        ] ** 2
        * 0.01
    )

    gex_strike = (
        cadena.groupby(
            "strike",
            as_index=False,
        )[
            "gex_contrato"
        ]
        .sum()
    )

    positivo = gex_strike[
        gex_strike[
            "gex_contrato"
        ] > 0
    ]

    negativo = gex_strike[
        gex_strike[
            "gex_contrato"
        ] < 0
    ]

    nodo_positivo = (
        float(
            positivo.loc[
                positivo[
                    "gex_contrato"
                ].idxmax(),
                "strike",
            ]
        )
        if not positivo.empty
        else None
    )

    nodo_negativo = (
        float(
            negativo.loc[
                negativo[
                    "gex_contrato"
                ].idxmin(),
                "strike",
            ]
        )
        if not negativo.empty
        else None
    )

    if flow_strike.empty:

        flow_gamma_max = None
        flow_premium_max = None

    else:

        flow_gamma_max = float(
            flow_strike.loc[
                flow_strike[
                    "gamma_flow"
                ].abs().idxmax(),
                "strike_t1",
            ]
        )

        flow_premium_max = float(
            flow_strike.loc[
                flow_strike[
                    "premium_nuevo"
                ].idxmax(),
                "strike_t1",
            ]
        )

    return {
        "gamma_node_positivo": nodo_positivo,
        "gamma_node_negativo": nodo_negativo,
        "flow_gamma_node": flow_gamma_max,
        "flow_premium_node": flow_premium_max,
    }


def construir_resumen(
    perfil: pd.DataFrame,
    flow: pd.DataFrame,
    niveles: dict,
) -> pd.DataFrame:
    """Construye resumen Dealer Engine V4."""

    base = perfil.iloc[
        (
            perfil[
                "shock_spot_pct"
            ].abs()
        ).argmin()
    ]

    flip = interpolar_flip(
        perfil
    )

    return pd.DataFrame(
        [
            {
                "spot": base[
                    "spot"
                ],
                "gex_estructural": base[
                    "gex_estructural"
                ],
                "dex_estructural": base[
                    "dex_estructural"
                ],
                "vanna_estructural": base[
                    "vanna_estructural"
                ],
                "charm_estructural": base[
                    "charm_estructural"
                ],
                "gamma_flip": flip,
                "delta_flow_proxy": flow[
                    "delta_flow_proxy"
                ].sum(),
                "gamma_flow_proxy": flow[
                    "gamma_flow_proxy"
                ].sum(),
                "vanna_flow_proxy": flow[
                    "vanna_flow_proxy"
                ].sum(),
                "charm_flow_proxy": flow[
                    "charm_flow_proxy"
                ].sum(),
                **niveles,
            }
        ]
    )