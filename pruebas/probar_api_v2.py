from __future__ import annotations

import json

from motor_sistema.api_v2 import (
    api_activo,
    api_health,
    api_universo,
    api_watchlist,
)


def verificar_json(
    nombre: str,
    datos: object,
) -> None:
    """Comprueba serialización JSON estricta."""

    json.dumps(
        datos,
        ensure_ascii=False,
        allow_nan=False,
    )

    print(
        f"{nombre:<24} | OK"
    )


def main() -> None:
    """Prueba endpoints internos de API V2."""

    print(
        "=" * 70
    )

    print(
        "TEST API V2"
    )

    print(
        "=" * 70
    )

    verificar_json(
        "Health",
        api_health(),
    )

    verificar_json(
        "Activo AAPL",
        api_activo(
            "AAPL",
            horizonte=5,
        ),
    )

    verificar_json(
        "Universo US_TECH",
        api_universo(
            "US_TECH"
        ),
    )

    verificar_json(
        "Watchlist PRINCIPAL",
        api_watchlist(
            "PRINCIPAL"
        ),
    )

    print()
    print(
        "API V2: OK"
    )


if __name__ == "__main__":
    main()