from __future__ import annotations

from core.activos import resolver_activo
from motor_opciones.options_engine_universal import (
    ejecutar_options_engine,
)


ACTIVOS = [
    "QQQ",
    "SPY",
    "AAPL",
    "NVDA",
]


def main() -> None:
    """Prueba Options Engine con varios subyacentes."""

    errores = 0

    print(
        "=" * 90
    )

    print(
        "TEST OPTIONS ENGINE MULTI-ACTIVO"
    )

    print(
        "=" * 90
    )

    for simbolo in ACTIVOS:
        try:
            activo = resolver_activo(
                simbolo
            )

            resultado = ejecutar_options_engine(
                activo
            )

            if resultado.cadena.empty:
                raise AssertionError(
                    "Cadena vacía."
                )

            print(
                f"{simbolo:<8} | OK | "
                f"Spot: {resultado.spot:>10.2f} | "
                f"Exp: {resultado.vencimiento} | "
                f"Contratos: "
                f"{resultado.resumen['contratos']}"
            )

        except Exception as error:
            errores += 1

            print(
                f"{simbolo:<8} | ERROR | "
                f"{error}"
            )

    print()

    if errores:
        raise SystemExit(
            f"Fallos encontrados: {errores}"
        )

    print(
        "OPTIONS ENGINE MULTI-ACTIVO: OK"
    )


if __name__ == "__main__":
    main()