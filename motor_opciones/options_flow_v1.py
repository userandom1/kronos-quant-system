from pathlib import Path

import numpy as np
import pandas as pd


RUTA_BASE = Path(__file__).resolve().parents[1]

RUTA_ENTRADA = (
    RUTA_BASE
    / "resultados"
    / "dealer_engine"
    / "QQQ"
    / "cadena_filtrada.csv"
)

RUTA_RESULTADOS = (
    RUTA_BASE
    / "resultados"
    / "options_flow"
    / "QQQ"
    / "v1"
)

MULTIPLICADOR = 100.0


def cargar_datos() -> pd.DataFrame:
    """Carga la cadena filtrada de QQQ."""

    datos = pd.read_csv(
        RUTA_ENTRADA
    )

    columnas = [
        "strike",
        "spot",
        "bid",
        "ask",
        "mid",
        "lastPrice",
        "volume",
        "openInterest",
        "impliedVolatility",
        "dte",
        "delta",
        "gamma",
        "vanna",
        "delta_decay",
    ]

    for columna in columnas:
        if columna in datos.columns:
            datos[columna] = pd.to_numeric(
                datos[columna],
                errors="coerce",
            )

    datos["volume"] = (
        datos["volume"]
        .fillna(0)
    )

    datos["openInterest"] = (
        datos["openInterest"]
        .fillna(0)
    )

    return datos


def preparar_metricas(
    datos: pd.DataFrame,
) -> pd.DataFrame:
    """Construye métricas proxy de actividad de opciones."""

    datos = datos.copy()

    datos["volume_oi_ratio"] = np.where(
        datos["openInterest"] > 0,
        datos["volume"]
        / datos["openInterest"],
        np.nan,
    )

    datos["premium_proxy"] = (
        datos["volume"]
        * MULTIPLICADOR
        * datos["mid"]
    )

    datos["oi_notional"] = (
        datos["openInterest"]
        * MULTIPLICADOR
        * datos["spot"]
    )

    datos["distancia_spot_pct"] = (
        datos["strike"]
        / datos["spot"]
        - 1.0
    ) * 100.0

    datos["spread"] = (
        datos["ask"]
        - datos["bid"]
    )

    datos["spread_pct"] = np.where(
        datos["mid"] > 0,
        datos["spread"]
        / datos["mid"],
        np.nan,
    )

    datos["posicion_ultimo_en_spread"] = np.where(
        datos["spread"] > 0,
        (
            datos["lastPrice"]
            - datos["bid"]
        )
        / datos["spread"],
        np.nan,
    )

    datos[
        "posicion_ultimo_en_spread"
    ] = datos[
        "posicion_ultimo_en_spread"
    ].clip(
        0.0,
        1.0,
    )

    datos["actividad_atm"] = (
        datos["distancia_spot_pct"]
        .abs()
        <= 2.0
    )

    datos["volumen_inusual"] = (
        datos["volume_oi_ratio"]
        >= 1.0
    )

    return datos


def calcular_flow_score(
    datos: pd.DataFrame,
) -> pd.DataFrame:
    """
    Construye un score relativo de actividad.

    No representa dirección real de compra o venta.
    """

    datos = datos.copy()

    def percentil(
        serie: pd.Series,
    ) -> pd.Series:
        return (
            serie
            .rank(
                pct=True
            )
            .fillna(0.0)
        )

    score_volume = percentil(
        datos["volume"]
    )

    score_premium = percentil(
        datos["premium_proxy"]
    )

    score_volume_oi = percentil(
        datos["volume_oi_ratio"]
    )

    score_gamma = percentil(
        datos["gamma"].abs()
    )

    datos["flow_score"] = (
        0.30 * score_volume
        + 0.30 * score_premium
        + 0.25 * score_volume_oi
        + 0.15 * score_gamma
    ) * 100.0

    return datos


def resumen_call_put(
    datos: pd.DataFrame,
) -> pd.DataFrame:
    """Resume actividad separada entre calls y puts."""

    return (
        datos.groupby(
            "tipo",
            as_index=False,
        )
        .agg(
            contratos=(
                "contractSymbol",
                "count",
            ),
            volumen=(
                "volume",
                "sum",
            ),
            open_interest=(
                "openInterest",
                "sum",
            ),
            premium_proxy=(
                "premium_proxy",
                "sum",
            ),
        )
    )


def actividad_por_strike(
    datos: pd.DataFrame,
) -> pd.DataFrame:
    """Agrega actividad por strike."""

    return (
        datos.groupby(
            [
                "strike",
                "tipo",
            ],
            as_index=False,
        )
        .agg(
            volumen=(
                "volume",
                "sum",
            ),
            open_interest=(
                "openInterest",
                "sum",
            ),
            premium_proxy=(
                "premium_proxy",
                "sum",
            ),
            flow_score_medio=(
                "flow_score",
                "mean",
            ),
        )
    )


