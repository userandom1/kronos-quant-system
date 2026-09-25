from __future__ import annotations

from motor_sistema.orquestador_universal import (
    analizar_activo_completo,
)


ACTIVOS = [
    "QQQ",
    "AAPL",
    "BTC-USD",
    "EURUSD=X",
    "NQ=F",
]


def main() -> None:
    """Prueba el pipeline universal."""

    errores = 0

    print(
        "=" * 100
    )

    print(
        "TEST PIPELINE UNIVERSAL"
    )

    print(
        "=" * 100
    )

    for simbolo in ACTIVOS:
        try:
            resultado = analizar_activo_completo(
                simbolo,
                horizonte_forecast=5,
            )

            mercado = resultado.motores.get(
                "market_regime"
            )

            if mercado is None:
                raise AssertionError(
                    "Falta Market Regime."
                )

            if mercado.estado != "OK":
                raise AssertionError(
                    f"Market Regime falló: "
                    f"{mercado.error}"
                )

            print(
                f"{simbolo:<12} | "
                f"{resultado.clase:<10} | "
                f"{resultado.resumen_estados()}"
            )

        except Exception as error:
            errores += 1

            print(
                f"{simbolo:<12} | ERROR | "
                f"{error}"
            )

    print()

    if errores:
        raise SystemExit(
            f"Errores encontrados: {errores}"
        )

    print(
        "PIPELINE UNIVERSAL: OK"
    )


if __name__ == "__main__":
    main()