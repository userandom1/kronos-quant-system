from __future__ import annotations

import math

from motor_mercado.regimen_universal import (
    analizar_regimen_universal,
)


ACTIVOS = [
    "QQQ",
    "AAPL",
    "GLD",
    "BTC-USD",
    "EURUSD=X",
    "NQ=F",
]


CAMPOS_OBLIGATORIOS = [
    "simbolo",
    "clase",
    "benchmark",
    "precio",
    "retorno_20d",
    "retorno_60d",
    "vol20",
    "vol60",
    "drawdown_actual",
    "regimen_global",
    "score_regimen",
    "confianza_regimen",
]


def validar_resultado(
    simbolo: str,
    resultado: dict[str, object],
) -> None:
    """Valida un resultado universal."""

    faltantes = [
        campo
        for campo in CAMPOS_OBLIGATORIOS
        if campo not in resultado
    ]

    if faltantes:
        raise AssertionError(
            f"{simbolo}: faltan campos "
            f"{faltantes}"
        )

    precio = float(
        resultado["precio"]
    )

    if (
        not math.isfinite(precio)
        or precio <= 0
    ):
        raise AssertionError(
            f"{simbolo}: precio inválido."
        )


def main() -> None:
    """Ejecuta pruebas multi-activo básicas."""

    errores = 0

    print(
        "=" * 90
    )

    print(
        "TEST MARKET ENGINE MULTI-ACTIVO"
    )

    print(
        "=" * 90
    )

    for simbolo in ACTIVOS:
        try:
            resultado = (
                analizar_regimen_universal(
                    simbolo
                )
            )

            validar_resultado(
                simbolo,
                resultado,
            )

            print(
                f"{simbolo:<12} | OK | "
                f"{resultado['clase']:<10} | "
                f"{resultado['regimen_global']}"
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
            f"Pruebas fallidas: {errores}"
        )

    print(
        "TODAS LAS PRUEBAS MULTI-ACTIVO: OK"
    )


if __name__ == "__main__":
    main()