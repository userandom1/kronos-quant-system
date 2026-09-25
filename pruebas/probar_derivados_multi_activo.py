from __future__ import annotations

from core.activos import resolver_activo
from motor_opciones.dealer_universal import (
    calcular_exposiciones_dealer,
    resumir_dealer,
)
from motor_opciones.griegas_universales import (
    aplicar_griegas,
)
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
    """Prueba Greeks y Dealer Engine multi-activo."""

    errores = 0

    for simbolo in ACTIVOS:
        try:
            activo = resolver_activo(
                simbolo
            )

            resultado = (
                ejecutar_options_engine(
                    activo
                )
            )

            cadena = aplicar_griegas(
                resultado.cadena,
                resultado.spot,
            )

            cadena = (
                calcular_exposiciones_dealer(
                    cadena,
                    resultado.spot,
                )
            )

            resumen = resumir_dealer(
                cadena
            )

            print(
                f"{simbolo:<6} | OK | "
                f"{len(cadena):>5} contratos | "
                f"GEX: "
                f"${resumen['net_gex_1pct']:,.0f}"
            )

        except Exception as error:
            errores += 1

            print(
                f"{simbolo:<6} | ERROR | "
                f"{error}"
            )

    if errores:
        raise SystemExit(
            f"Errores: {errores}"
        )

    print()
    print(
        "DERIVADOS MULTI-ACTIVO: OK"
    )


if __name__ == "__main__":
    main()