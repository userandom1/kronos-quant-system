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
    / "escenarios_v2"
)


# =============================================================================
# CONFIGURACIÓN
# =============================================================================

MULTIPLICADOR = 100.0

TIPO_INTERES = 0.04

DIVIDENDO = 0.01

SHOCKS_SPOT_PCT = np.arange(
    -10.0,
    10.01,
    1.0,
)

SHOCKS_IV_PUNTOS = (
    -10.0,
    -5.0,
    -2.0,
    0.0,
    2.0,
    5.0,
    10.0,
)

DECAIMIENTOS_DIAS = (
    0.0,
    1.0,
    2.0,
    5.0,
)

IV_MINIMA = 0.01

DTE_MINIMO = 0.01


# =============================================================================
# DATOS
# =============================================================================


def cargar_cadena() -> pd.DataFrame:
    """Carga y prepara la cadena de opciones filtrada."""

    datos = pd.read_csv(
        RUTA_ENTRADA
    )

    columnas_numericas = [
        "dte",
        "spot",
        "strike",
        "openInterest",
        "impliedVolatility",
    ]

    for columna in columnas_numericas:
        datos[columna] = pd.to_numeric(
            datos[columna],
            errors="coerce",
        )

    datos = datos.dropna(
        subset=[
            "dte",
            "spot",
            "strike",
            "openInterest",
            "impliedVolatility",
            "tipo",
        ]
    )

    return datos.reset_index(
        drop=True
    )


# =============================================================================
# SIGNO DEALER PROXY
# =============================================================================


def obtener_signo_dealer(
    tipo: str,
) -> float:
    """
    Convención V2 del proxy dealer.

    Call:
        dealer short -> -1

    Put:
        dealer long -> +1

    Es una hipótesis, no una posición observada.
    """

    if tipo == "call":
        return -1.0

    return 1.0


# =============================================================================
# ESCENARIO INDIVIDUAL
# =============================================================================


