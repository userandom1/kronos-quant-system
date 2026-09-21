from __future__ import annotations

import pandas as pd

from motor_validacion.backtest_composite import (
    HORIZONTES,
    validar_horizonte,
)
from motor_validacion.historico_senales import (
    RUTA_RESULTADOS,
    UNIVERSO,
    construir_composite_historico,
    descargar_precios,
    guardar_historico,
)


def imprimir_resumen(
    resumen: pd.DataFrame,
) -> None:
    """Muestra los resultados principales."""

    salida = resumen.copy()

    columnas_pct = [
        "directional_accuracy",
        "q1_retorno_medio",
        "q5_retorno_medio",
        "spread_q5_q1",
        "q5_max_drawdown",
        "q5_hit_rate",
        "ls_max_drawdown",
        "ls_hit_rate",
        "ic_hit_rate",
    ]

    for columna in columnas_pct:
        salida[columna] = (
            salida[columna]
            * 100.0
        )

    print()
    print("=" * 145)
    print(
        "VALIDACIÓN COMPOSITE SIGNALS V1"
    )
    print("=" * 145)

    columnas = [
        "horizonte_dias",
        "ic_medio",
        "ic_mediana",
        "ic_hit_rate",
        "directional_accuracy",
        "q1_retorno_medio",
        "q5_retorno_medio",
        "spread_q5_q1",
        "q5_sharpe",
        "ls_sharpe",
        "q5_max_drawdown",
        "ls_max_drawdown",
    ]

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
    """Ejecuta la validación histórica completa."""

    print(
        "Descargando histórico..."
    )

    precios = descargar_precios(
        UNIVERSO,
        periodo="10y",
    )

    print(
        "Construyendo Composite histórico..."
    )

    composite = (
        construir_composite_historico(
            precios
        )
    )

    guardar_historico(
        precios,
        composite,
    )

    resumenes = []

    for horizonte in HORIZONTES:
        print(
            f"Validando horizonte "
            f"{horizonte}D..."
        )

        resumen, quintiles = (
            validar_horizonte(
                precios=precios,
                senal=composite,
                horizonte=horizonte,
            )
        )

        resumenes.append(
            resumen
        )

        quintiles.to_csv(
            RUTA_RESULTADOS
            / (
                f"quintiles_"
                f"{horizonte}d.csv"
            )
        )

    resumen_df = pd.DataFrame(
        resumenes
    )

    resumen_df.to_csv(
        RUTA_RESULTADOS
        / "resumen_validacion_v1.csv",
        index=False,
    )

    imprimir_resumen(
        resumen_df
    )

    print()
    print(
        f"Resultados: {RUTA_RESULTADOS}"
    )


if __name__ == "__main__":
    main()