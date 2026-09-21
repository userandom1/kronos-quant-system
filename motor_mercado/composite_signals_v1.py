from pathlib import Path

import numpy as np
import pandas as pd


RUTA_BASE = Path(__file__).resolve().parents[1]

RUTA_MULTI_ACTIVO = (
    RUTA_BASE
    / "resultados"
    / "market_regime_v1"
    / "comparador_multi_activo"
    / "ranking_multi_activo.csv"
)

RUTA_DEALER = (
    RUTA_BASE
    / "resultados"
    / "dealer_engine"
    / "QQQ"
    / "v31"
    / "dealer_v31_escenarios.csv"
)

RUTA_FLOW = (
    RUTA_BASE
    / "resultados"
    / "options_flow"
    / "QQQ"
    / "v1"
    / "options_flow_contratos.csv"
)

RUTA_RESULTADOS = (
    RUTA_BASE
    / "resultados"
    / "composite_signals"
    / "v1"
)


def normalizar_zscore(
    serie: pd.Series,
) -> pd.Series:
    """Normaliza una serie mediante z-score."""

    serie = pd.to_numeric(
        serie,
        errors="coerce",
    )

    media = serie.mean()
    desviacion = serie.std(
        ddof=0
    )

    if (
        not np.isfinite(desviacion)
        or desviacion == 0
    ):
        return pd.Series(
            0.0,
            index=serie.index,
        )

    return (
        serie - media
    ) / desviacion


def cargar_base() -> pd.DataFrame:
    """Carga el ranking multi-activo."""

    if not RUTA_MULTI_ACTIVO.exists():
        raise FileNotFoundError(
            f"No existe: {RUTA_MULTI_ACTIVO}"
        )

    return pd.read_csv(
        RUTA_MULTI_ACTIVO
    )


def calcular_score_mercado(
    datos: pd.DataFrame,
) -> pd.DataFrame:
    """Construye componentes principales de mercado."""

    datos = datos.copy()

    datos["z_momentum"] = (
        0.50
        * normalizar_zscore(
            datos["momentum20"]
        )
        + 0.50
        * normalizar_zscore(
            datos["momentum60"]
        )
    )

    datos["z_tendencia"] = (
        0.40
        * normalizar_zscore(
            datos["distancia_ma20"]
        )
        + 0.30
        * normalizar_zscore(
            datos["distancia_ma50"]
        )
        + 0.30
        * normalizar_zscore(
            datos["distancia_ma200"]
        )
    )

    datos["z_rendimiento"] = (
        0.40
        * normalizar_zscore(
            datos["retorno_20d"]
        )
        + 0.60
        * normalizar_zscore(
            datos["retorno_60d"]
        )
    )

    datos["z_sharpe"] = (
        normalizar_zscore(
            datos["sharpe60"]
        )
    )

    datos["z_riesgo"] = (
        -0.50
        * normalizar_zscore(
            datos["vol20"]
        )
        + 0.50
        * normalizar_zscore(
            datos["drawdown_actual"]
        )
    )

    datos["z_relativo"] = (
        normalizar_zscore(
            datos["score_relativo"]
        )
    )

    return datos


def leer_dealer_qqq() -> float:
    """Calcula un componente simplificado de Dealer Engine para QQQ."""

    if not RUTA_DEALER.exists():
        return 0.0

    datos = pd.read_csv(
        RUTA_DEALER
    )

    base = datos[
        (
            datos["shock_spot_pct"] == 0
        )
        & (
            datos["shock_iv_puntos"] == 0
        )
        & (
            datos["decaimiento_dias"] == 0
        )
    ]

    if base.empty:
        return 0.0

    fila = base.iloc[0]

    gamma = float(
        fila.get(
            "gamma_acciones_por_dolar",
            0.0,
        )
    )

    if gamma > 0:
        return 0.50

    if gamma < 0:
        return -0.50

    return 0.0


