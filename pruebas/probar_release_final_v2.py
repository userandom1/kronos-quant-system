from __future__ import annotations

from motor_sistema.api_v2 import (
    api_activo,
    api_health,
)
from motor_sistema.workspaces import (
    cargar_watchlists,
)


def main() -> None:
    """Smoke test final de V2."""

    health = api_health()

    if not health[
        "operativo"
    ]:
        raise AssertionError(
            "Health Check V2 fallido."
        )

    watchlists = cargar_watchlists()

    if not watchlists:
        raise AssertionError(
            "No existen watchlists."
        )

    resultado = api_activo(
        "AAPL",
        horizonte=5,
    )

    if (
        "market_regime"
        not in resultado[
            "motores"
        ]
    ):
        raise AssertionError(
            "Falta Market Regime."
        )

    print(
        "API INTERNA            : OK"
    )

    print(
        "WATCHLISTS             : OK"
    )

    print(
        "MULTI-ASSET PIPELINE   : OK"
    )

    print(
        "QUANT PLATFORM V2.0.0  : OK"
    )


if __name__ == "__main__":
    main()