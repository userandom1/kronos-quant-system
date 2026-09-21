from __future__ import annotations

import pandas as pd

from motor_mercado.regimen_mercado_v2 import (
    RUTA_RESULTADOS,
    ejecutar_analisis,
)


def imprimir_resultados(
    componentes: dict,
) -> None:
    """Muestra el régimen actual."""

    print()
    print("=" * 95)
    print(
        "MARKET REGIME V2"
    )
    print("=" * 95)

    orden = [
        "tendencia",
        "volatilidad",
        "credito",
        "tipos",
        "cross_asset",
        "correlacion",
        "breadth",
        "global",
    ]

    for nombre in orden:
        datos = componentes[
            nombre
        ]

        print(
            f"{nombre.upper():<20} "
            f"{datos['estado']:<24} "
            f"score={datos['score']:+.3f}"
        )

    print()
    print(
        "RÉGIMEN GLOBAL:"
    )

    print(
        componentes[
            "global"
        ]["estado"]
    )

    print(
        "Score global:"
        f" {componentes['global']['score']:+.3f}"
    )


def main() -> None:
    """Ejecuta Market Regime V2."""

    RUTA_RESULTADOS.mkdir(
        parents=True,
        exist_ok=True,
    )

    print(
        "Descargando universo macro..."
    )

    (
        componentes,
        detalle,
    ) = ejecutar_analisis()

    detalle.to_csv(
        RUTA_RESULTADOS
        / "regimen_mercado_v2.csv",
        index=False,
    )

    global_df = pd.DataFrame(
        [
            {
                "score_global": (
                    componentes[
                        "global"
                    ]["score"]
                ),
                "regimen_global": (
                    componentes[
                        "global"
                    ]["estado"]
                ),
            }
        ]
    )

    global_df.to_csv(
        RUTA_RESULTADOS
        / "regimen_global.csv",
        index=False,
    )

    imprimir_resultados(
        componentes
    )

    print()
    print(
        f"Resultados: {RUTA_RESULTADOS}"
    )


if __name__ == "__main__":
    main()