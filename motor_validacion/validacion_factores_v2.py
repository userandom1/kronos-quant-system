from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from motor_validacion.backtest_no_solapado import (
    block_bootstrap_ic,
    calcular_ic,
    calcular_metricas,
    construir_long_short,
    retornos_futuros,
)
from motor_validacion.historico_senales import (
    UNIVERSO,
    construir_features,
    descargar_precios,
    zscore_cross_sectional,
)


RUTA_BASE = Path(__file__).resolve().parents[1]

RUTA_RESULTADOS = (
    RUTA_BASE
    / "resultados"
    / "validacion"
    / "v2_factores"
)

HORIZONTES = [
    5,
    20,
    60,
]


def construir_factores(
    precios: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    """Reconstruye los factores históricos individuales."""

    features = construir_features(
        precios
    )

    momentum = (
        0.50
        * zscore_cross_sectional(
            features["momentum20"]
        )
        + 0.50
        * zscore_cross_sectional(
            features["momentum60"]
        )
    )

    tendencia = (
        0.40
        * zscore_cross_sectional(
            features["distancia_ma20"]
        )
        + 0.30
        * zscore_cross_sectional(
            features["distancia_ma50"]
        )
        + 0.30
        * zscore_cross_sectional(
            features["distancia_ma200"]
        )
    )

    rendimiento = (
        0.40
        * zscore_cross_sectional(
            features["retorno_20d"]
        )
        + 0.60
        * zscore_cross_sectional(
            features["retorno_60d"]
        )
    )

    sharpe = zscore_cross_sectional(
        features["sharpe60"]
    )

    riesgo = (
        -0.50
        * zscore_cross_sectional(
            features["vol20"]
        )
        + 0.50
        * zscore_cross_sectional(
            features["drawdown"]
        )
    )

    relativo = (
        0.20
        * zscore_cross_sectional(
            features["retorno_20d"]
        )
        + 0.20
        * zscore_cross_sectional(
            features["retorno_60d"]
        )
        + 0.20
        * zscore_cross_sectional(
            features["momentum20"]
        )
        + 0.20
        * zscore_cross_sectional(
            features["sharpe60"]
        )
        - 0.10
        * zscore_cross_sectional(
            features["vol20"]
        )
        + 0.10
        * zscore_cross_sectional(
            features["drawdown"]
        )
    )

    relativo = zscore_cross_sectional(
        relativo
    )

    composite = (
        0.20 * tendencia
        + 0.20 * momentum
        + 0.15 * rendimiento
        + 0.15 * sharpe
        + 0.10 * riesgo
        + 0.10 * relativo
    )

    factores = {
        "MOMENTUM": momentum,
        "TENDENCIA": tendencia,
        "RENDIMIENTO": rendimiento,
        "SHARPE": sharpe,
        "RIESGO": riesgo,
        "RELATIVO": relativo,
        "COMPOSITE": composite,
    }

    # La señal se desplaza una sesión para evitar
    # utilizar información del cierre para operar ese mismo cierre.
    return {
        nombre: factor.shift(1)
        for nombre, factor in factores.items()
    }


def validar_factor(
    nombre: str,
    senal: pd.DataFrame,
    precios: pd.DataFrame,
    horizonte: int,
) -> dict:
    """Valida un factor para un horizonte."""

    futuro = retornos_futuros(
        precios,
        horizonte,
    )

    ic = calcular_ic(
        senal,
        futuro,
        horizonte,
    )

    estrategia = construir_long_short(
        senal,
        futuro,
        horizonte,
    )

    if estrategia.empty:
        metricas_ls = calcular_metricas(
            pd.Series(dtype=float),
            horizonte,
        )

        retorno_q1 = np.nan
        retorno_q5 = np.nan

    else:
        metricas_ls = calcular_metricas(
            estrategia["long_short"],
            horizonte,
        )

        retorno_q1 = (
            estrategia["q1"].mean()
        )

        retorno_q5 = (
            estrategia["q5"].mean()
        )

    ci_inferior, ci_superior = (
        block_bootstrap_ic(
            ic
        )
    )

    return {
        "factor": nombre,
        "horizonte_dias": horizonte,
        "ic_medio": ic.mean(),
        "ic_mediana": ic.median(),
        "ic_hit_rate": (
            (ic > 0).mean()
            if len(ic)
            else np.nan
        ),
        "ic_ci95_inferior": (
            ci_inferior
        ),
        "ic_ci95_superior": (
            ci_superior
        ),
        "q1_retorno_medio": (
            retorno_q1
        ),
        "q5_retorno_medio": (
            retorno_q5
        ),
        "spread_q5_q1": (
            retorno_q5
            - retorno_q1
        ),
        "ls_sharpe": (
            metricas_ls["sharpe"]
        ),
        "ls_max_drawdown": (
            metricas_ls[
                "max_drawdown"
            ]
        ),
        "ls_hit_rate": (
            metricas_ls[
                "hit_rate"
            ]
        ),
        "n_operaciones": (
            metricas_ls[
                "n_operaciones"
            ]
        ),
    }


def calcular_ic_anual(
    factor: pd.DataFrame,
    precios: pd.DataFrame,
    horizonte: int,
) -> pd.DataFrame:
    """Calcula IC medio anual."""

    futuro = retornos_futuros(
        precios,
        horizonte,
    )

    ic = calcular_ic(
        factor,
        futuro,
        horizonte,
    )

    if ic.empty:
        return pd.DataFrame()

    datos = ic.to_frame()

    datos["anio"] = (
        datos.index.year
    )

    salida = (
        datos.groupby(
            "anio"
        )["ic"]
        .agg(
            [
                "mean",
                "median",
                "count",
            ]
        )
        .reset_index()
    )

    salida.columns = [
        "anio",
        "ic_medio",
        "ic_mediana",
        "n_observaciones",
    ]

    return salida


def imprimir_resumen(
    datos: pd.DataFrame,
) -> None:
    """Muestra resumen compacto."""

    columnas = [
        "factor",
        "horizonte_dias",
        "ic_medio",
        "ic_ci95_inferior",
        "ic_ci95_superior",
        "spread_q5_q1",
        "ls_sharpe",
        "ls_max_drawdown",
        "ls_hit_rate",
        "n_operaciones",
    ]

    salida = datos[
        columnas
    ].copy()

    salida[
        "spread_q5_q1"
    ] *= 100.0

    salida[
        "ls_max_drawdown"
    ] *= 100.0

    salida[
        "ls_hit_rate"
    ] *= 100.0

    print()
    print("=" * 145)
    print(
        "VALIDACIÓN ROBUSTA DE FACTORES V2"
    )
    print("=" * 145)

    print(
        salida.to_string(
            index=False,
            float_format=lambda x: (
                f"{x:,.4f}"
            ),
        )
    )


def main() -> None:
    """Ejecuta la validación robusta."""

    RUTA_RESULTADOS.mkdir(
        parents=True,
        exist_ok=True,
    )

    print(
        "Descargando histórico..."
    )

    precios = descargar_precios(
        UNIVERSO,
        periodo="10y",
    )

    print(
        "Construyendo factores..."
    )

    factores = construir_factores(
        precios
    )

    resultados = []

    for nombre, factor in factores.items():
        for horizonte in HORIZONTES:
            print(
                f"Validando "
                f"{nombre} "
                f"{horizonte}D..."
            )

            resultado = validar_factor(
                nombre=nombre,
                senal=factor,
                precios=precios,
                horizonte=horizonte,
            )

            resultados.append(
                resultado
            )

            anual = calcular_ic_anual(
                factor,
                precios,
                horizonte,
            )

            anual.to_csv(
                RUTA_RESULTADOS
                / (
                    f"ic_anual_"
                    f"{nombre.lower()}_"
                    f"{horizonte}d.csv"
                ),
                index=False,
            )

    resumen = pd.DataFrame(
        resultados
    )

    resumen.to_csv(
        RUTA_RESULTADOS
        / "validacion_factores_v2.csv",
        index=False,
    )

    imprimir_resumen(
        resumen
    )

    print()
    print(
        f"Resultados: {RUTA_RESULTADOS}"
    )


if __name__ == "__main__":
    main()