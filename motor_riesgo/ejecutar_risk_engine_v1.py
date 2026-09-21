from __future__ import annotations

from pathlib import Path

import pandas as pd

from motor_portfolio.datos_portfolio import (
    UNIVERSO_PORTFOLIO,
    calcular_retornos,
    descargar_precios,
)
from motor_riesgo.contribucion_riesgo import (
    calcular_component_var,
    calcular_contribucion_riesgo,
)
from motor_riesgo.metricas_riesgo import (
    calcular_metricas_riesgo,
)
from motor_riesgo.stress_test import (
    ejecutar_stress_tests,
    stress_historico,
)


RUTA_BASE = Path(__file__).resolve().parents[1]

RUTA_PESOS = (
    RUTA_BASE
    / "resultados"
    / "portfolio_engine"
    / "v1"
    / "v2"
    / "pesos_portfolio_v2.csv"
)

RUTA_RESULTADOS = (
    RUTA_BASE
    / "resultados"
    / "risk_engine"
    / "v1"
)


def cargar_pesos() -> pd.Series:
    """Carga los pesos actuales del Signal Tilted V2."""

    datos = pd.read_csv(
        RUTA_PESOS,
        index_col=0,
    )

    columna = (
        "Signal Tilted V2"
    )

    if columna not in datos.columns:
        raise KeyError(
            f"No existe la columna '{columna}'."
        )

    pesos = datos[
        columna
    ].astype(float)

    return pesos


def imprimir_metricas(
    metricas: dict[str, float],
) -> None:
    """Muestra métricas principales."""

    print()
    print("=" * 85)
    print("RISK ENGINE V1 - MÉTRICAS")
    print("=" * 85)

    for nombre, valor in metricas.items():

        if nombre in {
            "volatilidad_anual",
            "downside_volatility",
            "var_95_1d",
            "var_99_1d",
            "cvar_95_1d",
            "cvar_99_1d",
            "max_drawdown",
        }:
            print(
                f"{nombre:<28}: "
                f"{valor * 100:,.2f}%"
            )

        else:
            print(
                f"{nombre:<28}: "
                f"{valor:,.4f}"
            )


def imprimir_contribucion(
    contribucion: pd.DataFrame,
) -> None:
    """Muestra contribución al riesgo."""

    salida = contribucion.copy()

    salida[
        "peso"
    ] *= 100.0

    salida[
        "contribucion_riesgo_pct"
    ] *= 100.0

    print()
    print("=" * 85)
    print("CONTRIBUCIÓN AL RIESGO")
    print("=" * 85)

    print(
        salida.to_string(
            index=False,
            float_format=lambda x: (
                f"{x:,.4f}"
            ),
        )
    )


def imprimir_stress(
    stress: pd.DataFrame,
) -> None:
    """Muestra stress tests principales."""

    salida = stress[
        [
            "escenario",
            "impacto_portfolio",
        ]
    ].copy()

    salida[
        "impacto_portfolio"
    ] *= 100.0

    print()
    print("=" * 85)
    print("STRESS TESTS")
    print("=" * 85)

    print(
        salida.to_string(
            index=False,
            float_format=lambda x: (
                f"{x:,.2f}%"
            ),
        )
    )


def main() -> None:
    """Ejecuta Risk Engine V1."""

    RUTA_RESULTADOS.mkdir(
        parents=True,
        exist_ok=True,
    )

    print(
        "Cargando pesos oficiales..."
    )

    pesos = cargar_pesos()

    print(
        "Descargando histórico..."
    )

    precios = descargar_precios(
        UNIVERSO_PORTFOLIO,
        periodo="5y",
    )

    retornos = calcular_retornos(
        precios
    )

    pesos = pesos.reindex(
        retornos.columns
    ).fillna(0.0)

    pesos = (
        pesos
        / pesos.sum()
    )

    retornos_portfolio = (
        retornos
        @ pesos
    )

    benchmark = retornos[
        "SPY"
    ]

    metricas = calcular_metricas_riesgo(
        retornos=retornos_portfolio,
        pesos=pesos,
        benchmark=benchmark,
    )

    contribucion = calcular_contribucion_riesgo(
        retornos,
        pesos,
    )

    component_var = calcular_component_var(
        retornos,
        pesos,
        confianza=0.95,
    )

    stress = ejecutar_stress_tests(
        pesos
    )

    historico = stress_historico(
        retornos_portfolio
    )

    pd.DataFrame(
        [metricas]
    ).to_csv(
        RUTA_RESULTADOS
        / "metricas_riesgo.csv",
        index=False,
    )

    contribucion.to_csv(
        RUTA_RESULTADOS
        / "contribucion_riesgo.csv",
        index=False,
    )

    component_var.to_csv(
        RUTA_RESULTADOS
        / "component_var.csv",
        index=False,
    )

    stress.to_csv(
        RUTA_RESULTADOS
        / "stress_tests.csv",
        index=False,
    )

    historico.to_csv(
        RUTA_RESULTADOS
        / "stress_historico.csv",
        index=False,
    )

    retornos_portfolio.to_csv(
        RUTA_RESULTADOS
        / "retornos_portfolio.csv",
        header=[
            "retorno"
        ],
    )

    imprimir_metricas(
        metricas
    )

    imprimir_contribucion(
        contribucion
    )

    imprimir_stress(
        stress
    )

    print()
    print(
        f"Resultados: {RUTA_RESULTADOS}"
    )


if __name__ == "__main__":
    main()