def actividad_por_vencimiento(
    datos: pd.DataFrame,
) -> pd.DataFrame:
    """Agrega actividad por vencimiento."""

    return (
        datos.groupby(
            [
                "vencimiento",
                "tipo",
            ],
            as_index=False,
        )
        .agg(
            volumen=(
                "volume",
                "sum",
            ),
            open_interest=(
                "openInterest",
                "sum",
            ),
            premium_proxy=(
                "premium_proxy",
                "sum",
            ),
        )
    )


def obtener_top_flow(
    datos: pd.DataFrame,
    n: int = 25,
) -> pd.DataFrame:
    """Selecciona contratos con mayor actividad relativa."""

    columnas = [
        "contractSymbol",
        "tipo",
        "vencimiento",
        "dte",
        "strike",
        "spot",
        "distancia_spot_pct",
        "bid",
        "ask",
        "mid",
        "lastPrice",
        "volume",
        "openInterest",
        "volume_oi_ratio",
        "premium_proxy",
        "impliedVolatility",
        "delta",
        "gamma",
        "flow_score",
    ]

    return (
        datos
        .sort_values(
            "flow_score",
            ascending=False,
        )
        .head(n)[
            columnas
        ]
    )


def imprimir_resumen(
    datos: pd.DataFrame,
    call_put: pd.DataFrame,
    top: pd.DataFrame,
) -> None:
    """Muestra el resumen principal en terminal."""

    volumen_total = (
        datos["volume"].sum()
    )

    premium_total = (
        datos[
            "premium_proxy"
        ].sum()
    )

    calls = datos[
        datos["tipo"]
        == "call"
    ]

    puts = datos[
        datos["tipo"]
        == "put"
    ]

    volumen_calls = (
        calls["volume"].sum()
    )

    volumen_puts = (
        puts["volume"].sum()
    )

    put_call_volume = (
        volumen_puts
        / volumen_calls
        if volumen_calls > 0
        else np.nan
    )

    print()
    print("=" * 90)
    print("OPTIONS FLOW PROXY V1 - QQQ")
    print("=" * 90)

    print(
        f"Contratos analizados : "
        f"{len(datos):,}"
    )

    print(
        f"Volumen total        : "
        f"{volumen_total:,.0f}"
    )

    print(
        f"Premium proxy        : "
        f"${premium_total:,.0f}"
    )

    print(
        f"Put/Call Volume      : "
        f"{put_call_volume:.3f}"
    )

    print(
        f"Volumen inusual      : "
        f"{datos['volumen_inusual'].sum():,} contratos"
    )

    print()
    print("CALL / PUT")
    print("-" * 90)

    print(
        call_put.to_string(
            index=False
        )
    )

    print()
    print("TOP 15 CONTRATOS POR FLOW SCORE")
    print("-" * 90)

    print(
        top.head(15).to_string(
            index=False,
            float_format=lambda x: (
                f"{x:,.2f}"
            ),
        )
    )

    print()
    print(
        "NOTA: Flow Score mide actividad relativa. "
        "No identifica comprador/vendedor real."
    )


def main() -> None:
    """Ejecuta Options Flow Proxy V1."""

    RUTA_RESULTADOS.mkdir(
        parents=True,
        exist_ok=True,
    )

    datos = cargar_datos()

    datos = preparar_metricas(
        datos
    )

    datos = calcular_flow_score(
        datos
    )

    call_put = resumen_call_put(
        datos
    )

    por_strike = actividad_por_strike(
        datos
    )

    por_vencimiento = (
        actividad_por_vencimiento(
            datos
        )
    )

    top = obtener_top_flow(
        datos
    )

    datos.to_csv(
        RUTA_RESULTADOS
        / "options_flow_contratos.csv",
        index=False,
    )

    call_put.to_csv(
        RUTA_RESULTADOS
        / "resumen_call_put.csv",
        index=False,
    )

    por_strike.to_csv(
        RUTA_RESULTADOS
        / "actividad_por_strike.csv",
        index=False,
    )

    por_vencimiento.to_csv(
        RUTA_RESULTADOS
        / "actividad_por_vencimiento.csv",
        index=False,
    )

    top.to_csv(
        RUTA_RESULTADOS
        / "top_flow.csv",
        index=False,
    )

    imprimir_resumen(
        datos,
        call_put,
        top,
    )

    print()
    print(
        f"Resultados: {RUTA_RESULTADOS}"
    )


if __name__ == "__main__":
    main()