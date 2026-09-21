from pathlib import Path

import numpy as np
import pandas as pd


RUTA_BASE = Path(__file__).resolve().parents[1]

RUTA_ENTRADA = (
    RUTA_BASE
    / "resultados"
    / "options_chain_real"
    / "QQQ"
    / "cadena_qqq_griegas.csv"
)

RUTA_SALIDA = (
    RUTA_BASE
    / "resultados"
    / "dealer_engine"
    / "QQQ"
)

MONEYNESS_MIN = 0.70
MONEYNESS_MAX = 1.30

IV_MIN = 0.03
IV_MAX = 3.00

SPREAD_MAX_PCT = 1.00

DTE_MAX = 365.0


def cargar_cadena() -> pd.DataFrame:
    """Carga la cadena real calculada previamente."""

    datos = pd.read_csv(
        RUTA_ENTRADA
    )

    columnas_numericas = [
        "dte",
        "spot",
        "strike",
        "moneyness",
        "bid",
        "ask",
        "mid",
        "volume",
        "openInterest",
        "impliedVolatility",
        "delta",
        "gamma",
        "theta",
        "vega",
        "vanna",
        "delta_decay",
    ]

    for columna in columnas_numericas:
        if columna in datos.columns:
            datos[columna] = pd.to_numeric(
                datos[columna],
                errors="coerce",
            )

    return datos


def limpiar_cadena(
    datos: pd.DataFrame,
) -> pd.DataFrame:
    """Aplica controles básicos de calidad y liquidez."""

    datos = datos.copy()

    datos["spread"] = (
        datos["ask"]
        - datos["bid"]
    )

    datos["spread_pct"] = np.where(
        datos["mid"] > 0,
        datos["spread"]
        / datos["mid"],
        np.nan,
    )

    datos["distancia_spot_pct"] = (
        (
            datos["strike"]
            / datos["spot"]
        )
        - 1.0
    ) * 100.0

    datos["notional_oi"] = (
        datos["openInterest"]
        * 100.0
        * datos["spot"]
    )

    condiciones = (
        datos["openInterest"].fillna(0) > 0
    )

    condiciones &= (
        datos["impliedVolatility"]
        .between(
            IV_MIN,
            IV_MAX,
        )
    )

    condiciones &= (
        datos["moneyness"]
        .between(
            MONEYNESS_MIN,
            MONEYNESS_MAX,
        )
    )

    condiciones &= (
        datos["dte"] > 0
    )

    condiciones &= (
        datos["dte"] <= DTE_MAX
    )

    condiciones &= (
        datos["ask"] >= datos["bid"]
    )

    condiciones &= (
        datos["mid"] > 0
    )

    condiciones &= (
        datos["spread_pct"]
        <= SPREAD_MAX_PCT
    )

    columnas_griegas = [
        "delta",
        "gamma",
        "theta",
        "vega",
        "vanna",
        "delta_decay",
    ]

    for columna in columnas_griegas:
        condiciones &= np.isfinite(
            datos[columna]
        )

    filtrados = (
        datos[
            condiciones
        ]
        .copy()
        .reset_index(drop=True)
    )

    return filtrados


def main() -> None:
    """Genera la cadena limpia."""

    RUTA_SALIDA.mkdir(
        parents=True,
        exist_ok=True,
    )

    datos = cargar_cadena()

    filtrados = limpiar_cadena(
        datos
    )

    datos.to_csv(
        RUTA_SALIDA
        / "cadena_raw.csv",
        index=False,
    )

    filtrados.to_csv(
        RUTA_SALIDA
        / "cadena_filtrada.csv",
        index=False,
    )

    print()
    print("=" * 70)
    print("LIMPIEZA DE CADENA QQQ")
    print("=" * 70)

    print(
        f"Contratos originales : {len(datos)}"
    )

    print(
        f"Contratos aceptados  : {len(filtrados)}"
    )

    print(
        f"Eliminados           : {len(datos) - len(filtrados)}"
    )

    print()
    print(
        "Calls:",
        (
            filtrados["tipo"]
            == "call"
        ).sum(),
    )

    print(
        "Puts :",
        (
            filtrados["tipo"]
            == "put"
        ).sum(),
    )


if __name__ == "__main__":
    main()