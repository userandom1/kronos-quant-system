from __future__ import annotations

import argparse
import subprocess
import sys
import time
import webbrowser
from datetime import datetime
from pathlib import Path

from motor_sistema.actualizar_todo import (
    actualizar_todo,
)
from motor_sistema.comprobar_sistema import (
    comprobar_sistema,
    guardar_resultado,
    imprimir_resultado,
)


RUTA_BASE = Path(__file__).resolve().parents[1]

URL_DASHBOARD = (
    "http://127.0.0.1:8000"
)


def imprimir_banner() -> None:
    """Muestra información de Release V1."""

    print()

    print(
        "=" * 100
    )

    print(
        "KRONOS QUANT SYSTEM"
    )

    print(
        "RELEASE V1"
    )

    print(
        "=" * 100
    )

    print(
        f"Fecha: "
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    print(
        f"Ruta: {RUTA_BASE}"
    )

    print(
        f"Python: {sys.executable}"
    )

    print()


def lanzar_dashboard() -> subprocess.Popen:
    """Lanza dashboard Kronos en segundo plano."""

    proceso = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "dashboard.servidor_perspective",
        ],
        cwd=RUTA_BASE,
    )

    return proceso


def esperar_dashboard(
    segundos: float = 2.5,
) -> None:
    """Espera brevemente al arranque de Uvicorn."""

    time.sleep(
        segundos
    )


def ejecutar_release(
    actualizar: bool,
    dashboard: bool,
) -> int:
    """Ejecuta Release V1."""

    imprimir_banner()

    if actualizar:
        print(
            "1. Ejecutando actualización completa..."
        )

        print()

        correcto_pipeline = actualizar_todo()

        if not correcto_pipeline:
            print()

            print(
                "El pipeline ha terminado con "
                "errores críticos."
            )

            print(
                "Se ejecutará igualmente la "
                "comprobación del sistema."
            )

    else:
        correcto_pipeline = True

        print(
            "1. Actualización omitida."
        )

    print()

    print(
        "2. Comprobando estado del sistema..."
    )

    correcto_sistema, tabla = (
        comprobar_sistema()
    )

    imprimir_resultado(
        tabla
    )

    ruta_estado = guardar_resultado(
        tabla
    )

    print()

    print(
        f"Estado guardado: {ruta_estado}"
    )

    print()

    if correcto_sistema:
        print(
            "KRONOS RELEASE V1: OPERATIVO"
        )

    else:
        print(
            "KRONOS RELEASE V1: INCOMPLETO"
        )

    if dashboard:
        print()

        print(
            "3. Iniciando dashboard..."
        )

        lanzar_dashboard()

        esperar_dashboard()

        print(
            f"Dashboard: {URL_DASHBOARD}"
        )

        try:
            webbrowser.open(
                URL_DASHBOARD
            )

        except Exception:
            pass

    if (
        correcto_pipeline
        and correcto_sistema
    ):
        return 0

    return 1


def construir_argumentos() -> argparse.Namespace:
    """Procesa argumentos de línea de comandos."""

    parser = argparse.ArgumentParser(
        description=(
            "Kronos Quant System Release V1"
        )
    )

    parser.add_argument(
        "--dashboard",
        action="store_true",
        help=(
            "Inicia el dashboard tras actualizar "
            "y comprobar el sistema."
        ),
    )

    parser.add_argument(
        "--sin-actualizar",
        action="store_true",
        help=(
            "Comprueba el sistema sin ejecutar "
            "el pipeline de actualización."
        ),
    )

    return parser.parse_args()


def main() -> None:
    """Punto de entrada oficial de Kronos."""

    argumentos = construir_argumentos()

    codigo = ejecutar_release(
        actualizar=(
            not argumentos.sin_actualizar
        ),
        dashboard=argumentos.dashboard,
    )

    raise SystemExit(
        codigo
    )


if __name__ == "__main__":
    main()