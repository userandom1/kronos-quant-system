from pathlib import Path

import numpy as np
import pandas as pd


RUTA_BASE = Path(__file__).resolve().parents[1]

RUTA_SNAPSHOTS = (
    RUTA_BASE
    / "resultados"
    / "options_flow"
    / "QQQ"
    / "snapshots"
)

RUTA_RESULTADOS = (
    RUTA_BASE
    / "resultados"
    / "options_flow"
    / "QQQ"
    / "dinamico"
)

MULTIPLICADOR = 100.0


def obtener_snapshots() -> list[Path]:
    """Obtiene snapshots ordenados cronológicamente."""

    archivos = sorted(
        RUTA_SNAPSHOTS.glob(
            "snapshot_*.csv"
        )
    )

    return archivos


def cargar_snapshot(
    ruta: Path,
) -> pd.DataFrame:
    """Carga y normaliza un snapshot."""

    datos = pd.read_csv(
        ruta
    )

    numericas = [
        "spot",
        "strike",
        "bid",
        "ask",
        "mid",
        "lastPrice",
        "volume",
        "openInterest",
        "impliedVolatility",
        "delta",
        "gamma",
        "vanna",
        "delta_decay",
    ]

    for columna in numericas:
        if columna in datos.columns:
            datos[columna] = pd.to_numeric(
                datos[columna],
                errors="coerce",
            )

    return datos


def signo_dealer(
    tipo: str,
) -> float:
    """Aplica la convención proxy actual de posicionamiento dealer."""

    if tipo == "call":
        return -1.0

    return 1.0


def calcular_exposiciones(
    datos: pd.DataFrame,
) -> pd.DataFrame:
    """Calcula proxies de exposición por contrato."""

    datos = datos.copy()

    signos = datos[
        "tipo"
    ].map(
        {
            "call": -1.0,
            "put": 1.0,
        }
    )

    oi = datos[
        "openInterest"
    ].fillna(0.0)

    spot = datos[
        "spot"
    ]

    datos["gex_proxy"] = (
        signos
        * datos["gamma"]
        * oi
        * MULTIPLICADOR
        * spot.pow(2)
        * 0.01
    )

    datos["vanna_proxy"] = (
        signos
        * (
            datos["vanna"]
            / 100.0
        )
        * oi
        * MULTIPLICADOR
        * spot
    )

    datos["charm_proxy"] = (
        signos
        * (
            datos["delta_decay"]
            / 365.0
        )
        * oi
        * MULTIPLICADOR
        * spot
    )

    return datos


def comparar(
    anterior: pd.DataFrame,
    actual: pd.DataFrame,
) -> pd.DataFrame:
    """Compara dos snapshots contrato a contrato."""

    anterior = calcular_exposiciones(
        anterior
    )

    actual = calcular_exposiciones(
        actual
    )

    columnas = [
        "contractSymbol",
        "tipo",
        "vencimiento",
        "dte",
        "strike",
        "spot",
        "bid",
        "ask",
        "mid",
        "lastPrice",
        "volume",
        "openInterest",
        "impliedVolatility",
        "delta",
        "gamma",
        "vanna",
        "delta_decay",
        "gex_proxy",
        "vanna_proxy",
        "charm_proxy",
    ]

    anterior = anterior[
        columnas
    ]

    actual = actual[
        columnas
    ]

    combinado = anterior.merge(
        actual,
        on="contractSymbol",
        how="outer",
        suffixes=(
            "_t0",
            "_t1",
        ),
        indicator=True,
    )

    combinado["estado_contrato"] = (
        combinado["_merge"]
        .map(
            {
                "both": "EXISTENTE",
                "left_only": "DESAPARECIDO",
                "right_only": "NUEVO",
            }
        )
    )

    combinado["delta_volume"] = (
        combinado["volume_t1"]
        - combinado["volume_t0"]
    )

    combinado[
        "nuevo_volumen"
    ] = combinado[
        "delta_volume"
    ].clip(
        lower=0.0
    )

    combinado["delta_oi"] = (
        combinado["openInterest_t1"]
        - combinado["openInterest_t0"]
    )

    combinado[
        "delta_iv_puntos"
    ] = (
        combinado[
            "impliedVolatility_t1"
        ]
        - combinado[
            "impliedVolatility_t0"
        ]
    ) * 100.0

    combinado[
        "delta_mid"
    ] = (
        combinado["mid_t1"]
        - combinado["mid_t0"]
    )

    combinado[
        "delta_mid_pct"
    ] = np.where(
        combinado["mid_t0"] > 0,
        combinado["delta_mid"]
        / combinado["mid_t0"]
        * 100.0,
        np.nan,
    )

    combinado[
        "nuevo_premium_proxy"
    ] = (
        combinado[
            "nuevo_volumen"
        ]
        * combinado["mid_t1"]
        * MULTIPLICADOR
    )

    combinado[
        "delta_gex_proxy"
    ] = (
        combinado["gex_proxy_t1"]
        - combinado["gex_proxy_t0"]
    )

    combinado[
        "delta_vanna_proxy"
    ] = (
        combinado["vanna_proxy_t1"]
        - combinado["vanna_proxy_t0"]
    )

    combinado[
        "delta_charm_proxy"
    ] = (
        combinado["charm_proxy_t1"]
        - combinado["charm_proxy_t0"]
    )

    spread = (
        combinado["ask_t1"]
        - combinado["bid_t1"]
    )

    combinado[
        "posicion_ultimo_spread"
    ] = np.where(
        spread > 0,
        (
            combinado["lastPrice_t1"]
            - combinado["bid_t1"]
        )
        / spread,
        np.nan,
    )

    combinado[
        "posicion_ultimo_spread"
    ] = combinado[
        "posicion_ultimo_spread"
    ].clip(
        0.0,
        1.0,
    )

    return combinado


