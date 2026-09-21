from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ShockSuperficieIV:
    """
    Shock aplicado sobre la IV observada de cada contrato.

    atm_puntos:
        Cambio paralelo de IV expresado en puntos porcentuales.

    skew:
        Cambio de pendiente respecto a log-moneyness.

    curvatura:
        Cambio de convexidad respecto a log-moneyness.
    """

    atm_puntos: float = 0.0
    skew: float = 0.0
    curvatura: float = 0.0


IV_MINIMA = 0.01
IV_MAXIMA = 5.00


SHOCKS_IV_ATM = (
    -5.0,
    -2.0,
    0.0,
    2.0,
    5.0,
)

SHOCKS_SKEW = (
    -0.20,
    -0.10,
    0.0,
    0.10,
    0.20,
)

SHOCKS_CURVATURA = (
    -0.50,
    0.0,
    0.50,
)


def aplicar_shock_iv(
    iv_base: float,
    log_moneyness: float,
    shock: ShockSuperficieIV,
) -> float:
    """
    Aplica un shock local sobre la IV observada.

    sigma' =
        sigma
        + shock_ATM
        + shock_skew * m
        + shock_curvatura * m²

    donde:

        m = ln(K / S_escenario)
    """

    iv = (
        iv_base
        + shock.atm_puntos / 100.0
        + shock.skew * log_moneyness
        + shock.curvatura * log_moneyness**2
    )

    return float(
        np.clip(
            iv,
            IV_MINIMA,
            IV_MAXIMA,
        )
    )