from __future__ import annotations

import numpy as np
import pandas as pd

from skfolio import RiskMeasure
from skfolio.optimization import (
    MeanRisk,
    ObjectiveFunction,
)

from motor_portfolio.optimizador_v2 import (
    pesos_signal_tilted,
)
from motor_validacion.composite_v2 import (
    construir_senales_v2,
)


SESIONES_ANUALES = 252
VENTANA_ESTIMACION = 504
PESO_MAXIMO = 0.35


def pesos_equal_weight(
    columnas: pd.Index,
) -> pd.Series:
    """Construye pesos equiponderados."""

    n = len(columnas)

    return pd.Series(
        1.0 / n,
        index=columnas,
        dtype=float,
    )


def pesos_minimum_variance(
    retornos: pd.DataFrame,
) -> pd.Series:
    """Calcula cartera de mínima varianza."""

    modelo = MeanRisk(
        objective_function=(
            ObjectiveFunction.MINIMIZE_RISK
        ),
        risk_measure=RiskMeasure.VARIANCE,
        min_weights=0.0,
        max_weights=PESO_MAXIMO,
    )

    modelo.fit(
        retornos
    )

    return pd.Series(
        modelo.weights_,
        index=retornos.columns,
        dtype=float,
    )


def pesos_maximum_sharpe(
    retornos: pd.DataFrame,
) -> pd.Series:
    """Calcula cartera de máximo Sharpe."""

    modelo = MeanRisk(
        objective_function=(
            ObjectiveFunction.MAXIMIZE_RATIO
        ),
        risk_measure=(
            RiskMeasure.STANDARD_DEVIATION
        ),
        min_weights=0.0,
        max_weights=PESO_MAXIMO,
    )

    modelo.fit(
        retornos
    )

    return pd.Series(
        modelo.weights_,
        index=retornos.columns,
        dtype=float,
    )


def construir_alpha_historico(
    precios: pd.DataFrame,
) -> pd.DataFrame:
    """Construye el alpha histórico V2."""

    senales = construir_senales_v2(
        precios
    )

    return (
        0.40 * senales["MOMENTUM"]
        + 0.60 * senales["COMPOSITE_V2_60D"]
    )


def normalizar_pesos(
    pesos: pd.Series,
) -> pd.Series:
    """Normaliza pesos para que sumen uno."""

    suma = pesos.sum()

    if suma <= 0:
        raise ValueError(
            "Los pesos no suman un valor positivo."
        )

    return (
        pesos / suma
    )


def evolucionar_pesos(
    pesos: pd.Series,
    retornos_periodo: pd.DataFrame,
) -> tuple[pd.Series, pd.Series]:
    """
    Evoluciona una cartera buy-and-hold entre rebalanceos.

    Devuelve:
    - retornos diarios de cartera
    - pesos finales reales
    """

    pesos_actuales = (
        pesos.copy()
    )

    retornos_cartera = []

    for fecha, fila in retornos_periodo.iterrows():
        retorno_dia = float(
            pesos_actuales
            @ fila
        )

        retornos_cartera.append(
            (
                fecha,
                retorno_dia,
            )
        )

        valores = (
            pesos_actuales
            * (
                1.0
                + fila
            )
        )

        suma = valores.sum()

        if suma > 0:
            pesos_actuales = (
                valores / suma
            )

    serie = pd.Series(
        {
            fecha: retorno
            for fecha, retorno
            in retornos_cartera
        },
        dtype=float,
    )

    return (
        serie,
        pesos_actuales,
    )


def calcular_turnover_real(
    pesos_objetivo: pd.Series,
    pesos_previos_reales: pd.Series | None,
) -> float:
    """Calcula turnover frente a pesos reales previos."""

    if pesos_previos_reales is None:
        return 1.0

    previos = (
        pesos_previos_reales
        .reindex(
            pesos_objetivo.index
        )
        .fillna(0.0)
    )

    return float(
        0.5
        * (
            pesos_objetivo
            - previos
        )
        .abs()
        .sum()
    )


def construir_carteras(
    ventana: pd.DataFrame,
    alpha_fecha: pd.Series,
) -> dict[str, pd.Series]:
    """Construye las carteras objetivo."""

    return {
        "Equal Weight": (
            pesos_equal_weight(
                ventana.columns
            )
        ),
        "Minimum Variance": (
            pesos_minimum_variance(
                ventana
            )
        ),
        "Maximum Sharpe": (
            pesos_maximum_sharpe(
                ventana
            )
        ),
        "Signal Tilted V2": (
            pesos_signal_tilted(
                retornos=ventana,
                alpha=alpha_fecha,
                aversion_riesgo=3.0,
                peso_maximo=PESO_MAXIMO,
            )
        ),
    }


