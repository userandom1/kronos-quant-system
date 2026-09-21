from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


RUTA_BASE = Path(__file__).resolve().parents[1]

RUTA_PORTFOLIO_V2 = (
    RUTA_BASE
    / "resultados"
    / "portfolio_engine"
    / "v1"
    / "v2"
)


def resolver_csv_portfolio(
    nombre_preferido: str,
    patrones: list[str],
) -> Path:
    """Localiza un CSV de Portfolio V2 de forma robusta."""

    ruta_preferida = (
        RUTA_PORTFOLIO_V2
        / nombre_preferido
    )

    if ruta_preferida.exists():
        return ruta_preferida

    for patron in patrones:
        candidatos = sorted(
            RUTA_PORTFOLIO_V2.glob(
                patron
            ),
            key=lambda ruta: (
                ruta.stat().st_mtime
            ),
            reverse=True,
        )

        if candidatos:
            return candidatos[0]

    return ruta_preferida

RUTAS_DATOS = {
    "senales_v2": (
        RUTA_BASE
        / "resultados"
        / "senales_v2"
        / "senales_v2.csv"
    ),

    "market_regime_v1": (
        RUTA_BASE
        / "resultados"
        / "market_regime_v1"
        / "comparador_multi_activo"
        / "ranking_multi_activo.csv"
    ),

    "market_regime_v2": (
        RUTA_BASE
        / "resultados"
        / "regimen_mercado_v2"
        / "regimen_mercado_v2.csv"
    ),

    "market_regime_global": (
        RUTA_BASE
        / "resultados"
        / "regimen_mercado_v2"
        / "regimen_global.csv"
    ),

    "portfolio_v2_alpha": resolver_csv_portfolio(
    "alpha_portfolio_v2.csv",
    [
        "*alpha*v2*.csv",
        "*alpha*.csv",
    ],
),

"portfolio_v2_pesos": resolver_csv_portfolio(
    "pesos_portfolio_v2.csv",
    [
        "*pesos*v2*.csv",
        "*pesos*.csv",
    ],
),

"portfolio_v2_metricas": resolver_csv_portfolio(
    "metricas_portfolio_v2.csv",
    [
        "*metricas*v2*.csv",
        "*metricas*.csv",
    ],
),

"portfolio_v2_correlaciones": resolver_csv_portfolio(
    "correlaciones_portfolio_v2.csv",
    [
        "*correlaciones*v2*.csv",
        "*correl*.csv",
    ],
),

    "risk_metricas": (
        RUTA_BASE
        / "resultados"
        / "risk_engine"
        / "v1"
        / "metricas_riesgo.csv"
    ),

    "risk_contribucion": (
        RUTA_BASE
        / "resultados"
        / "risk_engine"
        / "v1"
        / "contribucion_riesgo.csv"
    ),

    "risk_component_var": (
        RUTA_BASE
        / "resultados"
        / "risk_engine"
        / "v1"
        / "component_var.csv"
    ),

    "risk_stress": (
        RUTA_BASE
        / "resultados"
        / "risk_engine"
        / "v1"
        / "stress_tests.csv"
    ),

    "risk_stress_historico": (
        RUTA_BASE
        / "resultados"
        / "risk_engine"
        / "v1"
        / "stress_historico.csv"
    ),

    "options_flow_v2": (
        RUTA_BASE
        / "resultados"
        / "options_flow"
        / "QQQ"
        / "v2"
        / "options_flow_v2_contratos.csv"
    ),

    "options_flow_resumen": (
        RUTA_BASE
        / "resultados"
        / "options_flow"
        / "QQQ"
        / "v2"
        / "resumen_flow_v2.csv"
    ),

    "options_flow_strike": (
        RUTA_BASE
        / "resultados"
        / "options_flow"
        / "QQQ"
        / "v2"
        / "flow_por_strike.csv"
    ),

    "options_flow_vencimiento": (
        RUTA_BASE
        / "resultados"
        / "options_flow"
        / "QQQ"
        / "v2"
        / "flow_por_vencimiento.csv"
    ),

    "dealer_v4_resumen": (
        RUTA_BASE
        / "resultados"
        / "dealer_engine"
        / "QQQ"
        / "v4"
        / "resumen_dealer_v4.csv"
    ),

    "dealer_v4_perfil": (
        RUTA_BASE
        / "resultados"
        / "dealer_engine"
        / "QQQ"
        / "v4"
        / "perfil_gamma_v4.csv"
    ),

    "dealer_v4_flow": (
        RUTA_BASE
        / "resultados"
        / "dealer_engine"
        / "QQQ"
        / "v4"
        / "dealer_flow_v4.csv"
    ),

    "dealer_v4_strike": (
        RUTA_BASE
        / "resultados"
        / "dealer_engine"
        / "QQQ"
        / "v4"
        / "dealer_flow_por_strike.csv"
    ),
}


