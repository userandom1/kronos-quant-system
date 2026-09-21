import numpy as np
import pandas as pd

from motor_portfolio.datos_portfolio import (
    RUTA_RESULTADOS,
    UNIVERSO_PORTFOLIO,
    calcular_retornos,
    descargar_precios,
    guardar_datos,
)
from motor_portfolio.optimizador_v1 import (
    construir_tabla_pesos,
)


SESIONES_ANUALES = 252


def calcular_metricas(
    retornos: pd.DataFrame,
    pesos: pd.DataFrame,
) -> pd.DataFrame:
    """Calcula métricas básicas por cartera."""

    resultados = []

    for nombre in pesos.columns:
        w = pesos[
            nombre
        ]

        retorno_cartera = (
            retornos
            @ w
        )

        retorno_anual = (
            retorno_cartera.mean()
            * SESIONES_ANUALES
        )

        volatilidad_anual = (
            retorno_cartera.std(
                ddof=1
            )
            * np.sqrt(
                SESIONES_ANUALES
            )
        )

        sharpe = (
            retorno_anual
            / volatilidad_anual
            if volatilidad_anual > 0
            else np.nan
        )

        curva = (
            1.0
            + retorno_cartera
        ).cumprod()

        drawdown = (
            curva
            / curva.cummax()
            - 1.0
        )

        max_drawdown = (
            drawdown.min()
        )

        resultados.append(
            {
                "cartera": nombre,
                "retorno_anual": retorno_anual,
                "volatilidad_anual": volatilidad_anual,
                "sharpe": sharpe,
                "max_drawdown": max_drawdown,
            }
        )

    return pd.DataFrame(
        resultados
    )


def imprimir_pesos(
    pesos: pd.DataFrame,
) -> None:
    """Muestra los pesos de cada cartera."""

    print()
    print("=" * 100)
    print(
        "PORTFOLIO ENGINE V1 - PESOS"
    )
    print("=" * 100)

    salida = (
        pesos
        * 100.0
    )

    print(
        salida.to_string(
            float_format=lambda x: (
                f"{x:,.2f}%"
            )
        )
    )


def imprimir_metricas(
    metricas: pd.DataFrame,
) -> None:
    """Muestra métricas de las carteras."""

    salida = metricas.copy()

    for columna in [
        "retorno_anual",
        "volatilidad_anual",
        "max_drawdown",
    ]:
        salida[
            columna
        ] = (
            salida[
                columna
            ]
            * 100.0
        )

    print()
    print("=" * 100)
    print(
        "PORTFOLIO ENGINE V1 - MÉTRICAS"
    )
    print("=" * 100)

    print(
        salida.to_string(
            index=False,
            float_format=lambda x: (
                f"{x:,.3f}"
            ),
        )
    )


def main() -> None:
    """Ejecuta Portfolio Engine V1."""

    print(
        "Descargando histórico..."
    )

    precios = descargar_precios(
        UNIVERSO_PORTFOLIO
    )

    retornos = calcular_retornos(
        precios
    )

    guardar_datos(
        precios,
        retornos,
    )

    print(
        "Optimizando carteras..."
    )

    pesos = construir_tabla_pesos(
        retornos
    )

    metricas = calcular_metricas(
        retornos,
        pesos,
    )

    RUTA_RESULTADOS.mkdir(
        parents=True,
        exist_ok=True,
    )

    pesos.to_csv(
        RUTA_RESULTADOS
        / "pesos_portfolio_v1.csv"
    )

    metricas.to_csv(
        RUTA_RESULTADOS
        / "metricas_portfolio_v1.csv",
        index=False,
    )

    correlaciones = (
        retornos.corr()
    )

    correlaciones.to_csv(
        RUTA_RESULTADOS
        / "correlaciones.csv"
    )

    imprimir_pesos(
        pesos
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