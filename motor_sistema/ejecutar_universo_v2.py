from __future__ import annotations

import sys

from core.activos.universos import (
    obtener_universo,
)
from motor_sistema.orquestador_universal import (
    analizar_activo_completo,
)


def main() -> None:
    """Ejecuta el sistema sobre un universo completo."""

    if len(sys.argv) < 2:
        raise SystemExit(
            "Uso: python -m "
            "motor_sistema.ejecutar_universo_v2 "
            "UNIVERSO"
        )

    nombre = sys.argv[
        1
    ].upper()

    activos = obtener_universo(
        nombre
    )

    print(
        "=" * 100
    )

    print(
        f"UNIVERSO: {nombre}"
    )

    print(
        "=" * 100
    )

    for simbolo in activos:
        print()
        print(
            f"Analizando {simbolo}..."
        )

        resultado = analizar_activo_completo(
            simbolo
        )

        estados = resultado.resumen_estados()

        mercado = resultado.motores.get(
            "market_regime"
        )

        regimen = "-"

        if (
            mercado
            and mercado.estado == "OK"
        ):
            regimen = str(
                mercado.datos.get(
                    "regimen_global"
                )
            )

        print(
            f"{simbolo:<12} | "
            f"{resultado.clase:<10} | "
            f"{regimen:<18} | "
            f"{estados}"
        )


if __name__ == "__main__":
    main()