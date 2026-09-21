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
from motor_validacion.composite_v2 import (
    construir_senales_v2,
)
from motor_validacion.historico_senales import (
    UNIVERSO,
    descargar_precios,
)


RUTA_BASE = Path(__file__).resolve().parents[1]

RUTA_RESULTADOS = (
    RUTA_BASE
    / "resultados"
    / "validacion"
    / "walk_forward_v2"
)

HORIZONTES = [
    20,
    60,
]

NUMERO_BLOQUES = 5


def crear_bloques_temporales(
    indice: pd.Index,
    numero_bloques: int,
) -> list[pd.Index]:
    """Divide cronológicamente el periodo disponible."""

    fechas = pd.Index(
        indice
    ).sort_values()

    return [
        bloque
        for bloque in np.array_split(
            fechas,
            numero_bloques,
        )
        if len(bloque) > 0
    ]


def evaluar_bloque(
    senal: pd.DataFrame,
    precios: pd.DataFrame,
    fechas: pd.Index,
    horizonte: int,
) -> dict[str, float]:
    """Evalúa una señal dentro de un bloque temporal."""

    futuro = retornos_futuros(
        precios,
        horizonte,
    )

    senal_bloque = senal.loc[
        senal.index.intersection(
            fechas
        )
    ]

    futuro_bloque = futuro.loc[
        futuro.index.intersection(
            fechas
        )
    ]

    ic = calcular_ic(
        senal_bloque,
        futuro_bloque,
        horizonte,
    )

    estrategia = construir_long_short(
        senal_bloque,
        futuro_bloque,
        horizonte,
    )

    if estrategia.empty:
        metricas = calcular_metricas(
            pd.Series(dtype=float),
            horizonte,
        )

        spread = np.nan

    else:
        metricas = calcular_metricas(
            estrategia["long_short"],
            horizonte,
        )

        spread = (
            estrategia["long_short"]
            .mean()
        )

    inferior, superior = (
        block_bootstrap_ic(
            ic
        )
    )

    return {
        "ic_medio": ic.mean(),
        "ic_mediana": ic.median(),
        "ic_hit_rate": (
            (ic > 0).mean()
            if len(ic)
            else np.nan
        ),
        "ic_ci95_inferior": inferior,
        "ic_ci95_superior": superior,
        "spread_q5_q1": spread,
        "ls_sharpe": metricas[
            "sharpe"
        ],
        "ls_max_drawdown": metricas[
            "max_drawdown"
        ],
        "ls_hit_rate": metricas[
            "hit_rate"
        ],
        "n_operaciones": metricas[
            "n_operaciones"
        ],
    }


def ejecutar_walk_forward(
    precios: pd.DataFrame,
    senales: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """Ejecuta validación temporal por bloques."""

    filas = []

    fechas_validas = precios.index[
        220:
    ]

    bloques = crear_bloques_temporales(
        fechas_validas,
        NUMERO_BLOQUES,
    )

    for nombre, senal in senales.items():
        for horizonte in HORIZONTES:
            for numero, bloque in enumerate(
                bloques,
                start=1,
            ):
                resultado = evaluar_bloque(
                    senal=senal,
                    precios=precios,
                    fechas=bloque,
                    horizonte=horizonte,
                )

                filas.append(
                    {
                        "senal": nombre,
                        "horizonte_dias": horizonte,
                        "bloque": numero,
                        "fecha_inicio": bloque[0],
                        "fecha_fin": bloque[-1],
                        **resultado,
                    }
                )

    return pd.DataFrame(
        filas
    )


def construir_resumen(
    datos: pd.DataFrame,
) -> pd.DataFrame:
    """Resume estabilidad de cada señal."""

    resumen = (
        datos.groupby(
            [
                "senal",
                "horizonte_dias",
            ],
            as_index=False,
        )
        .agg(
            ic_medio=(
                "ic_medio",
                "mean",
            ),
            ic_mediana=(
                "ic_medio",
                "median",
            ),
            ic_minimo=(
                "ic_medio",
                "min",
            ),
            ic_maximo=(
                "ic_medio",
                "max",
            ),
            bloques_ic_positivo=(
                "ic_medio",
                lambda x: (
                    x > 0
                ).mean(),
            ),
            spread_medio=(
                "spread_q5_q1",
                "mean",
            ),
            bloques_spread_positivo=(
                "spread_q5_q1",
                lambda x: (
                    x > 0
                ).mean(),
            ),
            sharpe_medio=(
                "ls_sharpe",
                "mean",
            ),
            hit_rate_medio=(
                "ls_hit_rate",
                "mean",
            ),
        )
    )

    return resumen


def imprimir_resumen(
    datos: pd.DataFrame,
) -> None:
    """Muestra resumen walk-forward."""

    salida = datos.copy()

    salida[
        "bloques_ic_positivo"
    ] *= 100.0

    salida[
        "spread_medio"
    ] *= 100.0

    salida[
        "bloques_spread_positivo"
    ] *= 100.0

    salida[
        "hit_rate_medio"
    ] *= 100.0

    columnas = [
        "senal",
        "horizonte_dias",
        "ic_medio",
        "ic_minimo",
        "ic_maximo",
        "bloques_ic_positivo",
        "spread_medio",
        "bloques_spread_positivo",
        "sharpe_medio",
        "hit_rate_medio",
    ]

    print()
    print("=" * 150)
    print(
        "COMPOSITE V2 - WALK FORWARD"
    )
    print("=" * 150)

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
    """Ejecuta Composite V2 Walk-Forward."""

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
        "Construyendo señales..."
    )

    senales = construir_senales_v2(
        precios
    )

    print(
        "Ejecutando validación temporal..."
    )

    resultados = ejecutar_walk_forward(
        precios,
        senales,
    )

    resumen = construir_resumen(
        resultados
    )

    resultados.to_csv(
        RUTA_RESULTADOS
        / "walk_forward_detalle.csv",
        index=False,
    )

    resumen.to_csv(
        RUTA_RESULTADOS
        / "walk_forward_resumen.csv",
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