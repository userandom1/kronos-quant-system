from __future__ import annotations

from itertools import product
from pathlib import Path

import pandas as pd

from motor_portfolio.datos_portfolio import (
    UNIVERSO_PORTFOLIO,
    descargar_precios,
)
from motor_validacion.backtest_portfolio_v21 import (
    calcular_metricas,
    ejecutar_backtest,
)


RUTA_BASE = Path(__file__).resolve().parents[1]

RUTA_RESULTADOS = (
    RUTA_BASE
    / "resultados"
    / "validacion"
    / "portfolio_v21"
)

FRECUENCIAS = [
    10,
    20,
    40,
]

COSTES_BPS = [
    5.0,
    10.0,
    20.0,
    30.0,
]


def imprimir_resumen(
    resumen: pd.DataFrame,
) -> None:
    """Muestra el stress test del Signal Tilted."""

    signal = resumen[
        resumen["cartera"]
        == "Signal Tilted V2"
    ].copy()

    for columna in [
        "cagr",
        "volatilidad",
        "max_drawdown",
        "costes_totales",
    ]:
        signal[
            columna
        ] *= 100.0

    columnas = [
        "frecuencia",
        "coste_bps",
        "cagr",
        "volatilidad",
        "sharpe",
        "max_drawdown",
        "calmar",
        "valor_final",
        "turnover_total",
        "costes_totales",
    ]

    print()
    print("=" * 145)
    print(
        "STRESS TEST PORTFOLIO V2.1 - SIGNAL TILTED"
    )
    print("=" * 145)

    print(
        signal[
            columnas
        ]
        .sort_values(
            [
                "frecuencia",
                "coste_bps",
            ]
        )
        .to_string(
            index=False,
            float_format=lambda x: (
                f"{x:,.4f}"
            ),
        )
    )


def main() -> None:
    """Ejecuta stress test robusto."""

    RUTA_RESULTADOS.mkdir(
        parents=True,
        exist_ok=True,
    )

    print(
        "Descargando histórico..."
    )

    precios = descargar_precios(
        UNIVERSO_PORTFOLIO,
        periodo="10y",
    )

    resumenes = []

    for frecuencia, coste_bps in product(
        FRECUENCIAS,
        COSTES_BPS,
    ):
        print(
            f"Probando rebalanceo "
            f"{frecuencia}D | "
            f"{coste_bps:.0f} bps..."
        )

        (
            retornos,
            pesos,
            rebalanceos,
        ) = ejecutar_backtest(
            precios=precios,
            frecuencia_rebalanceo=frecuencia,
            coste_bps=coste_bps,
        )

        metricas = calcular_metricas(
            retornos,
            rebalanceos,
        )

        metricas[
            "frecuencia"
        ] = frecuencia

        metricas[
            "coste_bps"
        ] = coste_bps

        resumenes.append(
            metricas
        )

        etiqueta = (
            f"{frecuencia}d_"
            f"{int(coste_bps)}bps"
        )

        retornos.to_csv(
            RUTA_RESULTADOS
            / (
                f"retornos_"
                f"{etiqueta}.csv"
            )
        )

        pesos.to_csv(
            RUTA_RESULTADOS
            / (
                f"pesos_"
                f"{etiqueta}.csv"
            ),
            index=False,
        )

        rebalanceos.to_csv(
            RUTA_RESULTADOS
            / (
                f"rebalanceos_"
                f"{etiqueta}.csv"
            ),
            index=False,
        )

    resumen = pd.concat(
        resumenes,
        ignore_index=True,
    )

    resumen.to_csv(
        RUTA_RESULTADOS
        / "stress_test_portfolio_v21.csv",
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