from dataclasses import dataclass

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


@dataclass(frozen=True)
class ConfiguracionSuperficie:
    """Configuración de una superficie de Greeks."""

    spot: float = 100.0

    volatilidad: float = 0.20

    tipo_interes: float = 0.04

    dividendo: float = 0.01

    tipo: str = "call"

    moneyness_min: float = 0.80

    moneyness_max: float = 1.20

    puntos_moneyness: int = 81

    dte_min: int = 1

    dte_max: int = 365

    puntos_dte: int = 90


GRIEGAS_DISPONIBLES = {
    "delta": delta,
    "gamma": gamma,
    "theta": theta_por_dia,
    "vega": vega_por_punto,
    "vanna": vanna_por_punto,
    "delta_decay": delta_decay_por_dia,
}


def crear_ejes(
    configuracion: ConfiguracionSuperficie,
) -> tuple[np.ndarray, np.ndarray]:
    """Crea los ejes de moneyness y DTE."""

    moneyness = np.linspace(
        configuracion.moneyness_min,
        configuracion.moneyness_max,
        configuracion.puntos_moneyness,
    )

    dte = np.linspace(
        configuracion.dte_min,
        configuracion.dte_max,
        configuracion.puntos_dte,
    )

    return (
        moneyness,
        dte,
    )


def calcular_superficie(
    nombre_griega: str,
    configuracion: ConfiguracionSuperficie,
) -> pd.DataFrame:
    """Calcula una superficie Moneyness x DTE para una Greek."""

    if nombre_griega not in GRIEGAS_DISPONIBLES:
        raise ValueError(
            f"Greek no soportada: {nombre_griega}"
        )

    funcion = GRIEGAS_DISPONIBLES[
        nombre_griega
    ]

    moneyness, dte = crear_ejes(
        configuracion
    )

    filas: list[dict[str, float]] = []

    for dias in dte:
        tiempo = float(
            dias / 365.0
        )

        for ratio in moneyness:
            strike = float(
                configuracion.spot
                * ratio
            )

            parametros = ParametrosOpcion(
                spot=configuracion.spot,
                strike=strike,
                tiempo=tiempo,
                volatilidad=(
                    configuracion.volatilidad
                ),
                tipo_interes=(
                    configuracion.tipo_interes
                ),
                dividendo=(
                    configuracion.dividendo
                ),
                tipo=configuracion.tipo,
            )

            valor = float(
                funcion(
                    parametros
                )
            )

            filas.append(
                {
                    "moneyness": float(
                        ratio
                    ),
                    "dte": float(
                        dias
                    ),
                    "strike": strike,
                    "valor": valor,
                }
            )

    return pd.DataFrame(
        filas
    )


def calcular_todas_las_superficies(
    configuracion: ConfiguracionSuperficie,
) -> dict[str, pd.DataFrame]:
    """Calcula todas las superficies soportadas."""

    superficies: dict[
        str,
        pd.DataFrame,
    ] = {}

    for nombre_griega in GRIEGAS_DISPONIBLES:
        superficies[
            nombre_griega
        ] = calcular_superficie(
            nombre_griega,
            configuracion,
        )

    return superficies