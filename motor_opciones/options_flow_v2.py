from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


RUTA_BASE = Path(__file__).resolve().parents[1]

RUTA_DINAMICO = (
    RUTA_BASE
    / "resultados"
    / "options_flow"
    / "QQQ"
    / "dinamico"
)

RUTA_RESULTADOS = (
    RUTA_BASE
    / "resultados"
    / "options_flow"
    / "QQQ"
    / "v2"
)


def obtener_ultima_comparacion() -> Path:
    """Obtiene la comparación dinámica más reciente."""

    archivos = sorted(
        RUTA_DINAMICO.glob(
            "comparacion_*.csv"
        )
    )

    if not archivos:
        raise FileNotFoundError(
            "No existen comparaciones dinámicas. "
            "Ejecuta primero monitor_flow."
        )

    return archivos[-1]


def cargar_datos() -> pd.DataFrame:
    """Carga la comparación dinámica más reciente."""

    ruta = obtener_ultima_comparacion()

    print(
        f"Comparación utilizada: {ruta.name}"
    )

    datos = pd.read_csv(
        ruta
    )

    return datos


def percentil(
    serie: pd.Series,
) -> pd.Series:
    """Convierte una serie en ranking percentil."""

    serie = pd.to_numeric(
        serie,
        errors="coerce",
    ).replace(
        [
            np.inf,
            -np.inf,
        ],
        np.nan,
    ).fillna(0.0)

    return serie.rank(
        pct=True
    )


def clasificar_ejecucion(
    posicion: float,
) -> str:
    """Clasifica la posición del último precio en el spread."""

    if not np.isfinite(
        posicion
    ):
        return "DESCONOCIDA"

    if posicion >= 0.75:
        return "ASK"

    if posicion <= 0.25:
        return "BID"

    return "MID"


def sesgo_proxy(
    tipo: str,
    ejecucion: str,
) -> int:
    """
    Construye un proxy direccional.

    +1 = presión alcista proxy
    -1 = presión bajista proxy
     0 = indeterminada
    """

    if ejecucion not in {
        "ASK",
        "BID",
    }:
        return 0

    if tipo == "call":
        return (
            1
            if ejecucion == "ASK"
            else -1
        )

    if tipo == "put":
        return (
            -1
            if ejecucion == "ASK"
            else 1
        )

    return 0


def etiqueta_sesgo(
    valor: int,
) -> str:
    """Convierte el sesgo numérico en etiqueta."""

    if valor > 0:
        return "ALCISTA_PROXY"

    if valor < 0:
        return "BAJISTA_PROXY"

    return "NEUTRAL"


def bucket_dte(
    dte: float,
) -> str:
    """Agrupa contratos por horizonte temporal."""

    if not np.isfinite(
        dte
    ):
        return "DESCONOCIDO"

    if dte <= 1:
        return "0_1DTE"

    if dte <= 7:
        return "2_7DTE"

    if dte <= 30:
        return "8_30DTE"

    if dte <= 90:
        return "31_90DTE"

    return "MAS_90DTE"


def preparar_flow(
    datos: pd.DataFrame,
) -> pd.DataFrame:
    """Construye las variables principales de Options Flow V2."""

    datos = datos.copy()

    datos = datos[
        datos[
            "nuevo_volumen"
        ].fillna(0.0)
        > 0
    ].copy()

    datos[
        "ejecucion_proxy"
    ] = datos[
        "posicion_ultimo_spread"
    ].apply(
        clasificar_ejecucion
    )

    datos[
        "sesgo_numerico"
    ] = [
        sesgo_proxy(
            tipo,
            ejecucion,
        )
        for tipo, ejecucion in zip(
            datos["tipo_t1"],
            datos[
                "ejecucion_proxy"
            ],
        )
    ]

    datos[
        "sesgo_proxy"
    ] = datos[
        "sesgo_numerico"
    ].apply(
        etiqueta_sesgo
    )

    datos[
        "premium_firmado_proxy"
    ] = (
        datos[
            "nuevo_premium_proxy"
        ].fillna(0.0)
        * datos[
            "sesgo_numerico"
        ]
    )

    datos[
        "delta_premium_proxy"
    ] = (
        datos[
            "nuevo_premium_proxy"
        ].fillna(0.0)
        * datos[
            "delta_t1"
        ].abs()
    )

    datos[
        "gamma_premium_proxy"
    ] = (
        datos[
            "nuevo_premium_proxy"
        ].fillna(0.0)
        * datos[
            "gamma_t1"
        ].abs()
    )

    datos[
        "bucket_dte"
    ] = datos[
        "dte_t1"
    ].apply(
        bucket_dte
    )

    return datos


