from __future__ import annotations

from pathlib import Path

import pandas as pd

from motor_portfolio.datos_portfolio import (
    UNIVERSO_PORTFOLIO,
    descargar_precios,
)
from motor_validacion.backtest_portfolio_v2 import (
    calcular_metricas,
    construir_curvas,
    ejecutar_backtest,
)


RUTA_BASE = Path(__file__).resolve().parents[1]

RUTA_RESULTADOS = (
    RUTA_BASE
    / "resultados"
    / "validacion"
    / "portfolio_v2"
)


def imprimir_metricas(
    metricas: pd.DataFrame,
) -> None:
    """Muestra resumen del backtest."""

    salida = metricas.copy()

    for columna in [
        "cagr",
        "volatilidad",
        "max_drawdown",
        "hit_rate",
        "turnover_medio",
        "costes_totales",
    ]:
        salida[
            columna
        ] *= 100.0

    columnas = [
        "cartera",
        "cagr",
        "volatilidad",
        "sharpe",
        "max_drawdown",
        "calmar",
        "hit_rate",
        "valor_final",
        "turnover_medio",
        "turnover_total",
        "costes_totales",
    ]

    print()
    print("=" * 145)
    print(
        "BACKTEST PORTFOLIO V2"
    )
    print("=" * 145)

    print(
        salida[
            columnas
        ].to_string(
            index=False,
            float_format=lambda x: (
                f"{x:,.4f}"
            ),
        )
    )


def main() -> None:
    """Ejecuta la validación Portfolio V2."""

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

    print(
        "Ejecutando walk-forward..."
    )

    (
        retornos,
        pesos,
        rebalanceos,
    ) = ejecutar_backtest(
        precios
    )

    metricas = calcular_metricas(
        retornos,
        rebalanceos,
    )

    curvas = construir_curvas(
        retornos
    )

    retornos.to_csv(
        RUTA_RESULTADOS
        / "retornos_diarios.csv"
    )

    curvas.to_csv(
        RUTA_RESULTADOS
        / "curvas_capital.csv"
    )

    pesos.to_csv(
        RUTA_RESULTADOS
        / "historial_pesos.csv",
        index=False,
    )

    rebalanceos.to_csv(
        RUTA_RESULTADOS
        / "rebalanceos.csv",
        index=False,
    )

    metricas.to_csv(
        RUTA_RESULTADOS
        / "metricas_backtest.csv",
        index=False,
    )

    imprimir_metricas(
        metricas
    )

    print()
    print(
        f"Resultados: {RUTA_RESULTADOS}"
    )


if __name__ == "__main__":
    main()