def ejecutar_backtest(
    precios: pd.DataFrame,
    frecuencia_rebalanceo: int,
    coste_bps: float,
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
]:
    """Ejecuta backtest con drift real y costes."""

    retornos = (
        precios
        .pct_change()
        .dropna()
    )

    alpha_historico = (
        construir_alpha_historico(
            precios
        )
        .reindex(
            retornos.index
        )
    )

    nombres = [
        "Equal Weight",
        "Minimum Variance",
        "Maximum Sharpe",
        "Signal Tilted V2",
    ]

    series_cartera = {
        nombre: []
        for nombre in nombres
    }

    pesos_previos_reales = {
        nombre: None
        for nombre in nombres
    }

    historial_pesos = []
    historial_rebalanceos = []

    fechas = retornos.index

    indices_rebalanceo = range(
        VENTANA_ESTIMACION,
        len(fechas),
        frecuencia_rebalanceo,
    )

    for numero, posicion in enumerate(
        indices_rebalanceo,
        start=1,
    ):
        fecha_rebalanceo = (
            fechas[posicion]
        )

        inicio = (
            posicion
            - VENTANA_ESTIMACION
        )

        ventana = retornos.iloc[
            inicio:posicion
        ].copy()

        alpha_fecha = (
            alpha_historico.loc[
                fecha_rebalanceo
            ]
            .reindex(
                retornos.columns
            )
        )

        if alpha_fecha.isna().any():
            continue

        carteras = construir_carteras(
            ventana,
            alpha_fecha,
        )

        posicion_fin = min(
            posicion
            + frecuencia_rebalanceo,
            len(fechas),
        )

        periodo = retornos.iloc[
            posicion:posicion_fin
        ]

        for nombre, pesos_objetivo in carteras.items():
            pesos_objetivo = (
                normalizar_pesos(
                    pesos_objetivo
                    .reindex(
                        retornos.columns
                    )
                    .fillna(0.0)
                )
            )

            turnover = (
                calcular_turnover_real(
                    pesos_objetivo,
                    pesos_previos_reales[
                        nombre
                    ],
                )
            )

            coste = (
                turnover
                * coste_bps
                / 10000.0
            )

            (
                retorno_periodo,
                pesos_finales,
            ) = evolucionar_pesos(
                pesos_objetivo,
                periodo,
            )

            if not retorno_periodo.empty:
                retorno_periodo.iloc[
                    0
                ] -= coste

            series_cartera[
                nombre
            ].append(
                retorno_periodo
            )

            for ticker, peso in pesos_objetivo.items():
                historial_pesos.append(
                    {
                        "fecha": fecha_rebalanceo,
                        "rebalanceo": numero,
                        "cartera": nombre,
                        "ticker": ticker,
                        "peso_objetivo": peso,
                    }
                )

            historial_rebalanceos.append(
                {
                    "fecha": fecha_rebalanceo,
                    "rebalanceo": numero,
                    "cartera": nombre,
                    "turnover": turnover,
                    "coste": coste,
                    "frecuencia": frecuencia_rebalanceo,
                    "coste_bps": coste_bps,
                }
            )

            pesos_previos_reales[
                nombre
            ] = pesos_finales.copy()

    retornos_finales = {}

    for nombre, bloques in series_cartera.items():
        if bloques:
            retornos_finales[
                nombre
            ] = pd.concat(
                bloques
            ).sort_index()

    retornos_df = pd.DataFrame(
        retornos_finales
    )

    pesos_df = pd.DataFrame(
        historial_pesos
    )

    rebalanceos_df = pd.DataFrame(
        historial_rebalanceos
    )

    return (
        retornos_df,
        pesos_df,
        rebalanceos_df,
    )


def calcular_metricas(
    retornos: pd.DataFrame,
    rebalanceos: pd.DataFrame,
) -> pd.DataFrame:
    """Calcula métricas finales."""

    filas = []

    for nombre in retornos.columns:
        serie = (
            retornos[
                nombre
            ]
            .dropna()
        )

        if serie.empty:
            continue

        curva = (
            1.0
            + serie
        ).cumprod()

        anos = (
            len(serie)
            / SESIONES_ANUALES
        )

        valor_final = float(
            curva.iloc[-1]
        )

        cagr = (
            valor_final
            ** (
                1.0 / anos
            )
            - 1.0
            if (
                anos > 0
                and valor_final > 0
            )
            else np.nan
        )

        desviacion = (
            serie.std(
                ddof=1
            )
        )

        volatilidad = (
            desviacion
            * np.sqrt(
                SESIONES_ANUALES
            )
        )

        sharpe = (
            serie.mean()
            / desviacion
            * np.sqrt(
                SESIONES_ANUALES
            )
            if desviacion > 0
            else np.nan
        )

        drawdown = (
            curva
            / curva.cummax()
            - 1.0
        )

        max_drawdown = float(
            drawdown.min()
        )

        calmar = (
            cagr
            / abs(
                max_drawdown
            )
            if max_drawdown < 0
            else np.nan
        )

        reb = rebalanceos[
            rebalanceos[
                "cartera"
            ]
            == nombre
        ]

        filas.append(
            {
                "cartera": nombre,
                "cagr": cagr,
                "volatilidad": volatilidad,
                "sharpe": sharpe,
                "max_drawdown": max_drawdown,
                "calmar": calmar,
                "hit_rate": (
                    serie > 0
                ).mean(),
                "valor_final": valor_final,
                "turnover_medio": (
                    reb[
                        "turnover"
                    ].mean()
                ),
                "turnover_total": (
                    reb[
                        "turnover"
                    ].sum()
                ),
                "costes_totales": (
                    reb[
                        "coste"
                    ].sum()
                ),
            }
        )

    return pd.DataFrame(
        filas
    )