def calcular_score(
    datos: pd.DataFrame,
) -> pd.DataFrame:
    """Calcula el Flow Score V2."""

    datos = datos.copy()

    score_volumen = percentil(
        datos[
            "nuevo_volumen"
        ]
    )

    score_premium = percentil(
        datos[
            "nuevo_premium_proxy"
        ]
    )

    score_iv = percentil(
        datos[
            "delta_iv_puntos"
        ].abs()
    )

    score_gex = percentil(
        datos[
            "delta_gex_proxy"
        ].abs()
    )

    score_delta = percentil(
        datos[
            "delta_premium_proxy"
        ]
    )

    certeza_ejecucion = np.where(
        datos[
            "ejecucion_proxy"
        ].isin(
            [
                "ASK",
                "BID",
            ]
        ),
        1.0,
        0.40,
    )

    datos[
        "flow_score_v2"
    ] = (
        0.25 * score_volumen
        + 0.25 * score_premium
        + 0.15 * score_iv
        + 0.15 * score_gex
        + 0.15 * score_delta
        + 0.05 * certeza_ejecucion
    ) * 100.0

    datos[
        "conviccion_proxy"
    ] = (
        datos[
            "flow_score_v2"
        ]
        * np.where(
            datos[
                "sesgo_numerico"
            ] != 0,
            1.0,
            0.50,
        )
    )

    return datos


def agregar_por_strike(
    datos: pd.DataFrame,
) -> pd.DataFrame:
    """Agrega flow por strike."""

    salida = (
        datos.groupby(
            "strike_t1",
            as_index=False,
        )
        .agg(
            nuevo_volumen=(
                "nuevo_volumen",
                "sum",
            ),
            nuevo_premium=(
                "nuevo_premium_proxy",
                "sum",
            ),
            premium_firmado=(
                "premium_firmado_proxy",
                "sum",
            ),
            delta_gex=(
                "delta_gex_proxy",
                "sum",
            ),
            delta_vanna=(
                "delta_vanna_proxy",
                "sum",
            ),
            delta_charm=(
                "delta_charm_proxy",
                "sum",
            ),
            score_medio=(
                "flow_score_v2",
                "mean",
            ),
        )
    )

    return salida.sort_values(
        "nuevo_premium",
        ascending=False,
    )


def agregar_por_vencimiento(
    datos: pd.DataFrame,
) -> pd.DataFrame:
    """Agrega flow por vencimiento."""

    return (
        datos.groupby(
            [
                "vencimiento_t1",
                "bucket_dte",
            ],
            as_index=False,
        )
        .agg(
            nuevo_volumen=(
                "nuevo_volumen",
                "sum",
            ),
            nuevo_premium=(
                "nuevo_premium_proxy",
                "sum",
            ),
            premium_firmado=(
                "premium_firmado_proxy",
                "sum",
            ),
            delta_gex=(
                "delta_gex_proxy",
                "sum",
            ),
            score_medio=(
                "flow_score_v2",
                "mean",
            ),
        )
        .sort_values(
            "nuevo_premium",
            ascending=False,
        )
    )


def construir_resumen(
    datos: pd.DataFrame,
) -> pd.DataFrame:
    """Construye resumen global de flow."""

    alcista = datos[
        datos[
            "sesgo_numerico"
        ] > 0
    ]

    bajista = datos[
        datos[
            "sesgo_numerico"
        ] < 0
    ]

    neutral = datos[
        datos[
            "sesgo_numerico"
        ] == 0
    ]

    premium_alcista = (
        alcista[
            "nuevo_premium_proxy"
        ].sum()
    )

    premium_bajista = (
        bajista[
            "nuevo_premium_proxy"
        ].sum()
    )

    premium_total = (
        datos[
            "nuevo_premium_proxy"
        ].sum()
    )

    balance = (
        (
            premium_alcista
            - premium_bajista
        )
        / premium_total
        if premium_total > 0
        else 0.0
    )

    if balance >= 0.20:
        estado = "PRESION_ALCISTA_PROXY"

    elif balance <= -0.20:
        estado = "PRESION_BAJISTA_PROXY"

    else:
        estado = "FLUJO_MIXTO"

    return pd.DataFrame(
        [
            {
                "contratos_activos": (
                    len(datos)
                ),
                "nuevo_volumen": (
                    datos[
                        "nuevo_volumen"
                    ].sum()
                ),
                "premium_nuevo": (
                    premium_total
                ),
                "premium_alcista_proxy": (
                    premium_alcista
                ),
                "premium_bajista_proxy": (
                    premium_bajista
                ),
                "premium_neutral": (
                    neutral[
                        "nuevo_premium_proxy"
                    ].sum()
                ),
                "balance_flow_proxy": (
                    balance
                ),
                "estado_flow": estado,
                "delta_gex_total": (
                    datos[
                        "delta_gex_proxy"
                    ].sum()
                ),
                "delta_vanna_total": (
                    datos[
                        "delta_vanna_proxy"
                    ].sum()
                ),
                "delta_charm_total": (
                    datos[
                        "delta_charm_proxy"
                    ].sum()
                ),
            }
        ]
    )