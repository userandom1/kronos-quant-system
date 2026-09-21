from pathlib import Path

import numpy as np
import pandas as pd


RUTA_BASE = Path(__file__).resolve().parents[1]

RUTA_DATOS = (
    RUTA_BASE
    / "resultados"
    / "dealer_engine"
    / "QQQ"
    / "cadena_filtrada.csv"
)

RUTA_RESULTADOS = (
    RUTA_BASE
    / "resultados"
    / "dealer_engine"
    / "QQQ"
)

MULTIPLICADOR = 100.0


def calcular_exposiciones(
    datos: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calcula exposiciones derivadas del Open Interest.

    Las columnas sin sufijo dealer representan
    exposición matemática del conjunto de contratos.
    """

    datos = datos.copy()

    oi = datos[
        "openInterest"
    ].fillna(0)

    spot = datos["spot"]

    # -------------------------------------------------------------------------
    # Delta Exposure
    # -------------------------------------------------------------------------

    datos["dex"] = (
        datos["delta"]
        * oi
        * MULTIPLICADOR
        * spot
    )

    # -------------------------------------------------------------------------
    # Gamma Exposure para movimiento del 1 % del spot
    # -------------------------------------------------------------------------

    datos["gex_1pct"] = (
        datos["gamma"]
        * oi
        * MULTIPLICADOR
        * spot**2
        * 0.01
    )

    # -------------------------------------------------------------------------
    # Theta: P&L teórico diario por OI
    # -------------------------------------------------------------------------

    datos["theta_exposure_dia"] = (
        datos["theta"]
        * oi
        * MULTIPLICADOR
    )

    # -------------------------------------------------------------------------
    # Vega: P&L por movimiento de 1 punto porcentual de IV
    # -------------------------------------------------------------------------

    datos["vega_exposure_1pt"] = (
        datos["vega"]
        * oi
        * MULTIPLICADOR
    )

    # -------------------------------------------------------------------------
    # Vanna:
    # cambio aproximado del hedge Delta en dólares
    # por +1 punto porcentual de IV
    # -------------------------------------------------------------------------

    datos["vanna_exposure_1pt"] = (
        datos["vanna"]
        * oi
        * MULTIPLICADOR
        * spot
    )

    # -------------------------------------------------------------------------
    # Delta Decay / Charm:
    # cambio aproximado diario del hedge Delta en dólares
    # -------------------------------------------------------------------------

    datos["charm_exposure_dia"] = (
        datos["delta_decay"]
        * oi
        * MULTIPLICADOR
        * spot
    )

    return datos


def aplicar_proxy_dealer(
    datos: pd.DataFrame,
) -> pd.DataFrame:
    """
    Aplica una hipótesis simplificada de posicionamiento.

    IMPORTANTE:
    Esta señal no es observable directamente.

    Convención V1:
    dealer short calls -> -1
    dealer long puts   -> +1
    """

    datos = datos.copy()

    datos["signo_dealer_proxy"] = np.where(
        datos["tipo"] == "call",
        -1.0,
        1.0,
    )

    columnas = [
        "dex",
        "gex_1pct",
        "theta_exposure_dia",
        "vega_exposure_1pt",
        "vanna_exposure_1pt",
        "charm_exposure_dia",
    ]

    for columna in columnas:
        datos[
            f"{columna}_dealer"
        ] = (
            datos[columna]
            * datos[
                "signo_dealer_proxy"
            ]
        )

    return datos


def agregar_por_strike(
    datos: pd.DataFrame,
) -> pd.DataFrame:
    """Agrega exposiciones dealer por strike."""

    columnas = [
        "dex_dealer",
        "gex_1pct_dealer",
        "theta_exposure_dia_dealer",
        "vega_exposure_1pt_dealer",
        "vanna_exposure_1pt_dealer",
        "charm_exposure_dia_dealer",
    ]

    agregado = (
        datos.groupby(
            "strike",
            as_index=False,
        )[columnas]
        .sum()
    )

    return agregado


def agregar_por_vencimiento(
    datos: pd.DataFrame,
) -> pd.DataFrame:
    """Agrega exposures por vencimiento."""

    columnas = [
        "dex_dealer",
        "gex_1pct_dealer",
        "theta_exposure_dia_dealer",
        "vega_exposure_1pt_dealer",
        "vanna_exposure_1pt_dealer",
        "charm_exposure_dia_dealer",
    ]

    return (
        datos.groupby(
            [
                "vencimiento",
                "dte",
            ],
            as_index=False,
        )[columnas]
        .sum()
    )


def main() -> None:
    """Calcula todas las exposiciones."""

    datos = pd.read_csv(
        RUTA_DATOS
    )

    datos = calcular_exposiciones(
        datos
    )

    datos = aplicar_proxy_dealer(
        datos
    )

    por_strike = agregar_por_strike(
        datos
    )

    por_vencimiento = (
        agregar_por_vencimiento(
            datos
        )
    )

    datos.to_csv(
        RUTA_RESULTADOS
        / "exposiciones_contratos.csv",
        index=False,
    )

    por_strike.to_csv(
        RUTA_RESULTADOS
        / "exposiciones_por_strike.csv",
        index=False,
    )

    por_vencimiento.to_csv(
        RUTA_RESULTADOS
        / "exposiciones_por_vencimiento.csv",
        index=False,
    )

    print()
    print("=" * 70)
    print("MOTOR DE EXPOSICIONES")
    print("=" * 70)

    print(
        f"Contratos procesados: {len(datos)}"
    )

    print()
    print(
        "Net GEX proxy:",
        f"{datos['gex_1pct_dealer'].sum():,.0f}",
    )

    print(
        "Net DEX proxy:",
        f"{datos['dex_dealer'].sum():,.0f}",
    )

    print(
        "Net Vanna proxy:",
        f"{datos['vanna_exposure_1pt_dealer'].sum():,.0f}",
    )

    print(
        "Net Charm proxy:",
        f"{datos['charm_exposure_dia_dealer'].sum():,.0f}",
    )


if __name__ == "__main__":
    main()