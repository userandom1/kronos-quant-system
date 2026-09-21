from pathlib import Path

import numpy as np
import pandas as pd

from motor_opciones.griegas import (
    ParametrosOpcion,
    delta,
    delta_decay_por_dia,
    gamma,
    vanna_por_punto,
)


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
    / "v31"
)


MULTIPLICADOR = 100.0

TIPO_INTERES = 0.04
DIVIDENDO = 0.01


SHOCKS_SPOT_PCT = (
    -1.00,
    -0.50,
    -0.25,
    0.00,
    0.25,
    0.50,
    1.00,
)

SHOCKS_IV_PUNTOS = (
    -2.0,
    0.0,
    2.0,
)

DECAIMIENTOS_DIAS = (
    0.0,
    0.25,
    1.0,
)


def cargar_cadena() -> pd.DataFrame:
    """Carga la cadena limpia."""

    datos = pd.read_csv(
        RUTA_ENTRADA
    )

    return datos.dropna(
        subset=[
            "tipo",
            "dte",
            "spot",
            "strike",
            "openInterest",
            "impliedVolatility",
        ]
    ).reset_index(
        drop=True
    )


def signo_dealer(
    tipo: str,
) -> float:
    """Convención proxy dealer."""

    if tipo == "call":
        return -1.0

    return 1.0


def calcular_estado(
    datos: pd.DataFrame,
    spot: float,
    shock_iv_puntos: float,
    decaimiento_dias: float,
) -> dict[str, float]:
    """Calcula estado agregado de hedge y Greeks."""

    hedge_acciones = 0.0
    net_gamma_acciones = 0.0
    net_vanna_acciones = 0.0
    net_charm_acciones = 0.0

    contratos_activos = 0

    for fila in datos.itertuples():
        dte = (
            float(fila.dte)
            - decaimiento_dias
        )

        if dte <= 0:
            continue

        oi = float(
            fila.openInterest
        )

        if oi <= 0:
            continue

        iv = max(
            float(
                fila.impliedVolatility
            )
            + shock_iv_puntos / 100.0,
            0.01,
        )

        parametros = ParametrosOpcion(
            spot=spot,
            strike=float(
                fila.strike
            ),
            tiempo=dte / 365.0,
            volatilidad=iv,
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

        vanna_valor = vanna_por_punto(
            parametros
        )

        charm_valor = delta_decay_por_dia(
            parametros
        )

        hedge_acciones += (
            delta_valor
            * oi
            * MULTIPLICADOR
            * signo
        )

        net_gamma_acciones += (
            gamma_valor
            * oi
            * MULTIPLICADOR
            * signo
        )

        net_vanna_acciones += (
            vanna_valor
            * oi
            * MULTIPLICADOR
            * signo
        )

        net_charm_acciones += (
            charm_valor
            * oi
            * MULTIPLICADOR
            * signo
        )

        contratos_activos += 1

    return {
        "hedge_acciones": hedge_acciones,
        "gamma_acciones_por_dolar": (
            net_gamma_acciones
        ),
        "vanna_acciones_por_punto_iv": (
            net_vanna_acciones
        ),
        "charm_acciones_por_dia": (
            net_charm_acciones
        ),
        "contratos_activos": contratos_activos,
    }


def ejecutar_escenarios(
    datos: pd.DataFrame,
) -> pd.DataFrame:
    """Ejecuta escenarios intradía de precisión."""

    spot_base = float(
        datos["spot"].iloc[0]
    )

    estado_base = calcular_estado(
        datos=datos,
        spot=spot_base,
        shock_iv_puntos=0.0,
        decaimiento_dias=0.0,
    )

    hedge_base = estado_base[
        "hedge_acciones"
    ]

    filas = []

    for decaimiento in DECAIMIENTOS_DIAS:
        for shock_iv in SHOCKS_IV_PUNTOS:
            for shock_spot in SHOCKS_SPOT_PCT:
                spot = (
                    spot_base
                    * (
                        1.0
                        + shock_spot
                        / 100.0
                    )
                )

                estado = calcular_estado(
                    datos=datos,
                    spot=spot,
                    shock_iv_puntos=shock_iv,
                    decaimiento_dias=decaimiento,
                )

                flujo_acciones_total = -(
                    estado[
                        "hedge_acciones"
                    ]
                    - hedge_base
                )

                flujo_dolares_total = (
                    flujo_acciones_total
                    * spot
                )

                filas.append(
                    {
                        "shock_spot_pct": shock_spot,
                        "spot": spot,
                        "shock_iv_puntos": shock_iv,
                        "decaimiento_dias": decaimiento,
                        "hedge_acciones": estado[
                            "hedge_acciones"
                        ],
                        "flujo_acciones_total": (
                            flujo_acciones_total
                        ),
                        "flujo_dolares_total": (
                            flujo_dolares_total
                        ),
                        "gamma_acciones_por_dolar": (
                            estado[
                                "gamma_acciones_por_dolar"
                            ]
                        ),
                        "vanna_acciones_por_punto_iv": (
                            estado[
                                "vanna_acciones_por_punto_iv"
                            ]
                        ),
                        "charm_acciones_por_dia": (
                            estado[
                                "charm_acciones_por_dia"
                            ]
                        ),
                        "contratos_activos": estado[
                            "contratos_activos"
                        ],
                    }
                )

    return pd.DataFrame(
        filas
    )


def añadir_descomposicion(
    escenarios: pd.DataFrame,
) -> pd.DataFrame:
    """Descompone el hedge flow en Gamma, Vanna y Charm."""

    datos = escenarios.copy()

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
    ].iloc[0]

    spot_base = float(
        base["spot"]
    )

    gamma_base = float(
        base[
            "gamma_acciones_por_dolar"
        ]
    )

    vanna_base = float(
        base[
            "vanna_acciones_por_punto_iv"
        ]
    )

    charm_base = float(
        base[
            "charm_acciones_por_dia"
        ]
    )

    datos[
        "delta_spot"
    ] = (
        datos["spot"]
        - spot_base
    )

    datos[
        "flujo_gamma_acciones"
    ] = -(
        gamma_base
        * datos["delta_spot"]
    )

    datos[
        "flujo_vanna_acciones"
    ] = -(
        vanna_base
        * datos["shock_iv_puntos"]
    )

    datos[
        "flujo_charm_acciones"
    ] = -(
        charm_base
        * datos["decaimiento_dias"]
    )

    datos[
        "flujo_aprox_acciones"
    ] = (
        datos[
            "flujo_gamma_acciones"
        ]
        + datos[
            "flujo_vanna_acciones"
        ]
        + datos[
            "flujo_charm_acciones"
        ]
    )

    datos[
        "residual_acciones"
    ] = (
        datos[
            "flujo_acciones_total"
        ]
        - datos[
            "flujo_aprox_acciones"
        ]
    )

    datos[
        "flujo_gamma_dolares"
    ] = (
        datos[
            "flujo_gamma_acciones"
        ]
        * datos["spot"]
    )

    datos[
        "flujo_vanna_dolares"
    ] = (
        datos[
            "flujo_vanna_acciones"
        ]
        * datos["spot"]
    )

    datos[
        "flujo_charm_dolares"
    ] = (
        datos[
            "flujo_charm_acciones"
        ]
        * datos["spot"]
    )

    datos[
        "residual_dolares"
    ] = (
        datos[
            "residual_acciones"
        ]
        * datos["spot"]
    )

    return datos


