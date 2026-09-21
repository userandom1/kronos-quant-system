from pathlib import Path

import numpy as np
import pandas as pd

from motor_opciones.griegas import (
    ParametrosOpcion,
    delta,
    delta_decay_por_dia,
    gamma,
    theta_por_dia,
    vanna_por_punto,
    vega_por_punto,
)

from motor_opciones.shocks_superficie_iv import (
    SHOCKS_CURVATURA,
    SHOCKS_IV_ATM,
    SHOCKS_SKEW,
    ShockSuperficieIV,
    aplicar_shock_iv,
)


# =============================================================================
# RUTAS
# =============================================================================

RUTA_BASE = Path(__file__).resolve().parents[1]

RUTA_ENTRADA = (
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
    / "intradia_v3"
)


# =============================================================================
# CONFIGURACIÓN
# =============================================================================

MULTIPLICADOR = 100.0

TIPO_INTERES = 0.04

DIVIDENDO = 0.01


SHOCKS_SPOT_PCT = (
    -2.00,
    -1.50,
    -1.00,
    -0.75,
    -0.50,
    -0.25,
    0.00,
    0.25,
    0.50,
    0.75,
    1.00,
    1.50,
    2.00,
)


# Aproximación en días naturales.
DECAIMIENTOS_DIAS = (
    0.00,
    0.25,
    0.50,
    1.00,
)


# =============================================================================
# CARGA
# =============================================================================


def cargar_cadena() -> pd.DataFrame:
    """Carga la cadena filtrada del Dealer Engine."""

    datos = pd.read_csv(
        RUTA_ENTRADA
    )

    columnas = [
        "dte",
        "spot",
        "strike",
        "openInterest",
        "impliedVolatility",
    ]

    for columna in columnas:
        datos[columna] = pd.to_numeric(
            datos[columna],
            errors="coerce",
        )

    datos = datos.dropna(
        subset=[
            "tipo",
            "dte",
            "spot",
            "strike",
            "openInterest",
            "impliedVolatility",
        ]
    )

    return datos.reset_index(
        drop=True
    )


# =============================================================================
# PROXY DEALER
# =============================================================================


def signo_dealer(
    tipo: str,
) -> float:
    """
    Hipótesis V3 de posición dealer.

    Call:
        dealer short -> -1

    Put:
        dealer long -> +1

    No es una posición observada.
    """

    if tipo == "call":
        return -1.0

    return 1.0


# =============================================================================
# REPRICING
# =============================================================================


def calcular_escenario(
    datos: pd.DataFrame,
    spot_escenario: float,
    shock_spot_pct: float,
    shock_iv: ShockSuperficieIV,
    decaimiento_dias: float,
) -> dict[str, float]:
    """Recalcula la cadena completa bajo un escenario."""

    net_dex = 0.0
    net_gex = 0.0
    net_theta = 0.0
    net_vega = 0.0
    net_vanna = 0.0
    net_charm = 0.0

    contratos_activos = 0

    for fila in datos.itertuples():
        dte_restante = (
            float(fila.dte)
            - decaimiento_dias
        )

        # Una opción ya vencida deja de formar parte del libro.
        if dte_restante <= 0:
            continue

        oi = float(
            fila.openInterest
        )

        if oi <= 0:
            continue

        strike = float(
            fila.strike
        )

        log_moneyness = float(
            np.log(
                strike
                / spot_escenario
            )
        )

        iv_escenario = aplicar_shock_iv(
            iv_base=float(
                fila.impliedVolatility
            ),
            log_moneyness=log_moneyness,
            shock=shock_iv,
        )

        parametros = ParametrosOpcion(
            spot=spot_escenario,
            strike=strike,
            tiempo=(
                dte_restante
                / 365.0
            ),
            volatilidad=iv_escenario,
            tipo_interes=TIPO_INTERES,
            dividendo=DIVIDENDO,
            tipo=fila.tipo,
        )

        signo = signo_dealer(
            fila.tipo
        )

        delta_valor = delta(
            parametros
        )

        gamma_valor = gamma(
            parametros
        )

        theta_valor = theta_por_dia(
            parametros
        )

        vega_valor = vega_por_punto(
            parametros
        )

        vanna_valor = vanna_por_punto(
            parametros
        )

        charm_valor = delta_decay_por_dia(
            parametros
        )

        net_dex += (
            delta_valor
            * oi
            * MULTIPLICADOR
            * spot_escenario
            * signo
        )

        net_gex += (
            gamma_valor
            * oi
            * MULTIPLICADOR
            * spot_escenario**2
            * 0.01
            * signo
        )

        net_theta += (
            theta_valor
            * oi
            * MULTIPLICADOR
            * signo
        )

        net_vega += (
            vega_valor
            * oi
            * MULTIPLICADOR
            * signo
        )

        net_vanna += (
            vanna_valor
            * oi
            * MULTIPLICADOR
            * spot_escenario
            * signo
        )

        net_charm += (
            charm_valor
            * oi
            * MULTIPLICADOR
            * spot_escenario
            * signo
        )

        contratos_activos += 1

    return {
        "spot": spot_escenario,
        "shock_spot_pct": shock_spot_pct,
        "shock_iv_puntos": shock_iv.atm_puntos,
        "shock_skew": shock_iv.skew,
        "shock_curvatura": shock_iv.curvatura,
        "decaimiento_dias": decaimiento_dias,
        "contratos_activos": contratos_activos,
        "net_dex": net_dex,
        "net_gex_1pct": net_gex,
        "net_theta_dia": net_theta,
        "net_vega_1pt": net_vega,
        "net_vanna_1pt": net_vanna,
        "net_charm_dia": net_charm,
    }