def limpiar_dataframe(
    datos: pd.DataFrame,
) -> pd.DataFrame:
    """Convierte NaN e infinitos en valores JSON compatibles."""

    datos = datos.copy()

    datos = datos.replace(
        [
            np.inf,
            -np.inf,
        ],
        np.nan,
    )

    return datos


def dataframe_a_registros(
    datos: pd.DataFrame,
) -> list[dict[str, Any]]:
    """Convierte DataFrame a registros compatibles con JSON."""

    limpio = limpiar_dataframe(
        datos
    )

    limpio = limpio.astype(
        object
    )

    limpio = limpio.where(
        pd.notna(limpio),
        None,
    )

    return limpio.to_dict(
        orient="records"
    )


def cargar_dataset(
    nombre: str,
) -> list[dict[str, Any]]:
    """Carga un dataset registrado."""

    if nombre not in RUTAS_DATOS:
        raise KeyError(
            f"Dataset desconocido: {nombre}"
        )

    ruta = RUTAS_DATOS[
        nombre
    ]

    if not ruta.exists():
        return []

    datos = pd.read_csv(
        ruta
    )

    return dataframe_a_registros(
        datos
    )


def cargar_primera_fila(
    nombre: str,
) -> dict[str, Any]:
    """Obtiene primera fila de un dataset."""

    registros = cargar_dataset(
        nombre
    )

    if not registros:
        return {}

    return registros[0]


def cargar_todos_disponibles() -> dict[str, bool]:
    """Indica qué datasets existen."""

    return {
        nombre: ruta.exists()
        for nombre, ruta
        in RUTAS_DATOS.items()
    }


def extraer_pesos_signal_tilted() -> list[dict[str, Any]]:
    """Normaliza pesos actuales de Signal Tilted V2."""

    ruta = RUTAS_DATOS[
        "portfolio_v2_pesos"
    ]

    if not ruta.exists():
        return []

    datos = pd.read_csv(
        ruta,
        index_col=0,
    )

    columna = (
        "Signal Tilted V2"
    )

    if columna not in datos.columns:
        return []

    salida = (
        datos[
            columna
        ]
        .rename("peso")
        .reset_index()
    )

    salida.columns = [
        "ticker",
        "peso",
    ]

    salida = salida.sort_values(
        "peso",
        ascending=False,
    )

    return dataframe_a_registros(
        salida
    )


def construir_resumen_dashboard() -> dict[str, Any]:
    """Construye KPIs principales del dashboard."""

    regimen = cargar_primera_fila(
        "market_regime_global"
    )

    riesgo = cargar_primera_fila(
        "risk_metricas"
    )

    flow = cargar_primera_fila(
        "options_flow_resumen"
    )

    dealer = cargar_primera_fila(
        "dealer_v4_resumen"
    )

    return {
        "ticker_principal": "QQQ",

        "regimen": {
            "estado": regimen.get(
                "regimen_global"
            ),
            "score": regimen.get(
                "score_global"
            ),
        },

        "riesgo": {
            "volatilidad": riesgo.get(
                "volatilidad_anual"
            ),
            "var_95": riesgo.get(
                "var_95_1d"
            ),
            "cvar_95": riesgo.get(
                "cvar_95_1d"
            ),
            "max_drawdown": riesgo.get(
                "max_drawdown"
            ),
            "beta_spy": riesgo.get(
                "beta_spy"
            ),
            "numero_efectivo_activos": riesgo.get(
                "numero_efectivo_activos"
            ),
        },

        "flow": {
            "estado": flow.get(
                "estado_flow"
            ),
            "balance": flow.get(
                "balance_flow_proxy"
            ),
            "premium": flow.get(
                "premium_nuevo"
            ),
            "volumen": flow.get(
                "nuevo_volumen"
            ),
        },

        "dealer": {
            "spot": dealer.get(
                "spot"
            ),
            "gamma_flip": dealer.get(
                "gamma_flip"
            ),
            "gex": dealer.get(
                "gex_estructural"
            ),
            "dex": dealer.get(
                "dex_estructural"
            ),
            "gamma_node_positivo": dealer.get(
                "gamma_node_positivo"
            ),
            "gamma_node_negativo": dealer.get(
                "gamma_node_negativo"
            ),
            "flow_gamma_node": dealer.get(
                "flow_gamma_node"
            ),
        },

        "portfolio": {
            "pesos": extraer_pesos_signal_tilted(),
        },
    }