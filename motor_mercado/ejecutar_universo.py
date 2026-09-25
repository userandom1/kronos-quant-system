from __future__ import annotations

import sys

from core.activos.universos import (
    listar_universos,
    obtener_universo,
)
from motor_mercado.comparador_universal import (
    analizar_universo,
    clasificar_fuerza_relativa,
    construir_score_relativo,
    guardar_resultados,
    imprimir_ranking,
    ordenar_resultados,
)


def ejecutar(
    nombre: str,
) -> None:
    """Ejecuta un universo completo."""

    simbolos = obtener_universo(
        nombre
    )

    print(
        f"Universo : {nombre}"
    )

    print(
        f"Activos  : {len(simbolos)}"
    )

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

    ruta_actual, ruta_historica = (
        guardar_resultados(
            datos
        )
    )

    print()
    print(
        f"Actual    : {ruta_actual}"
    )

    print(
        f"Histórico : {ruta_historica}"
    )


def main() -> None:
    """Punto de entrada por terminal."""

    if len(sys.argv) < 2:
        print(
            "Universos disponibles:"
        )

        for universo in listar_universos():
            print(
                f"  {universo}"
            )

        raise SystemExit(1)

    ejecutar(
        sys.argv[1].upper()
    )


if __name__ == "__main__":
    main()