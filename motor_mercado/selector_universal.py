from __future__ import annotations

import sys

from core.activos.universos import (
    listar_universos,
)
from motor_mercado.comparador_universal import (
    analizar_universo,
    clasificar_fuerza_relativa,
    construir_score_relativo,
    imprimir_ranking,
    ordenar_resultados,
)
from motor_mercado.ejecutar_universo import (
    ejecutar as ejecutar_universo,
)
from motor_mercado.regimen_universal import (
    analizar_regimen_universal,
    imprimir_regimen,
)


def ejecutar_activo(
    simbolo: str,
) -> None:
    """Analiza un activo individual."""

    resultado = analizar_regimen_universal(
        simbolo
    )

    imprimir_regimen(
        resultado
    )


def ejecutar_lista(
    simbolos: list[str],
) -> None:
    """Compara una lista arbitraria de activos."""

    datos = analizar_universo(
        simbolos
    )

    datos = construir_score_relativo(
        datos
    )

    datos = clasificar_fuerza_relativa(
        datos
    )

    datos = ordenar_resultados(
        datos
    )

    imprimir_ranking(
        datos
    )


def imprimir_ayuda() -> None:
    """Muestra comandos disponibles."""

    print(
        """
USO

Activo individual:
python -m motor_mercado.selector_universal ACTIVO QQQ

Universo:
python -m motor_mercado.selector_universal UNIVERSO US_TECH

Lista personalizada:
python -m motor_mercado.selector_universal LISTA QQQ AAPL BTC-USD GLD

Universos disponibles:
"""
    )

    for universo in listar_universos():
        print(
            f"  {universo}"
        )


def main() -> None:
    """CLI universal de Market Engine."""

    if len(sys.argv) < 2:
        imprimir_ayuda()
        raise SystemExit(0)

    comando = sys.argv[
        1
    ].strip().upper()

    if comando == "ACTIVO":
        if len(sys.argv) < 3:
            raise SystemExit(
                "Falta el símbolo."
            )

        ejecutar_activo(
            sys.argv[2]
        )

        return

    if comando == "UNIVERSO":
        if len(sys.argv) < 3:
            raise SystemExit(
                "Falta el nombre del universo."
            )

        ejecutar_universo(
            sys.argv[2].upper()
        )

        return

    if comando == "LISTA":
        if len(sys.argv) < 3:
            raise SystemExit(
                "Faltan activos."
            )

        ejecutar_lista(
            sys.argv[2:]
        )

        return

    if comando in {
        "AYUDA",
        "HELP",
        "-H",
        "--HELP",
    }:
        imprimir_ayuda()
        return

    # Atajo:
    # python -m motor_mercado.selector_universal NVDA
    ejecutar_activo(
        comando
    )


if __name__ == "__main__":
    main()