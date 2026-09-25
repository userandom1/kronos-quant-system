from __future__ import annotations

import sys
import time

from core.activos.universos import (
    obtener_universo,
)
from motor_sistema.comprobar_sistema_v2 import (
    comprobar_sistema,
)
from motor_sistema.orquestador_universal import (
    analizar_activo_completo,
)
from motor_sistema.orquestador_universo import (
    analizar_universo_completo,
)


def ejecutar_activo(
    simbolo: str,
) -> bool:
    """Ejecuta Release V2 para un activo."""

    resultado = analizar_activo_completo(
        simbolo
    )

    print()
    print(
        f"Activo : {resultado.simbolo}"
    )

    print(
        f"Clase  : {resultado.clase}"
    )

    for nombre, motor in resultado.motores.items():
        print(
            f"{nombre:<20}: "
            f"{motor.estado}"
        )

        if motor.error:
            print(
                f"  {motor.error}"
            )

    return all(
        motor.estado
        in {
            "OK",
            "NO_COMPATIBLE",
        }
        for motor in resultado.motores.values()
    )


def ejecutar_universo(
    nombre: str,
) -> bool:
    """Ejecuta Release V2 para un universo."""

    simbolos = obtener_universo(
        nombre
    )

    resultado = analizar_universo_completo(
        simbolos
    )

    print()
    print(
        "RANKING"
    )

    print(
        resultado.ranking[
            [
                "ranking",
                "simbolo",
                "regimen_global",
                "score_relativo",
            ]
        ].to_string(
            index=False
        )
    )

    print()
    print(
        "PESOS SIGNAL TILTED"
    )

    print(
        resultado.portfolio.pesos[
            "SIGNAL_TILTED"
        ]
        .sort_values(
            ascending=False
        )
        .round(
            4
        )
        .to_string()
    )

    print()
    print(
        f"Volatilidad anual : "
        f"{resultado.riesgo['volatilidad_anual'] * 100:.2f}%"
    )

    print(
        f"CVaR 95%          : "
        f"{resultado.riesgo['cvar_95'] * 100:.2f}%"
    )

    print(
        f"Max Drawdown      : "
        f"{resultado.riesgo['max_drawdown'] * 100:.2f}%"
    )

    return True


def main() -> None:
    """Punto de entrada de Release V2."""

    if len(sys.argv) < 3:
        raise SystemExit(
            "\nUso:\n"
            "  python -m motor_sistema.release_v2 "
            "ACTIVO AAPL\n"
            "  python -m motor_sistema.release_v2 "
            "UNIVERSO US_TECH\n"
        )

    modo = sys.argv[
        1
    ].upper()

    objetivo = sys.argv[
        2
    ].upper()

    inicio = time.perf_counter()

    print(
        "=" * 90
    )

    print(
        "QUANT PLATFORM — RELEASE V2"
    )

    print(
        "=" * 90
    )

    correcto_health, checks = (
        comprobar_sistema()
    )

    print()

    for check in checks:
        print(
            f"{check.componente:<20} | "
            f"{check.estado}"
        )

    if not correcto_health:
        print()
        print(
            "RELEASE V2: HEALTH CHECK FALLIDO"
        )

        raise SystemExit(1)

    print()

    try:
        if modo == "ACTIVO":
            correcto_pipeline = (
                ejecutar_activo(
                    objetivo
                )
            )

        elif modo == "UNIVERSO":
            correcto_pipeline = (
                ejecutar_universo(
                    objetivo
                )
            )

        else:
            raise ValueError(
                f"Modo desconocido: {modo}"
            )

    except Exception as error:
        print()
        print(
            f"ERROR PIPELINE: {error}"
        )

        correcto_pipeline = False

    duracion = (
        time.perf_counter()
        - inicio
    )

    print()

    print(
        "=" * 90
    )

    if correcto_pipeline:
        print(
            "RELEASE V2: OPERATIVO"
        )

    else:
        print(
            "RELEASE V2: PIPELINE CON ERRORES"
        )

    print(
        f"Duración: {duracion:.2f} s"
    )

    print(
        "=" * 90
    )

    raise SystemExit(
        0
        if correcto_pipeline
        else 1
    )


if __name__ == "__main__":
    main()