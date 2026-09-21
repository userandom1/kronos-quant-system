from pathlib import Path

import pandas as pd


RUTA_BASE = Path(__file__).resolve().parents[1]

RUTA_RESULTADOS = (
    RUTA_BASE
    / "resultados"
    / "dealer_engine"
    / "QQQ"
)


def obtener_extremos(
    datos: pd.DataFrame,
    columna: str,
    n: int = 10,
) -> pd.DataFrame:
    """Obtiene los strikes con mayor exposición absoluta."""

    resultado = datos.copy()

    resultado[
        "magnitud"
    ] = resultado[
        columna
    ].abs()

    return (
        resultado
        .sort_values(
            "magnitud",
            ascending=False,
        )
        .head(n)
    )


def main() -> None:
    """Detecta niveles relevantes de exposición."""

    datos = pd.read_csv(
        RUTA_RESULTADOS
        / "exposiciones_por_strike.csv"
    )

    metricas = {
        "GEX": "gex_1pct_dealer",
        "DEX": "dex_dealer",
        "VANNA": "vanna_exposure_1pt_dealer",
        "CHARM": "charm_exposure_dia_dealer",
    }

    print()
    print("=" * 80)
    print("NIVELES DEALER PROXY")
    print("=" * 80)

    for nombre, columna in metricas.items():
        extremos = obtener_extremos(
            datos,
            columna,
        )

        extremos.to_csv(
            RUTA_RESULTADOS
            / f"niveles_{nombre.lower()}.csv",
            index=False,
        )

        print()
        print(
            f"TOP {nombre}"
        )

        print(
            extremos[
                [
                    "strike",
                    columna,
                ]
            ]
            .to_string(
                index=False
            )
        )


if __name__ == "__main__":
    main()