def percentil(
    serie: pd.Series,
) -> pd.Series:
    """Convierte una métrica en rango percentil."""

    serie = (
        serie
        .replace(
            [
                np.inf,
                -np.inf,
            ],
            np.nan,
        )
        .fillna(0.0)
    )

    return serie.rank(
        pct=True
    )


def calcular_score(
    datos: pd.DataFrame,
) -> pd.DataFrame:
    """Calcula el score de nuevo flujo observado."""

    datos = datos.copy()

    score_volumen = percentil(
        datos["nuevo_volumen"]
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

    datos[
        "flow_dinamico_score"
    ] = (
        0.35 * score_volumen
        + 0.35 * score_premium
        + 0.15 * score_iv
        + 0.15 * score_gex
    ) * 100.0

    return datos


def clasificar_eventos(
    datos: pd.DataFrame,
) -> pd.DataFrame:
    """Añade etiquetas descriptivas de cambios observados."""

    datos = datos.copy()

    condiciones = [
        datos["nuevo_volumen"] >= 5000,
        datos["nuevo_volumen"] >= 1000,
        datos["nuevo_volumen"] >= 250,
    ]

    etiquetas = [
        "VOLUMEN_MUY_ALTO",
        "VOLUMEN_ALTO",
        "VOLUMEN_ACTIVO",
    ]

    datos[
        "evento_volumen"
    ] = np.select(
        condiciones,
        etiquetas,
        default="NORMAL",
    )

    datos[
        "evento_iv"
    ] = np.select(
        [
            datos[
                "delta_iv_puntos"
            ] >= 2.0,
            datos[
                "delta_iv_puntos"
            ] <= -2.0,
        ],
        [
            "IV_EXPANSION",
            "IV_COMPRESION",
        ],
        default="IV_ESTABLE",
    )

    datos[
        "evento_gamma"
    ] = np.where(
        datos[
            "delta_gex_proxy"
        ] >= 0,
        "GEX_SUBE",
        "GEX_BAJA",
    )

    return datos


def imprimir_resumen(
    datos: pd.DataFrame,
) -> None:
    """Muestra el nuevo flow más relevante."""

    activos = datos[
        datos["nuevo_volumen"] > 0
    ].copy()

    activos = activos.sort_values(
        "flow_dinamico_score",
        ascending=False,
    )

    print()
    print("=" * 110)
    print("OPTIONS FLOW DINÁMICO - QQQ")
    print("=" * 110)

    print(
        f"Contratos con nuevo volumen : "
        f"{len(activos):,}"
    )

    print(
        f"Nuevo volumen total         : "
        f"{activos['nuevo_volumen'].sum():,.0f}"
    )

    print(
        f"Nuevo premium proxy         : "
        f"${activos['nuevo_premium_proxy'].sum():,.0f}"
    )

    print()
    print("TOP NUEVO FLOW")
    print("-" * 110)

    columnas = [
        "contractSymbol",
        "tipo_t1",
        "strike_t1",
        "nuevo_volumen",
        "nuevo_premium_proxy",
        "delta_iv_puntos",
        "delta_gex_proxy",
        "flow_dinamico_score",
        "evento_volumen",
        "evento_iv",
    ]

    disponibles = [
        columna
        for columna in columnas
        if columna in activos.columns
    ]

    print(
        activos[
            disponibles
        ]
        .head(20)
        .to_string(
            index=False,
            float_format=lambda x: (
                f"{x:,.2f}"
            ),
        )
    )

    print()
    print(
        "Nota: actividad observada, no dirección "
        "comprador/vendedor confirmada."
    )


def ejecutar_comparacion() -> Path:
    """Compara automáticamente los dos snapshots más recientes."""

    archivos = obtener_snapshots()

    if len(archivos) < 2:
        raise RuntimeError(
            "Se necesitan al menos dos snapshots."
        )

    ruta_t0 = archivos[-2]
    ruta_t1 = archivos[-1]

    print()
    print(
        f"t0: {ruta_t0.name}"
    )
    print(
        f"t1: {ruta_t1.name}"
    )

    anterior = cargar_snapshot(
        ruta_t0
    )

    actual = cargar_snapshot(
        ruta_t1
    )

    resultado = comparar(
        anterior,
        actual,
    )

    resultado = calcular_score(
        resultado
    )

    resultado = clasificar_eventos(
        resultado
    )

    RUTA_RESULTADOS.mkdir(
        parents=True,
        exist_ok=True,
    )

    nombre = (
        "comparacion_"
        f"{ruta_t0.stem.replace('snapshot_', '')}"
        "_a_"
        f"{ruta_t1.stem.replace('snapshot_', '')}"
        ".csv"
    )

    ruta_salida = (
        RUTA_RESULTADOS
        / nombre
    )

    resultado.to_csv(
        ruta_salida,
        index=False,
    )

    imprimir_resumen(
        resultado
    )

    print()
    print(
        f"Guardado en: {ruta_salida}"
    )

    return ruta_salida


def main() -> None:
    """Ejecuta la comparación de snapshots."""

    ejecutar_comparacion()


if __name__ == "__main__":
    main()