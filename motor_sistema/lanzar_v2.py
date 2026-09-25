from __future__ import annotations

import argparse
import subprocess
import sys

from motor_sistema.comprobar_sistema_v2 import (
    comprobar_sistema,
)


def main() -> None:
    """Punto de entrada final de Quant Platform V2."""

    parser = argparse.ArgumentParser(
        description=(
            "Quant Platform V2"
        )
    )

    parser.add_argument(
        "--dashboard",
        action="store_true",
        help="Lanza Dashboard V2.",
    )

    parser.add_argument(
        "--activo",
        type=str,
        help="Analiza un activo.",
    )

    parser.add_argument(
        "--universo",
        type=str,
        help="Analiza un universo.",
    )

    argumentos = parser.parse_args()

    correcto, checks = comprobar_sistema()

    if not correcto:
        print(
            "Health Check V2 fallido."
        )

        for check in checks:
            print(
                f"{check.componente}: "
                f"{check.estado}"
            )

        raise SystemExit(1)

    if argumentos.activo:
        comando = [
            sys.executable,
            "-m",
            "motor_sistema.release_v2",
            "ACTIVO",
            argumentos.activo.upper(),
        ]

        raise SystemExit(
            subprocess.call(
                comando
            )
        )

    if argumentos.universo:
        comando = [
            sys.executable,
            "-m",
            "motor_sistema.release_v2",
            "UNIVERSO",
            argumentos.universo.upper(),
        ]

        raise SystemExit(
            subprocess.call(
                comando
            )
        )

    if argumentos.dashboard:
        from dashboard_v2.servidor import (
            main as lanzar_dashboard,
        )

        print(
            "Dashboard V2:"
        )

        print(
            "http://127.0.0.1:8010"
        )

        lanzar_dashboard()

        return

    print(
        "=" * 80
    )

    print(
        "QUANT PLATFORM V2.0.0"
    )

    print(
        "=" * 80
    )

    print(
        "Sistema operativo."
    )

    print()

    print(
        "Dashboard:"
    )

    print(
        "python -m "
        "motor_sistema.lanzar_v2 "
        "--dashboard"
    )

    print()

    print(
        "Activo:"
    )

    print(
        "python -m "
        "motor_sistema.lanzar_v2 "
        "--activo AAPL"
    )

    print()

    print(
        "Universo:"
    )

    print(
        "python -m "
        "motor_sistema.lanzar_v2 "
        "--universo US_TECH"
    )


if __name__ == "__main__":
    main()