def imprimir_resumen(
    datos: pd.DataFrame,
) -> None:
    """Imprime los escenarios principales."""

    muestra = datos[
        (
            datos[
                "shock_iv_puntos"
            ]
            == 0
        )
        & (
            datos[
                "decaimiento_dias"
            ]
            == 0
        )
    ][
        [
            "shock_spot_pct",
            "spot",
            "flujo_acciones_total",
            "flujo_gamma_acciones",
            "residual_acciones",
            "flujo_dolares_total",
        ]
    ]

    print()
    print("=" * 90)
    print("DEALER ENGINE V3.1")
    print("=" * 90)

    print(
        muestra.to_string(
            index=False,
            float_format=lambda x: (
                f"{x:,.2f}"
            ),
        )
    )


def main() -> None:
    """Ejecuta Dealer Engine V3.1."""

    RUTA_RESULTADOS.mkdir(
        parents=True,
        exist_ok=True,
    )

    cadena = cargar_cadena()

    escenarios = ejecutar_escenarios(
        cadena
    )

    escenarios = añadir_descomposicion(
        escenarios
    )

    ruta = (
        RUTA_RESULTADOS
        / "dealer_v31_escenarios.csv"
    )

    escenarios.to_csv(
        ruta,
        index=False,
    )

    imprimir_resumen(
        escenarios
    )

    print()
    print(
        f"Guardado en: {ruta}"
    )


if __name__ == "__main__":
    main()