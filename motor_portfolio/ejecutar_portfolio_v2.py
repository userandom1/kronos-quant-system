from __future__ import annotations

import numpy as np
import pandas as pd

from motor_portfolio.datos_portfolio import (
    RUTA_RESULTADOS,
    UNIVERSO_PORTFOLIO,
    calcular_retornos,
    descargar_precios,
)
from motor_portfolio.optimizador_v2 import (
    construir_carteras_v2,
)
from motor_portfolio.senales_portfolio_v2 import (
    cargar_senales,
    construir_alpha_proxy,
)


SESIONES_ANUALES = 252

RUTA_RESULTADOS_V2 = (
    RUTA_RESULTADOS
    / "v2"
)


def calcular_metricas(
    retornos: pd.DataFrame,
    pesos: pd.DataFrame,
) -> pd.DataFrame:
    """Calcula métricas para cada cartera."""

    filas = []

    for nombre in pesos.columns:
        w = pesos[
            nombre
        ]

        retorno = (
            retornos
            @ w
        )

        retorno_anual = (
            retorno.mean()
            * SESIONES_ANUALES
        )

        volatilidad = (
            retorno.std(
                ddof=1
            )
            * np.sqrt(
                SESIONES_ANUALES
            )
        )

        sharpe = (
            retorno_anual
            / volatilidad
            if volatilidad > 0
            else np.nan
        )

        curva = (
            1.0 + retorno
        ).cumprod()

        drawdown = (
            curva
            / curva.cummax()
            - 1.0
        )

        filas.append(
            {
                "cartera": nombre,
                "retorno_anual": retorno_anual,
                "volatilidad_anual": volatilidad,
                "sharpe": sharpe,
                "max_drawdown": drawdown.min(),
            }
        )

    return pd.DataFrame(
        filas
    )


def imprimir_alpha(
    alpha: pd.Series,
) -> None:
    """Muestra el alpha proxy utilizado."""

    print()
    print("=" * 80)
    print("ALPHA PROXY V2")
    print("=" * 80)

    salida = alpha.sort_values(
        ascending=False
    )

    print(
        salida.to_string(
            float_format=lambda x: (
                f"{x:,.4f}"
            )
        )
    )


def imprimir_pesos(
    pesos: pd.DataFrame,
) -> None:
    """Muestra los pesos obtenidos."""

    print()
    print("=" * 105)
    print("PORTFOLIO ENGINE V2 - PESOS")
    print("=" * 105)

    print(
        (
            pesos * 100.0
        ).to_string(
            float_format=lambda x: (
                f"{x:,.2f}%"
            )
        )
    )


def imprimir_metricas(
    metricas: pd.DataFrame,
) -> None:
    """Muestra las métricas de las carteras."""

    salida = metricas.copy()

    for columna in [
        "retorno_anual",
        "volatilidad_anual",
        "max_drawdown",
    ]:
        salida[
            columna
        ] *= 100.0

    print()
    print("=" * 105)
    print("PORTFOLIO ENGINE V2 - MÉTRICAS")
    print("=" * 105)

    print(
        salida.to_string(
            index=False,
            float_format=lambda x: (
                f"{x:,.3f}"
            ),
        )
    )


def main() -> None:
    """Ejecuta Portfolio Engine V2."""

    RUTA_RESULTADOS_V2.mkdir(
        parents=True,
        exist_ok=True,
    )

    print(
        "Cargando señales V2..."
    )

    senales = cargar_senales()

    senales = senales[
        senales["ticker"].isin(
            UNIVERSO_PORTFOLIO
        )
    ].copy()

    alpha = construir_alpha_proxy(
        senales,
        peso_20d=0.40,
        peso_60d=0.60,
    )

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

    alpha = alpha.reindex(
        retornos.columns
    )

    print(
        "Optimizando Portfolio V2..."
    )

    pesos = construir_carteras_v2(
        retornos=retornos,
        alpha=alpha,
    )

    metricas = calcular_metricas(
        retornos,
        pesos,
    )

    correlaciones = (
        retornos.corr()
    )

    covarianza = (
        retornos.cov()
        * SESIONES_ANUALES
    )

    alpha.to_csv(
        RUTA_RESULTADOS_V2
        / "alpha_proxy_v2.csv",
        header=True,
    )

    pesos.to_csv(
        RUTA_RESULTADOS_V2
        / "pesos_portfolio_v2.csv"
    )

    metricas.to_csv(
        RUTA_RESULTADOS_V2
        / "metricas_portfolio_v2.csv",
        index=False,
    )

    correlaciones.to_csv(
        RUTA_RESULTADOS_V2
        / "correlaciones_v2.csv"
    )

    covarianza.to_csv(
        RUTA_RESULTADOS_V2
        / "covarianza_anual_v2.csv"
    )

    imprimir_alpha(
        alpha
    )

    imprimir_pesos(
        pesos
    )

    imprimir_metricas(
        metricas
    )

    print()
    print(
        f"Resultados: {RUTA_RESULTADOS_V2}"
    )


if __name__ == "__main__":
    main()