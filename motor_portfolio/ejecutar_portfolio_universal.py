from __future__ import annotations

import sys
from pathlib import Path

from motor_portfolio.portfolio_universal import (
    ejecutar_portfolio_universal,
)


RUTA_BASE = Path(
    __file__
).resolve().parents[1]

RUTA_RESULTADOS = (
    RUTA_BASE
    / "resultados"
    / "portfolio_universal"
)


def main() -> None:
    """Ejecuta Portfolio Engine Universal."""

    if len(sys.argv) < 3:
        raise SystemExit(
            "Uso: python -m "
            "motor_portfolio.ejecutar_portfolio_universal "
            "ACTIVO1 ACTIVO2 ACTIVO3 ..."
        )

    simbolos = [
        simbolo.upper()
        for simbolo in sys.argv[
            1:
        ]
    ]

    resultado = ejecutar_portfolio_universal(
        simbolos
    )

    print(
        "=" * 90
    )

    print(
        "PORTFOLIO ENGINE UNIVERSAL"
    )

    print(
        "=" * 90
    )

    print(
        resultado.pesos.round(
            4
        ).to_string()
    )

    RUTA_RESULTADOS.mkdir(
        parents=True,
        exist_ok=True,
    )

    resultado.pesos.to_csv(
        RUTA_RESULTADOS
        / "pesos_actuales.csv"
    )

    resultado.retornos.to_csv(
        RUTA_RESULTADOS
        / "retornos.csv"
    )

    print()
    print(
        f"Resultados: {RUTA_RESULTADOS}"
    )


if __name__ == "__main__":
    main()