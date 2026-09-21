from __future__ import annotations

import numpy as np
import pandas as pd


SESIONES_ANUALES = 252

HORIZONTES = [
    1,
    5,
    10,
    20,
    60,
]


def retornos_futuros(
    precios: pd.DataFrame,
    horizonte: int,
) -> pd.DataFrame:
    """Calcula retorno futuro desde t hasta t+h."""

    return (
        precios.shift(
            -horizonte
        )
        / precios
        - 1.0
    )


def calcular_ic_diario(
    senal: pd.DataFrame,
    retorno_futuro: pd.DataFrame,
) -> pd.Series:
    """Calcula IC transversal diario."""

    indices = (
        senal.index
        .intersection(
            retorno_futuro.index
        )
    )

    valores = []

    for fecha in indices:
        x = senal.loc[
            fecha
        ]

        y = retorno_futuro.loc[
            fecha
        ]

        conjunto = pd.concat(
            [
                x.rename(
                    "senal"
                ),
                y.rename(
                    "retorno"
                ),
            ],
            axis=1,
        ).dropna()

        if len(conjunto) < 3:
            valores.append(
                np.nan
            )
            continue

        if (
            conjunto["senal"].std() == 0
            or conjunto["retorno"].std() == 0
        ):
            valores.append(
                np.nan
            )
            continue

        valores.append(
            conjunto[
                "senal"
            ].corr(
                conjunto[
                    "retorno"
                ]
            )
        )

    return pd.Series(
        valores,
        index=indices,
        name="ic",
    )


def directional_accuracy(
    senal: pd.DataFrame,
    retorno_futuro: pd.DataFrame,
) -> float:
    """Calcula acierto de signo señal-retorno."""

    alineados = pd.concat(
        [
            senal.stack().rename(
                "senal"
            ),
            retorno_futuro.stack().rename(
                "retorno"
            ),
        ],
        axis=1,
        join="inner",
    ).dropna()

    if alineados.empty:
        return np.nan

    aciertos = (
        np.sign(
            alineados["senal"]
        )
        == np.sign(
            alineados["retorno"]
        )
    )

    return float(
        aciertos.mean()
    )


def construir_quintiles(
    senal: pd.DataFrame,
    retorno_futuro: pd.DataFrame,
) -> pd.DataFrame:
    """Calcula retornos futuros medios por quintil."""

    filas = []

    for fecha in senal.index:
        if fecha not in retorno_futuro.index:
            continue

        conjunto = pd.concat(
            [
                senal.loc[
                    fecha
                ].rename(
                    "senal"
                ),
                retorno_futuro.loc[
                    fecha
                ].rename(
                    "retorno"
                ),
            ],
            axis=1,
        ).dropna()

        if len(conjunto) < 5:
            continue

        ranking = conjunto[
            "senal"
        ].rank(
            method="first"
        )

        try:
            conjunto[
                "quintil"
            ] = pd.qcut(
                ranking,
                5,
                labels=[
                    1,
                    2,
                    3,
                    4,
                    5,
                ],
            )

        except ValueError:
            continue

        promedio = (
            conjunto.groupby(
                "quintil",
                observed=True,
            )["retorno"]
            .mean()
        )

        fila = {
            "fecha": fecha,
        }

        for quintil in range(
            1,
            6,
        ):
            fila[
                f"q{quintil}"
            ] = promedio.get(
                quintil,
                np.nan,
            )

        filas.append(
            fila
        )

    if not filas:
        return pd.DataFrame()

    return (
        pd.DataFrame(
            filas
        )
        .set_index(
            "fecha"
        )
    )


def metricas_estrategia(
    retornos: pd.Series,
    horizonte: int,
) -> dict[str, float]:
    """Calcula métricas básicas de una estrategia."""

    retornos = retornos.dropna()

    if retornos.empty:
        return {
            "retorno_medio": np.nan,
            "sharpe": np.nan,
            "max_drawdown": np.nan,
            "hit_rate": np.nan,
        }

    factor_anual = (
        SESIONES_ANUALES
        / horizonte
    )

    volatilidad = retornos.std(
        ddof=1
    )

    sharpe = (
        retornos.mean()
        / volatilidad
        * np.sqrt(
            factor_anual
        )
        if volatilidad > 0
        else np.nan
    )

    curva = (
        1.0
        + retornos
    ).cumprod()

    drawdown = (
        curva
        / curva.cummax()
        - 1.0
    )

    return {
        "retorno_medio": float(
            retornos.mean()
        ),
        "sharpe": float(
            sharpe
        ),
        "max_drawdown": float(
            drawdown.min()
        ),
        "hit_rate": float(
            (
                retornos > 0
            ).mean()
        ),
    }


def validar_horizonte(
    precios: pd.DataFrame,
    senal: pd.DataFrame,
    horizonte: int,
) -> tuple[dict, pd.DataFrame]:
    """Valida la señal para un horizonte."""

    futuro = retornos_futuros(
        precios,
        horizonte,
    )

    ic_diario = calcular_ic_diario(
        senal,
        futuro,
    )

    da = directional_accuracy(
        senal,
        futuro,
    )

    quintiles = construir_quintiles(
        senal,
        futuro,
    )

    if quintiles.empty:
        q1 = pd.Series(
            dtype=float
        )
        q5 = pd.Series(
            dtype=float
        )
    else:
        q1 = quintiles["q1"]
        q5 = quintiles["q5"]

    long_short = (
        q5 - q1
    )

    metricas_q5 = metricas_estrategia(
        q5,
        horizonte,
    )

    metricas_ls = metricas_estrategia(
        long_short,
        horizonte,
    )

    resumen = {
        "horizonte_dias": horizonte,
        "ic_medio": float(
            ic_diario.mean()
        ),
        "ic_mediana": float(
            ic_diario.median()
        ),
        "ic_hit_rate": float(
            (
                ic_diario > 0
            ).mean()
        ),
        "directional_accuracy": da,
        "q1_retorno_medio": float(
            q1.mean()
        ),
        "q5_retorno_medio": float(
            q5.mean()
        ),
        "spread_q5_q1": float(
            long_short.mean()
        ),
        "q5_sharpe": (
            metricas_q5[
                "sharpe"
            ]
        ),
        "q5_max_drawdown": (
            metricas_q5[
                "max_drawdown"
            ]
        ),
        "q5_hit_rate": (
            metricas_q5[
                "hit_rate"
            ]
        ),
        "ls_sharpe": (
            metricas_ls[
                "sharpe"
            ]
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
    }

    return (
        resumen,
        quintiles,
    )