def leer_flow_qqq() -> float:
    """Construye un componente descriptivo del Options Flow de QQQ."""

    if not RUTA_FLOW.exists():
        return 0.0

    datos = pd.read_csv(
        RUTA_FLOW
    )

    if datos.empty:
        return 0.0

    calls = datos[
        datos["tipo"] == "call"
    ]

    puts = datos[
        datos["tipo"] == "put"
    ]

    vol_calls = calls[
        "volume"
    ].sum()

    vol_puts = puts[
        "volume"
    ].sum()

    total = (
        vol_calls
        + vol_puts
    )

    if total <= 0:
        return 0.0

    desequilibrio = (
        vol_calls
        - vol_puts
    ) / total

    return float(
        np.clip(
            desequilibrio,
            -1.0,
            1.0,
        )
    )


def añadir_componentes_opciones(
    datos: pd.DataFrame,
) -> pd.DataFrame:
    """Añade componentes Dealer/Options cuando están disponibles."""

    datos = datos.copy()

    datos[
        "score_dealer"
    ] = 0.0

    datos[
        "score_options_flow"
    ] = 0.0

    mascara_qqq = (
        datos["ticker"]
        == "QQQ"
    )

    datos.loc[
        mascara_qqq,
        "score_dealer",
    ] = leer_dealer_qqq()

    datos.loc[
        mascara_qqq,
        "score_options_flow",
    ] = leer_flow_qqq()

    return datos


def construir_composite(
    datos: pd.DataFrame,
) -> pd.DataFrame:
    """Construye el Composite Signal."""

    datos = datos.copy()

    datos[
        "composite_score"
    ] = (
        0.20
        * datos["z_tendencia"]
        + 0.20
        * datos["z_momentum"]
        + 0.15
        * datos["z_rendimiento"]
        + 0.15
        * datos["z_sharpe"]
        + 0.10
        * datos["z_riesgo"]
        + 0.10
        * datos["z_relativo"]
        + 0.05
        * datos["score_dealer"]
        + 0.05
        * datos["score_options_flow"]
    )

    return datos


def clasificar_estado(
    score: float,
) -> str:
    """Clasifica el estado cuantitativo agregado."""

    if score >= 1.0:
        return "FORTALEZA_ALTA"

    if score >= 0.35:
        return "FORTALEZA"

    if score <= -1.0:
        return "DEBILIDAD_ALTA"

    if score <= -0.35:
        return "DEBILIDAD"

    return "NEUTRAL"


def añadir_clasificacion(
    datos: pd.DataFrame,
) -> pd.DataFrame:
    """Añade clasificación descriptiva."""

    datos = datos.copy()

    datos[
        "estado_compuesto"
    ] = datos[
        "composite_score"
    ].apply(
        clasificar_estado
    )

    datos[
        "ranking_composite"
    ] = datos[
        "composite_score"
    ].rank(
        ascending=False,
        method="min",
    )

    return datos


def imprimir_resultados(
    datos: pd.DataFrame,
) -> None:
    """Muestra resultados resumidos."""

    columnas = [
        "ranking_composite",
        "ticker",
        "composite_score",
        "z_tendencia",
        "z_momentum",
        "z_rendimiento",
        "z_sharpe",
        "z_riesgo",
        "z_relativo",
        "score_dealer",
        "score_options_flow",
        "estado_compuesto",
    ]

    salida = (
        datos[
            columnas
        ]
        .sort_values(
            "ranking_composite"
        )
    )

    print()
    print("=" * 135)
    print(
        "COMPOSITE SIGNALS V1"
    )
    print("=" * 135)

    print(
        salida.to_string(
            index=False,
            float_format=lambda x: (
                f"{x:,.3f}"
            ),
        )
    )


def main() -> None:
    """Ejecuta Composite Signals V1."""

    RUTA_RESULTADOS.mkdir(
        parents=True,
        exist_ok=True,
    )

    datos = cargar_base()

    datos = calcular_score_mercado(
        datos
    )

    datos = añadir_componentes_opciones(
        datos
    )

    datos = construir_composite(
        datos
    )

    datos = añadir_clasificacion(
        datos
    )

    ruta = (
        RUTA_RESULTADOS
        / "composite_signals_v1.csv"
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