def calcular_escenario(
    datos: pd.DataFrame,
    spot_escenario: float,
    shock_spot_pct: float,
    shock_iv_puntos: float,
    decaimiento_dias: float,
) -> dict[str, float]:
    """Recalcula todas las exposiciones para un escenario."""

    net_dex = 0.0
    net_gex = 0.0
    net_theta = 0.0
    net_vega = 0.0
    net_vanna = 0.0
    net_charm = 0.0

    for fila in datos.itertuples():
        oi = float(
            fila.openInterest
        )

        if oi <= 0:
            continue

        iv_escenario = max(
            float(
                fila.impliedVolatility
            )
            + shock_iv_puntos / 100.0,
            IV_MINIMA,
        )

        dte_escenario = max(
            float(fila.dte)
            - decaimiento_dias,
            DTE_MINIMO,
        )

        parametros = ParametrosOpcion(
            spot=spot_escenario,
            strike=float(
                fila.strike
            ),
            tiempo=(
                dte_escenario
                / 365.0
            ),
            volatilidad=iv_escenario,
            tipo_interes=TIPO_INTERES,
            dividendo=DIVIDENDO,
            tipo=fila.tipo,
        )

        signo_dealer = obtener_signo_dealer(
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

        charm_valor = (
            delta_decay_por_dia(
                parametros
            )
        )

        dex = (
            delta_valor
            * oi
            * MULTIPLICADOR
            * spot_escenario
            * signo_dealer
        )

        gex = (
            gamma_valor
            * oi
            * MULTIPLICADOR
            * spot_escenario**2
            * 0.01
            * signo_dealer
        )

        theta_exp = (
            theta_valor
            * oi
            * MULTIPLICADOR
            * signo_dealer
        )

        vega_exp = (
            vega_valor
            * oi
            * MULTIPLICADOR
            * signo_dealer
        )

        vanna_exp = (
            vanna_valor
            * oi
            * MULTIPLICADOR
            * spot_escenario
            * signo_dealer
        )

        charm_exp = (
            charm_valor
            * oi
            * MULTIPLICADOR
            * spot_escenario
            * signo_dealer
        )

        net_dex += dex
        net_gex += gex
        net_theta += theta_exp
        net_vega += vega_exp
        net_vanna += vanna_exp
        net_charm += charm_exp

    return {
        "shock_spot_pct": shock_spot_pct,
        "spot": spot_escenario,
        "shock_iv_puntos": shock_iv_puntos,
        "decaimiento_dias": decaimiento_dias,
        "net_dex": net_dex,
        "net_gex_1pct": net_gex,
        "net_theta_dia": net_theta,
        "net_vega_1pt": net_vega,
        "net_vanna_1pt": net_vanna,
        "net_charm_dia": net_charm,
    }


# =============================================================================
# MATRIZ COMPLETA
# =============================================================================


def ejecutar_escenarios(
    datos: pd.DataFrame,
) -> pd.DataFrame:
    """Ejecuta toda la matriz Spot x IV x tiempo."""

    spot_base = float(
        datos["spot"].iloc[0]
    )

    escenarios: list[dict] = []

    total = (
        len(SHOCKS_SPOT_PCT)
        * len(SHOCKS_IV_PUNTOS)
        * len(DECAIMIENTOS_DIAS)
    )

    contador = 0

    print()
    print("=" * 80)
    print("DEALER SCENARIO ENGINE V2")
    print("=" * 80)

    print(
        f"Spot base: {spot_base:.4f}"
    )

    print(
        f"Contratos: {len(datos)}"
    )

    print(
        f"Escenarios: {total}"
    )

    print()

    for decaimiento in DECAIMIENTOS_DIAS:
        for shock_iv in SHOCKS_IV_PUNTOS:
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

                if contador % 25 == 0:
                    print(
                        f"[{contador}/{total}] "
                        f"Spot {shock_spot:+.0f}% | "
                        f"IV {shock_iv:+.0f} pt | "
                        f"t +{decaimiento:g}d"
                    )

                resultado = calcular_escenario(
                    datos=datos,
                    spot_escenario=spot_escenario,
                    shock_spot_pct=float(
                        shock_spot
                    ),
                    shock_iv_puntos=float(
                        shock_iv
                    ),
                    decaimiento_dias=float(
                        decaimiento
                    ),
                )

                escenarios.append(
                    resultado
                )

    return pd.DataFrame(
        escenarios
    )


# =============================================================================
# HEDGE FLOW
# =============================================================================


def calcular_hedge_flow(
    escenarios: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calcula el cambio estimado de hedge respecto al escenario base.

    Posición dealer proxy:
        DEX

    Hedge teórico:
        -DEX

    Cambio del hedge:
        -(DEX_escenario - DEX_base)
    """

    escenarios = escenarios.copy()

    base = escenarios[
        (
            escenarios[
                "shock_spot_pct"
            ]
            == 0.0
        )
        & (
            escenarios[
                "shock_iv_puntos"
            ]
            == 0.0
        )
        & (
            escenarios[
                "decaimiento_dias"
            ]
            == 0.0
        )
    ]

    if base.empty:
        raise RuntimeError(
            "No existe escenario base."
        )

    dex_base = float(
        base["net_dex"].iloc[0]
    )

    escenarios[
        "cambio_dex_dealer"
    ] = (
        escenarios["net_dex"]
        - dex_base
    )

    escenarios[
        "flujo_hedge_estimado"
    ] = -(
        escenarios[
            "cambio_dex_dealer"
        ]
    )

    return escenarios


# =============================================================================
# PERFIL GAMMA
# =============================================================================


def generar_perfil_gamma(
    escenarios: pd.DataFrame,
) -> pd.DataFrame:
    """Obtiene Net GEX en función exclusivamente del spot."""

    return (
        escenarios[
            (
                escenarios[
                    "shock_iv_puntos"
                ]
                == 0.0
            )
            & (
                escenarios[
                    "decaimiento_dias"
                ]
                == 0.0
            )
        ]
        .sort_values(
            "spot"
        )
        .reset_index(
            drop=True
        )
    )


# =============================================================================
# GAMMA FLIP
# =============================================================================


def calcular_gamma_flip(
    perfil: pd.DataFrame,
) -> pd.DataFrame:
    """
    Busca cruces de Net GEX por cero.

    Utiliza interpolación lineal entre escenarios
    consecutivos.
    """

    resultados = []

    perfil = perfil.sort_values(
        "spot"
    )

    valores = perfil[
        [
            "spot",
            "net_gex_1pct",
        ]
    ].to_numpy()

    for i in range(
        len(valores) - 1
    ):
        spot_1 = float(
            valores[i, 0]
        )

        gex_1 = float(
            valores[i, 1]
        )

        spot_2 = float(
            valores[i + 1, 0]
        )

        gex_2 = float(
            valores[i + 1, 1]
        )

        if gex_1 == 0:
            flip = spot_1

        elif (
            np.sign(gex_1)
            != np.sign(gex_2)
        ):
            flip = (
                spot_1
                + (
                    0.0 - gex_1
                )
                * (
                    spot_2
                    - spot_1
                )
                / (
                    gex_2
                    - gex_1
                )
            )

        else:
            continue

        resultados.append(
            {
                "gamma_flip": flip,
                "spot_inferior": spot_1,
                "gex_inferior": gex_1,
                "spot_superior": spot_2,
                "gex_superior": gex_2,
            }
        )

    return pd.DataFrame(
        resultados
    )


# =============================================================================
# NIVELES ESTRUCTURALES
# =============================================================================


def calcular_niveles_estructurales(
    datos: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Detecta concentraciones estructurales por strike."""

    datos = datos.copy()

    datos[
        "signo_dealer"
    ] = np.where(
        datos["tipo"]
        == "call",
        -1.0,
        1.0,
    )

    datos[
        "gex_proxy_actual"
    ] = (
        datos["gamma"]
        * datos["openInterest"]
        * MULTIPLICADOR
        * datos["spot"]**2
        * 0.01
        * datos["signo_dealer"]
    )

    datos[
        "vanna_proxy_actual"
    ] = (
        datos["vanna"]
        * datos["openInterest"]
        * MULTIPLICADOR
        * datos["spot"]
        * datos["signo_dealer"]
    )

    datos[
        "charm_proxy_actual"
    ] = (
        datos["delta_decay"]
        * datos["openInterest"]
        * MULTIPLICADOR
        * datos["spot"]
        * datos["signo_dealer"]
    )

    agregado = (
        datos.groupby(
            "strike",
            as_index=False,
        )
        .agg(
            gex=(
                "gex_proxy_actual",
                "sum",
            ),
            vanna=(
                "vanna_proxy_actual",
                "sum",
            ),
            charm=(
                "charm_proxy_actual",
                "sum",
            ),
        )
    )

    call_oi = (
        datos[
            datos["tipo"]
            == "call"
        ]
        .groupby(
            "strike",
            as_index=False,
        )["openInterest"]
        .sum()
        .rename(
            columns={
                "openInterest":
                "call_oi"
            }
        )
    )

    put_oi = (
        datos[
            datos["tipo"]
            == "put"
        ]
        .groupby(
            "strike",
            as_index=False,
        )["openInterest"]
        .sum()
        .rename(
            columns={
                "openInterest":
                "put_oi"
            }
        )
    )

    concentracion = (
        call_oi.merge(
            put_oi,
            on="strike",
            how="outer",
        )
        .fillna(0)
    )

    niveles = []

    if not agregado.empty:
        niveles.extend(
            [
                {
                    "nivel":
                    "Major Positive Gamma Node",
                    "strike": float(
                        agregado.loc[
                            agregado["gex"].idxmax(),
                            "strike",
                        ]
                    ),
                },
                {
                    "nivel":
                    "Major Negative Gamma Node",
                    "strike": float(
                        agregado.loc[
                            agregado["gex"].idxmin(),
                            "strike",
                        ]
                    ),
                },
                {
                    "nivel":
                    "Vanna Node",
                    "strike": float(
                        agregado.loc[
                            agregado[
                                "vanna"
                            ].abs().idxmax(),
                            "strike",
                        ]
                    ),
                },
                {
                    "nivel":
                    "Charm Node",
                    "strike": float(
                        agregado.loc[
                            agregado[
                                "charm"
                            ].abs().idxmax(),
                            "strike",
                        ]
                    ),
                },
            ]
        )

    if not concentracion.empty:
        niveles.extend(
            [
                {
                    "nivel":
                    "Call Wall Proxy",
                    "strike": float(
                        concentracion.loc[
                            concentracion[
                                "call_oi"
                            ].idxmax(),
                            "strike",
                        ]
                    ),
                },
                {
                    "nivel":
                    "Put Wall Proxy",
                    "strike": float(
                        concentracion.loc[
                            concentracion[
                                "put_oi"
                            ].idxmax(),
                            "strike",
                        ]
                    ),
                },
            ]
        )

    return (
        pd.DataFrame(
            niveles
        ),
        concentracion,
    )


# =============================================================================
# MAIN
# =============================================================================


def main() -> None:
    """Ejecuta Dealer Scenario Engine V2."""

    RUTA_RESULTADOS.mkdir(
        parents=True,
        exist_ok=True,
    )

    datos = cargar_cadena()

    escenarios = ejecutar_escenarios(
        datos
    )

    escenarios = calcular_hedge_flow(
        escenarios
    )

    perfil_gamma = generar_perfil_gamma(
        escenarios
    )

    gamma_flip = calcular_gamma_flip(
        perfil_gamma
    )

    (
        niveles,
        concentracion,
    ) = calcular_niveles_estructurales(
        datos
    )

    escenarios.to_csv(
        RUTA_RESULTADOS
        / "escenarios_completos.csv",
        index=False,
    )

    perfil_gamma.to_csv(
        RUTA_RESULTADOS
        / "perfil_gamma_spot.csv",
        index=False,
    )

    gamma_flip.to_csv(
        RUTA_RESULTADOS
        / "gamma_flip.csv",
        index=False,
    )

    niveles.to_csv(
        RUTA_RESULTADOS
        / "niveles_estructurales.csv",
        index=False,
    )

    concentracion.to_csv(
        RUTA_RESULTADOS
        / "concentracion_oi_strike.csv",
        index=False,
    )

    print()
    print("=" * 80)
    print("RESULTADOS DEALER SCENARIO ENGINE V2")
    print("=" * 80)

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
    print(
        f"Spot base          : "
        f"{base['spot']:.4f}"
    )

    print(
        f"Net GEX base       : "
        f"{base['net_gex_1pct']:,.0f}"
    )

    print(
        f"Net DEX base       : "
        f"{base['net_dex']:,.0f}"
    )

    print(
        f"Net Vanna base     : "
        f"{base['net_vanna_1pt']:,.0f}"
    )

    print(
        f"Net Charm base     : "
        f"{base['net_charm_dia']:,.0f}"
    )

    print()

    if gamma_flip.empty:
        print(
            "Gamma Flip: no encontrado "
            "dentro del rango ±10 %."
        )

    else:
        print(
            "Gamma Flip(s):"
        )

        print(
            gamma_flip.to_string(
                index=False,
                float_format=lambda x: (
                    f"{x:,.4f}"
                ),
            )
        )

    print()
    print(
        "Niveles estructurales:"
    )

    print(
        niveles.to_string(
            index=False
        )
    )

    print()
    print(
        f"Resultados: "
        f"{RUTA_RESULTADOS}"
    )


if __name__ == "__main__":
    main()