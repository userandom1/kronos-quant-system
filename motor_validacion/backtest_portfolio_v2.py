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
FRECUENCIA_REBALANCEO = 20

PESO_MAXIMO = 0.35

COSTE_BPS = 10.0


def pesos_equal_weight(
    columnas: pd.Index,
) -> pd.Series:
    """Construye una cartera equiponderada."""

    numero_activos = len(columnas)

    return pd.Series(
        1.0 / numero_activos,
        index=columnas,
        dtype=float,
    )


def pesos_minimum_variance(
    retornos: pd.DataFrame,
) -> pd.Series:
    """Calcula mínima varianza con límite del 35%."""

    modelo = MeanRisk(
        objective_function=(
            ObjectiveFunction.MINIMIZE_RISK
        ),
        risk_measure=(
            RiskMeasure.VARIANCE
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


def pesos_maximum_sharpe(
    retornos: pd.DataFrame,
) -> pd.Series:
    """Calcula máximo Sharpe con límite del 35%."""

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
    """Construye el alpha histórico 20D/60D."""

    senales = construir_senales_v2(
        precios
    )

    signal_20d = senales[
        "MOMENTUM"
    ]

    signal_60d = senales[
        "COMPOSITE_V2_60D"
    ]

    alpha = (
        0.40 * signal_20d
        + 0.60 * signal_60d
    )

    return alpha


def calcular_turnover(
    pesos_nuevos: pd.Series,
    pesos_anteriores: pd.Series | None,
) -> float:
    """Calcula turnover unilateral de la cartera."""

    if pesos_anteriores is None:
        return float(
            pesos_nuevos.abs().sum()
        )

    anteriores = pesos_anteriores.reindex(
        pesos_nuevos.index
    ).fillna(0.0)

    return float(
        0.5
        * (
            pesos_nuevos
            - anteriores
        )
        .abs()
        .sum()
    )


def ejecutar_backtest(
    precios: pd.DataFrame,
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
]:
    """Ejecuta backtest walk-forward de las cuatro carteras."""

    retornos = (
        precios
        .pct_change()
        .dropna()
    )

    alpha_historico = (
        construir_alpha_historico(
            precios
        )
    )

    nombres = [
        "Equal Weight",
        "Minimum Variance",
        "Maximum Sharpe",
        "Signal Tilted V2",
    ]

    retornos_carteras = pd.DataFrame(
        index=retornos.index,
        columns=nombres,
        dtype=float,
    )

    historial_pesos = []

    historial_rebalanceos = []

    pesos_previos: dict[
        str,
        pd.Series | None
    ] = {
        nombre: None
        for nombre in nombres
    }

    fechas = retornos.index

    indices_rebalanceo = range(
        VENTANA_ESTIMACION,
        len(fechas),
        FRECUENCIA_REBALANCEO,
    )

    for numero_rebalanceo, posicion in enumerate(
        indices_rebalanceo,
        start=1,
    ):
        fecha = fechas[
            posicion
        ]

        inicio = (
            posicion
            - VENTANA_ESTIMACION
        )

        ventana = retornos.iloc[
            inicio:posicion
        ].copy()

        if len(ventana) < VENTANA_ESTIMACION:
            continue

        alpha_fecha = (
            alpha_historico
            .reindex(
                retornos.index
            )
            .loc[
                fecha
            ]
            .reindex(
                retornos.columns
            )
        )

        if alpha_fecha.isna().any():
            continue

        carteras = {
            "Equal Weight": (
                pesos_equal_weight(
                    retornos.columns
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

        posicion_fin = min(
            posicion
            + FRECUENCIA_REBALANCEO,
            len(fechas),
        )

        periodo = retornos.iloc[
            posicion:posicion_fin
        ]

        for nombre, pesos in carteras.items():
            pesos = pesos.reindex(
                retornos.columns
            ).fillna(0.0)

            turnover = calcular_turnover(
                pesos,
                pesos_previos[
                    nombre
                ],
            )

            coste = (
                turnover
                * COSTE_BPS
                / 10000.0
            )

            retorno_periodo = (
                periodo
                @ pesos
            )

            if len(
                retorno_periodo
            ) > 0:
                retorno_periodo.iloc[
                    0
                ] -= coste

            retornos_carteras.loc[
                retorno_periodo.index,
                nombre,
            ] = retorno_periodo

            for ticker, peso in pesos.items():
                historial_pesos.append(
                    {
                        "fecha": fecha,
                        "rebalanceo": numero_rebalanceo,
                        "cartera": nombre,
                        "ticker": ticker,
                        "peso": peso,
                    }
                )

            historial_rebalanceos.append(
                {
                    "fecha": fecha,
                    "rebalanceo": numero_rebalanceo,
                    "cartera": nombre,
                    "turnover": turnover,
                    "coste": coste,
                }
            )

            pesos_previos[
                nombre
            ] = pesos.copy()

    retornos_carteras = (
        retornos_carteras
        .dropna(
            how="all"
        )
        .fillna(0.0)
    )

    pesos_df = pd.DataFrame(
        historial_pesos
    )

    rebalanceos_df = pd.DataFrame(
        historial_rebalanceos
    )

    return (
        retornos_carteras,
        pesos_df,
        rebalanceos_df,
    )


def calcular_metricas(
    retornos: pd.DataFrame,
    rebalanceos: pd.DataFrame,
) -> pd.DataFrame:
    """Calcula métricas finales de cada cartera."""

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

        numero_dias = len(
            serie
        )

        anos = (
            numero_dias
            / SESIONES_ANUALES
        )

        valor_final = float(
            curva.iloc[-1]
        )

        if (
            anos > 0
            and valor_final > 0
        ):
            cagr = (
                valor_final
                ** (
                    1.0 / anos
                )
                - 1.0
            )
        else:
            cagr = np.nan

        volatilidad = (
            serie.std(
                ddof=1
            )
            * np.sqrt(
                SESIONES_ANUALES
            )
        )

        sharpe = (
            serie.mean()
            / serie.std(
                ddof=1
            )
            * np.sqrt(
                SESIONES_ANUALES
            )
            if serie.std(
                ddof=1
            ) > 0
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

        hit_rate = float(
            (
                serie > 0
            ).mean()
        )

        rebalanceos_cartera = (
            rebalanceos[
                rebalanceos[
                    "cartera"
                ]
                == nombre
            ]
        )

        turnover_medio = (
            rebalanceos_cartera[
                "turnover"
            ].mean()
        )

        turnover_total = (
            rebalanceos_cartera[
                "turnover"
            ].sum()
        )

        costes_totales = (
            rebalanceos_cartera[
                "coste"
            ].sum()
        )

        filas.append(
            {
                "cartera": nombre,
                "cagr": cagr,
                "volatilidad": volatilidad,
                "sharpe": sharpe,
                "max_drawdown": max_drawdown,
                "calmar": calmar,
                "hit_rate": hit_rate,
                "valor_final": valor_final,
                "turnover_medio": turnover_medio,
                "turnover_total": turnover_total,
                "costes_totales": costes_totales,
                "dias_backtest": numero_dias,
            }
        )

    return pd.DataFrame(
        filas
    )


def construir_curvas(
    retornos: pd.DataFrame,
) -> pd.DataFrame:
    """Construye curvas acumuladas."""

    return (
        1.0
        + retornos
    ).cumprod()