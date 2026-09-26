from __future__ import annotations

import sys

from motor_mercado.deep_research_activo import (
    ejecutar_deep_research_activo,
)


def main() -> None:
    """Punto de entrada CLI para Deep Research Universal."""

    if len(sys.argv) < 2:
        raise SystemExit(
            "Uso: python -m "
            "motor_sistema.deep_research "
            "TICKER [HORIZONTE]"
        )

    ticker = (
        sys.argv[
            1
        ]
        .strip()
        .upper()
    )

    horizonte = (
        int(
            sys.argv[
                2
            ]
        )
        if len(
            sys.argv
        ) >= 3
        else 20
    )

    ejecutar_deep_research_activo(
        ticker=ticker,
        horizonte=horizonte,
    )


if __name__ == "__main__":
    main()