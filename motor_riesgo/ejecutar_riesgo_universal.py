from __future__ import annotations

import sys

from motor_portfolio.portfolio_universal import (
    ejecutar_portfolio_universal,
)
from motor_riesgo.risk_engine_universal import (
    analizar_riesgo,
)


def main() -> None:
    """Ejecuta Portfolio + Risk Engine Universal."""

    if len(sys.argv) < 3:
        raise SystemExit(
            "Uso: python -m "
            "motor_riesgo.ejecutar_riesgo_universal "
            "ACTIVO1 ACTIVO2 ..."
        )

    simbolos = [
        simbolo.upper()
        for simbolo in sys.argv[
            1:
        ]
    ]

    portfolio = ejecutar_portfolio_universal(
        simbolos
    )

    pesos = portfolio.pesos[
        "SIGNAL_TILTED"
    ]

    riesgo = analizar_riesgo(
        retornos=portfolio.retornos,
        pesos=pesos,
        factor_anual=portfolio.factor_anual,
    )

    print(
        "=" * 90
    )

    print(
        "RISK ENGINE UNIVERSAL"
    )

    print(
        "=" * 90
    )

    print(
        f"Volatilidad anual : "
        f"{riesgo['volatilidad_anual'] * 100:.2f}%"
    )

    print(
        f"VaR 95%           : "
        f"{riesgo['var_95'] * 100:.2f}%"
    )

    print(
        f"VaR 99%           : "
        f"{riesgo['var_99'] * 100:.2f}%"
    )

    print(
        f"CVaR 95%          : "
        f"{riesgo['cvar_95'] * 100:.2f}%"
    )

    print(
        f"CVaR 99%          : "
        f"{riesgo['cvar_99'] * 100:.2f}%"
    )

    print(
        f"Max Drawdown      : "
        f"{riesgo['max_drawdown'] * 100:.2f}%"
    )

    print(
        f"HHI               : "
        f"{riesgo['hhi']:.4f}"
    )

    print(
        f"Activos efectivos : "
        f"{riesgo['activos_efectivos']:.2f}"
    )

    print()
    print(
        "CONTRIBUCIÓN AL RIESGO"
    )

    print(
        riesgo[
            "contribucion_riesgo"
        ]
        .sort_values(
            ascending=False
        )
        .mul(
            100
        )
        .round(
            2
        )
        .to_string()
    )


if __name__ == "__main__":
    main()