# =============================================================================
# MATRIZ SPOT x IV x TIEMPO
# =============================================================================


def ejecutar_matriz_intradia(
    datos: pd.DataFrame,
) -> pd.DataFrame:
    """Calcula Spot x IV ATM x tiempo."""

    spot_base = float(
        datos["spot"].iloc[0]
    )

    resultados = []

    total = (
        len(SHOCKS_SPOT_PCT)
        * len(SHOCKS_IV_ATM)
        * len(DECAIMIENTOS_DIAS)
    )

    contador = 0

    print()
    print("=" * 80)
    print("DEALER SCENARIO ENGINE V3 - INTRADÍA")
    print("=" * 80)

    print(
        f"Spot base            : {spot_base:.4f}"
    )

    print(
        f"Contratos de entrada : {len(datos)}"
    )

    print(
        f"Escenarios principales: {total}"
    )

    print()

    for decaimiento in DECAIMIENTOS_DIAS:
        for shock_iv_atm in SHOCKS_IV_ATM:
            for shock_spot in SHOCKS_SPOT_PCT:
                contador += 1

                spot_escenario = (
                    spot_base
                    * (
                        1.0
                        + shock_spot
                        / 100.0
                    )
                )

                shock_iv = ShockSuperficieIV(
                    atm_puntos=shock_iv_atm,
                )

                resultado = calcular_escenario(
                    datos=datos,
                    spot_escenario=spot_escenario,
                    shock_spot_pct=shock_spot,
                    shock_iv=shock_iv,
                    decaimiento_dias=decaimiento,
                )

                resultados.append(
                    resultado
                )

                if contador % 25 == 0:
                    print(
                        f"[{contador}/{total}] "
                        f"Spot {shock_spot:+.2f}% | "
                        f"IV {shock_iv_atm:+.1f} pt | "
                        f"t +{decaimiento:.2f}d"
                    )

    return pd.DataFrame(
        resultados
    )


# =============================================================================
# MATRIZ DE SKEW
# =============================================================================


def ejecutar_matriz_skew(
    datos: pd.DataFrame,
) -> pd.DataFrame:
    """Calcula Spot x shock de skew a t=0."""

    spot_base = float(
        datos["spot"].iloc[0]
    )

    resultados = []

    for shock_skew in SHOCKS_SKEW:
        for shock_spot in SHOCKS_SPOT_PCT:
            spot_escenario = (
                spot_base
                * (
                    1.0
                    + shock_spot
                    / 100.0
                )
            )

            shock_iv = ShockSuperficieIV(
                skew=shock_skew,
            )

            resultados.append(
                calcular_escenario(
                    datos=datos,
                    spot_escenario=spot_escenario,
                    shock_spot_pct=shock_spot,
                    shock_iv=shock_iv,
                    decaimiento_dias=0.0,
                )
            )

    return pd.DataFrame(
        resultados
    )


# =============================================================================
# MATRIZ DE CURVATURA
# =============================================================================


def ejecutar_matriz_curvatura(
    datos: pd.DataFrame,
) -> pd.DataFrame:
    """Calcula Spot x shock de curvatura."""

    spot_base = float(
        datos["spot"].iloc[0]
    )

    resultados = []

    for shock_curvatura in SHOCKS_CURVATURA:
        for shock_spot in SHOCKS_SPOT_PCT:
            spot_escenario = (
                spot_base
                * (
                    1.0
                    + shock_spot
                    / 100.0
                )
            )

            shock_iv = ShockSuperficieIV(
                curvatura=shock_curvatura,
            )

            resultados.append(
                calcular_escenario(
                    datos=datos,
                    spot_escenario=spot_escenario,
                    shock_spot_pct=shock_spot,
                    shock_iv=shock_iv,
                    decaimiento_dias=0.0,
                )
            )

    return pd.DataFrame(
        resultados
    )


# =============================================================================
# DESCOMPOSICIÓN DEL HEDGE
# =============================================================================


