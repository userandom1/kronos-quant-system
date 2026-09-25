from __future__ import annotations

import numpy as np

from motor_portfolio.portfolio_universal import (
    ejecutar_portfolio_universal,
)
from motor_riesgo.risk_engine_universal import (
    analizar_riesgo,
)


ACTIVOS = [
    "QQQ",
    "SPY",
    "GLD",
    "TLT",
    "AAPL",
]


def main() -> None:
    """Prueba Portfolio y Risk Engine universales."""

    portfolio = ejecutar_portfolio_universal(
        ACTIVOS
    )

    for columna in portfolio.pesos.columns:
        suma = float(
            portfolio.pesos[
                columna
            ].sum()
        )

        if not np.isclose(
            suma,
            1.0,
            atol=1e-6,
        ):
            raise AssertionError(
                f"{columna}: pesos suman {suma}"
            )

    pesos = portfolio.pesos[
        "SIGNAL_TILTED"
    ]

    riesgo = analizar_riesgo(
        retornos=portfolio.retornos,
        pesos=pesos,
        factor_anual=portfolio.factor_anual,
    )

    assert (
        riesgo[
            "volatilidad_anual"
        ]
        > 0
    )

    print(
        "PORTFOLIO UNIVERSAL: OK"
    )

    print(
        "RISK ENGINE UNIVERSAL: OK"
    )

    print()

    print(
        portfolio.pesos.round(
            4
        )
    )


if __name__ == "__main__":
    main()