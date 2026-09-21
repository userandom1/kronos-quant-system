from __future__ import annotations

import numpy as np
import pandas as pd


SESIONES_ANUALES = 252


def retornos_futuros(
    precios: pd.DataFrame,
    horizonte: int,
) -> pd.DataFrame:
    """Calcula retornos futuros simples."""

    return (
        precios.shift(-horizonte)
        / precios
        - 1.0
    )


def fechas_no_solapadas(
    indice: pd.Index,
    horizonte: int,
) -> pd.Index:
    """Selecciona fechas de rebalanceo sin solapamiento."""

    return indice[::horizonte]


def calcular_ic(
    senal: pd.DataFrame,
    retorno_futuro: pd.DataFrame,
    horizonte: int,
) -> pd.Series:
    """Calcula IC transversal en fechas no solapadas."""

    fechas = fechas_no_solapadas(
        senal.index.intersection(
            retorno_futuro.index
        ),
        horizonte,
    )

    valores: dict[pd.Timestamp, float] = {}

    for fecha in fechas:
        conjunto = pd.concat(
            [
                senal.loc[fecha].rename("senal"),
                retorno_futuro.loc[fecha].rename(
                    "retorno"
                ),
            ],
            axis=1,
        ).dropna()

        if len(conjunto) < 4:
            continue

        if (
            conjunto["senal"].std() == 0
            or conjunto["retorno"].std() == 0
        ):
            continue

        valores[fecha] = conjunto[
            "senal"
        ].corr(
            conjunto["retorno"]
        )

    return pd.Series(
        valores,
        name="ic",
        dtype=float,
    )


def construir_long_short(
    senal: pd.DataFrame,
    retorno_futuro: pd.DataFrame,
    horizonte: int,
) -> pd.DataFrame:
    """Construye estrategia Q5, Q1 y Q5-Q1 sin solapamiento."""

    fechas = fechas_no_solapadas(
        senal.index.intersection(
            retorno_futuro.index
        ),
        horizonte,
    )

    filas = []

    for fecha in fechas:
        conjunto = pd.concat(
            [
                senal.loc[fecha].rename("senal"),
                retorno_futuro.loc[fecha].rename(
                    "retorno"
                ),
            ],
            axis=1,
        ).dropna()

        if len(conjunto) < 5:
            continue

        conjunto = conjunto.sort_values(
            "senal"
        )

        n = len(conjunto)

        tamano_extremo = max(
            1,
            int(np.ceil(n * 0.20)),
        )

        q1 = conjunto.head(
            tamano_extremo
        )

        q5 = conjunto.tail(
            tamano_extremo
        )

        retorno_q1 = q1[
            "retorno"
        ].mean()

        retorno_q5 = q5[
            "retorno"
        ].mean()

        filas.append(
            {
                "fecha": fecha,
                "q1": retorno_q1,
                "q5": retorno_q5,
                "long_short": (
                    retorno_q5
                    - retorno_q1
                ),
            }
        )

    if not filas:
        return pd.DataFrame()

    return (
        pd.DataFrame(filas)
        .set_index("fecha")
        .sort_index()
    )


def calcular_metricas(
    retornos: pd.Series,
    horizonte: int,
) -> dict[str, float]:
    """Calcula métricas sobre retornos no solapados."""

    retornos = retornos.dropna()

    if len(retornos) < 2:
        return {
            "retorno_medio": np.nan,
            "sharpe": np.nan,
            "max_drawdown": np.nan,
            "hit_rate": np.nan,
            "n_operaciones": len(retornos),
        }

    periodos_anuales = (
        SESIONES_ANUALES
        / horizonte
    )

    media = retornos.mean()

    volatilidad = retornos.std(
        ddof=1
    )

    sharpe = (
        media
        / volatilidad
        * np.sqrt(periodos_anuales)
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
        "retorno_medio": float(media),
        "sharpe": float(sharpe),
        "max_drawdown": float(
            drawdown.min()
        ),
        "hit_rate": float(
            (retornos > 0).mean()
        ),
        "n_operaciones": int(
            len(retornos)
        ),
    }


def block_bootstrap_ic(
    ic: pd.Series,
    bloque: int = 5,
    repeticiones: int = 2000,
    semilla: int = 42,
) -> tuple[float, float]:
    """Calcula intervalo bootstrap por bloques para el IC medio."""

    valores = (
        ic.dropna()
        .to_numpy(
            dtype=float
        )
    )

    n = len(valores)

    if n < bloque * 2:
        return np.nan, np.nan

    generador = np.random.default_rng(
        semilla
    )

    medias = []

    for _ in range(
        repeticiones
    ):
        muestra = []

        while len(muestra) < n:
            inicio = generador.integers(
                0,
                n - bloque + 1,
            )

            muestra.extend(
                valores[
                    inicio:
                    inicio + bloque
                ]
            )

        muestra = np.asarray(
            muestra[:n]
        )

        medias.append(
            muestra.mean()
        )

    inferior, superior = np.percentile(
        medias,
        [
            2.5,
            97.5,
        ],
    )

    return (
        float(inferior),
        float(superior),
    )