def añadir_descomposicion_flujo(
    datos: pd.DataFrame,
) -> pd.DataFrame:
    """
    Descompone el cambio de hedge en:

    1. efecto Spot
    2. efecto IV
    3. efecto tiempo

    La descomposición es secuencial y suma exactamente
    el flujo total dentro del modelo.
    """

    datos = datos.copy()

    base = datos[
        (
            datos["shock_spot_pct"]
            == 0
        )
        & (
            datos["shock_iv_puntos"]
            == 0
        )
        & (
            datos["decaimiento_dias"]
            == 0
        )
    ]

    if base.empty:
        raise RuntimeError(
            "No se encuentra el escenario base."
        )

    dex_base = float(
        base["net_dex"].iloc[0]
    )

    dex_spot = (
        datos[
            (
                datos["shock_iv_puntos"]
                == 0
            )
            & (
                datos["decaimiento_dias"]
                == 0
            )
        ][
            [
                "shock_spot_pct",
                "net_dex",
            ]
        ]
        .rename(
            columns={
                "net_dex":
                "dex_spot_solo"
            }
        )
    )

    dex_spot_iv = (
        datos[
            datos[
                "decaimiento_dias"
            ]
            == 0
        ][
            [
                "shock_spot_pct",
                "shock_iv_puntos",
                "net_dex",
            ]
        ]
        .rename(
            columns={
                "net_dex":
                "dex_spot_iv"
            }
        )
    )

    datos = datos.merge(
        dex_spot,
        on="shock_spot_pct",
        how="left",
    )

    datos = datos.merge(
        dex_spot_iv,
        on=[
            "shock_spot_pct",
            "shock_iv_puntos",
        ],
        how="left",
    )

    # Hedge dealer = -posición Delta dealer.
    datos[
        "flujo_spot"
    ] = -(
        datos[
            "dex_spot_solo"
        ]
        - dex_base
    )

    datos[
        "flujo_iv"
    ] = -(
        datos[
            "dex_spot_iv"
        ]
        - datos[
            "dex_spot_solo"
        ]
    )

    datos[
        "flujo_tiempo"
    ] = -(
        datos[
            "net_dex"
        ]
        - datos[
            "dex_spot_iv"
        ]
    )

    datos[
        "flujo_hedge_total"
    ] = (
        datos["flujo_spot"]
        + datos["flujo_iv"]
        + datos["flujo_tiempo"]
    )

    return datos


# =============================================================================
# RESUMEN
# =============================================================================


def imprimir_resumen(
    escenarios: pd.DataFrame,
) -> None:
    """Muestra el escenario base y shocks pequeños."""

    base = escenarios[
        (
            escenarios[
                "shock_spot_pct"
            ]
            == 0
        )
        & (
            escenarios[
                "shock_iv_puntos"
            ]
            == 0
        )
        & (
            escenarios[
                "decaimiento_dias"
            ]
            == 0
        )
    ].iloc[0]

    print()
    print("=" * 80)
    print("RESULTADOS DEALER SCENARIO ENGINE V3")
    print("=" * 80)

    print(
        f"Spot base        : {base['spot']:.4f}"
    )

    print(
        f"Net GEX          : {base['net_gex_1pct']:,.0f}"
    )

    print(
        f"Net DEX          : {base['net_dex']:,.0f}"
    )

    print(
        f"Net Vanna        : {base['net_vanna_1pt']:,.0f}"
    )

    print(
        f"Net Charm        : {base['net_charm_dia']:,.0f}"
    )

    print()

    muestra = escenarios[
        (
            escenarios[
                "shock_iv_puntos"
            ]
            == 0
        )
        & (
            escenarios[
                "decaimiento_dias"
            ]
            == 0
        )
        & (
            escenarios[
                "shock_spot_pct"
            ].isin(
                [
                    -1.0,
                    -0.5,
                    -0.25,
                    0.0,
                    0.25,
                    0.5,
                    1.0,
                ]
            )
        )
    ][
        [
            "shock_spot_pct",
            "spot",
            "net_gex_1pct",
            "flujo_hedge_total",
        ]
    ]

    print(
        "ESCENARIOS INTRADÍA:"
    )

    print(
        muestra.to_string(
            index=False,
            float_format=lambda x: (
                f"{x:,.2f}"
            ),
        )
    )


# =============================================================================
# MAIN
# =============================================================================


def main() -> None:
    """Ejecuta Dealer Scenario Engine V3."""

    RUTA_RESULTADOS.mkdir(
        parents=True,
        exist_ok=True,
    )

    datos = cargar_cadena()

    escenarios = ejecutar_matriz_intradia(
        datos
    )

    escenarios = añadir_descomposicion_flujo(
        escenarios
    )

    escenarios_skew = ejecutar_matriz_skew(
        datos
    )

    escenarios_curvatura = (
        ejecutar_matriz_curvatura(
            datos
        )
    )

    escenarios.to_csv(
        RUTA_RESULTADOS
        / "escenarios_intradia.csv",
        index=False,
    )

    escenarios_skew.to_csv(
        RUTA_RESULTADOS
        / "escenarios_skew.csv",
        index=False,
    )

    escenarios_curvatura.to_csv(
        RUTA_RESULTADOS
        / "escenarios_curvatura.csv",
        index=False,
    )

    imprimir_resumen(
        escenarios
    )

    print()
    print(
        f"Resultados: {RUTA_RESULTADOS}"
    )


if __name__ == "__main__":
    main()